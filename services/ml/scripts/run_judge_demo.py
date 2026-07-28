"""Build a two-run deterministic judge-demo artifact candidate."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import click

ML_ROOT = Path(__file__).resolve().parents[1]
RUNNER_REPO_ROOT = ML_ROOT.parents[1].resolve()
if str(ML_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_ROOT))

from pipeline.main import process_point_cloud  # noqa: E402
from pipeline.ply_export import write_xyz_ply  # noqa: E402
from pipeline.provenance import git_worktree_dirty, resolve_git_commit  # noqa: E402
from pipeline.synthetic import generate_synthetic_plot  # noqa: E402

DEMO_CONFIG = {
    "n_trees": 3,
    "plot_size_m": 20.0,
    "ground_z_variation": 0.8,
    "ground_point_density": 20.0,
    "leaves_per_tree": 1500,
    "seed": 42,
}
DATASET = "deterministic_synthetic_plot_seed_42"
SCOPE = "deterministic_fixture_not_accuracy_or_credit_validation"


def _json_bytes(payload: dict[str, Any]) -> bytes:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
    return f"{encoded}\n".encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _artifact(filename: str, data: bytes) -> dict[str, Any]:
    return {"filename": filename, "sha256": _sha256(data), "size_bytes": len(data)}


def _repo_state(repo_root: Path) -> dict[str, Any]:
    return {
        "commit": resolve_git_commit(repo_root),
        "dirty": git_worktree_dirty(repo_root),
    }


def _result_payload(result: Any, repo_state: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(result.metadata)
    metadata["input_file"] = "input.ply"
    metadata["git_commit"] = repo_state["commit"]
    metadata["git_dirty"] = repo_state["dirty"]
    return {
        "metadata": metadata,
        "summary": result.summary,
        "diagnostics": {"dataset": DATASET, "scope": SCOPE},
        "trees": [asdict(tree) for tree in result.trees],
    }


def run_judge_demo(output_dir: str | Path, repo_root: str | Path) -> dict[str, Any]:
    """Run the repository fixture twice and publish only identical outputs."""
    output_dir = Path(output_dir)
    repo_root = Path(repo_root).resolve()
    if repo_root != RUNNER_REPO_ROOT:
        raise ValueError("repo_root must be the checkout containing the judge runner")
    if output_dir.exists():
        if not output_dir.is_dir() or any(output_dir.iterdir()):
            raise ValueError("Judge demo output directory must be empty")
    else:
        output_dir.mkdir(parents=True)

    start_state = _repo_state(repo_root)
    if start_state["dirty"]:
        raise ValueError("Judge demo requires a clean repository before analysis")

    points, _, _ = generate_synthetic_plot(**DEMO_CONFIG)
    input_path = write_xyz_ply(points, output_dir / "input.ply")
    input_bytes = input_path.read_bytes()

    result_bytes: list[bytes] = []
    segmented_paths: list[Path] = []
    segmented_bytes: list[bytes] = []
    payloads: list[dict[str, Any]] = []
    for run_number in (1, 2):
        segmented_path = output_dir / f"segmented-run-{run_number}.ply"
        result = process_point_cloud(
            input_path,
            wood_leaf_backend="tlsep",
            default_species="Tectona grandis",
            segmented_ply_out=str(segmented_path),
        )
        payload = _result_payload(result, start_state)
        payloads.append(payload)
        result_bytes.append(_json_bytes(payload))
        segmented_paths.append(segmented_path)
        segmented_bytes.append(segmented_path.read_bytes())

    result_hashes = [_sha256(data) for data in result_bytes]
    segmented_hashes = [_sha256(data) for data in segmented_bytes]
    reproducible = result_bytes[0] == result_bytes[1] and segmented_bytes[0] == segmented_bytes[1]
    summary = {
        "reproducible": reproducible,
        "result_sha256": result_hashes,
        "segmented_ply_sha256": segmented_hashes,
    }
    if not reproducible:
        raise RuntimeError("Judge demo is not reproducible")
    end_state = _repo_state(repo_root)
    if end_state != start_state or end_state["dirty"]:
        raise RuntimeError("Repository changed during judge demo analysis")

    (output_dir / "result.json").write_bytes(result_bytes[0])
    segmented_paths[0].replace(output_dir / "segmented.ply")
    segmented_paths[1].unlink()

    metadata = payloads[0]["metadata"]
    pipeline_summary = payloads[0]["summary"]
    candidate = {
        "schema_version": 1,
        "reproducible": True,
        "analyzed_commit": metadata["git_commit"],
        "git_dirty": metadata["git_dirty"],
        "dataset": DATASET,
        "scope": SCOPE,
        "reproducibility": {
            "run_count": 2,
            "result_sha256": result_hashes,
            "segmented_ply_sha256": segmented_hashes,
        },
        "pipeline": {
            "version": metadata["pipeline_version"],
            "backend": metadata["wood_leaf_backend"],
            "checkpoint_sha256": metadata["checkpoint_sha256"],
            "algorithms": metadata["algorithms"],
        },
        "result": {
            "input_points": metadata["n_input_points"],
            "total_trees": pipeline_summary["total_trees"],
            "total_carbon_kg": pipeline_summary["total_carbon_kg"],
            "total_co2eq_kg": pipeline_summary["total_co2eq_kg"],
        },
        "artifacts": {
            "input": _artifact("input.ply", input_bytes),
            "result": _artifact("result.json", result_bytes[0]),
            "segmented": _artifact("segmented.ply", segmented_bytes[0]),
        },
    }
    (output_dir / "candidate.json").write_bytes(_json_bytes(candidate))
    published = {path.name for path in output_dir.iterdir()}
    expected = {"input.ply", "result.json", "segmented.ply", "candidate.json"}
    if published != expected or not all((output_dir / name).is_file() for name in expected):
        raise RuntimeError("Judge demo output does not contain exactly four regular files")
    return summary


@click.command()
@click.option("--output-dir", required=True, type=click.Path(path_type=Path))
@click.option("--repo-root", default=RUNNER_REPO_ROOT, type=click.Path(path_type=Path))
def cli(output_dir: Path, repo_root: Path) -> None:
    """Generate candidate files and print an ASCII-safe verification summary."""
    click.echo(json.dumps(run_judge_demo(output_dir, repo_root), sort_keys=True))


if __name__ == "__main__":
    cli()
