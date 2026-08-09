"""The Phase C gate: does photogrammetry of a real trunk measure anything?

Nobody knows yet. The wrappers shell out to COLMAP and OpenMVS, the sparse cloud
from SfM may or may not have enough points on a trunk to fit a circle at 1.3 m,
and dense reconstruction may not be reachable without a GPU. Building the rest
of the path before answering that is building on a guess.

    python -m scripts.photogrammetry_gate --photos ./tree-photos \\
        --marker-side-m 0.20 --taped-dbh-cm 27.4

What it does, in order, stopping at the first thing that fails:

  1. Are the external binaries present?
  2. Is there a scale reference in the photographs?   <- cheap, and decisive
  3. Reconstruct.
  4. Scale, measure, compare against the tape.

Step 2 comes before step 3 deliberately. Reconstruction takes minutes to hours;
a photo set with no marker produces a cloud with no unit, and every diameter
from it is meaningless however good the geometry looks.

Verdict: under 10% error is a pass. Over, or too few points to fit a circle at
breast height, means this path needs dense reconstruction — and that is worth
knowing before any of it is wired into the API.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import numpy as np


def _fail(stage: str, detail: str, **extra: object) -> int:
    print(json.dumps({"verdict": "BLOCKED", "stage": stage, "detail": detail, **extra},
                     ensure_ascii=False, indent=2))
    return 1


@click.command()
@click.option("--photos", required=True, type=click.Path(exists=True, file_okay=False))
@click.option("--marker-side-m", required=True, type=float,
              help="Printed marker side, measured with a ruler. The only real unit here.")
@click.option("--taped-dbh-cm", required=True, type=float,
              help="The tree's diameter at 1.3 m, measured with a tape.")
@click.option("--taped-height-m", type=float, default=None)
@click.option("--work-dir", type=click.Path(file_okay=False), default=None)
@click.option("--pass-threshold", type=float, default=0.10, show_default=True)
def main(
    photos: str,
    marker_side_m: float,
    taped_dbh_cm: float,
    taped_height_m: float | None,
    work_dir: str | None,
    pass_threshold: float,
) -> None:
    """Run one real tree through photos -> cloud -> measurement and report."""
    from photogrammetry.run import check_binaries
    from photogrammetry.scale import check_photoset_for_scale_reference

    photo_dir = Path(photos)

    # 1. Binaries.
    binaries = check_binaries()
    missing = sorted(name for name, path in binaries.items() if path is None)
    if missing:
        sys.exit(_fail(
            "binaries",
            f"not installed: {', '.join(missing)}. Sparse SfM alone may be enough for "
            "this gate; if pycolmap is importable it can stand in for the colmap "
            "binary, but OpenMVS has no wheel and dense reconstruction needs it.",
            missing=missing,
        ))

    # 2. Scale reference. Cheap, and it decides whether step 3 is worth running.
    reference = check_photoset_for_scale_reference(photo_dir)
    if not reference["usable"]:
        sys.exit(_fail("scale_reference", str(reference["reason"]), **reference))

    # 3. Reconstruct.
    from photogrammetry.run import photos_to_pointcloud

    out_dir = Path(work_dir) if work_dir else photo_dir.parent / "gate-work"
    out_dir.mkdir(parents=True, exist_ok=True)
    cloud_path = out_dir / "dense.ply"
    try:
        photos_to_pointcloud(photo_dir, cloud_path)
    except Exception as exc:  # noqa: BLE001 - the point is to report, not to raise
        sys.exit(_fail("reconstruction", f"{type(exc).__name__}: {exc}"))

    # 4. Scale it, measure it, compare.
    #
    # The marker's corners have to be located in the reconstruction, not just in
    # the photographs. COLMAP can triangulate them from the pixel detections,
    # which is the remaining piece of plumbing; until a real photo set exists to
    # develop it against, this reports what it has rather than pretending.
    from pipeline.realdata_eval import load_point_cloud
    from pipeline.single_tree import measure_single_tree

    cloud = np.asarray(load_point_cloud(cloud_path), dtype=np.float64)
    print(json.dumps({
        "stage": "reconstructed",
        "cloud_path": str(cloud_path),
        "points": int(len(cloud)),
        "scale_reference": reference,
        "note": (
            "Cloud is in reconstruction units. Triangulating the marker corners "
            "into these coordinates is the step that turns this into metres."
        ),
    }, ensure_ascii=False, indent=2))

    result = measure_single_tree(cloud)
    if not result.measured:
        sys.exit(_fail(
            "measurement",
            f"the cloud produced no measurement: {result.excluded_reason}. If this is "
            "QSM_LOW_FIT_QUALITY or WOOD_EMPTY, the sparse cloud is too thin at "
            "breast height and this path needs dense reconstruction.",
            points=int(len(cloud)),
        ))

    error = abs(result.dbh_cm - taped_dbh_cm) / taped_dbh_cm
    verdict = "PASS" if error <= pass_threshold else "FAIL"
    print(json.dumps({
        "verdict": verdict,
        "dbh_cm_unscaled": result.dbh_cm,
        "taped_dbh_cm": taped_dbh_cm,
        "relative_error": error,
        "height_m_unscaled": result.height_m,
        "taped_height_m": taped_height_m,
        "fit_quality": result.model_quality,
        "wood_points": result.wood_point_count,
        "threshold": pass_threshold,
        "caveat": (
            "Units are reconstruction units unless the cloud was scaled. Compare "
            "only after applying ScaleEstimate.apply()."
        ),
    }, ensure_ascii=False, indent=2))
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
