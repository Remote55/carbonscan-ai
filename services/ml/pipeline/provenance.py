"""Auditable provenance and evidence-gated model promotion."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

ALGORITHM_MAP = {
    "ground_segmentation": "percentile_grid",
    "height_normalization": "knn_idw",
    "chm": "max_z_morphology",
    "tree_segmentation": "watershed",
    "wood_leaf": "tlsep",
    "qsm": "ransac_dbh_maxz_height_taper_volume",
    "species": "stub",
    "allometric": "species_db_or_chave_fallback",
}


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 hex digest for bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Hash a file without interpreting its contents."""
    return sha256_bytes(Path(path).read_bytes())


def hash_points(points: np.ndarray) -> str:
    """Hash XYZ values in a stable little-endian float64 representation."""
    stable = np.asarray(points, dtype="<f8", order="C")
    if stable.ndim != 2 or stable.shape[1] != 3:
        raise ValueError(f"Expected points (N, 3), got {stable.shape}")
    return sha256_bytes(stable.tobytes(order="C"))


def normalized_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    """Copy evidence while excluding the explicitly non-deterministic runtime block."""
    payload = json.loads(json.dumps(evidence, ensure_ascii=False))
    payload.pop("runtime", None)
    return payload


def normalized_sha256(evidence: dict[str, Any]) -> str:
    """Hash deterministic evidence fields using canonical JSON."""
    encoded = json.dumps(
        normalized_payload(evidence),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256_bytes(encoded)


def resolve_git_commit(repo_root: str | Path) -> str:
    """Return the commit that owns a pipeline run."""
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def checkpoint_identity(model_path: str | Path | None) -> str | None:
    """Return a checkpoint hash, or None for a non-model baseline."""
    if model_path is None:
        return None
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {path}")
    return sha256_file(path)


@dataclass(frozen=True)
class EvaluationMetrics:
    """Metrics required for a downstream-safe model comparison."""

    wood_iou: float
    dbh_mae_cm: float
    height_mae_m: float
    volume_mape_pct: float
    measurable_trees: int


@dataclass(frozen=True)
class PromotionEvidence:
    """All evidence inputs required to consider model promotion."""

    baseline: EvaluationMetrics
    candidate: EvaluationMetrics | None
    checkpoint_sha256: str | None
    training_provenance_complete: bool
    independent_real_test: bool
    reproducible_command: bool


@dataclass(frozen=True)
class PromotionDecision:
    """Machine-readable, fail-closed promotion decision."""

    promote: bool
    status: str
    failed_criteria: tuple[str, ...]
    baseline: dict[str, Any]
    candidate: dict[str, Any] | None


def _is_sha256(value: str | None) -> bool:
    if value is None or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def evaluate_promotion(evidence: PromotionEvidence) -> PromotionDecision:
    """Promote only when every identity, evaluation, and downstream gate passes."""
    if evidence.candidate is None:
        return PromotionDecision(
            promote=False,
            status="candidate_not_evaluated",
            failed_criteria=("candidate_metrics",),
            baseline=asdict(evidence.baseline),
            candidate=None,
        )

    candidate = evidence.candidate
    baseline = evidence.baseline
    checks = {
        "checkpoint_sha256": _is_sha256(evidence.checkpoint_sha256),
        "training_provenance": evidence.training_provenance_complete,
        "independent_real_test": evidence.independent_real_test,
        "reproducible_command": evidence.reproducible_command,
        "wood_iou_improves": candidate.wood_iou > baseline.wood_iou,
        "dbh_mae_non_regression": candidate.dbh_mae_cm <= baseline.dbh_mae_cm,
        "height_mae_non_regression": candidate.height_mae_m <= baseline.height_mae_m,
        "volume_mape_non_regression": candidate.volume_mape_pct <= baseline.volume_mape_pct,
        "measurable_tree_count": candidate.measurable_trees >= baseline.measurable_trees,
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return PromotionDecision(
        promote=not failed,
        status="promoted" if not failed else "rejected",
        failed_criteria=failed,
        baseline=asdict(baseline),
        candidate=asdict(candidate),
    )
