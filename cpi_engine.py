def calculate_demographics_score(gen_z_pop: int, income: float) -> float:
    gen_z_norm = min(gen_z_pop / 15000.0, 1.0) * 10.0
    income_norm = min(income / 450000.0, 1.0) * 10.0
    return (gen_z_norm * 0.6) + (income_norm * 0.4)

def compute_cpi(
    waste_supply: float, 
    gen_z_pop: int, 
    income: float, 
    market_gap: float,
    w_supply: float = 0.40,
    w_demo: float = 0.35,
    w_gap: float = 0.25
) -> dict:
    # 1. Punteggi puri (da mostrare sul Radar Chart in modo stabile)
    supply_score = waste_supply
    demographics_score = calculate_demographics_score(gen_z_pop, income)
    gap_score = market_gap

    # 2. Punteggio CPI finale (influenzato dai cursori)
    cpi = (supply_score * w_supply) + (demographics_score * w_demo) + (gap_score * w_gap)
    
    # 3. Restituiamo un dizionario completo invece di un singolo float
    return {
        "cpi_score": round(cpi, 2),
        "supply_score": round(supply_score, 2),
        "demographics_score": round(demographics_score, 2),
        "market_gap_score": round(gap_score, 2)
    }