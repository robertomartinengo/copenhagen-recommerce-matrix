def calculate_demographics_score(gen_z_pop: int, income: float) -> float:
    # Normalizzazione basata sui parametri della regione metropolitana
    gen_z_norm = min(gen_z_pop / 15000.0, 1.0) * 10.0
    income_norm = min(income / 450000.0, 1.0) * 10.0
    return (gen_z_norm * 0.6) + (income_norm * 0.4)

def compute_cpi(waste_supply: float, gen_z_pop: int, income: float, market_gap: float) -> float:
    supply_score = waste_supply
    demographics_score = calculate_demographics_score(gen_z_pop, income)
    gap_score = market_gap

    cpi = (supply_score * 0.40) + (demographics_score * 0.35) + (gap_score * 0.25)
    return round(cpi, 2)