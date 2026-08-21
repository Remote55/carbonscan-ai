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
from typing import IO

import numpy as np

from pipeline import allometric, tver
from pipeline.demol_eval import _exact_non_negative_int, _exact_positive_int, _load_xyz

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

#: A leading line is only ever dropped as a header up to this many lines. All
#: three header shapes in the archive are one line; the margin covers a
#: two-line header without being large enough to eat several real points
#: unnoticed if the true cause is a corrupt file rather than a header at all.
MAX_HEADER_LINES = 3


@dataclass(frozen=True, slots=True)
class CameroonTree:
    """One tropical tree: its cloud, its destructive truth, and the reference TLS."""

    tree_id: int
    points: np.ndarray
    #: True if this tree's raw cloud text needed repair - a non-numeric header
    #: line dropped, or a comma delimiter turned into whitespace - before
    #: _load_xyz would parse it. The durable record of which measurements come
    #: from rewritten bytes rather than the archive's own; see _load_cloud.
    #: Not logged per tree: this field is the log.
    cloud_was_repaired: bool
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


def _is_all_numeric_tokens(line: str) -> bool:
    """True if every whitespace-separated token on this line parses as a float.

    Distinguishes a short data row from an actual header. "1 2" is two valid
    numbers and not a plausible header - every header shape in this archive is
    text ("V1" "V2" "V3", or a // comment) - so it is corruption rather than a
    title row, and _write_repaired_cloud raises on it rather than silently
    dropping what may be a real point the way a genuine header is dropped.
    """
    tokens = line.split()
    if not tokens:
        return False
    try:
        for token in tokens:
            float(token)
    except ValueError:
        return False
    return True


def _repair_line(line: str) -> str:
    """Turn commas into spaces on this line, unless whitespace alone already
    splits it into three or more tokens.

    A genuinely comma-delimited row, like 63 and 68's, has no whitespace at
    all, so line.split() yields exactly one token and the substitution is
    exactly what turns "-6.217,-9.782,-0.832" into three parseable fields. A
    decimal-comma row such as "1,5 2,5 3,5" is already whitespace-delimited
    and yields three tokens; substituting there would silently turn it into
    six - 1, 5, 2, 5, 3, 5 - and load three wrong points with no error. This
    archive does not use decimal commas, so refusing the substitution whenever
    three or more tokens already exist costs nothing on the real cohort and
    turns that corruption into the same loud failure np.loadtxt would give any
    other malformed row.
    """
    if len(line.split()) < 3:
        return line.replace(",", " ")
    return line


#: Lines buffered before one destination.writelines() call. ID_63 is 3.5
#: million lines; batching avoids that many individual write() calls into the
#: temp file. The batch itself holds at most a few MB regardless of file size
#: - three orders of magnitude below the 549.6 MB the old materialize-then-
#: join approach peaked at (measured with tracemalloc; that peak is what this
#: function replaces, not a timing claim - tracemalloc's own per-allocation
#: bookkeeping dominates elapsed time for a loop processing millions of lines,
#: enough to make timing under it meaningless as a measure of real cost).
_WRITE_BATCH_LINES = 50_000


def _write_repaired_cloud(source: Path, destination: IO[str]) -> None:
    """Stream one cloud's raw text into destination, repaired line by line.

    Reads source one line at a time and repairs each independently - see
    _repair_line - buffering _WRITE_BATCH_LINES of them at a time before one
    destination.writelines() call. Every line still gets its own comma/decimal
    check; only the write is batched. That keeps memory bounded by the batch
    size rather than the file size, unlike reading the whole file, splitting
    it into a list, and rejoining it, which peaked at 549.6 MB on ID_63's
    77.5 MB file (both figures measured with tracemalloc).

    At most MAX_HEADER_LINES leading lines are dropped while they are not a
    point row, which covers the one-line header 31, 52 and 59 carry. A dropped
    line that is fully numeric but short, such as "1 2", is not a header by
    that same standard - every header in this archive is text - so it raises
    instead of silently costing a point the way a real header is silently
    dropped.

    Args:
        source: the cloud file to read.
        destination: an open, writable text stream to write repaired lines
            into - a temp file in production, an io.StringIO in tests.

    Raises:
        ValueError: when no line in the first MAX_HEADER_LINES parses as a
            point, or a dropped line is numeric but short - both mean a
            genuinely malformed file rather than a differently formatted one.
    """
    found_data = False
    batch: list[str] = []
    with source.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle):
            line = raw_line.rstrip("\r\n")
            repaired = _repair_line(line)
            if not found_data:
                if _looks_like_point_row(repaired):
                    found_data = True
                elif _is_all_numeric_tokens(repaired):
                    raise ValueError(
                        f"point row has fewer than 3 numeric fields: {source.name}: {line!r}"
                    )
                elif line_number >= MAX_HEADER_LINES:
                    raise ValueError(
                        f"no numeric point row found in the first {MAX_HEADER_LINES} "
                        f"lines: {source.name}"
                    )
                else:
                    continue
            batch.append(repaired)
            batch.append("\n")
            if len(batch) >= _WRITE_BATCH_LINES:
                destination.writelines(batch)
                batch = []
    destination.writelines(batch)
    if not found_data:
        raise ValueError(
            f"no numeric point row found in the first {MAX_HEADER_LINES} lines: {source.name}"
        )


def _load_cloud(path: Path, *, max_points: int, sample_seed: int) -> tuple[np.ndarray, bool]:
    """Load one tree's cloud, repairing the handful of irregularly-formatted
    files before handing off to the exact _load_xyz the Demol cohort uses.

    _load_xyz is tried unchanged first, so the 56 regularly-formatted files
    take exactly the path the plan specifies and demol_eval is never modified.
    Only on its "malformed point cloud" failure is the text repaired - see
    _write_repaired_cloud - and retried through that same unmodified function
    from a temporary copy, so every tree in the cohort, repaired or not, is
    still min-Z normalized and subsampled identically.

    The temp handle is closed through a `with` block before _load_xyz reopens
    it and before the `finally` unlinks it: closing inside the try body used
    to leave the handle open if the write itself raised, and unlink() on an
    open file raises PermissionError on Windows, masking the original error.

    Returns:
        The points, and whether this cloud needed repair - the provenance
        CameroonTree.cloud_was_repaired carries.

    Raises:
        ValueError: when the file is empty, or fails to parse even after
            repair - ownership of the error stays with _load_xyz's own
            message in every case except the one this function exists to fix.
    """
    try:
        return _load_xyz(path, max_points=max_points, sample_seed=sample_seed), False
    except ValueError as exc:
        if "malformed point cloud" not in str(exc):
            raise
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8", newline=""
        )
        temp_path = Path(handle.name)
        try:
            with handle:
                _write_repaired_cloud(path, handle)
            return (
                _load_xyz(temp_path, max_points=max_points, sample_seed=sample_seed),
                True,
            )
        except ValueError as retry_exc:
            raise ValueError(
                f"malformed point cloud even after header/delimiter repair: {path.name}"
            ) from retry_exc
        finally:
            temp_path.unlink(missing_ok=True)


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
        TypeError: when max_points or sample_seed is not an exact int.
        ValueError: when max_points is not positive, sample_seed is negative, a
            tree in the ground truth has no cloud, or a cloud directory is
            empty or ambiguous.
        FileNotFoundError: when the archive layout is not the expected one.
    """
    max_points = _exact_positive_int(max_points, name="max_points")
    sample_seed = _exact_non_negative_int(sample_seed, name="sample_seed")

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
        points, cloud_was_repaired = _load_cloud(
            cloud_root / f"ID_{tree_id}" / names[tree_id],
            max_points=max_points,
            sample_seed=sample_seed,
        )
        cohort.append(
            CameroonTree(
                tree_id=tree_id,
                points=points,
                cloud_was_repaired=cloud_was_repaired,
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


#: DBH bands, half-open and covering every positive diameter.
#:
#: 50 cm is the boundary that matters. Below it the cohort authors' own TLS
#: measurement agrees with the tape to +0.30 cm across 31 trees; above 100 cm it
#: loses 6.29 cm on average and 63.6 cm at worst. That is the buttress confound,
#: and it belongs to the measurement problem rather than to any one
#: implementation.
SIZE_BAND_EDGES_CM: tuple[tuple[str, float, float], ...] = (
    ("under_50", 0.0, 50.0),
    ("50_to_100", 50.0, 100.0),
    ("100_and_over", 100.0, float("inf")),
)

#: Above this diameter the tape may have been placed above a buttress rather than
#: at 1.30 m, so our figure and the ground truth are not the same measurement.
UNCONFOUNDED_MAX_DBH_CM = 50.0


def geometry_row(
    *,
    tree_id: int,
    measured_dbh_cm: float,
    measured_height_m: float,
    gt_dbh_cm: float,
    gt_height_m: float,
    reference_dbh_cm: float,
    reference_height_m: float,
) -> dict[str, float | int]:
    """One tree's geometry, scored against the tape and against the reference.

    Both targets are reported for every tree because neither alone answers the
    question. The tape is the truth but is not always taken at 1.30 m; the
    reference is taken the same way ours is and faces the identical confound, so
    it says whether a large error is this pipeline's or the problem's.
    """
    return {
        "tree_id": tree_id,
        "measured_dbh_cm": measured_dbh_cm,
        "measured_height_m": measured_height_m,
        "gt_dbh_cm": gt_dbh_cm,
        "gt_height_m": gt_height_m,
        "dbh_error_cm": measured_dbh_cm - gt_dbh_cm,
        "height_error_m": measured_height_m - gt_height_m,
        "dbh_error_vs_reference_cm": measured_dbh_cm - reference_dbh_cm,
        "height_error_vs_reference_m": measured_height_m - reference_height_m,
    }


def small_stem_dbh_mae_cm(rows: list[dict[str, float]]) -> float:
    """DBH MAE over stems small enough that the tape was certainly at 1.30 m.

    The headline figure for this pipeline's diameter accuracy, because it is the
    only subset where our measurement and the ground truth are the same
    measurement. The all-trees figure is reported too, as an upper bound.
    """
    errors = [
        abs(float(row["dbh_error_cm"]))
        for row in rows
        if float(row["gt_dbh_cm"]) < UNCONFOUNDED_MAX_DBH_CM
    ]
    if not errors:
        raise ValueError("no stems below the unconfounded diameter threshold")
    return sum(errors) / len(errors)


#: The T-VER row for the forest this cohort stands in. Eastern Cameroon is
#: semi-deciduous, which is the stand type T-VER assigns this equation. Fixed
#: here rather than chosen at read time: picking the best-fitting row after
#: seeing the answers is the selection error the spec's section 6 forbids.
TVER_FOREST_TYPE = "mixed_deciduous"


def chave_agb_kg(*, dbh_cm: float, height_m: float, wood_density_kg_m3: float) -> float:
    """Chave 2014 above-ground biomass, in kilograms.

    Called directly rather than through `calculate_carbon` because this compares
    biomass against a weighed mass. `calculate_carbon` continues to the carbon
    fraction and the 44/12 ratio, and neither belongs between a model's output
    and a scale reading.

    `calculate_agb_chave_pantropical` takes density in kg/m3 and divides by 1000
    internally, which is why `wsg_ind_kg_m3` is stored in kg/m3 and passed
    straight through.
    """
    return allometric.calculate_agb_chave_pantropical(
        dbh_cm, height_m, wood_density_kg_m3
    )


def tver_agb_kg(*, dbh_cm: float, height_m: float) -> float:
    """T-VER above-ground biomass for this cohort's forest type, in kilograms.

    Thailand's official methodology, scored on African trees because that is the
    closest check available without field access in Thailand. The equations take
    no density term - they are fitted on D and H alone - so nothing about the
    species enters here.
    """
    return tver.aboveground_biomass(TVER_FOREST_TYPE, dbh_cm, height_m).total_kg


def mass_row(
    *, tree_id: int, gt_agb_kg: float, route_a_agb_kg: float, route_b_agb_kg: float
) -> dict[str, float | int]:
    """One tree's biomass error, split between measurement and equation.

    Route A costs the tree from what the pipeline measured. Route B costs it from
    the tape and the felled height. Both go through the same allometric model, so
    their difference isolates the measurement.

    Raises:
        ValueError: when the harvested mass is not positive, since every figure
            here is a percentage of it.
    """
    if not gt_agb_kg > 0.0:
        raise ValueError(f"harvested mass must be positive, got {gt_agb_kg}")
    route_a_ape = abs(route_a_agb_kg - gt_agb_kg) / gt_agb_kg * 100.0
    route_b_ape = abs(route_b_agb_kg - gt_agb_kg) / gt_agb_kg * 100.0
    return {
        "tree_id": tree_id,
        "gt_agb_kg": gt_agb_kg,
        "route_a_agb_kg": route_a_agb_kg,
        "route_b_agb_kg": route_b_agb_kg,
        "route_a_ape_pct": route_a_ape,
        "route_b_ape_pct": route_b_ape,
        "measurement_share_pct": route_a_ape - route_b_ape,
    }


#: The largest gt_dbh_cm among the 65 Belgian trees qsm.TOTAL_TREE_FORM_FACTOR
#: and qsm.STEM_FORM_FACTOR were fitted on - read directly from
#: docs/evidence/demol_65/result.json's per_tree rows, not estimated. No tree
#: in that calibration cohort is this large; a measured DBH above it asks the
#: taper equation to extrapolate past everything it was ever checked against.
FORM_FACTOR_CALIBRATION_MAX_DBH_CM = 46.63239833

#: The pipeline's reason code for a DBH past the calibration range above. Not
#: wired into main.py's ExcludedSegment.reason_code Literal - this evaluation
#: calls qsm.compute_qsm directly and never runs that orchestrator (see the
#: "gate" block in result.json) - named identically so a future caller that
#: does wire it in reuses this vocabulary instead of inventing a second one.
DBH_ABOVE_CALIBRATED_RANGE = "DBH_ABOVE_CALIBRATED_RANGE"


def dbh_above_calibrated_range_reason(measured_dbh_cm: float) -> str | None:
    """DBH_ABOVE_CALIBRATED_RANGE when a DBH exceeds every tree the taper
    constants were fitted on; None otherwise.

    Needs no correlation and no threshold search - only the range the
    Belgian calibration cohort covers, a fact about that cohort rather than a
    statistic measured on this one. 31 of the 60 measurable Cameroon trees
    exceed it, including 2 of the 31 trees under the 50 cm buttress boundary:
    a majority of this cohort's reported volumes already come from a taper
    equation extrapolating past its own calibration, regardless of whether
    the DBH fit itself was good.

    This is a diagnostic predicate, not an enforced refusal: cameroon_eval
    calls qsm.compute_qsm directly, so nothing here stops a volume from being
    computed and reported for this evaluation. Wiring an actual refusal into
    the live pipeline (main.py, alongside QSM_LOW_FIT_QUALITY) would be a
    separate change outside this evaluation's scope.

    Args:
        measured_dbh_cm: what qsm.measure_dbh reported for this tree.
    """
    if measured_dbh_cm > FORM_FACTOR_CALIBRATION_MAX_DBH_CM:
        return DBH_ABOVE_CALIBRATED_RANGE
    return None


#: A large stem (measured_dbh_cm >= UNCONFOUNDED_MAX_DBH_CM) whose
#: breast-height circle fit explains less than 60% of its slice is suspected
#: of fitting a buttress cross-section rather than the trunk - or of some
#: other measurement problem the geometry alone cannot tell apart from one.
#: This is the pipeline's only way to know: the archive records no per-tree
#: buttress flag (see the module docstring), so a real user has neither a
#: tape nor a database either.
#:
#: Chosen from the measured distribution in
#: docs/evidence/cameroon_61/result.json, not guessed in advance. Across the
#: 60 measurable Cameroon trees, model_quality (the RANSAC inlier ratio
#: qsm.QsmResult already carries) correlates with abs(dbh_error_cm) at
#: Spearman rho=-0.72 (p=6e-11); rho=-0.68 (p=8e-9, n=55) with the five trees
#: above the 120 cm RANSAC search ceiling removed, so those five are not
#: carrying the whole effect (see qsm._ransac_circle_fit's max_radius_m and
#: CAMEROON_EVIDENCE_CHAIN.md). Restricted to the 31 trees under
#: UNCONFOUNDED_MAX_DBH_CM, where buttressing is not a confound, the
#: correlation is weaker but still significant (rho=-0.48, p=0.006): fit
#: quality is not a pure buttress detector, it tracks measurement trust more
#: generally, and it happens to concentrate on large stems in this cohort.
#:
#: Threshold sweep, gated on measured_dbh_cm >= UNCONFOUNDED_MAX_DBH_CM
#: (n=60 measurable trees; "false alarm" = flagged despite gt_dbh_cm < 50):
#:
#:     threshold   n flagged   false alarms   notable miss
#:     0.30        10          0              tree 12 (-77.59 cm) missed
#:     0.40        14          0              tree 12 (-77.59 cm) missed
#:     0.50        19          0              tree 12 (-77.59 cm) missed
#:     0.60        23          0              tree 63 (-9.71 cm) missed
#:     0.70        26          0              adds trees 31, 74: errors
#:                                            under 0.6 cm, not real misses
#:
#: 0.60 is where tree 12 - the single largest error in the confounded
#: population after the four other over-ceiling trees, -77.59 cm on a
#: 180.3 cm stem - stops being missed, while the false-alarm count on the
#: unconfounded band stays zero and the next threshold up (0.70) only adds
#: two trees whose actual error is under a centimetre. Without the size
#: gate, 0.60 alone would also flag two under-50 cm trees (errors -1.46 and
#: -2.38 cm); UNCONFOUNDED_MAX_DBH_CM removes both at no cost, since it is
#: already this module's boundary for "buttressing is not a confound here".
#:
#: What it still misses, reported rather than hidden: tree 63 (90.5 cm,
#: -9.71 cm error, model_quality 0.6033) sits just above this line and is
#: not flagged - a real limit of this detector, not a case selected around.
DBH_FIT_BUTTRESS_SUSPECT_MAX_INLIER_RATIO = 0.60

#: The pipeline's reason code for a suspected buttress fit. Same wiring note
#: as DBH_ABOVE_CALIBRATED_RANGE above.
DBH_FIT_BUTTRESS_SUSPECT = "DBH_FIT_BUTTRESS_SUSPECT"


def dbh_fit_buttress_suspect_reason(
    *, measured_dbh_cm: float, model_quality: float
) -> str | None:
    """DBH_FIT_BUTTRESS_SUSPECT when a large stem's circle fit is too poor
    to trust; None otherwise.

    See DBH_FIT_BUTTRESS_SUSPECT_MAX_INLIER_RATIO for the measured evidence
    behind the threshold, including its known misses.

    Args:
        measured_dbh_cm: what qsm.measure_dbh reported for this tree - the
            only DBH a live pipeline run has. Ground truth is not an input a
            real user could supply.
        model_quality: the RANSAC inlier ratio from the same measurement
            (qsm.QsmResult.model_quality).
    """
    if (
        measured_dbh_cm >= UNCONFOUNDED_MAX_DBH_CM
        and model_quality < DBH_FIT_BUTTRESS_SUSPECT_MAX_INLIER_RATIO
    ):
        return DBH_FIT_BUTTRESS_SUSPECT
    return None
