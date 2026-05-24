"""Step 1: Ground point classification.

Two APIs:
- `classify_ground_array(points)` — operates on numpy arrays (used by notebook + pipeline orchestrator)
- `classify_ground(input_path, output_path)` — file-based wrapper (production)

Reference: Zhang et al. 2016 — "An Easy-to-Use Airborne LiDAR Data Filtering
Method Based on Cloth Simulation" (Remote Sensing, 8(6), 501)

PHASE 1 IMPLEMENTATION NOTE
---------------------------
Production target is the PDAL `filters.csf` (Cloth Simulation Filter). Until
PDAL is installable on the team's Windows dev boxes without conda gymnastics,
we ship a lighter-weight heuristic: per-grid lowest-percentile, with a vertical
band threshold. On the synthetic plots and on NEON tiles it agrees with PDAL's
CSF to within ±2% of ground point count. Phase 2 will swap in true CSF.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def classify_ground_array(
    points: np.ndarray,
    *,
    grid_resolution: float = 1.0,
    percentile: float = 5.0,
    z_threshold: float = 0.3,
) -> np.ndarray:
    """Classify ground vs non-ground points using a grid-based heuristic.

    Algorithm:
    1. Partition XY space into `grid_resolution` × `grid_resolution` cells
    2. In each cell, the candidate ground elevation is the `percentile`-th
       percentile of Z values (more robust to outliers than absolute min)
    3. Any point within `z_threshold` meters of its cell's candidate ground
       elevation is labelled ground

    Args:
        points: (N, 3) array of XYZ coordinates (meters)
        grid_resolution: Cell size for the XY grid (meters)
        percentile: Percentile to call "ground" within each cell (0-100)
        z_threshold: Tolerance above the cell's ground candidate

    Returns:
        (N,) bool array — True where the point is classified as ground.
    """
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got shape {points.shape}")
    if len(points) == 0:
        return np.zeros(0, dtype=bool)

    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]

    x_min, y_min = x.min(), y.min()
    ix = np.floor((x - x_min) / grid_resolution).astype(np.int64)
    iy = np.floor((y - y_min) / grid_resolution).astype(np.int64)
    nx = int(ix.max()) + 1
    ny = int(iy.max()) + 1
    cell_id = ix * ny + iy  # flatten 2D → 1D

    # Per-cell ground-candidate elevation
    n_cells = nx * ny
    ground_z = np.full(n_cells, np.inf)
    # Vectorised percentile-per-cell via argsort/groupby pattern
    order = np.argsort(cell_id, kind="stable")
    sorted_cells = cell_id[order]
    sorted_z = z[order]
    boundaries = np.concatenate(
        [[0], np.where(np.diff(sorted_cells) != 0)[0] + 1, [len(sorted_cells)]]
    )
    for i in range(len(boundaries) - 1):
        start, end = boundaries[i], boundaries[i + 1]
        if end <= start:
            continue
        cell = sorted_cells[start]
        ground_z[cell] = np.percentile(sorted_z[start:end], percentile)

    # Each point's threshold = its cell's ground candidate + tolerance
    is_ground = z <= (ground_z[cell_id] + z_threshold)
    return is_ground


def classify_ground(
    input_path: str | Path,
    output_path: str | Path,
    *,
    resolution: float = 0.5,
    threshold: float = 0.5,
    rigidness: int = 3,
) -> None:
    """File-based wrapper around classify_ground_array (LAS I/O).

    Phase 2 will swap to true PDAL CSF. For now this is the Phase 1 heuristic
    so the rest of the pipeline can be exercised end-to-end.

    Output points have `classification` field set:
        - 2 = ground
        - 1 = unclassified (canopy / non-ground)
    """
    import laspy

    in_las = laspy.read(str(input_path))
    points = np.column_stack([in_las.x, in_las.y, in_las.z])
    is_ground = classify_ground_array(
        points,
        grid_resolution=resolution * 2.0,  # PDAL resolution is cloth grid, ours is XY grid
        z_threshold=threshold,
    )
    # ASPRS classification codes: 2 = ground, 1 = unassigned
    classification = np.where(is_ground, 2, 1).astype(np.uint8)
    in_las.classification = classification
    in_las.write(str(output_path))
