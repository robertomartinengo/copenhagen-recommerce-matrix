from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI(
    title="Copenhagen Re-Commerce Matrix API",
    description="API per il calcolo del potenziale di re-commerce nei distretti di Copenhagen.",
    version="1.0.0"
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


@app.get("/zones")
def get_zones():
    if not supabase:
        # Dati di fallback nel caso Supabase non sia configurato
        return [
            {
                "name": "Nørrebro",
                "cpi_score": 8.9,
                "waste_supply_score": 9.1,
                "demographics_score": 8.8,
                "market_gap_score": 8.7,
                "population_gen_z": 14200
            }
        ]
    
    response = supabase.table("districts").select("*").execute()
    return response.data