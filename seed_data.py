import os
from database import supabase
from cpi_engine import compute_cpi

INITIAL_ZONES = [
    {
        "name": "Indre By",
        "district_code": "DK-1000",
        "population_gen_z": 4500,
        "avg_income_dkk": 380000,
        "waste_supply_score": 8.5,
        "market_gap_score": 6.0
    },
    {
        "name": "Nørrebro",
        "district_code": "DK-2200",
        "population_gen_z": 14200,
        "avg_income_dkk": 290000,
        "waste_supply_score": 9.5,
        "market_gap_score": 8.8
    },
    {
        "name": "Vesterbro / Kongens Enghave",
        "district_code": "DK-1600",
        "population_gen_z": 9800,
        "avg_income_dkk": 340000,
        "waste_supply_score": 8.2,
        "market_gap_score": 7.5
    },
    {
        "name": "Østerbro",
        "district_code": "DK-2100",
        "population_gen_z": 11000,
        "avg_income_dkk": 390000,
        "waste_supply_score": 7.0,
        "market_gap_score": 6.5
    },
    {
        "name": "Amager Vest",
        "district_code": "DK-2300",
        "population_gen_z": 10500,
        "avg_income_dkk": 320000,
        "waste_supply_score": 6.8,
        "market_gap_score": 8.0
    },
    {
        "name": "Amager Øst",
        "district_code": "DK-2300-E",
        "population_gen_z": 8900,
        "avg_income_dkk": 305000,
        "waste_supply_score": 6.5,
        "market_gap_score": 7.8
    },
    {
        "name": "Valby",
        "district_code": "DK-2500",
        "population_gen_z": 7800,
        "avg_income_dkk": 310000,
        "waste_supply_score": 6.0,
        "market_gap_score": 7.2
    },
    {
        "name": "Bispebjerg",
        "district_code": "DK-2400",
        "population_gen_z": 8200,
        "avg_income_dkk": 275000,
        "waste_supply_score": 7.5,
        "market_gap_score": 8.5
    },
    {
        "name": "Vanløse",
        "district_code": "DK-2720",
        "population_gen_z": 4900,
        "avg_income_dkk": 330000,
        "waste_supply_score": 5.2,
        "market_gap_score": 6.0
    },
    {
        "name": "Brønshøj-Husum",
        "district_code": "DK-2700",
        "population_gen_z": 5100,
        "avg_income_dkk": 295000,
        "waste_supply_score": 4.8,
        "market_gap_score": 6.2
    },
    {
        "name": "Frederiksberg",
        "district_code": "DK-2000",
        "population_gen_z": 13500,
        "avg_income_dkk": 410000,
        "waste_supply_score": 7.8,
        "market_gap_score": 5.5
    }
]

def run_seed():
    print("--> Avvio reset e seeding della tabella copenhagen_zones...")
    
    # 1. Pulizia tabella esistente
    supabase.table("copenhagen_zones").delete().neq("id", 0).execute()
    print("--> Tabella svuotata.")

    # 2. Inserimento e calcolo CPI baseline
    prepared_data = []
    for zone in INITIAL_ZONES:
        score = compute_cpi(
            zone["waste_supply_score"],
            zone["population_gen_z"],
            zone["avg_income_dkk"],
            zone["market_gap_score"]
        )
        zone["cpi_score"] = score
        prepared_data.append(zone)

    supabase.table("copenhagen_zones").insert(prepared_data).execute()
    print(f"--> Seeding completato con successo! Inserite {len(prepared_data)} zone.")

if __name__ == "__main__":
    run_seed()