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
