"""Photogrammetry pipeline — tree photos -> dense point cloud (.ply).

    # preview the exact commands (no binaries needed)
    python -m photogrammetry.run --images path/to/photos --out tree.ply --dry-run

    # real run (needs COLMAP + OpenMVS on PATH — see docs/PHOTOGRAMMETRY.md)
    python -m photogrammetry.run --images path/to/photos --out tree.ply

Pipeline: COLMAP (Structure-from-Motion) -> OpenMVS (Multi-View Stereo).
The resulting .ply then feeds the ML pipeline:
    python -m pipeline.main process --input tree.ply --output result.json
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from photogrammetry.colmap_wrapper import build_sfm_commands, find_images, run_sfm
from photogrammetry.openmvs_wrapper import build_densify_commands, densify

REQUIRED_BINARIES = ("colmap", "InterfaceCOLMAP", "DensifyPointCloud")
RECOMMENDED_MIN_IMAGES = 15


def check_binaries() -> dict[str, str | None]:
    """Map each required external binary to its resolved path (None if missing)."""
    return {b: shutil.which(b) for b in REQUIRED_BINARIES}


def photos_to_pointcloud(
    image_dir: str | Path,
    out_ply: str | Path,
    *,
    use_gpu: bool = True,
    work_dir: str | Path | None = None,
    dry_run: bool = False,
) -> Path:
    """Reconstruct a dense point cloud from a folder of tree photos.

    Raises:
        ValueError: no images found.
        FileNotFoundError: required binaries missing (real run only).
    """
    image_dir = Path(image_dir)
    out_ply = Path(out_ply)
    images = find_images(image_dir)
    print(f"Found {len(images)} images in {image_dir}")
    if len(images) < RECOMMENDED_MIN_IMAGES:
        print(f"WARNING: only {len(images)} images; >= {RECOMMENDED_MIN_IMAGES} "
              "recommended for a usable reconstruction")

    work = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="photogrammetry_"))
    work.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print("\n# DRY RUN — commands that would run:\n")
        for c in build_sfm_commands(image_dir, work, use_gpu=use_gpu):
            print(" ".join(c))
        for c in build_densify_commands(work, out_ply):
            print(" ".join(c))
        return out_ply

    missing = [b for b, p in check_binaries().items() if p is None]
    if missing:
        raise FileNotFoundError(
            f"Missing binaries {missing} — install COLMAP + OpenMVS "
            "(see docs/PHOTOGRAMMETRY.md), or use --dry-run to preview commands"
        )

    run_sfm(image_dir, work, use_gpu=use_gpu)
    densify(work, out_ply)
    print(f"OK - dense point cloud written: {out_ply}")
    return out_ply


def main() -> None:
    ap = argparse.ArgumentParser(description="Photogrammetry: photos -> .ply (COLMAP + OpenMVS)")
    ap.add_argument("--images", required=True, help="folder of overlapping tree photos")
    ap.add_argument("--out", default="tree.ply", help="output dense point cloud path")
    ap.add_argument("--work-dir", default=None, help="scratch dir (default: temp)")
    ap.add_argument("--no-gpu", action="store_true", help="disable GPU for COLMAP")
    ap.add_argument("--dry-run", action="store_true", help="print commands, do not execute")
    args = ap.parse_args()
    photos_to_pointcloud(
        args.images, args.out,
        use_gpu=not args.no_gpu, work_dir=args.work_dir, dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
