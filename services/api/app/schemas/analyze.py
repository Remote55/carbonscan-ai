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
    #: Bounds from the plausible wood density range, which the pipeline never
    #: measures, plus a sentence saying so. Optional because results stored by
    #: earlier pipeline versions do not carry them.
    co2eq_low_kg: float | None = None
    co2eq_high_kg: float | None = None
    uncertainty_basis: str | None = None
    #: The same tree costed through its taper volume rather than Chave, and how
    #: far apart the two models land. Both are functions of ρ·D²·H; neither has
    #: been checked against a tropical tree.
    co2eq_volume_route_kg: float | None = None
    method_disagreement: float | None = None
    #: RANSAC inlier ratio for the breast-height circle. Near 1.0 is a clean
    #: stem; the pipeline refuses anything below 0.20 outright.
    dbh_fit_quality: float | None = None
    #: How much of the crown the scan resolved into branch-shaped wood, 0-1.
    #: The crown is about 30% of a tree and is estimated rather than measured.
    crown_resolved_fraction: float | None = None
    location: dict[str, float] = Field(default_factory=dict)
    point_count: int = 0


class AnalyzeExcludedSegment(BaseModel):
    """A detected segment the pipeline could not measure, and why."""

    tree_id: int
    stage: Literal["wood_leaf", "qsm"]
    # Must track pipeline.main.ExcludedSegment. A code the pipeline can emit and
    # this Literal does not list fails validation at the API boundary, so the
    # whole response dies over one unmeasurable tree.
    reason_code: Literal["WOOD_EMPTY", "QSM_INVALID", "QSM_LOW_FIT_QUALITY"]


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
    #: Plot totals at the ends of the density range. Summed, not added in
    #: quadrature: on one site the density error is shared, not independent.
    total_co2eq_low_kg: float | None = None
    total_co2eq_high_kg: float | None = None


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
    #: Points in the uploaded file, and the share of them that was measured.
    #: The pipeline thins anything over 200,000 points, and n_input_points is
    #: the count AFTER that — true about the array, wrong about the file. These
    #: two say so. Optional so results stored by an earlier pipeline still
    #: deserialise, and None rather than a default, because "this run did not
    #: record it" and "nothing was discarded" are different claims.
    n_source_points: int | None = Field(default=None, ge=0)
    analysed_point_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
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
