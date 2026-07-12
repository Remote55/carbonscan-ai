"""Response schemas for async pipeline jobs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.analyze import AnalyzeResponse


class JobCreated(BaseModel):
    """Returned by POST /jobs/analyze (HTTP 202)."""

    id: UUID
    status: str
    created_at: datetime


class JobDetail(BaseModel):
    """Returned by GET /jobs/{id} and GET /jobs."""

    id: UUID
    status: str
    progress: int
    total_trees_detected: int | None = None
    total_carbon_kg: float | None = None
    result: AnalyzeResponse | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
