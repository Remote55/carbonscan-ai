"""File upload endpoints — stub for Phase 1.

TODO Phase 1:
- LAS/LAZ direct upload to Supabase Storage (chunked via tus protocol)
- Photogrammetry photo upload (multipart, 30-50 images)
- Validation (file size, extension, EXIF for photos)
- Create Job record + push to Queue
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.analyze import AnalyzeResponse
from app.services.pipeline_runner import PipelineError, redact_operator_detail, run_pipeline
from app.services.upload_validation import read_upload_limited, validate_upload

router = APIRouter()
logger = logging.getLogger(__name__)


def _run_pipeline_on_bytes(data: bytes, ext: str) -> dict:
    """Persist bytes to a temp file, run the pipeline, clean up. Blocking — run
    in a threadpool from async endpoints."""
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
        tf.write(data)
        tmp_path = Path(tf.name)
    try:
        return run_pipeline(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_point_cloud(file: UploadFile = File(...)) -> AnalyzeResponse:
    """Upload a point-cloud file, run the full pipeline, return carbon results.

    Synchronous MVP (small files). Phase 2 moves heavy jobs to a queue + GPU worker.
    """
    max_bytes = (
        settings.TREEQ_DEMO_MAX_UPLOAD_SIZE_BYTES
        if settings.TREEQ_DEMO_MODE
        else settings.MAX_UPLOAD_SIZE_BYTES
    )
    data = await read_upload_limited(file, max_bytes)
    ext = validate_upload(file.filename, data)

    try:
        result = await run_in_threadpool(_run_pipeline_on_bytes, data, ext)
    except PipelineError as exc:
        logger.error("Pipeline execution failed: %s", redact_operator_detail(exc.operator_detail))
        raise HTTPException(status_code=502, detail=exc.public_message) from exc

    return AnalyzeResponse(**result)


@router.post("/las", status_code=501)
async def upload_las() -> dict[str, str]:
    """Direct .las/.laz upload to Supabase Storage. TODO Phase 1."""
    return {"message": "Not implemented — see TODO in upload.py"}


@router.post("/photos", status_code=501)
async def upload_photos() -> dict[str, str]:
    """Upload 30-50 photos for photogrammetry. TODO: implement."""
    return {"message": "Not implemented — see TODO in upload.py"}
