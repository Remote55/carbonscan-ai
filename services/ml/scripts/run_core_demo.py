"""Run the reviewed tlsep core demo twice and emit auditable artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click

from pipeline.main import PIPELINE_VERSION, process_points
from pipeline.provenance import normalized_sha256, resolve_git_commit, sha256_file
from pipeline.synthetic import generate_synthetic_plot

DEMO_CONFIG = {
    "n_trees": 3,
    "plot_size_m": 20.0,
    "ground_z_variation": 0.8,
    "ground_point_density": 20.0,
    "leaves_per_tree": 1500,
    "seed": 42,
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _pipeline_payload(result: Any) -> dict[str, Any]:
    from pipeline.main import pipeline_result_to_dict

    return pipeline_result_to_dict(result)


def _evidence(
    payload: dict[str, Any], created_at: str, output_dir: Path
) -> dict[str, Any]:
    metadata = payload["metadata"]
    return {
        "schema_version": "1",
        "run": {
            "input_sha256": metadata["input_sha256"],
            "git_commit": metadata["git_commit"],
            "git_dirty": metadata["git_dirty"],
            "pipeline_version": metadata["pipeline_version"],
            "backend": metadata["wood_leaf_backend"],
            "checkpoint_sha256": metadata["checkpoint_sha256"],
            "config": DEMO_CONFIG,
        },
        "algorithms": metadata["algorithms"],
        "results": payload["summary"],
        "trees": payload["trees"],
        "evidence": {
            "dataset": "deterministic_synthetic_plot_seed_42",
            "scope": "core_demo_fixture_not_accuracy_benchmark",
            "candidate_status": metadata["candidate_status"],
        },
        "runtime": {
            "created_at": created_at,
            "output_dir": str(output_dir),
        },
    }


def run_core_demo(output_dir: str | Path, repo_root: str | Path) -> dict[str, Any]:
    """Run the fixed fixture twice and publish artifacts only when both runs agree."""
    output_dir = Path(output_dir)
    repo_root = Path(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    points, _, _ = generate_synthetic_plot(**DEMO_CONFIG)

    evidence_runs: list[dict[str, Any]] = []
    ply_hashes: list[str] = []
    payloads: list[dict[str, Any]] = []
    run_ply_paths: list[Path] = []

    for index in (1, 2):
        ply_path = output_dir / f"segmented-run-{index}.ply"
        result = process_points(
            points,
            wood_leaf_backend="tlsep",
            default_species="Tectona grandis",
            segmented_ply_out=str(ply_path),
        )
        result.metadata["git_commit"] = resolve_git_commit(repo_root)
        payload = _pipeline_payload(result)
        payloads.append(payload)
        evidence_runs.append(
            _evidence(payload, datetime.now(UTC).isoformat(), output_dir)
        )
        ply_hashes.append(sha256_file(ply_path))
        run_ply_paths.append(ply_path)

    result_hashes = [normalized_sha256(item) for item in evidence_runs]
    reproducible = (
        result_hashes[0] == result_hashes[1]
        and ply_hashes[0] == ply_hashes[1]
    )
    summary = {
        "schema_version": "1",
        "reproducible": reproducible,
        "normalized_result_sha256": result_hashes,
        "segmented_ply_sha256": ply_hashes,
        "git_commit": resolve_git_commit(repo_root),
        "pipeline_version": PIPELINE_VERSION,
    }
    if not reproducible:
        raise RuntimeError("Core demo is not reproducible")

    _write_json(output_dir / "result.json", payloads[0])
    _write_json(output_dir / "evidence.json", evidence_runs[0])
    _write_json(output_dir / "verification-summary.json", summary)
    run_ply_paths[0].replace(output_dir / "segmented.ply")
    run_ply_paths[1].unlink()
    return summary


#: Fields of validation.core_demo that a fresh run reproduces, and where each
#: one comes from in the run's own evidence.json.
MANIFEST_CHECKED_FIELDS = {
    "total_trees": ("results", "total_trees"),
    "total_carbon_kg": ("results", "total_carbon_kg"),
    "total_co2eq_kg": ("results", "total_co2eq_kg"),
    "pipeline_version": ("run", "pipeline_version"),
}

#: Recorded in the manifest, deliberately not compared here, with the reason.
#:
#: input_sha256 hashes the raw float64 bytes of the generated plot. The first
#: CI run of this check caught it disagreeing -- 5ca1abb9 on Windows against
#: acf893e1 on Linux -- with identical numpy 2.4.6, identical Python, identical
#: seed, and identical results downstream. pipeline/synthetic.py builds every
#: coordinate out of np.sin and np.cos, and numpy dispatches those to different
#: SIMD kernels on different platforms and CPU feature sets. The values agree to
#: about fifteen significant digits, which is why total_carbon_kg and the tree
#: counts match exactly; the last bit does not, which is all a byte hash reads.
#:
#: So the hash is a within-machine determinism check -- two runs of this script
#: agreeing, which run_core_demo already asserts -- and not a cross-machine
#: invariant. It stays in the manifest as provenance for the run that produced
#: it. Comparing it across platforms would fail forever for a reason that has
#: nothing to do with the measurement.
MANIFEST_PER_MACHINE_FIELDS = ("input_sha256", "normalized_result_sha256", "segmented_ply_sha256")


def check_against_manifest(evidence: dict[str, Any], manifest_path: Path) -> list[str]:
    """Compare a completed run against the figures the manifest publishes.

    `sync_truth.py` validates that core_demo.total_carbon_kg is a positive
    number and stops there, so the block could describe any pipeline at all. It
    described one from three releases back: on 2026-08-14 the manifest carried
    pipeline_version 0.3.0, an analyzed_commit from long before, and totals 1.9%
    away from what the code produced, with every check green.

    That is the same defect docs/ml/DEMOL_EVIDENCE_CHAIN.md records for the
    accuracy figures, and it is easier to close here: the core demo is a
    synthetic plot with a fixed seed, so unlike the Demol cohort it runs on CI
    and this comparison can be enforced on every push.

    Returns:
        A list of human-readable disagreements; empty when the manifest is
        current.
    """
    published = json.loads(manifest_path.read_text(encoding="utf-8"))["core_demo"]
    problems = []
    for field, (section, key) in MANIFEST_CHECKED_FIELDS.items():
        produced = evidence[section][key]
        if published.get(field) != produced:
            problems.append(f"{field}: manifest {published.get(field)!r}, run {produced!r}")
    return problems


@click.command()
@click.option("--output-dir", required=True, type=click.Path(path_type=Path))
@click.option("--repo-root", default="../..", type=click.Path(path_type=Path))
@click.option(
    "--manifest",
    type=click.Path(path_type=Path, exists=True),
    help="fail if the published core_demo block no longer matches this run",
)
def cli(output_dir: Path, repo_root: Path, manifest: Path | None) -> None:
    """Run the deterministic baseline and print an ASCII-safe JSON summary."""
    summary = run_core_demo(output_dir, repo_root)
    click.echo(json.dumps(summary, sort_keys=True))

    if manifest is None:
        return
    evidence = json.loads((output_dir / "evidence.json").read_text(encoding="utf-8"))
    problems = check_against_manifest(evidence, manifest)
    if problems:
        for problem in problems:
            click.echo(f"core_demo is stale -- {problem}", err=True)
        click.echo(
            "Re-derive it: run this without --manifest from a clean worktree and "
            "copy the run's figures into docs/evidence/core_demo_manifest.json.",
            err=True,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
