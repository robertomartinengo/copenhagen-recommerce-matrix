from fastapi import FastAPI, HTTPException, Response
from typing import List
import csv
import io

from database import supabase
from cpi_engine import compute_cpi
from schemas import (
    ZoneResponse, 
    CPICalculationResponse, 
    CPISimulationRequest, 
    CPISimulationResponse, 
    SimulatedZoneResult
)

app = FastAPI(
    title="Copenhagen Re-Commerce Matrix API",
    version="0.3.0",
    description="Location Intelligence & Data Analytics for Circular Fashion in Greater Copenhagen"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "Copenhagen Re-Commerce Matrix",
        "supabase_connected": supabase is not None
    }

@app.get("/zones", response_model=List[ZoneResponse])
def get_zones():
    try:
        response = supabase.table("copenhagen_zones").select("*").order("cpi_score", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/zones/{district_code}", response_model=ZoneResponse)
def get_zone_by_code(district_code: str):
    try:
        response = supabase.table("copenhagen_zones").select("*").eq("district_code", district_code.upper()).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Zone with code '{district_code}' not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-cpi", response_model=CPICalculationResponse)
def calculate_all_cpi():
    try:
        response = supabase.table("copenhagen_zones").select("*").execute()
        zones = response.data

        results = []
        for zone in zones:
            score = compute_cpi(
                float(zone["waste_supply_score"]),
                int(zone["population_gen_z"]),
                float(zone["avg_income_dkk"]),
                float(zone["market_gap_score"])
            )
            
            supabase.table("copenhagen_zones").update({"cpi_score": score}).eq("id", zone["id"]).execute()
            results.append({"name": zone["name"], "cpi_score": score})

        results.sort(key=lambda x: x["cpi_score"], reverse=True)

        return {
            "status": "success",
            "updated_count": len(results),
            "top_zone": results[0] if results else None,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate-cpi", response_model=CPISimulationResponse)
def simulate_cpi_scenario(weights: CPISimulationRequest):
    # Verifica che la somma dei pesi sia valida (tolleranza arrotondamento a 1.0)
    total_weight = round(weights.weight_supply + weights.weight_demographics + weights.weight_market_gap, 2)
    if total_weight != 1.0:
        raise HTTPException(
            status_code=400, 
            detail=f"La somma dei pesi deve essere pari a 1.0 (100%). Somma attuale: {total_weight}"
        )

    try:
        response = supabase.table("copenhagen_zones").select("*").order("cpi_score", desc=True).execute()
        original_zones = response.data

        # Mappa della posizione iniziale baseline (1-based index)
        original_ranks = {zone["district_code"]: idx + 1 for idx, zone in enumerate(original_zones)}

        simulated_list = []
        for zone in original_zones:
            sim_score = compute_cpi(
                float(zone["waste_supply_score"]),
                int(zone["population_gen_z"]),
                float(zone["avg_income_dkk"]),
                float(zone["market_gap_score"]),
                w_supply=weights.weight_supply,
                w_demo=weights.weight_demographics,
                w_gap=weights.weight_market_gap
            )
            simulated_list.append({
                "name": zone["name"],
                "district_code": zone["district_code"],
                "original_cpi_score": zone["cpi_score"],
                "simulated_cpi_score": sim_score
            })

        # Ordina per il nuovo punteggio simulato
        simulated_list.sort(key=lambda x: x["simulated_cpi_score"], reverse=True)

        # Calcola la variazione di posizione (rank_change)
        final_results = []
        for new_rank, item in enumerate(simulated_list, start=1):
            old_rank = original_ranks[item["district_code"]]
            # Variazione: +2 significa che la zona è salita di 2 posizioni
            rank_change = old_rank - new_rank
            
            final_results.append(SimulatedZoneResult(
                name=item["name"],
                district_code=item["district_code"],
                original_cpi_score=item["original_cpi_score"],
                simulated_cpi_score=item["simulated_cpi_score"],
                rank_change=rank_change
            ))

        return CPISimulationResponse(
            status="success",
            applied_weights=weights,
            top_zone=final_results[0],
            results=final_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/csv")
def export_zones_csv():
    try:
        response = supabase.table("copenhagen_zones").select("*").order("cpi_score", desc=True).execute()
        zones = response.data

        if not zones:
            raise HTTPException(status_code=404, detail="No data available to export")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=zones[0].keys())
        writer.writeheader()
        writer.writerows(zones)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=copenhagen_recommerce_matrix.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))