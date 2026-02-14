from __future__ import annotations
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

SoilType = Literal["sandy", "loam", "clay"]
IrrigationType = Literal["drip", "sprinkler", "flood", "other"]

Constraint = Literal[
    "water_limit",
    "budget_cap",
    "organic_only",
    "labor_limited",
    "maximize_yield",
    "maximize_carbon",
]

Bucket = Literal["Low", "Med", "High"]
CostBucket = Literal["$", "$$", "$$$"]
SoilImpact = Literal["--", "-", "0", "+", "++"]

class GenerateRequest(BaseModel):
    crop: str = Field(..., examples=["tomato"])
    acres: float = Field(..., gt=0)
    soil_type: SoilType
    irrigation: IrrigationType
    location: str = Field(default="Davis, CA")
    constraints: List[Constraint] = Field(default_factory=list)

    # NEW: Only if you want optional fallback. Default False.
    allow_stub: bool = Field(default=False, description="If true, fallback to stub plans when LLM is unavailable.")


class Plan(BaseModel):
    key: Literal["water_saver", "yield_priority", "carbon_priority"]
    title: str
    summary: str
    practices: List[str]
    timeline: Dict[str, List[str]]  # pre_season / early / mid / late
    assumptions: List[str]
    risks: List[str]
    mitigations: List[str]

    # Filled by scoring step:
    water_use: Optional[Bucket] = None
    cost: Optional[CostBucket] = None
    soil_health: Optional[SoilImpact] = None
    risk: Optional[Bucket] = None

class ComparisonRow(BaseModel):
    plan_key: str
    title: str
    water_use: Bucket
    cost: CostBucket
    soil_health: SoilImpact
    risk: Bucket

class GenerateResponse(BaseModel):
    farm_profile: Dict[str, Any]
    constraints: List[Constraint]
    plans: List[Plan]
    comparison: List[ComparisonRow]
    recommendation: Dict[str, Any]
