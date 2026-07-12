"""Tests for Job model + in-memory store."""

from uuid import uuid4

import pytest

from app.models.job import Job, JobStatus, JobType
from app.services.job_store import InMemoryJobStore


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


@pytest.mark.asyncio
async def test_create_then_get():
    store = InMemoryJobStore()
    uid = uuid4()
    rec = await store.create(owner_id=uid, owner_email="a@b.co", input_url="/tmp/x.las")
    assert rec.status == "queued"
    assert rec.user_id == uid
    got = await store.get(rec.id)
    assert got is not None and got.id == rec.id


@pytest.mark.asyncio
async def test_claim_next_transitions_to_processing_and_is_exclusive():
    store = InMemoryJobStore()
    rec = await store.create(owner_id=uuid4(), owner_email="a@b.co", input_url="/tmp/x.las")
    claimed = await store.claim_next(worker_id="w1")
    assert claimed is not None and claimed.id == rec.id
    assert claimed.status == "processing"
    # nothing left to claim
    assert await store.claim_next(worker_id="w1") is None


@pytest.mark.asyncio
async def test_mark_completed_stores_result_and_summary():
    store = InMemoryJobStore()
    rec = await store.create(owner_id=uuid4(), owner_email="a@b.co", input_url="/tmp/x.las")
    await store.claim_next(worker_id="w1")
    await store.mark_completed(rec.id, result={"summary": {}}, total_trees=3, total_carbon_kg=99.0)
    got = await store.get(rec.id)
    assert got.status == "completed"
    assert got.total_trees_detected == 3
    assert got.result_json == {"summary": {}}


@pytest.mark.asyncio
async def test_mark_failed_stores_error():
    store = InMemoryJobStore()
    rec = await store.create(owner_id=uuid4(), owner_email="a@b.co", input_url="/tmp/x.las")
    await store.claim_next(worker_id="w1")
    await store.mark_failed(rec.id, error_message="boom", error_traceback="trace")
    got = await store.get(rec.id)
    assert got.status == "failed"
    assert got.error_message == "boom"


@pytest.mark.asyncio
async def test_list_for_user_filters_by_owner():
    store = InMemoryJobStore()
    u1, u2 = uuid4(), uuid4()
    await store.create(owner_id=u1, owner_email="a@b.co", input_url="/x")
    await store.create(owner_id=u2, owner_email="c@d.co", input_url="/y")
    mine = await store.list_for_user(u1)
    assert len(mine) == 1 and mine[0].user_id == u1
