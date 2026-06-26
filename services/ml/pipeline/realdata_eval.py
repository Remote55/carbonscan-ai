"""Zero-shot real wood/leaf IoU evaluation (spec 2026-06-26).

Runs the existing wood/leaf segmenter on real labelled TLS trees and reports
per-class IoU. Dataset-specific parsing is isolated in the two loaders; the
eval core is dataset-agnostic.

Classes: WOOD = 0, LEAF = 1 (matches pipeline.wood_leaf_separation).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pipeline.field_eval import load_point_cloud
from training.metrics import iou_score

_NO_DECIMATION = 10**12  # pass as max_points to load every point


def load_labelled_cloud(
    path: str | Path, *, label_col: int, wood_labels: Sequence[float]
) -> tuple[np.ndarray, np.ndarray]:
    """Load XYZ + a per-point wood/leaf label column (Wan-style datasets).

    Args:
        path: whitespace- (.txt/.xyz) or comma- (.csv) separated file
        label_col: column index holding the class label
        wood_labels: label values that mean wood; everything else is leaf

    Returns:
        (points (N,3) float64, gt (N,) uint8 in {0=wood, 1=leaf})
    """
    path = Path(path)
    delimiter = "," if path.suffix.lower() == ".csv" else None
    arr = np.atleast_2d(np.loadtxt(path, delimiter=delimiter))
    points = arr[:, :3].astype(np.float64)
    labels = arr[:, label_col]
    gt = np.where(np.isin(labels, np.asarray(wood_labels, dtype=labels.dtype)), 0, 1)
    return points, gt.astype(np.uint8)


def derive_labels_from_woodonly(
    full_path: str | Path, wood_only_path: str | Path, tol: float = 1e-3
) -> tuple[np.ndarray, np.ndarray]:
    """Derive per-point wood/leaf labels by matching against a wood-only cloud.

    Shivalik provides ground truth as a separate file containing only the wood
    points. A full-tree point within `tol` (metres) of any wood-only point is
    labelled wood (0); the rest are leaf (1). Matching uses XYZ only (avoids the
    zero-intensity quirk noted in the dataset's paper). Both clouds are loaded
    in full (no decimation) so the match stays aligned.
    """
    from scipy.spatial import cKDTree

    full = load_point_cloud(full_path, max_points=_NO_DECIMATION)
    wood_only = load_point_cloud(wood_only_path, max_points=_NO_DECIMATION)
    dist, _ = cKDTree(wood_only).query(full, k=1)
    gt = np.where(dist <= tol, 0, 1).astype(np.uint8)
    return full, gt


def _decimate_joint(
    points: np.ndarray, gt: np.ndarray, max_points: int, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Jointly subsample points + gt (seeded) so the pairing is preserved."""
    n = len(points)
    if n <= max_points:
        return points, gt
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(n, max_points, replace=False))
    return points[idx], gt[idx]


def _metrics_from_pred(pred: np.ndarray, gt: np.ndarray) -> dict:
    """Per-class IoU + accuracy + class fractions for one tree."""
    pred = np.asarray(pred)
    gt = np.asarray(gt)
    wood_iou = iou_score(pred, gt, positive_class=0)
    leaf_iou = iou_score(pred, gt, positive_class=1)
    return {
        "wood_iou": round(wood_iou, 4),
        "leaf_iou": round(leaf_iou, 4),
        "mean_iou": round((wood_iou + leaf_iou) / 2, 4),
        "accuracy": round(float(np.mean(pred == gt)), 4),
        "wood_frac_gt": round(float(np.mean(gt == 0)), 4),
        "wood_frac_pred": round(float(np.mean(pred == 0)), 4),
        "n_points": int(len(gt)),
    }


def evaluate_cloud(
    points: np.ndarray,
    gt: np.ndarray,
    *,
    backend: str = "tlsep",
    model_path: str | None = None,
    max_points: int = 200_000,
) -> dict:
    """Zero-shot: segment one tree with `backend` and score against `gt`."""
    from pipeline import wood_leaf_separation

    points = np.asarray(points, dtype=np.float64)
    gt = np.asarray(gt, dtype=np.uint8)
    points, gt = _decimate_joint(points, gt, max_points)

    segmenter = wood_leaf_separation.WoodLeafSegmenter(model_path=model_path, backend=backend)
    if backend == "pointnet":
        segmenter.load()
    pred = np.asarray(segmenter.segment(points), dtype=np.uint8)
    return _metrics_from_pred(pred, gt)


def evaluate_dataset(
    trees: list[tuple[str, np.ndarray, np.ndarray]],
    *,
    backends: Sequence[str],
    model_path: str | None = None,
    max_points: int = 200_000,
) -> dict:
    """Run `evaluate_cloud` over every (tree_id, points, gt) for each backend.

    Returns {"per_tree": [...], "summary": {backend: {n_trees, mean_*_iou}}}.
    """
    per_tree: list[dict] = []
    summary: dict[str, dict] = {}
    for backend in backends:
        wood, leaf, mean = [], [], []
        for tree_id, points, gt in trees:
            m = evaluate_cloud(
                points, gt, backend=backend, model_path=model_path, max_points=max_points
            )
            per_tree.append({"tree_id": tree_id, "backend": backend, **m})
            wood.append(m["wood_iou"])
            leaf.append(m["leaf_iou"])
            mean.append(m["mean_iou"])
        summary[backend] = {
            "n_trees": len(trees),
            "mean_wood_iou": round(float(np.mean(wood)), 4) if wood else 0.0,
            "mean_leaf_iou": round(float(np.mean(leaf)), 4) if leaf else 0.0,
            "mean_iou": round(float(np.mean(mean)), 4) if mean else 0.0,
        }
    return {"per_tree": per_tree, "summary": summary}
