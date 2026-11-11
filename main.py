import hmac
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv

from cpi_engine import calculate_dynamic_cpi
from bot import start_telegram_bot

load_dotenv(override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Avvia il bot Telegram in background all'avvio del server
    asyncio.create_task(start_telegram_bot())
    yield


app = FastAPI(
    title="Copenhagen Re-Commerce Matrix API",
    description="API per il calcolo del potenziale di re-commerce nei distretti di Copenhagen.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"deleted": int(deleted)}


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
    return updated_zones

@app.get("/zones/top")
def get_top_zone(business_type: str = "curated_vintage"):
    zones = get_zones(business_type=business_type)
    return zones[0] if zones else {}