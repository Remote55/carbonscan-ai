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


@click.command()
@click.option("--output-dir", required=True, type=click.Path(path_type=Path))
@click.option("--repo-root", default="../..", type=click.Path(path_type=Path))
def cli(output_dir: Path, repo_root: Path) -> None:
    """Run the deterministic baseline and print an ASCII-safe JSON summary."""
    summary = run_core_demo(output_dir, repo_root)
    click.echo(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    cli()
