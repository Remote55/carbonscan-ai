"""Step 3: Canopy Height Model.

Phase 1: max-Z-per-cell rasterization with a small pit-fill morphology step.
Phase 2: full pit-free algorithm (Khosravipour et al. 2014) with multi-threshold
         layers — improves tree detection in dense, multi-storey canopy.

Reference: Khosravipour et al. 2014 — "Generating Pit-free Canopy Height Models
from Airborne Lidar" (Photogrammetric Engineering & Remote Sensing, 80(9))
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import grey_closing


@dataclass(frozen=True)
class ChmTransform:
    """Geo-transform mapping CHM pixel (row, col) ↔ world (x, y)."""

    x_min: float
    y_min: float
    resolution: float
    n_rows: int
    n_cols: int

    def world_to_pixel(self, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        col = np.floor((x - self.x_min) / self.resolution).astype(np.int64)
        row = np.floor((y - self.y_min) / self.resolution).astype(np.int64)
        return row, col

    def pixel_to_world(self, row: np.ndarray, col: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x = self.x_min + (col + 0.5) * self.resolution
        y = self.y_min + (row + 0.5) * self.resolution
        return x, y


def compute_chm_array(
    normalized_points: np.ndarray,
    *,
    resolution: float = 0.5,
    closing_size: int = 2,
    min_height: float = 0.0,
) -> tuple[np.ndarray, ChmTransform]:
    """Compute Canopy Height Model from height-normalized points.

    Args:
        normalized_points: (N, 3) array where Z is height-above-ground
        resolution: Pixel size (meters)
        closing_size: Morphological closing footprint (pixels) to fill pits.
                      Use 0 to disable.
        min_height: Discard points below this Z before rasterizing (meters)

    Returns:
        chm: (H, W) float32 array — max canopy height per cell, NaN where empty
        transform: ChmTransform with geo-reference info
    """
    if normalized_points.ndim != 2 or normalized_points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {normalized_points.shape}")

    pts = normalized_points[normalized_points[:, 2] >= min_height]
    if len(pts) == 0:
        raise ValueError("No points above min_height after filtering")

    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    x_min, x_max = float(x.min()), float(x.max())
    y_min, y_max = float(y.min()), float(y.max())
    n_cols = int(np.ceil((x_max - x_min) / resolution)) + 1
    n_rows = int(np.ceil((y_max - y_min) / resolution)) + 1

    # Initialize to -inf so np.maximum.at can accumulate correctly.
    # (Initializing to NaN breaks np.maximum.at because max(NaN, x) → NaN.)
    chm = np.full((n_rows, n_cols), -np.inf, dtype=np.float32)
    col = np.clip(np.floor((x - x_min) / resolution).astype(np.int64), 0, n_cols - 1)
    row = np.clip(np.floor((y - y_min) / resolution).astype(np.int64), 0, n_rows - 1)

    # max-Z reduction per cell — np.maximum.at handles repeated indices correctly.
    np.maximum.at(chm, (row, col), z)
    # Empty cells (no points landed in them) stay at -inf; mark them as NaN.
    empty_mask = np.isinf(chm)
    chm[empty_mask] = np.nan

    # Morphological closing to fill small pits — phase-2 will replace with
    # the multi-threshold pit-free algorithm
    if closing_size > 0 and empty_mask.any() and (~empty_mask).any():
        filled = np.where(empty_mask, 0.0, chm).astype(np.float32)
        closed = grey_closing(filled, size=(closing_size, closing_size))
        # Use closing only to fill the previously-empty cells
        chm = np.where(empty_mask & (closed > 0), closed, chm)

    transform = ChmTransform(
        x_min=x_min,
        y_min=y_min,
        resolution=resolution,
        n_rows=n_rows,
        n_cols=n_cols,
    )
    return chm, transform


def compute_chm(
    points: np.ndarray,
    resolution: float = 0.5,
    thresholds: tuple[float, ...] = (0, 10, 20, 30, 40, 50),
    subcircle: float = 0.2,
) -> np.ndarray:
    """Legacy entry point — returns CHM array only (no transform).

    Prefer `compute_chm_array` for new code.
    """
    chm, _ = compute_chm_array(points, resolution=resolution)
    return chm
