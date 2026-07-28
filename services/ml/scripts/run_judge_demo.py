"""Build a two-run deterministic judge-demo artifact candidate."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

import click

ML_ROOT = Path(__file__).resolve().parents[1]
RUNNER_REPO_ROOT = ML_ROOT.parents[1].resolve()

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
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "commit": commit,
        "dirty": bool(dirty),
    }


def _git_bytes(repo_root: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True).stdout


def _source_identity(repo_root: Path, commit: str) -> dict[str, Any]:
    listed = _git_bytes(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        commit,
        "--",
        "services/ml/pipeline",
        "services/ml/scripts/run_judge_demo.py",
        "services/ml/data/species_db.csv",
    ).decode("utf-8")
    tracked_files = sorted(
        path
        for path in listed.splitlines()
        if path.endswith(".py") or path == "services/ml/data/species_db.csv"
    )
    required = {
        "services/ml/scripts/run_judge_demo.py",
        "services/ml/pipeline/main.py",
        "services/ml/pipeline/ply_export.py",
        "services/ml/data/species_db.csv",
    }
    if not required.issubset(tracked_files):
        raise RuntimeError("Required judge-demo source files are not tracked")

    digest = hashlib.sha256()
    for relative in tracked_files:
        path = repo_root / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(repo_root):
            raise RuntimeError(f"Judge-demo source is not a contained regular file: {relative}")
        committed_blob = _git_bytes(repo_root, "rev-parse", f"{commit}:{relative}").strip()
        working_blob = _git_bytes(repo_root, "hash-object", f"--path={relative}", relative).strip()
        if working_blob != committed_blob:
            raise RuntimeError(f"Judge-demo source does not match analyzed commit: {relative}")
        blob_bytes = _git_bytes(repo_root, "show", f"{commit}:{relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(blob_bytes).digest())
    return {"tree_sha256": digest.hexdigest(), "tracked_files": tracked_files}


def _snapshot_identity(snapshot_root: Path, tracked_files: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in tracked_files:
        path = snapshot_root / relative
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.resolve().is_relative_to(snapshot_root)
        ):
            raise RuntimeError(f"Snapshot source is not a contained regular file: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


@contextmanager
def _source_snapshot(repo_root: Path, commit: str) -> Iterator[tuple[Path, dict[str, Any]]]:
    source = _source_identity(repo_root, commit)
    with tempfile.TemporaryDirectory(prefix="treeq-judge-source-") as temp_dir:
        snapshot_root = Path(temp_dir) / "source"
        for relative in source["tracked_files"]:
            target = snapshot_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_git_bytes(repo_root, "show", f"{commit}:{relative}"))
        if _snapshot_identity(snapshot_root, source["tracked_files"]) != source["tree_sha256"]:
            raise RuntimeError("Materialized source snapshot identity does not match commit")
        subprocess.run(["git", "init", "-q"], cwd=snapshot_root, check=True)
        subprocess.run(
            ["git", "-c", "core.autocrlf=false", "add", "services/ml"],
            cwd=snapshot_root,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=TreeQ Snapshot",
                "-c",
                "user.email=treeq-snapshot@example.invalid",
                "commit",
                "-qm",
                f"judge source snapshot {commit}",
            ],
            cwd=snapshot_root,
            check=True,
        )
        yield snapshot_root, source


def _load_pipeline_modules(source_ml_root: str | Path | None = None) -> dict[str, Any]:
    source_ml_root = Path(source_ml_root or ML_ROOT).resolve()
    ml_root = str(source_ml_root)
    if ml_root in sys.path:
        sys.path.remove(ml_root)
    sys.path.insert(0, ml_root)
    for module_name in list(sys.modules):
        if module_name == "pipeline" or module_name.startswith("pipeline."):
            del sys.modules[module_name]
    modules = {
        name: importlib.import_module(module_name)
        for name, module_name in {
            "main": "pipeline.main",
            "ply_export": "pipeline.ply_export",
            "synthetic": "pipeline.synthetic",
        }.items()
    }
    for name, module in modules.items():
        origin = Path(module.__file__).resolve()
        if not origin.is_relative_to(source_ml_root):
            raise RuntimeError(f"Pipeline module {name} came from another checkout: {origin}")
    return modules


@contextmanager
def _isolated_pipeline_modules(source_ml_root: Path) -> Iterator[dict[str, Any]]:
    original_path = list(sys.path)
    displaced = {
        name: module
        for name, module in sys.modules.items()
        if name == "pipeline" or name.startswith("pipeline.")
    }
    try:
        yield _load_pipeline_modules(source_ml_root)
    finally:
        for module_name in list(sys.modules):
            if module_name == "pipeline" or module_name.startswith("pipeline."):
                del sys.modules[module_name]
        sys.modules.update(displaced)
        sys.path[:] = original_path


def _result_payload(
    result: Any, repo_state: dict[str, Any], source: dict[str, Any]
) -> dict[str, Any]:
    metadata = dict(result.metadata)
    metadata["input_file"] = "input.ply"
    metadata["git_commit"] = repo_state["commit"]
    metadata["git_dirty"] = repo_state["dirty"]
    metadata["source_tree_sha256"] = source["tree_sha256"]
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
    with _source_snapshot(repo_root, start_state["commit"]) as (
        snapshot_root,
        source,
    ):
        snapshot_ml_root = snapshot_root / "services" / "ml"
        with _isolated_pipeline_modules(snapshot_ml_root) as modules:
            points, _, _ = modules["synthetic"].generate_synthetic_plot(**DEMO_CONFIG)
            input_path = modules["ply_export"].write_xyz_ply(points, output_dir / "input.ply")
            input_bytes = input_path.read_bytes()

            result_bytes: list[bytes] = []
            segmented_paths: list[Path] = []
            segmented_bytes: list[bytes] = []
            payloads: list[dict[str, Any]] = []
            for run_number in (1, 2):
                segmented_path = output_dir / f"segmented-run-{run_number}.ply"
                result = modules["main"].process_point_cloud(
                    input_path,
                    wood_leaf_backend="tlsep",
                    default_species="Tectona grandis",
                    segmented_ply_out=str(segmented_path),
                )
                payload = _result_payload(result, start_state, source)
                payloads.append(payload)
                result_bytes.append(_json_bytes(payload))
                segmented_paths.append(segmented_path)
                segmented_bytes.append(segmented_path.read_bytes())
                if (
                    _snapshot_identity(snapshot_root, source["tracked_files"])
                    != source["tree_sha256"]
                ):
                    raise RuntimeError("Materialized source snapshot changed during analysis")
                if _source_identity(repo_root, start_state["commit"]) != source:
                    raise RuntimeError("Judge-demo source changed during analysis")

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
        "source": source,
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
