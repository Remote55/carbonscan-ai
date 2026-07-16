"""Segmented point-cloud PLY export/import (ply-viewer spec §3.1).

Writes a binary_little_endian PLY with per-point class so the web viewer can
colour wood/leaf/ground:
    property float x, float y, float z, uchar class   (class: 0=wood, 1=leaf, 2=ground)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# Packed dtype (no alignment padding) matching the PLY property order.
_PLY_DTYPE = np.dtype([("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("class", "u1")])

_HEADER = (
    "ply\n"
    "format binary_little_endian 1.0\n"
    "comment TreeQ Carbon Platform segmented point cloud (class: 0=wood,1=leaf,2=ground)\n"
    "element vertex {n}\n"
    "property float x\n"
    "property float y\n"
    "property float z\n"
    "property uchar class\n"
    "end_header\n"
)


def write_segmented_ply(points: np.ndarray, classes: np.ndarray, path: str | Path) -> Path:
    """Write XYZ + per-point class to a binary_little_endian PLY.

    Args:
        points: (N, 3) float coordinates
        classes: (N,) class ids (0=wood, 1=leaf, 2=ground)

    Raises:
        ValueError: if shapes are inconsistent.
    """
    points = np.asarray(points, dtype=np.float64)
    classes = np.asarray(classes, dtype=np.uint8)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Expected points (N, 3), got {points.shape}")
    if len(classes) != len(points):
        raise ValueError(f"points ({len(points)}) and classes ({len(classes)}) length mismatch")

    rec = np.empty(len(points), dtype=_PLY_DTYPE)
    rec["x"] = points[:, 0]
    rec["y"] = points[:, 1]
    rec["z"] = points[:, 2]
    rec["class"] = classes

    path = Path(path)
    with path.open("wb") as f:
        f.write(_HEADER.format(n=len(points)).encode("ascii"))
        f.write(rec.tobytes())
    return path


def read_segmented_ply(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Read back a PLY written by write_segmented_ply.

    Returns:
        (points (N,3) float32, classes (N,) uint8)
    """
    path = Path(path)
    raw = path.read_bytes()
    marker = b"end_header\n"
    idx = raw.find(marker)
    if idx < 0:
        raise ValueError(f"Not a PLY with end_header: {path}")
    header = raw[:idx].decode("ascii", "ignore")
    n = next(int(line.split()[-1]) for line in header.splitlines() if line.startswith("element vertex"))
    body = raw[idx + len(marker):]
    rec = np.frombuffer(body, dtype=_PLY_DTYPE, count=n)
    points = np.column_stack([rec["x"], rec["y"], rec["z"]]).astype(np.float32)
    return points, rec["class"].copy()
