"""Derive the Cameroon tropical accuracy figures this project publishes.

The counterpart to derive_demol_evidence.py, over 61 destructively harvested
tropical trees instead of 65 temperate ones. Same discipline: nothing here is
hand-typed, --check re-derives the whole evaluation and fails on drift, and
the constants scored against this cohort were calibrated on a different one
and stay frozen -- see pipeline/cameroon_eval.py's module docstring and the
spec at docs/superpowers/specs/2026-08-19-tropical-validation-design.md,
section 6.

Two things this script measures that Demol cannot, because the Cameroon
cohort carries a harvested mass and a published reference TLS measurement:

    Route A: point cloud -> compute_qsm -> DBH/height -> Chave/T-VER -> AGB.
    Route B: tape DBH + felled height (no point cloud) -> Chave/T-VER -> AGB.

Route A costs a tree the way a user of the product would; route B costs the
same tree with the measurement removed, so route A minus route B isolates
what the point-cloud measurement contributed versus what the allometric
equation got wrong on its own. Both routes are scored against the same
harvested AGB, for both Chave 2014 and T-VER's mixed_deciduous row.

    python scripts/derive_cameroon_evidence.py --archive data/raw/dryad_cameroon/Trees --output ../../docs/evidence/cameroon_61/result.json
    python scripts/derive_cameroon_evidence.py --check

Needs the archive in data/raw/dryad_cameroon/ (1.29 GB, not in git) -- see
docs/ml/WHAT_CI_DOES_NOT_CHECK.md. Reads 61 clouds and runs compute_qsm on
each; expect minutes, not seconds.

Whatever this produces gets committed. docs/evidence/pointnet_independent_eval/
result.json is already committed carrying FAIL_METRICS; this follows that
precedent. Nothing here recalibrates qsm.py's taper constants on this cohort --
that is the exact defect this project already punished PointNet++ for, and the
spec's section 6 forbids it a second time, for the same reason.
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
ARCHIVE = ML_ROOT / "data" / "raw" / "dryad_cameroon" / "Trees"
GROUND_TRUTH_CSV = ML_ROOT / "data" / "cameroon_61" / "ground_truth.csv"
ARTEFACT = REPO_ROOT / "docs" / "evidence" / "cameroon_61" / "result.json"

#: Decimal places for every published aggregate. Matches derive_demol_evidence.py:
#: finer than the cohort's own measurements (DBH taped to the millimetre at
#: best) and readable wherever these figures land.
PUBLISHED_DECIMALS = 6

#: max_points and sample_seed match the Demol protocol exactly, so the two
#: cohorts are read at the same point budget and their figures sit in one
#: table. See pipeline/cameroon_eval.py's module docstring. Chosen once, here,
#: before the run -- not tuned afterward to make a figure look better.
MAX_POINTS = 20_000
SAMPLE_SEED = 0
QSM_SEED = 0

#: The commit that fitted qsm.TOTAL_TREE_FORM_FACTOR and qsm.STEM_FORM_FACTOR
#: on the 65 Belgian Demol trees. Recorded so a later reader can check that
#: the spec's section 6 rule held: this evaluation runs with those constants
#: unchanged, never refit on the Cameroon cohort.
TAPER_CALIBRATION_COMMIT = "baa1128"


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    )
    return proc.stdout.strip()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_positive(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


def _error_stats(errors: np.ndarray, truth: np.ndarray, *, prefix: str, unit: str) -> dict[str, Any]:
    """MAE/RMSE/bias/MAPE/within-10/worst for one (errors, truth) pair.

    Same shape as derive_demol_evidence.py's _statistics, generalised to take
    raw arrays instead of gt_/pred_ keyed rows, so it can be reused for the
    tape comparison, the reference-TLS comparison and the reference-QSM
    volume comparison without three near-duplicate copies.
    """
    absolute = np.abs(errors)
    relative = absolute / truth * 100.0
    n = len(errors)
    return {
        f"{prefix}_mae_{unit}": float(np.mean(absolute)),
        f"{prefix}_rmse_{unit}": float(math.sqrt(float(np.mean(errors**2)))),
        f"{prefix}_bias_{unit}": float(np.mean(errors)),
        f"{prefix}_mape_pct": float(np.mean(relative)),
        f"{prefix}_within_10_pct": f"{int(np.sum(relative <= 10.0))}/{n}",
        f"{prefix}_worst_pct": float(np.max(relative)),
        f"{prefix}_worst_abs_{unit}": float(np.max(absolute)),
    }


def _ratio_stats(ratios: list[float]) -> dict[str, float]:
    """Median/min/max of predicted-over-harvested, the sanity-check framing.

    Task 4's implementer ran route B ad hoc, uncommitted, and reported a
    Chave median ratio of 1.0962 (range 0.709-2.326) and a T-VER median of
    0.9807 (range 0.494-2.113). This is what a wildly different number here
    would be checked against before trusting the rest of the run.
    """
    ordered = sorted(ratios)
    return {
        "predicted_over_harvested_median": float(ordered[len(ordered) // 2]),
        "predicted_over_harvested_min": float(ordered[0]),
        "predicted_over_harvested_max": float(ordered[-1]),
    }


def _round_floats(value: Any) -> Any:
    """Round every float in a nested structure, once, after every average is
    taken -- never before. Rounding first and averaging second is the exact
    mistake documented in docs/ml/DEMOL_EVIDENCE_CHAIN.md: it produced a
    published DBH MAE 3% higher than the pipeline's own arithmetic.
    """
    if isinstance(value, float):
        return round(value, PUBLISHED_DECIMALS)
    if isinstance(value, dict):
        return {key: _round_floats(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round_floats(item) for item in value]
    return value


def derive(*, archive_root: Path) -> dict[str, Any]:
    """Run the frozen protocol and return the artefact, unwritten."""
    from pipeline import qsm, wood_leaf_separation
    from pipeline.cameroon_eval import (
        CLOUD_WITHOUT_GROUND_TRUTH,
        COHORT_SIZE,
        SIZE_BAND_EDGES_CM,
        TVER_FOREST_TYPE,
        UNCONFOUNDED_MAX_DBH_CM,
        chave_agb_kg,
        geometry_row,
        load_cameroon_cohort,
        mass_row,
        small_stem_dbh_mae_cm,
        tver_agb_kg,
    )

    cohort = load_cameroon_cohort(
        archive_root, GROUND_TRUTH_CSV, max_points=MAX_POINTS, sample_seed=SAMPLE_SEED
    )
    if len(cohort) != COHORT_SIZE:
        raise SystemExit(f"expected {COHORT_SIZE} trees, loaded {len(cohort)}")

    segmenter = wood_leaf_separation.WoodLeafSegmenter(backend="tlsep")

    def size_band(dbh_cm: float) -> str:
        for name, low, high in SIZE_BAND_EDGES_CM:
            if low <= dbh_cm < high:
                return name
        raise ValueError(f"{dbh_cm} cm matched no size band")

    per_tree: list[dict[str, Any]] = []
    for tree in cohort:
        row: dict[str, Any] = {
            "tree_id": tree.tree_id,
            "genus": tree.genus,
            "species": tree.species,
            "cloud_was_repaired": tree.cloud_was_repaired,
            "size_band": size_band(tree.gt_dbh_cm),
            "gt_dbh_cm": tree.gt_dbh_cm,
            "gt_height_m": tree.gt_height_m,
            "gt_agb_kg": tree.gt_agb_kg,
            "gt_volume_m3": tree.gt_volume_m3,
            "gt_stem_volume_m3": tree.gt_stem_volume_m3,
            "wsg_kg_m3": tree.wsg_kg_m3,
            "reference_dbh_cm": tree.reference_dbh_cm,
            "reference_height_m": tree.reference_height_m,
            "reference_qsm_volume_m3": tree.reference_qsm_volume_m3,
        }

        # Route B: tape DBH and felled height, no point cloud involved. Costed
        # for every tree regardless of whether the cloud can be measured at
        # all, because it needs no QSM -- this is the equation's own error
        # with measurement removed.
        route_b_chave = chave_agb_kg(
            dbh_cm=tree.gt_dbh_cm, height_m=tree.gt_height_m, wood_density_kg_m3=tree.wsg_kg_m3
        )
        route_b_tver = tver_agb_kg(dbh_cm=tree.gt_dbh_cm, height_m=tree.gt_height_m)
        row["chave_route_b_agb_kg"] = route_b_chave
        row["chave_route_b_ape_pct"] = abs(route_b_chave - tree.gt_agb_kg) / tree.gt_agb_kg * 100.0
        row["chave_route_b_ratio"] = route_b_chave / tree.gt_agb_kg
        row["tver_route_b_agb_kg"] = route_b_tver
        row["tver_route_b_ape_pct"] = abs(route_b_tver - tree.gt_agb_kg) / tree.gt_agb_kg * 100.0
        row["tver_route_b_ratio"] = route_b_tver / tree.gt_agb_kg

        # Route A: whatever the pipeline itself measures off the point cloud.
        # This is the step expected to fail sometimes -- a slice with too few
        # wood points at breast height, an occluded scan -- and a failure here
        # is counted and named, not dropped.
        try:
            labels = segmenter.segment(tree.points)
            labels = np.asarray(labels)
            if labels.shape != (len(tree.points),):
                raise ValueError(f"tlsep returned {labels.shape} labels for {len(tree.points)} points")
            wood_points = np.ascontiguousarray(tree.points[labels == 0], dtype=np.float64)
            measurement = qsm.compute_qsm(wood_points, seed=QSM_SEED)
            bad_fields = [
                field
                for field, value in (
                    ("dbh_cm", measurement.dbh_cm),
                    ("height_m", measurement.height_m),
                    ("total_volume_m3", measurement.total_volume_m3),
                )
                if not _finite_positive(value)
            ]
            if bad_fields:
                raise ValueError(f"non-positive or non-finite: {', '.join(bad_fields)}")
            failure = None
        except Exception as exc:  # the boundary this evaluation exists to report through
            measurement = None
            failure = f"{type(exc).__name__}: {exc}"

        row["status"] = "measurable" if failure is None else "excluded"
        row["exclusion_reason"] = failure

        route_a_fields = (
            "measured_dbh_cm", "measured_height_m", "measured_stem_volume_m3",
            "measured_total_volume_m3", "model_quality", "dbh_error_cm", "height_error_m",
            "dbh_error_vs_reference_cm", "height_error_vs_reference_m",
            "chave_route_a_agb_kg", "chave_route_a_ape_pct", "chave_measurement_share_pct",
            "tver_route_a_agb_kg", "tver_route_a_ape_pct", "tver_measurement_share_pct",
        )
        if measurement is None:
            row.update(dict.fromkeys(route_a_fields))
            per_tree.append(row)
            continue

        geometry = geometry_row(
            tree_id=tree.tree_id,
            measured_dbh_cm=measurement.dbh_cm,
            measured_height_m=measurement.height_m,
            gt_dbh_cm=tree.gt_dbh_cm,
            gt_height_m=tree.gt_height_m,
            reference_dbh_cm=tree.reference_dbh_cm,
            reference_height_m=tree.reference_height_m,
        )
        route_a_chave = chave_agb_kg(
            dbh_cm=measurement.dbh_cm, height_m=measurement.height_m, wood_density_kg_m3=tree.wsg_kg_m3
        )
        route_a_tver = tver_agb_kg(dbh_cm=measurement.dbh_cm, height_m=measurement.height_m)
        chave_mass = mass_row(
            tree_id=tree.tree_id,
            gt_agb_kg=tree.gt_agb_kg,
            route_a_agb_kg=route_a_chave,
            route_b_agb_kg=route_b_chave,
        )
        tver_mass = mass_row(
            tree_id=tree.tree_id,
            gt_agb_kg=tree.gt_agb_kg,
            route_a_agb_kg=route_a_tver,
            route_b_agb_kg=route_b_tver,
        )
        row.update(
            {
                "measured_dbh_cm": measurement.dbh_cm,
                "measured_height_m": measurement.height_m,
                "measured_stem_volume_m3": measurement.stem_volume_m3,
                "measured_total_volume_m3": measurement.total_volume_m3,
                "model_quality": measurement.model_quality,
                "dbh_error_cm": geometry["dbh_error_cm"],
                "height_error_m": geometry["height_error_m"],
                "dbh_error_vs_reference_cm": geometry["dbh_error_vs_reference_cm"],
                "height_error_vs_reference_m": geometry["height_error_vs_reference_m"],
                "chave_route_a_agb_kg": route_a_chave,
                "chave_route_a_ape_pct": chave_mass["route_a_ape_pct"],
                "chave_measurement_share_pct": chave_mass["measurement_share_pct"],
                "tver_route_a_agb_kg": route_a_tver,
                "tver_route_a_ape_pct": tver_mass["route_a_ape_pct"],
                "tver_measurement_share_pct": tver_mass["measurement_share_pct"],
            }
        )
        per_tree.append(row)

    per_tree.sort(key=lambda item: item["tree_id"])
    measurable = [row for row in per_tree if row["status"] == "measurable"]
    excluded = [row for row in per_tree if row["status"] != "measurable"]
    if not measurable:
        raise SystemExit("no tree in the cohort was measurable -- nothing to publish")

    metrics: dict[str, Any] = {
        "cohort_size": COHORT_SIZE,
        "trees_measured": len(measurable),
        "trees_excluded": len(excluded),
        "excluded": [
            {"tree_id": row["tree_id"], "reason": row["exclusion_reason"]} for row in excluded
        ],
    }

    # 1. The headline: DBH MAE on the unconfounded (small-stem) subset -- the
    # only one where our measurement and the ground truth are the same
    # measurement. Raises if the subset is empty, which is deliberate: a run
    # that could not report this figure has nothing to be judged on.
    small_stem_rows = [row for row in measurable if row["gt_dbh_cm"] < UNCONFOUNDED_MAX_DBH_CM]
    metrics["dbh_mae_cm_small_stems"] = small_stem_dbh_mae_cm(measurable)
    metrics["dbh_mae_cm_small_stems_n"] = len(small_stem_rows)

    # DBH / height vs the tape, all measurable trees -- an upper bound on
    # measurement error, confounded by buttressing above ~50 cm. See
    # pipeline/cameroon_eval.py's UNCONFOUNDED_MAX_DBH_CM.
    dbh_errors = np.array([row["dbh_error_cm"] for row in measurable])
    dbh_truth = np.array([row["gt_dbh_cm"] for row in measurable])
    metrics.update(_error_stats(dbh_errors, dbh_truth, prefix="dbh", unit="cm"))

    height_errors = np.array([row["height_error_m"] for row in measurable])
    height_truth = np.array([row["gt_height_m"] for row in measurable])
    metrics.update(_error_stats(height_errors, height_truth, prefix="height", unit="m"))

    # Volume vs the destructive total (oven-dry, stump-inclusive). The taper
    # form factor that produces measured_total_volume_m3 is Belgian; see
    # protocol.taper_form_factor below.
    volume_errors = np.array(
        [row["measured_total_volume_m3"] - row["gt_volume_m3"] for row in measurable]
    )
    volume_truth = np.array([row["gt_volume_m3"] for row in measurable])
    metrics.update(_error_stats(volume_errors, volume_truth, prefix="volume", unit="m3"))

    # 2. DBH vs tape and vs the reference TLS, by size band -- where the
    # confound actually lives, and whether this pipeline is worse than a
    # published method facing the identical confound on the identical clouds.
    band_stats: dict[str, Any] = {}
    for name, low, high in SIZE_BAND_EDGES_CM:
        band_rows = [row for row in measurable if low <= row["gt_dbh_cm"] < high]
        if not band_rows:
            band_stats[name] = {"n": 0}
            continue
        band_dbh_err = np.array([row["dbh_error_cm"] for row in band_rows])
        band_ref_err = np.array([row["dbh_error_vs_reference_cm"] for row in band_rows])
        band_quality = np.array([row["model_quality"] for row in band_rows])
        band_stats[name] = {
            "n": len(band_rows),
            "dbh_bias_cm": float(np.mean(band_dbh_err)),
            "dbh_mae_cm": float(np.mean(np.abs(band_dbh_err))),
            "dbh_bias_vs_reference_cm": float(np.mean(band_ref_err)),
            "dbh_mae_vs_reference_cm": float(np.mean(np.abs(band_ref_err))),
            "ransac_inlier_ratio_mean": float(np.mean(band_quality)),
        }
    metrics["dbh_bias_by_size_band"] = band_stats

    # vs the reference TLS, across all measurable trees (not banded).
    ref_dbh_err = np.array([row["dbh_error_vs_reference_cm"] for row in measurable])
    ref_height_err = np.array([row["height_error_vs_reference_m"] for row in measurable])
    metrics["dbh_mae_vs_reference_cm"] = float(np.mean(np.abs(ref_dbh_err)))
    metrics["dbh_bias_vs_reference_cm"] = float(np.mean(ref_dbh_err))
    metrics["height_mae_vs_reference_m"] = float(np.mean(np.abs(ref_height_err)))
    metrics["height_bias_vs_reference_m"] = float(np.mean(ref_height_err))

    # vs the authors' own edited QSM total volume (the _5 family, branches
    # under 5 cm excluded). Not the same basis as gt_volume_m3 -- see
    # data/cameroon_61/README.md -- but both are what a QSM can see, so this
    # is the fairer method-vs-method comparison for volume.
    ref_qsm_errors = np.array(
        [row["measured_total_volume_m3"] - row["reference_qsm_volume_m3"] for row in measurable]
    )
    ref_qsm_truth = np.array([row["reference_qsm_volume_m3"] for row in measurable])
    metrics.update(
        _error_stats(ref_qsm_errors, ref_qsm_truth, prefix="volume_vs_reference_qsm", unit="m3")
    )

    # 3 & 4. Route B (equation only) and route A (what a user gets), Chave and
    # T-VER, plus the measurement/equation split.
    for model in ("chave", "tver"):
        route_b_ape = [row[f"{model}_route_b_ape_pct"] for row in per_tree]
        route_b_ratio = [row[f"{model}_route_b_ratio"] for row in per_tree]
        metrics[f"{model}_route_b_ape_pct_mean"] = float(np.mean(route_b_ape))
        metrics[f"{model}_route_b_ape_pct_median"] = float(np.median(route_b_ape))
        metrics[f"{model}_route_b"] = _ratio_stats(route_b_ratio)

        route_a_ape = [row[f"{model}_route_a_ape_pct"] for row in measurable]
        metrics[f"{model}_route_a_ape_pct_mean"] = float(np.mean(route_a_ape))
        metrics[f"{model}_route_a_ape_pct_median"] = float(np.median(route_a_ape))
        within_20 = sum(1 for value in route_a_ape if value <= 20.0)
        metrics[f"{model}_route_a_within_20_pct"] = f"{within_20}/{len(route_a_ape)}"

        share = [row[f"{model}_measurement_share_pct"] for row in measurable]
        metrics[f"{model}_measurement_share_pct_mean"] = float(np.mean(share))
        metrics[f"{model}_measurement_share_pct_median"] = float(np.median(share))

    # Chave vs T-VER, route B, head to head on the same 61 trees. No verdict
    # is enforced either way -- see cameroon_eval.TVER_FOREST_TYPE's docstring
    # and the spec section 6: which model wins is the finding, not a gate.
    chave_closer = sum(
        1 for row in per_tree if row["chave_route_b_ape_pct"] < row["tver_route_b_ape_pct"]
    )
    metrics["chave_vs_tver_route_b_chave_closer_count"] = chave_closer
    metrics["chave_vs_tver_route_b_tver_closer_count"] = COHORT_SIZE - chave_closer

    metrics = _round_floats(metrics)

    return {
        "schema_version": "1",
        "dataset": "Momo Takoudjou et al. 2018 destructive tropical validation",
        "gate": {
            "min_dbh_fit_quality": qsm.MIN_DBH_FIT_QUALITY,
            "applied": False,
            "note": (
                "Recorded for context, not applied. compute_qsm does not read this "
                "gate -- it is applied by single_tree.py and main.py -- and this "
                "evaluation calls compute_qsm directly, exactly as "
                "derive_demol_evidence.py does for the Demol cohort."
            ),
        },
        "derivation": {
            "commit": _git("rev-parse", "HEAD"),
            "dirty": bool(_git("status", "--porcelain", "--untracked-files=normal")),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "protocol": {
            "cohort_size": COHORT_SIZE,
            "clouds_available": COHORT_SIZE + 1,
            "excluded_cloud": CLOUD_WITHOUT_GROUND_TRUTH,
            "max_points": MAX_POINTS,
            "sample_seed": SAMPLE_SEED,
            "qsm_seed": QSM_SEED,
            "ground_truth_csv_sha256": _sha256_file(GROUND_TRUTH_CSV),
            "tver_forest_type": TVER_FOREST_TYPE,
            "tver_forest_type_reason": (
                "eastern Cameroon is semi-deciduous forest, the stand type T-VER's "
                "mixed_deciduous row covers; fixed before the run rather than chosen "
                "after seeing the answers -- spec section 6"
            ),
            "taper_form_factor": {
                "total_tree_form_factor": qsm.TOTAL_TREE_FORM_FACTOR,
                "stem_form_factor": qsm.STEM_FORM_FACTOR,
                "calibrated_on": "65 Belgian temperate trees (Demol et al. 2021), not this cohort",
                "calibration_commit": TAPER_CALIBRATION_COMMIT,
            },
            # The commit this run happened at. Excluded from the --check
            # comparison for the same reason derivation.commit is: it
            # legitimately differs on a later run, while every other field in
            # this dict must not. See _comparable.
            "derivation_commit": _git("rev-parse", "HEAD"),
        },
        "metrics": metrics,
        "per_tree": per_tree,
    }


def _serialise(artefact: dict[str, Any]) -> str:
    return json.dumps(artefact, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _comparable(artefact: dict[str, Any]) -> dict[str, Any]:
    """Everything a re-run must reproduce.

    `derivation` is dropped entirely, and `protocol.derivation_commit` with
    it, for the same reason derive_demol_evidence.py drops `derivation`: the
    commit a run happened at legitimately differs on a later run, while the
    measurement and the protocol that produced it must not. Every other
    protocol field -- the taper constants and where they were calibrated, the
    point budget, the seeds, the T-VER row, the ground-truth hash, the cohort
    accounting -- gets no such exemption.
    """
    result = {key: value for key, value in artefact.items() if key != "derivation"}
    protocol = {key: value for key, value in result["protocol"].items() if key != "derivation_commit"}
    result["protocol"] = protocol
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-derive and fail if the recorded artefact no longer matches",
    )
    parser.add_argument("--archive", type=Path, default=ARCHIVE, help="path to the extracted Trees/ directory")
    parser.add_argument("--output", type=Path, default=ARTEFACT, help="where to write/read the artefact")
    args = parser.parse_args(argv)

    archive_root = args.archive.resolve()
    output = args.output.resolve()

    if not (archive_root / "database.xls").is_file():
        print(f"Cameroon archive not found under {archive_root}", file=sys.stderr)
        print("1.29 GB, not in git -- see docs/ml/CAMEROON_EVIDENCE_CHAIN.md", file=sys.stderr)
        return 2

    artefact = derive(archive_root=archive_root)

    if not args.check:
        output.parent.mkdir(parents=True, exist_ok=True)
        # newline="" so the bytes on disk are the bytes hashed -- the default
        # translates \n to \r\n on Windows, which would leave the printed
        # digest describing a file that does not exist.
        payload = _serialise(artefact).encode("utf-8")
        with output.open("wb") as handle:
            handle.write(payload)
        digest = hashlib.sha256(payload).hexdigest()
        print(f"wrote {output}")
        print(f"sha256 {digest}")
        metrics = artefact["metrics"]
        print("headline, in the reading order Task 5 specifies:")
        print(
            f"  1. dbh_mae_cm_small_stems: {metrics['dbh_mae_cm_small_stems']} "
            f"(n={metrics['dbh_mae_cm_small_stems_n']})"
        )
        print(f"  2. dbh_bias_by_size_band: {metrics['dbh_bias_by_size_band']}")
        print(
            f"  3. chave_route_b_ape_pct_median: {metrics['chave_route_b_ape_pct_median']}  "
            f"tver_route_b_ape_pct_median: {metrics['tver_route_b_ape_pct_median']}"
        )
        print(
            f"  4. chave_measurement_share_pct_median: {metrics['chave_measurement_share_pct_median']}  "
            f"tver_measurement_share_pct_median: {metrics['tver_measurement_share_pct_median']}"
        )
        print(f"  5. trees_excluded: {metrics['trees_excluded']} of {metrics['cohort_size']}: {metrics['excluded']}")
        return 0

    if not output.is_file():
        print(f"{output} does not exist -- run without --check to derive it", file=sys.stderr)
        return 1

    recorded = json.loads(output.read_text(encoding="utf-8"))
    recorded_comparable = _comparable(recorded)
    artefact_comparable = _comparable(artefact)
    if recorded_comparable == artefact_comparable:
        print(f"{output} reproduces")
        return 0

    print(f"{output} no longer reproduces:", file=sys.stderr)
    recorded_metrics = recorded_comparable.get("metrics", {})
    artefact_metrics = artefact_comparable["metrics"]
    for field in sorted(set(recorded_metrics) | set(artefact_metrics)):
        was = recorded_metrics.get(field)
        now = artefact_metrics.get(field)
        if was != now:
            print(f"  metrics.{field}: recorded {was!r}, derived {now!r}", file=sys.stderr)
    if recorded_comparable["protocol"] != artefact_comparable["protocol"]:
        print(
            f"  protocol: recorded {recorded_comparable['protocol']!r}",
            file=sys.stderr,
        )
        print(f"  protocol: derived  {artefact_comparable['protocol']!r}", file=sys.stderr)
    print("Re-run without --check, then update the manifest from it.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
