from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ZoneBase(BaseModel):
    name: str
    district_code: str
    population_gen_z: int
    avg_income_dkk: float
    waste_supply_score: float
    market_gap_score: float

class ZoneResponse(ZoneBase):
    id: int
    cpi_score: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CPICalculationResult(BaseModel):
    name: str
    cpi_score: float

class CPICalculationResponse(BaseModel):
    status: str
    updated_count: int
    top_zone: Optional[CPICalculationResult] = None
    results: list[CPICalculationResult]