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

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.analyze import AnalyzeResponse
from app.services import segmented_cloud_store
from app.services.pipeline_runner import PipelineError, redact_operator_detail, run_pipeline
from app.services.upload_validation import read_upload_limited, validate_upload

router = APIRouter()
logger = logging.getLogger(__name__)


def _run_pipeline_on_bytes(data: bytes, ext: str) -> dict:
    """Persist bytes to a temp file, run the pipeline, clean up. Blocking — run
    in a threadpool from async endpoints.

    Also asks the pipeline for the segmented cloud and registers it, so the
    viewer can show the wood/leaf separation these numbers came from instead of
    continuing to display the raw upload.
    """
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
        tf.write(data)
        tmp_path = Path(tf.name)
    cloud_id, cloud_path = segmented_cloud_store.store.reserve()
    try:
        result = run_pipeline(tmp_path, segmented_ply_out=cloud_path)
        # commit returns None when the pipeline wrote nothing, and the response
        # then carries no id. A missing picture is reported as missing.
        result["segmented_cloud_id"] = segmented_cloud_store.store.commit(cloud_id, cloud_path)
        return result
    except Exception:
        cloud_path.unlink(missing_ok=True)
        raise
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


@router.get("/segmented/{cloud_id}")
async def download_segmented_cloud(cloud_id: str) -> Response:
    """Return the segmented PLY an analysis produced.

    404 covers unknown, expired and malformed ids alike: the caller has no
    business learning which of the three it was, and the store treats anything
    that is not id-shaped as unknown rather than touching the filesystem.
    """
    data = segmented_cloud_store.store.get(cloud_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Segmented cloud not found or expired")

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={
            # The bytes never change under an id, but they do stop existing, so
            # let a client cache within the lifetime and not beyond it.
            "cache-control": "private, max-age=600",
            "content-disposition": 'attachment; filename="segmented.ply"',
        },
    )


@router.post("/las", status_code=501)
async def upload_las() -> dict[str, str]:
    """Direct .las/.laz upload to Supabase Storage. TODO Phase 1."""
    return {"message": "Not implemented — see TODO in upload.py"}


@router.post("/photos", status_code=501)
async def upload_photos() -> dict[str, str]:
    """Upload 30-50 photos for photogrammetry. TODO: implement."""
    return {"message": "Not implemented — see TODO in upload.py"}
