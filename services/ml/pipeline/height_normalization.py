"""Step 2: Height normalization — subtract DTM from each point.

After this step, ground points have Z ≈ 0 and tree points have Z = true height
above ground (regardless of underlying terrain).

TODO Phase 1: Implement using Open3D + scipy interpolation.
"""

from __future__ import annotations

from pathlib import Path


def normalize_height(input_path: str | Path, output_path: str | Path) -> None:
    """Normalize heights by subtracting interpolated DTM.

    Algorithm:
    1. Extract ground points
    2. Build DTM via TIN interpolation (scipy.interpolate.griddata)
    3. For each non-ground point: z_norm = z - dtm(x, y)

    Raises:
        ValueError: if input lacks ground classification
    """
    raise NotImplementedError("Implement in Phase 1")
