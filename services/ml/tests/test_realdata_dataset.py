"""Tests for the real-data (Wan) -> PointNet++ training-sample converter."""

from __future__ import annotations

import numpy as np

from training.realdata_dataset import spatial_split, tile_samples


def _grid_cloud(n_per_tile=2000):
    """A cloud spanning 4 tiles along x (tile=2.5 m), half wood / half leaf."""
    rng = np.random.default_rng(0)
    pts, lab = [], []
    for tx in range(4):
        x = rng.uniform(tx * 2.5, tx * 2.5 + 2.5, n_per_tile)
        y = rng.uniform(0.0, 2.5, n_per_tile)
        z = rng.uniform(0.0, 5.0, n_per_tile)
        pts.append(np.column_stack([x, y, z]))
        lab.append(np.arange(n_per_tile) % 2)  # 0=wood, 1=leaf
    return np.vstack(pts), np.concatenate(lab).astype(np.uint8)


def test_tile_samples_shapes_and_labels():
    pts, lab = _grid_cloud()
    x, y, centers = tile_samples(pts, lab, tile=2.5, n_points=64, min_pts=500)
    assert x.shape == (4, 64, 3)
    assert y.shape == (4, 64)
    assert x.dtype == np.float32
    assert y.dtype == np.int64
    assert set(np.unique(y).tolist()) <= {0, 1}
    assert centers.shape == (4, 2)


def test_tile_samples_normalized_to_unit_sphere():
    pts, lab = _grid_cloud()
    x, _, _ = tile_samples(pts, lab, tile=2.5, n_points=128, min_pts=500)
    for sample in x:
        assert np.allclose(sample.mean(axis=0), 0.0, atol=1e-4)
        assert np.max(np.linalg.norm(sample, axis=1)) <= 1.0 + 1e-4


def test_tile_samples_skips_small_tiles():
    pts, lab = _grid_cloud()
    x, _y, centers = tile_samples(pts, lab, tile=2.5, n_points=64, min_pts=10_000)
    assert x.shape[0] == 0
    assert centers.shape[0] == 0


def test_spatial_split_buffer_separates_train_and_test():
    n = 10
    x = np.zeros((n, 4, 3), np.float32)
    y = np.zeros((n, 4), np.int64)
    centers = np.zeros((n, 2))
    centers[:, 0] = np.arange(n)  # x-centers 0..9
    xtr, ytr, xte, yte = spatial_split(x, y, centers, frac=0.5, buffer=2.0, axis=0)
    # cut = 0 + 0.5*9 = 4.5 ; train x < 3.5 -> {0,1,2,3}; test x > 5.5 -> {6,7,8,9}; drop {4,5}
    assert len(xtr) == 4
    assert len(xte) == 4
    assert len(ytr) == 4
    assert len(yte) == 4
