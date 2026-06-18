"""COLMAP Structure-from-Motion wrapper.

Wraps the COLMAP CLI to turn a folder of overlapping tree photos into a sparse
reconstruction + undistorted images ready for OpenMVS densification.

Reference: Schönberger & Frahm 2016 — Structure-from-Motion Revisited (CVPR)
Docs: https://colmap.github.io/   Install: see docs/PHOTOGRAMMETRY.md

The command-building functions are pure (no subprocess) so they are unit-
testable without COLMAP installed; run_sfm() executes them.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def find_images(image_dir: str | Path) -> list[Path]:
    """Return sorted image files in a directory (jpg/jpeg/png).

    Raises:
        ValueError: if the directory has no images.
    """
    image_dir = Path(image_dir)
    images = sorted(p for p in image_dir.glob("*") if p.suffix.lower() in IMAGE_EXTS)
    if not images:
        raise ValueError(f"No images (jpg/jpeg/png) found in {image_dir}")
    return images


def build_sfm_commands(
    image_dir: str | Path,
    work_dir: str | Path,
    *,
    use_gpu: bool = True,
) -> list[list[str]]:
    """Build the COLMAP command sequence (feature -> match -> map -> undistort).

    Returns a list of argv lists; the final step writes undistorted images +
    cameras to ``work_dir/dense`` (COLMAP format) for OpenMVS.
    """
    image_dir = Path(image_dir)
    work_dir = Path(work_dir)
    db = work_dir / "database.db"
    sparse = work_dir / "sparse"
    dense = work_dir / "dense"
    gpu = "1" if use_gpu else "0"
    return [
        ["colmap", "feature_extractor",
         "--database_path", str(db), "--image_path", str(image_dir),
         "--SiftExtraction.use_gpu", gpu],
        ["colmap", "exhaustive_matcher",
         "--database_path", str(db), "--SiftMatching.use_gpu", gpu],
        ["colmap", "mapper",
         "--database_path", str(db), "--image_path", str(image_dir),
         "--output_path", str(sparse)],
        ["colmap", "image_undistorter",
         "--image_path", str(image_dir), "--input_path", str(sparse / "0"),
         "--output_path", str(dense), "--output_type", "COLMAP"],
    ]


def run_sfm(
    image_dir: str | Path,
    work_dir: str | Path,
    *,
    use_gpu: bool = True,
    dry_run: bool = False,
) -> Path:
    """Run COLMAP SfM. Returns the dense (undistorted) output dir.

    Raises:
        FileNotFoundError: if the `colmap` binary is not on PATH.
    """
    image_dir = Path(image_dir)
    work_dir = Path(work_dir)
    find_images(image_dir)  # validate input
    (work_dir / "sparse").mkdir(parents=True, exist_ok=True)
    commands = build_sfm_commands(image_dir, work_dir, use_gpu=use_gpu)

    if dry_run:
        for c in commands:
            print(" ".join(c))
        return work_dir / "dense"

    if shutil.which("colmap") is None:
        raise FileNotFoundError("COLMAP not found on PATH — see docs/PHOTOGRAMMETRY.md")
    for c in commands:
        subprocess.run(c, check=True)
    return work_dir / "dense"
