"""COLMAP Structure-from-Motion wrapper.

Reference: Schönberger & Frahm 2016 — Structure-from-Motion Revisited (CVPR)
Docs: https://colmap.github.io/

TODO Phase 3: Implement.
"""

from __future__ import annotations

from pathlib import Path


def run_sfm(
    image_dir: Path,
    output_dir: Path,
    *,
    use_gpu: bool = True,
) -> Path:
    """Run COLMAP automatic reconstruction.

    Args:
        image_dir: Directory with 30-50 JPEG images of the tree
        output_dir: Where to write sparse + dense reconstruction
        use_gpu: Use GPU for feature matching (recommended)

    Returns:
        Path to output sparse .ply point cloud.
    """
    raise NotImplementedError("Implement in Phase 3 — wrap colmap CLI")
