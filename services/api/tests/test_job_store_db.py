"""Integration tests for DbJobStore. Skips when no Postgres is reachable.

Self-provisions only the `users` + `jobs` tables (no PostGIS needed) so it runs
on the plain CI sidecar or any local Postgres. Set DATABASE_URL to enable.
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.job import Job
from app.models.user import User
from app.services.job_store import DbJobStore

pytestmark = pytest.mark.asyncio

DB_URL = os.getenv("DATABASE_URL", "")


@pytest.fixture
async def session():
    if not DB_URL:
        pytest.skip("DATABASE_URL not set — skipping DB integration test")
    engine = create_async_engine(DB_URL)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, tables=[User.__table__, Job.__table__])
            )
    except Exception as exc:  # DB not reachable
        await engine.dispose()
        pytest.skip(f"Postgres not reachable: {exc}")
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda c: Base.metadata.drop_all(c, tables=[Job.__table__, User.__table__])
        )
    await engine.dispose()


async def test_create_upserts_user_and_inserts_queued_job(session):
    store = DbJobStore(session)
    uid = uuid4()
    rec = await store.create(owner_id=uid, owner_email="stud@uni.ac.th", input_url="/tmp/x.las")
    assert rec.status == "queued"
    got = await store.get(rec.id)
    assert got is not None and got.user_id == uid


async def test_claim_next_is_exclusive_and_completes(session):
    store = DbJobStore(session)
    uid = uuid4()
    rec = await store.create(owner_id=uid, owner_email="stud@uni.ac.th", input_url="/tmp/x.las")

    claimed = await store.claim_next(worker_id="w1")
    assert claimed is not None and claimed.id == rec.id and claimed.status == "processing"
    # only one queued job existed
    assert await store.claim_next(worker_id="w1") is None

    await store.mark_completed(rec.id, result={"summary": {}}, total_trees=4, total_carbon_kg=50.0)
    done = await store.get(rec.id)
    assert done.status == "completed"
    assert done.total_trees_detected == 4
    assert done.result_json == {"summary": {}}
