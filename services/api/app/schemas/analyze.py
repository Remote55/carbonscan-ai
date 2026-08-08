"""Schemas for the synchronous point-cloud analyze endpoint."""

from typing import Literal

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


class AnalyzeExcludedSegment(BaseModel):
    """A detected segment the pipeline could not measure, and why."""

    tree_id: int
    stage: Literal["wood_leaf", "qsm"]
    reason_code: Literal["WOOD_EMPTY", "QSM_INVALID"]


class AnalyzeDiagnostics(BaseModel):
    """Why the measured tree count differs from the detected tree count."""

    excluded_segments: list[AnalyzeExcludedSegment] = Field(default_factory=list)


class AnalyzeSummary(BaseModel):
    """Plot-level totals.

    The three count fields arrived with pipeline 0.4.0. They stay optional so
    async-job rows stored by 0.3.0 keep deserialising, and they are ``None``
    rather than ``0`` when absent so a caller cannot mistake an old result for
    one where nothing was excluded.
    """

    total_trees: int
    total_carbon_kg: float
    total_co2eq_kg: float
    detected_trees: int | None = None
    measured_trees: int | None = None
    excluded_trees: int | None = None


class AnalyzeMetadata(BaseModel):
    """Auditable identity and implementation details for one pipeline run."""

    pipeline_version: str
    git_commit: str
    git_dirty: bool
    wood_leaf_backend: str
    input_sha256: str = Field(min_length=64, max_length=64)
    checkpoint_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    algorithms: dict[str, str]
    evidence_status: str
    candidate_status: str
    n_input_points: int = Field(ge=0)
    status: str
    input_file: str | None = None


class AnalyzeResponse(BaseModel):
    """Full pipeline result returned by POST /upload/analyze."""

    metadata: AnalyzeMetadata
    summary: AnalyzeSummary
    trees: list[AnalyzeTree]
    diagnostics: AnalyzeDiagnostics | None = None
    #: Fetch at GET /upload/segmented/{id} to get the plot-wide PLY carrying the
    #: wood/leaf/ground label of every point - the same labels these numbers were
    #: measured from. None when the run produced no such file, which callers must
    #: handle rather than assume: the viewer then keeps showing the raw upload and
    #: has to say so instead of implying the colours are a result.
    segmented_cloud_id: str | None = None
