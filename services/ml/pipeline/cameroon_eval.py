"""Evaluate the pipeline against 61 destructively harvested tropical trees.

Momo Takoudjou et al. 2018, Dryad 10.5061/dryad.10hq7, CC0 - scanned, felled and
weighed in semi-deciduous forest in eastern Cameroon. The counterpart to
`demol_eval`, which covers 65 temperate Belgian trees and no harvested mass.

Two things this cohort supports that Demol cannot. It carries `Destructive AGB`,
an oven-dry stump-inclusive mass, so the allometric stage can be scored rather
than only the geometry. And it carries `DBH_L`/`Hauteur_L`, the cohort authors'
own published TLS measurements on these exact clouds, so this pipeline can be
compared against a competent method on identical data instead of only against
the tape.

The tape is not an unambiguous target here. `database.xls` defines `DBH_dest` as
taken "at breast height or above buttresses if present" and records no per-tree
flag, while `qsm.compute_qsm` always fits at 1.30 m. On a buttressed tree the two
describe different cross-sections, so a disagreement is not necessarily a fit
failure. See docs/ml/CAMEROON_EVIDENCE_CHAIN.md and the spec's section 7.
"""

from __future__ import annotations

import csv
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pipeline.demol_eval import _load_xyz

#: The tree with a point cloud and no destructive row. Excluded by keying the
#: cohort on the ground truth, and named here so the exclusion is legible.
CLOUD_WITHOUT_GROUND_TRUTH = 56

#: The archive's own count, frozen so a partial extraction cannot pass quietly.
COHORT_SIZE = 61

#: Clouds whose raw text is not what _load_xyz expects: 31 and 52 open with an
#: R write.table header ("V1" "V2" "V3"), 59 opens with a CloudCompare comment
#: (//X Y Z Scalar_field), and 63 and 68 are comma-delimited throughout instead
#: of the archive's usual whitespace. None of this is in
#: CAMEROON_EVIDENCE_CHAIN.md's "tab-separated X Y Z, no header" description -
#: found only by attempting to load all 61 required trees. Named here so
#: _load_cloud's repair path is not a silent guess, and so a test can pin it.
IRREGULAR_CLOUD_FORMAT_TREE_IDS = frozenset({31, 52, 59, 63, 68})


@dataclass(frozen=True, slots=True)
class CameroonTree:
    """One tropical tree: its cloud, its destructive truth, and the reference TLS."""

    tree_id: int
    points: np.ndarray
    gt_dbh_cm: float
    gt_height_m: float
    gt_agb_kg: float
    gt_volume_m3: float
    gt_stem_volume_m3: float
    wsg_kg_m3: float
    genus: str
    species: str
    #: The cohort authors' published TLS measurements. Not ground truth - a
    #: baseline. See the module docstring.
    reference_dbh_cm: float
    reference_height_m: float
    #: Their hand-corrected QSM total, excluding branches under 5 cm. Not
    #: comparable to gt_volume_m3, which counts everything.
    reference_qsm_volume_m3: float


def resolve_cloud_names(listing: dict[int, list[str]]) -> dict[int, str]:
    """Pick each tree's single cloud file from what its directory contains.

    Nine of the archive's 62 filenames are irregular in five different ways -
    singular `feuille`, an `ID` prefix, a space instead of an underscore, both,
    and no separator at all. Constructing a filename from a tree ID drops those
    nine, so the name is read rather than predicted.

    Args:
        listing: tree ID to the filenames in that tree's directory.

    Returns:
        Tree ID to its single filename.

    Raises:
        ValueError: when a directory holds anything other than one file, because
            an empty directory and an ambiguous one are both unresolved
            questions rather than trees to skip.
    """
    resolved: dict[int, str] = {}
    for tree_id, names in sorted(listing.items()):
        if len(names) != 1:
            raise ValueError(
                f"tree {tree_id} must have exactly one point-cloud file, found "
                f"{len(names)}: {sorted(names)}"
            )
        resolved[tree_id] = names[0]
    return resolved


def read_ground_truth(csv_path: str | os.PathLike[str]) -> dict[int, dict[str, str]]:
    """The committed 61-row table, keyed by tree ID."""
    rows: dict[int, dict[str, str]] = {}
    with Path(csv_path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            tree_id = int(row["tree_id"])
            if tree_id in rows:
                raise ValueError(f"duplicate tree_id in ground truth: {tree_id}")
            rows[tree_id] = row
    if len(rows) != COHORT_SIZE:
        raise ValueError(f"expected {COHORT_SIZE} ground-truth rows, found {len(rows)}")
    return rows


def _looks_like_point_row(line: str) -> bool:
    """True if a line's first three whitespace-separated tokens parse as floats."""
    tokens = line.split()
    if len(tokens) < 3:
        return False
    try:
        for token in tokens[:3]:
            float(token)
    except ValueError:
        return False
    return True


def _repaired_cloud_text(path: Path) -> str:
    """Normalize one cloud's raw text to what _load_xyz expects.

    Commas become spaces on every line - a no-op where there are none, and what
    63 and 68 need since they are comma-delimited throughout. Then at most the
    first three lines are dropped while they fail to parse as a point, which
    covers the one-line header that 31, 52 and 59 carry, with margin to spare
    without silently eating real data: if no numeric line turns up within
    three, this raises rather than returning a file that is short by however
    many lines were dropped.

    Args:
        path: the cloud file to read.

    Returns:
        Whitespace-delimited numeric rows only, newline-terminated.

    Raises:
        ValueError: when no line in the first three parses as a point, because
            that is a genuinely malformed file rather than a differently
            formatted one.
    """
    lines = [line.replace(",", " ") for line in path.read_text(encoding="utf-8").splitlines()]
    skipped = 0
    while lines and not _looks_like_point_row(lines[0]) and skipped < 3:
        lines = lines[1:]
        skipped += 1
    if not lines or not _looks_like_point_row(lines[0]):
        raise ValueError(f"no numeric point row found in the first 3 lines: {path.name}")
    return "\n".join(lines) + "\n"


def _load_cloud(path: Path, *, max_points: int, sample_seed: int) -> np.ndarray:
    """Load one tree's cloud, repairing the handful of irregularly-formatted
    files before handing off to the exact _load_xyz the Demol cohort uses.

    _load_xyz is tried unchanged first, so the 56 regularly-formatted files
    take exactly the path the plan specifies and demol_eval is never modified.
    Only on its "malformed point cloud" failure is the text repaired - see
    _repaired_cloud_text - and retried through that same unmodified function
    from a temporary copy, so every tree in the cohort, repaired or not, is
    still min-Z normalized and subsampled identically.

    Raises:
        ValueError: when the file is empty, or fails to parse even after
            repair - ownership of the error stays with _load_xyz's own
            message in every case except the one this function exists to fix.
    """
    try:
        return _load_xyz(path, max_points=max_points, sample_seed=sample_seed)
    except ValueError as exc:
        if "malformed point cloud" not in str(exc):
            raise
        repaired_text = _repaired_cloud_text(path)
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8", newline=""
        )
        try:
            handle.write(repaired_text)
            handle.close()
            return _load_xyz(Path(handle.name), max_points=max_points, sample_seed=sample_seed)
        except ValueError as retry_exc:
            raise ValueError(
                f"malformed point cloud even after header/delimiter repair: {path.name}"
            ) from retry_exc
        finally:
            Path(handle.name).unlink(missing_ok=True)


def load_cameroon_cohort(
    archive_root: str | os.PathLike[str],
    ground_truth_csv: str | os.PathLike[str],
    *,
    max_points: int = 20_000,
    sample_seed: int = 0,
) -> list[CameroonTree]:
    """Load the cohort, keyed on the ground truth rather than the directory listing.

    The archive holds 62 cloud directories and 61 destructive rows. Keying on the
    clouds would produce a 62-tree cohort with one tree that cannot be scored;
    keying on the table produces 61 and makes the exclusion explicit.

    Points are min-Z normalized and deterministically subsampled by the same
    `_load_xyz` the Demol path uses, so the two cohorts are measured the same
    way. Clouds here reach 3.4 million points, so the cap is doing real work and
    the caveat in docs/ml/WHAT_CI_DOES_NOT_CHECK.md applies to both.

    Raises:
        FileNotFoundError: when the archive layout is not the expected one.
        ValueError: when a tree in the ground truth has no cloud, or a cloud
            directory is empty or ambiguous.
    """
    root = Path(archive_root)
    cloud_root = root / "Points_clouds"
    if not cloud_root.is_dir():
        raise FileNotFoundError(f"missing Points_clouds directory: {cloud_root}")

    listing: dict[int, list[str]] = {}
    for directory in sorted(cloud_root.iterdir()):
        if not directory.is_dir() or not directory.name.startswith("ID_"):
            continue
        listing[int(directory.name.removeprefix("ID_"))] = sorted(
            item.name for item in directory.iterdir() if item.is_file()
        )
    names = resolve_cloud_names(listing)

    truth = read_ground_truth(ground_truth_csv)
    missing = sorted(set(truth) - set(names))
    if missing:
        raise ValueError(f"ground-truth trees with no point cloud: {missing}")

    cohort: list[CameroonTree] = []
    for tree_id in sorted(truth):
        row = truth[tree_id]
        points = _load_cloud(
            cloud_root / f"ID_{tree_id}" / names[tree_id],
            max_points=max_points,
            sample_seed=sample_seed,
        )
        cohort.append(
            CameroonTree(
                tree_id=tree_id,
                points=points,
                gt_dbh_cm=float(row["dbh_dest_cm"]),
                gt_height_m=float(row["height_dest_m"]),
                gt_agb_kg=float(row["agb_dest_kg"]),
                gt_volume_m3=float(row["volume_total_dest_m3"]),
                gt_stem_volume_m3=float(row["volume_stem_dest_m3"]),
                wsg_kg_m3=float(row["wsg_ind_kg_m3"]),
                genus=row["genus"],
                species=row["species"],
                reference_dbh_cm=float(row["dbh_tls_cm"]),
                reference_height_m=float(row["height_tls_m"]),
                reference_qsm_volume_m3=float(row["volume_total_reference_qsm_m3"]),
            )
        )
    return cohort
