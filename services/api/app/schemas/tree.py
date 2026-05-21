"""Pydantic schemas for Tree."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GpsPoint(BaseModel):
    """GPS coordinate (WGS84)."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    elevation_m: float | None = None


class TreeBase(BaseModel):
    """Common tree fields."""

    species_name_th: str | None = None
    species_name_sci: str | None = None
    dbh_cm: float = Field(..., gt=0, description="Diameter at Breast Height (cm)")
    height_m: float = Field(..., gt=0, description="Total height (m)")
    location: GpsPoint


class TreeCreate(TreeBase):
    """Schema for creating a tree (called by ML worker)."""

    species_confidence: float | None = Field(None, ge=0, le=1)
    volume_m3: float | None = Field(None, gt=0)
    source_type: str = Field(..., pattern="^(lidar|photogrammetry|manual)$")
    scanned_at: datetime


class TreeOut(TreeBase):
    """Schema for tree response."""

    id: UUID
    species_confidence: float | None = None
    volume_m3: float | None = None
    biomass_kg: float | None = None
    carbon_kg: float | None = None
    co2eq_kg: float | None = None
    source_type: str
    scanned_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class TreeFilters(BaseModel):
    """Query parameters for filtering trees."""

    species: str | None = None
    lat: float | None = None
    lon: float | None = None
    radius_km: float | None = Field(None, gt=0, le=100)
    min_carbon_kg: float | None = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
