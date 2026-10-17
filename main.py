from fastapi import FastAPI
from database import supabase
from cpi_engine import compute_cpi

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
        response = supabase.table("copenhagen_zones").select("*").order("cpi_score", desc=True).execute()
        return response.data
    except Exception as e:
        return {"error_detail": str(e)}

@app.post("/calculate-cpi")
def calculate_all_cpi():
    try:
        # 1. Recupera tutte le zone dal database
        response = supabase.table("copenhagen_zones").select("*").execute()
        zones = response.data

        results = []
        # 2. Calcola e aggiorna in modo sicuro solo il cpi_score per ogni zona
        for zone in zones:
            score = compute_cpi(
                float(zone["waste_supply_score"]),
                int(zone["population_gen_z"]),
                float(zone["avg_income_dkk"]),
                float(zone["market_gap_score"])
            )
            
            # Aggiornamento mirato della colonna cpi_score
            supabase.table("copenhagen_zones").update({"cpi_score": score}).eq("id", zone["id"]).execute()
            results.append({"name": zone["name"], "cpi_score": score})

        # Ordina i risultati dal punteggio più alto al più basso
        results.sort(key=lambda x: x["cpi_score"], reverse=True)

        return {
            "status": "success",
            "updated_count": len(results),
            "top_zone": results[0] if results else None,
            "results": results
        }
    except Exception as e:
        return {"error_detail": str(e)}