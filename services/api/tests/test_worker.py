"""Worker tests — no DB, no ML. Fake runner + InMemoryJobStore."""

from uuid import uuid4

import pytest

from app.services.job_store import InMemoryJobStore
from app.worker import process_one

FAKE_RESULT = {
    "metadata": {"status": "ok"},
    "summary": {"total_trees": 2, "total_carbon_kg": 123.45, "total_co2eq_kg": 452.6},
    "trees": [],
}


@pytest.mark.asyncio
async def test_process_one_completes_job():
    store = InMemoryJobStore()
    rec = await store.create(owner_id=uuid4(), owner_email="a@b.co", input_url="/tmp/x.las")

    did = await process_one(store, worker_id="w1", runner=lambda path: FAKE_RESULT)

    assert did is True
    got = await store.get(rec.id)
    assert got.status == "completed"
    assert got.total_trees_detected == 2
    assert got.total_carbon_kg == 123.45


@pytest.mark.asyncio
async def test_process_one_marks_failed_on_runner_error():
    store = InMemoryJobStore()
    rec = await store.create(owner_id=uuid4(), owner_email="a@b.co", input_url="/tmp/x.las")

    def boom(path):
        raise RuntimeError("pipeline exploded")

    did = await process_one(store, worker_id="w1", runner=boom)

    assert did is True
    got = await store.get(rec.id)
    assert got.status == "failed"
    assert "pipeline exploded" in got.error_message


@pytest.mark.asyncio
async def test_process_one_returns_false_when_idle():
    store = InMemoryJobStore()
    assert await process_one(store, worker_id="w1", runner=lambda path: FAKE_RESULT) is False
