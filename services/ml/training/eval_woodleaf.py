"""Evaluate + compare wood/leaf segmenters: PCA baseline vs PointNet++ (G2).

Both methods are scored on the SAME held-out synthetic trees (true wood/leaf
labels known) with training.metrics.iou_score — an apples-to-apples comparison
that answers "does the deep model actually beat the rule-based heuristic?".

Torch-free here; the PointNet++ labeler (which needs torch) is passed in by the
caller (see notebooks/compare_woodleaf.py).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from training.metrics import iou_score
from training.woodleaf_dataset import WOOD, make_woodleaf_sample


def make_test_samples(
    n_test: int = 12,
    n_points: int = 4096,
    seed0: int = 20_000,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Build held-out labelled test trees.

    Seeds start at 20_000 — disjoint from training (0..) and validation
    (10_000..) so the comparison is on genuinely unseen trees.

    Returns a list of (points (n_points,3) float32, true_labels (n_points,) int64).
    """
    return [make_woodleaf_sample(seed=seed0 + i, n_points=n_points) for i in range(n_test)]


def evaluate_segmenter(
    label_fn: Callable[[np.ndarray], np.ndarray],
    samples: list[tuple[np.ndarray, np.ndarray]],
    *,
    positive_class: int = WOOD,
) -> list[float]:
    """Per-tree wood IoU for one labeler over the given (points, true) samples.

    Args:
        label_fn: maps (N,3) points -> (N,) predicted wood/leaf labels
        samples: list of (points, true_labels)
        positive_class: class to score IoU for (default WOOD)
    """
    return [iou_score(label_fn(pts), true, positive_class) for pts, true in samples]
