"""Persist uploaded point clouds so the worker can read them later.

MVP: local filesystem shared between API + worker. Phase 3 replaces this with
Supabase Storage (upload here, worker downloads by object key).

Two things remove these files. The worker deletes the one it just finished with,
which covers every job that reaches a terminal state. `sweep_orphans` covers the
ones that never do — a job enqueued while no worker was running, a queue
abandoned, a crash between write and claim — because otherwise those stay on
disk forever and nothing ever looks at them again.
"""

import logging
import tempfile
import time
from pathlib import Path
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)

#: How long an upload may sit unclaimed before it is treated as abandoned.
#: Far longer than any legitimate queue wait - the pipeline subprocess itself
#: times out at 600 s - because the only job of this number is to stop
#: unbounded growth, not to reclaim space promptly.
ORPHAN_TTL_SECONDS = 24 * 60 * 60


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
    # Opportunistic, so there is no scheduler to deploy and nothing to forget to
    # start. It runs on the one event that grows the directory.
    sweep_orphans()
    return str(path)


def discard_job_input(path: str | Path) -> None:
    """Delete one job input. Safe to call twice, or on a path already gone.

    Refuses anything outside the upload directory: `input_url` is a column in a
    database row, and a delete driven by stored data should not be able to reach
    arbitrary paths if that row is ever wrong.
    """
    target = Path(path)
    root = job_upload_dir().resolve()
    try:
        resolved = target.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        logger.warning("refusing to delete job input outside the upload dir: %s", target)
        return
    resolved.unlink(missing_ok=True)


def sweep_orphans(*, ttl_seconds: float = ORPHAN_TTL_SECONDS) -> int:
    """Delete uploads older than the TTL. Returns how many went."""
    cutoff = time.time() - ttl_seconds
    removed = 0
    try:
        entries = list(job_upload_dir().iterdir())
    except OSError:
        return 0
    for entry in entries:
        try:
            if not entry.is_file() or entry.stat().st_mtime >= cutoff:
                continue
            entry.unlink(missing_ok=True)
            removed += 1
        except OSError:
            # Another worker got there first, or the file is locked. Neither is
            # worth failing an upload over.
            continue
    if removed:
        logger.info("swept %d abandoned job upload(s)", removed)
    return removed
