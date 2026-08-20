"""The Cameroon tropical cohort: loader, metrics, and the committed ground truth."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest  # noqa: F401 — used by pytest.raises/approx/mark in tests appended by later tasks

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


def test_ground_truth_ids_match_the_archive_exactly():
    """56 is absent: it has a point cloud and no destructive row."""
    ids = sorted(int(row["tree_id"]) for row in _rows())

    assert 56 not in ids
    assert ids[0] == 1
    assert ids[-1] == 106
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
