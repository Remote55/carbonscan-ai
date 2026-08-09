"""Async job worker: claim queued jobs, run the ML pipeline, store results.

Run:  python -m app.worker
Each iteration claims one job atomically (DbJobStore uses SELECT ... FOR UPDATE
SKIP LOCKED), runs the existing subprocess pipeline in a threadpool, and marks
the job completed/failed. Safe to run multiple instances against one DB.
"""

from __future__ import annotations

import asyncio
import socket
import traceback
from collections.abc import Callable

from starlette.concurrency import run_in_threadpool

from app.services.job_input import discard_job_input
from app.services.job_store import JobStore
from app.services.pipeline_runner import run_pipeline


async def process_one(
    store: JobStore,
    *,
    worker_id: str = "worker",
    runner: Callable[..., dict] = run_pipeline,
) -> bool:
    """Claim and process at most one job. Return True if one was processed."""
    job = await store.claim_next(worker_id=worker_id)
    if job is None:
        return False
    try:
        result = await run_in_threadpool(runner, job.input_url)
        summary = result.get("summary", {})
        await store.mark_completed(
            job.id,
            result=result,
            total_trees=int(summary.get("total_trees", 0)),
            total_carbon_kg=float(summary.get("total_carbon_kg", 0.0)),
        )
    except Exception as exc:
        await store.mark_failed(
            job.id, error_message=str(exc), error_traceback=traceback.format_exc()
        )
    finally:
        # Both outcomes are terminal - nothing retries a failed job - so the
        # upload has no reader left either way. Nothing deleted these, so an
        # instance accumulated every point cloud ever submitted until the disk
        # filled. Removal must not turn a completed job into a failed one, hence
        # the swallow: the result is already recorded by this point.
        try:
            discard_job_input(job.input_url)
        except OSError:
            pass
    return True


async def run_forever(poll_interval: float = 2.0) -> None:
    """Poll the DB for queued jobs forever. Import DB bits lazily so unit tests
    (which use InMemoryJobStore) never require a database."""
    from app.core.database import AsyncSessionLocal
    from app.services.job_store import DbJobStore

    worker_id = socket.gethostname()
    print(f"worker {worker_id} started (poll={poll_interval}s)")
    while True:
        async with AsyncSessionLocal() as session:
            did = await process_one(DbJobStore(session), worker_id=worker_id)
        if not did:
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(run_forever())
