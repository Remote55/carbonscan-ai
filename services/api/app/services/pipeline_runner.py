"""Run the ML pipeline out-of-process and return its JSON result.

The ML pipeline lives in ``services/ml`` with its own venv (heavy deps: numpy,
laspy, torch). The API stays lightweight by shelling out to that venv's CLI
(``pipeline.main process``) instead of importing it. Synchronous MVP — Phase 2
will move this behind a job queue + RunPod GPU worker.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from app.core.config import settings

# repo layout: services/api/app/services/pipeline_runner.py -> <repo>/services/ml
_DEFAULT_ML_DIR = Path(__file__).resolve().parents[3] / "ml"


class PipelineError(RuntimeError):
    """The ML pipeline subprocess failed."""

    def __init__(
        self,
        *,
        public_message: str = "Pipeline execution failed",
        operator_detail: str = "",
    ) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.operator_detail = operator_detail


_ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/)(?:[^\s:]+[\\/])*[^\s:]*")


def redact_operator_detail(detail: str) -> str:
    """Remove absolute filesystem paths before writing operator diagnostics."""
    return _ABSOLUTE_PATH.sub("<path>", detail)


def _child_env() -> dict[str, str]:
    child_env = os.environ.copy()
    child_env.pop("TREEQ_DEMO_TOKEN", None)
    child_env.pop("SUPABASE_SERVICE_KEY", None)
    return child_env


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


def probe_pipeline_runtime(timeout: int = 30) -> str:
    """Import the ML orchestrator in its runtime and return its pipeline version."""
    cmd = [
        _ml_python(),
        "-c",
        "from pipeline.main import PIPELINE_VERSION; print(PIPELINE_VERSION)",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(_ml_dir()),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_child_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PipelineError(operator_detail=f"pipeline readiness probe failed: {exc}") from exc
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-600:]
        raise PipelineError(
            operator_detail=f"pipeline readiness probe exited {proc.returncode}: {tail}"
        )
    version = proc.stdout.strip()
    if not version:
        raise PipelineError(operator_detail="pipeline readiness probe returned no version")
    return version


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
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(_ml_dir()),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=_child_env(),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PipelineError(operator_detail=f"pipeline subprocess failed: {exc}") from exc
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "")[-600:]
            raise PipelineError(
                operator_detail=f"pipeline exited {proc.returncode}: {tail}"
            )
        try:
            return json.loads(out_json.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PipelineError(operator_detail=f"pipeline output was invalid: {exc}") from exc
    finally:
        out_json.unlink(missing_ok=True)
