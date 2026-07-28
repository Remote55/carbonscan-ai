"""Fail-closed contracts for sealing judge-demo evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import subprocess
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
            {"tree_id": index + 1}
            for index in range(candidate["result"]["total_trees"])
        ],
    }


def write_candidate_artifacts(candidate: dict, candidate_dir: Path) -> None:
    candidate_dir.mkdir(exist_ok=True)
    contents = {
        "input": b"input.ply",
        "result": (json.dumps(valid_result(candidate), sort_keys=True) + "\n").encode(),
        "segmented": b"segmented.ply",
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
    with pytest.raises(ValueError, match="result.json"):
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


def test_seal_finalize_and_check_preserve_analyzed_commit(tmp_path):
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
    check_manifest(repo_root, candidate_dir=candidate_dir)

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


def test_seal_rejects_repository_change_during_staging(tmp_path, monkeypatch):
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


def test_seal_hashes_committed_core_manifest_blob_across_checkout_eol(tmp_path):
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

    with pytest.raises(ValueError, match="symlink|reparse"):
        check_candidate_artifacts(candidate, candidate_dir)


def test_seal_rejects_reparse_public_output_directory(tmp_path, monkeypatch):
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

    with pytest.raises(ValueError, match="symlink|reparse"):
        seal_candidate(candidate_dir, repo_root)
    assert list(external_dir.iterdir()) == []
