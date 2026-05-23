"""Step 2: Height normalization — subtract DTM from each point.

After this step, ground points have Z ≈ 0 and tree points have Z = true height
above ground (regardless of underlying terrain).

Phase 1 implementation uses K-nearest-neighbor averaging of ground points to
estimate the terrain elevation under each non-ground point. Faster and more
robust than full Delaunay triangulation for typical plot sizes (< 1 ha).
Phase 2 will swap in `scipy.interpolate.griddata` for production runs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


def normalize_height_array(
    points: np.ndarray,
    ground_mask: np.ndarray,
    *,
    k_neighbors: int = 5,
    distance_weight_power: float = 2.0,
) -> np.ndarray:
    """Subtract interpolated ground elevation from every point's Z.

    For each point, look up the K nearest ground points (by XY distance) and
    use their inverse-distance-weighted mean Z as the terrain elevation under
    that point. Subtract that from the point's Z.

    Args:
        points: (N, 3) XYZ array
        ground_mask: (N,) bool — True where the point is ground (from step 1)
        k_neighbors: Number of ground neighbors for IDW interpolation
        distance_weight_power: IDW exponent (2 = inverse-square, classic)

    Returns:
        (N, 3) array with Z normalized so ground ≈ 0 and tree Z = height above ground.
    """
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {points.shape}")
    if len(ground_mask) != len(points):
        raise ValueError("ground_mask length must match points length")

    ground_xy = points[ground_mask, :2]
    ground_z = points[ground_mask, 2]
    if len(ground_xy) == 0:
        raise ValueError("No ground points — cannot normalize heights")

    k = min(k_neighbors, len(ground_xy))
    tree = cKDTree(ground_xy)
    dists, idx = tree.query(points[:, :2], k=k)

    if k == 1:
        terrain_z = ground_z[idx]
    else:
        # Inverse-distance weighting
        weights = 1.0 / (dists ** distance_weight_power + 1e-9)
        weights /= weights.sum(axis=1, keepdims=True)
        terrain_z = np.sum(ground_z[idx] * weights, axis=1)

    out = points.copy()
    out[:, 2] = points[:, 2] - terrain_z
    return out


def normalize_height(input_path: str | Path, output_path: str | Path) -> None:
    """File-based wrapper around normalize_height_array (LAS I/O).

    Requires step 1 (ground_classification) to have been run on input first.
    """
    import laspy

    las = laspy.read(str(input_path))
    points = np.column_stack([las.x, las.y, las.z])
    ground_mask = np.array(las.classification) == 2
    if not ground_mask.any():
        raise ValueError(
            "Input LAS has no ground classification — run classify_ground first"
        )

    normalized = normalize_height_array(points, ground_mask)
    las.z = normalized[:, 2]
    las.write(str(output_path))
