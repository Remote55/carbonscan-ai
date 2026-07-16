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
