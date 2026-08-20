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
