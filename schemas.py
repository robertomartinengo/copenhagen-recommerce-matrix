from pydantic import BaseModel

class ZoneBase(BaseModel):
    name: str
    district_code: str
    population_gen_z: int
    avg_income_dkk: float
    waste_supply_score: float
    market_gap_score: float