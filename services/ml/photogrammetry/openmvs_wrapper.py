"""OpenMVS Multi-View Stereo wrapper.

Densifies COLMAP's undistorted output into a dense point cloud (.ply).

Repo: https://github.com/cdcseacave/openMVS   Install: see docs/PHOTOGRAMMETRY.md

Command-building is pure (unit-testable without OpenMVS); densify() executes it.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def build_densify_commands(work_dir: str | Path, out_ply: str | Path) -> list[list[str]]:
    """Build the OpenMVS command sequence: InterfaceCOLMAP -> DensifyPointCloud.

    Reads ``work_dir/dense`` (COLMAP undistorter output) and produces a dense
    point cloud at ``out_ply``.
    """
    work_dir = Path(work_dir)
    dense = work_dir / "dense"
    scene = work_dir / "scene.mvs"
    return [
        ["InterfaceCOLMAP", "-i", str(dense), "-o", str(scene),
         "--image-folder", str(dense / "images")],
        ["DensifyPointCloud", str(scene), "-o", str(out_ply)],
    ]


def densify(
    work_dir: str | Path,
    out_ply: str | Path,
    *,
    dry_run: bool = False,
) -> Path:
    """Run OpenMVS densification. Returns the dense .ply path.

    Raises:
        FileNotFoundError: if OpenMVS binaries are not on PATH.
    """
    out_ply = Path(out_ply)
    commands = build_densify_commands(work_dir, out_ply)

    if dry_run:
        for c in commands:
            print(" ".join(c))
        return out_ply

    for prog in ("InterfaceCOLMAP", "DensifyPointCloud"):
        if shutil.which(prog) is None:
            raise FileNotFoundError(f"OpenMVS '{prog}' not on PATH — see docs/PHOTOGRAMMETRY.md")
    for c in commands:
        subprocess.run(c, check=True)
    return out_ply
