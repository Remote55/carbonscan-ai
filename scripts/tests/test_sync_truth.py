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

CURRENT_CLAIM_DOCS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/PROJECT_SPEC.md"),
    Path("docs/CAPABILITY_MATRIX.md"),
    Path("docs/ml/PIPELINE.md"),
    Path("docs/ml/WOODLEAF_RESULTS.md"),
)

STATUS_BANNER_DOCS = (
    Path("docs/AI_AGENT_CONTEXT.md"),
    Path("docs/SESSION_HANDOFF.md"),
    Path("docs/ARCHITECTURE.md"),
    Path("docs/API.md"),
    Path("docs/DEPLOYMENT.md"),
    Path("docs/DEVELOPMENT_PLAN.md"),
    Path("docs/P1_SPRINT_PLAN.md"),
    Path("docs/DATASET_REQUEST.md"),
    Path("docs/ROADMAP.md"),
    Path("docs/learning/README.md"),
    Path("docs/decisions/README.md"),
    Path("proposal/outline.md"),
    Path("docs/proposal/DATASET_SECTION.md"),
    Path("docs/proposal/SYSTEM_OVERVIEW.md"),
    Path("proposal/5-questions-answers.md"),
    Path("services/api/README.md"),
    Path("services/ml/README.md"),
    Path("apps/web/README.md"),
    Path("apps/mobile/README.md"),
)

WAN_DEVELOPMENT_DOCS = (
    Path("docs/ml/FINETUNE_REALDATA.md"),
    Path("docs/ml/WOODLEAF_RESULTS.md"),
    Path("docs/ml/PIPELINE.md"),
)

CONTROLLED_WAN_METRIC_DOCS = (
    Path("docs/ml/WOODLEAF_RESULTS.md"),
    Path("docs/ml/PIPELINE.md"),
)


def _without_generated_truth_blocks(text: str) -> str:
    """Return prose that authors, rather than sync_truth, control."""
    start = "<!-- TREEQ_TRUTH_START -->"
    end = "<!-- TREEQ_TRUTH_END -->"
    while start in text:
        block_end = text.index(end, text.index(start)) + len(end)
        text = text[: text.index(start)] + text[block_end:]
    return text


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


def test_ml_ci_does_not_swallow_test_failures():
    workflow = Path(".github/workflows/ci-ml.yml").read_text(encoding="utf-8")
    assert "pytest tests/ -v --tb=short || true" not in workflow
    assert "scripts/run_core_demo.py" in workflow
    assert "scripts/sync_truth.py --check" in workflow
    assert "python-docx" in workflow
    assert "python -m pytest scripts/tests/" in workflow
    assert workflow.count('"docs/evidence/pointnet_independent_eval/**"') == 2
    assert "ruff check pipeline/ photogrammetry/ training/" in workflow


def test_current_claim_documents_share_exact_evidence():
    texts = {path: path.read_text(encoding="utf-8") for path in CURRENT_CLAIM_DOCS}
    combined = "\n".join(texts.values())

    for path, text in texts.items():
        assert "tlsep" in text, path
        assert "PointNet++" in text, path
    for exact in (
        "0.418",
        "0.808",
        "0.613",
        "0.831",
        "1.1673846154",
        "0.5446153846",
        "18.7650916186",
    ):
        assert exact in combined

    assert "wood IoU = 0.42" not in combined
    assert "PointNet++ เป็น production default" not in combined


@pytest.mark.parametrize("path", WAN_DEVELOPMENT_DOCS)
def test_wan_development_prose_states_split_limits(path: Path):
    prose = " ".join(
        _without_generated_truth_blocks(path.read_text(encoding="utf-8")).split()
    ).lower()

    for fact in (
        "spatially separated development split",
        "2.5 m excluded band",
        "native tree ids are unavailable",
        "same dev loader selected the epoch",
    ):
        assert fact in prose, (path, fact)

    for stale_claim in (
        "leakage-free held-out",
        "train/test never share a tree",
        "no tree leaks across the split",
        "unseen trees",
        "honest number to report",
    ):
        assert stale_claim not in prose, (path, stale_claim)


def test_wan_converter_legacy_test_names_are_disclosed():
    text = Path("docs/ml/FINETUNE_REALDATA.md").read_text(encoding="utf-8").lower()
    assert "--out-test" in text
    assert "wan_test.npz" in text
    assert "legacy names for the development/validation split" in text


@pytest.mark.parametrize("path", CONTROLLED_WAN_METRIC_DOCS)
def test_controlled_wan_documents_retain_exact_recorded_metrics(path: Path):
    text = path.read_text(encoding="utf-8")
    for metric in ("0.418", "0.808", "0.613", "0.831"):
        assert metric in text, (path, metric)


def test_g3_is_confounded_historical_comparison_not_promotion_evidence():
    source = Path("services/ml/notebooks/experiment_g3_pointnet_volume.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "confounded historical experiment" in source
    assert "not promotion evidence" in source
    assert "both segmentation and volume method changed" in lowered
    assert "within-script historical comparison only" in lowered
    assert "not an adoption or promotion decision" in lowered
    assert "adopt sectional" not in lowered


@pytest.mark.parametrize("path", STATUS_BANNER_DOCS)
def test_mixed_or_historical_documents_have_status_banner(path: Path):
    opening = "\n".join(path.read_text(encoding="utf-8").splitlines()[:15])
    assert "[!CAUTION]" in opening or "[!NOTE]" in opening
    status_words = ("current", "historical", "target", "superseded", "archived")
    assert "ปัจจุบัน" in opening or any(word in opening.lower() for word in status_words)


def test_active_web_package_uses_current_product_name():
    package = json.loads(Path("apps/web/package.json").read_text(encoding="utf-8"))

    assert package["description"] == "TreeQ Carbon Platform — Web Dashboard (Next.js 14)"


def test_mobile_ci_uses_flutter_version_supported_by_app():
    workflow = Path(".github/workflows/ci-mobile.yml").read_text(encoding="utf-8")
    pubspec = Path("apps/mobile/pubspec.yaml").read_text(encoding="utf-8")

    assert 'FLUTTER_VERSION: "3.44.0"' in workflow
    assert 'flutter: ">=3.44.0"' in pubspec
