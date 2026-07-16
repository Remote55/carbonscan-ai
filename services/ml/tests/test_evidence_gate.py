"""Tests for evidence-gated PointNet++ promotion."""

from dataclasses import replace

from pipeline.provenance import (
    EvaluationMetrics,
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
