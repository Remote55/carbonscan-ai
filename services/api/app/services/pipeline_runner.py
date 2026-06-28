"""Run the ML pipeline out-of-process and return its JSON result.

The ML pipeline lives in ``services/ml`` with its own venv (heavy deps: numpy,
laspy, torch). The API stays lightweight by shelling out to that venv's CLI
(``pipeline.main process``) instead of importing it. Synchronous MVP — Phase 2
will move this behind a job queue + RunPod GPU worker.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from app.core.config import settings

# repo layout: services/api/app/services/pipeline_runner.py -> <repo>/services/ml
_DEFAULT_ML_DIR = Path(__file__).resolve().parents[3] / "ml"


class PipelineError(RuntimeError):
    """The ML pipeline subprocess failed."""


def _ml_dir() -> Path:
    return Path(settings.ML_DIR) if settings.ML_DIR else _DEFAULT_ML_DIR


def _ml_python() -> str:
    """Locate the ml venv interpreter (Windows or POSIX), else fall back."""
    if settings.ML_PYTHON:
        return settings.ML_PYTHON
    for rel in (".venv/Scripts/python.exe", ".venv/bin/python"):
        candidate = _ml_dir() / rel
        if candidate.exists():
            return str(candidate)
    return sys.executable


def run_pipeline(
    input_path: str | Path,
    *,
    backend: str = "tlsep",
    species: str | None = None,
    timeout: int = 600,
) -> dict:
    """Process a point-cloud file via the ML CLI; return the result JSON dict.

    Raises:
        PipelineError: if the subprocess exits non-zero or writes no output.
    """
    input_path = Path(input_path)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        out_json = Path(tf.name)
    try:
        cmd = [
            _ml_python(), "-m", "pipeline.main", "process",
            "--input", str(input_path), "--output", str(out_json),
            "--backend", backend,
        ]
        if species:
            cmd += ["--species", species]
        proc = subprocess.run(
            cmd, cwd=str(_ml_dir()), capture_output=True, text=True, timeout=timeout
        )
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "")[-600:]
            raise PipelineError(f"pipeline exited {proc.returncode}: {tail}")
        return json.loads(out_json.read_text(encoding="utf-8"))
    finally:
        out_json.unlink(missing_ok=True)
