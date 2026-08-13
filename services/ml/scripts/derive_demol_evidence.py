"""Derive the Demol accuracy figures that this project publishes.

`docs/evidence/core_demo_manifest.json` carries a `validation.demol_65` block of
eighteen numbers. Those numbers reach the proposal, the README and the web
dashboard through `scripts/build_truth_aligned_report.py` and
`scripts/sync_truth.py`. Until this script existed, nothing in the repository
produced them.

That was not a filing oversight. The published numbers were never the
evaluator's:

- Every linear statistic in the block is an exact multiple of 1/65 of a
  two-decimal sum -- `dbh_mae_cm x 65 = 75.88`, `height_mae_m x 65 = 35.40`,
  `dbh_bias_cm x 65 = -33.58` -- and the volume figures are the same at four
  decimals. They were averaged from a table that had already been rounded for
  display.
- `docs/evidence/pointnet_independent_eval/result.json`, which does carry
  provenance, records the same cohort and the same tlsep baseline at
  `dbh_mae_cm = 1.1339` and `volume_mape_pct = 18.93`. The manifest said 1.1674
  and 18.77. The two disagreed for as long as both existed.
- `sync_truth.py` guarded the block by comparing it to a literal written in its
  own source. Two copies of an underived number checking each other.

So this script exists to make the block derivable, and `--check` exists to keep
it that way. Both run the protocol frozen in `training/evidence_protocol.py`:
the same 65 tree ids, the same 20,000-point cap, the same sampling and QSM
seeds the independent evaluation used.

    python scripts/derive_demol_evidence.py            # write the artefact
    python scripts/derive_demol_evidence.py --check    # fail if it has drifted

`--check` re-runs the whole evaluation, so it is also the determinism test: a
protocol that did not reproduce would fail here rather than quietly publish a
different number next time.

Needs the cohort in `data/raw/zenodo_belgium/` (691 MB, not in git), so it
cannot run on CI -- see `docs/ml/WHAT_CI_DOES_NOT_CHECK.md`. Takes about four
minutes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

ML_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ML_ROOT.parent.parent
COHORT = ML_ROOT / "data" / "raw" / "zenodo_belgium"
ARTEFACT = REPO_ROOT / "docs" / "evidence" / "demol_65" / "result.json"

#: Decimal places for every published aggregate. Six is already finer than the
#: cohort's own measurements -- DBH was taped to the centimetre -- and it keeps
#: the figures readable where they land, in the proposal and on the dashboard.
PUBLISHED_DECIMALS = 6

#: Field-by-field, the block the manifest publishes. Producing exactly this set
#: is the point: a derivation that emitted a different shape would leave some
#: published number still underived.
MANIFEST_FIELDS = (
    "dbh_mae_cm",
    "dbh_rmse_cm",
    "dbh_bias_cm",
    "dbh_mape_pct",
    "dbh_within_10_pct",
    "dbh_worst_pct",
    "dbh_worst_abs_cm",
    "height_mae_m",
    "height_rmse_m",
    "height_bias_m",
    "height_mape_pct",
    "height_within_10_pct",
    "volume_mae_m3",
    "volume_mape_pct",
    "volume_bias_m3",
    "volume_within_10_pct",
    "volume_worst_pct",
)


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    )
    return proc.stdout.strip()


def _statistics(rows: list[dict[str, float]], *, key: str, unit: str) -> dict[str, Any]:
    """Mean, spread, bias and worst case for one measured quantity.

    Errors are computed from the full-precision predictions. Rounding happens
    once, in the JSON encoder, never before an average -- which is the specific
    mistake that produced the numbers this file replaces.
    """
    truth = np.array([row[f"gt_{key}_{unit}"] for row in rows], dtype=float)
    predicted = np.array([row[f"pred_{key}_{unit}"] for row in rows], dtype=float)
    error = predicted - truth
    absolute = np.abs(error)
    relative = absolute / truth * 100.0

    return {
        f"{key}_mae_{unit}": float(np.mean(absolute)),
        f"{key}_rmse_{unit}": float(math.sqrt(float(np.mean(error**2)))),
        f"{key}_bias_{unit}": float(np.mean(error)),
        f"{key}_mape_pct": float(np.mean(relative)),
        f"{key}_within_10_pct": f"{int(np.sum(relative <= 10.0))}/{len(rows)}",
        f"{key}_worst_pct": float(np.max(relative)),
        f"{key}_worst_abs_{unit}": float(np.max(absolute)),
    }


def derive() -> dict[str, Any]:
    """Run the frozen protocol and return the artefact, unwritten."""
    from pipeline import wood_leaf_separation
    from pipeline.demol_eval import evaluate_demol_pair, load_demol_cohort
    from pipeline.qsm import MIN_DBH_FIT_QUALITY
    from training.evidence_protocol import EXPECTED_SECTIONS

    protocol = EXPECTED_SECTIONS["demol"]
    tree_ids = list(protocol["tree_ids"])

    def tlsep(points: np.ndarray) -> Any:
        return wood_leaf_separation.WoodLeafSegmenter(backend="tlsep").segment(points)

    cohort = load_demol_cohort(
        COHORT,
        max_points=protocol["max_points"],
        sample_seed=protocol["sampling_seed"],
        expected_tree_ids=tree_ids,
    )
    # The published block describes tlsep alone. `evaluate_demol_pair` is the
    # only entry point that runs the cohort through the QSM path the protocol
    # fixes, and it is paired, so tlsep goes in on both sides and the candidate
    # half is discarded.
    evaluation = evaluate_demol_pair(
        cohort,
        baseline_predictor=tlsep,
        candidate_predictor=tlsep,
        qsm_seed=protocol["qsm_seed"],
    )

    rows = [
        {
            "tree_id": row["tree_id"],
            "gt_dbh_cm": row["gt_dbh_cm"],
            "gt_height_m": row["gt_height_m"],
            "gt_volume_m3": row["gt_volume_m3"],
            "pred_dbh_cm": row["baseline_dbh_cm"],
            "pred_height_m": row["baseline_height_m"],
            "pred_volume_m3": row["baseline_volume_m3"],
        }
        for row in evaluation["per_tree"]
        if row["baseline_status"] == "measurable"
    ]
    if not rows:
        raise SystemExit("no tree in the cohort was measurable -- nothing to publish")

    metrics: dict[str, Any] = {"trees": len(rows)}
    metrics.update(_statistics(rows, key="dbh", unit="cm"))
    metrics.update(_statistics(rows, key="height", unit="m"))
    metrics.update(_statistics(rows, key="volume", unit="m3"))
    # Rounded once, here, after every average is taken, because these values are
    # interpolated straight into the proposal and the dashboard and a DBH error
    # quoted to 10^-16 cm claims a precision no tape measure has. This is the
    # exact inverse of the bug that produced the figures this replaces, which
    # rounded per tree and then averaged. `per_tree` below keeps full precision,
    # so the rounding is checkable rather than merely asserted.
    metrics = {
        key: round(value, PUBLISHED_DECIMALS) if isinstance(value, float) else value
        for key, value in metrics.items()
    }

    missing = [field for field in MANIFEST_FIELDS if field not in metrics]
    if missing:
        raise SystemExit(f"derivation does not produce published fields: {missing}")

    return {
        "schema_version": "1",
        "dataset": "Demol et al. 2021 isolated-tree TLS validation",
        "protocol": {
            "record_id": protocol["record_id"],
            "expected_trees": protocol["expected_trees"],
            "max_points": protocol["max_points"],
            "sampling_seed": protocol["sampling_seed"],
            "qsm_seed": protocol["qsm_seed"],
            "qsm_algorithm": protocol["qsm_algorithm"],
            "tree_ids_sha256": hashlib.sha256(
                "\n".join(tree_ids).encode("utf-8")
            ).hexdigest(),
        },
        # Recorded so a future disagreement can be attributed instead of
        # guessed at. Note that compute_qsm, which is what this path calls, does
        # not read it -- the gate is applied by single_tree.py and main.py. It
        # is here because it is the constant everyone reaches for first when the
        # DBH figures move, and knowing it did not change is worth the line.
        "gate": {"min_dbh_fit_quality": MIN_DBH_FIT_QUALITY},
        "derivation": {
            "commit": _git("rev-parse", "HEAD"),
            "dirty": bool(_git("status", "--porcelain", "--untracked-files=normal")),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "metrics": metrics,
        "per_tree": sorted(rows, key=lambda row: row["tree_id"]),
    }


def _serialise(artefact: dict[str, Any]) -> str:
    return json.dumps(artefact, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _comparable(artefact: dict[str, Any]) -> dict[str, Any]:
    """Everything a re-run must reproduce.

    `derivation` is dropped: commit and dirty flag record when the artefact was
    made, and they legitimately differ on a later run. The measurement and the
    protocol that produced it must not.
    """
    return {key: value for key, value in artefact.items() if key != "derivation"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-derive and fail if the recorded artefact no longer matches",
    )
    args = parser.parse_args(argv)

    if not (COHORT / "Destructive_and_qsm_data_DEMOL.csv").is_file():
        print(f"Demol cohort not found under {COHORT}", file=sys.stderr)
        print("691 MB, not in git -- see docs/ml/DATASETS.md", file=sys.stderr)
        return 2

    artefact = derive()

    if not args.check:
        ARTEFACT.parent.mkdir(parents=True, exist_ok=True)
        # newline="" so the bytes on disk are the bytes hashed. The default
        # translates \n to \r\n on Windows, which leaves the printed digest
        # describing a file that does not exist -- and this digest is what the
        # manifest pins.
        payload = _serialise(artefact).encode("utf-8")
        with ARTEFACT.open("wb") as handle:
            handle.write(payload)
        digest = hashlib.sha256(payload).hexdigest()
        print(f"wrote {ARTEFACT.relative_to(REPO_ROOT)}")
        print(f"sha256 {digest}")
        for field in ("dbh_mae_cm", "height_mae_m", "volume_mape_pct"):
            print(f"  {field}: {artefact['metrics'][field]}")
        return 0

    if not ARTEFACT.is_file():
        print(f"{ARTEFACT.relative_to(REPO_ROOT)} does not exist -- run without", file=sys.stderr)
        print("--check to derive it", file=sys.stderr)
        return 1

    recorded = json.loads(ARTEFACT.read_text(encoding="utf-8"))
    if _comparable(recorded) == _comparable(artefact):
        print(f"{ARTEFACT.relative_to(REPO_ROOT)} reproduces")
        return 0

    print(f"{ARTEFACT.relative_to(REPO_ROOT)} no longer reproduces:", file=sys.stderr)
    for field in MANIFEST_FIELDS:
        was = recorded.get("metrics", {}).get(field)
        now = artefact["metrics"][field]
        if was != now:
            print(f"  {field}: recorded {was}, derived {now}", file=sys.stderr)
    print("Re-run without --check, then update the manifest from it.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
