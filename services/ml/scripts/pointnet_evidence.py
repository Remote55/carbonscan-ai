"""CLI for deterministic PointNet++ evidence preparation, training, and freeze."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pipeline.external_tree_dataset import fetch_external_cohort
from pipeline.independent_eval import run_independent_evaluation
from pipeline.provenance import (
    git_worktree_dirty,
    resolve_git_commit,
    sha256_file,
    write_canonical_json,
)
from training.evidence_protocol import load_protocol
from training.realdata_dataset import build_evidence_dataset


def _train_woodleaf(args: Any) -> dict[str, Any]:
    from training.train_woodleaf import train

    return train(args)


train_woodleaf = SimpleNamespace(train=_train_woodleaf)


def _summary_line(payload: dict[str, Any]) -> None:
    print(
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    )


def _prepare_wan(args: argparse.Namespace) -> dict[str, Any]:
    protocol = load_protocol(args.protocol)
    wan_root = Path(args.wan_root).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()
    manifest_out = Path(args.manifest_out).resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    plot_paths = [wan_root / filename for filename in protocol["wan"]["files"]]
    build_evidence_dataset(
        plot_paths,
        artifact_dir / "wan-train.npz",
        artifact_dir / "wan-dev.npz",
        manifest_out,
        protocol=protocol,
        repo_root=args.repo_root,
    )
    return {
        "command": "prepare-wan",
        "manifest_file": manifest_out.name,
        "manifest_sha256": sha256_file(manifest_out),
        "status": "ok",
    }


def _sanitize_training_record(
    record: dict[str, Any],
    expected_checkpoint_path: Path,
) -> dict[str, Any]:
    returned_path = Path(record["checkpoint_path"]).resolve()
    expected_checkpoint_path = expected_checkpoint_path.resolve()
    if returned_path != expected_checkpoint_path:
        raise ValueError("trainer returned an unexpected checkpoint_path")
    checkpoint_sha256 = sha256_file(expected_checkpoint_path)
    if record.get("checkpoint_sha256") != checkpoint_sha256:
        raise ValueError("trainer checkpoint_sha256 does not match checkpoint bytes")
    return {
        "seed": record["seed"],
        "best_epoch": record["best_epoch"],
        "best_macro_tile_wood_iou": record["best_macro_tile_wood_iou"],
        "dev_metrics": record["dev_metrics"],
        "state_dict_sha256": record["state_dict_sha256"],
        "checkpoint_file": expected_checkpoint_path.name,
        "checkpoint_sha256": checkpoint_sha256,
        "protocol_sha256": record["protocol_sha256"],
        "wan_manifest_sha256": record["wan_manifest_sha256"],
        "training_git_commit": record["training_git_commit"],
    }


def _training_command(
    protocol_path: Path,
    wan_manifest_path: Path,
    artifact_dir: Path,
) -> list[str]:
    return [
        "python",
        "-m",
        "scripts.pointnet_evidence",
        "train",
        "--protocol",
        protocol_path.name,
        "--wan-manifest",
        wan_manifest_path.name,
        "--artifact-dir",
        artifact_dir.name,
        "--repo-root",
        ".",
    ]


def _train(args: argparse.Namespace) -> dict[str, Any]:
    from training import evidence_training
    from training.evidence_training import run_training_matrix

    protocol_path = Path(args.protocol).resolve()
    wan_manifest_path = Path(args.wan_manifest).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()
    repo_root = Path(args.repo_root).resolve()
    protocol = load_protocol(protocol_path)
    protocol_sha256 = sha256_file(protocol_path)
    wan_manifest_sha256 = sha256_file(wan_manifest_path)
    wan_manifest = json.loads(wan_manifest_path.read_text(encoding="utf-8"))
    wan_evidence = evidence_training._validate_wan_manifest(wan_manifest)
    wan_output_paths = {}
    for split_name, output in wan_evidence["outputs"].items():
        output_path = (artifact_dir / output["filename"]).resolve()
        if not output_path.is_relative_to(artifact_dir):
            raise ValueError(f"Wan output {split_name} must resolve under artifact_dir")
        if not output_path.is_file():
            raise ValueError(f"Wan output {split_name} file is missing")
        if sha256_file(output_path) != output["sha256"]:
            raise ValueError(f"Wan output {split_name} sha256 mismatch")
        wan_output_paths[split_name] = output_path
    if git_worktree_dirty(repo_root):
        raise ValueError("Git working tree must be clean before training")
    training_git_commit = resolve_git_commit(repo_root)
    environment = evidence_training.capture_training_environment()
    training_command = _training_command(
        protocol_path,
        wan_manifest_path,
        artifact_dir,
    )
    evidence_training._validate_path_privacy(
        training_command,
        repo_root=repo_root,
    )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    training_runs_path = artifact_dir / "training_runs.json"
    winner_path = artifact_dir / "winner.pt"
    if training_runs_path.exists() or winner_path.exists():
        raise ValueError("training outputs already exist")
    train_npz = wan_output_paths["train"]
    dev_npz = wan_output_paths["dev"]
    training = protocol["training"]

    def train_one_seed(seed: int, output_path: Path) -> dict[str, Any]:
        train_args = SimpleNamespace(
            device="auto",
            seed=seed,
            train_npz=str(train_npz),
            val_npz=str(dev_npz),
            augment_synthetic=training["synthetic_samples"],
            synthetic_seed_start=training["synthetic_seed_start"],
            n_train=0,
            n_val=0,
            n_points=protocol["wan"]["points_per_tile"],
            batch_size=training["batch_size"],
            epochs=training["epochs"],
            lr=training["learning_rate"],
            weight_decay=training["weight_decay"],
            scheduler_step=training["scheduler_step"],
            scheduler_gamma=training["scheduler_gamma"],
            class_weight=training["class_weight"],
            init_checkpoint=None,
            out=str(output_path),
            protocol_sha256=protocol_sha256,
            wan_manifest_sha256=wan_manifest_sha256,
            training_git_commit=training_git_commit,
        )
        return train_woodleaf.train(train_args)

    matrix = run_training_matrix(
        protocol,
        artifact_dir,
        train_one_seed=train_one_seed,
    )
    winning_source = Path(matrix["winner"]["checkpoint_path"]).resolve()
    if winning_source.parent != artifact_dir:
        raise ValueError("winning checkpoint must resolve under artifact_dir")
    shutil.copyfile(winning_source, winner_path)

    runs = [
        _sanitize_training_record(
            record,
            artifact_dir / f"seed-{record['seed']}.pt",
        )
        for record in matrix["runs"]
    ]
    winner = _sanitize_training_record(matrix["winner"], winning_source)
    winner["checkpoint_file"] = "winner.pt"
    winner["checkpoint_sha256"] = sha256_file(winner_path)
    rerun = _sanitize_training_record(
        matrix["rerun"],
        artifact_dir / f"seed-{matrix['winner']['seed']}-rerun.pt",
    )
    training_runs = {
        "schema_version": "1",
        "experiment_id": protocol["experiment_id"],
        "protocol_sha256": protocol_sha256,
        "wan_manifest_sha256": wan_manifest_sha256,
        "training_git_commit": training_git_commit,
        "training_command": training_command,
        "environment": environment,
        "runs": runs,
        "winner": winner,
        "rerun": rerun,
        "reproducible": True,
    }
    evidence_training._validate_path_privacy(training_runs, repo_root=repo_root)
    write_canonical_json(training_runs_path, training_runs)
    return {
        "command": "train",
        "reproducible": True,
        "status": "ok",
        "winner_seed": winner["seed"],
    }


def _freeze(args: argparse.Namespace) -> dict[str, Any]:
    from training.evidence_training import build_freeze_manifest

    artifact_dir = Path(args.artifact_dir).resolve()
    manifest = build_freeze_manifest(
        args.protocol,
        args.wan_manifest,
        artifact_dir / "training_runs.json",
        artifact_dir,
        args.evidence_dir,
        args.repo_root,
    )
    return {
        "command": "freeze",
        "status": "ok",
        "training_runs_sha256": manifest["training_runs_sha256"],
        "winner_seed": manifest["winner"]["seed"],
    }


def _fetch_external(args: argparse.Namespace) -> dict[str, Any]:
    protocol_path = Path(args.protocol).resolve()
    protocol = load_protocol(protocol_path)
    manifest = fetch_external_cohort(
        protocol=protocol,
        freeze_manifest=args.freeze_manifest,
        checkpoint=args.checkpoint,
        destination=args.destination,
        manifest_out=args.manifest_out,
        repo_root=args.repo_root,
        protocol_sha256=sha256_file(protocol_path),
    )
    return {
        "command": "fetch-external",
        "files": len(manifest["files"]),
        "record_id": manifest["record"]["record_id"],
        "status": "ok",
        "trees": len(manifest["tree_ids"]),
    }


def _evaluate(args: argparse.Namespace) -> dict[str, Any]:
    result = run_independent_evaluation(
        protocol=args.protocol,
        freeze_manifest=args.freeze_manifest,
        checkpoint=args.checkpoint,
        external_root=args.external_root,
        external_manifest=args.external_manifest,
        demol_root=args.demol_root,
        evidence_dir=args.evidence_dir,
        repo_root=args.repo_root,
    )
    baseline = result["baseline"]
    candidate = result["candidate"]
    return {
        "baseline_dbh_mae_cm": baseline["downstream"]["dbh_mae_cm"],
        "baseline_height_mae_m": baseline["downstream"]["height_mae_m"],
        "baseline_measurable_trees": baseline["downstream"]["measurable_trees"],
        "baseline_volume_mape_pct": baseline["downstream"]["volume_mape_pct"],
        "baseline_wood_iou": baseline["external_segmentation"]["macro"]["wood_iou"],
        "candidate_dbh_mae_cm": candidate["downstream"]["dbh_mae_cm"],
        "candidate_height_mae_m": candidate["downstream"]["height_mae_m"],
        "candidate_measurable_trees": candidate["downstream"]["measurable_trees"],
        "candidate_volume_mape_pct": candidate["downstream"]["volume_mape_pct"],
        "candidate_wood_iou": candidate["external_segmentation"]["macro"]["wood_iou"],
        "checkpoint_sha256": result["checkpoint_sha256"],
        "command": "evaluate",
        "promote": result["verdict"]["promote"],
        "status": "ok",
        "verdict": result["verdict"]["verdict"],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-wan")
    prepare.add_argument("--protocol", required=True)
    prepare.add_argument("--wan-root", required=True)
    prepare.add_argument("--artifact-dir", required=True)
    prepare.add_argument("--manifest-out", required=True)
    prepare.add_argument("--repo-root", required=True)
    prepare.set_defaults(handler=_prepare_wan)

    train = subparsers.add_parser("train")
    train.add_argument("--protocol", required=True)
    train.add_argument("--wan-manifest", required=True)
    train.add_argument("--artifact-dir", required=True)
    train.add_argument("--repo-root", required=True)
    train.set_defaults(handler=_train)

    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--protocol", required=True)
    freeze.add_argument("--wan-manifest", required=True)
    freeze.add_argument("--artifact-dir", required=True)
    freeze.add_argument("--evidence-dir", required=True)
    freeze.add_argument("--repo-root", required=True)
    freeze.set_defaults(handler=_freeze)

    fetch_external = subparsers.add_parser("fetch-external")
    fetch_external.add_argument("--protocol", required=True)
    fetch_external.add_argument("--freeze-manifest", required=True)
    fetch_external.add_argument("--checkpoint", required=True)
    fetch_external.add_argument("--destination", required=True)
    fetch_external.add_argument("--manifest-out", required=True)
    fetch_external.add_argument("--repo-root", required=True)
    fetch_external.set_defaults(handler=_fetch_external)

    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--protocol", required=True)
    evaluate.add_argument("--freeze-manifest", required=True)
    evaluate.add_argument("--checkpoint", required=True)
    evaluate.add_argument("--external-root", required=True)
    evaluate.add_argument("--external-manifest", required=True)
    evaluate.add_argument("--demol-root", required=True)
    evaluate.add_argument("--evidence-dir", required=True)
    evaluate.add_argument("--repo-root", required=True)
    evaluate.set_defaults(handler=_evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        summary = args.handler(args)
    except Exception as exc:
        failure = {
            "command": args.command,
            "error": str(exc),
            "error_type": type(exc).__name__,
            "status": "error",
        }
        if args.command == "evaluate":
            failure["verdict"] = "INVALID_EVIDENCE"
        _summary_line(failure)
        return 1
    _summary_line(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
