"""Integration test for the reproducible tlsep core demo."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_core_demo_runs_twice_and_writes_reproducible_artifacts(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "services" / "ml" / "scripts" / "run_core_demo.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-dir",
            str(tmp_path),
            "--repo-root",
            str(repo_root),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr

    summary = json.loads(
        (tmp_path / "verification-summary.json").read_text(encoding="utf-8")
    )
    assert summary["reproducible"] is True
    assert summary["normalized_result_sha256"][0] == summary["normalized_result_sha256"][1]
    assert summary["segmented_ply_sha256"][0] == summary["segmented_ply_sha256"][1]

    for name in ("result.json", "segmented.ply", "evidence.json", "verification-summary.json"):
        assert (tmp_path / name).is_file()

    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["run"]["backend"] == "tlsep"
    assert evidence["run"]["checkpoint_sha256"] is None
    assert isinstance(evidence["run"]["git_dirty"], bool)
    assert evidence["algorithms"]["species"] == "stub"
    assert evidence["evidence"]["candidate_status"] == "candidate_not_evaluated"
    assert evidence["evidence"]["scope"] == "core_demo_fixture_not_accuracy_benchmark"
