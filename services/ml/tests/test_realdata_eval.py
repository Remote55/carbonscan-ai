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
    _p, g = _decimate_joint(points, gt, max_points=100)
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


def _toy_tree(seed=0):
    """A vertical wood trunk + a scattered leaf blob (enough points for PCA)."""
    rng = np.random.default_rng(seed)
    z = np.linspace(0, 5, 200)
    trunk = np.column_stack([rng.normal(0, 0.02, 200), rng.normal(0, 0.02, 200), z])
    leaf = rng.normal([0, 0, 5], 0.6, size=(200, 3))
    points = np.vstack([trunk, leaf])
    gt = np.concatenate([np.zeros(200, np.uint8), np.ones(200, np.uint8)])
    return points, gt


def test_evaluate_cloud_returns_metrics(tmp_path):
    from pipeline.realdata_eval import evaluate_cloud

    points, gt = _toy_tree()
    m = evaluate_cloud(points, gt, backend="tlsep")
    assert set(m) == {
        "wood_iou", "leaf_iou", "mean_iou", "accuracy",
        "wood_frac_gt", "wood_frac_pred", "n_points",
    }
    assert 0.0 <= m["mean_iou"] <= 1.0
    assert m["n_points"] == 400


def test_evaluate_cloud_decimates(tmp_path):
    from pipeline.realdata_eval import evaluate_cloud

    points, gt = _toy_tree()
    m = evaluate_cloud(points, gt, backend="tlsep", max_points=150)
    assert m["n_points"] == 150


def test_evaluate_dataset_aggregates(monkeypatch):
    import pipeline.realdata_eval as re

    def fake_eval(points, gt, *, backend, model_path=None, max_points=200_000):
        return {
            "wood_iou": 0.80, "leaf_iou": 0.60, "mean_iou": 0.70,
            "accuracy": 0.9, "wood_frac_gt": 0.5, "wood_frac_pred": 0.5,
            "n_points": len(gt),
        }

    monkeypatch.setattr(re, "evaluate_cloud", fake_eval)
    trees = [
        ("t1", np.zeros((4, 3)), np.array([0, 0, 1, 1], np.uint8)),
        ("t2", np.zeros((4, 3)), np.array([0, 1, 0, 1], np.uint8)),
    ]
    result = re.evaluate_dataset(trees, backends=["tlsep"])
    assert len(result["per_tree"]) == 2
    s = result["summary"]["tlsep"]
    assert s["n_trees"] == 2
    assert s["mean_wood_iou"] == 0.8
    assert s["mean_leaf_iou"] == 0.6
    assert s["mean_iou"] == 0.7


def test_cli_eval_realdata_wan(tmp_path):
    import json

    from click.testing import CliRunner

    from pipeline.main import cli

    # two toy labelled trees: cols x y z label, wood label = 0
    root = tmp_path / "wan"
    root.mkdir()
    for name, seed in [("a.txt", 1), ("b.txt", 2)]:
        pts, gt = _toy_tree(seed)
        rows = np.column_stack([pts, gt.astype(float)])
        np.savetxt(root / name, rows)

    out = tmp_path / "wan_iou.json"
    res = CliRunner().invoke(
        cli,
        [
            "eval-realdata", "--dataset", "wan", "--root", str(root),
            "--backend", "tlsep", "--out", str(out),
            "--label-col", "3", "--wood-labels", "0",
        ],
    )
    assert res.exit_code == 0, res.output
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["summary"]["tlsep"]["n_trees"] == 2
    assert len(data["per_tree"]) == 2
