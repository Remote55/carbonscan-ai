"""Step 4: Individual Tree Detection (ITD) via Watershed segmentation.

Reference: Roussel et al. 2020 — lidR package (Remote Sensing of Environment)

TODO Phase 1: Implement using scikit-image.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


def detect_trees(
    chm: "np.ndarray",
    *,
    min_height: float = 4.0,
    min_distance: int = 3,
) -> "np.ndarray":
    """Watershed segmentation on Canopy Height Model.

    Args:
        chm: 2D array from compute_chm()
        min_height: Minimum tree height to be detected (meters)
        min_distance: Minimum pixel distance between treetops

    Returns:
        2D int array same shape as CHM, with tree IDs (0 = no tree)

    Algorithm:
        1. Find local maxima in CHM (treetops)
        2. Use maxima as watershed markers
        3. Flood-fill from markers to boundaries
    """
    raise NotImplementedError("Implement in Phase 1 — use skimage.segmentation.watershed")


def extract_tree_points(
    points: "np.ndarray",
    chm_labels: "np.ndarray",
    chm_origin: tuple[float, float],
    chm_resolution: float,
) -> dict[int, "np.ndarray"]:
    """Group point cloud points by tree ID.

    Returns:
        Dict mapping tree_id (int) → (N, 3) point array.
    """
    raise NotImplementedError("Implement in Phase 1")
