"""Full-precision metrics and uncertainty gates for independent evaluation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from numbers import Real
from typing import Any

import numpy as np

from pipeline.provenance import PromotionDecision

_CONFUSION_KEYS = (
    "wood_as_wood",
    "wood_as_leaf",
    "leaf_as_wood",
    "leaf_as_leaf",
)
_METRIC_KEYS = ("wood_iou", "leaf_iou", "mean_iou", "accuracy")
_INTERVAL_KEYS = {
    "wood_iou_delta",
    "dbh_abs_error_delta",
    "height_abs_error_delta",
    "volume_ape_delta",
}
_INTERVAL_VALUE_KEYS = {"estimate", "lower", "upper"}


def _binary_labels(labels: np.ndarray, *, name: str) -> np.ndarray:
    array = np.asarray(labels)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if array.size == 0:
        raise ValueError(f"{name} must be non-empty")
    if not np.issubdtype(array.dtype, np.integer):
        raise TypeError(f"{name} must contain integer labels")
    if not np.all((array == 0) | (array == 1)):
        raise ValueError(f"{name} labels must be in {{0, 1}}")
    return array


def _iou(intersection: int, union: int) -> float:
    return float(intersection / union) if union else 1.0


def _metrics_from_confusion(confusion: Mapping[str, int]) -> dict[str, Any]:
    wood_as_wood = confusion["wood_as_wood"]
    wood_as_leaf = confusion["wood_as_leaf"]
    leaf_as_wood = confusion["leaf_as_wood"]
    leaf_as_leaf = confusion["leaf_as_leaf"]
    wood_iou = _iou(wood_as_wood, wood_as_wood + wood_as_leaf + leaf_as_wood)
    leaf_iou = _iou(leaf_as_leaf, leaf_as_leaf + wood_as_leaf + leaf_as_wood)
    total = wood_as_wood + wood_as_leaf + leaf_as_wood + leaf_as_leaf
    return {
        "wood_iou": wood_iou,
        "leaf_iou": leaf_iou,
        "mean_iou": (wood_iou + leaf_iou) / 2.0,
        "accuracy": float((wood_as_wood + leaf_as_leaf) / total),
        "confusion": dict(confusion),
    }


def segmentation_metrics(pred: np.ndarray, gt: np.ndarray) -> dict[str, Any]:
    """Return exact binary wood/leaf metrics without presentation rounding."""
    pred_array = _binary_labels(pred, name="pred")
    gt_array = _binary_labels(gt, name="gt")
    if pred_array.shape != gt_array.shape:
        raise ValueError("pred and gt must have equal lengths")

    confusion = {
        "wood_as_wood": int(np.count_nonzero((gt_array == 0) & (pred_array == 0))),
        "wood_as_leaf": int(np.count_nonzero((gt_array == 0) & (pred_array == 1))),
        "leaf_as_wood": int(np.count_nonzero((gt_array == 1) & (pred_array == 0))),
        "leaf_as_leaf": int(np.count_nonzero((gt_array == 1) & (pred_array == 1))),
    }
    return _metrics_from_confusion(confusion)


def _finite_real(value: Any, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be finite")
    return converted


def aggregate_segmentation_metrics(
    per_tree: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Retain per-tree metrics and report distinct macro and pooled aggregates."""
    if not isinstance(per_tree, Mapping):
        raise TypeError("per_tree must be a mapping")
    if not per_tree:
        raise ValueError("per_tree must be non-empty")
    if any(type(tree_id) is not str for tree_id in per_tree):
        raise TypeError("per_tree IDs must be strings")

    retained: dict[str, dict[str, Any]] = {}
    macro_values = {key: [] for key in _METRIC_KEYS}
    pooled_confusion = dict.fromkeys(_CONFUSION_KEYS, 0)
    for tree_id, metrics in per_tree.items():
        if not isinstance(metrics, Mapping):
            raise TypeError(f"metrics for {tree_id!r} must be a mapping")
        if not set(_METRIC_KEYS).issubset(metrics):
            raise ValueError(f"metrics for {tree_id!r} are incomplete")
        confusion = metrics.get("confusion")
        if not isinstance(confusion, Mapping) or set(confusion) != set(_CONFUSION_KEYS):
            raise ValueError(f"confusion for {tree_id!r} must have exact required keys")

        retained[tree_id] = dict(metrics)
        for key in _METRIC_KEYS:
            macro_values[key].append(_finite_real(metrics[key], name=f"{tree_id}.{key}"))
        for key in _CONFUSION_KEYS:
            count = confusion[key]
            if type(count) is not int:
                raise TypeError(f"{tree_id}.confusion.{key} must be an integer")
            if count < 0:
                raise ValueError(f"{tree_id}.confusion.{key} must be non-negative")
            pooled_confusion[key] += count

    macro = {key: float(sum(values) / len(values)) for key, values in macro_values.items()}
    return {
        "per_tree": retained,
        "macro": macro,
        "pooled": _metrics_from_confusion(pooled_confusion),
    }


def paired_percentile_ci(
    baseline: dict[str, float],
    candidate: dict[str, float],
    *,
    resamples: int,
    seed: int,
    confidence: float,
) -> dict[str, float]:
    """Bootstrap a paired candidate-minus-baseline mean over sorted tree IDs."""
    if type(resamples) is not int or resamples <= 0:
        raise ValueError("resamples must be a positive integer")
    if type(seed) is not int or seed <= 0:
        raise ValueError("seed must be a positive integer")
    confidence_value = _finite_real(confidence, name="confidence")
    if not 0.0 < confidence_value < 1.0:
        raise ValueError("confidence must be between zero and one")
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        raise TypeError("baseline and candidate must be dictionaries")
    if not baseline or not candidate:
        raise ValueError("baseline and candidate must be non-empty")
    if any(type(tree_id) is not str for tree_id in baseline | candidate):
        raise TypeError("tree IDs must be strings")
    if set(baseline) != set(candidate):
        raise ValueError("baseline and candidate must have identical tree ID sets")

    tree_ids = sorted(baseline)
    baseline_values = np.array(
        [_finite_real(baseline[tree_id], name=f"baseline[{tree_id!r}]") for tree_id in tree_ids],
        dtype=np.float64,
    )
    candidate_values = np.array(
        [_finite_real(candidate[tree_id], name=f"candidate[{tree_id!r}]") for tree_id in tree_ids],
        dtype=np.float64,
    )
    with np.errstate(over="ignore", invalid="ignore"):
        deltas = candidate_values - baseline_values
    if not np.all(np.isfinite(deltas)):
        raise ValueError("candidate-minus-baseline deltas must be finite")

    estimate = float(np.mean(deltas))
    rng = np.random.default_rng(seed)
    sampled_indices = rng.integers(
        0,
        len(tree_ids),
        size=(resamples, len(tree_ids)),
    )
    with np.errstate(over="ignore", invalid="ignore"):
        bootstrap_means = np.mean(deltas[sampled_indices], axis=1)
    alpha = (1.0 - confidence_value) / 2.0
    lower, upper = np.percentile(
        bootstrap_means,
        [100.0 * alpha, 100.0 * (1.0 - alpha)],
        method="linear",
    )
    result = {
        "estimate": estimate,
        "lower": float(lower),
        "upper": float(upper),
    }
    if not all(math.isfinite(value) for value in result.values()):
        raise ValueError("bootstrap interval must be finite")
    if not result["lower"] <= result["estimate"] <= result["upper"]:
        raise ValueError("bootstrap interval must contain its estimate")
    return result


def _validated_intervals(
    intervals: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    if not isinstance(intervals, dict):
        raise TypeError("intervals must be a dictionary")
    if set(intervals) != _INTERVAL_KEYS:
        raise ValueError("intervals must have exact required metric keys")

    validated: dict[str, dict[str, float]] = {}
    for metric_name, interval in intervals.items():
        if not isinstance(interval, dict):
            raise TypeError(f"{metric_name} interval must be a dictionary")
        if set(interval) != _INTERVAL_VALUE_KEYS:
            raise ValueError(f"{metric_name} interval must have estimate/lower/upper")
        values = {
            key: _finite_real(value, name=f"{metric_name}.{key}") for key, value in interval.items()
        }
        if not values["lower"] <= values["estimate"] <= values["upper"]:
            raise ValueError(f"{metric_name} interval bounds are inconsistent")
        validated[metric_name] = values
    return validated


def decide_independent_verdict(
    *,
    evidence_valid: bool,
    formal_decision: PromotionDecision,
    intervals: dict[str, dict[str, float]],
) -> dict[str, Any]:
    """Map formal metrics and uncertainty evidence to a fail-closed verdict."""
    if type(evidence_valid) is not bool:
        raise TypeError("evidence_valid must be a boolean")
    if not evidence_valid:
        return {"verdict": "INVALID_EVIDENCE", "promote": False}
    if not isinstance(formal_decision, PromotionDecision):
        raise TypeError("formal_decision must be a PromotionDecision")
    if type(formal_decision.promote) is not bool:
        raise TypeError("formal_decision.promote must be a boolean")
    if not formal_decision.promote:
        return {"verdict": "FAIL_METRICS", "promote": False}

    validated = _validated_intervals(intervals)
    strong = (
        validated["wood_iou_delta"]["lower"] > 0.0
        and validated["dbh_abs_error_delta"]["upper"] <= 0.0
        and validated["height_abs_error_delta"]["upper"] <= 0.0
        and validated["volume_ape_delta"]["upper"] <= 0.0
    )
    if not strong:
        return {"verdict": "POINT_ESTIMATE_PASS_ONLY", "promote": False}
    return {"verdict": "PROMOTE_POINTNET", "promote": True}
