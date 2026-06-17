"""Build labelled wood/leaf training samples from the synthetic generator.

`pipeline.synthetic.generate_synthetic_plot` already returns per-point class
labels (0=ground, 1=wood, 2=leaf), so it doubles as a free, reproducible
source of labelled training data for the Phase 2 PointNet++ model — no 5 GB
download, no manual annotation needed to get started.

All functions here are torch-free (pure NumPy) so they are testable on any
machine; the model consumes the produced arrays on a GPU.
"""

from __future__ import annotations

import numpy as np

from pipeline.synthetic import CLASS_GROUND, CLASS_WOOD, generate_synthetic_plot

# Output label convention — matches pipeline.wood_leaf_separation (WOOD=0, LEAF=1)
WOOD = 0
LEAF = 1


def normalize_points(points: np.ndarray) -> np.ndarray:
    """Center a point cloud at the origin and scale it into the unit sphere.

    Returns points with centroid at 0 and a maximum radius of 1 — the standard
    input normalisation for PointNet-family models so they are translation- and
    scale-invariant.
    """
    points = np.asarray(points, dtype=np.float64)
    centered = points - points.mean(axis=0)
    scale = np.linalg.norm(centered, axis=1).max()
    if scale > 0:
        centered = centered / scale
    return centered


def _resample_indices(n_available: int, n_points: int, rng: np.random.Generator) -> np.ndarray:
    """Pick exactly n_points indices (no replacement if enough, else with)."""
    replace = n_available < n_points
    return rng.choice(n_available, size=n_points, replace=replace)


def make_woodleaf_sample(seed: int, n_points: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """Generate one normalised, fixed-size labelled tree point cloud.

    Args:
        seed: RNG seed (also varies the tree geometry — deterministic)
        n_points: fixed number of points to return (for batching)

    Returns:
        points: (n_points, 3) float32, centroid-centered, unit-sphere scaled
        labels: (n_points,) int64 with WOOD=0, LEAF=1 (ground removed)
    """
    points, labels, _ = generate_synthetic_plot(n_trees=1, seed=seed)
    keep = labels != CLASS_GROUND
    tree_pts = points[keep]
    tree_lbl = labels[keep]
    out_lbl = np.where(tree_lbl == CLASS_WOOD, WOOD, LEAF).astype(np.int64)

    pts_norm = normalize_points(tree_pts).astype(np.float32)

    rng = np.random.default_rng(seed)
    sel = _resample_indices(len(pts_norm), n_points, rng)
    return pts_norm[sel], out_lbl[sel]


def build_woodleaf_dataset(
    n_samples: int,
    n_points: int = 2048,
    seed0: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Build a batched dataset of labelled tree samples.

    Returns:
        x: (n_samples, n_points, 3) float32
        y: (n_samples, n_points) int64
    """
    xs, ys = [], []
    for i in range(n_samples):
        pts, lbl = make_woodleaf_sample(seed=seed0 + i, n_points=n_points)
        xs.append(pts)
        ys.append(lbl)
    return np.stack(xs).astype(np.float32), np.stack(ys).astype(np.int64)
