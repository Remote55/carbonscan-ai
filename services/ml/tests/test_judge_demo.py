"""Integration contract for deterministic judge-demo artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from services.ml.scripts import run_judge_demo as judge_runner

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def clean_repo_state(monkeypatch):
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setattr(
        judge_runner,
        "_repo_state",
        lambda _repo_root: {"commit": commit, "dirty": False},
        raising=False,
    )


def test_judge_demo_is_reproducible_and_path_free(tmp_path, clean_repo_state):
    summary = judge_runner.run_judge_demo(tmp_path, REPO_ROOT)

    assert summary["reproducible"] is True
    assert summary["result_sha256"][0] == summary["result_sha256"][1]
    assert summary["segmented_ply_sha256"][0] == summary["segmented_ply_sha256"][1]
    result_text = (tmp_path / "result.json").read_text(encoding="utf-8")
    assert str(tmp_path) not in result_text


def test_judge_demo_candidate_records_fixture_scope_and_real_artifacts(tmp_path, clean_repo_state):
    judge_runner.run_judge_demo(tmp_path, REPO_ROOT)

    candidate = json.loads((tmp_path / "candidate.json").read_text(encoding="utf-8"))
    assert candidate["dataset"] == "deterministic_synthetic_plot_seed_42"
    assert candidate["scope"] == "deterministic_fixture_not_accuracy_or_credit_validation"
    assert candidate["pipeline"]["backend"] == "tlsep"
    assert candidate["pipeline"]["checkpoint_sha256"] is None
    assert candidate["pipeline"]["algorithms"]["species"] == "stub"
    assert candidate["result"]["total_trees"] > 0
    assert candidate["result"]["total_co2eq_kg"] != 93135
    evidence = candidate["reproducibility"]
    assert evidence["run_count"] == 2
    assert evidence["result_sha256"][0] == evidence["result_sha256"][1]
    assert evidence["segmented_ply_sha256"][0] == evidence["segmented_ply_sha256"][1]
    assert candidate["artifacts"]["result"]["sha256"] == evidence["result_sha256"][0]
    assert candidate["artifacts"]["segmented"]["sha256"] == evidence["segmented_ply_sha256"][0]
    assert set(candidate["artifacts"]) == {"input", "result", "segmented"}
    for artifact in candidate["artifacts"].values():
        path = tmp_path / artifact["filename"]
        assert path.is_file()
        assert artifact["size_bytes"] == path.stat().st_size
        assert len(artifact["sha256"]) == 64
    assert {path.name for path in tmp_path.iterdir()} == {
        "input.ply",
        "result.json",
        "segmented.ply",
        "candidate.json",
    }


def test_judge_demo_rejects_non_empty_output_directory(tmp_path):
    (tmp_path / "stale.txt").write_text("stale", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        judge_runner.run_judge_demo(tmp_path, REPO_ROOT)


def test_judge_demo_rejects_provenance_from_another_checkout(tmp_path):
    other_checkout = tmp_path / "other-checkout"
    other_checkout.mkdir()

    with pytest.raises(ValueError, match="checkout"):
        judge_runner.run_judge_demo(tmp_path / "candidate", other_checkout)


def test_judge_demo_rejects_repository_change_across_analysis(tmp_path, monkeypatch):
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    states = iter(
        [
            {"commit": commit, "dirty": False},
            {"commit": commit, "dirty": True},
        ]
    )
    monkeypatch.setattr(judge_runner, "_repo_state", lambda _repo_root: next(states))

    with pytest.raises(RuntimeError, match="changed"):
        judge_runner.run_judge_demo(tmp_path, REPO_ROOT)


def test_judge_demo_cli_uses_pipeline_from_its_own_checkout(tmp_path):
    script = REPO_ROOT / "services" / "ml" / "scripts" / "run_judge_demo.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--help",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert proc.returncode == 0, proc.stderr
    assert "--output-dir" in proc.stdout
