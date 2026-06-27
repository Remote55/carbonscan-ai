"""File upload endpoints — stub for Phase 1.

TODO Phase 1:
- LAS/LAZ direct upload to Supabase Storage (chunked via tus protocol)
- Photogrammetry photo upload (multipart, 30-50 images)
- Validation (file size, extension, EXIF for photos)
- Create Job record + push to Queue
"""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.analyze import AnalyzeResponse
from app.services.pipeline_runner import PipelineError, run_pipeline

router = APIRouter()

# Formats the ML pipeline can load (pipeline.field_eval.load_point_cloud)
_ANALYZE_EXTENSIONS = {".las", ".laz", ".ply", ".txt", ".xyz", ".csv"}


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
    ext = os.path.splitext((file.filename or "").lower())[1]
    if ext not in _ANALYZE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(_ANALYZE_EXTENSIONS)}",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413, detail=f"File too large (> {settings.MAX_UPLOAD_SIZE_MB} MB)"
        )

    try:
        result = await run_in_threadpool(_run_pipeline_on_bytes, data, ext)
    except PipelineError as exc:
        raise HTTPException(status_code=502, detail=f"Pipeline failed: {exc}") from exc

    return AnalyzeResponse(**result)


@router.post("/las", status_code=501)
async def upload_las() -> dict[str, str]:
    """Direct .las/.laz upload to Supabase Storage. TODO Phase 1."""
    return {"message": "Not implemented — see TODO in upload.py"}


@router.post("/photos", status_code=501)
async def upload_photos() -> dict[str, str]:
    """Upload 30-50 photos for photogrammetry. TODO: implement."""
    return {"message": "Not implemented — see TODO in upload.py"}
