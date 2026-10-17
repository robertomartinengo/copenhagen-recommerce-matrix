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

@app.get("/zones")
def get_zones():
    try:
        # Tenta di leggere la tabella da Supabase
        response = supabase.table("copenhagen_zones").select("*").execute()
        return response.data
    except Exception as e:
        # Se c'è un errore, lo restituisce subito sullo schermo
        return {"error_detail": str(e)}