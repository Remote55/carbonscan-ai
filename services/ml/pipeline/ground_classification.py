"""Step 1: Ground point classification using CSF algorithm.

Reference: Zhang et al. 2016 — "An Easy-to-Use Airborne LiDAR Data Filtering
Method Based on Cloth Simulation" (Remote Sensing, 8(6), 501)

Implementation: PDAL CSF filter wrapper.

TODO Phase 1:
- Implement using PDAL pipeline
- Add parameter tuning per forest type (dense vs sparse canopy)
"""

from __future__ import annotations

from pathlib import Path


def classify_ground(
    input_path: str | Path,
    output_path: str | Path,
    *,
    resolution: float = 0.5,
    threshold: float = 0.5,
    rigidness: int = 3,
) -> None:
    """Classify ground vs non-ground points using CSF.

    Args:
        input_path: Input .las/.laz file
        output_path: Output .las file with classification field set
        resolution: Cloth grid resolution in meters (default 0.5)
        threshold: Distance threshold for ground classification (default 0.5)
        rigidness: Cloth rigidness 1 (loose) - 3 (rigid)

    Output points have `classification` field:
        - 2 = ground
        - 1 = unclassified (canopy/non-ground)
    """
    raise NotImplementedError("Implement in Phase 1 — use PDAL filters.csf")
