"""Seal, finalize, and verify deterministic judge-demo artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

CORE_MANIFEST_PATH = Path("docs/evidence/core_demo_manifest.json")
DOCS_MANIFEST_PATH = Path("docs/evidence/judge_demo_manifest.json")
PUBLIC_DEMO_DIR = Path("apps/web/public/demo")
PUBLIC_MANIFEST_PATH = PUBLIC_DEMO_DIR / "manifest.json"
TYPESCRIPT_PATH = Path("apps/web/src/generated/judge-demo-evidence.ts")

ARTIFACT_PATHS = {
    "input": "/demo/input.ply",
    "result": "/demo/result.json",
    "segmented": "/demo/segmented.ply",
}
ARTIFACT_FILENAMES = {name: Path(path).name for name, path in ARTIFACT_PATHS.items()}
ALLOWED_RELEASE_STATUSES = {"candidate", "frozen"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_hex(value: Any, length: int) -> bool:
    if not isinstance(value, str) or len(value) != length:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _json_bytes(payload: dict[str, Any]) -> bytes:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    return f"{encoded}\n".encode()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def validate_candidate(candidate: dict[str, Any]) -> None:
    """Reject candidates that cannot prove a clean, reproducible tlsep run."""
    if candidate.get("schema_version") != 1:
        raise ValueError("Candidate schema_version must be 1")
    if candidate.get("reproducible") is not True:
        raise ValueError("Candidate must be reproducible across two runs")
    if candidate.get("git_dirty") is not False:
        raise ValueError("Candidate must come from a clean analyzed worktree")
    if not _is_hex(candidate.get("analyzed_commit"), 40):
        raise ValueError("Candidate analyzed_commit must be a full Git SHA")
    if candidate.get("dataset") != "deterministic_synthetic_plot_seed_42":
        raise ValueError("Candidate dataset does not identify the reviewed fixture")
    if (
        candidate.get("scope")
        != "deterministic_fixture_not_accuracy_or_credit_validation"
    ):
        raise ValueError(
            "Candidate scope does not match the deterministic fixture contract"
        )

    pipeline = candidate.get("pipeline")
    if not isinstance(pipeline, dict) or pipeline.get("backend") != "tlsep":
        raise ValueError("Candidate pipeline backend must be tlsep")
    if pipeline.get("checkpoint_sha256") is not None:
        raise ValueError("tlsep candidate must not claim a checkpoint")
    algorithms = pipeline.get("algorithms")
    if not isinstance(algorithms, dict) or algorithms.get("species") != "stub":
        raise ValueError("Candidate must report species as stub")
    if algorithms.get("wood_leaf") != "tlsep":
        raise ValueError("Candidate algorithms must report tlsep wood/leaf separation")
    if not isinstance(pipeline.get("version"), str) or not pipeline["version"]:
        raise ValueError("Candidate pipeline version is required")

    result = candidate.get("result")
    required_result = (
        "input_points",
        "total_trees",
        "total_carbon_kg",
        "total_co2eq_kg",
    )
    if not isinstance(result, dict) or any(
        key not in result for key in required_result
    ):
        raise ValueError("Candidate result totals are incomplete")
    if not isinstance(result["total_trees"], int) or result["total_trees"] < 0:
        raise ValueError("Candidate total_trees must be a non-negative integer")

    artifacts = candidate.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(ARTIFACT_FILENAMES):
        raise ValueError(
            "Candidate artifacts must contain input, result, and segmented"
        )
    for name, expected_filename in ARTIFACT_FILENAMES.items():
        artifact = artifacts[name]
        if (
            not isinstance(artifact, dict)
            or artifact.get("filename") != expected_filename
        ):
            raise ValueError(f"Candidate {name} artifact filename is invalid")
        if not _is_hex(artifact.get("sha256"), 64):
            raise ValueError(f"Candidate {expected_filename} SHA-256 is invalid")
        if (
            not isinstance(artifact.get("size_bytes"), int)
            or artifact["size_bytes"] <= 0
        ):
            raise ValueError(f"Candidate {expected_filename} size is invalid")


def check_candidate_artifacts(
    candidate: dict[str, Any], candidate_dir: str | Path
) -> None:
    """Verify candidate file bytes against the candidate's recorded identities."""
    validate_candidate(candidate)
    candidate_dir = Path(candidate_dir)
    for artifact in candidate["artifacts"].values():
        path = candidate_dir / artifact["filename"]
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ValueError(
                f"Cannot read candidate artifact {artifact['filename']}"
            ) from exc
        if (
            len(data) != artifact["size_bytes"]
            or _sha256_bytes(data) != artifact["sha256"]
        ):
            raise ValueError(
                f"Candidate artifact bytes changed: {artifact['filename']}"
            )


def build_manifest(
    candidate: dict[str, Any],
    core_manifest_hash: str,
    *,
    status: str = "candidate",
) -> dict[str, Any]:
    """Build the stable public schema only from validated candidate facts."""
    validate_candidate(candidate)
    if not _is_hex(core_manifest_hash, 64):
        raise ValueError("Core manifest SHA-256 is invalid")
    if status not in ALLOWED_RELEASE_STATUSES:
        raise ValueError("Release status must be candidate or frozen")
    artifacts = {
        name: {
            "path": ARTIFACT_PATHS[name],
            "sha256": candidate["artifacts"][name]["sha256"],
            "size_bytes": candidate["artifacts"][name]["size_bytes"],
        }
        for name in ARTIFACT_PATHS
    }
    return {
        "schema_version": 1,
        "analyzed_commit": candidate["analyzed_commit"],
        "git_dirty": False,
        "pipeline": {
            "version": candidate["pipeline"]["version"],
            "backend": candidate["pipeline"]["backend"],
            "species": candidate["pipeline"]["algorithms"]["species"],
            "dataset_scope": {
                "dataset": candidate["dataset"],
                "scope": candidate["scope"],
            },
        },
        "source": {
            "core_manifest_path": CORE_MANIFEST_PATH.as_posix(),
            "core_manifest_sha256": core_manifest_hash,
        },
        "artifacts": artifacts,
        "result": {
            "total_trees": candidate["result"]["total_trees"],
            "total_carbon_kg": candidate["result"]["total_carbon_kg"],
            "total_co2eq_kg": candidate["result"]["total_co2eq_kg"],
        },
        "viewer": {"original": True, "wood_leaf": True, "qsm": False},
        "release": {"status": status, "backup_video": None},
    }


def _typescript_bytes(manifest_bytes: bytes) -> bytes:
    manifest_hash = _sha256_bytes(manifest_bytes)
    return (
        "// Generated by scripts/judge_demo_manifest.py; do not edit.\n"
        "export interface JudgeDemoEvidenceIdentity {\n"
        "  manifestSha256: string;\n"
        "  manifestPath: '/demo/manifest.json';\n"
        "  inputPath: '/demo/input.ply';\n"
        "  segmentedPath: '/demo/segmented.ply';\n"
        "  resultPath: '/demo/result.json';\n"
        "}\n\n"
        "export const JUDGE_DEMO_EVIDENCE: JudgeDemoEvidenceIdentity = {\n"
        f"  manifestSha256: '{manifest_hash}',\n"
        "  manifestPath: '/demo/manifest.json',\n"
        "  inputPath: '/demo/input.ply',\n"
        "  segmentedPath: '/demo/segmented.ply',\n"
        "  resultPath: '/demo/result.json',\n"
        "};\n"
    ).encode()


def generate_typescript_identity(
    manifest_path: str | Path, output_path: str | Path
) -> None:
    """Generate the web identity constant from the exact public manifest bytes."""
    manifest_bytes = Path(manifest_path).read_bytes()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_typescript_bytes(manifest_bytes))


def _git_output(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _write_manifest_bundle(repo_root: Path, manifest: dict[str, Any]) -> None:
    manifest_bytes = _json_bytes(manifest)
    docs_path = repo_root / DOCS_MANIFEST_PATH
    public_path = repo_root / PUBLIC_MANIFEST_PATH
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.write_bytes(manifest_bytes)
    public_path.write_bytes(manifest_bytes)
    ts_path = repo_root / TYPESCRIPT_PATH
    ts_path.parent.mkdir(parents=True, exist_ok=True)
    ts_path.write_bytes(_typescript_bytes(manifest_bytes))


def seal_candidate(
    artifact_dir: str | Path,
    repo_root: str | Path,
    *,
    status: str = "candidate",
) -> dict[str, Any]:
    """Copy a clean candidate into the public bundle and seal its identities."""
    artifact_dir = Path(artifact_dir).resolve()
    repo_root = Path(repo_root).resolve()
    candidate = _load_json(artifact_dir / "candidate.json")
    check_candidate_artifacts(candidate, artifact_dir)
    if _git_output(repo_root, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("Repository must be clean before sealing")
    if _git_output(repo_root, "rev-parse", "HEAD") != candidate["analyzed_commit"]:
        raise ValueError(
            "Candidate analyzed_commit does not match the clean repository HEAD"
        )

    core_bytes = (repo_root / CORE_MANIFEST_PATH).read_bytes()
    manifest = build_manifest(candidate, _sha256_bytes(core_bytes), status=status)
    public_dir = repo_root / PUBLIC_DEMO_DIR
    public_dir.mkdir(parents=True, exist_ok=True)
    for name, filename in ARTIFACT_FILENAMES.items():
        source_bytes = (artifact_dir / filename).read_bytes()
        (public_dir / filename).write_bytes(source_bytes)
        if _sha256_bytes(source_bytes) != manifest["artifacts"][name]["sha256"]:
            raise ValueError(f"Copied artifact hash mismatch: {filename}")
    _write_manifest_bundle(repo_root, manifest)
    return manifest


def _validate_public_manifest(manifest: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "analyzed_commit",
        "git_dirty",
        "pipeline",
        "source",
        "artifacts",
        "result",
        "viewer",
        "release",
    }
    if set(manifest) != required or manifest.get("schema_version") != 1:
        raise ValueError("Public manifest schema is invalid")
    if (
        not _is_hex(manifest.get("analyzed_commit"), 40)
        or manifest.get("git_dirty") is not False
    ):
        raise ValueError("Public manifest analyzed commit identity is invalid")
    pipeline = manifest.get("pipeline")
    if (
        not isinstance(pipeline, dict)
        or set(pipeline) != {"version", "backend", "species", "dataset_scope"}
        or not isinstance(pipeline["version"], str)
        or not pipeline["version"]
        or pipeline["backend"] != "tlsep"
        or pipeline["species"] != "stub"
        or pipeline["dataset_scope"]
        != {
            "dataset": "deterministic_synthetic_plot_seed_42",
            "scope": "deterministic_fixture_not_accuracy_or_credit_validation",
        }
    ):
        raise ValueError("Public manifest pipeline contract is invalid")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(ARTIFACT_PATHS):
        raise ValueError("Public manifest artifacts contract is invalid")
    for artifact in artifacts.values():
        if not isinstance(artifact, dict) or set(artifact) != {
            "path",
            "sha256",
            "size_bytes",
        }:
            raise ValueError("Public manifest artifact identity is invalid")
    result = manifest.get("result")
    if not isinstance(result, dict) or set(result) != {
        "total_trees",
        "total_carbon_kg",
        "total_co2eq_kg",
    }:
        raise ValueError("Public manifest result contract is invalid")
    if (
        not isinstance(result["total_trees"], int)
        or isinstance(result["total_trees"], bool)
        or result["total_trees"] <= 0
    ):
        raise ValueError("Public manifest tree count is invalid")
    for name in ("total_carbon_kg", "total_co2eq_kg"):
        value = result[name]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise ValueError(f"Public manifest {name} is invalid")
    if manifest.get("viewer") != {"original": True, "wood_leaf": True, "qsm": False}:
        raise ValueError("Public manifest viewer capabilities are invalid")
    release = manifest.get("release")
    if (
        not isinstance(release, dict)
        or set(release) != {"status", "backup_video"}
        or release.get("status") not in ALLOWED_RELEASE_STATUSES
    ):
        raise ValueError("Public manifest release status is invalid")
    backup = release.get("backup_video")
    if backup is not None:
        if (
            not isinstance(backup, dict)
            or set(backup) != {"path", "sha256", "size_bytes"}
            or not isinstance(backup["path"], str)
            or Path(backup["path"]).name != backup["path"]
            or not _is_hex(backup["sha256"], 64)
            or not isinstance(backup["size_bytes"], int)
            or backup["size_bytes"] <= 0
        ):
            raise ValueError("Public manifest backup video identity is invalid")


def check_manifest(
    repo_root: str | Path,
    *,
    candidate_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Fail closed when committed manifest, artifacts, or generated identity differ."""
    repo_root = Path(repo_root).resolve()
    docs_bytes = (repo_root / DOCS_MANIFEST_PATH).read_bytes()
    public_bytes = (repo_root / PUBLIC_MANIFEST_PATH).read_bytes()
    if docs_bytes != public_bytes:
        raise ValueError("Documentation and public manifests are not byte-identical")
    manifest = json.loads(public_bytes.decode("utf-8"))
    _validate_public_manifest(manifest)

    core_bytes = (repo_root / CORE_MANIFEST_PATH).read_bytes()
    source = manifest["source"]
    if source != {
        "core_manifest_path": CORE_MANIFEST_PATH.as_posix(),
        "core_manifest_sha256": _sha256_bytes(core_bytes),
    }:
        raise ValueError("Core manifest source identity changed")
    if manifest["viewer"] != {"original": True, "wood_leaf": True, "qsm": False}:
        raise ValueError("Viewer capability declaration is invalid")

    for name, expected_path in ARTIFACT_PATHS.items():
        artifact = manifest["artifacts"].get(name)
        if not isinstance(artifact, dict) or artifact.get("path") != expected_path:
            raise ValueError(f"Public {name} artifact contract is invalid")
        public_artifact = repo_root / PUBLIC_DEMO_DIR / Path(expected_path).name
        data = public_artifact.read_bytes()
        if artifact.get("size_bytes") != len(data) or artifact.get(
            "sha256"
        ) != _sha256_bytes(data):
            raise ValueError(f"Public artifact bytes changed: {expected_path}")

    ts_bytes = (repo_root / TYPESCRIPT_PATH).read_bytes()
    if ts_bytes != _typescript_bytes(public_bytes):
        raise ValueError(
            "Generated TypeScript identity does not match public manifest bytes"
        )

    if candidate_dir is not None:
        candidate_dir = Path(candidate_dir)
        candidate = _load_json(candidate_dir / "candidate.json")
        check_candidate_artifacts(candidate, candidate_dir)
        if candidate["analyzed_commit"] != manifest["analyzed_commit"]:
            raise ValueError(
                "Candidate analyzed_commit differs from the sealed manifest"
            )
        for name in ARTIFACT_PATHS:
            if (
                candidate["artifacts"][name]["sha256"]
                != manifest["artifacts"][name]["sha256"]
            ):
                raise ValueError(f"Candidate {name} differs from the sealed manifest")
    return manifest


def finalize_manifest(
    backup_video: str | Path, repo_root: str | Path
) -> dict[str, Any]:
    """Freeze an existing checked manifest while preserving its analyzed commit."""
    repo_root = Path(repo_root).resolve()
    manifest = check_manifest(repo_root)
    analyzed_commit = manifest["analyzed_commit"]
    backup_video = Path(backup_video)
    video_bytes = backup_video.read_bytes()
    manifest["release"] = {
        "status": "frozen",
        "backup_video": {
            "path": backup_video.name,
            "sha256": _sha256_bytes(video_bytes),
            "size_bytes": len(video_bytes),
        },
    }
    if manifest["analyzed_commit"] != analyzed_commit:
        raise ValueError("Finalize cannot change the analyzed commit")
    _write_manifest_bundle(repo_root, manifest)
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    seal = subparsers.add_parser("seal")
    seal.add_argument("--artifact-dir", required=True, type=Path)
    seal.add_argument(
        "--status", choices=sorted(ALLOWED_RELEASE_STATUSES), default="candidate"
    )
    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--backup-video", required=True, type=Path)
    check = subparsers.add_parser("check")
    check.add_argument("--candidate-dir", type=Path)
    return parser


def cli(argv: list[str] | None = None) -> int:
    """Run the manifest CLI from the repository containing this script."""
    args = _parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    if args.command == "seal":
        seal_candidate(args.artifact_dir, repo_root, status=args.status)
    elif args.command == "finalize":
        finalize_manifest(args.backup_video, repo_root)
    else:
        check_manifest(repo_root, candidate_dir=args.candidate_dir)
    print(json.dumps({"status": "ok", "command": args.command}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
