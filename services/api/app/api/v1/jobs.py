"""Job status endpoints — stub for Phase 1.

TODO Phase 1:
- GET /jobs/{id} — status, progress, result
- GET /jobs — list (paginated, filtered)
- POST /jobs/{id}/cancel
- WS /jobs/{id}/ws — real-time progress
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/{job_id}", status_code=501)
async def get_job(job_id: str) -> dict[str, str]:
    """Get job status by ID. TODO: implement."""
    return {"message": f"Not implemented — job_id={job_id}"}


@router.get("/", status_code=501)
async def list_jobs() -> dict[str, str]:
    """List jobs for current user. TODO: implement."""
    return {"message": "Not implemented — see TODO in jobs.py"}
