"""Integration contract for deterministic judge-demo artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from services.ml.scripts.run_judge_demo import run_judge_demo

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_judge_demo_is_reproducible_and_path_free(tmp_path):
    summary = run_judge_demo(tmp_path, REPO_ROOT)

    assert summary["reproducible"] is True
    assert summary["result_sha256"][0] == summary["result_sha256"][1]
    assert summary["segmented_ply_sha256"][0] == summary["segmented_ply_sha256"][1]
    result_text = (tmp_path / "result.json").read_text(encoding="utf-8")
    assert str(tmp_path) not in result_text


def test_judge_demo_candidate_records_fixture_scope_and_real_artifacts(tmp_path):
    run_judge_demo(tmp_path, REPO_ROOT)

    candidate = json.loads((tmp_path / "candidate.json").read_text(encoding="utf-8"))
    assert candidate["dataset"] == "deterministic_synthetic_plot_seed_42"
    assert candidate["scope"] == "deterministic_fixture_not_accuracy_or_credit_validation"
    assert candidate["pipeline"]["backend"] == "tlsep"
    assert candidate["pipeline"]["checkpoint_sha256"] is None
    assert candidate["pipeline"]["algorithms"]["species"] == "stub"
    assert candidate["result"]["total_trees"] > 0
    assert candidate["result"]["total_co2eq_kg"] != 93135
    assert set(candidate["artifacts"]) == {"input", "result", "segmented"}
    for artifact in candidate["artifacts"].values():
        path = tmp_path / artifact["filename"]
        assert path.is_file()
        assert artifact["size_bytes"] == path.stat().st_size
        assert len(artifact["sha256"]) == 64


def test_judge_demo_cli_uses_pipeline_from_its_own_checkout(tmp_path):
    script = REPO_ROOT / "services" / "ml" / "scripts" / "run_judge_demo.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-dir",
            str(tmp_path),
            "--repo-root",
            str(REPO_ROOT),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary["reproducible"] is True
