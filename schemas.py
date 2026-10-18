from pydantic import BaseModel, Field
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

# Nuovi schemi per la simulazione "What-If"
class CPISimulationRequest(BaseModel):
    weight_supply: float = Field(0.40, ge=0.0, le=1.0, description="Peso per la fornitura di rifiuti/tessile")
    weight_demographics: float = Field(0.35, ge=0.0, le=1.0, description="Peso per Gen Z e reddito medio")
    weight_market_gap: float = Field(0.25, ge=0.0, le=1.0, description="Peso per il vuoto di mercato")

class SimulatedZoneResult(BaseModel):
    name: str
    district_code: str
    original_cpi_score: float
    simulated_cpi_score: float
    rank_change: int

class CPISimulationResponse(BaseModel):
    status: str
    applied_weights: CPISimulationRequest
    top_zone: SimulatedZoneResult
    results: list[SimulatedZoneResult]