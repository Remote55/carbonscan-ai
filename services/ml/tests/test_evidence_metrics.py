"""Tests for full-precision independent-evaluation metrics."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import pipeline.evidence_metrics as evidence_metrics

aggregate_segmentation_metrics = evidence_metrics.aggregate_segmentation_metrics
paired_percentile_ci = evidence_metrics.paired_percentile_ci
segmentation_metrics = evidence_metrics.segmentation_metrics

ROOT = Path(__file__).resolve().parents[3]


def _naive_sum(values):
    total = 0
    for value in values:
        total += value
    return total


def test_segmentation_metrics_keeps_full_precision_and_confusion_counts():
    gt = np.array([0, 0, 0, 1], dtype=np.uint8)
    pred = np.array([0, 0, 1, 1], dtype=np.uint8)

    result = segmentation_metrics(pred, gt)

    assert result["wood_iou"] == 2 / 3
    assert result["leaf_iou"] == 1 / 2
    assert result["mean_iou"] == ((2 / 3) + (1 / 2)) / 2
    assert result["accuracy"] == 3 / 4
    assert result["confusion"] == {
        "wood_as_wood": 2,
        "wood_as_leaf": 1,
        "leaf_as_wood": 0,
        "leaf_as_leaf": 1,
    }
    assert all(type(count) is int for count in result["confusion"].values())


@pytest.mark.parametrize(
    ("pred", "gt"),
    [
        (np.array([], dtype=np.int8), np.array([], dtype=np.int8)),
        (np.array([[0, 1]], dtype=np.int8), np.array([0, 1], dtype=np.int8)),
        (np.array([0], dtype=np.int8), np.array([0, 1], dtype=np.int8)),
        (np.array([0.0, 1.0]), np.array([0, 1], dtype=np.int8)),
        (np.array([False, True]), np.array([0, 1], dtype=np.int8)),
        (np.array([0, 2], dtype=np.int8), np.array([0, 1], dtype=np.int8)),
    ],
)
def test_segmentation_metrics_rejects_malformed_labels(pred, gt):
    with pytest.raises((TypeError, ValueError)):
        segmentation_metrics(pred, gt)


def test_segmentation_metrics_scores_absent_class_as_exact_agreement():
    result = segmentation_metrics(
        np.array([0, 0], dtype=np.int8),
        np.array([0, 0], dtype=np.int8),
    )
    assert result["wood_iou"] == 1.0
    assert result["leaf_iou"] == 1.0


def test_aggregation_retains_trees_and_separates_macro_from_pooled_metrics():
    per_tree = {
        "small": segmentation_metrics(
            np.array([0, 1], dtype=np.int8),
            np.array([0, 1], dtype=np.int8),
        ),
        "large": segmentation_metrics(
            np.array([1, 1, 1, 1], dtype=np.int8),
            np.array([0, 0, 0, 1], dtype=np.int8),
        ),
    }

    result = aggregate_segmentation_metrics(per_tree)

    assert result["per_tree"] == per_tree
    assert result["macro"] == {
        "wood_iou": 1 / 2,
        "leaf_iou": 5 / 8,
        "mean_iou": 9 / 16,
        "accuracy": 5 / 8,
    }
    assert result["pooled"] == {
        "wood_iou": 1 / 4,
        "leaf_iou": 2 / 5,
        "mean_iou": (1 / 4 + 2 / 5) / 2,
        "accuracy": 1 / 2,
        "confusion": {
            "wood_as_wood": 1,
            "wood_as_leaf": 3,
            "leaf_as_wood": 0,
            "leaf_as_leaf": 2,
        },
    }


def test_aggregation_macro_is_independent_of_runtime_sum_algorithm(monkeypatch):
    committed = json.loads(
        (ROOT / "docs/evidence/pointnet_independent_eval/result.json").read_text(
            encoding="utf-8"
        )
    )
    segmentation = committed["baseline"]["external_segmentation"]
    monkeypatch.setattr(evidence_metrics, "sum", _naive_sum, raising=False)

    result = aggregate_segmentation_metrics(segmentation["per_tree"])

    assert result["macro"] == segmentation["macro"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("wood_iou", 0.99),
        ("leaf_iou", float("nan")),
        ("mean_iou", True),
        ("accuracy", float("inf")),
    ],
)
def test_aggregation_rejects_scalar_metrics_inconsistent_with_confusion(field, value):
    metrics = segmentation_metrics(
        np.array([0, 0, 1, 1], dtype=np.int8),
        np.array([0, 1, 0, 1], dtype=np.int8),
    )
    metrics[field] = value

    with pytest.raises((TypeError, ValueError)):
        aggregate_segmentation_metrics({"tree": metrics})


def test_aggregation_requires_exact_per_tree_record_schema():
    metrics = segmentation_metrics(
        np.array([0, 1], dtype=np.int8),
        np.array([0, 1], dtype=np.int8),
    )
    metrics["unexpected"] = "not canonical"

    with pytest.raises(ValueError):
        aggregate_segmentation_metrics({"tree": metrics})

    del metrics["unexpected"]
    del metrics["accuracy"]
    with pytest.raises(ValueError):
        aggregate_segmentation_metrics({"tree": metrics})


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("wood_as_wood", np.int64(1), TypeError),
        ("wood_as_leaf", True, TypeError),
        ("leaf_as_wood", -1, ValueError),
    ],
)
def test_aggregation_rejects_noncanonical_confusion_counts(field, value, error_type):
    metrics = segmentation_metrics(
        np.array([0, 1], dtype=np.int8),
        np.array([0, 1], dtype=np.int8),
    )
    metrics["confusion"][field] = value

    with pytest.raises(error_type):
        aggregate_segmentation_metrics({"tree": metrics})


def test_aggregation_rejects_zero_point_confusion():
    metrics = {
        "wood_iou": 1.0,
        "leaf_iou": 1.0,
        "mean_iou": 1.0,
        "accuracy": 1.0,
        "confusion": {
            "wood_as_wood": 0,
            "wood_as_leaf": 0,
            "leaf_as_wood": 0,
            "leaf_as_leaf": 0,
        },
    }

    with pytest.raises(ValueError):
        aggregate_segmentation_metrics({"tree": metrics})


def test_aggregation_returns_canonical_deep_copy_without_input_aliases():
    metrics = segmentation_metrics(
        np.array([0, 0, 1, 1], dtype=np.int8),
        np.array([0, 1, 0, 1], dtype=np.int8),
    )
    expected = segmentation_metrics(
        np.array([0, 0, 1, 1], dtype=np.int8),
        np.array([0, 1, 0, 1], dtype=np.int8),
    )

    result = aggregate_segmentation_metrics({"tree": metrics})
    metrics["wood_iou"] = 0.0
    metrics["confusion"]["wood_as_wood"] = 999

    assert result["per_tree"] == {"tree": expected}
    assert result["per_tree"]["tree"] is not metrics
    assert result["per_tree"]["tree"]["confusion"] is not metrics["confusion"]


def test_paired_percentile_ci_is_seeded_and_order_independent():
    baseline = {"a": 0.2, "b": 0.3, "c": 0.4}
    candidate = {"a": 0.4, "b": 0.5, "c": 0.6}

    first = paired_percentile_ci(
        baseline,
        candidate,
        resamples=10_000,
        seed=20_260_716,
        confidence=0.95,
    )
    second = paired_percentile_ci(
        dict(reversed(list(baseline.items()))),
        dict(reversed(list(candidate.items()))),
        resamples=10_000,
        seed=20_260_716,
        confidence=0.95,
    )

    assert first == second
    assert first["estimate"] == pytest.approx(0.2)
    assert first["lower"] <= first["estimate"] <= first["upper"]
    assert all(type(value) is float for value in first.values())


@pytest.mark.parametrize(
    ("baseline", "candidate"),
    [
        ({}, {}),
        ({"a": 1.0}, {"b": 1.0}),
        ({1: 1.0}, {1: 2.0}),
        ({"a": True}, {"a": 1.0}),
        ({"a": 1.0}, {"a": float("nan")}),
        ({"a": float("inf")}, {"a": 1.0}),
        ({"a": "1.0"}, {"a": 2.0}),
    ],
)
def test_paired_percentile_ci_rejects_malformed_records(baseline, candidate):
    with pytest.raises((TypeError, ValueError)):
        paired_percentile_ci(
            baseline,
            candidate,
            resamples=100,
            seed=1,
            confidence=0.95,
        )


@pytest.mark.parametrize(
    ("resamples", "seed", "confidence"),
    [
        (0, 1, 0.95),
        (True, 1, 0.95),
        (10.0, 1, 0.95),
        (10, 0, 0.95),
        (10, True, 0.95),
        (10, 1, 0.0),
        (10, 1, 1.0),
        (10, 1, True),
        (10, 1, float("nan")),
    ],
)
def test_paired_percentile_ci_rejects_invalid_controls(resamples, seed, confidence):
    with pytest.raises((TypeError, ValueError)):
        paired_percentile_ci(
            {"tree": 1.0},
            {"tree": 2.0},
            resamples=resamples,
            seed=seed,
            confidence=confidence,
        )
