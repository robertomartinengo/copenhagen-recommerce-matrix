from database import supabase
from cpi_engine import calculate_dynamic_cpi

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

POPULATION_MIN: int = min(int(z["population_gen_z"]) for z in INITIAL_ZONES)  # type: ignore
POPULATION_MAX: int = max(int(z["population_gen_z"]) for z in INITIAL_ZONES)  # type: ignore
INCOME_MIN: float = min(float(z["avg_income_dkk"]) for z in INITIAL_ZONES)  # type: ignore
INCOME_MAX: float = max(float(z["avg_income_dkk"]) for z in INITIAL_ZONES)  # type: ignore


def _normalise_0_10(value: float, vmin: float, vmax: float) -> float:
    """Normalizza un valore su scala 0-10 usando min-max. Se vmin==vmax restituisce 5.0."""
    if vmax == vmin:
        return 5.0
    return round((value - vmin) / (vmax - vmin) * 10.0, 2)


def compute_demographics_score(zone: dict) -> float:
    """Calcola il punteggio Demographics (0-10) da population_gen_z e avg_income_dkk.

    Formula (vedi D-016): 0.6 * gen_z_normalised + 0.4 * income_normalised.
    La normalizzazione è min-max sui valori osservati nelle 11 zone di Copenhagen.
    """
    gen_z_norm = _normalise_0_10(zone["population_gen_z"], POPULATION_MIN, POPULATION_MAX)
    income_norm = _normalise_0_10(zone["avg_income_dkk"], INCOME_MIN, INCOME_MAX)
    return round(0.6 * gen_z_norm + 0.4 * income_norm, 2)


def run_seed():
    print("--> Avvio reset e seeding della tabella copenhagen_zones...")
    
    # 1. Pulizia tabella esistente
    supabase.table("copenhagen_zones").delete().neq("id", 0).execute()
    print("--> Tabella svuotata.")

    # 2. Calcolo Demographics score per ogni zona (D-016)
    for zone in INITIAL_ZONES:
        zone["demographics_score"] = compute_demographics_score(zone)

    # 3. Inserimento e calcolo CPI baseline
    prepared_data = []
    for zone in INITIAL_ZONES:
        score = calculate_dynamic_cpi(zone, business_type="curated_vintage")["cpi_score"]
        zone["cpi_score"] = score
        prepared_data.append(zone)

    supabase.table("copenhagen_zones").insert(prepared_data).execute()
    print(f"--> Seeding completato con successo! Inserite {len(prepared_data)} zone.")

if __name__ == "__main__":
    run_seed()