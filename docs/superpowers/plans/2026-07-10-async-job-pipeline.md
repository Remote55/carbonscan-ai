# Async Job Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **STATUS: Phase 2 blueprint — NOT scheduled for immediate implementation.** Written 2026-07-10 as the design deliverable for production-review finding #1 ("`/analyze` runs heavy compute synchronously"). Execute after the NSC report deadline unless priorities change.

**Goal:** Turn point-cloud analysis into an asynchronous job: the API accepts an upload, returns a `job_id` immediately (HTTP 202), and a separate worker process runs the ML pipeline and writes the result back — so heavy compute never blocks an HTTP request and can't be killed by a proxy timeout.

**Architecture:** A `jobs` row is the unit of work (the table already exists from migration `0001`). `POST /api/v1/jobs/analyze` saves the upload, inserts a `queued` job, returns 202. A `JobStore` abstraction (in-memory for tests, Postgres for prod) owns all state transitions; the Postgres impl claims work atomically with `SELECT … FOR UPDATE SKIP LOCKED`. A standalone worker (`python -m app.worker`) polls the store, runs the existing `run_pipeline` subprocess in a threadpool, and marks the job `completed`/`failed`. The existing synchronous `POST /upload/analyze` stays untouched for the live demo.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, asyncpg, Postgres, Pydantic v2, pytest + pytest-asyncio. No new runtime dependencies.

---

## Key Design Decisions (read before starting)

1. **The `jobs` table already exists** (`services/api/alembic/versions/0001_initial_schema.py`). Its status CHECK constraint allows exactly `queued | processing | completed | failed | cancelled`, and its `type` CHECK allows `las_upload | photogrammetry | pipeline`. **We MUST reuse these exact strings** — do not invent `running`/`succeeded`. Analyze jobs use `type='pipeline'`.
2. **Only one schema change is needed:** add a `result_json JSONB` column to `jobs` (migration `0002`) to hold the full per-tree `AnalyzeResponse`. The row's existing `total_trees_detected` / `total_carbon_kg` columns hold the summary for cheap listing.
3. **DB-as-queue, not PGMQ/Redis.** Claiming via `FOR UPDATE SKIP LOCKED` on the `jobs` table needs no extra extension or broker, works on the plain Postgres that CI already runs, and is trivially testable. The `config.py` comment mentioning Supabase PGMQ is superseded by this decision — a `PgmqJobStore` could later replace `DbJobStore` behind the same `JobStore` interface with zero API/worker changes. (Note the stale comment in Task 9.)
4. **Auth is included** because the `jobs.user_id` column is `NOT NULL` with an FK to `users.id`; a job must have an owner. We reuse the existing `CurrentUser` dependency (Supabase-verified). `DbJobStore.create` upserts the Supabase user into `users` first (this also removes the `NotImplementedError` in `sync_user_to_db`, review finding #6). **Rate-limiting is out of scope** (review finding #2, deferred).
5. **Input handoff for the MVP is a local file path** stored in `jobs.input_url`. This assumes the worker shares a filesystem with the API (same host / same volume). Cross-host object storage (Supabase Storage) is documented as the Phase 3 upgrade — see Task 9.
6. **CI does not run migrations** (`.github/workflows/ci-api.yml` runs `pytest` directly against the sidecar Postgres with no `alembic upgrade`). Therefore: all endpoint/worker/store unit tests use the in-memory store and need no DB; the one DB integration test self-provisions its two tables (`users`, `jobs`) via `Base.metadata.create_all` and `skip`s when no database is reachable. Neither `users` nor `jobs` needs PostGIS, so this runs on any Postgres.

---

## File Structure

**Create:**
- `services/api/app/models/job.py` — `Job` ORM model + `JobStatus`/`JobType` enums (maps the existing table).
- `services/api/alembic/versions/0002_job_result_json.py` — adds `jobs.result_json JSONB`.
- `services/api/app/schemas/job.py` — `JobCreated`, `JobDetail` response schemas.
- `services/api/app/services/upload_validation.py` — shared extension/size validation (DRY with `upload.py`).
- `services/api/app/services/job_input.py` — save upload bytes to the job upload dir.
- `services/api/app/services/job_store.py` — `JobRecord`, `JobStore` Protocol, `InMemoryJobStore`, `DbJobStore`.
- `services/api/app/worker.py` — `process_one`, `run_forever`, `__main__` entrypoint.
- `services/api/tests/test_upload_validation.py`
- `services/api/tests/test_job_store_inmemory.py`
- `services/api/tests/test_worker.py`
- `services/api/tests/test_jobs_api.py`
- `services/api/tests/test_job_store_db.py` (integration, `skipif` no DB)
- `services/api/docs/WORKER_RUNBOOK.md` (or `docs/ml/…` — see Task 9)

**Modify:**
- `services/api/app/core/config.py` — add `JOB_UPLOAD_DIR`.
- `services/api/app/models/__init__.py` — register `Job` (so Alembic + `create_all` see it).
- `services/api/app/api/deps.py` — add `get_job_store` + `JobStoreDep`.
- `services/api/app/api/v1/jobs.py` — replace the 501 stubs with real endpoints.
- `services/api/app/api/v1/upload.py` — use the shared validation helper (behavior unchanged).

---

## Task 1: Shared upload validation + config

**Files:**
- Create: `services/api/app/services/upload_validation.py`
- Modify: `services/api/app/core/config.py` (add `JOB_UPLOAD_DIR` after the File Upload block, ~line 73)
- Modify: `services/api/app/api/v1/upload.py` (reuse the helper)
- Test: `services/api/tests/test_upload_validation.py`

- [ ] **Step 1: Write the failing test**

```python
# services/api/tests/test_upload_validation.py
"""Unit tests for the shared upload validation helper."""

import pytest
from fastapi import HTTPException

from app.services.upload_validation import ANALYZE_EXTENSIONS, validate_upload


def test_accepts_known_extension_and_returns_ext():
    assert validate_upload("plot.LAS", b"some-bytes") == ".las"


def test_rejects_unknown_extension():
    with pytest.raises(HTTPException) as exc:
        validate_upload("photo.jpg", b"x")
    assert exc.value.status_code == 400


def test_rejects_empty_file():
    with pytest.raises(HTTPException) as exc:
        validate_upload("plot.las", b"")
    assert exc.value.status_code == 400


def test_rejects_oversize_file(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)
    with pytest.raises(HTTPException) as exc:
        validate_upload("plot.las", b"too-big")
    assert exc.value.status_code == 413


def test_all_known_extensions_present():
    assert ANALYZE_EXTENSIONS == {".las", ".laz", ".ply", ".txt", ".xyz", ".csv"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_upload_validation.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.upload_validation'`

- [ ] **Step 3: Create the helper**

```python
# services/api/app/services/upload_validation.py
"""Shared validation for point-cloud uploads (used by /upload and /jobs)."""

import os

from fastapi import HTTPException

from app.core.config import settings

# Formats the ML pipeline can load (pipeline.field_eval.load_point_cloud)
ANALYZE_EXTENSIONS = {".las", ".laz", ".ply", ".txt", ".xyz", ".csv"}


def validate_upload(filename: str | None, data: bytes) -> str:
    """Validate a point-cloud upload; return its lowercased extension.

    Raises HTTPException (400/413) on bad extension, empty, or oversize input.
    """
    ext = os.path.splitext((filename or "").lower())[1]
    if ext not in ANALYZE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ANALYZE_EXTENSIONS)}",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413, detail=f"File too large (> {settings.MAX_UPLOAD_SIZE_MB} MB)"
        )
    return ext
```

- [ ] **Step 4: Add `JOB_UPLOAD_DIR` to config**

In `services/api/app/core/config.py`, immediately after the `ALLOWED_IMAGE_EXTENSIONS` line (~line 73), add:

```python
    # Where POST /jobs/analyze persists uploads for the worker to read.
    # Empty = <system temp>/carbonscan-jobs. Must be shared between API + worker.
    JOB_UPLOAD_DIR: str = ""
```

- [ ] **Step 5: Refactor `upload.py` to use the helper (behavior unchanged)**

In `services/api/app/api/v1/upload.py`, replace the inline validation in `analyze_point_cloud`. Change the imports near the top to add:

```python
from app.services.upload_validation import validate_upload
```

Then replace the body of `analyze_point_cloud` from the `ext = os.path.splitext(...)` block through the size check with:

```python
    data = await file.read()
    ext = validate_upload(file.filename, data)
```

(Delete the now-unused `_ANALYZE_EXTENSIONS` constant and the three `raise HTTPException` blocks it replaces. Keep `import os` only if still used elsewhere — it is not, so remove it.)

- [ ] **Step 6: Run the new + existing upload tests**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_upload_validation.py tests/test_upload_analyze.py -v --no-cov`
Expected: PASS (all). The existing `test_analyze_rejects_bad_extension` still passes because behavior is identical.

- [ ] **Step 7: Commit**

```bash
git add services/api/app/services/upload_validation.py services/api/app/core/config.py services/api/app/api/v1/upload.py services/api/tests/test_upload_validation.py
git commit -m "refactor(api): extract shared upload validation + add JOB_UPLOAD_DIR"
```

---

## Task 2: `Job` ORM model + `result_json` migration

**Files:**
- Create: `services/api/app/models/job.py`
- Modify: `services/api/app/models/__init__.py`
- Create: `services/api/alembic/versions/0002_job_result_json.py`
- Test: `services/api/tests/test_job_store_inmemory.py` is added later; this task is verified by import + a model smoke test below.

- [ ] **Step 1: Write the failing test**

```python
# append to services/api/tests/test_job_store_inmemory.py  (create the file)
"""Tests for Job model + in-memory store."""

from app.models.job import Job, JobStatus, JobType


def test_job_status_values_match_db_check_constraint():
    # These MUST equal the CHECK constraint in migration 0001.
    assert {s.value for s in JobStatus} == {
        "queued", "processing", "completed", "failed", "cancelled"
    }
    assert {t.value for t in JobType} == {"las_upload", "photogrammetry", "pipeline"}


def test_job_model_maps_jobs_table():
    assert Job.__tablename__ == "jobs"
    assert "result_json" in Job.__table__.columns
    assert "user_id" in Job.__table__.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_store_inmemory.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models.job'`

- [ ] **Step 3: Create the model**

```python
# services/api/app/models/job.py
"""Job model — async pipeline processing.

Maps the existing `jobs` table (alembic 0001) plus the `result_json` column
added in 0002. Lifecycle: queued -> processing -> completed | failed.
The status/type string values MUST match the CHECK constraints in 0001.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    LAS_UPLOAD = "las_upload"
    PHOTOGRAMMETRY = "photogrammetry"
    PIPELINE = "pipeline"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    # plot_id has an FK to plots.id in the DB, but the MVP doesn't use plots.
    # Map it as a plain column so tests can create just users+jobs.
    plot_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=JobStatus.QUEUED.value
    )
    input_url: Mapped[str] = mapped_column(Text, nullable=False)
    output_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_trees_detected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_carbon_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gpu_seconds_used: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # added in 0002
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Job {self.id} {self.type} {self.status}>"
```

- [ ] **Step 4: Register the model**

Replace `services/api/app/models/__init__.py` contents with:

```python
"""SQLAlchemy ORM models.

Models are registered automatically when imported. Make sure to import all
models in alembic/env.py for autogenerate to detect them.
"""

from app.models.job import Job
from app.models.tree import Tree
from app.models.user import User

__all__ = ["Job", "Tree", "User"]
```

- [ ] **Step 5: Create the migration**

```python
# services/api/alembic/versions/0002_job_result_json.py
"""add jobs.result_json for full pipeline output

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-10
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("result_json", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "result_json")
```

- [ ] **Step 6: Run the model tests**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_store_inmemory.py -v --no-cov`
Expected: PASS (the two model tests). Store tests are added in Task 4.

- [ ] **Step 7: Commit**

```bash
git add services/api/app/models/job.py services/api/app/models/__init__.py services/api/alembic/versions/0002_job_result_json.py services/api/tests/test_job_store_inmemory.py
git commit -m "feat(api): add Job model + result_json migration (0002)"
```

---

## Task 3: Job response schemas

**Files:**
- Create: `services/api/app/schemas/job.py`
- Test: covered by API tests in Task 7; add a construction smoke test here.

- [ ] **Step 1: Write the failing test**

```python
# services/api/tests/test_job_schemas.py
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.job import JobCreated, JobDetail


def test_job_created_minimal():
    j = JobCreated(id=uuid4(), status="queued", created_at=datetime.now(timezone.utc))
    assert j.status == "queued"


def test_job_detail_parses_embedded_result():
    result = {
        "metadata": {"status": "ok"},
        "summary": {"total_trees": 1, "total_carbon_kg": 10.0, "total_co2eq_kg": 36.7},
        "trees": [],
    }
    d = JobDetail(
        id=uuid4(), status="completed", progress=100,
        total_trees_detected=1, total_carbon_kg=10.0,
        result=result, created_at=datetime.now(timezone.utc),
    )
    assert d.result is not None
    assert d.result.summary.total_trees == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_schemas.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.schemas.job'`

- [ ] **Step 3: Create the schemas**

```python
# services/api/app/schemas/job.py
"""Response schemas for async pipeline jobs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.analyze import AnalyzeResponse


class JobCreated(BaseModel):
    """Returned by POST /jobs/analyze (HTTP 202)."""

    id: UUID
    status: str
    created_at: datetime


class JobDetail(BaseModel):
    """Returned by GET /jobs/{id} and GET /jobs."""

    id: UUID
    status: str
    progress: int
    total_trees_detected: int | None = None
    total_carbon_kg: float | None = None
    result: AnalyzeResponse | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
```

- [ ] **Step 4: Run the test**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_schemas.py -v --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/api/app/schemas/job.py services/api/tests/test_job_schemas.py
git commit -m "feat(api): add JobCreated + JobDetail schemas"
```

---

## Task 4: `JobStore` abstraction + `InMemoryJobStore`

**Files:**
- Create: `services/api/app/services/job_store.py` (JobRecord, JobStore Protocol, InMemoryJobStore; DbJobStore added in Task 8)
- Test: `services/api/tests/test_job_store_inmemory.py` (extend the file from Task 2)

- [ ] **Step 1: Write the failing test** (append to `tests/test_job_store_inmemory.py`)

```python
from uuid import uuid4

import pytest

from app.services.job_store import InMemoryJobStore


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
    await store.mark_completed(
        rec.id, result={"summary": {}}, total_trees=3, total_carbon_kg=99.0
    )
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_store_inmemory.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'InMemoryJobStore'`

- [ ] **Step 3: Create the store module**

```python
# services/api/app/services/job_store.py
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
```

- [ ] **Step 4: Run the tests**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_store_inmemory.py -v --no-cov`
Expected: PASS (model tests + 5 store tests)

- [ ] **Step 5: Commit**

```bash
git add services/api/app/services/job_store.py services/api/tests/test_job_store_inmemory.py
git commit -m "feat(api): JobStore abstraction + InMemoryJobStore"
```

---

## Task 5: Job input persistence helper

**Files:**
- Create: `services/api/app/services/job_input.py`
- Test: `services/api/tests/test_job_input.py`

- [ ] **Step 1: Write the failing test**

```python
# services/api/tests/test_job_input.py
from pathlib import Path

from app.services.job_input import job_upload_dir, save_job_input


def test_save_job_input_writes_file_with_ext(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "JOB_UPLOAD_DIR", str(tmp_path))
    path = save_job_input(b"point-bytes", ".las")
    p = Path(path)
    assert p.exists()
    assert p.suffix == ".las"
    assert p.read_bytes() == b"point-bytes"
    assert p.parent == tmp_path


def test_job_upload_dir_defaults_to_temp(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "JOB_UPLOAD_DIR", "")
    d = job_upload_dir()
    assert d.name == "carbonscan-jobs"
    assert d.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_input.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.job_input'`

- [ ] **Step 3: Create the helper**

```python
# services/api/app/services/job_input.py
"""Persist uploaded point clouds so the worker can read them later.

MVP: local filesystem shared between API + worker. Phase 3 replaces this with
Supabase Storage (upload here, worker downloads by object key).
"""

import tempfile
from pathlib import Path
from uuid import uuid4

from app.core.config import settings


def job_upload_dir() -> Path:
    base = (
        Path(settings.JOB_UPLOAD_DIR)
        if settings.JOB_UPLOAD_DIR
        else Path(tempfile.gettempdir()) / "carbonscan-jobs"
    )
    base.mkdir(parents=True, exist_ok=True)
    return base


def save_job_input(data: bytes, ext: str) -> str:
    """Write bytes to a uniquely-named file in the job upload dir; return path."""
    path = job_upload_dir() / f"{uuid4().hex}{ext}"
    path.write_bytes(data)
    return str(path)
```

- [ ] **Step 4: Run the test**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_input.py -v --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/api/app/services/job_input.py services/api/tests/test_job_input.py
git commit -m "feat(api): job input persistence helper"
```

---

## Task 6: Worker — `process_one` + `run_forever`

**Files:**
- Create: `services/api/app/worker.py`
- Test: `services/api/tests/test_worker.py`

- [ ] **Step 1: Write the failing test**

```python
# services/api/tests/test_worker.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_worker.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.worker'`

- [ ] **Step 3: Create the worker**

```python
# services/api/app/worker.py
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
    except Exception as exc:  # noqa: BLE001 — worker must never crash on one bad job
        await store.mark_failed(
            job.id, error_message=str(exc), error_traceback=traceback.format_exc()
        )
    return True


async def run_forever(poll_interval: float = 2.0) -> None:
    """Poll the DB for queued jobs forever. Import DB bits lazily so unit tests
    (which use InMemoryJobStore) never require a database."""
    from app.core.database import AsyncSessionLocal
    from app.services.job_store import DbJobStore

    worker_id = socket.gethostname()
    print(f"⚙️  worker {worker_id} started (poll={poll_interval}s)")
    while True:
        async with AsyncSessionLocal() as session:
            did = await process_one(DbJobStore(session), worker_id=worker_id)
        if not did:
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(run_forever())
```

- [ ] **Step 4: Run the tests**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_worker.py -v --no-cov`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add services/api/app/worker.py services/api/tests/test_worker.py
git commit -m "feat(api): async job worker (process_one + run_forever)"
```

---

## Task 7: Job endpoints + store dependency

**Files:**
- Modify: `services/api/app/api/deps.py` (add `get_job_store` + `JobStoreDep`)
- Modify: `services/api/app/api/v1/jobs.py` (replace stubs)
- Test: `services/api/tests/test_jobs_api.py`

- [ ] **Step 1: Write the failing test**

```python
# services/api/tests/test_jobs_api.py
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
    "metadata": {"status": "ok"},
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
async def test_get_job_returns_result_after_worker_runs(client, store, monkeypatch):
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_jobs_api.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'get_job_store'`

- [ ] **Step 3: Add the store dependency**

Append to `services/api/app/api/deps.py`:

```python
from app.services.job_store import DbJobStore, JobStore


async def get_job_store(db: DbSession) -> JobStore:
    """Provide the production Postgres-backed job store."""
    return DbJobStore(db)


JobStoreDep = Annotated[JobStore, Depends(get_job_store)]
```

(`Annotated` and `Depends` are already imported at the top of `deps.py`; `DbSession` is already defined there.)

- [ ] **Step 4: Replace the jobs endpoints**

Replace the entire contents of `services/api/app/api/v1/jobs.py` with:

```python
"""Async pipeline job endpoints.

POST /jobs/analyze  — submit a point cloud; returns 202 + job id (queued).
GET  /jobs/{id}     — status + result (owner-only).
GET  /jobs          — list the caller's jobs.

Heavy ML runs in a separate worker (app/worker.py), never in the request.
"""

from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser, JobStoreDep
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.job import JobCreated, JobDetail
from app.services.job_input import save_job_input
from app.services.job_store import JobRecord
from app.services.upload_validation import validate_upload

router = APIRouter()


def _to_detail(rec: JobRecord) -> JobDetail:
    return JobDetail(
        id=rec.id,
        status=rec.status,
        progress=rec.progress,
        total_trees_detected=rec.total_trees_detected,
        total_carbon_kg=rec.total_carbon_kg,
        result=rec.result_json,
        error_message=rec.error_message,
        created_at=rec.created_at,
        started_at=rec.started_at,
        completed_at=rec.completed_at,
    )


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED, response_model=JobCreated)
async def submit_analyze_job(
    user: CurrentUser,
    store: JobStoreDep,
    file: UploadFile = File(...),
) -> JobCreated:
    """Accept an upload, enqueue a pipeline job, return immediately."""
    data = await file.read()
    ext = validate_upload(file.filename, data)
    input_path = save_job_input(data, ext)
    rec = await store.create(
        owner_id=UUID(user["id"]),
        owner_email=user["email"],
        input_url=input_path,
    )
    return JobCreated(id=rec.id, status=rec.status, created_at=rec.created_at)


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: UUID, user: CurrentUser, store: JobStoreDep) -> JobDetail:
    rec = await store.get(job_id)
    if rec is None:
        raise NotFoundError("Job not found")
    if rec.user_id != UUID(user["id"]):
        raise ForbiddenError("This job belongs to another user")
    return _to_detail(rec)


@router.get("/", response_model=list[JobDetail])
async def list_jobs(user: CurrentUser, store: JobStoreDep) -> list[JobDetail]:
    recs = await store.list_for_user(UUID(user["id"]))
    return [_to_detail(r) for r in recs]
```

- [ ] **Step 5: Run the API tests**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_jobs_api.py -v --no-cov`
Expected: PASS (5 tests)

- [ ] **Step 6: Run the whole suite to check nothing regressed**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest --no-cov -q`
Expected: PASS (all prior tests + the new ones). `test_job_store_db.py` does not exist yet.

- [ ] **Step 7: Commit**

```bash
git add services/api/app/api/deps.py services/api/app/api/v1/jobs.py services/api/tests/test_jobs_api.py
git commit -m "feat(api): async job endpoints (submit/get/list) with owner auth"
```

---

## Task 8: `DbJobStore` (Postgres, SKIP LOCKED) + integration test

**Files:**
- Modify: `services/api/app/services/job_store.py` (add `DbJobStore`)
- Test: `services/api/tests/test_job_store_db.py` (integration; skips without a DB)

- [ ] **Step 1: Write the failing integration test**

```python
# services/api/tests/test_job_store_db.py
"""Integration tests for DbJobStore. Skips when no Postgres is reachable.

Self-provisions only the `users` + `jobs` tables (no PostGIS needed) so it runs
on the plain CI sidecar or any local Postgres. Set DATABASE_URL to enable.
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.job import Job  # noqa: F401 — registers table
from app.models.user import User  # noqa: F401 — registers table
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
                lambda c: Base.metadata.create_all(
                    c, tables=[User.__table__, Job.__table__]
                )
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_store_db.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'DbJobStore'` (import happens before the skip fixture, so this fails rather than skips — that is what we want at this step).

- [ ] **Step 3: Add `DbJobStore` to `job_store.py`**

Add these imports at the top of `services/api/app/services/job_store.py`:

```python
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
```

Then append this class at the end of the file:

```python
class DbJobStore:
    """Postgres-backed JobStore. Claims work with FOR UPDATE SKIP LOCKED so
    multiple worker processes can run safely against one database."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    @staticmethod
    def _to_record(job: Job) -> JobRecord:
        return JobRecord(
            id=job.id,
            user_id=job.user_id,
            type=job.type,
            status=job.status,
            input_url=job.input_url,
            progress=job.progress,
            total_trees_detected=job.total_trees_detected,
            total_carbon_kg=job.total_carbon_kg,
            result_json=job.result_json,
            error_message=job.error_message,
            output_url=job.output_url,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    async def create(
        self,
        *,
        owner_id: UUID,
        owner_email: str,
        input_url: str,
        job_type: str = JobType.PIPELINE.value,
    ) -> JobRecord:
        # Ensure the Supabase user exists locally (jobs.user_id FK -> users.id).
        # Also resolves review finding #6 (sync_user_to_db was NotImplemented).
        await self._s.execute(
            text(
                "INSERT INTO users (id, email) VALUES (:id, :email) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": owner_id, "email": owner_email},
        )
        job = Job(
            user_id=owner_id,
            type=job_type,
            status=JobStatus.QUEUED.value,
            input_url=input_url,
            progress=0,
        )
        self._s.add(job)
        await self._s.flush()
        rec = self._to_record(job)
        await self._s.commit()
        return rec

    async def get(self, job_id: UUID) -> JobRecord | None:
        job = await self._s.get(Job, job_id)
        return self._to_record(job) if job else None

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> list[JobRecord]:
        stmt = (
            select(Job)
            .where(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        rows = (await self._s.execute(stmt)).scalars().all()
        return [self._to_record(j) for j in rows]

    async def claim_next(self, *, worker_id: str) -> JobRecord | None:
        row = (
            await self._s.execute(
                text(
                    """
                    UPDATE jobs
                       SET status = 'processing', started_at = now(),
                           worker_id = :wid, progress = 0
                     WHERE id = (
                         SELECT id FROM jobs
                          WHERE status = 'queued'
                          ORDER BY created_at
                          FOR UPDATE SKIP LOCKED
                          LIMIT 1
                     )
                    RETURNING id
                    """
                ),
                {"wid": worker_id},
            )
        ).first()
        await self._s.commit()
        if row is None:
            return None
        job = await self._s.get(Job, row[0])
        return self._to_record(job)

    async def mark_completed(
        self, job_id: UUID, *, result: dict, total_trees: int, total_carbon_kg: float
    ) -> None:
        job = await self._s.get(Job, job_id)
        if job is None:
            return
        job.status = JobStatus.COMPLETED.value
        job.progress = 100
        job.result_json = result
        job.total_trees_detected = total_trees
        job.total_carbon_kg = total_carbon_kg
        job.completed_at = _now()
        await self._s.commit()

    async def mark_failed(
        self, job_id: UUID, *, error_message: str, error_traceback: str | None = None
    ) -> None:
        job = await self._s.get(Job, job_id)
        if job is None:
            return
        job.status = JobStatus.FAILED.value
        job.error_message = error_message
        job.error_traceback = error_traceback
        job.completed_at = _now()
        await self._s.commit()
```

- [ ] **Step 4: Run the integration test**

Local (no DB): Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest tests/test_job_store_db.py -v --no-cov`
Expected: SKIPPED (2 skipped) when `DATABASE_URL` is unset or Postgres is down.

With a DB (matches CI): Run: `cd services/api && DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/carbonscan_test" ./.venv/Scripts/python.exe -m pytest tests/test_job_store_db.py -v --no-cov`
Expected: PASS (2 tests) — requires a running Postgres with that DB.

- [ ] **Step 5: Run the full suite**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest --no-cov -q`
Expected: PASS (DB test skips locally). In CI (Postgres sidecar present) it runs and passes.

- [ ] **Step 6: Commit**

```bash
git add services/api/app/services/job_store.py services/api/tests/test_job_store_db.py
git commit -m "feat(api): DbJobStore with FOR UPDATE SKIP LOCKED claim"
```

---

## Task 9: Runbook, docs, and stale-comment cleanup

**Files:**
- Create: `services/api/docs/WORKER_RUNBOOK.md`
- Modify: `services/api/app/core/config.py` (fix the stale PGMQ queue comment, ~line 67-68)
- Modify: `services/api/app/services/supabase.py` (note the store now upserts users)

- [ ] **Step 1: Write the runbook**

```markdown
# Async Job Worker — Runbook

CarbonScan processes point clouds asynchronously so the API never blocks on
heavy ML. This doc covers running and deploying the worker.

## Flow
1. Client `POST /api/v1/jobs/analyze` (multipart file, Bearer token).
2. API validates, saves the upload to `JOB_UPLOAD_DIR`, inserts a `queued`
   job, returns **202** `{id, status, created_at}`.
3. The worker claims the job (`FOR UPDATE SKIP LOCKED`), runs the pipeline,
   marks it `completed` (result in `jobs.result_json`) or `failed`.
4. Client polls `GET /api/v1/jobs/{id}` until `status` is terminal.

## Run locally
```bash
cd services/api
# 1. apply migrations (needs Postgres + PostGIS for the full schema)
alembic upgrade head
# 2. API
uvicorn app.main:app --reload
# 3. worker (separate terminal) — shares JOB_UPLOAD_DIR + DATABASE_URL with API
python -m app.worker
```

## Config
- `JOB_UPLOAD_DIR` — dir shared by API + worker (default `<temp>/carbonscan-jobs`).
- `DATABASE_URL` — same Postgres for API + worker.
- `ML_DIR` / `ML_PYTHON` — override ML venv auto-detection if needed.

## Deploy (Phase 2 → 3)
- **Phase 2 (single host):** API + worker on the same box/volume; the local
  `JOB_UPLOAD_DIR` handoff works. Run 1+ workers (`python -m app.worker`).
- **Phase 3 (scale-out):** replace `job_input.save_job_input` with Supabase
  Storage upload and have the worker download by object key. Then the worker
  can run anywhere (e.g. RunPod GPU). Swap `DbJobStore` for a `PgmqJobStore`
  only if DB-as-queue contention becomes a bottleneck — same `JobStore` API.

## Known limits (MVP)
- No progress streaming (`progress` stays 0→100); add stage updates later.
- No ret/cancel endpoint yet (`cancelled` status exists in the schema).
- Rate limiting not wired (review finding #2) — add before public exposure.
```

- [ ] **Step 2: Fix the stale queue comment in config.py**

In `services/api/app/core/config.py`, replace the two-line `# --- Queue ---` comment block (~line 67-68) with:

```python
    # --- Queue ---
    # Jobs use the `jobs` table itself as the queue (claimed via
    # SELECT ... FOR UPDATE SKIP LOCKED in DbJobStore). No Redis/PGMQ needed.
    # See services/api/docs/WORKER_RUNBOOK.md.
```

- [ ] **Step 3: Note the resolved user-sync in supabase.py**

In `services/api/app/services/supabase.py`, replace the `raise NotImplementedError(...)` line in `sync_user_to_db` with a docstring note (do not change behavior of callers — nothing calls it now):

```python
    # NOTE: user upsert now happens in DbJobStore.create (INSERT ... ON CONFLICT).
    # This standalone helper is kept as a documented no-op until a dedicated
    # /me sync flow needs it; wire it from a DbSession dependency then.
    return None
```

- [ ] **Step 4: Verify docs build / suite still green**

Run: `cd services/api && ./.venv/Scripts/python.exe -m pytest --no-cov -q && ruff check .`
Expected: tests PASS, ruff clean.

- [ ] **Step 5: Commit**

```bash
git add services/api/docs/WORKER_RUNBOOK.md services/api/app/core/config.py services/api/app/services/supabase.py
git commit -m "docs(api): worker runbook + fix stale queue/user-sync comments"
```

---

## Self-Review

**Spec coverage vs finding #1** ("`/analyze` runs heavy compute synchronously; needs enqueue → job_id → worker → poll"):
- Enqueue + immediate 202 → Task 7 (`submit_analyze_job`). ✅
- `job_id` returned → `JobCreated` (Task 3, 7). ✅
- Worker processes out-of-band → Task 6. ✅
- Poll for status/result → `GET /jobs/{id}` (Task 7). ✅
- No proxy-timeout risk → request no longer waits on `run_pipeline`. ✅
- Concurrency-safe claiming → `FOR UPDATE SKIP LOCKED` (Task 8). ✅
- Owner auth (required by `jobs.user_id`) → Task 7 + user upsert Task 8. ✅ (Rate-limiting explicitly deferred — finding #2.)

**Placeholder scan:** No TBD/TODO-as-implementation; every code step is complete. The only `TODO`-like text is inside the runbook's "Known limits", which is intentional documentation. ✅

**Type consistency:** `JobRecord` fields are identical across `InMemoryJobStore`, `DbJobStore._to_record`, and `_to_detail`. Status strings come from the `JobStatus` enum everywhere and match the 0001 CHECK constraint (`queued/processing/completed/failed/cancelled`). `store.create(owner_id, owner_email, input_url)`, `claim_next(worker_id=...)`, `mark_completed(result, total_trees, total_carbon_kg)`, `mark_failed(error_message, error_traceback)` signatures match between the Protocol, both impls, and all call sites (worker + endpoints). ✅

**Scope check:** One subsystem (async job processing). No unrelated refactoring beyond the DRY validation extraction (Task 1) and two comment fixes (Task 9), both of which serve this feature. ✅
