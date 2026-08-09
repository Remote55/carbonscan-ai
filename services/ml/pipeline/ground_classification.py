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
we ship a lighter-weight heuristic: per-grid k-th-lowest point, with a vertical
band threshold. On the synthetic plots and on NEON tiles it agrees with PDAL's
CSF to within ±2% of ground point count. Phase 2 will swap in true CSF.

That agreement was measured when the candidate was a percentile of each cell's
points. It is not evidence for the current rank-based candidate, and both
comparisons were against plots whose ground was visible; see GROUND_RANK.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

#: Which point, counting up from the lowest in a grid cell, is taken as the
#: ground candidate. 1 would be the true minimum and would follow any single
#: low outlier; 3 tolerates two of them. It is deliberately not a fraction of
#: the cell's population — see the note in classify_ground_array.
GROUND_RANK = 3


def classify_ground_array(
    points: np.ndarray,
    *,
    grid_resolution: float = 1.0,
    z_threshold: float = 0.3,
) -> np.ndarray:
    """Classify ground vs non-ground points using a grid-based heuristic.

    Algorithm:
    1. Partition XY space into `grid_resolution` × `grid_resolution` cells
    2. In each cell, the candidate ground elevation is the GROUND_RANK-th
       lowest Z — an order statistic from the bottom, so it does not move when
       the cell fills up with trunk and branch returns
    3. Any point within `z_threshold` meters of its cell's candidate ground
       elevation is labelled ground

    Args:
        points: (N, 3) array of XYZ coordinates (meters)
        grid_resolution: Cell size for the XY grid (meters)
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
    ny = int(iy.max()) + 1
    cell_key = ix * ny + iy  # flatten 2D → 1D; injective because iy < ny

    # Index the cells that actually hold points, not every cell the bounding box
    # could contain. The array used to be sized nx*ny, so its cost followed the
    # square of the plot's span rather than the amount of data: four points a
    # hundred metres apart needed 1.6 MB, the same four points a hundred
    # kilometres apart needed about 75 GB. Nothing upstream bounds extent - the
    # byte limit, the vertex-count limit and the 200k subsample all pass a
    # 200-byte file straight through - so this had to stop being extent-shaped
    # rather than acquire a cap. Occupied cells never outnumber points, which
    # makes this O(N) and removes the failure mode instead of bounding it.
    cell_ids, cell_id = np.unique(cell_key, return_inverse=True)

    # Per-cell ground-candidate elevation
    ground_z = np.full(len(cell_ids), np.inf)
    # Vectorised per-cell order statistic via argsort/groupby pattern
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
        cell_z = np.sort(sorted_z[start:end])
        # A rank from the bottom, not a percentile of everything in the cell.
        #
        # A percentile asks "how far up this cell's points is the 5% mark",
        # which is only the ground when most of the cell is ground. Under a
        # stem it is not: a 1 m cell holding 10,000 trunk and branch returns
        # over 50 ground returns puts the 5% mark 500 points above the lowest,
        # which is somewhere up the trunk. Measured on one Demol tree dropped
        # onto flat ground, cells that were 97-99% tree returned ground
        # candidates of 0.23, 4.09, 4.16, 7.95 and 10.03 m where the true
        # ground sat at -0.04 m. The estimator failed hardest exactly where it
        # matters, directly beneath the trees being measured.
        #
        # The k-th lowest point does not care how many tree points share the
        # cell. k > 1 keeps one stray low return - a multipath ghost below the
        # surface - from dragging the whole cell down with it.
        #
        # k has to shrink on sparse cells, though, and only shrink. An airborne
        # sweep can leave a cell holding two points, one ground and one canopy;
        # asking for the 3rd lowest there returns the canopy and calls it the
        # floor. So k climbs to GROUND_RANK as the cell fills and is capped
        # there - it never tracks the population upward, which is the failure
        # the percentile had.
        rank = min(GROUND_RANK, 1 + len(cell_z) // 25)
        ground_z[cell] = cell_z[rank - 1]

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
