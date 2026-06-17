"""Segmentation metrics (torch-free) for wood-leaf evaluation."""

from __future__ import annotations

import numpy as np


def iou_score(pred: np.ndarray, target: np.ndarray, positive_class: int = 0) -> float:
    """Intersection-over-Union for one class.

    IoU = |pred==c ∩ target==c| / |pred==c ∪ target==c|

    Args:
        pred: (N,) predicted class labels
        target: (N,) ground-truth class labels
        positive_class: class id to score (default 0 = WOOD)

    Returns:
        IoU in [0, 1]. If the class is absent from both pred and target
        (union is empty) they agree perfectly, so returns 1.0.
    """
    pred = np.asarray(pred)
    target = np.asarray(target)
    pred_mask = pred == positive_class
    target_mask = target == positive_class
    intersection = int(np.count_nonzero(pred_mask & target_mask))
    union = int(np.count_nonzero(pred_mask | target_mask))
    if union == 0:
        return 1.0
    return intersection / union
