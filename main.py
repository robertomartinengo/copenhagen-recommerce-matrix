import atexit
import asyncio
import hmac
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from posthog import Posthog
from posthog.integrations.asgi import PosthogASGIMiddleware
from supabase import create_client

from bot import start_telegram_bot, stop_telegram_bot
from config import get_settings
from cpi_engine import calculate_dynamic_cpi

load_dotenv(override=True)

logger = logging.getLogger(__name__)
posthog_log_logger = logging.getLogger("posthog.exporter")
posthog_log_logger.setLevel(logging.INFO)
posthog_log_logger.propagate = False
settings = get_settings()
posthog_client: Posthog | None = None
posthog_log_provider: LoggerProvider | None = None

if settings.posthog_project_token and settings.posthog_host:
    posthog_client = Posthog(
        settings.posthog_project_token,
        host=settings.posthog_host,
        enable_exception_autocapture=True,
        privacy_mode=False,
    )
    atexit.register(posthog_client.shutdown)

    # Keep log export isolated to the purpose-written logger below so existing
    # application and dependency logs remain on their current outputs only.
    posthog_log_provider = LoggerProvider()
    posthog_log_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=f"{settings.posthog_host.rstrip('/')}/i/v1/logs",
                headers={"Authorization": f"Bearer {settings.posthog_project_token}"},
            )
        )
    )
    posthog_log_logger.addHandler(
        LoggingHandler(logger_provider=posthog_log_provider)
    )
elif settings.app_environment != "production":
    for variable_name in (
        "POSTHOG_PROJECT_TOKEN",
        "POSTHOG_HOST",
    ):
        if not getattr(settings, variable_name.lower()):
            logger.warning(
                "%s variable required by PostHog is missing or un-configured, "
                "this causes events to be silently missed. This error stops "
                "appearing once %s is configured",
                variable_name,
                variable_name,
            )

# Riferimento al task del bot Telegram per evitare avvii duplicati
# (es. reload in sviluppo) e per lo shutdown pulito.
_bot_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot_task
    # Ferma eventuali task precedenti (es. reload in sviluppo)
    if _bot_task is not None and not _bot_task.done():
        _bot_task.cancel()
        try:
            await _bot_task
        except asyncio.CancelledError:
            pass
    # Avvia il bot Telegram in background all'avvio del server
    _bot_task = asyncio.create_task(start_telegram_bot())
    posthog_log_logger.info("FastAPI service started", extra={"component": "api"})
    try:
        yield
    finally:
        # Shutdown pulito del bot
        if _bot_task is not None and not _bot_task.done():
            _bot_task.cancel()
            try:
                await _bot_task
            except asyncio.CancelledError:
                pass
        await stop_telegram_bot()
        _bot_task = None
        posthog_log_logger.info("FastAPI service stopping", extra={"component": "api"})
        if posthog_client is not None:
            try:
                posthog_client.flush()
            except Exception:
                logger.exception("Unable to flush PostHog events during shutdown")
        if posthog_log_provider is not None:
            try:
                posthog_log_provider.force_flush(timeout_millis=5_000)
                posthog_log_provider.shutdown()
            except Exception:
                logger.exception("Unable to flush PostHog logs during shutdown")


app = FastAPI(
    title="Copenhagen Re-Commerce Matrix API",
    description="API per il calcolo del potenziale di re-commerce nei distretti di Copenhagen.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if posthog_client is not None:
    app.add_middleware(PosthogASGIMiddleware, client=posthog_client)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


@app.get("/")
def read_root():
    return {"status": "online", "message": "Copenhagen Re-Commerce Matrix API is running."}


@app.delete("/leads/{telegram_user_id}")
def delete_lead(
    telegram_user_id: int,
    x_lead_delete_token: str | None = Header(default=None),
):
    """Delete all lead data for a Telegram user after an authenticated request."""
    configured_token = os.getenv("LEAD_DELETE_TOKEN")
    if not configured_token:
        raise HTTPException(status_code=503, detail="Lead deletion is not configured")
    if not x_lead_delete_token or not hmac.compare_digest(
        x_lead_delete_token, configured_token
    ):
        raise HTTPException(status_code=401, detail="Invalid deletion token")

    if supabase is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    try:
        response = supabase.rpc(
            "delete_lead_data",
            {
                "p_telegram_user_id": telegram_user_id,
                "p_actor": "authenticated_api_request",
            },
        ).execute()
    except Exception:
        raise HTTPException(status_code=500, detail="Lead deletion failed")

    deleted = getattr(response, "data", 0) or 0
    if isinstance(deleted, list):
        deleted = deleted[0] if deleted else 0
    deleted_count = int(deleted)
    if posthog_client is not None:
        posthog_client.capture(
            "lead_data_deleted",
            properties={"deleted_record_count": deleted_count},
        )
    posthog_log_logger.info(
        "Lead data deleted",
        extra={"deleted_record_count": deleted_count},
    )
    return {"deleted": deleted_count}


@app.get("/zones")
def get_zones(business_type: str = "curated_vintage"):
    # Recupera i dati da Supabase
    response = supabase.table("copenhagen_zones").select("*").execute()
    zones = response.data

    # Ricalcola il CPI dinamico per ogni zona in base al profilo
    updated_zones = [
        {**z, **calculate_dynamic_cpi(z, business_type=business_type)}
        for z in zones
    ]

    # Ordina decrescente per il nuovo CPI dinamico
    updated_zones.sort(key=lambda x: float(x.get("cpi_score", 0)), reverse=True)
    if posthog_client is not None:
        posthog_client.capture(
            "zone_analysis_completed",
            properties={
                "business_type": business_type,
                "zone_count": len(updated_zones),
            },
        )
    posthog_log_logger.info(
        "Zone analysis completed",
        extra={
            "business_type": business_type,
            "zone_count": len(updated_zones),
        },
    )
    return updated_zones


@app.get("/zones/top")
def get_top_zone(business_type: str = "curated_vintage"):
    zones = get_zones(business_type=business_type)
    top_zone = zones[0] if zones else {}
    if posthog_client is not None:
        posthog_client.capture(
            "top_zone_retrieved",
            properties={
                "business_type": business_type,
                "has_recommendation": bool(top_zone),
            },
        )
    return top_zone