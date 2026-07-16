from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.job import JobCreated, JobDetail


def test_job_created_minimal():
    j = JobCreated(id=uuid4(), status="queued", created_at=datetime.now(timezone.utc))
    assert j.status == "queued"


def test_job_detail_parses_embedded_result():
    result = {
        "metadata": {
            "pipeline_version": "0.3.0",
            "git_commit": "9d7b43c",
            "git_dirty": False,
            "wood_leaf_backend": "tlsep",
            "input_sha256": "a" * 64,
            "checkpoint_sha256": None,
            "algorithms": {"wood_leaf": "tlsep", "species": "stub"},
            "evidence_status": "baseline",
            "candidate_status": "candidate_not_evaluated",
            "n_input_points": 1000,
            "status": "ok",
        },
        "summary": {"total_trees": 1, "total_carbon_kg": 10.0, "total_co2eq_kg": 36.7},
        "trees": [],
    }
    d = JobDetail(
        id=uuid4(),
        status="completed",
        progress=100,
        total_trees_detected=1,
        total_carbon_kg=10.0,
        result=result,
        created_at=datetime.now(timezone.utc),
    )
    assert d.result is not None
    assert d.result.summary.total_trees == 1
    assert d.result.metadata.evidence_status == "baseline"
