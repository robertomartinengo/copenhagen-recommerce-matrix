# cpi_engine.py
from typing import Dict, TypedDict

class BusinessProfile(TypedDict):
    label: str
    weights: Dict[str, float]

BUSINESS_PROFILES: Dict[str, BusinessProfile] = {
    "vintage_premium": {
        "label": "Boutique / Lusso",
        "weights": {"waste": 0.2, "demo": 0.4, "gap": 0.4}
    },
    "kilo_sale": {
        "label": "Mercatino a Peso",
        "weights": {"waste": 0.5, "demo": 0.3, "gap": 0.2}
    },
    "upcycling": {
        "label": "Laboratorio Sartoriale",
        "weights": {"waste": 0.4, "demo": 0.2, "gap": 0.4}
    },
    "curated_vintage": {
        "label": "Pop-Up / Curated",
        "weights": {"waste": 0.33, "demo": 0.33, "gap": 0.34}
    }
}

def calculate_dynamic_cpi(zone_data: dict, business_type: str = "curated_vintage") -> dict:
    """Calcola il punteggio CPI dinamico pesato in base al modello di business selezionato."""
    profile = BUSINESS_PROFILES.get(business_type, BUSINESS_PROFILES["curated_vintage"])
    weights = profile["weights"]

    waste = float(zone_data.get("waste_supply_score", 5.0))
    demo = float(zone_data.get("demographics_score", zone_data.get("cpi_score", 5.0)))
    gap = float(zone_data.get("market_gap_score", 5.0))

    cpi = (waste * weights["waste"]) + (demo * weights["demo"]) + (gap * weights["gap"])

    return {
        "cpi_score": round(cpi, 2),
        "business_profile_used": business_type,
        "business_profile_label": profile["label"]
    }

def calculate_cpi(zone_data: dict, business_type: str = "curated_vintage") -> float:
    """Funzione di supporto/compatibilità."""
    return calculate_dynamic_cpi(zone_data, business_type)["cpi_score"]