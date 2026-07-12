"""Tests for Job model + in-memory store."""

from app.models.job import Job, JobStatus, JobType


def test_job_status_values_match_db_check_constraint():
    # These MUST equal the CHECK constraint in migration 0001.
    assert {s.value for s in JobStatus} == {
        "queued",
        "processing",
        "completed",
        "failed",
        "cancelled",
    }
    assert {t.value for t in JobType} == {"las_upload", "photogrammetry", "pipeline"}


def test_job_model_maps_jobs_table():
    assert Job.__tablename__ == "jobs"
    assert "result_json" in Job.__table__.columns
    assert "user_id" in Job.__table__.columns
