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
