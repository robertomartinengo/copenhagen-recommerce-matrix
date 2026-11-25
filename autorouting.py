# autorouting.py
"""
Automatic LLM fallback routing for budget-zero operation.

Tries, in order:
1. Google Gemini (google-genai SDK)
2. Groq (HTTP API)
3. OpenRouter (HTTP API, free models only)
4. Returns None if all fail (caller must use deterministic fallback).

All API keys are read from environment variables. No personal data is sent
to any model (see .clinerules rule 10).
"""

import logging
import os
import sys
import time
import uuid

import httpx
from google import genai
from google.genai import types
from posthog.ai.gemini import Client as PostHogGeminiClient

logger = logging.getLogger(__name__)

GEMINI_DEFAULT_MODEL = "gemini-3.8-flash"
GROQ_DEFAULT_MODEL = "llama-3.1-8b-instant"
OPENROUTER_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _get_posthog_client():
    """Return the FastAPI singleton when this module runs inside the server app."""
    main_module = sys.modules.get("main")
    return getattr(main_module, "posthog_client", None)


def _ai_session_id() -> str:
    """Group report-generation turns within the currently running application."""
    return f"executive-report-process-{os.getpid()}"


def _capture_http_generation(
    *,
    prompt: str,
    text: str,
    model: str,
    provider: str,
    trace_id: str,
    latency: float,
    status_code: int | None,
    data: dict | None = None,
    is_error: bool = False,
) -> None:
    """Capture a raw HTTP provider call without affecting the fallback flow."""
    posthog_client = _get_posthog_client()
    if posthog_client is None:
        return

    properties = {
        "$ai_trace_id": trace_id,
        "$ai_session_id": _ai_session_id(),
        "$ai_model": model,
        "$ai_provider": provider,
        "$ai_input": [{"role": "user", "content": prompt}],
        "$ai_output_choices": [{"role": "assistant", "content": text}],
        "$ai_latency": latency,
        "$ai_temperature": 0.4,
        "$ai_max_tokens": 1024,
        "$ai_is_error": is_error,
    }
    if status_code is not None:
        properties["$ai_http_status"] = status_code
    if data:
        usage = data.get("usage", {})
        if usage.get("prompt_tokens") is not None:
            properties["$ai_input_tokens"] = usage["prompt_tokens"]
        if usage.get("completion_tokens") is not None:
            properties["$ai_output_tokens"] = usage["completion_tokens"]

    try:
        posthog_client.capture_ai("$ai_generation", properties=properties)
    except Exception:
        logger.debug("Unable to capture HTTP AI generation", exc_info=True)


def _call_gemini(prompt: str, trace_id: str) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        posthog_client = _get_posthog_client()
        client = (
            PostHogGeminiClient(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=20000),
                posthog_client=posthog_client,
            )
            if posthog_client is not None
            else genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=20000),
            )
        )
        model = os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
        generation_options = {
            "model": model,
            "contents": prompt,
            "config": types.GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.4,
            ),
        }
        if posthog_client is not None:
            generation_options.update(
                posthog_trace_id=trace_id,
                posthog_properties={"$ai_session_id": _ai_session_id()},
            )
        response = client.models.generate_content(**generation_options)
        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()
    except Exception:
        logger.warning("Gemini provider failed")
    return None


def _call_groq(prompt: str, trace_id: str) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL)
    started_at = time.monotonic()
    try:
        with httpx.Client(timeout=20.0) as http:
            response = http.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 1024,
                },
            )
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            text = choices[0].get("message", {}).get("content", "") if choices else ""
            _capture_http_generation(
                prompt=prompt,
                text=text,
                model=model,
                provider="groq",
                trace_id=trace_id,
                latency=time.monotonic() - started_at,
                status_code=response.status_code,
                data=data,
            )
            if text and text.strip():
                return text.strip()
        else:
            _capture_http_generation(
                prompt=prompt,
                text="",
                model=model,
                provider="groq",
                trace_id=trace_id,
                latency=time.monotonic() - started_at,
                status_code=response.status_code,
                is_error=True,
            )
    except Exception:
        _capture_http_generation(
            prompt=prompt,
            text="",
            model=model,
            provider="groq",
            trace_id=trace_id,
            latency=time.monotonic() - started_at,
            status_code=None,
            is_error=True,
        )
        logger.warning("Groq provider failed")
    return None


def _call_openrouter(prompt: str, trace_id: str) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    model = os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)
    started_at = time.monotonic()
    try:
        with httpx.Client(timeout=20.0) as http:
            response = http.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 1024,
                },
            )
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            text = choices[0].get("message", {}).get("content", "") if choices else ""
            _capture_http_generation(
                prompt=prompt,
                text=text,
                model=model,
                provider="openrouter",
                trace_id=trace_id,
                latency=time.monotonic() - started_at,
                status_code=response.status_code,
                data=data,
            )
            if text and text.strip():
                return text.strip()
        else:
            _capture_http_generation(
                prompt=prompt,
                text="",
                model=model,
                provider="openrouter",
                trace_id=trace_id,
                latency=time.monotonic() - started_at,
                status_code=response.status_code,
                is_error=True,
            )
    except Exception:
        _capture_http_generation(
            prompt=prompt,
            text="",
            model=model,
            provider="openrouter",
            trace_id=trace_id,
            latency=time.monotonic() - started_at,
            status_code=None,
            is_error=True,
        )
        logger.warning("OpenRouter provider failed")
    return None


def call_llm_with_fallback(prompt: str) -> str | None:
    """
    Try LLM providers in order: Gemini -> Groq -> OpenRouter.
    Returns the generated text, or None if all fail.
    """
    trace_id = str(uuid.uuid4())
    for provider in (_call_gemini, _call_groq, _call_openrouter):
        try:
            result = provider(prompt, trace_id)
            if result:
                return result
        except Exception:
            continue
    return None
