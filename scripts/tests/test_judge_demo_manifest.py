"""Fail-closed contracts for sealing judge-demo evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "judge_demo_manifest.py"
SPEC = importlib.util.spec_from_file_location("judge_demo_manifest", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
judge_demo_manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(judge_demo_manifest)
build_manifest = judge_demo_manifest.build_manifest
check_candidate_artifacts = judge_demo_manifest.check_candidate_artifacts
check_manifest = judge_demo_manifest.check_manifest
finalize_manifest = judge_demo_manifest.finalize_manifest
generate_typescript_identity = judge_demo_manifest.generate_typescript_identity
seal_candidate = judge_demo_manifest.seal_candidate
validate_candidate = judge_demo_manifest.validate_candidate


def valid_candidate() -> dict:
    return {
        "schema_version": 1,
        "reproducible": True,
        "analyzed_commit": "1" * 40,
        "git_dirty": False,
        "dataset": "deterministic_synthetic_plot_seed_42",
        "scope": "deterministic_fixture_not_accuracy_or_credit_validation",
        "source": {
            "tree_sha256": "e" * 64,
            "tracked_files": ["services/ml/pipeline/main.py"],
        },
        "reproducibility": {
            "run_count": 2,
            "result_sha256": ["b" * 64, "b" * 64],
            "segmented_ply_sha256": ["c" * 64, "c" * 64],
        },
        "pipeline": {
            "version": "0.3.0",
            "backend": "tlsep",
            "checkpoint_sha256": None,
            "algorithms": {"species": "stub", "wood_leaf": "tlsep"},
        },
        "result": {
            "input_points": 123,
            "total_trees": 3,
            "total_carbon_kg": 1320.39,
            "total_co2eq_kg": 4841.48,
        },
        "artifacts": {
            "input": {"filename": "input.ply", "sha256": "a" * 64, "size_bytes": 10},
            "result": {"filename": "result.json", "sha256": "b" * 64, "size_bytes": 20},
            "segmented": {
                "filename": "segmented.ply",
                "sha256": "c" * 64,
                "size_bytes": 30,
            },
        },
    }


def valid_result(candidate: dict) -> dict:
    return {
        "metadata": {
            "input_file": "input.ply",
            "git_commit": candidate["analyzed_commit"],
            "git_dirty": False,
            "pipeline_version": candidate["pipeline"]["version"],
            "wood_leaf_backend": candidate["pipeline"]["backend"],
            "checkpoint_sha256": candidate["pipeline"]["checkpoint_sha256"],
            "algorithms": candidate["pipeline"]["algorithms"],
            "n_input_points": candidate["result"]["input_points"],
            "source_tree_sha256": candidate["source"]["tree_sha256"],
        },
        "summary": {
            "total_trees": candidate["result"]["total_trees"],
            "total_carbon_kg": candidate["result"]["total_carbon_kg"],
            "total_co2eq_kg": candidate["result"]["total_co2eq_kg"],
        },
        "diagnostics": {
            "dataset": candidate["dataset"],
            "scope": candidate["scope"],
        },
        "trees": [
            {
                "tree_id": index + 1,
                "species_sci": "Tectona grandis",
                "species_confidence": None,
                "dbh_cm": 20.0,
                "height_m": 10.0,
                "crown_radius_m": None,
                "volume_m3": 0.1,
                "biomass_kg": candidate["result"]["total_carbon_kg"] / 0.47 / 3,
                "carbon_kg": candidate["result"]["total_carbon_kg"] / 3,
                "co2eq_kg": candidate["result"]["total_co2eq_kg"] / 3,
                # These seven are required by _validate_candidate_result, whose
                # comments explain why each one may not be dropped. They were
                # added to that check and not to this fixture, so every test
                # using it failed with "tree semantics are incomplete" — the
                # validator was right and the fixture was stale.
                "co2eq_low_kg": candidate["result"]["total_co2eq_kg"] / 3 * 0.8,
                "co2eq_high_kg": candidate["result"]["total_co2eq_kg"] / 3 * 1.2,
                "uncertainty_basis": "wood density range 400-800 kg/m3",
                "co2eq_volume_route_kg": candidate["result"]["total_co2eq_kg"] / 3 * 1.15,
                "method_disagreement": 0.15,
                "dbh_fit_quality": 0.99,
                "crown_resolved_fraction": 0.42,
                "location": {"x": float(index), "y": 0.0},
                "point_count": 41,
                "wood_leaf_iou": None,
            }
            for index in range(candidate["result"]["total_trees"])
        ],
    }


def minimal_ply(vertex_count: int, *, segmented: bool) -> bytes:
    class_property = "property uchar class\n" if segmented else ""
    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {vertex_count}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        f"{class_property}"
        "end_header\n"
    ).encode("ascii")
    point = struct.pack("<fff", 0.0, 0.0, 0.0)
    body = (point + (b"\x00" if segmented else b"")) * vertex_count
    return header + body


def write_candidate_artifacts(candidate: dict, candidate_dir: Path) -> None:
    candidate_dir.mkdir(exist_ok=True)
    contents = {
        "input": minimal_ply(candidate["result"]["input_points"], segmented=False),
        "result": (json.dumps(valid_result(candidate), sort_keys=True) + "\n").encode(),
        "segmented": minimal_ply(candidate["result"]["input_points"], segmented=True),
    }
    for name, content in contents.items():
        artifact = candidate["artifacts"][name]
        (candidate_dir / artifact["filename"]).write_bytes(content)
        artifact["sha256"] = hashlib.sha256(content).hexdigest()
        artifact["size_bytes"] = len(content)
    candidate["reproducibility"]["result_sha256"] = [
        candidate["artifacts"]["result"]["sha256"]
    ] * 2
    candidate["reproducibility"]["segmented_ply_sha256"] = [
        candidate["artifacts"]["segmented"]["sha256"]
    ] * 2
    (candidate_dir / "candidate.json").write_text(
        json.dumps(candidate), encoding="utf-8"
    )


def init_clean_repo_and_candidate(
    tmp_path: Path, *, autocrlf: bool = False
) -> tuple[Path, Path, dict, str]:
    repo_root = tmp_path / "repo"
    candidate_dir = tmp_path / "candidate"
    core_manifest = repo_root / "docs" / "evidence" / "core_demo_manifest.json"
    core_manifest.parent.mkdir(parents=True)
    core_manifest.write_bytes(b'{"schema_version":"1"}\n')
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    if autocrlf:
        (repo_root / ".gitattributes").write_text(
            "*.json text eol=crlf\n", encoding="ascii"
        )
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=TreeQ Test",
            "-c",
            "user.email=treeq-test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=repo_root,
        check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    candidate = valid_candidate()
    candidate["analyzed_commit"] = commit
    write_candidate_artifacts(candidate, candidate_dir)
    (candidate_dir / "candidate.json").write_text(
        json.dumps(candidate), encoding="utf-8"
    )
    return repo_root, candidate_dir, candidate, commit


def init_manifest_cli_checkout(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "manifest-checkout"
    script_path = repo_root / "scripts" / "judge_demo_manifest.py"
    script_path.parent.mkdir(parents=True)
    shutil.copyfile(MODULE_PATH, script_path)
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=TreeQ Test",
            "-c",
            "user.email=treeq-test@example.invalid",
            "commit",
            "-qm",
            "manifest CLI fixture",
        ],
        cwd=repo_root,
        check=True,
    )
    return repo_root, script_path


def run_manifest_cli(
    script_path: Path, repo_root: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script_path), *arguments],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def allow_independent_reproduction(monkeypatch):
    monkeypatch.setattr(
        judge_demo_manifest,
        "_require_independent_reproduction",
        lambda _candidate, _staged, _repo_root: None,
        raising=False,
    )


def test_cli_repo_root_is_subcommand_scoped_backward_compatible_and_checkout_bound(
    tmp_path,
):
    repo_root, script_path = init_manifest_cli_checkout(tmp_path)

    exact_task_4 = run_manifest_cli(
        script_path,
        repo_root,
        "seal",
        "--repo-root",
        ".",
        "--artifact-dir",
        "missing-candidate",
        "--status",
        "candidate",
    )
    omitted = run_manifest_cli(
        script_path,
        repo_root,
        "seal",
        "--artifact-dir",
        "missing-candidate",
        "--status",
        "candidate",
    )

    assert exact_task_4.returncode == omitted.returncode == 1
    assert "Candidate directory must be a directory" in exact_task_4.stderr
    assert "Candidate directory must be a directory" in omitted.stderr

    for command, required_arguments in (
        ("finalize", ("--backup-video", "missing-video.mp4")),
        ("check", ()),
    ):
        completed = run_manifest_cli(
            script_path,
            repo_root,
            command,
            "--repo-root",
            ".",
            *required_arguments,
        )
        assert completed.returncode == 1
        assert (
            "Documentation manifest must be a contained regular file"
            in completed.stderr
        )

    other_checkout = tmp_path / "other-checkout"
    other_checkout.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=other_checkout, check=True)
    rejected = run_manifest_cli(
        script_path,
        repo_root,
        "check",
        "--repo-root",
        str(other_checkout),
    )

    assert rejected.returncode == 1
    assert "same repository checkout" in rejected.stderr


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [("git_dirty", True, "clean"), ("reproducible", False, "reproducible")],
)
def test_seal_rejects_dirty_or_non_reproducible_candidate(field, value, message):
    candidate = valid_candidate()
    candidate[field] = value
    with pytest.raises(ValueError, match=message):
        validate_candidate(candidate)


def test_manifest_never_uses_layout_fixture_values():
    candidate = valid_candidate()
    manifest = build_manifest(candidate, core_manifest_hash="d" * 64)

    encoded = json.dumps(manifest)
    assert "93135" not in encoded
    assert manifest["result"]["total_co2eq_kg"] == candidate["result"]["total_co2eq_kg"]
    assert manifest["source"]["core_manifest_sha256"] == "d" * 64
    assert manifest["analyzed_commit"] == candidate["analyzed_commit"]
    assert manifest["release"]["status"] == "candidate"
    assert manifest["viewer"] == {"original": True, "wood_leaf": True, "qsm": False}


def test_candidate_check_rejects_changed_artifact_bytes(tmp_path):
    candidate = valid_candidate()
    write_candidate_artifacts(candidate, tmp_path)

    check_candidate_artifacts(candidate, tmp_path)
    (tmp_path / "result.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match=r"result\.json"):
        check_candidate_artifacts(candidate, tmp_path)


def test_candidate_rejects_unproven_or_unpublished_run_hashes():
    candidate = valid_candidate()
    candidate["reproducibility"]["result_sha256"][1] = "d" * 64
    with pytest.raises(ValueError, match="two result runs"):
        validate_candidate(candidate)

    candidate = valid_candidate()
    candidate["artifacts"]["result"]["sha256"] = "d" * 64
    with pytest.raises(ValueError, match="published result"):
        validate_candidate(candidate)


def test_candidate_check_rejects_result_totals_or_provenance_not_in_result(tmp_path):
    candidate = valid_candidate()
    write_candidate_artifacts(candidate, tmp_path)
    candidate["result"]["total_co2eq_kg"] = 999.0
    with pytest.raises(ValueError, match="total_co2eq_kg"):
        check_candidate_artifacts(candidate, tmp_path)

    candidate = valid_candidate()
    other_dir = tmp_path / "other"
    write_candidate_artifacts(candidate, other_dir)
    result_path = other_dir / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["metadata"]["wood_leaf_backend"] = "pointnet"
    result_bytes = (json.dumps(result, sort_keys=True) + "\n").encode()
    result_path.write_bytes(result_bytes)
    result_hash = hashlib.sha256(result_bytes).hexdigest()
    candidate["artifacts"]["result"]["sha256"] = result_hash
    candidate["artifacts"]["result"]["size_bytes"] = len(result_bytes)
    candidate["reproducibility"]["result_sha256"] = [result_hash, result_hash]
    with pytest.raises(ValueError, match="wood_leaf_backend"):
        check_candidate_artifacts(candidate, other_dir)


def test_candidate_check_rejects_incomplete_tree_semantics(tmp_path):
    candidate = valid_candidate()
    write_candidate_artifacts(candidate, tmp_path)
    result_path = tmp_path / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["trees"][0] = {"tree_id": 1}
    result_bytes = (json.dumps(result, sort_keys=True) + "\n").encode()
    result_path.write_bytes(result_bytes)
    result_hash = hashlib.sha256(result_bytes).hexdigest()
    candidate["artifacts"]["result"].update(
        {"sha256": result_hash, "size_bytes": len(result_bytes)}
    )
    candidate["reproducibility"]["result_sha256"] = [result_hash, result_hash]

    with pytest.raises(ValueError, match="tree semantics"):
        check_candidate_artifacts(candidate, tmp_path)


def test_candidate_check_rejects_non_ply_artifact_even_with_matching_hashes(tmp_path):
    candidate = valid_candidate()
    write_candidate_artifacts(candidate, tmp_path)
    invalid = b"not a point cloud"
    input_path = tmp_path / "input.ply"
    input_path.write_bytes(invalid)
    candidate["artifacts"]["input"].update(
        {"sha256": hashlib.sha256(invalid).hexdigest(), "size_bytes": len(invalid)}
    )

    with pytest.raises(ValueError, match="PLY"):
        check_candidate_artifacts(candidate, tmp_path)


@pytest.mark.parametrize("value", [True, -1, math.nan, math.inf, -math.inf])
def test_candidate_rejects_invalid_numeric_facts(value):
    candidate = valid_candidate()
    candidate["result"]["total_carbon_kg"] = value
    with pytest.raises(ValueError, match="total_carbon_kg"):
        validate_candidate(candidate)


def test_manifest_cannot_be_sealed_as_frozen_without_finalize():
    with pytest.raises(ValueError, match="candidate"):
        build_manifest(valid_candidate(), core_manifest_hash="d" * 64, status="frozen")


def test_typescript_identity_hashes_public_manifest_bytes(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(b'{"release":{"status":"candidate"}}\n')
    output_path = tmp_path / "judge-demo-evidence.ts"

    generate_typescript_identity(manifest_path, output_path)

    expected = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    generated = output_path.read_text(encoding="utf-8")
    assert expected in generated
    assert "manifestPath: '/demo/manifest.json'" in generated
    assert "inputPath: '/demo/input.ply'" in generated
    assert "segmentedPath: '/demo/segmented.ply'" in generated
    assert "resultPath: '/demo/result.json'" in generated


def test_seal_finalize_and_check_preserve_analyzed_commit(
    tmp_path, allow_independent_reproduction
):
    repo_root, candidate_dir, candidate, commit = init_clean_repo_and_candidate(
        tmp_path
    )

    seal_candidate(candidate_dir, repo_root, status="candidate")

    docs_manifest = repo_root / "docs" / "evidence" / "judge_demo_manifest.json"
    public_manifest = repo_root / "apps" / "web" / "public" / "demo" / "manifest.json"
    assert docs_manifest.read_bytes() == public_manifest.read_bytes()
    sealed = json.loads(public_manifest.read_text(encoding="utf-8"))
    assert sealed["analyzed_commit"] == commit
    assert (
        sealed["source"]["core_manifest_path"]
        == "docs/evidence/core_demo_manifest.json"
    )
    assert sealed["pipeline"]["dataset_scope"] == {
        "dataset": candidate["dataset"],
        "scope": candidate["scope"],
    }
    checked = check_manifest(repo_root, candidate_dir=candidate_dir)
    assert checked["_check"]["independent_reproduction"] == "unavailable"

    backup_video = tmp_path / "judge-backup.mp4"
    backup_video.write_bytes(b"video evidence")
    finalize_manifest(backup_video, repo_root)

    finalized = json.loads(public_manifest.read_text(encoding="utf-8"))
    assert finalized["analyzed_commit"] == commit
    assert finalized["release"]["status"] == "frozen"
    assert finalized["release"]["backup_video"]["path"] == "judge-backup.mp4"
    assert docs_manifest.read_bytes() == public_manifest.read_bytes()
    check_manifest(repo_root)

    finalized["pipeline"]["backend"] = "pointnet"
    tampered_bytes = (json.dumps(finalized, indent=2, sort_keys=True) + "\n").encode()
    docs_manifest.write_bytes(tampered_bytes)
    public_manifest.write_bytes(tampered_bytes)
    generate_typescript_identity(
        public_manifest,
        repo_root / "apps" / "web" / "src" / "generated" / "judge-demo-evidence.ts",
    )
    with pytest.raises(ValueError, match="pipeline"):
        check_manifest(repo_root)


def test_seal_rejects_repository_change_during_staging(
    tmp_path, monkeypatch, allow_independent_reproduction
):
    repo_root, candidate_dir, _, commit = init_clean_repo_and_candidate(tmp_path)
    states = iter(
        [
            {"commit": commit, "dirty": False},
            {"commit": commit, "dirty": True},
        ]
    )
    monkeypatch.setattr(
        judge_demo_manifest,
        "_repo_state",
        lambda _repo_root: next(states),
        raising=False,
    )

    with pytest.raises(RuntimeError, match="changed"):
        seal_candidate(candidate_dir, repo_root)


def test_check_runs_independent_gate_for_matching_clean_checkout(
    tmp_path, monkeypatch, allow_independent_reproduction
):
    repo_root, candidate_dir, candidate, commit = init_clean_repo_and_candidate(
        tmp_path
    )
    seal_candidate(candidate_dir, repo_root)
    calls = []
    monkeypatch.setattr(
        judge_demo_manifest,
        "_repo_state",
        lambda _repo_root: {"commit": commit, "dirty": False},
    )
    monkeypatch.setattr(
        judge_demo_manifest,
        "_require_independent_reproduction",
        lambda checked_candidate, _staged, _repo_root: calls.append(checked_candidate),
    )

    checked = check_manifest(repo_root, candidate_dir=candidate_dir)

    assert calls == [candidate]
    assert checked["_check"]["independent_reproduction"] == "passed"


def test_seal_hashes_committed_core_manifest_blob_across_checkout_eol(
    tmp_path, allow_independent_reproduction
):
    repo_root, candidate_dir, _, commit = init_clean_repo_and_candidate(
        tmp_path, autocrlf=True
    )
    core_path = repo_root / "docs" / "evidence" / "core_demo_manifest.json"
    core_path.unlink()
    subprocess.run(
        ["git", "checkout", "--", "docs/evidence/core_demo_manifest.json"],
        cwd=repo_root,
        check=True,
    )
    assert b"\r\n" in core_path.read_bytes()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert status == ""

    manifest = seal_candidate(candidate_dir, repo_root)

    blob = subprocess.run(
        ["git", "show", f"{commit}:docs/evidence/core_demo_manifest.json"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout
    assert (
        manifest["source"]["core_manifest_sha256"] == hashlib.sha256(blob).hexdigest()
    )


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="NTFS directory junctions can only be created with Windows mklink",
)
def test_candidate_check_rejects_reparse_directory(tmp_path):
    candidate = valid_candidate()
    external_dir = tmp_path / "private-candidate"
    write_candidate_artifacts(candidate, external_dir)
    candidate_dir = tmp_path / "candidate-link"
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(candidate_dir), str(external_dir)],
        check=True,
        capture_output=True,
        text=True,
    )

    with pytest.raises(ValueError, match=r"symlink|reparse"):
        check_candidate_artifacts(candidate, candidate_dir)


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="NTFS directory junctions can only be created with Windows mklink",
)
def test_seal_rejects_reparse_public_output_directory(
    tmp_path, monkeypatch, allow_independent_reproduction
):
    repo_root, candidate_dir, _, commit = init_clean_repo_and_candidate(tmp_path)
    external_dir = tmp_path / "private-public-output"
    external_dir.mkdir()
    public_parent = repo_root / "apps" / "web" / "public"
    public_parent.mkdir(parents=True)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(public_parent / "demo"), str(external_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    monkeypatch.setattr(
        judge_demo_manifest,
        "_repo_state",
        lambda _repo_root: {"commit": commit, "dirty": False},
    )

    with pytest.raises(ValueError, match=r"symlink|reparse"):
        seal_candidate(candidate_dir, repo_root)
    assert list(external_dir.iterdir()) == []


def test_seal_rejects_self_consistent_semantic_forgery(tmp_path, monkeypatch):
    repo_root, trusted_dir, trusted, _ = init_clean_repo_and_candidate(tmp_path)
    trusted_staged = {
        name: (trusted_dir / artifact["filename"]).read_bytes()
        for name, artifact in trusted["artifacts"].items()
    }
    forged = json.loads(json.dumps(trusted))
    forged["result"]["total_co2eq_kg"] = 999.0
    forged_dir = tmp_path / "forged"
    write_candidate_artifacts(forged, forged_dir)
    monkeypatch.setattr(
        judge_demo_manifest,
        "_generate_independent_candidate",
        lambda _repo_root: (trusted, trusted_staged),
        raising=False,
    )

    with pytest.raises(ValueError, match="independent reproduction"):
        seal_candidate(forged_dir, repo_root)
