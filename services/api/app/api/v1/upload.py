"""Point-cloud upload and synchronous analysis.

Input is a point cloud from a scanner. A photogrammetry path was sketched here
and has been dropped: whether photographs of a real trunk yield enough points to
fit a circle at breast height was never established, so it promised a capability
nobody had shown was reachable.

TODO:
- LAS/LAZ direct upload to Supabase Storage (chunked via tus protocol)
- Create Job record + push to Queue
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.analyze import AnalyzeResponse
from app.services import segmented_cloud_store, species_catalogue
from app.services.pipeline_runner import PipelineError, redact_operator_detail, run_pipeline
from app.services.upload_validation import read_upload_limited, validate_upload

router = APIRouter()
logger = logging.getLogger(__name__)


def _run_pipeline_on_bytes(data: bytes, ext: str, species: str | None = None) -> dict:
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
        result = run_pipeline(tmp_path, segmented_ply_out=cloud_path, species=species)
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
async def analyze_point_cloud(
    file: UploadFile = File(...),
    species: str | None = Form(
        default=None,
        description=(
            "Scientific name, if known. Halves the carbon error: the wood "
            "density is otherwise assumed."
        ),
    ),
) -> AnalyzeResponse:
    """Upload a point-cloud file, run the full pipeline, return carbon results.

    Synchronous MVP (small files). Phase 2 moves heavy jobs to a queue + GPU worker.
    """
    # The smaller of the two, always. This route is unauthenticated and runs a
    # multi-minute subprocess, and ingestion buffers roughly twice the file, so
    # the 500 MB general limit was never a limit this endpoint could survive -
    # it applied only when demo mode was off, which is exactly the configuration
    # a public deployment runs. Demo mode may lower the cap; it may not raise it.
    max_bytes = min(
        settings.TREEQ_DEMO_MAX_UPLOAD_SIZE_BYTES, settings.MAX_UPLOAD_SIZE_BYTES
    )
    data = await read_upload_limited(file, max_bytes)
    ext = validate_upload(file.filename, data)

    # A name the catalogue does not know is refused rather than ignored. Falling
    # back to the default density would answer with a number that looks like it
    # used the species the caller asked for, and be 40% out without saying so.
    chosen = (species or "").strip() or None
    if chosen is not None and not species_catalogue.is_known(chosen):
        raise HTTPException(
            status_code=422,
            detail=f"Unknown species '{chosen}'. See GET /api/v1/upload/species.",
        )

    try:
        result = await run_in_threadpool(_run_pipeline_on_bytes, data, ext, chosen)
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


# There was a POST /photos here, returning 501 with "TODO: implement", for a
# photogrammetry path that has been dropped. Whether photogrammetry of a real
# trunk even yields enough points to fit a circle at breast height was never
# established, so the endpoint advertised a capability nobody had shown was
# reachable. This service takes point clouds from a scanner.


@router.get("/species")
async def list_species() -> dict[str, object]:
    """The species this deployment can cost, for a picker.

    Naming one replaces an assumed wood density with a measured one, which is
    the largest accuracy gain available at the cost of a single form field.
    `coefficients_verified` is false on every row today: naming a species buys
    its density, not its allometric equation, because none of those equations
    has been checked against the paper it cites.
    """
    catalogue = species_catalogue.load_species()
    return {
        "species": [
            {
                "name_sci": item.name_sci,
                "name_th": item.name_th,
                "name_en": item.name_en,
                "wood_density_kg_m3": item.wood_density,
                "coefficients_verified": item.coefficients_verified,
            }
            for item in sorted(catalogue.values(), key=lambda s: s.name_sci)
        ],
        "note": (
            "ไม่ระบุชนิดได้ ระบบจะใช้ความหนาแน่นไม้เขตร้อนมาตรฐาน "
            "ซึ่งเป็นแหล่งความคลาดเคลื่อนที่ใหญ่ที่สุดของค่าคาร์บอน"
        ),
    }
