"""HTTP tests for the async job endpoints — InMemory store + fake auth, no DB."""

from uuid import uuid4

import pytest

from app.api.deps import get_current_user, get_job_store
from app.main import app
from app.services.job_store import InMemoryJobStore
from app.worker import process_one

USER = {"id": str(uuid4()), "email": "student@uni.ac.th"}
OTHER = {"id": str(uuid4()), "email": "other@uni.ac.th"}

FAKE_RESULT = {
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
    "summary": {"total_trees": 2, "total_carbon_kg": 123.45, "total_co2eq_kg": 452.6},
    "trees": [],
}


@pytest.fixture
def store():
    s = InMemoryJobStore()
    app.dependency_overrides[get_job_store] = lambda: s
    app.dependency_overrides[get_current_user] = lambda: USER
    yield s
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_returns_202_and_queued_id(client, store):
    resp = await client.post(
        "/api/v1/jobs/analyze",
        files={"file": ("plot.las", b"dummy-bytes", "application/octet-stream")},
    )
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "queued"
    assert "id" in body


@pytest.mark.asyncio
async def test_submit_rejects_bad_extension(client, store):
    resp = await client.post(
        "/api/v1/jobs/analyze",
        files={"file": ("photo.jpg", b"x", "image/jpeg")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_job_returns_result_after_worker_runs(client, store):
    submit = await client.post(
        "/api/v1/jobs/analyze",
        files={"file": ("plot.las", b"dummy-bytes", "application/octet-stream")},
    )
    job_id = submit.json()["id"]

    # queued initially
    r1 = await client.get(f"/api/v1/jobs/{job_id}")
    assert r1.json()["status"] == "queued"

    # run the worker once against the same store
    await process_one(store, worker_id="w1", runner=lambda path: FAKE_RESULT)

    r2 = await client.get(f"/api/v1/jobs/{job_id}")
    body = r2.json()
    assert body["status"] == "completed"
    assert body["result"]["summary"]["total_trees"] == 2
    assert body["result"]["metadata"]["evidence_status"] == "baseline"


@pytest.mark.asyncio
async def test_get_other_users_job_is_forbidden(client, store):
    submit = await client.post(
        "/api/v1/jobs/analyze",
        files={"file": ("plot.las", b"dummy-bytes", "application/octet-stream")},
    )
    job_id = submit.json()["id"]
    app.dependency_overrides[get_current_user] = lambda: OTHER
    resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_missing_job_is_404(client, store):
    resp = await client.get(f"/api/v1/jobs/{uuid4()}")
    assert resp.status_code == 404
