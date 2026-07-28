"""Tests for evidence-gated PointNet++ promotion."""

from dataclasses import replace

import pytest

from pipeline.evidence_metrics import decide_independent_verdict
from pipeline.provenance import (
    EvaluationMetrics,
    PromotionDecision,
    PromotionEvidence,
    evaluate_promotion,
)

BASELINE = EvaluationMetrics(
    wood_iou=0.42,
    dbh_mae_cm=1.2,
    height_mae_m=0.55,
    volume_mape_pct=18.8,
    measurable_trees=65,
)
CANDIDATE = EvaluationMetrics(
    wood_iou=0.50,
    dbh_mae_cm=1.1,
    height_mae_m=0.54,
    volume_mape_pct=18.0,
    measurable_trees=65,
)
VALID = PromotionEvidence(
    baseline=BASELINE,
    candidate=CANDIDATE,
    checkpoint_sha256="b" * 64,
    training_provenance_complete=True,
    independent_real_test=True,
    reproducible_command=True,
)


def test_complete_non_regressing_candidate_is_promoted():
    decision = evaluate_promotion(VALID)
    assert decision.promote is True
    assert decision.status == "promoted"
    assert decision.failed_criteria == ()


def test_missing_candidate_is_not_evaluated():
    decision = evaluate_promotion(replace(VALID, candidate=None))
    assert decision.promote is False
    assert decision.status == "candidate_not_evaluated"
    assert decision.failed_criteria == ("candidate_metrics",)


def test_every_gate_is_mandatory():
    cases = (
        (replace(VALID, checkpoint_sha256=None), "checkpoint_sha256"),
        (replace(VALID, checkpoint_sha256="not-a-sha256"), "checkpoint_sha256"),
        (replace(VALID, training_provenance_complete=False), "training_provenance"),
        (replace(VALID, independent_real_test=False), "independent_real_test"),
        (replace(VALID, reproducible_command=False), "reproducible_command"),
        (replace(VALID, candidate=replace(CANDIDATE, wood_iou=0.42)), "wood_iou_improves"),
        (
            replace(VALID, candidate=replace(CANDIDATE, dbh_mae_cm=1.21)),
            "dbh_mae_non_regression",
        ),
        (
            replace(VALID, candidate=replace(CANDIDATE, height_mae_m=0.56)),
            "height_mae_non_regression",
        ),
        (
            replace(VALID, candidate=replace(CANDIDATE, volume_mape_pct=18.81)),
            "volume_mape_non_regression",
        ),
        (
            replace(VALID, candidate=replace(CANDIDATE, measurable_trees=64)),
            "measurable_tree_count",
        ),
    )
    for evidence, criterion in cases:
        decision = evaluate_promotion(evidence)
        assert decision.promote is False
        assert decision.status == "rejected"
        assert criterion in decision.failed_criteria


def _intervals(*, wood_lower=0.01, downstream_upper=0.0):
    return {
        "wood_iou_delta": {"estimate": 0.05, "lower": wood_lower, "upper": 0.1},
        "dbh_abs_error_delta": {
            "estimate": -0.05,
            "lower": -0.1,
            "upper": downstream_upper,
        },
        "height_abs_error_delta": {
            "estimate": -0.05,
            "lower": -0.1,
            "upper": downstream_upper,
        },
        "volume_ape_delta": {
            "estimate": -0.05,
            "lower": -0.1,
            "upper": downstream_upper,
        },
    }


def test_invalid_evidence_maps_to_invalid_verdict():
    result = decide_independent_verdict(
        evidence_valid=False,
        formal_decision=evaluate_promotion(VALID),
        intervals=_intervals(),
    )
    assert result == {"verdict": "INVALID_EVIDENCE", "promote": False}


def test_invalid_evidence_precedes_untrusted_decision_and_intervals():
    result = decide_independent_verdict(
        evidence_valid=False,
        formal_decision=object(),
        intervals={},
    )

    assert result == {"verdict": "INVALID_EVIDENCE", "promote": False}


def test_failed_formal_metric_maps_to_fail_metrics_verdict():
    rejected = evaluate_promotion(replace(VALID, candidate=replace(CANDIDATE, wood_iou=0.42)))
    result = decide_independent_verdict(
        evidence_valid=True,
        formal_decision=rejected,
        intervals=_intervals(),
    )
    assert result == {"verdict": "FAIL_METRICS", "promote": False}


def test_weak_interval_maps_to_point_estimate_only_verdict():
    result = decide_independent_verdict(
        evidence_valid=True,
        formal_decision=evaluate_promotion(VALID),
        intervals=_intervals(wood_lower=0.0),
    )
    assert result == {"verdict": "POINT_ESTIMATE_PASS_ONLY", "promote": False}


def test_strong_intervals_map_to_pointnet_promotion_verdict():
    result = decide_independent_verdict(
        evidence_valid=True,
        formal_decision=evaluate_promotion(VALID),
        intervals=_intervals(),
    )
    assert result == {"verdict": "PROMOTE_POINTNET", "promote": True}


def test_verdict_rejects_non_boolean_evidence_flag():
    with pytest.raises(TypeError):
        decide_independent_verdict(
            evidence_valid=1,
            formal_decision=evaluate_promotion(VALID),
            intervals=_intervals(),
        )


@pytest.mark.parametrize(
    "intervals",
    [
        {},
        {**_intervals(), "unexpected": {"estimate": 0.0, "lower": 0.0, "upper": 0.0}},
        {**_intervals(), "wood_iou_delta": {"estimate": 0.05, "lower": 0.01}},
        {
            **_intervals(),
            "wood_iou_delta": {"estimate": 0.05, "lower": float("nan"), "upper": 0.1},
        },
        {**_intervals(), "wood_iou_delta": {"estimate": 0.05, "lower": 0.1, "upper": 0.0}},
    ],
)
def test_verdict_never_promotes_malformed_intervals(intervals):
    with pytest.raises((TypeError, ValueError)):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=evaluate_promotion(VALID),
            intervals=intervals,
        )


def test_verdict_requires_exact_promotion_decision_type():
    class DerivedPromotionDecision(PromotionDecision):
        pass

    valid = evaluate_promotion(VALID)
    derived = DerivedPromotionDecision(
        promote=valid.promote,
        status=valid.status,
        failed_criteria=valid.failed_criteria,
        baseline=valid.baseline,
        candidate=valid.candidate,
    )

    with pytest.raises(TypeError):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=derived,
            intervals=_intervals(),
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"promote": 1},
        {"status": "unknown"},
        {"failed_criteria": ["checkpoint_sha256"]},
        {"failed_criteria": ("checkpoint_sha256", "checkpoint_sha256")},
        {"failed_criteria": ("",)},
        {"failed_criteria": ("not_a_criterion",)},
    ],
)
def test_verdict_rejects_malformed_decision_fields(changes):
    forged = replace(evaluate_promotion(VALID), **changes)

    with pytest.raises((TypeError, ValueError)):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=forged,
            intervals=_intervals(),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("wood_iou", True),
        ("wood_iou", float("nan")),
        ("wood_iou", 1.01),
        ("dbh_mae_cm", -0.01),
        ("height_mae_m", float("inf")),
        ("volume_mape_pct", -0.01),
        ("measurable_trees", True),
        ("measurable_trees", 0),
    ],
)
def test_verdict_rejects_malformed_baseline_metrics(field, value):
    valid = evaluate_promotion(VALID)
    baseline = dict(valid.baseline)
    baseline[field] = value
    forged = replace(valid, baseline=baseline)

    with pytest.raises((TypeError, ValueError)):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=forged,
            intervals=_intervals(),
        )


def test_verdict_requires_exact_baseline_and_candidate_metric_schemas():
    valid = evaluate_promotion(VALID)
    baseline = dict(valid.baseline)
    baseline["unexpected"] = 1.0
    with pytest.raises(ValueError):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=replace(valid, baseline=baseline),
            intervals=_intervals(),
        )

    candidate = dict(valid.candidate)
    del candidate["height_mae_m"]
    with pytest.raises(ValueError):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=replace(valid, candidate=candidate),
            intervals=_intervals(),
        )


@pytest.mark.parametrize(
    "forged",
    [
        replace(evaluate_promotion(VALID), status="rejected"),
        replace(
            evaluate_promotion(VALID),
            failed_criteria=("checkpoint_sha256",),
        ),
        replace(evaluate_promotion(VALID), candidate=None),
        replace(
            evaluate_promotion(VALID),
            candidate={**evaluate_promotion(VALID).candidate, "wood_iou": BASELINE.wood_iou},
        ),
        replace(
            evaluate_promotion(VALID),
            promote=False,
            status="rejected",
            failed_criteria=("wood_iou_improves",),
        ),
    ],
)
def test_verdict_rejects_forged_promoted_state_or_metric_relationships(forged):
    with pytest.raises(ValueError):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=forged,
            intervals=_intervals(),
        )


def test_verdict_requires_matching_failure_for_each_point_metric_violation():
    rejected = evaluate_promotion(
        replace(VALID, candidate=replace(CANDIDATE, wood_iou=BASELINE.wood_iou))
    )
    forged = replace(rejected, failed_criteria=("checkpoint_sha256",))

    with pytest.raises(ValueError):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=forged,
            intervals=_intervals(),
        )


@pytest.mark.parametrize(
    "forged",
    [
        replace(evaluate_promotion(replace(VALID, candidate=None)), promote=True),
        replace(evaluate_promotion(replace(VALID, candidate=None)), status="rejected"),
        replace(evaluate_promotion(replace(VALID, candidate=None)), failed_criteria=()),
        replace(
            evaluate_promotion(replace(VALID, candidate=None)),
            failed_criteria=("candidate_metrics", "checkpoint_sha256"),
        ),
    ],
)
def test_verdict_rejects_forged_candidate_not_evaluated_state(forged):
    with pytest.raises(ValueError):
        decide_independent_verdict(
            evidence_valid=True,
            formal_decision=forged,
            intervals=_intervals(),
        )


def test_valid_non_reconstructible_provenance_failure_still_fails_metrics_gate():
    rejected = evaluate_promotion(replace(VALID, checkpoint_sha256=None))

    result = decide_independent_verdict(
        evidence_valid=True,
        formal_decision=rejected,
        intervals=_intervals(),
    )

    assert result == {"verdict": "FAIL_METRICS", "promote": False}
