from typing import Dict, Any

# Definizione dei profili di business e relative matrici di peso (somma = 1.0)
BUSINESS_PROFILES = {
    "vintage_premium": {
        "label": "Vintage Premium & Lusso",
        "weights": {
            "income": 0.40,
            "gap": 0.30,
            "demographics": 0.15,
            "waste": 0.15
        },
        "description": "Boutique ad alto scontrino medio. Richiede elevato potere d'acquisto e gap di mercato."
    },
    "kilo_sale": {
        "label": "Kilo Sale & Thrift Massivo",
        "weights": {
            "waste": 0.40,
            "demographics": 0.35,
            "gap": 0.15,
            "income": 0.10
        },
        "description": "Format ad alto volume. Richiede massima densita di Gen Z e continua fornitura di materiale usabile."
    },
    "upcycling": {
        "label": "Upcycling & Laboratorio Creativo",
        "weights": {
            "waste": 0.45,
            "demographics": 0.25,
            "gap": 0.20,
            "income": 0.10
        },
        "description": "Produzione e vendita di capi rilavorati. Richiede vicinanza ai punti di scarto e quartieri creativi."
    },
    "curated_vintage": {
        "label": "Curated Vintage & Pop-Up",
        "weights": {
            "demographics": 0.30,
            "gap": 0.30,
            "waste": 0.20,
            "income": 0.20
        },
        "description": "Format bilanciato e trendy. Ideale per concept store e boutique di quartiere."
    }
}


def _normalize_income_score(avg_income_dkk: float) -> float:
    """
    Normalizza il reddito medio DKK su una scala da 1.0 a 10.0.
    Baseline Copenhagen: Min ~200k DKK (5.0), Max ~450k DKK (10.0).
    """
    if not avg_income_dkk or avg_income_dkk <= 0:
        return 5.0
    score = ((avg_income_dkk - 200000) / (450000 - 200000)) * 5.0 + 5.0
    return max(1.0, min(10.0, score))


def calculate_custom_cpi(zone_data: Dict[str, Any], business_type: str = "curated_vintage") -> Dict[str, Any]:
    """
    Calcola il CPI dinamico e personalizzato per un dato distretto sulla base del modello di business.
    """
    profile = BUSINESS_PROFILES.get(business_type, BUSINESS_PROFILES["curated_vintage"])
    weights = profile["weights"]

    # Estrazione e normalizzazione indicatori
    waste_score = float(zone_data.get("waste_supply_score", 5.0))
    demo_score = float(zone_data.get("demographics_score", zone_data.get("cpi_score", 5.0)))
    gap_score = float(zone_data.get("market_gap_score", 5.0))
    
    raw_income = zone_data.get("avg_income_dkk", 300000)
    income_score = _normalize_income_score(float(raw_income) if raw_income else 300000)

    # Calcolo pesato del nuovo CPI (Scala 1.0 - 10.0)
    custom_cpi = (
        (waste_score * weights["waste"]) +
        (demo_score * weights["demographics"]) +
        (gap_score * weights["gap"]) +
        (income_score * weights["income"])
    )
    
    custom_cpi = round(max(1.0, min(10.0, custom_cpi)), 2)

    # Arricchisce il dizionario di output
    result = dict(zone_data)
    result["static_cpi_score"] = float(zone_data.get("cpi_score", custom_cpi))
    result["cpi_score"] = custom_cpi
    result["business_profile_used"] = business_type
    result["business_profile_label"] = profile["label"]
    
    return result


if __name__ == "__main__":
    # Test Locale rapido dell'algoritmo dinamico
    sample_zone = {
        "name": "Nørrebro",
        "cpi_score": 8.89,
        "waste_supply_score": 9.5,
        "demographics_score": 8.8,
        "market_gap_score": 8.8,
        "avg_income_dkk": 290000
    }

    print("--- TEST CALCOLO CPI DINAMICO SU NØRREBRO ---")
    for b_type in BUSINESS_PROFILES.keys():
        calc = calculate_custom_cpi(sample_zone, business_type=b_type)
        print(f"Modello: {calc['business_profile_label']:<35} -> CPI Personalizzato: {calc['cpi_score']:.2f}")