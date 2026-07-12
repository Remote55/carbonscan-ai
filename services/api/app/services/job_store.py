"""Job persistence abstraction.

`JobStore` is the single interface the API endpoints and the worker use.
`InMemoryJobStore` backs unit tests and local demos; `DbJobStore` (Task 8)
backs production against Postgres. A future `PgmqJobStore` could replace
`DbJobStore` behind this same interface with no changes to callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from app.models.job import JobStatus, JobType


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobRecord:
    """Plain snapshot of a job — decouples callers from the ORM."""

    id: UUID
    user_id: UUID
    type: str
    status: str
    input_url: str
    progress: int = 0
    total_trees_detected: int | None = None
    total_carbon_kg: float | None = None
    result_json: dict | None = None
    error_message: str | None = None
    output_url: str | None = None
    created_at: datetime = field(default_factory=_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobStore(Protocol):
    async def create(
        self,
        *,
        owner_id: UUID,
        owner_email: str,
        input_url: str,
        job_type: str = JobType.PIPELINE.value,
    ) -> JobRecord: ...

    async def get(self, job_id: UUID) -> JobRecord | None: ...

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> list[JobRecord]: ...

    async def claim_next(self, *, worker_id: str) -> JobRecord | None: ...

    async def mark_completed(
        self, job_id: UUID, *, result: dict, total_trees: int, total_carbon_kg: float
    ) -> None: ...

    async def mark_failed(
        self, job_id: UUID, *, error_message: str, error_traceback: str | None = None
    ) -> None: ...


class InMemoryJobStore:
    """Dict-backed JobStore for tests + local single-process demos."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, JobRecord] = {}

    async def create(
        self,
        *,
        owner_id: UUID,
        owner_email: str,
        input_url: str,
        job_type: str = JobType.PIPELINE.value,
    ) -> JobRecord:
        rec = JobRecord(
            id=uuid4(),
            user_id=owner_id,
            type=job_type,
            status=JobStatus.QUEUED.value,
            input_url=input_url,
        )
        self._jobs[rec.id] = rec
        return rec

    async def get(self, job_id: UUID) -> JobRecord | None:
        return self._jobs.get(job_id)

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> list[JobRecord]:
        rows = [r for r in self._jobs.values() if r.user_id == user_id]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows[:limit]

    async def claim_next(self, *, worker_id: str) -> JobRecord | None:
        queued = sorted(
            (r for r in self._jobs.values() if r.status == JobStatus.QUEUED.value),
            key=lambda r: r.created_at,
        )
        if not queued:
            return None
        rec = queued[0]
        rec.status = JobStatus.PROCESSING.value
        rec.started_at = _now()
        return rec

    async def mark_completed(
        self, job_id: UUID, *, result: dict, total_trees: int, total_carbon_kg: float
    ) -> None:
        rec = self._jobs[job_id]
        rec.status = JobStatus.COMPLETED.value
        rec.progress = 100
        rec.result_json = result
        rec.total_trees_detected = total_trees
        rec.total_carbon_kg = total_carbon_kg
        rec.completed_at = _now()

    async def mark_failed(
        self, job_id: UUID, *, error_message: str, error_traceback: str | None = None
    ) -> None:
        rec = self._jobs[job_id]
        rec.status = JobStatus.FAILED.value
        rec.error_message = error_message
        rec.completed_at = _now()
