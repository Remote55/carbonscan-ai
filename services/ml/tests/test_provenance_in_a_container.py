"""Provenance where there is no git.

resolve_git_commit and git_worktree_dirty shell out. An image built from this
repository has neither .git nor, usually, the git binary, so both raised — and
they were called while building the result, after the entire analysis had run.
A ten-minute request would spend all ten minutes and then fail to report a
misconfiguration that was knowable before it started.
"""

from __future__ import annotations

import subprocess

import numpy as np
import pytest

from pipeline import main as pipeline_main
from pipeline.provenance import (
    COMMIT_ENV_VAR,
    DIRTY_ENV_VAR,
    ProvenanceUnavailable,
    git_worktree_dirty,
    resolve_git_commit,
)

SHA = "0123456789abcdef0123456789abcdef01234567"


class TestBakedCommit:
    def test_env_var_wins_over_the_working_tree(self, monkeypatch, tmp_path):
        monkeypatch.setenv(COMMIT_ENV_VAR, SHA)
        assert resolve_git_commit(tmp_path) == SHA

    def test_uppercase_is_normalised(self, monkeypatch, tmp_path):
        monkeypatch.setenv(COMMIT_ENV_VAR, SHA.upper())
        assert resolve_git_commit(tmp_path) == SHA

    @pytest.mark.parametrize("bad", ["", "   ", "abc123", SHA + "0", "z" * 40])
    def test_a_malformed_sha_is_not_quietly_accepted(self, monkeypatch, tmp_path, bad):
        monkeypatch.setenv(COMMIT_ENV_VAR, bad)
        with pytest.raises((ProvenanceUnavailable, Exception)):
            resolve_git_commit(tmp_path)

    def test_no_git_and_no_env_is_fatal_and_says_what_to_set(self, monkeypatch, tmp_path):
        monkeypatch.delenv(COMMIT_ENV_VAR, raising=False)
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("git"))
        )
        with pytest.raises(ProvenanceUnavailable) as exc:
            resolve_git_commit(tmp_path)
        assert COMMIT_ENV_VAR in str(exc.value)


class TestBakedDirtyFlag:
    @pytest.mark.parametrize("value,expected", [
        ("0", False), ("false", False), ("no", False), ("FALSE", False),
        ("1", True), ("true", True), ("yes", True),
    ])
    def test_reads_the_env_var(self, monkeypatch, tmp_path, value, expected):
        monkeypatch.setenv(DIRTY_ENV_VAR, value)
        assert git_worktree_dirty(tmp_path) is expected

    def test_a_baked_commit_without_a_dirty_flag_reports_dirty(self, monkeypatch, tmp_path):
        """Pessimistic on purpose. Dirty means "do not trust this provenance",
        which is exactly the situation when nobody recorded the answer."""
        monkeypatch.setenv(COMMIT_ENV_VAR, SHA)
        monkeypatch.delenv(DIRTY_ENV_VAR, raising=False)
        assert git_worktree_dirty(tmp_path) is True


class TestFailsBeforeTheWork:
    def test_a_container_without_provenance_does_not_run_the_pipeline(self, monkeypatch):
        """The point of the whole change. Without it this raised after ground
        classification, height normalisation, segmentation, wood/leaf and QSM
        had all completed."""
        monkeypatch.delenv(COMMIT_ENV_VAR, raising=False)
        monkeypatch.delenv(DIRTY_ENV_VAR, raising=False)
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("git"))
        )

        stages: list[str] = []
        rng = np.random.default_rng(0)
        points = np.column_stack([
            rng.uniform(0, 20, 4000), rng.uniform(0, 20, 4000), rng.uniform(0, 15, 4000)
        ])

        with pytest.raises(ProvenanceUnavailable):
            pipeline_main.process_points(
                points, progress_callback=lambda stage, _pct: stages.append(stage)
            )

        assert stages == [], f"work started before provenance was settled: {stages}"

    def test_a_baked_commit_reaches_the_result_metadata(self, monkeypatch):
        monkeypatch.setenv(COMMIT_ENV_VAR, SHA)
        monkeypatch.setenv(DIRTY_ENV_VAR, "false")
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("git"))
        )

        rng = np.random.default_rng(1)
        points = np.column_stack([
            rng.uniform(0, 20, 4000), rng.uniform(0, 20, 4000), rng.uniform(0, 15, 4000)
        ])
        result = pipeline_main.process_points(points)

        assert result.metadata["git_commit"] == SHA
        assert result.metadata["git_dirty"] is False
