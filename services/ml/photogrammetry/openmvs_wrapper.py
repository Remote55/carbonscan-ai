"""OpenMVS Multi-View Stereo wrapper.

Densifies COLMAP sparse output → dense point cloud.

Repo: https://github.com/cdcseacave/openMVS

TODO Phase 3: Implement.
"""

from __future__ import annotations

from pathlib import Path


def densify(sparse_ply: Path, output_dir: Path) -> Path:
    """Run OpenMVS DensifyPointCloud.

    Args:
        sparse_ply: Sparse reconstruction from COLMAP
        output_dir: Output directory

    Returns:
        Path to dense .ply point cloud.
    """
    raise NotImplementedError("Implement in Phase 3 — wrap OpenMVS DensifyPointCloud")
