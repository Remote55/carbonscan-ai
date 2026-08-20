# Cameroon Tropical Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure this pipeline against 61 tropical trees that were scanned, felled
and weighed — the first check of its geometry outside temperate Belgium, and the
first check of its allometric stage against a harvested mass anywhere.

**Architecture:** Mirrors the Demol path exactly — a frozen cohort loader, a
deterministic evaluation, a committed `result.json`, and a manifest block that
`sync_truth --check` guards. Two additions Demol could not support: a mass route
scored against `Destructive AGB`, and a comparison against the cohort authors'
own published TLS measurements on the same clouds.

**Tech Stack:** Python 3.11, numpy, pytest. Existing `pipeline/demol_eval.py`,
`pipeline/qsm.py`, `pipeline/allometric.py`, `pipeline/tver.py`. No new runtime
dependencies.

---

## Source spec

`docs/superpowers/specs/2026-08-19-tropical-validation-design.md`, revised at
`5ddc1bb` after the archive was opened. Read §5–§8 and §14 before starting; they
were rewritten around what the archive actually contains and no longer say what
the first draft said.

The cohort inventory is `docs/ml/CAMEROON_EVIDENCE_CHAIN.md`. Everything below
depends on it being accurate; if you find it is not, fix it there first and say
so, because the evaluation is only as good as that description.

## Preconditions

**The cohort must be on disk** at `services/ml/data/raw/dryad_cameroon/Trees/`,
extracted, with `database.xls` and `Points_clouds/` present. It is excluded from
git by `services/ml/.gitignore:26` (`data/raw/`). Verify before starting:

```bash
services/ml/.venv/Scripts/python.exe -c "import pathlib; r=pathlib.Path('services/ml/data/raw/dryad_cameroon/Trees'); print('db', (r/'database.xls').is_file()); print('clouds', sum(1 for p in (r/'Points_clouds').iterdir() if p.is_dir()))"
```

Expected: `db True`, `clouds 62`.

**Python.** `services/ml/.venv/Scripts/python.exe` on this machine; bare `python`
in CI. Both are written where a command appears. `cd` into `services/ml` leaves
your shell there — return to `D:\Project_Carbon` before git commands.

## What the archive forces on the design

Four properties, measured rather than assumed. Each drives a decision below.

| property | consequence |
|---|---|
| `Destructive AGB` is oven-dry, stump-inclusive (`AGB / (vol × WSG)` median 1.0074) | the Chave comparison is sound and needs no moisture conversion |
| `DBH_dest` is taken "at breast height **or above buttresses if present**", with no flag | the DBH comparison is confounded on large trees; §7 of the spec says how to report it |
| `DBH_L` / `Hauteur_L` / `Edited_QSMs` are the authors' own published TLS results | there is a baseline to score against, not just a ground truth |
| 62 cloud directories, 61 database rows; `ID_56` is the orphan | the cohort keys on the database, never on the directory listing |

And one that only matters to the loader:

**Nine of 62 cloud filenames are irregular**, in five distinct ways —
`15_sans_feuille.txt` (singular), `ID63_sans_feuilles.txt` (prefixed),
`67_sans feuilles.txt` (space), `74_sans _feuille.txt` (space and singular),
`97sans_feuilles.txt` (no separator). **The loader must never construct a
filename from an ID.** It lists the directory and requires exactly one file.

Cloud sizes run 131 KB to 103 MB, median 16 MB, 1.29 GB in total — roughly 3.4
million points in the largest. The 20,000-point cap and seeded subsample that
`demol_eval._load_xyz` already applies are what make this tractable, and they
carry the same caveat as Demol: the evaluation measures a pipeline running well
below the product's point budget.

## File structure

| file | responsibility |
|---|---|
| `services/ml/data/cameroon_61/ground_truth.csv` | the 61 rows, extracted from `database.xls`, committed |
| `services/ml/data/cameroon_61/README.md` | where that CSV came from and why it is committed |
| `services/ml/scripts/extract_cameroon_ground_truth.py` | one-shot `.xls` → CSV, re-runnable and verifiable |
| `services/ml/pipeline/cameroon_eval.py` | cohort loader, evaluation, aggregation |
| `services/ml/scripts/derive_cameroon_evidence.py` | produce and `--check` the committed artefact |
| `services/ml/tests/test_cameroon_eval.py` | the loader and the metrics |
| `docs/evidence/cameroon_61/result.json` | the artefact, committed whatever it says |
| `docs/evidence/core_demo_manifest.json` | gains `validation.cameroon_61` |
| `docs/ml/CAMEROON_EVIDENCE_CHAIN.md` | gains the results section |
| `docs/ml/WHAT_CI_DOES_NOT_CHECK.md` | gains the new skips |

---

## Task 1: Commit the ground truth as a CSV

`database.xls` is a binary spreadsheet that needs `xlrd`, which is not a project
dependency and should not become one — nothing in the pipeline reads `.xls`. The
table is 61 rows and the dataset is **CC0**, so it can be committed. That makes
the ground truth reviewable in git, diffable when it changes, and readable
without the 1 GB archive.

**Files:**
- Create: `services/ml/scripts/extract_cameroon_ground_truth.py`
- Create: `services/ml/data/cameroon_61/ground_truth.csv`
- Create: `services/ml/data/cameroon_61/README.md`
- Test: `services/ml/tests/test_cameroon_eval.py`

- [ ] **Step 1: Write the failing test**

Create `services/ml/tests/test_cameroon_eval.py`:

```python
"""The Cameroon tropical cohort: loader, metrics, and the committed ground truth."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

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
```

- [ ] **Step 2: Run it and watch it fail**

```bash
services/ml/.venv/Scripts/python.exe -m pytest services/ml/tests/test_cameroon_eval.py -v --no-cov
```

Expected: every test fails, the first with `missing .../ground_truth.csv`.

- [ ] **Step 3: Write the extractor**

Create `services/ml/scripts/extract_cameroon_ground_truth.py`:

```python
"""Extract the Cameroon destructive ground truth from database.xls to CSV.

Run once, then commit the CSV. `database.xls` is a binary spreadsheet needing
`xlrd`, which is deliberately not a project dependency - nothing in the pipeline
reads `.xls`. The table is 61 rows and the dataset is CC0, so the extracted form
is committed and the archive is needed only for point clouds.

Units are converted here so no consumer has to remember them:

    Destructive AGB   Mg     -> kg
    WSG_ind           g/cm3  -> kg/m3

`--check` re-extracts and compares against the committed file, so the CSV cannot
drift from the archive unnoticed.

    python scripts/extract_cameroon_ground_truth.py --archive <Trees dir>
    python scripts/extract_cameroon_ground_truth.py --archive <Trees dir> --check
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

#: Source column -> (output column, multiplier). The multiplier carries the unit
#: conversion, so a reader of the CSV never has to know the archive's units.
COLUMN_MAP: tuple[tuple[str, str, float], ...] = (
    ("ID", "tree_id", 1.0),
    ("Genus", "genus", 1.0),
    ("Species", "species", 1.0),
    ("DBH_dest", "dbh_dest_cm", 1.0),
    ("H_tot_dest", "height_dest_m", 1.0),
    ("Destructive AGB", "agb_dest_kg", 1000.0),
    ("WSG_ind", "wsg_ind_kg_m3", 1000.0),
    ("Destructive total volume", "volume_total_dest_m3", 1.0),
    ("Destructive stem volume", "volume_stem_dest_m3", 1.0),
    ("DBH_L", "dbh_tls_cm", 1.0),
    ("Hauteur_L", "height_tls_m", 1.0),
    # The authors' hand-corrected QSM volume. Taken from the database rather
    # than by summing the 61 Edited_QSMs cylinder tables, because the archive
    # already publishes the total and re-deriving it would be our arithmetic
    # standing in for theirs.
    ("TLS edited total volume_5", "volume_total_reference_qsm_m3", 1.0),
)

SHEET = "datafinal_test2"
EXPECTED_ROWS = 61


def extract(archive_root: Path) -> str:
    """Read database.xls and return the CSV text, newline-normalized."""
    try:
        import xlrd
    except ImportError as exc:  # pragma: no cover - environment guard
        raise SystemExit(
            "xlrd is required to read database.xls. It is not a project "
            "dependency; install it into the venv for this one-shot extraction:\n"
            "    python -m pip install xlrd"
        ) from exc

    workbook = xlrd.open_workbook(archive_root / "database.xls")
    sheet = workbook.sheet_by_name(SHEET)
    header = [str(cell).strip() for cell in sheet.row_values(0)]
    missing = [source for source, _, _ in COLUMN_MAP if source not in header]
    if missing:
        raise ValueError(f"database.xls is missing expected columns: {missing}")
    index = {name: position for position, name in enumerate(header)}

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([out for _, out, _ in COLUMN_MAP])
    rows = 0
    for row_number in range(1, sheet.nrows):
        values = sheet.row_values(row_number)
        record = []
        for source, out, scale in COLUMN_MAP:
            raw = values[index[source]]
            if out == "tree_id":
                record.append(str(int(float(raw))))
            elif scale == 1.0 and isinstance(raw, str):
                record.append(raw.strip())
            else:
                record.append(f"{float(raw) * scale:.10g}")
        writer.writerow(record)
        rows += 1
    if rows != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} data rows, found {rows}")
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "cameroon_61" / "ground_truth.csv",
    )
    args = parser.parse_args()

    extracted = extract(args.archive.resolve(strict=True))
    if args.check:
        committed = args.output.read_text(encoding="utf-8")
        if committed != extracted:
            print("ground_truth.csv does not match database.xls", file=sys.stderr)
            return 1
        print('{"status": "ok", "mode": "check"}')
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(extracted, encoding="utf-8", newline="")
    print(f'{{"status": "written", "rows": {EXPECTED_ROWS}}}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Install xlrd into the venv and run the extractor**

```bash
services/ml/.venv/Scripts/python.exe -m pip install xlrd
services/ml/.venv/Scripts/python.exe services/ml/scripts/extract_cameroon_ground_truth.py --archive services/ml/data/raw/dryad_cameroon/Trees
```

Expected: `{"status": "written", "rows": 61}`.

Do **not** add `xlrd` to `services/ml/pyproject.toml`. It is a one-shot tool for
a file the pipeline never reads.

- [ ] **Step 5: Run the tests**

```bash
services/ml/.venv/Scripts/python.exe -m pytest services/ml/tests/test_cameroon_eval.py -v --no-cov
```

Expected: all five pass. If `test_agb_is_oven_dry_mass_including_the_stump` fails,
stop — either the wrong AGB column was mapped or the archive is not what
`CAMEROON_EVIDENCE_CHAIN.md` describes, and both invalidate the evaluation.

- [ ] **Step 6: Write the data README**

Create `services/ml/data/cameroon_61/README.md`:

```markdown
# Cameroon destructive ground truth, 61 trees

Extracted from `database.xls` sheet `datafinal_test2` in the Dryad archive by
`scripts/extract_cameroon_ground_truth.py`. Re-verify with `--check`.

**Source:** Momo Takoudjou, S. et al. (2018), Dryad,
<https://doi.org/10.5061/dryad.10hq7> — **CC0 1.0**, which is why this table can
be committed. The point clouds are not: they are 1.29 GB and stay under
`data/raw/`, excluded by `.gitignore`.

`docs/ml/CAMEROON_EVIDENCE_CHAIN.md` records what the archive contains and how
these columns were established, including the arithmetic showing `agb_dest_kg`
is oven-dry mass including the stump.

## Columns

| column | source column | unit | note |
|---|---|---|---|
| `tree_id` | `ID` | — | 61 of the archive's 62 clouds; `ID_56` has no destructive row |
| `genus`, `species` | `Genus`, `Species` | — | 15 species |
| `dbh_dest_cm` | `DBH_dest` | cm | **at 1.30 m, or above buttresses if present** — the archive does not say which trees |
| `height_dest_m` | `H_tot_dest` | m | felled height |
| `agb_dest_kg` | `Destructive AGB` | kg | archive gives Mg; oven-dry, stump-inclusive |
| `wsg_ind_kg_m3` | `WSG_ind` | kg/m³ | archive gives g/cm³ |
| `volume_total_dest_m3` | `Destructive total volume` | m³ | includes the stump |
| `volume_stem_dest_m3` | `Destructive stem volume` | m³ | stem only |
| `dbh_tls_cm` | `DBH_L` | cm | the authors' own TLS-derived diameter |
| `height_tls_m` | `Hauteur_L` | m | the authors' own TLS-derived height |
| `volume_total_reference_qsm_m3` | `TLS edited total volume_5` | m³ | the authors' hand-corrected QSM, branches under 5 cm excluded |

The last three are not ground truth. They are a published reference
implementation on the same point clouds, and exist here so this pipeline can be
scored against a competent method rather than only against the tape.

`volume_total_reference_qsm_m3` comes from the `_5` family of columns, which
exclude branches thinner than 5 cm. It is therefore **not** directly comparable
to `volume_total_dest_m3`; it is comparable to what a QSM can see. Any figure
derived from it has to say so.
```

- [ ] **Step 7: Commit**

```bash
git add services/ml/scripts/extract_cameroon_ground_truth.py services/ml/data/cameroon_61 services/ml/tests/test_cameroon_eval.py
git commit -F - <<'MSG'
feat(ml): the Cameroon ground truth is 61 rows locked in a 1 GB binary

database.xls needs xlrd to read, and xlrd is deliberately not a project
dependency because nothing in the pipeline reads .xls. So the table sat inside a
1.29 GB archive that cannot be committed, which would have made the ground truth
of every tropical figure this project publishes unreviewable in git.

The dataset is CC0. The table is 61 rows. It is committed, with the units
converted once at extraction - Mg to kg, g/cm3 to kg/m3 - so no consumer has to
remember the archive's conventions.

extract_cameroon_ground_truth.py --check re-extracts and compares, so the CSV
cannot drift from the archive unnoticed.

The suite asserts the property the entire evaluation rests on: AGB divided by
volume times wood specific gravity has median 1.0074, which says the biomass is
oven-dry and stump-inclusive - the quantity Chave predicts. A re-extraction that
silently picked a different AGB column would pass every other test and fail that
one.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 2: The cohort loader

Mirrors `load_demol_cohort`, with the differences the archive forces: clouds
live one-per-directory under irregular filenames, and the cohort is keyed on the
CSV so `ID_56` is excluded by construction.

**Files:**
- Create: `services/ml/pipeline/cameroon_eval.py`
- Test: `services/ml/tests/test_cameroon_eval.py`

- [ ] **Step 1: Write the failing tests**

Append to `services/ml/tests/test_cameroon_eval.py`:

```python
from pipeline import cameroon_eval

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
    cohort = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)

    for tree in cohort:
        assert tree.points.shape[1] == 3
        assert len(tree.points) <= 2_000
        assert float(tree.points[:, 2].min()) == pytest.approx(0.0, abs=1e-9)


@requires_archive
def test_loading_is_deterministic_for_a_fixed_seed():
    first = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)
    second = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)

    for left, right in zip(first, second, strict=True):
        assert left.tree_id == right.tree_id
        assert (left.points == right.points).all()
```

- [ ] **Step 2: Run and watch them fail**

```bash
cd services/ml && .venv/Scripts/python.exe -m pytest tests/test_cameroon_eval.py -v --no-cov; cd ../..
```

Expected: the three unit tests fail with `AttributeError: ... resolve_cloud_names`;
the four archive tests fail the same way (they do not skip — the archive is
present on this machine).

- [ ] **Step 3: Implement the loader**

Create `services/ml/pipeline/cameroon_eval.py`:

```python
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
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pipeline.demol_eval import _load_xyz

#: The tree with a point cloud and no destructive row. Excluded by keying the
#: cohort on the ground truth, and named here so the exclusion is legible.
CLOUD_WITHOUT_GROUND_TRUTH = 56

#: The archive's own count, frozen so a partial extraction cannot pass quietly.
COHORT_SIZE = 61


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
        points = _load_xyz(
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
```

- [ ] **Step 4: Run the tests**

```bash
cd services/ml && .venv/Scripts/python.exe -m pytest tests/test_cameroon_eval.py -v --no-cov; cd ../..
```

Expected: all pass. The archive tests take a minute — they read 61 clouds
totalling 1.29 GB even at a 2,000-point cap.

- [ ] **Step 5: Commit**

```bash
git add services/ml/pipeline/cameroon_eval.py services/ml/tests/test_cameroon_eval.py
git commit -F - <<'MSG'
feat(ml): nine of the archive's filenames would have dropped nine trees

The Cameroon clouds are named five different ways - 15_sans_feuille.txt is
singular, ID63_sans_feuilles.txt is prefixed, 67_sans feuilles.txt has a space,
74_sans _feuille.txt has both, 97sans_feuilles.txt has no separator. A loader
that builds a filename from a tree ID finds 53 of 62 and reports a cohort, which
is the silent-shrink failure this project keeps finding in its own code.
resolve_cloud_names reads the directory instead, and refuses a directory holding
anything other than one file rather than skipping it.

The cohort keys on the committed ground truth, not the clouds: the archive has
62 cloud directories and 61 destructive rows, and keying the other way would
produce a 62-tree cohort containing one tree that cannot be scored.
CLOUD_WITHOUT_GROUND_TRUTH names it so the exclusion is legible rather than
arithmetic nobody can follow.

CameroonTree carries reference_dbh_cm and reference_height_m alongside the
destructive values. They are not ground truth - they are the cohort authors'
published TLS results on these exact clouds, and they are in the dataclass
because the tape is not an unambiguous target here: DBH_dest is taken "at breast
height or above buttresses if present" with no per-tree flag, while compute_qsm
always fits at 1.30 m.

Points go through demol_eval._load_xyz unchanged, so both cohorts are min-Z
normalized and subsampled identically and their figures can sit in one table.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 3: Route A — geometry, and the reference comparison

**Files:**
- Modify: `services/ml/pipeline/cameroon_eval.py`
- Test: `services/ml/tests/test_cameroon_eval.py`

- [ ] **Step 1: Write the failing tests**

Append to `services/ml/tests/test_cameroon_eval.py`:

```python
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
```

- [ ] **Step 2: Run and watch them fail**

Expected: `AttributeError` for `geometry_row`, `SIZE_BAND_EDGES_CM`,
`small_stem_dbh_mae_cm`.

- [ ] **Step 3: Implement**

Append to `services/ml/pipeline/cameroon_eval.py`:

```python
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
```

- [ ] **Step 4: Run the tests, then commit**

```bash
cd services/ml && .venv/Scripts/python.exe -m pytest tests/test_cameroon_eval.py -v --no-cov; cd ../..
git add services/ml/pipeline/cameroon_eval.py services/ml/tests/test_cameroon_eval.py
git commit -F - <<'MSG'
feat(ml): a DBH error on a buttressed tree is not a DBH error

database.xls defines DBH_dest as taken "at breast height or above buttresses if
present" and records no per-tree flag. compute_qsm always fits at 1.30 m. On a
buttressed stem the two describe different cross-sections of a tapering trunk,
so scoring one against the other and calling the difference measurement error is
wrong, and averaging it over the cohort hides which trees it came from.

Three responses, none of which pretend the confound away. Every tree is scored
against the reference TLS as well as the tape, because the reference faces the
identical confound on identical clouds and therefore says whether a large error
belongs to this pipeline or to the problem. The bands are reported so a reader
sees where the error lives. And small_stem_dbh_mae_cm restricts to stems under
50 cm, where the archive's own reference agrees with the tape to +0.30 cm across
31 trees - the only subset comparing like with like, and the figure this
pipeline should be judged on.

The all-trees DBH MAE is still reported. It is an upper bound on measurement
error rather than a measurement of it, and it matters to a user whatever its
cause.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 4: Routes A and B against harvested mass

The first check of the allometric stage against a weighed tree, anywhere in this
project.

**Files:**
- Modify: `services/ml/pipeline/cameroon_eval.py`
- Test: `services/ml/tests/test_cameroon_eval.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_mass_row_separates_measurement_error_from_equation_error():
    """Route A costs what the pipeline measured; route B costs the tape.

    A minus B is the measurement's contribution; B against the harvested mass is
    the equation's own error. Without the split a bad end-to-end number cannot be
    attributed, and the next sprint is a guess.
    """
    row = cameroon_eval.mass_row(
        tree_id=7,
        gt_agb_kg=1000.0,
        route_a_agb_kg=800.0,
        route_b_agb_kg=900.0,
    )

    assert row["route_a_ape_pct"] == pytest.approx(20.0)
    assert row["route_b_ape_pct"] == pytest.approx(10.0)
    assert row["measurement_share_pct"] == pytest.approx(10.0)


def test_mass_row_refuses_a_non_positive_harvested_mass():
    with pytest.raises(ValueError, match="positive"):
        cameroon_eval.mass_row(tree_id=1, gt_agb_kg=0.0, route_a_agb_kg=1.0, route_b_agb_kg=1.0)


@requires_archive
def test_chave_on_the_tape_lands_within_an_order_of_the_harvested_mass():
    """A smoke test, not an accuracy claim.

    Chave 2014 fitted on pantropical destructive data should not be wrong by more
    than a factor of a few on trees inside its domain. If it is, the wiring is
    broken - wrong units, wrong density, wrong column - and no later figure from
    this module means anything.
    """
    cohort = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)

    ratios = []
    for tree in cohort:
        predicted = cameroon_eval.chave_agb_kg(
            dbh_cm=tree.gt_dbh_cm, height_m=tree.gt_height_m, wood_density_kg_m3=tree.wsg_kg_m3
        )
        ratios.append(predicted / tree.gt_agb_kg)

    median = sorted(ratios)[len(ratios) // 2]
    assert 0.5 < median < 2.0, f"Chave median ratio {median} - check units and wiring"
```

- [ ] **Step 2: Run and watch them fail**

- [ ] **Step 3: Implement**

Append to `services/ml/pipeline/cameroon_eval.py`:

```python
from pipeline import allometric, tver

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
```

- [ ] **Step 4: Add the T-VER comparison test**

Append to `services/ml/tests/test_cameroon_eval.py`:

```python
@requires_archive
def test_two_unvalidated_models_are_scored_against_the_same_weighed_trees():
    """docs/ml/TVER_EQUATIONS.md currently ends "agreement between two
    unvalidated models, not validation". This is what changes that sentence.

    Both models are costed from the tape and the felled height - route B - so
    the comparison isolates the equations from the measurement entirely.
    """
    cohort = cameroon_eval.load_cameroon_cohort(ARCHIVE, GROUND_TRUTH, max_points=2_000)

    chave, tver_pred = [], []
    for tree in cohort:
        chave.append(
            cameroon_eval.chave_agb_kg(
                dbh_cm=tree.gt_dbh_cm,
                height_m=tree.gt_height_m,
                wood_density_kg_m3=tree.wsg_kg_m3,
            )
            / tree.gt_agb_kg
        )
        tver_pred.append(
            cameroon_eval.tver_agb_kg(dbh_cm=tree.gt_dbh_cm, height_m=tree.gt_height_m)
            / tree.gt_agb_kg
        )

    # No assertion on which wins - that is the finding, not a requirement.
    # Both must merely be finite and positive, so a broken wiring cannot pass.
    assert all(ratio > 0 for ratio in chave)
    assert all(ratio > 0 for ratio in tver_pred)
    assert len(chave) == len(tver_pred) == 61
```

**Which model is closer is the result, not an acceptance criterion.** Do not add
an assertion that Chave beats T-VER or the reverse. If one of them is badly
wrong on tropical African trees, that is a finding worth publishing, and a test
asserting otherwise would be exactly the pressure this project exists to resist.

- [ ] **Step 5: Run the tests, then commit**

```bash
git add services/ml/pipeline/cameroon_eval.py services/ml/tests/test_cameroon_eval.py
git commit -F - <<'MSG'
feat(ml): the allometric stage has never been checked against a weighed tree

core_demo_manifest.json says so in the Demol block's own words: that evaluation
"does not validate ... allometric biomass, carbon stock, CO2e". Demol has
harvested volumes and no masses, so there was nothing to check against. This
cohort has 61 harvested masses.

Two routes over the same trees and the same model. Route A costs each tree from
what the pipeline measured; route B costs it from the tape and the felled
height. Route B against the scale is the equation's own error with measurement
removed - the first honest answer to how wrong Chave is on a tropical tree.
A minus B is what the measurement contributed. Without the split a bad
end-to-end number cannot be attributed to a cause and the next sprint is a
guess.

chave_agb_kg stops at biomass rather than going through calculate_carbon,
because this compares a model against a scale and the carbon fraction and 44/12
ratio have no place between the two.

The smoke test asserts only that Chave lands within a factor of two of the
harvested median. That is not an accuracy claim - it is the check that the
wiring is right, since a units error in the ground-truth extraction or a density
in the wrong scale would make every later figure meaningless while still
producing numbers.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 5: Run it, derive the artefact, publish whatever it says

**Files:**
- Create: `services/ml/scripts/derive_cameroon_evidence.py`
- Create: `docs/evidence/cameroon_61/result.json`
- Modify: `docs/evidence/core_demo_manifest.json`, `docs/ml/CAMEROON_EVIDENCE_CHAIN.md`, `docs/ml/WHAT_CI_DOES_NOT_CHECK.md`

- [ ] **Step 1: Write the derivation script**

Mirror `services/ml/scripts/derive_demol_evidence.py`. Read it first and follow
its structure — argument names, `--check` behaviour, and the `schema_version` /
`dataset` / `derivation` / `gate` / `metrics` / `per_tree` / `protocol` shape of
`docs/evidence/demol_65/result.json`. Do not invent a new document shape.

`protocol` must record, because §6 and §13 of the spec require it:
- `qsm.TOTAL_TREE_FORM_FACTOR` and the commit it was calibrated at (Belgium's)
- `max_points`, `sample_seed`
- the T-VER forest type scored (`mixed_deciduous`) and why
- the ground-truth CSV's SHA-256
- `cohort_size: 61`, `clouds_available: 62`, `excluded_cloud: 56`

- [ ] **Step 2: Run the full evaluation**

```bash
cd services/ml && .venv/Scripts/python.exe scripts/derive_cameroon_evidence.py --archive data/raw/dryad_cameroon/Trees --output ../../docs/evidence/cameroon_61/result.json; cd ../..
```

This reads 1.29 GB across 61 clouds and runs `compute_qsm` on each. Expect
minutes, not seconds.

- [ ] **Step 3: Read the result before doing anything else**

Look at, in this order:

1. `small_stem_dbh_mae_cm` — the like-for-like diameter figure.
2. `dbh_error_vs_reference_cm` by band — are we near the published method, or far
   off it?
3. `route_b_ape_pct` — how wrong is Chave on a tropical tree, measurement removed.
4. `measurement_share_pct` — does the error live in stage 6 or stage 8?
5. The excluded count and reasons.

**Whatever these say, they get committed.** `pointnet_independent_eval/result.json`
is committed carrying `FAIL_METRICS`; this follows that precedent. Do not tune
anything to improve a number. §6 forbids recalibrating on this cohort, and that
prohibition is the point of the task, not an obstacle to it.

- [ ] **Step 4: Wire into the manifest and regenerate**

Add `validation.cameroon_61` to `docs/evidence/core_demo_manifest.json` following
the shape of the `demol_65` block, including `result_path`, `result_sha256`,
`scope` and `excludes`. The `excludes` string must name what this still does not
validate — stages 1–4, stage 5 (the clouds arrive leaf-stripped), stage 7, and
Thailand.

```bash
services/ml/.venv/Scripts/python.exe scripts/sync_truth.py --write
services/ml/.venv/Scripts/python.exe scripts/sync_truth.py --check
```

- [ ] **Step 5: Write the results into the evidence chain**

Add a results section to `docs/ml/CAMEROON_EVIDENCE_CHAIN.md` in the shape
`DEMOL_EVIDENCE_CHAIN.md` uses: what was expected, what was measured, and where
they differ. Score the predictions in §14 of the spec explicitly — including the
ones that turn out wrong, which are the ones worth reading.

- [ ] **Step 6: Record the new skips**

Add the archive-dependent tests to `docs/ml/WHAT_CI_DOES_NOT_CHECK.md`, in its
existing table, with the reason `-rs` will print.

- [ ] **Step 7: Commit**

Write the message yourself, in this repo's voice: lead with what the numbers
say, including the unflattering parts, and state plainly which predictions from
the spec were wrong. End with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

---

## Task 6: Can the pipeline tell a buttressed stem on its own?

Spec §8. This task exists because the archive has **no per-tree buttress flag**,
so a geometric signal computed from the cloud is the only thing that could
partition the cohort at evaluation time — or warn a real user, who has no tape
and no database.

It comes after Task 5 deliberately: the threshold is chosen from the measured
distribution, and choosing it before seeing the data would be a guess dressed as
a design decision.

**Files:**
- Modify: `services/ml/pipeline/cameroon_eval.py`
- Test: `services/ml/tests/test_cameroon_eval.py`
- Modify: `docs/ml/CAMEROON_EVIDENCE_CHAIN.md`

- [ ] **Step 1: Measure whether the signal exists at all**

`TreeResult` already carries `ransac_inlier_ratio` — the fraction of the
breast-height slice the fitted circle explains. Using the per-tree rows from
Task 5's run, print the inlier ratio against `abs(dbh_error_cm)` and against
`gt_dbh_cm`, and compute the rank correlation of each pair.

- [ ] **Step 2: Decide from what you measured, and write the decision down**

Two outcomes, and both are results:

**If the inlier ratio separates the divergent trees** — low ratio where our DBH
and `DBH_dest` disagree most — pick a threshold from that distribution, add
`DBH_FIT_BUTTRESS_SUSPECT` to the pipeline's `reason_code` set, and report how
many trees it flags and how many of those are the large ones.

**If it does not separate them**, that is a negative result and it goes in
`CAMEROON_EVIDENCE_CHAIN.md` in those words. Do **not** add a reason code that
does not detect anything, and do not search for a different statistic until one
correlates — that is fitting a threshold to a cohort of 61 trees, and §6 forbids
the same move for the taper constants for the same reason.

Either way `DBH_ABOVE_CALIBRATED_RANGE` is added: it needs no correlation, only
the range the Belgian taper constants were fitted over, which is known.

- [ ] **Step 3: Write a test for whichever outcome you got**

If the code was added, test that it fires on a low-inlier large stem and stays
silent on a clean small one — with the threshold as a named module constant, not
a literal in the test.

If it was not added, test nothing new, and make sure the evidence chain says why.

- [ ] **Step 4: Commit**

Write the message yourself. If the signal did not work, say that in the subject
line — a negative result reported plainly is worth more here than a detector
nobody can trust.

---

## Task 7: Verify the branch

- [ ] **Step 1: Full suites**

```bash
cd services/ml && .venv/Scripts/python.exe -m pytest tests/ -q -rs --no-cov; cd ../..
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/ -q --no-cov
```

Expected: `services/ml` passes. The skip count rises by the number of
archive-dependent tests **only on a machine without the cohort**; on this machine
they run. Record both numbers.

- [ ] **Step 2: Lint**

```bash
cd services/ml && .venv/Scripts/python.exe -m ruff check pipeline/ training/ scripts/ tests/ ../../scripts/*.py ../../scripts/tests/; cd ../..
```

- [ ] **Step 3: Gates**

```bash
services/ml/.venv/Scripts/python.exe scripts/sync_truth.py --check
services/ml/.venv/Scripts/python.exe scripts/judge_demo_manifest.py check
services/ml/.venv/Scripts/python.exe services/ml/scripts/extract_cameroon_ground_truth.py --archive services/ml/data/raw/dryad_cameroon/Trees --check
```

- [ ] **Step 4: Confirm no cohort file is staged**

```bash
git status --porcelain
```

Nothing under `services/ml/data/raw/` may appear. If it does, the ignore rule
failed and that is a blocker — the archive is 1.29 GB.

---

## What this plan does not do

- **No recalibration.** §6 of the spec forbids fitting the taper constants on
  this cohort and reporting the improvement. If the geometry is poor, that is
  the result.
- **No wood/leaf evaluation.** The clouds arrive leaf-stripped, so stage 5
  cannot be scored here. That is P2.
- **No stages 1–4.** Isolated trees again, as with Demol. No real plot has been
  validated end to end.
- **No default change.** Whether T-VER should replace Chave is a separate
  decision with its own evidence, whatever this measures.
- **No claim about Thailand.** Cameroon is tropical, semi-deciduous, and not
  Thai. T-VER is being scored on African trees because that is the closest check
  available without field access, and the result must say so wherever it is
  quoted.
