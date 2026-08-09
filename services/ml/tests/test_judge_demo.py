"""Integration contract for deterministic judge-demo artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import run_judge_demo as judge_runner

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
    listed = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            commit,
            "--",
            "services/ml/pipeline",
            "services/ml/scripts/run_judge_demo.py",
            "services/ml/data/species_db.csv",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    tracked_files = sorted(
        path for path in listed if path.endswith(".py") or path == "services/ml/data/species_db.csv"
    )
    digest = hashlib.sha256()
    for relative in tracked_files:
        blob = subprocess.run(
            ["git", "show", f"{commit}:{relative}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(blob).digest())
    source = {
        "tree_sha256": digest.hexdigest(),
        "tracked_files": tracked_files,
    }
    monkeypatch.setattr(
        judge_runner,
        "_source_identity",
        lambda _repo_root, _commit: source,
        raising=False,
    )
    return source


def init_clean_runner_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    ml_root = repo_root / "services" / "ml"
    shutil.copytree(
        REPO_ROOT / "services" / "ml" / "pipeline",
        ml_root / "pipeline",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copytree(REPO_ROOT / "services" / "ml" / "data", ml_root / "data")
    scripts = ml_root / "scripts"
    scripts.mkdir()
    shutil.copy2(
        REPO_ROOT / "services" / "ml" / "scripts" / "run_judge_demo.py",
        scripts / "run_judge_demo.py",
    )
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
            "runner snapshot fixture",
        ],
        cwd=repo_root,
        check=True,
    )
    return repo_root


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
    assert candidate["source"]["tree_sha256"] == clean_repo_state["tree_sha256"]
    assert "services/ml/pipeline/main.py" in candidate["source"]["tracked_files"]
    assert "services/ml/data/species_db.csv" in candidate["source"]["tracked_files"]
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


def test_judge_demo_rejects_repository_change_across_analysis(
    tmp_path, monkeypatch, clean_repo_state
):
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


def test_judge_demo_rejects_transient_source_change(tmp_path, monkeypatch, clean_repo_state):
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
    )
    identities = iter(
        [
            clean_repo_state,
            {
                "tree_sha256": "b" * 64,
                "tracked_files": clean_repo_state["tracked_files"],
            },
        ]
    )
    monkeypatch.setattr(
        judge_runner,
        "_source_identity",
        lambda _repo_root, _commit: next(identities),
        raising=False,
    )

    with pytest.raises(RuntimeError, match="source"):
        judge_runner.run_judge_demo(tmp_path, REPO_ROOT)


def test_judge_demo_uses_commit_snapshot_during_transient_data_edit(tmp_path, monkeypatch):
    repo_root = init_clean_runner_repo(tmp_path)
    ml_root = repo_root / "services" / "ml"
    species_path = ml_root / "data" / "species_db.csv"
    original_species = species_path.read_bytes()
    mutated_species = original_species.replace(b",0.0509,", b",5.0900,", 1)
    assert mutated_species != original_species

    monkeypatch.setattr(judge_runner, "RUNNER_REPO_ROOT", repo_root)
    monkeypatch.setattr(judge_runner, "ML_ROOT", ml_root)
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    for name in list(sys.modules):
        if name == "pipeline" or name.startswith("pipeline."):
            monkeypatch.delitem(sys.modules, name)

    real_load = judge_runner._load_pipeline_modules
    loaded_roots: list[Path] = []

    def load_with_transient_edit(source_ml_root=None):
        modules = real_load() if source_ml_root is None else real_load(source_ml_root)
        loaded_roots.append(Path(source_ml_root) if source_ml_root is not None else ml_root)
        process = modules["main"].process_point_cloud

        def process_while_worktree_is_modified(*args, **kwargs):
            species_path.write_bytes(mutated_species)
            try:
                return process(*args, **kwargs)
            finally:
                species_path.write_bytes(original_species)

        modules["main"].process_point_cloud = process_while_worktree_is_modified
        return modules

    monkeypatch.setattr(judge_runner, "_load_pipeline_modules", load_with_transient_edit)
    output_dir = tmp_path / "candidate"
    judge_runner.run_judge_demo(output_dir, repo_root)

    candidate = json.loads((output_dir / "candidate.json").read_text(encoding="utf-8"))
    result_text = (output_dir / "result.json").read_text(encoding="utf-8")
    # 4613.45 after the coefficient gate; 4672.7 once the RANSAC circle fit
    # refits on its consensus set, which moves DBH by a few millimetres and so
    # moves biomass. Was 4729.06 before either.
    #
    # 4729.06 until the allometric coefficient gate landed. run_judge_demo
    # passes default_species="Tectona grandis", and teak's equation has never
    # been checked against Tsutsumi 1983, so the tree is now costed with Chave
    # 2014 at teak's own wood density instead. Lower, and defensible.
    #
    # The published artifacts under apps/web/public/demo still record 4729.06.
    # That is not wrong - it is what the pipeline produced at that commit, and
    # it still verifies against its own manifest - but it is no longer what this
    # code produces. Regenerating them is a deliberate act on hash-verified
    # evidence and is tracked separately.
    assert candidate["result"]["total_co2eq_kg"] == 4672.7
    assert species_path.read_bytes() == original_species
    assert loaded_roots and loaded_roots[0] != ml_root
    assert not loaded_roots[0].exists()
    assert str(loaded_roots[0]) not in result_text
    assert "treeq-judge-source-" not in result_text


def test_judge_demo_cleans_commit_snapshot_after_analysis_error(tmp_path, monkeypatch):
    repo_root = init_clean_runner_repo(tmp_path)
    ml_root = repo_root / "services" / "ml"
    monkeypatch.setattr(judge_runner, "RUNNER_REPO_ROOT", repo_root)
    monkeypatch.setattr(judge_runner, "ML_ROOT", ml_root)
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    for name in list(sys.modules):
        if name == "pipeline" or name.startswith("pipeline."):
            monkeypatch.delitem(sys.modules, name)

    real_load = judge_runner._load_pipeline_modules
    loaded_roots: list[Path] = []

    def load_with_failure(source_ml_root=None):
        modules = real_load() if source_ml_root is None else real_load(source_ml_root)
        loaded_roots.append(Path(source_ml_root) if source_ml_root is not None else ml_root)

        def fail_analysis(*_args, **_kwargs):
            raise RuntimeError("forced analysis failure")

        modules["main"].process_point_cloud = fail_analysis
        return modules

    monkeypatch.setattr(judge_runner, "_load_pipeline_modules", load_with_failure)
    with pytest.raises(RuntimeError, match="forced analysis failure"):
        judge_runner.run_judge_demo(tmp_path / "candidate", repo_root)

    assert loaded_roots and loaded_roots[0] != ml_root
    assert not loaded_roots[0].exists()


def test_judge_demo_cli_uses_pipeline_from_its_own_checkout(tmp_path):
    script = REPO_ROOT / "services" / "ml" / "scripts" / "run_judge_demo.py"
    probe = (
        "import importlib.util,json,pathlib;"
        f"p=pathlib.Path({str(script)!r});"
        "s=importlib.util.spec_from_file_location('judge_runner_probe',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "mods=m._load_pipeline_modules();"
        "print(json.dumps({k:str(pathlib.Path(v.__file__).resolve()) "
        "for k,v in mods.items()}))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert proc.returncode == 0, proc.stderr
    origins = json.loads(proc.stdout)
    assert origins
    assert all(
        Path(path).is_relative_to(REPO_ROOT / "services" / "ml") for path in origins.values()
    )

    other_checkout = tmp_path / "other-checkout"
    other_checkout.mkdir()
    rejected = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-dir",
            str(tmp_path / "candidate"),
            "--repo-root",
            str(other_checkout),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert rejected.returncode != 0
    assert "checkout" in rejected.stderr
