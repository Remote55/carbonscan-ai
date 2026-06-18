"""Evaluate + compare wood/leaf segmenters: PCA baseline vs PointNet++ (G2).

Both methods are scored on the SAME held-out synthetic trees (true wood/leaf
labels known) with training.metrics.iou_score — an apples-to-apples comparison
that answers "does the deep model actually beat the rule-based heuristic?".

Torch-free here; the PointNet++ labeler (which needs torch) is passed in by the
caller (see notebooks/compare_woodleaf.py).
"""

from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path

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


def read_comparison_csv(path: str | Path) -> dict[str, list[float]]:
    """Reconstruct a {method: [iou, ...]} dict from a woodleaf_comparison.csv.

    Lets the comparison figure be regenerated from committed results without
    re-running the model (notebooks/compare_woodleaf.py --from-csv).
    """
    with Path(path).open(encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if r]
    methods = rows[0][1:]  # drop the leading tree_idx column
    results: dict[str, list[float]] = {m: [] for m in methods}
    for row in rows[1:]:
        for method, value in zip(methods, row[1:], strict=True):
            results[method].append(float(value))
    return results
