"""End-to-end orchestrator tests — pipeline.main.process_points.

Verifies the 8-step pipeline composes into carbon numbers, and that the
wood/leaf backend is selectable (PCA default; PointNet++ when a model exists).
"""

from __future__ import annotations

from pathlib import Path

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
