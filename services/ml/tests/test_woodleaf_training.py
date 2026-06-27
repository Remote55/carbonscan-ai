"""Tests for the torch-free parts of Phase 2 wood-leaf training.

The PointNet++ model + training loop need PyTorch (run on Colab/Kaggle GPU);
those are smoke-tested only when torch is importable. The pieces that decide
correctness — IoU metric and the synthetic labelled dataset — are pure NumPy
and tested here on any machine.
"""

from __future__ import annotations

import numpy as np
import pytest

from training.metrics import iou_score
from training.woodleaf_dataset import (
    build_woodleaf_dataset,
    make_woodleaf_sample,
    normalize_points,
)

# Class convention matches pipeline.wood_leaf_separation: WOOD = 0, LEAF = 1
WOOD, LEAF = 0, 1


# --- iou_score -------------------------------------------------------------


def test_iou_perfect_match_is_one():
    pred = np.array([WOOD, WOOD, LEAF, LEAF])
    target = np.array([WOOD, WOOD, LEAF, LEAF])
    assert iou_score(pred, target, positive_class=WOOD) == 1.0


def test_iou_disjoint_is_zero():
    pred = np.array([WOOD, WOOD, WOOD, WOOD])
    target = np.array([LEAF, LEAF, LEAF, LEAF])
    assert iou_score(pred, target, positive_class=WOOD) == 0.0


def test_iou_half_overlap():
    # wood predicted at {0,1}; wood actual at {1,2}
    pred = np.array([WOOD, WOOD, LEAF, LEAF])
    target = np.array([LEAF, WOOD, WOOD, LEAF])
    # intersection {1}=1, union {0,1,2}=3  ->  1/3
    assert iou_score(pred, target, positive_class=WOOD) == 1 / 3


def test_iou_absent_class_returns_one():
    # class WOOD absent in both pred and target -> they agree -> 1.0
    pred = np.array([LEAF, LEAF, LEAF])
    target = np.array([LEAF, LEAF, LEAF])
    assert iou_score(pred, target, positive_class=WOOD) == 1.0


# --- normalize_points ------------------------------------------------------


def test_normalize_centers_at_origin():
    pts = np.array([[10.0, 10.0, 10.0], [12.0, 14.0, 16.0], [8.0, 6.0, 4.0]])
    out = normalize_points(pts)
    assert np.allclose(out.mean(axis=0), 0.0, atol=1e-6)


def test_normalize_scales_to_unit_sphere():
    pts = np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0], [0.0, 4.0, 0.0]])
    out = normalize_points(pts)
    radii = np.linalg.norm(out, axis=1)
    assert np.isclose(radii.max(), 1.0)
    assert radii.max() <= 1.0 + 1e-6


# --- make_woodleaf_sample --------------------------------------------------


def test_sample_has_fixed_n_points():
    pts, labels = make_woodleaf_sample(seed=1, n_points=2048)
    assert pts.shape == (2048, 3)
    assert labels.shape == (2048,)


def test_sample_labels_are_binary_and_both_present():
    _, labels = make_woodleaf_sample(seed=1, n_points=2048)
    assert set(np.unique(labels)).issubset({WOOD, LEAF})
    # a real tree has both a trunk/branches and a canopy
    assert (labels == WOOD).any()
    assert (labels == LEAF).any()


def test_sample_is_deterministic():
    pts_a, lbl_a = make_woodleaf_sample(seed=7, n_points=1024)
    pts_b, lbl_b = make_woodleaf_sample(seed=7, n_points=1024)
    assert np.array_equal(pts_a, pts_b)
    assert np.array_equal(lbl_a, lbl_b)


def test_sample_is_normalized():
    pts, _ = make_woodleaf_sample(seed=3, n_points=1024)
    assert np.linalg.norm(pts, axis=1).max() <= 1.0 + 1e-6


# --- build_woodleaf_dataset ------------------------------------------------


def test_build_dataset_shapes():
    x, y = build_woodleaf_dataset(n_samples=3, n_points=512, seed0=0)
    assert x.shape == (3, 512, 3)
    assert y.shape == (3, 512)


def test_build_dataset_dtypes():
    x, y = build_woodleaf_dataset(n_samples=2, n_points=256, seed0=0)
    assert x.dtype == np.float32
    assert y.dtype == np.int64


# --- PointNet++ model (torch — skipped if not installed; runs on Colab/CI) --


def test_pointnet2_forward_shape():
    pytest.importorskip("torch")
    import torch

    from training.pointnet2_seg import PointNet2SegSSG

    model = PointNet2SegSSG(num_classes=2).eval()
    out = model(torch.randn(2, 1024, 3))
    assert out.shape == (2, 1024, 2)


def test_pointnet2_one_train_step_reduces_loss():
    pytest.importorskip("torch")
    import torch

    from training.pointnet2_seg import PointNet2SegSSG

    torch.manual_seed(0)
    model = PointNet2SegSSG(num_classes=2).train()
    x = torch.randn(2, 1024, 3)
    y = torch.randint(0, 2, (2, 1024))
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    logits = model(x).reshape(-1, 2)
    loss0 = torch.nn.functional.cross_entropy(logits, y.reshape(-1))
    loss0.backward()
    opt.step()
    opt.zero_grad()
    logits = model(x).reshape(-1, 2)
    loss1 = torch.nn.functional.cross_entropy(logits, y.reshape(-1))
    # one Adam step on the same batch should not increase the loss
    assert loss1.item() <= loss0.item() + 1e-4


# --- pipeline integration: WoodLeafSegmenter pointnet backend --------------


def test_segmenter_pointnet_backend_runs(tmp_path):
    pytest.importorskip("torch")
    import torch

    from pipeline.wood_leaf_separation import WoodLeafSegmenter
    from training.pointnet2_seg import PointNet2SegSSG

    ckpt = tmp_path / "model.pt"
    torch.save({"state_dict": PointNet2SegSSG(2).state_dict(), "num_classes": 2}, ckpt)

    seg = WoodLeafSegmenter(model_path=str(ckpt), backend="pointnet")
    seg.load()
    points = np.random.default_rng(0).standard_normal((1000, 3)).astype(np.float32)
    labels = seg.segment(points)

    assert labels.shape == (1000,)
    assert set(np.unique(labels)).issubset({WOOD, LEAF})


def test_segmenter_pointnet_falls_back_when_too_few_points(tmp_path):
    pytest.importorskip("torch")
    import torch

    from pipeline.wood_leaf_separation import WoodLeafSegmenter
    from training.pointnet2_seg import PointNet2SegSSG

    ckpt = tmp_path / "model.pt"
    torch.save({"state_dict": PointNet2SegSSG(2).state_dict(), "num_classes": 2}, ckpt)

    seg = WoodLeafSegmenter(model_path=str(ckpt), backend="pointnet")
    seg.load()
    # fewer points than the model's first sampling layer needs -> rule-based fallback
    points = np.random.default_rng(0).standard_normal((100, 3)).astype(np.float32)
    labels = seg.segment(points)
    assert labels.shape == (100,)


def test_class_weights_balanced_upweights_minority():
    pytest.importorskip("torch")  # train_woodleaf imports torch at module load
    from training.train_woodleaf import _class_weights

    y = np.array([WOOD] * 25 + [LEAF] * 75)  # 25% wood, 75% leaf
    w = _class_weights(y, num_classes=2)
    # sklearn 'balanced': total / (n_classes * count)
    assert np.isclose(w[WOOD], 100 / (2 * 25))   # 2.0
    assert np.isclose(w[LEAF], 100 / (2 * 75), atol=1e-4)  # 0.667
    assert w[WOOD] > w[LEAF]  # rare wood class up-weighted
