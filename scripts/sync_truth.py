"""Generate and verify user-facing truth from one reviewed evidence manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TRUTH_START = "<!-- TREEQ_TRUTH_START -->"
TRUTH_END = "<!-- TREEQ_TRUTH_END -->"
VALID_STATUSES = {"Implemented", "Experimental", "Stub", "Planned"}
CONTROLLED_DOCS = (
    Path("docs/PROJECT_SPEC.md"),
    Path("docs/ml/PIPELINE.md"),
    Path("docs/ml/WOODLEAF_RESULTS.md"),
)

EXPECTED_WAN = {
    "wood_iou": 0.418,
    "leaf_iou": 0.808,
    "mean_iou": 0.613,
    "accuracy": 0.831,
}


def _require_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise ValueError(f"{label} missing required keys: {missing}")


def _require_sha256(value: Any, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a 64-character SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load and validate the reviewed truth manifest."""
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    _require_keys(
        manifest,
        {
            "schema_version",
            "project",
            "baseline",
            "candidate",
            "validation",
            "capabilities",
            "core_demo",
        },
        "manifest",
    )
    if manifest["schema_version"] != "1":
        raise ValueError("unsupported manifest schema_version")
    if manifest["project"] != "TreeQ Carbon Platform":
        raise ValueError("project name must be TreeQ Carbon Platform")

    baseline = manifest["baseline"]
    if baseline != {"backend": "tlsep", "status": "Implemented"}:
        raise ValueError("baseline must be tlsep with Implemented status")

    candidate = manifest["candidate"]
    _require_keys(
        candidate,
        {
            "backend",
            "display_name",
            "status",
            "promoted",
            "promotion_evidence",
        },
        "candidate",
    )
    if candidate["backend"] != "pointnet" or candidate["display_name"] != "PointNet++":
        raise ValueError("candidate must identify the PointNet++ backend")
    if candidate["status"] not in VALID_STATUSES:
        raise ValueError("candidate has an invalid status")
    promotion = candidate["promotion_evidence"]
    _require_keys(promotion, {"all_passed", "failed_criteria"}, "promotion evidence")
    if candidate["promoted"] and (
        not promotion["all_passed"] or promotion["failed_criteria"]
    ):
        raise ValueError("candidate cannot be promoted without complete promotion evidence")
    if not candidate["promoted"] and candidate["status"] != "Experimental":
        raise ValueError("an unpromoted PointNet++ candidate must remain Experimental")

    validation = manifest["validation"]
    _require_keys(validation, {"wan_held_out", "demol_65"}, "validation")
    wan = validation["wan_held_out"]
    for name, expected in EXPECTED_WAN.items():
        if wan.get(name) != expected:
            raise ValueError(f"Wan held-out {name} must equal {expected}")
    if validation["demol_65"].get("dbh_mae_cm") != 1.1673846154:
        raise ValueError("Demol DBH MAE must equal 1.1673846154 cm")

    capabilities = manifest["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError("capabilities must be a non-empty list")
    seen_names: set[str] = set()
    required_capability_keys = {"name", "status", "implementation", "evidence", "claim"}
    for row in capabilities:
        _require_keys(row, required_capability_keys, "capability")
        if row["status"] not in VALID_STATUSES:
            raise ValueError(f"invalid capability status: {row['status']}")
        if row["name"] in seen_names:
            raise ValueError(f"duplicate capability: {row['name']}")
        seen_names.add(row["name"])

    core_demo = manifest["core_demo"]
    _require_keys(
        core_demo,
        {
            "reproducible",
            "analyzed_commit",
            "git_dirty",
            "pipeline_version",
            "input_sha256",
            "normalized_result_sha256",
            "segmented_ply_sha256",
            "total_trees",
            "total_carbon_kg",
            "total_co2eq_kg",
        },
        "core_demo",
    )
    if core_demo["reproducible"] is not True:
        raise ValueError("core demo must be reproducible")
    if core_demo["git_dirty"] is not False:
        raise ValueError("core demo evidence must come from a clean Git worktree")
    commit = core_demo["analyzed_commit"]
    if not isinstance(commit, str) or len(commit) != 40:
        raise ValueError("core_demo analyzed_commit must be a 40-character Git SHA")
    for field in ("input_sha256", "normalized_result_sha256", "segmented_ply_sha256"):
        _require_sha256(core_demo[field], f"core_demo {field}")
    if not isinstance(core_demo["total_trees"], int) or core_demo["total_trees"] < 1:
        raise ValueError("core_demo total_trees must be a positive integer")
    for field in ("total_carbon_kg", "total_co2eq_kg"):
        if not isinstance(core_demo[field], (int, float)) or core_demo[field] <= 0:
            raise ValueError(f"core_demo {field} must be positive")

    return manifest


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_capability_matrix(manifest: dict[str, Any]) -> str:
    """Render the complete capability matrix from validated data."""
    candidate = manifest["candidate"]
    promotion_label = "promoted" if candidate["promoted"] else "not promoted"
    lines = [
        "# TreeQ Carbon Platform — Capability Matrix",
        "",
        "> Generated from `docs/evidence/core_demo_manifest.json`; do not edit by hand.",
        "",
        f"Baseline: `{manifest['baseline']['backend']}` (`{manifest['baseline']['status']}`).",
        f"Candidate: {candidate['display_name']} (`{candidate['status']}`, {promotion_label}).",
        "",
        "| Capability | Status | Actual implementation | Evidence | Allowed claim |",
        "|---|---|---|---|---|",
    ]
    for row in manifest["capabilities"]:
        lines.append(
            "| "
            + " | ".join(
                _md(row[key])
                for key in ("name", "status", "implementation", "evidence", "claim")
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_typescript(manifest: dict[str, Any]) -> str:
    """Render the immutable subset used by the Next.js UI."""
    wan = manifest["validation"]["wan_held_out"]
    demol = manifest["validation"]["demol_65"]
    core = manifest["core_demo"]
    candidate = manifest["candidate"]
    return "\n".join(
        [
            "// Generated by scripts/sync_truth.py from the reviewed evidence manifest.",
            "// Do not edit this file by hand.",
            "export const CORE_DEMO_EVIDENCE = {",
            f"  project: {_js_string(manifest['project'])},",
            "  baseline: {",
            f"    backend: {_js_string(manifest['baseline']['backend'])},",
            f"    status: {_js_string(manifest['baseline']['status'])},",
            "  },",
            "  candidate: {",
            f"    backend: {_js_string(candidate['backend'])},",
            f"    displayName: {_js_string(candidate['display_name'])},",
            f"    status: {_js_string(candidate['status'])},",
            f"    promoted: {str(candidate['promoted']).lower()},",
            "  },",
            "  validation: {",
            "    wanHeldOut: {",
            f"      woodIoU: {wan['wood_iou']},",
            f"      leafIoU: {wan['leaf_iou']},",
            f"      meanIoU: {wan['mean_iou']},",
            f"      accuracy: {wan['accuracy']},",
            "    },",
            "    demol65: {",
            f"      dbhMaeCm: {demol['dbh_mae_cm']},",
            f"      volumeMapePct: {demol['volume_mape_pct']},",
            "    },",
            "  },",
            "  coreDemo: {",
            f"    reproducible: {str(core['reproducible']).lower()},",
            f"    analyzedCommit: {_js_string(core['analyzed_commit'])},",
            f"    pipelineVersion: {_js_string(core['pipeline_version'])},",
            f"    backend: {_js_string(manifest['baseline']['backend'])},",
            f"    totalTrees: {core.get('total_trees', 0)},",
            f"    totalCarbonKg: {core.get('total_carbon_kg', 0)},",
            f"    totalCo2eqKg: {core.get('total_co2eq_kg', 0)},",
            "  },",
            "} as const;",
            "",
        ]
    )


def render_truth_block(manifest: dict[str, Any]) -> str:
    """Render a compact human-readable snapshot for controlled documents."""
    wan = manifest["validation"]["wan_held_out"]
    demol = manifest["validation"]["demol_65"]
    core = manifest["core_demo"]
    candidate = manifest["candidate"]
    candidate_line = (
        f"- {candidate['display_name']}: **{candidate['status']}**, promoted by the recorded evidence gate."
        if candidate["promoted"]
        else (
            f"- {candidate['display_name']}: **{candidate['status']}**, not promoted; "
            "no verified independent final-test gate."
        )
    )
    return "\n".join(
        [
            "### Verified truth snapshot (generated)",
            "",
            f"- Baseline: `{manifest['baseline']['backend']}` — **Implemented**.",
            candidate_line,
            (
                f"- Wan 2021 held-out: Wood IoU `{wan['wood_iou']}`, "
                f"Leaf IoU `{wan['leaf_iou']}`, Mean IoU `{wan['mean_iou']}`, "
                f"accuracy `{wan['accuracy']}`. The held-out loader was also used for best-epoch selection."
            ),
            (
                f"- Demol isolated-tree validation (65 trees): DBH MAE "
                f"`{demol['dbh_mae_cm']} cm`; Volume MAPE "
                f"`{demol['volume_mape_pct']}%`. This is not an eight-stage or carbon validation."
            ),
            (
                f"- Deterministic core demo: `{core['total_trees']}` trees, "
                f"`{core['total_carbon_kg']} kg C`, `{core['total_co2eq_kg']} kg CO2e`; "
                f"analyzed commit `{core['analyzed_commit'][:12]}` with a clean worktree."
            ),
            "- Species classification: **Stub**. Carbon stock/CO2e estimates are not certified credits.",
        ]
    )


def replace_truth_block(text: str, rendered: str) -> str:
    """Replace exactly one generated block; fail on absent or ambiguous anchors."""
    if text.count(TRUTH_START) != 1 or text.count(TRUTH_END) != 1:
        raise ValueError("document must contain exactly one pair of truth markers")
    start = text.index(TRUTH_START) + len(TRUTH_START)
    end = text.index(TRUTH_END)
    if start > end:
        raise ValueError("truth markers are out of order")
    return text[:start] + "\n" + rendered.rstrip() + "\n" + text[end:]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sync(repo_root: Path, *, check: bool) -> int:
    """Write generated truth, or compare it with the checked-in bytes."""
    manifest = load_manifest(repo_root / "docs/evidence/core_demo_manifest.json")
    expected_files = {
        repo_root / "docs/CAPABILITY_MATRIX.md": render_capability_matrix(manifest),
        repo_root / "apps/web/src/generated/core-demo-evidence.ts": render_typescript(manifest),
    }
    truth_block = render_truth_block(manifest)
    for relative in CONTROLLED_DOCS:
        path = repo_root / relative
        expected_files[path] = replace_truth_block(path.read_text(encoding="utf-8"), truth_block)

    drift: list[str] = []
    for path, expected in expected_files.items():
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                drift.append(str(path.relative_to(repo_root)))
        else:
            _write_text(path, expected)
    if drift:
        print(json.dumps({"status": "drift", "files": drift}, sort_keys=True))
        return 1
    print(json.dumps({"status": "ok", "mode": "check" if check else "write"}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    return sync(repo_root=args.repo_root.resolve(), check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
