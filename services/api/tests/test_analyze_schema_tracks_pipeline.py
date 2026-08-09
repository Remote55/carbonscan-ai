"""The analyze schema has to keep up with the pipeline it describes.

The API runs the ML pipeline as a subprocess in another virtualenv, so nothing
at runtime forces the two to agree. A reason code the pipeline emits and this
service does not list fails Pydantic validation at the boundary, and the whole
response dies over one tree that could not be measured.

That is not hypothetical: QSM_LOW_FIT_QUALITY was added to the pipeline and this
schema kept the old two-value Literal. So the check reads the pipeline's own
source rather than a copy of the list.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import get_args

import pytest

from app.schemas.analyze import AnalyzeExcludedSegment

PIPELINE_MAIN = (
    Path(__file__).resolve().parents[3] / "services" / "ml" / "pipeline" / "main.py"
)

needs_pipeline = pytest.mark.skipif(
    not PIPELINE_MAIN.exists(), reason="ML service not checked out"
)


def _literal_values(source: str, class_name: str, field: str) -> set[str]:
    """Pull `field: Literal[...]` out of `class_name` without importing it."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name == class_name):
            continue
        for stmt in node.body:
            if (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and stmt.target.id == field
                and isinstance(stmt.annotation, ast.Subscript)
            ):
                elts = stmt.annotation.slice
                items = elts.elts if isinstance(elts, ast.Tuple) else [elts]
                return {e.value for e in items if isinstance(e, ast.Constant)}
    raise AssertionError(f"{class_name}.{field} not found — did the pipeline rename it?")


@needs_pipeline
def test_every_pipeline_exclusion_code_is_accepted_here():
    emitted = _literal_values(
        PIPELINE_MAIN.read_text(encoding="utf-8"), "ExcludedSegment", "reason_code"
    )
    accepted = set(get_args(AnalyzeExcludedSegment.model_fields["reason_code"].annotation))
    assert emitted, "parsed no codes at all — the parser is broken, not the schema"
    assert emitted <= accepted, (
        f"the pipeline can emit {sorted(emitted - accepted)}, which this API rejects"
    )


@needs_pipeline
def test_every_stage_the_pipeline_reports_is_accepted_here():
    emitted = _literal_values(
        PIPELINE_MAIN.read_text(encoding="utf-8"), "ExcludedSegment", "stage"
    )
    accepted = set(get_args(AnalyzeExcludedSegment.model_fields["stage"].annotation))
    assert emitted <= accepted, f"unhandled stages: {sorted(emitted - accepted)}"


@needs_pipeline
def test_the_schema_does_not_promise_codes_the_pipeline_cannot_produce():
    """The other direction. A stale extra value is harmless to callers but means
    nobody has looked at this pairing in a while, so it is worth a nudge."""
    emitted = _literal_values(
        PIPELINE_MAIN.read_text(encoding="utf-8"), "ExcludedSegment", "reason_code"
    )
    accepted = set(get_args(AnalyzeExcludedSegment.model_fields["reason_code"].annotation))
    assert accepted <= emitted, (
        f"{sorted(accepted - emitted)} is documented here but the pipeline never emits it"
    )


def test_a_low_fit_quality_exclusion_deserialises():
    segment = AnalyzeExcludedSegment(
        tree_id=7, stage="qsm", reason_code="QSM_LOW_FIT_QUALITY"
    )
    assert segment.reason_code == "QSM_LOW_FIT_QUALITY"
