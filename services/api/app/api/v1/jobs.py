"""Async pipeline job endpoints.

POST /jobs/analyze  — submit a point cloud; returns 202 + job id (queued).
GET  /jobs/{id}     — status + result (owner-only).
GET  /jobs          — list the caller's jobs.

Heavy ML runs in a separate worker (app/worker.py), never in the request.
"""

from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser, JobStoreDep
from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.job import JobCreated, JobDetail
from app.services.job_input import save_job_input
from app.services.job_store import JobRecord
from app.services.upload_validation import read_upload_limited, validate_upload

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
    # Smaller of the two, in every mode — same reasoning as the sync route.
    # This one is at least authenticated, but the file still lands on the same
    # disk and is read by the same pipeline.
    max_bytes = min(
        settings.TREEQ_DEMO_MAX_UPLOAD_SIZE_BYTES, settings.MAX_UPLOAD_SIZE_BYTES
    )
    data = await read_upload_limited(file, max_bytes)
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
