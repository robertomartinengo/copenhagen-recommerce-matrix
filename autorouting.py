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

import os
import httpx
from google import genai
from google.genai import types

GEMINI_DEFAULT_MODEL = "gemini-3.8-flash"
GROQ_DEFAULT_MODEL = "llama-3.1-8b-instant"
OPENROUTER_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _call_gemini(prompt: str) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=20000),
        )
        model = os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.4,
            ),
        )
        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()
    except Exception:
        pass
    return None


def _call_groq(prompt: str) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        model = os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL)
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
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                if text and text.strip():
                    return text.strip()
    except Exception:
        pass
    return None


def _call_openrouter(prompt: str) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    try:
        model = os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)
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
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                if text and text.strip():
                    return text.strip()
    except Exception:
        pass
    return None


def call_llm_with_fallback(prompt: str) -> str | None:
    """
    Try LLM providers in order: Gemini -> Groq -> OpenRouter.
    Returns the generated text, or None if all fail.
    """
    for provider in (_call_gemini, _call_groq, _call_openrouter):
        try:
            result = provider(prompt)
            if result:
                return result
        except Exception:
            continue
    return None
