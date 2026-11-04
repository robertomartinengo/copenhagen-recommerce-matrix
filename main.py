import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr

from cpi_engine import calculate_dynamic_cpi, BUSINESS_PROFILES
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


class LeadSchema(BaseModel):
    telegram_user_id: int
    telegram_username: str | None = None
    full_name: str
    email: str
    business_type: str | None = None
    interested_district: str | None = None


@app.post("/leads")
def create_lead(lead: LeadSchema):
    try:
        data = lead.model_dump()
        response = supabase.table("leads").insert(data).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore salvataggio lead: {e}")

@app.get("/")
def read_root():
    return {"status": "online", "message": "Copenhagen Re-Commerce Matrix API is running."}


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