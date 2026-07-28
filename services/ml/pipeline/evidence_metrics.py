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
_SEGMENTATION_RECORD_KEYS = {*_METRIC_KEYS, "confusion"}
_INTERVAL_KEYS = {
    "wood_iou_delta",
    "dbh_abs_error_delta",
    "height_abs_error_delta",
    "volume_ape_delta",
}
_INTERVAL_VALUE_KEYS = {"estimate", "lower", "upper"}
_EVALUATION_METRIC_KEYS = {
    "wood_iou",
    "dbh_mae_cm",
    "height_mae_m",
    "volume_mape_pct",
    "measurable_trees",
}
_PROMOTION_STATUSES = {"candidate_not_evaluated", "rejected", "promoted"}
_POINT_METRIC_CRITERIA = {
    "wood_iou_improves",
    "dbh_mae_non_regression",
    "height_mae_non_regression",
    "volume_mape_non_regression",
    "measurable_tree_count",
}
_OPAQUE_EVIDENCE_CRITERIA = {
    "checkpoint_sha256",
    "training_provenance",
    "independent_real_test",
    "reproducible_command",
}
_PROMOTION_CRITERIA = {
    "candidate_metrics",
    *_POINT_METRIC_CRITERIA,
    *_OPAQUE_EVIDENCE_CRITERIA,
}


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
    if total <= 0:
        raise ValueError("confusion must represent at least one point")
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


def _canonical_segmentation_record(metrics: Mapping[str, Any], *, tree_id: str) -> dict[str, Any]:
    if type(metrics) is not dict:
        raise TypeError(f"metrics for {tree_id!r} must be a dictionary")
    if set(metrics) != _SEGMENTATION_RECORD_KEYS:
        raise ValueError(f"metrics for {tree_id!r} must have exact required keys")

    confusion = metrics["confusion"]
    if type(confusion) is not dict:
        raise TypeError(f"confusion for {tree_id!r} must be a dictionary")
    if set(confusion) != set(_CONFUSION_KEYS):
        raise ValueError(f"confusion for {tree_id!r} must have exact required keys")

    canonical_confusion: dict[str, int] = {}
    for key in _CONFUSION_KEYS:
        count = confusion[key]
        if type(count) is not int:
            raise TypeError(f"{tree_id}.confusion.{key} must be an integer")
        if count < 0:
            raise ValueError(f"{tree_id}.confusion.{key} must be non-negative")
        canonical_confusion[key] = count
    if sum(canonical_confusion.values()) <= 0:
        raise ValueError(f"confusion for {tree_id!r} must represent at least one point")

    canonical = _metrics_from_confusion(canonical_confusion)
    for key in _METRIC_KEYS:
        supplied = _finite_real(metrics[key], name=f"{tree_id}.{key}")
        if supplied != canonical[key]:
            raise ValueError(f"{tree_id}.{key} is inconsistent with confusion counts")
    return canonical


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
        canonical = _canonical_segmentation_record(metrics, tree_id=tree_id)
        retained[tree_id] = canonical
        for key in _METRIC_KEYS:
            macro_values[key].append(canonical[key])
        for key in _CONFUSION_KEYS:
            pooled_confusion[key] += canonical["confusion"][key]

    macro = {
        key: float(math.fsum(values) / len(values))
        for key, values in macro_values.items()
    }
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


def _validated_evaluation_metrics(metrics: Any, *, name: str) -> dict[str, float | int]:
    if type(metrics) is not dict:
        raise TypeError(f"{name} must be a dictionary")
    if set(metrics) != _EVALUATION_METRIC_KEYS:
        raise ValueError(f"{name} must have exact required metric keys")

    wood_iou = _finite_real(metrics["wood_iou"], name=f"{name}.wood_iou")
    if not 0.0 <= wood_iou <= 1.0:
        raise ValueError(f"{name}.wood_iou must be between zero and one")

    canonical: dict[str, float | int] = {"wood_iou": wood_iou}
    for key in ("dbh_mae_cm", "height_mae_m", "volume_mape_pct"):
        value = _finite_real(metrics[key], name=f"{name}.{key}")
        if value < 0.0:
            raise ValueError(f"{name}.{key} must be non-negative")
        canonical[key] = value

    measurable_trees = metrics["measurable_trees"]
    if type(measurable_trees) is not int:
        raise TypeError(f"{name}.measurable_trees must be an integer")
    if measurable_trees <= 0:
        raise ValueError(f"{name}.measurable_trees must be positive")
    canonical["measurable_trees"] = measurable_trees
    return canonical


def _expected_point_metric_failures(
    baseline: Mapping[str, float | int],
    candidate: Mapping[str, float | int],
) -> set[str]:
    checks = {
        "wood_iou_improves": candidate["wood_iou"] > baseline["wood_iou"],
        "dbh_mae_non_regression": candidate["dbh_mae_cm"] <= baseline["dbh_mae_cm"],
        "height_mae_non_regression": candidate["height_mae_m"] <= baseline["height_mae_m"],
        "volume_mape_non_regression": candidate["volume_mape_pct"] <= baseline["volume_mape_pct"],
        "measurable_tree_count": candidate["measurable_trees"] >= baseline["measurable_trees"],
    }
    return {criterion for criterion, passed in checks.items() if not passed}


def _validate_formal_decision(formal_decision: PromotionDecision) -> None:
    if type(formal_decision) is not PromotionDecision:
        raise TypeError("formal_decision must be exactly PromotionDecision")
    if type(formal_decision.promote) is not bool:
        raise TypeError("formal_decision.promote must be a boolean")
    if type(formal_decision.status) is not str:
        raise TypeError("formal_decision.status must be a string")
    if formal_decision.status not in _PROMOTION_STATUSES:
        raise ValueError("formal_decision.status is not allowed")
    if type(formal_decision.failed_criteria) is not tuple:
        raise TypeError("formal_decision.failed_criteria must be a tuple")

    failed = formal_decision.failed_criteria
    for criterion in failed:
        if type(criterion) is not str:
            raise TypeError("failed criteria must be strings")
        if not criterion or criterion not in _PROMOTION_CRITERIA:
            raise ValueError("failed criterion is not allowed")
    if len(set(failed)) != len(failed):
        raise ValueError("failed criteria must be unique")

    baseline = _validated_evaluation_metrics(formal_decision.baseline, name="baseline")
    candidate_record = formal_decision.candidate
    if candidate_record is None:
        if not (
            formal_decision.promote is False
            and formal_decision.status == "candidate_not_evaluated"
            and failed == ("candidate_metrics",)
        ):
            raise ValueError("candidate-not-evaluated decision is inconsistent")
        return

    candidate = _validated_evaluation_metrics(candidate_record, name="candidate")
    if formal_decision.status == "candidate_not_evaluated" or "candidate_metrics" in failed:
        raise ValueError("evaluated candidate cannot use candidate_metrics state")

    expected_point_failures = _expected_point_metric_failures(baseline, candidate)
    reported_point_failures = set(failed) & _POINT_METRIC_CRITERIA
    if reported_point_failures != expected_point_failures:
        raise ValueError("point-metric failures are inconsistent with decision metrics")

    if formal_decision.promote:
        if formal_decision.status != "promoted" or failed:
            raise ValueError("promoted decision state is inconsistent")
        return
    if formal_decision.status != "rejected" or not failed:
        raise ValueError("rejected decision state is inconsistent")

    # Identity/provenance inputs are absent from PromotionDecision. Their allowed
    # criteria can be schema-checked here but cannot be independently reconstructed.


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
    _validate_formal_decision(formal_decision)
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
