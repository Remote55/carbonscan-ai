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


class TestThePublishedDemoFiguresAreStillCurrent:
    """core_demo in the manifest reaches CAPABILITY_MATRIX.md and the dashboard.

    Nothing re-derived it. `sync_truth.py` checks that total_carbon_kg is a
    positive number and stops, so on 2026-08-14 the block was published with
    pipeline_version 0.3.0, an analyzed_commit from long before, and totals 1.9%
    off what the code produced, with every check green. That is the defect
    docs/ml/DEMOL_EVIDENCE_CHAIN.md records for the accuracy figures.

    It closes more tightly here than it did there: the core demo is a synthetic
    plot with a fixed seed, so `run_core_demo.py --manifest` runs on CI.
    """

    @staticmethod
    def _evidence(**results):
        base = {
            "results": {"total_trees": 3, "total_carbon_kg": 1.0, "total_co2eq_kg": 2.0},
            "run": {"input_sha256": "a" * 64, "pipeline_version": "9.9.9"},
        }
        base["results"].update(results)
        return base

    @staticmethod
    def _manifest(tmp_path, **core):
        block = {
            "total_trees": 3,
            "total_carbon_kg": 1.0,
            "total_co2eq_kg": 2.0,
            "input_sha256": "a" * 64,
            "pipeline_version": "9.9.9",
        }
        block.update(core)
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps({"core_demo": block}), encoding="utf-8")
        return path

    def test_a_matching_manifest_reports_nothing(self, tmp_path):
        from scripts.run_core_demo import check_against_manifest

        assert check_against_manifest(self._evidence(), self._manifest(tmp_path)) == []

    def test_a_stale_carbon_total_is_reported(self, tmp_path):
        from scripts.run_core_demo import check_against_manifest

        problems = check_against_manifest(
            self._evidence(), self._manifest(tmp_path, total_carbon_kg=1320.39)
        )

        assert len(problems) == 1 and "total_carbon_kg" in problems[0]

    def test_a_stale_pipeline_version_is_reported(self, tmp_path):
        """The field that showed the block was three releases behind."""
        from scripts.run_core_demo import check_against_manifest

        problems = check_against_manifest(
            self._evidence(), self._manifest(tmp_path, pipeline_version="0.3.0")
        )

        assert len(problems) == 1 and "pipeline_version" in problems[0]

    def test_the_per_machine_hashes_are_excluded_on_purpose(self, tmp_path):
        """input_sha256 disagreed between Windows and Linux on this check's very
        first CI run, with the same numpy, seed and results. synthetic.py builds
        coordinates out of np.sin and np.cos, and numpy dispatches those to
        different SIMD kernels per platform, so the values agree to fifteen
        digits and the bytes do not.

        The field stays in the manifest as provenance. Comparing it here would
        fail forever for a reason unrelated to the measurement, and this test
        exists so that re-adding it is a decision rather than an oversight.
        """
        from scripts.run_core_demo import MANIFEST_CHECKED_FIELDS, MANIFEST_PER_MACHINE_FIELDS

        overlap = set(MANIFEST_CHECKED_FIELDS) & set(MANIFEST_PER_MACHINE_FIELDS)

        assert not overlap, (
            f"{sorted(overlap)} is compared across machines and cannot be. "
            "Read the comment beside MANIFEST_PER_MACHINE_FIELDS first"
        )

    def test_every_published_field_is_compared(self, tmp_path):
        """A block is only as current as its least-checked number."""
        from scripts.run_core_demo import MANIFEST_CHECKED_FIELDS, check_against_manifest

        for field in MANIFEST_CHECKED_FIELDS:
            problems = check_against_manifest(
                self._evidence(), self._manifest(tmp_path, **{field: "tampered"})
            )
            assert len(problems) == 1 and field in problems[0], field

    def test_a_missing_field_counts_as_a_disagreement(self, tmp_path):
        """Deleting the number is not a way to make it current."""
        from scripts.run_core_demo import MANIFEST_CHECKED_FIELDS, check_against_manifest

        path = tmp_path / "manifest.json"
        path.write_text(json.dumps({"core_demo": {"total_trees": 3}}), encoding="utf-8")

        assert len(check_against_manifest(self._evidence(), path)) == (
            len(MANIFEST_CHECKED_FIELDS) - 1
        )
