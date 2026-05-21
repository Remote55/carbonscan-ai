"""Step 3: Canopy Height Model (Pit-free CHM).

Reference: Khosravipour et al. 2014 — "Generating Pit-free Canopy Height Models
from Airborne Lidar" (Photogrammetric Engineering & Remote Sensing, 80(9))

TODO Phase 1: Implement using rasterio + numpy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


def compute_chm(
    points: "np.ndarray",
    resolution: float = 0.5,
    thresholds: tuple[float, ...] = (0, 10, 20, 30, 40, 50),
    subcircle: float = 0.2,
) -> "np.ndarray":
    """Compute pit-free Canopy Height Model.

    Args:
        points: (N, 3) array of normalized XYZ
        resolution: Cell size in meters
        thresholds: Multi-threshold for pit-free algorithm
        subcircle: Subcircle radius for filling pits

    Returns:
        2D numpy array of max height per cell.
    """
    raise NotImplementedError("Implement in Phase 1 — pitfree algorithm")
