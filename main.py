from fastapi import FastAPI
from database import supabase

app = FastAPI(
    title="Copenhagen Re-Commerce Matrix API",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "Copenhagen Re-Commerce Matrix",
        "supabase_connected": supabase is not None
    }