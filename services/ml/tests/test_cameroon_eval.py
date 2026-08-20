"""The Cameroon tropical cohort: loader, metrics, and the committed ground truth."""

from __future__ import annotations

import csv
import io
import math
from pathlib import Path

import pytest

from pipeline import cameroon_eval

ML_ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH = ML_ROOT / "data" / "cameroon_61" / "ground_truth.csv"

#: Every column the evaluation reads, and nothing it does not.
EXPECTED_COLUMNS = (
    "tree_id",
    "genus",
    "species",
    "dbh_dest_cm",
    "height_dest_m",
    "agb_dest_kg",
    "wsg_ind_kg_m3",
    "volume_total_dest_m3",
    "volume_stem_dest_m3",
    "dbh_tls_cm",
    "height_tls_m",
    "volume_total_reference_qsm_m3",
)

#: Every column that is a measurement rather than an identifier or a name.
#: extract_cameroon_ground_truth.py used to dispatch text-vs-numeric parsing
#: on the source cell's xlrd type, and most of these columns are stored as
#: TEXT cells in the archive - so they were copied through as strings with no
#: call to float() ever made on them. This list is what closes that gap.
NUMERIC_COLUMNS = tuple(c for c in EXPECTED_COLUMNS if c not in ("tree_id", "genus", "species"))


def _rows() -> list[dict[str, str]]:
    with GROUND_TRUTH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_ground_truth_csv_is_committed():
    """The 61 rows live in git, not only inside a 1 GB archive."""
    assert GROUND_TRUTH.is_file(), f"missing {GROUND_TRUTH}"


def test_ground_truth_has_sixty_one_trees_and_the_expected_columns():
    rows = _rows()

    assert len(rows) == 61
    assert tuple(rows[0]) == EXPECTED_COLUMNS


#: The archive's IDs are not contiguous, and 56 is additionally missing from
#: this table because it has a point cloud and no destructive row. Pinned as
#: the full set rather than min/max/count, which two transposed IDs would
#: still pass.
EXPECTED_IDS = (
    1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 15, 18, 28, 29, 31, 32, 52, 54, 55, 57,
    59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
    79, 80, 83, 85, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101,
    102, 103, 104, 105, 106,
)


def test_ground_truth_ids_match_the_archive_exactly():
    """56 is absent: it has a point cloud and no destructive row."""
    ids = tuple(sorted(int(row["tree_id"]) for row in _rows()))

    assert ids == EXPECTED_IDS
    assert 56 not in ids
    assert len(set(ids)) == 61


def test_agb_is_oven_dry_mass_including_the_stump():
    """The check that decides whether comparing against Chave means anything.

    Wood specific gravity is oven-dry mass over green volume, so AGB divided by
    volume times density lands on 1 for an oven-dry mass and near 1.5-2.5 for a
    green one. Measured on the archive: median 1.0074 including the stump.

    This is asserted rather than noted because the whole evaluation rests on it,
    and a future re-extraction that silently picked a different AGB column would
    otherwise pass every other test here.
    """
    ratios = sorted(
        float(row["agb_dest_kg"])
        / (float(row["volume_total_dest_m3"]) * float(row["wsg_ind_kg_m3"]))
        for row in _rows()
    )
    median = ratios[len(ratios) // 2]

    assert 0.98 < median < 1.03, f"AGB does not look oven-dry: median ratio {median}"


def test_units_are_the_ones_the_column_names_claim():
    """The archive gives AGB in Mg and density in g/cm3; this CSV uses kg and kg/m3."""
    rows = _rows()
    agb = [float(row["agb_dest_kg"]) for row in rows]
    wsg = [float(row["wsg_ind_kg_m3"]) for row in rows]

    assert 20.0 < min(agb) < 40.0, "smallest tree should be tens of kg, not tonnes"
    assert 43_000.0 < max(agb) < 44_500.0, "largest tree should be ~43.9 tonnes in kg"
    assert 300.0 < min(wsg) < 400.0, "density should be kg/m3, not g/cm3"


def test_every_numeric_column_is_finite_and_positive():
    """No column is exempt from being parsed as a number.

    Most of NUMERIC_COLUMNS is stored as TEXT cells in the source archive.
    extract_cameroon_ground_truth.py used to copy TEXT cells through as
    strings unparsed, so an NA, an empty cell, or a stray unit label in any of
    them would have landed in this CSV verbatim and never been caught here.
    Calling float() on every cell of every row is what closes that gap.
    """
    for row in _rows():
        for column in NUMERIC_COLUMNS:
            value = float(row[column])
            assert math.isfinite(value), f"{column} not finite for tree {row['tree_id']}: {row[column]!r}"
            assert value > 0.0, f"{column} not positive for tree {row['tree_id']}: {row[column]!r}"


ARCHIVE = ML_ROOT / "data" / "raw" / "dryad_cameroon" / "Trees"
requires_archive = pytest.mark.skipif(
    not (ARCHIVE / "Points_clouds").is_dir(),
    reason="Cameroon archive not present: see docs/ml/CAMEROON_EVIDENCE_CHAIN.md",
)


def test_cloud_paths_are_found_by_listing_not_by_name():
    """Nine of 62 filenames are irregular in five different ways.

    15_sans_feuille.txt is singular, ID63_sans_feuilles.txt is prefixed,
    67_sans feuilles.txt has a space, 74_sans _feuille.txt has both, and
    97sans_feuilles.txt has no separator. Any loader that builds a filename from
    an ID drops nine trees, and a cohort that silently shrinks is the failure
    this project keeps finding.
    """
    listing = {
        1: ["1_sans_feuilles.txt"],
        63: ["ID63_sans_feuilles.txt"],
        97: ["97sans_feuilles.txt"],
    }

    resolved = cameroon_eval.resolve_cloud_names(listing)

    assert resolved == {1: "1_sans_feuilles.txt", 63: "ID63_sans_feuilles.txt", 97: "97sans_feuilles.txt"}


def test_a_tree_directory_holding_two_clouds_is_refused():
    """One file per tree. Two means an ambiguity nobody has resolved."""
    with pytest.raises(ValueError, match="exactly one"):
        cameroon_eval.resolve_cloud_names({4: ["4_a.txt", "4_b.txt"]})


def test_an_empty_tree_directory_is_refused():
    with pytest.raises(ValueError, match="exactly one"):
        cameroon_eval.resolve_cloud_names({4: []})


@requires_archive
def test_cohort_is_keyed_on_the_ground_truth_not_the_directory_listing():
    """62 clouds, 61 rows. ID_56 has no destructive data and must not appear."""
    cohort = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)

    ids = sorted(tree.tree_id for tree in cohort)
    assert len(cohort) == 61
    assert 56 not in ids


@requires_archive
def test_loaded_points_are_capped_normalized_and_finite():
    """Z is normalized against the full cloud, not against what survives the cap.

    _load_xyz subtracts the whole cloud's min Z before subsampling, so the
    floor it sets is exactly 0 for the cloud it read - but at max_points=2_000
    against clouds up to 3.4 million points, the single lowest point is usually
    not among the 2_000 kept. Measured on this archive: 60 of 61 trees end up
    with a strictly positive post-subsample minimum, up to 0.53 m on the worst.
    Non-negative is what normalization actually guarantees once a cap has
    thrown points away; exact zero would only hold at max_points=None.
    """
    cohort = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)

    for tree in cohort:
        assert tree.points.shape[1] == 3
        assert len(tree.points) <= 2_000
        assert float(tree.points[:, 2].min()) >= -1e-9


@requires_archive
def test_loading_is_deterministic_for_a_fixed_seed():
    first = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)
    second = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)

    for left, right in zip(first, second, strict=True):
        assert left.tree_id == right.tree_id
        assert (left.points == right.points).all()


# _load_xyz alone cannot read five of the 61 required clouds: 31, 52 and 59
# open with a non-numeric header line (an R write.table header or a
# CloudCompare comment), and 63 and 68 are comma-delimited instead of the
# archive's usual whitespace. None of this is in CAMEROON_EVIDENCE_CHAIN.md's
# "tab-separated X Y Z, no header" description - found only by attempting to
# load all 61. cameroon_eval._load_cloud repairs the text and retries through
# the same unmodified _load_xyz rather than skipping the tree, because a
# cohort that quietly drops five more trees on top of ID_56 is the exact
# failure this module exists to prevent. _write_repaired_cloud streams rather
# than materializing the whole file in memory, so these tests write into an
# io.StringIO and read that back rather than asserting on an in-memory string
# the function itself no longer builds.


def _repaired_text(raw: Path) -> str:
    """Test helper: run _write_repaired_cloud into a StringIO and read it back."""
    destination = io.StringIO()
    cameroon_eval._write_repaired_cloud(raw, destination)
    return destination.getvalue()


def test_write_repaired_cloud_drops_a_non_numeric_header_line(tmp_path):
    """31 and 52 each open with one line that is not point data."""
    raw = tmp_path / "header.txt"
    raw.write_text('"V1" "V2" "V3"\n1.0 2.0 3.0\n4.0 5.0 6.0\n', encoding="utf-8")

    assert _repaired_text(raw) == "1.0 2.0 3.0\n4.0 5.0 6.0\n"


def test_write_repaired_cloud_turns_commas_into_whitespace(tmp_path):
    """63 and 68 are comma-delimited throughout, with no header to drop."""
    raw = tmp_path / "commas.txt"
    raw.write_text("1.0,2.0,3.0\n4.0,5.0,6.0\n", encoding="utf-8")

    assert _repaired_text(raw) == "1.0 2.0 3.0\n4.0 5.0 6.0\n"


def test_write_repaired_cloud_handles_tree_59s_shape(tmp_path):
    """Tree 59 is the one irregular shape with no CI coverage otherwise.

    data/raw/ is gitignored, so every @requires_archive test - including the
    one that exercises 59 for real, below - skips on a machine without the
    1.29 GB archive. This fixture reproduces its exact shape: a // comment
    header, a fourth scalar-field column left in place (_load_xyz's own
    usecols drops it, not this function), and CRLF line endings.
    """
    raw = tmp_path / "tree_59_shape.txt"
    raw.write_bytes(
        b"//X Y Z Scalar_field\r\n"
        b"8.135 -13.849 -2.502 -1339.000000\r\n"
        b"8.244 -13.726 -2.395 -1062.000000\r\n"
    )

    assert _repaired_text(raw) == (
        "8.135 -13.849 -2.502 -1339.000000\n8.244 -13.726 -2.395 -1062.000000\n"
    )


def test_write_repaired_cloud_refuses_a_file_with_no_numeric_line_at_all(tmp_path):
    """A genuinely malformed file must still fail loudly, not return a stub."""
    raw = tmp_path / "garbage.txt"
    raw.write_text("not\nany\nof\nthis\nis\nnumeric\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no numeric point row"):
        _repaired_text(raw)


def test_repair_line_leaves_a_decimal_comma_row_untouched():
    """"1,5 2,5 3,5" intends 1.5, 2.5, 3.5 in a decimal convention this archive
    does not use. Substituting its commas would silently produce six tokens -
    1, 5, 2, 5, 3, 5 - and load three wrong points with no error. Whitespace
    already splits it into three tokens, so the substitution is refused. A
    genuinely comma-delimited row like 63 or 68's has no whitespace at all and
    yields exactly one token, so it is still repaired.
    """
    assert cameroon_eval._repair_line("1,5 2,5 3,5") == "1,5 2,5 3,5"
    assert cameroon_eval._repair_line("-6.217,-9.782,-0.832") == "-6.217 -9.782 -0.832"


def test_write_repaired_cloud_fails_loudly_on_decimal_comma_input(tmp_path):
    """The corruption the reviewer reproduced: the old, unconditional comma
    substitution loaded [1.0, 5.0, ...] from "1,5 2,5 3,5" with no error.
    Refusing the substitution on an already-whitespace-split line means "1,5"
    never parses as a point row, so this raises instead of silently loading
    wrong coordinates.
    """
    raw = tmp_path / "decimal_comma.txt"
    raw.write_text("1,5 2,5 3,5\n4,5 5,5 6,5\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no numeric point row"):
        _repaired_text(raw)


def test_write_repaired_cloud_refuses_a_short_but_fully_numeric_row(tmp_path):
    """"1 2" is two valid numbers, not a header - every real header in this
    archive is text. Dropping it silently the way a header is dropped would
    cost a real point with no word said; this must raise instead.
    """
    raw = tmp_path / "truncated.txt"
    raw.write_text("1 2\n4 5 6\n7 8 9\n", encoding="utf-8")

    with pytest.raises(ValueError, match="fewer than 3 numeric fields"):
        _repaired_text(raw)


@requires_archive
def test_the_five_irregularly_formatted_clouds_load_through_the_same_cohort_call():
    """The repair is exercised end to end, not only on synthetic fixtures, and
    cloud_was_repaired is true for exactly these five and false for the rest -
    the durable provenance marker a results table can key on.
    """
    cohort = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)

    loaded_ids = {tree.tree_id for tree in cohort}
    assert cameroon_eval.IRREGULAR_CLOUD_FORMAT_TREE_IDS <= loaded_ids
    for tree in cohort:
        expected_repaired = tree.tree_id in cameroon_eval.IRREGULAR_CLOUD_FORMAT_TREE_IDS
        assert tree.cloud_was_repaired == expected_repaired
        if expected_repaired:
            assert tree.points.shape[1] == 3
            assert len(tree.points) > 0


def test_load_cameroon_cohort_refuses_a_non_positive_max_points():
    """Validation the plan omitted: load_demol_cohort has always had it."""
    with pytest.raises(ValueError, match="positive"):
        cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=0)


def test_load_cameroon_cohort_refuses_a_negative_sample_seed():
    with pytest.raises(ValueError, match="non-negative"):
        cameroon_eval.load_cameroon_cohort(
            ARCHIVE, GROUND_TRUTH, max_points=2_000, sample_seed=-1
        )


def test_geometry_row_reports_both_targets_for_one_tree():
    """Every measured tree is scored against the tape and against the reference."""
    row = cameroon_eval.geometry_row(
        tree_id=7,
        measured_dbh_cm=40.0,
        measured_height_m=30.0,
        gt_dbh_cm=44.0,
        gt_height_m=31.0,
        reference_dbh_cm=42.0,
        reference_height_m=30.5,
    )

    assert row["dbh_error_cm"] == pytest.approx(-4.0)
    assert row["dbh_error_vs_reference_cm"] == pytest.approx(-2.0)
    assert row["height_error_m"] == pytest.approx(-1.0)
    assert row["height_error_vs_reference_m"] == pytest.approx(-0.5)


def test_size_bands_partition_the_cohort_without_gaps_or_overlap():
    edges = cameroon_eval.SIZE_BAND_EDGES_CM
    for dbh in (0.1, 10.0, 49.9, 50.0, 99.9, 100.0, 500.0):
        matched = [name for name, low, high in edges if low <= dbh < high]
        assert len(matched) == 1, f"{dbh} cm matched {matched}"


def test_small_stem_subset_is_the_unconfounded_comparison():
    """Buttressing is effectively absent below 50 cm, so that subset compares like
    with like. The archive's own reference agrees with the tape to +0.30 cm mean
    over those 31 trees, and loses 63.6 cm on the worst tree above a metre.
    """
    rows = [
        {"gt_dbh_cm": 30.0, "dbh_error_cm": 1.0},
        {"gt_dbh_cm": 120.0, "dbh_error_cm": -40.0},
    ]

    assert cameroon_eval.small_stem_dbh_mae_cm(rows) == pytest.approx(1.0)
