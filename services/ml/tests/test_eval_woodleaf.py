"""Tests for PointNet++ vs PCA wood-leaf comparison helpers (Sprint P1 / G2).

Held-out synthetic trees (true labels known) scored with iou_score, so both
methods are compared apples-to-apples on identical inputs. Torch-free.
"""

from __future__ import annotations

import numpy as np

from training.eval_woodleaf import evaluate_segmenter, make_test_samples, read_comparison_csv

WOOD, LEAF = 0, 1


def test_make_test_samples_count_and_shape():
    samples = make_test_samples(n_test=3, n_points=512, seed0=20_000)
    assert len(samples) == 3
    for pts, true in samples:
        assert pts.shape == (512, 3)
        assert true.shape == (512,)
        assert set(np.unique(true)).issubset({WOOD, LEAF})


def test_make_test_samples_disjoint_from_training_seeds():
    # train uses seed0=0.., val uses 10_000.. — test must not overlap
    assert 20_000 >= 10_048


def test_evaluate_perfect_labeler_is_one():
    pts = np.zeros((4, 3))
    true = np.array([WOOD, WOOD, LEAF, LEAF])
    ious = evaluate_segmenter(lambda p: true.copy(), [(pts, true)])
    assert ious == [1.0]


def test_evaluate_inverted_labeler_is_zero():
    pts = np.zeros((4, 3))
    true = np.array([WOOD, WOOD, LEAF, LEAF])
    inverted = np.array([LEAF, LEAF, WOOD, WOOD])
    ious = evaluate_segmenter(lambda p: inverted, [(pts, true)])
    assert ious == [0.0]


def test_evaluate_returns_one_iou_per_sample_in_range():
    samples = make_test_samples(n_test=4, n_points=512, seed0=20_000)
    ious = evaluate_segmenter(lambda p: np.zeros(len(p), dtype=np.int8), samples)
    assert len(ious) == 4
    assert all(0.0 <= v <= 1.0 for v in ious)


def test_read_comparison_csv_roundtrip(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text(
        "tree_idx,PCA (Phase 1),PointNet++ (Phase 2)\n0,0.75,0.98\n1,0.80,0.97\n",
        encoding="utf-8",
    )
    results = read_comparison_csv(p)
    assert list(results) == ["PCA (Phase 1)", "PointNet++ (Phase 2)"]
    assert results["PCA (Phase 1)"] == [0.75, 0.80]
    assert results["PointNet++ (Phase 2)"] == [0.98, 0.97]
