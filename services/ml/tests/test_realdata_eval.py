"""Tests for real-world wood/leaf IoU evaluation (spec 2026-06-26)."""

from __future__ import annotations

import numpy as np

from pipeline.realdata_eval import load_labelled_cloud


def test_load_labelled_cloud_maps_wood_labels(tmp_path):
    # cols: x y z label   (label 1 == wood, 0 == leaf for this fixture)
    f = tmp_path / "tree.txt"
    f.write_text("0 0 0 1\n1 1 1 0\n2 2 2 1\n")
    points, gt = load_labelled_cloud(f, label_col=3, wood_labels=[1])
    assert points.shape == (3, 3)
    assert points.dtype == np.float64
    assert gt.tolist() == [0, 1, 0]  # label 1 -> wood(0); label 0 -> leaf(1)
    assert gt.dtype == np.uint8


def test_derive_labels_from_woodonly(tmp_path):
    full = tmp_path / "full.txt"
    full.write_text("0 0 0\n1 0 0\n2 0 0\n3 0 0\n4 0 0\n5 0 0\n")
    wood = tmp_path / "wood.txt"
    wood.write_text("0 0 0\n2 0 0\n4 0 0\n")  # points 0,2,4 are wood
    from pipeline.realdata_eval import derive_labels_from_woodonly

    points, gt = derive_labels_from_woodonly(full, wood, tol=1e-6)
    assert points.shape == (6, 3)
    assert gt.tolist() == [0, 1, 0, 1, 0, 1]  # matched -> wood(0), else leaf(1)


def test_decimate_joint_keeps_pairs():
    from pipeline.realdata_eval import _decimate_joint

    n = 1000
    points = np.zeros((n, 3))
    points[:, 0] = np.arange(n)  # x encodes original index
    gt = (np.arange(n) % 3).astype(np.uint8)
    p, g = _decimate_joint(points, gt, max_points=100)
    assert len(g) == 100
    assert p.shape == (100, 3)
    # invariant gt == x % 3 must survive
    assert np.array_equal(g, (p[:, 0].astype(int) % 3).astype(np.uint8))


def test_decimate_joint_noop_when_small():
    from pipeline.realdata_eval import _decimate_joint

    points = np.zeros((5, 3))
    gt = np.array([0, 1, 0, 1, 0], np.uint8)
    p, g = _decimate_joint(points, gt, max_points=100)
    assert len(g) == 5


def test_metrics_from_pred_perfect():
    from pipeline.realdata_eval import _metrics_from_pred

    gt = np.array([0, 0, 1, 1], np.uint8)
    m = _metrics_from_pred(gt.copy(), gt)
    assert m["wood_iou"] == 1.0
    assert m["leaf_iou"] == 1.0
    assert m["mean_iou"] == 1.0
    assert m["accuracy"] == 1.0
    assert m["wood_frac_gt"] == 0.5
    assert m["n_points"] == 4


def test_metrics_from_pred_known_overlap():
    from pipeline.realdata_eval import _metrics_from_pred

    gt = np.array([0, 0, 0, 1], np.uint8)
    pred = np.array([0, 0, 1, 1], np.uint8)
    # wood: inter {0,1}=2, union {0,1,2}=3 -> 2/3 ; leaf: inter {3}=1, union {2,3}=2 -> 1/2
    m = _metrics_from_pred(pred, gt)
    assert m["wood_iou"] == round(2 / 3, 4)
    assert m["leaf_iou"] == 0.5
