"""Step 6: Quantitative Structure Model — cylinder fitting on wood points.

Reference: Raumonen et al. 2013 — TreeQSM (Remote Sensing, 5(2), 491-520)

Computes:
- DBH (Diameter at Breast Height, 1.3 m above ground)
- Total wood volume (m³)
- Branch structure

TODO Phase 2: Implement cylinder fitting via RANSAC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


@dataclass
class QsmResult:
    """QSM output for a single tree."""

    dbh_cm: float
    height_m: float
    stem_volume_m3: float
    branches_volume_m3: float
    total_volume_m3: float
    n_cylinders: int
    model_quality: float  # 0-1 fit quality


def compute_qsm(wood_points: "np.ndarray") -> QsmResult:
    """Fit cylinders to wood points to estimate volume + DBH.

    Args:
        wood_points: (N, 3) array of XYZ — wood points only (no leaves)

    Returns:
        QsmResult with measurements.

    Algorithm Overview:
        1. Skeleton extraction (find centerline of wood structure)
        2. Branching detection (where stem splits)
        3. Cylinder fit per segment using RANSAC
        4. Sum cylinder volumes
        5. Extract DBH from cylinder at z=1.3m
    """
    raise NotImplementedError("Implement in Phase 2 — cylinder fitting")


def measure_dbh(wood_points: "np.ndarray", target_height_m: float = 1.3) -> float:
    """Measure DBH from cross-section at given height.

    Simple alternative to full QSM — fits a circle to the points
    intersecting the horizontal plane at 1.3 m above ground.

    Args:
        wood_points: (N, 3) array, Z = height above ground
        target_height_m: Height to measure at (default 1.3 m = breast height)

    Returns:
        DBH in centimeters.

    TODO Phase 1: Implement simple version.
    """
    raise NotImplementedError("Implement in Phase 1 — RANSAC circle fitting")
