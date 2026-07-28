"""End-to-end orchestrator tests — pipeline.main.process_points.

Verifies the 8-step pipeline composes into carbon numbers, and that the
wood/leaf backend is selectable (PCA default; PointNet++ when a model exists).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from pipeline import synthetic
from pipeline.main import process_points


@pytest.fixture(scope="module")
def synth_points():
    points, _, _ = synthetic.generate_synthetic_plot(
        n_trees=3, plot_size_m=20.0, ground_z_variation=0.8,
        ground_point_density=20.0, leaves_per_tree=1500, seed=42,
    )
    return points


def test_process_points_tlsep_produces_carbon(synth_points):
    result = process_points(synth_points, wood_leaf_backend="tlsep", default_species="Tectona grandis")
    assert result.summary["total_trees"] >= 1
    assert result.summary["total_carbon_kg"] > 0
    for t in result.trees:
        assert t.dbh_cm > 0
        assert t.height_m > 0
        assert t.carbon_kg > 0
        assert t.co2eq_kg > t.carbon_kg  # 44/12 ratio


def test_process_points_records_backend(synth_points):
    result = process_points(synth_points, wood_leaf_backend="tlsep")
    assert result.metadata["wood_leaf_backend"] == "tlsep"


def test_process_points_records_auditable_provenance(synth_points):
    result = process_points(synth_points, wood_leaf_backend="tlsep")
    metadata = result.metadata
    assert len(metadata["input_sha256"]) == 64
    assert len(metadata["git_commit"]) == 40
    assert isinstance(metadata["git_dirty"], bool)
    assert metadata["checkpoint_sha256"] is None
    assert metadata["algorithms"]["ground_segmentation"] == "percentile_grid"
    assert metadata["algorithms"]["wood_leaf"] == "tlsep"
    assert metadata["algorithms"]["species"] == "stub"
    assert metadata["evidence_status"] == "baseline"
    assert metadata["candidate_status"] == "candidate_not_evaluated"


def test_counts_reconcile_on_a_normal_run(synth_points):
    result = process_points(synth_points, wood_leaf_backend="tlsep")
    summary = result.summary

    assert summary["detected_trees"] == summary["measured_trees"] + summary["excluded_trees"]
    assert summary["measured_trees"] == len(result.trees)
    # total_trees stays the measured count so existing consumers keep working.
    assert summary["total_trees"] == summary["measured_trees"]
    assert len(result.diagnostics.excluded_segments) == summary["excluded_trees"]


def test_empty_wood_is_reported_not_silently_dropped(synth_points, monkeypatch):
    from pipeline import wood_leaf_separation

    monkeypatch.setattr(
        wood_leaf_separation.WoodLeafSegmenter,
        "segment",
        lambda self, points: np.full(len(points), wood_leaf_separation.LEAF, dtype=np.uint8),
    )
    result = process_points(synth_points, wood_leaf_backend="tlsep")
    summary = result.summary

    assert summary["detected_trees"] > 0
    assert summary["measured_trees"] == 0
    assert summary["excluded_trees"] == summary["detected_trees"]
    excluded = result.diagnostics.excluded_segments
    assert {item.reason_code for item in excluded} == {"WOOD_EMPTY"}
    assert {item.stage for item in excluded} == {"wood_leaf"}


def test_invalid_qsm_is_reported_not_silently_dropped(synth_points, monkeypatch):
    from pipeline import qsm, wood_leaf_separation

    monkeypatch.setattr(
        wood_leaf_separation.WoodLeafSegmenter,
        "segment",
        lambda self, points: np.full(len(points), wood_leaf_separation.WOOD, dtype=np.uint8),
    )
    monkeypatch.setattr(
        qsm,
        "compute_qsm",
        lambda wood, *, seed: SimpleNamespace(dbh_cm=0.0, height_m=5.0, total_volume_m3=1.0),
    )
    result = process_points(synth_points, wood_leaf_backend="tlsep")
    summary = result.summary

    assert summary["measured_trees"] == 0
    assert summary["excluded_trees"] == summary["detected_trees"]
    excluded = result.diagnostics.excluded_segments
    assert {item.reason_code for item in excluded} == {"QSM_INVALID"}
    assert {item.stage for item in excluded} == {"qsm"}


def test_unexpected_segmenter_error_fails_the_run(synth_points, monkeypatch):
    """An unexpected fault must fail loudly, never become an excluded segment."""
    from pipeline import wood_leaf_separation

    def fail(self, points):
        raise RuntimeError("segmenter exploded")

    monkeypatch.setattr(wood_leaf_separation.WoodLeafSegmenter, "segment", fail)
    with pytest.raises(RuntimeError, match="segmenter exploded"):
        process_points(synth_points, wood_leaf_backend="tlsep")


def test_process_points_pointnet_backend(synth_points):
    pytest.importorskip("torch")
    model = Path(__file__).resolve().parents[1] / "woodleaf_pn2.pt"
    if not model.exists():
        pytest.skip("no trained PointNet++ checkpoint (woodleaf_pn2.pt) available")
    result = process_points(
        synth_points, wood_leaf_backend="pointnet",
        model_path=str(model), default_species="Tectona grandis",
    )
    assert result.summary["total_trees"] >= 1
    assert result.metadata["wood_leaf_backend"] == "pointnet"
