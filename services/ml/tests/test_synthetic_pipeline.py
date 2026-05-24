"""Smoke test: run every pipeline step on a small synthetic plot.

Catches import errors, shape bugs, and gross algorithmic regressions.
Designed to finish in < 10 seconds on CI.
"""

from __future__ import annotations

import numpy as np
import pytest

from pipeline import (
    allometric,
    canopy_height_model,
    ground_classification,
    height_normalization,
    qsm,
    synthetic,
    tree_segmentation,
    wood_leaf_separation,
)


@pytest.fixture(scope="module")
def synth_plot():
    """Small synthetic plot — keep tiny for CI speed."""
    points, gt_labels, trees = synthetic.generate_synthetic_plot(
        n_trees=3,
        plot_size_m=20.0,
        ground_z_variation=0.8,
        ground_point_density=20.0,
        leaves_per_tree=1500,
        seed=42,
    )
    return points, gt_labels, trees


def test_synthetic_generates_points(synth_plot):
    points, gt_labels, trees = synth_plot
    assert points.shape[1] == 3
    assert points.shape[0] > 1000
    assert len(gt_labels) == len(points)
    assert len(trees) == 3
    # Every class should have at least some points
    assert (gt_labels == synthetic.CLASS_GROUND).sum() > 0
    assert (gt_labels == synthetic.CLASS_WOOD).sum() > 0
    assert (gt_labels == synthetic.CLASS_LEAF).sum() > 0


def test_step1_ground_classification_recovers_ground(synth_plot):
    points, gt_labels, _ = synth_plot
    mask = ground_classification.classify_ground_array(points)
    # Recall ≥ 80% — heuristic doesn't have to be perfect
    truth_ground = gt_labels == synthetic.CLASS_GROUND
    tp = int((mask & truth_ground).sum())
    recall = tp / max(int(truth_ground.sum()), 1)
    assert recall >= 0.80, f"Ground recall too low: {recall:.2%}"


def test_step2_height_normalization_grounds_zero(synth_plot):
    points, _, _ = synth_plot
    mask = ground_classification.classify_ground_array(points)
    norm = height_normalization.normalize_height_array(points, mask)
    # Ground points after normalization should be close to Z = 0
    ground_z_after = norm[mask, 2]
    assert abs(ground_z_after.mean()) < 0.3, f"Ground not zeroed: mean={ground_z_after.mean()}"


def test_step3_chm_max_reasonable(synth_plot):
    points, _, trees = synth_plot
    mask = ground_classification.classify_ground_array(points)
    norm = height_normalization.normalize_height_array(points, mask)
    chm, _ = canopy_height_model.compute_chm_array(norm, resolution=0.5, min_height=0.5)
    max_truth_height = max(t.height for t in trees)
    # CHM max should be within 20% of the tallest tree
    assert abs(np.nanmax(chm) - max_truth_height) / max_truth_height < 0.2


def test_step4_watershed_detects_trees(synth_plot):
    points, _, trees = synth_plot
    mask = ground_classification.classify_ground_array(points)
    norm = height_normalization.normalize_height_array(points, mask)
    chm, _ = canopy_height_model.compute_chm_array(norm, resolution=0.5, min_height=0.5)
    labels_2d = tree_segmentation.watershed_segmentation(chm, min_height=3.0, min_distance=5)
    n_detected = int(labels_2d.max())
    # Heuristic watershed sometimes over-segments wide canopies; we just want
    # to confirm it finds *at least* the truth count (Phase 2 will tune via
    # marker-controlled watershed).
    assert n_detected >= len(trees), f"Detected {n_detected}, truth {len(trees)}"
    assert n_detected <= len(trees) * 3, f"Detected {n_detected} — over-segmenting badly"


def test_step5_wood_leaf_finds_wood(synth_plot):
    points, gt_labels, _ = synth_plot
    # Use ground-truth wood+leaf points (skip the upstream steps to keep test focused)
    tree_only_mask = gt_labels != synthetic.CLASS_GROUND
    tree_points = points[tree_only_mask]
    # Subsample to keep test fast
    rng = np.random.default_rng(0)
    if len(tree_points) > 3000:
        idx = rng.choice(len(tree_points), 3000, replace=False)
        tree_points = tree_points[idx]
    labels = wood_leaf_separation.segment_wood_leaf(tree_points)
    # Some points should be wood (verifies the function runs and produces both classes)
    n_wood = int((labels == wood_leaf_separation.WOOD).sum())
    assert 0 < n_wood < len(tree_points)


def test_step6_qsm_dbh_in_reasonable_range(synth_plot):
    points, gt_labels, trees = synth_plot
    # Pick wood points only (use ground truth)
    wood_pts = points[gt_labels == synthetic.CLASS_WOOD]
    # Filter to wood near the first tree
    first = trees[0]
    near = (
        (np.abs(wood_pts[:, 0] - first.x) < 1.5)
        & (np.abs(wood_pts[:, 1] - first.y) < 1.5)
    )
    first_wood = wood_pts[near]
    # Need normalized Z — subtract local ground
    first_wood = first_wood.copy()
    first_wood[:, 2] -= first.z_ground
    result = qsm.compute_qsm(first_wood, seed=0)
    # DBH within ±40% of truth (heuristic, not perfect)
    rel_err = abs(result.dbh_cm - first.dbh_cm) / first.dbh_cm
    assert rel_err < 0.4, f"DBH error too large: pred={result.dbh_cm:.1f}, truth={first.dbh_cm:.1f}"


def test_step8_allometric_returns_positive_carbon():
    result = allometric.calculate_carbon(
        dbh_cm=30.0,
        height_m=15.0,
        species_sci="Tectona grandis",
    )
    assert result.carbon_kg > 0
    assert result.co2eq_kg > result.carbon_kg  # because of 44/12 ratio


def test_end_to_end_no_exceptions(synth_plot):
    """Run all 8 steps in sequence — verifies they compose without errors."""
    points, _, _ = synth_plot
    ground_mask = ground_classification.classify_ground_array(points)
    norm = height_normalization.normalize_height_array(points, ground_mask)
    chm, transform = canopy_height_model.compute_chm_array(norm, resolution=0.5, min_height=0.5)
    labels_2d = tree_segmentation.watershed_segmentation(chm, min_height=3.0, min_distance=5)
    tree_ids = tree_segmentation.assign_points_to_trees(norm, labels_2d, transform)
    tree_clouds = tree_segmentation.extract_tree_points(norm, tree_ids)
    assert len(tree_clouds) > 0

    segmenter = wood_leaf_separation.WoodLeafSegmenter(backend="tlsep")
    first_tid = sorted(tree_clouds.keys())[0]
    labels = segmenter.segment(tree_clouds[first_tid])
    wood_pts = tree_clouds[first_tid][labels == wood_leaf_separation.WOOD]
    if len(wood_pts) > 0:
        result = qsm.compute_qsm(wood_pts, seed=first_tid)
        carbon = allometric.calculate_carbon(
            dbh_cm=max(result.dbh_cm, 1.0),  # avoid 0 if QSM fails
            height_m=max(result.height_m, 1.0),
            species_sci="Tectona grandis",
        )
        assert carbon.carbon_kg >= 0
