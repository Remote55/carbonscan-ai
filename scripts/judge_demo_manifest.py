"""Seal, finalize, and verify deterministic judge-demo artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import stat
import subprocess
import sys
import tempfile
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
    encoded = json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    )
    return f"{encoded}\n".encode()


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON number is not allowed: {value}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _safe_directory(path: str | Path, label: str) -> tuple[Path, Path]:
    raw = Path(path).absolute()
    if _is_reparse_or_symlink(raw):
        raise ValueError(f"{label} cannot be a symlink or reparse point")
    if not raw.is_dir():
        raise ValueError(f"{label} must be a directory")
    return raw, raw.resolve(strict=True)


def _safe_regular_file(root: str | Path, filename: str, label: str) -> Path:
    raw_root, resolved_root = _safe_directory(root, f"{label} directory")
    path = raw_root / filename
    if path.parent != raw_root or _is_reparse_or_symlink(path):
        raise ValueError(f"{label} cannot be a symlink or reparse point")
    if not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    resolved = path.resolve(strict=True)
    if resolved.parent != resolved_root:
        raise ValueError(f"{label} resolves outside its allowed directory")
    return path


def _safe_output_file(repo_root: Path, relative_path: Path, label: str) -> Path:
    resolved_repo = repo_root.resolve(strict=True)
    current = repo_root.absolute()
    for part in relative_path.parent.parts:
        current /= part
        if current.exists() and _is_reparse_or_symlink(current):
            raise ValueError(f"{label} parent cannot be a symlink or reparse point")
    current.mkdir(parents=True, exist_ok=True)
    if not current.resolve(strict=True).is_relative_to(resolved_repo):
        raise ValueError(f"{label} parent resolves outside the repository")
    path = current / relative_path.name
    if _is_reparse_or_symlink(path) or (path.exists() and not path.is_file()):
        raise ValueError(
            f"{label} cannot replace a symlink, reparse point, or non-file"
        )
    return path


def _positive_integer(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"Candidate {name} must be a positive integer")
    return value


def _non_negative_finite_number(value: Any, name: str) -> int | float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"Candidate {name} must be a finite non-negative number")
    return value


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

    source = candidate.get("source")
    if (
        not isinstance(source, dict)
        or set(source) != {"tree_sha256", "tracked_files"}
        or not _is_hex(source["tree_sha256"], 64)
        or not isinstance(source["tracked_files"], list)
        or not source["tracked_files"]
        or source["tracked_files"] != sorted(set(source["tracked_files"]))
        or not all(
            isinstance(path, str) and path.startswith("services/ml/")
            for path in source["tracked_files"]
        )
    ):
        raise ValueError("Candidate source-tree identity is invalid")

    reproducibility = candidate.get("reproducibility")
    if not isinstance(reproducibility, dict) or set(reproducibility) != {
        "run_count",
        "result_sha256",
        "segmented_ply_sha256",
    }:
        raise ValueError("Candidate reproducibility evidence is incomplete")
    if reproducibility["run_count"] != 2 or isinstance(
        reproducibility["run_count"], bool
    ):
        raise ValueError("Candidate reproducibility must record exactly two runs")
    for name in ("result_sha256", "segmented_ply_sha256"):
        hashes = reproducibility[name]
        if (
            not isinstance(hashes, list)
            or len(hashes) != 2
            or not all(_is_hex(value, 64) for value in hashes)
            or hashes[0] != hashes[1]
        ):
            display = (
                "two result runs" if name == "result_sha256" else "two segmented runs"
            )
            raise ValueError(f"Candidate {display} must have equal SHA-256 identities")

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
    _positive_integer(result["input_points"], "input_points")
    _positive_integer(result["total_trees"], "total_trees")
    _non_negative_finite_number(result["total_carbon_kg"], "total_carbon_kg")
    _non_negative_finite_number(result["total_co2eq_kg"], "total_co2eq_kg")

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
            or isinstance(artifact["size_bytes"], bool)
            or artifact["size_bytes"] <= 0
        ):
            raise ValueError(f"Candidate {expected_filename} size is invalid")
    if artifacts["result"]["sha256"] != reproducibility["result_sha256"][0]:
        raise ValueError(
            "Candidate published result hash lacks matching two-run evidence"
        )
    if artifacts["segmented"]["sha256"] != reproducibility["segmented_ply_sha256"][0]:
        raise ValueError(
            "Candidate published segmented hash lacks matching two-run evidence"
        )


def _validate_result_payload(candidate: dict[str, Any], result_bytes: bytes) -> None:
    try:
        payload = json.loads(
            result_bytes.decode("utf-8"), parse_constant=_reject_json_constant
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            "Candidate result.json must contain strict UTF-8 JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("Candidate result.json must contain a JSON object")
    metadata = payload.get("metadata")
    summary = payload.get("summary")
    diagnostics = payload.get("diagnostics")
    trees = payload.get("trees")
    if not all(isinstance(value, dict) for value in (metadata, summary, diagnostics)):
        raise ValueError("Candidate result.json provenance sections are incomplete")
    expected_metadata = {
        "input_file": "input.ply",
        "git_commit": candidate["analyzed_commit"],
        "git_dirty": False,
        "pipeline_version": candidate["pipeline"]["version"],
        "wood_leaf_backend": candidate["pipeline"]["backend"],
        "checkpoint_sha256": candidate["pipeline"]["checkpoint_sha256"],
        "algorithms": candidate["pipeline"]["algorithms"],
        "n_input_points": candidate["result"]["input_points"],
        "source_tree_sha256": candidate["source"]["tree_sha256"],
    }
    for name, expected in expected_metadata.items():
        if metadata.get(name) != expected:
            raise ValueError(
                f"Candidate result metadata {name} does not match candidate"
            )
    expected_summary = {
        "total_trees": candidate["result"]["total_trees"],
        "total_carbon_kg": candidate["result"]["total_carbon_kg"],
        "total_co2eq_kg": candidate["result"]["total_co2eq_kg"],
    }
    for name, expected in expected_summary.items():
        if summary.get(name) != expected:
            raise ValueError(f"Candidate result {name} does not match candidate")
    if diagnostics.get("dataset") != candidate["dataset"]:
        raise ValueError("Candidate result dataset does not match candidate")
    if diagnostics.get("scope") != candidate["scope"]:
        raise ValueError("Candidate result scope does not match candidate")
    if not isinstance(trees, list) or len(trees) != candidate["result"]["total_trees"]:
        raise ValueError("Candidate result tree list does not match total_trees")
    required_tree_fields = {
        "tree_id",
        "species_sci",
        "species_confidence",
        "dbh_cm",
        "height_m",
        "crown_radius_m",
        "volume_m3",
        "biomass_kg",
        "carbon_kg",
        "co2eq_kg",
        # The density bounds and the sentence explaining them are required, not
        # optional. The comparison below is exact set equality, so evidence
        # published from here on cannot quietly drop the caveat and leave a bare
        # co2eq_kg looking like a measured quantity.
        "co2eq_low_kg",
        "co2eq_high_kg",
        "uncertainty_basis",
        # The second model's answer and how far it lands from the first. Also
        # required: publishing one figure while the code computes two, and
        # knows they differ by about 15%, is publishing the narrower story.
        "co2eq_volume_route_kg",
        "method_disagreement",
        "dbh_fit_quality",
        "location",
        "point_count",
        "wood_leaf_iou",
    }
    tree_ids: set[int] = set()
    for tree in trees:
        if not isinstance(tree, dict) or set(tree) != required_tree_fields:
            raise ValueError("Candidate result tree semantics are incomplete")
        tree_id = tree["tree_id"]
        if (
            not isinstance(tree_id, int)
            or isinstance(tree_id, bool)
            or tree_id <= 0
            or tree_id in tree_ids
            or tree["species_sci"] != "Tectona grandis"
            or not isinstance(tree["location"], dict)
            or set(tree["location"]) != {"x", "y"}
        ):
            raise ValueError("Candidate result tree semantics are invalid")
        tree_ids.add(tree_id)
        for name in (
            "dbh_cm",
            "height_m",
            "volume_m3",
            "biomass_kg",
            "carbon_kg",
            "co2eq_kg",
        ):
            value = tree[name]
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(
                    "Candidate result tree semantics contain invalid numbers"
                )
        if tree["dbh_cm"] <= 0 or tree["height_m"] <= 0:
            raise ValueError(
                "Candidate result tree semantics require measurable geometry"
            )
        if (
            not isinstance(tree["point_count"], int)
            or isinstance(tree["point_count"], bool)
            or tree["point_count"] <= 0
        ):
            raise ValueError("Candidate result tree semantics require point counts")
        for coordinate in tree["location"].values():
            if (
                not isinstance(coordinate, (int, float))
                or isinstance(coordinate, bool)
                or not math.isfinite(coordinate)
            ):
                raise ValueError(
                    "Candidate result tree semantics require finite locations"
                )
    if (
        round(sum(tree["carbon_kg"] for tree in trees), 2)
        != candidate["result"]["total_carbon_kg"]
        or round(sum(tree["co2eq_kg"] for tree in trees), 2)
        != candidate["result"]["total_co2eq_kg"]
    ):
        raise ValueError(
            "Candidate result tree semantics do not sum to reported totals"
        )


def _validate_ply_bytes(
    data: bytes, *, expected_vertices: int, segmented: bool
) -> None:
    marker = b"end_header\n"
    header_end = data.find(marker)
    if header_end < 0 or header_end > 4096:
        raise ValueError("Candidate artifact is not a valid deterministic PLY")
    try:
        header = data[:header_end].decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("Candidate PLY header must be ASCII") from exc
    lines = header.splitlines()
    if not lines or lines[0] != "ply" or "format binary_little_endian 1.0" not in lines:
        raise ValueError("Candidate PLY must be binary little-endian")
    vertex_lines = [line for line in lines if line.startswith("element vertex ")]
    try:
        vertex_count = int(vertex_lines[0].split()[-1])
    except (IndexError, ValueError) as exc:
        raise ValueError("Candidate PLY vertex count is invalid") from exc
    has_class = "property uchar class" in lines
    if vertex_count != expected_vertices or has_class != segmented:
        raise ValueError("Candidate PLY semantic contract is invalid")
    record_size = 13 if segmented else 12
    body = data[header_end + len(marker) :]
    if len(body) != expected_vertices * record_size:
        raise ValueError("Candidate PLY body size is invalid")


def _read_candidate_artifacts(
    candidate: dict[str, Any], candidate_dir: str | Path
) -> dict[str, bytes]:
    validate_candidate(candidate)
    raw_dir, _ = _safe_directory(candidate_dir, "Candidate directory")
    expected_files = {"candidate.json", *ARTIFACT_FILENAMES.values()}
    if {path.name for path in raw_dir.iterdir()} != expected_files:
        raise ValueError(
            "Candidate directory must contain exactly four contracted files"
        )
    staged: dict[str, bytes] = {}
    for name, artifact in candidate["artifacts"].items():
        path = _safe_regular_file(
            raw_dir, artifact["filename"], f"Candidate {artifact['filename']}"
        )
        data = path.read_bytes()
        if (
            len(data) != artifact["size_bytes"]
            or _sha256_bytes(data) != artifact["sha256"]
        ):
            raise ValueError(
                f"Candidate artifact bytes changed: {artifact['filename']}"
            )
        staged[name] = data
    _safe_regular_file(raw_dir, "candidate.json", "Candidate candidate.json")
    _validate_ply_bytes(
        staged["input"],
        expected_vertices=candidate["result"]["input_points"],
        segmented=False,
    )
    _validate_ply_bytes(
        staged["segmented"],
        expected_vertices=candidate["result"]["input_points"],
        segmented=True,
    )
    _validate_result_payload(candidate, staged["result"])
    return staged


def check_candidate_artifacts(
    candidate: dict[str, Any], candidate_dir: str | Path
) -> None:
    """Verify candidate bytes, two-run evidence, and result provenance."""
    _read_candidate_artifacts(candidate, candidate_dir)


def _generate_independent_candidate(
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    runner = _safe_repo_file(
        repo_root,
        Path("services/ml/scripts/run_judge_demo.py"),
        "Trusted judge runner",
    )
    with tempfile.TemporaryDirectory(prefix="treeq-judge-reproduce-") as temp_dir:
        output_dir = Path(temp_dir) / "candidate"
        proc = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--output-dir",
                str(output_dir),
                "--repo-root",
                str(repo_root),
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if proc.returncode != 0:
            raise ValueError(
                "Independent reproduction runner failed: " + proc.stderr.strip()
            )
        candidate_path = _safe_regular_file(
            output_dir, "candidate.json", "Independent candidate.json"
        )
        candidate = _load_json(candidate_path)
        staged = _read_candidate_artifacts(candidate, output_dir)
        return candidate, staged


def _require_independent_reproduction(
    candidate: dict[str, Any], staged: dict[str, bytes], repo_root: Path
) -> None:
    reproduced, reproduced_staged = _generate_independent_candidate(repo_root)
    if reproduced != candidate:
        raise ValueError("Candidate facts differ from independent reproduction")
    for name in ARTIFACT_FILENAMES:
        if reproduced_staged[name] != staged[name]:
            raise ValueError(
                f"Candidate {name} bytes differ from independent reproduction"
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
    if status != "candidate":
        raise ValueError(
            "Seal status must be candidate; finalize creates frozen releases"
        )
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


def _repo_state(repo_root: Path) -> dict[str, Any]:
    return {
        "commit": _git_output(repo_root, "rev-parse", "HEAD"),
        "dirty": bool(
            _git_output(repo_root, "status", "--porcelain", "--untracked-files=normal")
        ),
    }


def _git_blob_bytes(repo_root: Path, commit: str, relative_path: Path) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{commit}:{relative_path.as_posix()}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return proc.stdout


def _safe_repo_file(repo_root: Path, relative_path: Path, label: str) -> Path:
    path = repo_root.absolute()
    for part in relative_path.parts:
        path /= part
        if _is_reparse_or_symlink(path):
            raise ValueError(f"{label} cannot be a symlink or reparse point")
    if not path.is_file() or not path.resolve(strict=True).is_relative_to(
        repo_root.resolve(strict=True)
    ):
        raise ValueError(f"{label} must be a contained regular file")
    return path


def _write_manifest_bundle(repo_root: Path, manifest: dict[str, Any]) -> None:
    manifest_bytes = _json_bytes(manifest)
    docs_path = _safe_output_file(
        repo_root, DOCS_MANIFEST_PATH, "Documentation manifest"
    )
    public_path = _safe_output_file(repo_root, PUBLIC_MANIFEST_PATH, "Public manifest")
    docs_path.write_bytes(manifest_bytes)
    public_path.write_bytes(manifest_bytes)
    ts_path = _safe_output_file(repo_root, TYPESCRIPT_PATH, "TypeScript identity")
    ts_path.write_bytes(_typescript_bytes(manifest_bytes))


def seal_candidate(
    artifact_dir: str | Path,
    repo_root: str | Path,
    *,
    status: str = "candidate",
) -> dict[str, Any]:
    """Copy a clean candidate into the public bundle and seal its identities."""
    repo_root = Path(repo_root).resolve(strict=True)
    before = _repo_state(repo_root)
    if before["dirty"]:
        raise ValueError("Repository must be clean before sealing")
    raw_artifact_dir, _ = _safe_directory(artifact_dir, "Candidate directory")
    candidate_path = _safe_regular_file(
        raw_artifact_dir, "candidate.json", "Candidate candidate.json"
    )
    candidate = _load_json(candidate_path)
    staged = _read_candidate_artifacts(candidate, raw_artifact_dir)
    if before["commit"] != candidate["analyzed_commit"]:
        raise ValueError(
            "Candidate analyzed_commit does not match the clean repository HEAD"
        )

    _safe_repo_file(repo_root, CORE_MANIFEST_PATH, "Core manifest")
    core_blob = _git_blob_bytes(repo_root, before["commit"], CORE_MANIFEST_PATH)
    manifest = build_manifest(candidate, _sha256_bytes(core_blob), status=status)
    _require_independent_reproduction(candidate, staged, repo_root)
    after = _repo_state(repo_root)
    if after != before or after["dirty"]:
        raise RuntimeError("Repository changed while staging judge demo evidence")
    for name, filename in ARTIFACT_FILENAMES.items():
        source_bytes = staged[name]
        destination = _safe_output_file(
            repo_root, PUBLIC_DEMO_DIR / filename, f"Public {filename}"
        )
        destination.write_bytes(source_bytes)
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
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value < 0
        ):
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
    if release["status"] == "candidate" and backup is not None:
        raise ValueError("Candidate release cannot include a backup video")
    if release["status"] == "frozen" and backup is None:
        raise ValueError("Frozen release requires a backup video identity")
    if backup is not None:
        if (
            not isinstance(backup, dict)
            or set(backup) != {"path", "sha256", "size_bytes"}
            or not isinstance(backup["path"], str)
            or Path(backup["path"]).name != backup["path"]
            or not _is_hex(backup["sha256"], 64)
            or not isinstance(backup["size_bytes"], int)
            or isinstance(backup["size_bytes"], bool)
            or backup["size_bytes"] <= 0
        ):
            raise ValueError("Public manifest backup video identity is invalid")


def _validate_public_result(manifest: dict[str, Any], result_bytes: bytes) -> int:
    try:
        payload = json.loads(
            result_bytes.decode("utf-8"), parse_constant=_reject_json_constant
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("Public result.json must contain strict UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Public result.json must contain a JSON object")
    metadata = payload.get("metadata")
    summary = payload.get("summary")
    diagnostics = payload.get("diagnostics")
    trees = payload.get("trees")
    if not all(isinstance(value, dict) for value in (metadata, summary, diagnostics)):
        raise ValueError("Public result.json provenance sections are incomplete")
    expected_metadata = {
        "input_file": "input.ply",
        "git_commit": manifest["analyzed_commit"],
        "git_dirty": False,
        "pipeline_version": manifest["pipeline"]["version"],
        "wood_leaf_backend": manifest["pipeline"]["backend"],
        "checkpoint_sha256": None,
    }
    for name, expected in expected_metadata.items():
        if metadata.get(name) != expected:
            raise ValueError(f"Public result metadata {name} is inconsistent")
    if not _is_hex(metadata.get("source_tree_sha256"), 64):
        raise ValueError("Public result source-tree identity is invalid")
    input_points = metadata.get("n_input_points")
    if (
        not isinstance(input_points, int)
        or isinstance(input_points, bool)
        or input_points <= 0
    ):
        raise ValueError("Public result input point count is invalid")
    algorithms = metadata.get("algorithms")
    if (
        not isinstance(algorithms, dict)
        or algorithms.get("species") != manifest["pipeline"]["species"]
        or algorithms.get("wood_leaf") != manifest["pipeline"]["backend"]
    ):
        raise ValueError("Public result algorithms are inconsistent")
    for name, expected in manifest["result"].items():
        if summary.get(name) != expected:
            raise ValueError(f"Public result {name} is inconsistent")
    dataset_scope = manifest["pipeline"]["dataset_scope"]
    if diagnostics.get("dataset") != dataset_scope["dataset"]:
        raise ValueError("Public result dataset is inconsistent")
    if diagnostics.get("scope") != dataset_scope["scope"]:
        raise ValueError("Public result scope is inconsistent")
    if not isinstance(trees, list) or len(trees) != manifest["result"]["total_trees"]:
        raise ValueError("Public result tree list is inconsistent")
    return input_points


def check_manifest(
    repo_root: str | Path,
    *,
    candidate_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Fail closed when committed manifest, artifacts, or generated identity differ."""
    repo_root = Path(repo_root).resolve(strict=True)
    docs_path = _safe_repo_file(repo_root, DOCS_MANIFEST_PATH, "Documentation manifest")
    public_path = _safe_repo_file(repo_root, PUBLIC_MANIFEST_PATH, "Public manifest")
    docs_bytes = docs_path.read_bytes()
    public_bytes = public_path.read_bytes()
    if docs_bytes != public_bytes:
        raise ValueError("Documentation and public manifests are not byte-identical")
    try:
        manifest = json.loads(
            public_bytes.decode("utf-8"), parse_constant=_reject_json_constant
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("Public manifest must contain strict UTF-8 JSON") from exc
    _validate_public_manifest(manifest)

    _safe_repo_file(repo_root, CORE_MANIFEST_PATH, "Core manifest")
    core_bytes = _git_blob_bytes(
        repo_root, manifest["analyzed_commit"], CORE_MANIFEST_PATH
    )
    source = manifest["source"]
    if source != {
        "core_manifest_path": CORE_MANIFEST_PATH.as_posix(),
        "core_manifest_sha256": _sha256_bytes(core_bytes),
    }:
        raise ValueError("Core manifest source identity changed")
    if manifest["viewer"] != {"original": True, "wood_leaf": True, "qsm": False}:
        raise ValueError("Viewer capability declaration is invalid")

    public_artifacts: dict[str, bytes] = {}
    for name, expected_path in ARTIFACT_PATHS.items():
        artifact = manifest["artifacts"].get(name)
        if not isinstance(artifact, dict) or artifact.get("path") != expected_path:
            raise ValueError(f"Public {name} artifact contract is invalid")
        public_artifact = _safe_repo_file(
            repo_root,
            PUBLIC_DEMO_DIR / Path(expected_path).name,
            f"Public {name} artifact",
        )
        data = public_artifact.read_bytes()
        if artifact.get("size_bytes") != len(data) or artifact.get(
            "sha256"
        ) != _sha256_bytes(data):
            raise ValueError(f"Public artifact bytes changed: {expected_path}")
        if name == "result":
            public_artifacts["result"] = data
        else:
            public_artifacts[name] = data
    if "result" not in public_artifacts:
        raise ValueError("Public result.json is missing")
    input_points = _validate_public_result(manifest, public_artifacts["result"])
    _validate_ply_bytes(
        public_artifacts["input"], expected_vertices=input_points, segmented=False
    )
    _validate_ply_bytes(
        public_artifacts["segmented"], expected_vertices=input_points, segmented=True
    )

    ts_bytes = _safe_repo_file(
        repo_root, TYPESCRIPT_PATH, "TypeScript identity"
    ).read_bytes()
    if ts_bytes != _typescript_bytes(public_bytes):
        raise ValueError(
            "Generated TypeScript identity does not match public manifest bytes"
        )

    if candidate_dir is not None:
        raw_candidate_dir, _ = _safe_directory(candidate_dir, "Candidate directory")
        candidate_path = _safe_regular_file(
            raw_candidate_dir, "candidate.json", "Candidate candidate.json"
        )
        candidate = _load_json(candidate_path)
        staged = _read_candidate_artifacts(candidate, raw_candidate_dir)
        expected = build_manifest(candidate, manifest["source"]["core_manifest_sha256"])
        for name in (
            "analyzed_commit",
            "git_dirty",
            "pipeline",
            "source",
            "artifacts",
            "result",
            "viewer",
        ):
            if expected[name] != manifest[name]:
                raise ValueError(f"Candidate {name} differs from the sealed manifest")
        current = _repo_state(repo_root)
        reproduction_status = "unavailable"
        if current == {"commit": candidate["analyzed_commit"], "dirty": False}:
            _require_independent_reproduction(candidate, staged, repo_root)
            reproduction_status = "passed"
        checked = dict(manifest)
        checked["_check"] = {
            "independent_reproduction": reproduction_status,
            "reason": (
                None
                if reproduction_status == "passed"
                else "current checkout is not the clean analyzed commit"
            ),
        }
        return checked
    return manifest


def finalize_manifest(
    backup_video: str | Path, repo_root: str | Path
) -> dict[str, Any]:
    """Freeze an existing checked manifest while preserving its analyzed commit."""
    repo_root = Path(repo_root).resolve(strict=True)
    manifest = check_manifest(repo_root)
    if manifest["release"] != {"status": "candidate", "backup_video": None}:
        raise ValueError("Finalize requires an existing candidate release")
    analyzed_commit = manifest["analyzed_commit"]
    backup_video = Path(backup_video).absolute()
    if _is_reparse_or_symlink(backup_video) or not backup_video.is_file():
        raise ValueError("Finalize requires a real regular backup video file")
    video_bytes = backup_video.read_bytes()
    if not video_bytes:
        raise ValueError("Finalize requires a non-empty backup video identity")
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
    seal.add_argument("--repo-root", type=Path)
    seal.add_argument("--artifact-dir", required=True, type=Path)
    seal.add_argument("--status", choices=["candidate"], default="candidate")
    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--repo-root", type=Path)
    finalize.add_argument("--backup-video", required=True, type=Path)
    check = subparsers.add_parser("check")
    check.add_argument("--repo-root", type=Path)
    check.add_argument("--candidate-dir", type=Path)
    return parser


def _resolve_cli_repo_root(requested_root: Path | None) -> Path:
    script_repo_root = Path(__file__).resolve().parents[1]
    if requested_root is None:
        return script_repo_root
    try:
        resolved_root = requested_root.resolve(strict=True)
    except OSError as exc:
        raise ValueError(
            "--repo-root must identify an existing repository checkout"
        ) from exc
    if resolved_root != script_repo_root:
        raise ValueError(
            "--repo-root must identify the same repository checkout containing "
            "scripts/judge_demo_manifest.py"
        )
    return resolved_root


def cli(argv: list[str] | None = None) -> int:
    """Run the manifest CLI from the repository containing this script."""
    args = _parser().parse_args(argv)
    repo_root = _resolve_cli_repo_root(args.repo_root)
    output: dict[str, Any] = {"status": "ok", "command": args.command}
    if args.command == "seal":
        seal_candidate(args.artifact_dir, repo_root, status=args.status)
    elif args.command == "finalize":
        finalize_manifest(args.backup_video, repo_root)
    else:
        checked = check_manifest(repo_root, candidate_dir=args.candidate_dir)
        if "_check" in checked:
            output["candidate_check"] = checked["_check"]
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
