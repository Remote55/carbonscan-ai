"""Schemas for the synchronous point-cloud analyze endpoint."""

from pydantic import BaseModel, Field


class AnalyzeTree(BaseModel):
    """One detected tree with its carbon estimate."""

    tree_id: int
    species_sci: str | None = None
    dbh_cm: float
    height_m: float
    volume_m3: float | None = None
    biomass_kg: float | None = None
    carbon_kg: float | None = None
    co2eq_kg: float | None = None
    location: dict[str, float] = Field(default_factory=dict)
    point_count: int = 0


class AnalyzeSummary(BaseModel):
    """Plot-level totals."""

    total_trees: int
    total_carbon_kg: float
    total_co2eq_kg: float


class AnalyzeResponse(BaseModel):
    """Full pipeline result returned by POST /upload/analyze."""

    metadata: dict
    summary: AnalyzeSummary
    trees: list[AnalyzeTree]
