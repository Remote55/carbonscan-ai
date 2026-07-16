"""Tests for the manifest-driven truth synchronizer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.sync_truth import (
    load_manifest,
    render_capability_matrix,
    render_typescript,
    replace_truth_block,
)


def _manifest(tmp_path: Path) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "project": "TreeQ Carbon Platform",
                "baseline": {"backend": "tlsep", "status": "Implemented"},
                "candidate": {
                    "backend": "pointnet",
                    "display_name": "PointNet++",
                    "status": "Experimental",
                    "promoted": False,
                    "promotion_evidence": {
                        "all_passed": False,
                        "failed_criteria": ["independent_real_test"],
                    },
                },
                "validation": {
                    "wan_held_out": {
                        "wood_iou": 0.418,
                        "leaf_iou": 0.808,
                        "mean_iou": 0.613,
                        "accuracy": 0.831,
                    },
                    "demol_65": {
                        "dbh_mae_cm": 1.1673846154,
                        "volume_mape_pct": 18.7650916186,
                    },
                },
                "capabilities": [
                    {
                        "name": "Species classification",
                        "status": "Stub",
                        "implementation": "No learned classifier",
                        "evidence": "services/ml/pipeline/species_classifier.py",
                        "claim": "Not implemented",
                    }
                ],
                "core_demo": {
                    "reproducible": True,
                    "analyzed_commit": "9" * 40,
                    "git_dirty": False,
                    "pipeline_version": "0.3.0",
                    "input_sha256": "1" * 64,
                    "normalized_result_sha256": "2" * 64,
                    "segmented_ply_sha256": "3" * 64,
                    "total_trees": 3,
                    "total_carbon_kg": 1320.39,
                    "total_co2eq_kg": 4841.48,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_manifest_rejects_promoted_pointnet_without_gate(tmp_path: Path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["candidate"]["promoted"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="promotion evidence"):
        load_manifest(path)


def test_manifest_rejects_dirty_core_demo(tmp_path: Path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["core_demo"]["git_dirty"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="clean Git worktree"):
        load_manifest(path)


def test_manifest_rejects_incomplete_core_demo_provenance(tmp_path: Path):
    path = _manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["core_demo"]["input_sha256"]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="core_demo missing required keys"):
        load_manifest(path)


def test_generated_outputs_contain_exact_truth(tmp_path: Path):
    data = load_manifest(_manifest(tmp_path))
    typescript = render_typescript(data)
    matrix = render_capability_matrix(data)
    assert "woodIoU: 0.418" in typescript
    assert "leafIoU: 0.808" in typescript
    assert "dbhMaeCm: 1.1673846154" in typescript
    assert "PointNet++" in matrix
    assert "Experimental" in matrix
    assert "Species classification" in matrix
    assert "Stub" in matrix


def test_truth_block_requires_exactly_one_marker_pair():
    source = (
        "before\n"
        "<!-- TREEQ_TRUTH_START -->\n"
        "old\n"
        "<!-- TREEQ_TRUTH_END -->\n"
        "after\n"
    )
    updated = replace_truth_block(source, "new")
    assert (
        "before\n"
        "<!-- TREEQ_TRUTH_START -->\n"
        "new\n"
        "<!-- TREEQ_TRUTH_END -->\n"
        "after"
    ) in updated

    with pytest.raises(ValueError, match="truth markers"):
        replace_truth_block("no markers", "new")

    duplicate = source + source
    with pytest.raises(ValueError, match="truth markers"):
        replace_truth_block(duplicate, "new")
