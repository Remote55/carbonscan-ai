"""Step 4: Individual Tree Detection (ITD) via Watershed segmentation.

Reference: Roussel et al. 2020 — lidR package (Remote Sensing of Environment)

Phase 1 implementation: scikit-image's `watershed` seeded by local maxima.
Phase 2 may add marker-controlled variants (e.g., Dalponte 2016) for very
dense canopy.
"""

from __future__ import annotations

import numpy as np
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

from .canopy_height_model import ChmTransform


def watershed_segmentation(
    chm: np.ndarray,
    *,
    min_height: float = 4.0,
    min_distance: int = 3,
) -> np.ndarray:
    """Run watershed on a Canopy Height Model.

    Args:
        chm: 2D array of canopy heights (NaN where empty)
        min_height: Minimum tree height (meters) — pixels below are ignored
        min_distance: Min distance between treetops in pixels

    Returns:
        (H, W) int32 array with tree IDs (0 = no tree, 1..N = tree)
    """
    if chm.ndim != 2:
        raise ValueError(f"Expected 2D CHM, got shape {chm.shape}")

    chm_clean = np.where(np.isnan(chm), 0.0, chm).astype(np.float32)
    mask = chm_clean >= min_height
    if not mask.any():
        return np.zeros_like(chm_clean, dtype=np.int32)

    coords = peak_local_max(
        chm_clean,
        min_distance=min_distance,
        threshold_abs=min_height,
        labels=mask.astype(np.int32),
    )
    if len(coords) == 0:
        return np.zeros_like(chm_clean, dtype=np.int32)

    markers = np.zeros_like(chm_clean, dtype=np.int32)
    for i, (r, c) in enumerate(coords, start=1):
        markers[r, c] = i

    # Watershed on the negative CHM (treats peaks as basins)
    labels = watershed(-chm_clean, markers=markers, mask=mask)
    return labels.astype(np.int32)


def detect_trees(
    chm: np.ndarray,
    *,
    min_height: float = 4.0,
    min_distance: int = 3,
) -> np.ndarray:
    """Alias kept for orchestrator backward compatibility."""
    return watershed_segmentation(
        chm, min_height=min_height, min_distance=min_distance
    )


def assign_points_to_trees(
    normalized_points: np.ndarray,
    tree_labels_2d: np.ndarray,
    transform: ChmTransform,
    *,
    min_height: float = 1.5,
) -> np.ndarray:
    """Assign each non-ground point to a tree ID by XY lookup.

    Args:
        normalized_points: (N, 3) XYZ where Z is height-above-ground
        tree_labels_2d: (H, W) tree IDs from watershed_segmentation
        transform: ChmTransform from compute_chm_array
        min_height: Below this Z (m), the point is treated as unassigned (ground/shrub)

    Returns:
        (N,) int32 array of tree IDs (0 = unassigned)
    """
    out = np.zeros(len(normalized_points), dtype=np.int32)
    x = normalized_points[:, 0]
    y = normalized_points[:, 1]
    z = normalized_points[:, 2]

    row, col = transform.world_to_pixel(x, y)
    in_bounds = (
        (row >= 0)
        & (row < transform.n_rows)
        & (col >= 0)
        & (col < transform.n_cols)
        & (z >= min_height)
    )
    rows_in = row[in_bounds]
    cols_in = col[in_bounds]
    out[in_bounds] = tree_labels_2d[rows_in, cols_in]
    return out


def extract_tree_points(
    points: np.ndarray,
    tree_ids: np.ndarray,
) -> dict[int, np.ndarray]:
    """Group a point cloud into a dict of per-tree arrays.

    Args:
        points: (N, 3) full point cloud (normalized)
        tree_ids: (N,) tree IDs from assign_points_to_trees

    Returns:
        Dict mapping tree_id → (Nk, 3) array (excluding tree_id == 0).
    """
    result: dict[int, np.ndarray] = {}
    unique_ids = np.unique(tree_ids)
    for tid in unique_ids:
        if tid == 0:
            continue
        result[int(tid)] = points[tree_ids == tid]
    return result
