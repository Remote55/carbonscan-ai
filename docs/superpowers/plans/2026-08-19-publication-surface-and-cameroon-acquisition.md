# Publication Surface and Cameroon Acquisition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the public site publishing a CO₂e figure 25% too high, guard the three
places where published figures drift from the manifest, and get the Cameroon cohort
onto disk and documented so the evaluation can be planned against a layout somebody
has actually seen.

**Architecture:** Four gates and one acquisition. Each gate is a pure function that
returns findings, wrapped by a test that asserts the findings are empty — so the
gate is written first, watched to fail on the real defect, and only then fixed. No
gate re-runs the pipeline: they compare committed artefacts and committed text
against the manifest, which keeps them fast enough for CI and independent of the
691 MB cohorts.

**Tech Stack:** Python 3.11, pytest, ruff. Existing modules `scripts/sync_truth.py`
and `scripts/judge_demo_manifest.py`. No new dependencies.

---

## Source spec

`docs/superpowers/specs/2026-08-19-tropical-validation-design.md`, sections 9 and
12. Section 12 step 2 forbids writing evaluation code before the archive is opened,
so this plan stops at acquisition. The evaluation plan is written from Task 5's
findings.

## Preconditions

**The working tree must be clean before Task 2.** `run_judge_demo.py` refuses to
produce artefacts from a dirty checkout, by design. The T-VER work in progress
(`services/ml/pipeline/tver.py`, `docs/ml/TVER_EQUATIONS.md`,
`services/ml/tests/test_tver.py`, and modifications to `allometric.py`,
`species_db.csv`, `ALLOMETRIC_COEFFICIENTS.md`, `test_independent_eval.py`) must be
committed or stashed first. Tasks 1, 3, 4 and 5 do not need a clean tree.

**Python.** Use the existing virtualenv: `services/ml/.venv/Scripts/python.exe` on
this machine. CI uses a bare `python`. Both are written where a command appears.

## File structure

| file | responsibility | change |
|---|---|---|
| `scripts/judge_demo_manifest.py` | seal/check the published demo artefacts | add a currency gate; it currently checks only self-consistency |
| `scripts/tests/test_judge_demo_manifest.py` | tests for the above | add currency tests |
| `scripts/sync_truth.py` | manifest ↔ document truth | add two gates: prose figures, evidence paths |
| `scripts/tests/test_sync_truth.py` | tests for the above | add tests for both gates |
| `apps/web/public/demo/*` | the artefacts the public sees | regenerate at HEAD |
| `docs/evidence/judge_demo_manifest.json` | byte-identical twin of the public manifest | regenerate |
| `apps/web/src/generated/judge-demo-evidence.ts` | the web app's typed copy | regenerate |
| `README.md`, `AGENTS.md`, `docs/PROJECT_SPEC.md`, `docs/ml/PIPELINE.md` | quote figures in prose | correct them |
| `docs/CAPABILITY_MATRIX.md`, `docs/evidence/core_demo_manifest.json` | capability claims | drop the mobile row |
| `apps/web/src/app/page.tsx` | landing copy | drop the aerial-photograph claim |
| `.github/workflows/ci-ml.yml` | CI | run the gates; drop the dead `apps/mobile` path |
| `services/ml/data/raw/dryad_cameroon/` | the cohort | new, gitignored |
| `docs/ml/CAMEROON_EVIDENCE_CHAIN.md` | what is in the archive | new |

---

## Task 1: A currency gate for the published demo artefacts

The published artefacts were analysed at `e88e616`, 28 commits back.
`scripts/judge_demo_manifest.py check` passes anyway, and the reason is structural:
`check_manifest` reads the core manifest with
`_git_blob_bytes(repo_root, manifest["analyzed_commit"], CORE_MANIFEST_PATH)` — at
the artefact's own recorded commit. It verifies the artefacts against the past they
pinned. It cannot notice that the present moved.

The gate added here asks a different question: has anything that determines the
output changed since that commit? It needs no clean worktree and no pipeline run.

**Files:**
- Modify: `scripts/judge_demo_manifest.py`
- Test: `scripts/tests/test_judge_demo_manifest.py`

- [ ] **Step 1: Write the failing test**

Append to `scripts/tests/test_judge_demo_manifest.py`:

```python
def test_stale_pipeline_paths_reports_nothing_when_analysed_at_head():
    """A demo sealed at HEAD has no pipeline change behind it."""
    repo_root = Path(__file__).resolve().parents[2]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert judge_demo_manifest.stale_pipeline_paths(repo_root, head) == ()


def test_published_demo_artifacts_are_current():
    """The committed artefacts must not lag a pipeline change.

    This is the check `check_manifest` structurally cannot make: it reads the
    core manifest at the artefact's own `analyzed_commit`, so it validates the
    artefacts against the commit they pinned and never against HEAD.
    """
    repo_root = Path(__file__).resolve().parents[2]
    manifest = json.loads(
        (repo_root / "apps/web/public/demo/manifest.json").read_text(encoding="utf-8")
    )

    stale = judge_demo_manifest.stale_pipeline_paths(
        repo_root, manifest["analyzed_commit"]
    )

    assert stale == (), (
        "The published demo artefacts were analysed at "
        f"{manifest['analyzed_commit'][:12]}, and these paths have changed since: "
        f"{', '.join(stale)}. Regenerate and reseal them."
    )
```

No new imports are needed: the file already imports `json`, `subprocess` and
`Path`, and loads the module as `judge_demo_manifest` through `importlib` at the
top.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/test_judge_demo_manifest.py -k stale_pipeline_paths -v --no-cov
```

Expected: both FAIL with `AttributeError: module 'judge_demo_manifest' has no
attribute 'stale_pipeline_paths'`.

- [ ] **Step 3: Implement the gate**

In `scripts/judge_demo_manifest.py`, after the `ALLOWED_RELEASE_STATUSES`
definition near line 28, add:

```python
#: Paths whose contents determine what `run_judge_demo.py` produces.
#:
#: A change under any of these makes the published artefacts describe a pipeline
#: that no longer exists. `species_db.csv` is here because it is data the image
#: ships and Chave reads: `8cf3058` changed five wood densities and moved the
#: demo's CO2e from 4748.95 to 3798.38 without touching a line of pipeline code.
PIPELINE_INPUT_PATHS = (
    "services/ml/pipeline",
    "services/ml/data/species_db.csv",
    "services/ml/scripts/run_judge_demo.py",
)


def stale_pipeline_paths(
    repo_root: str | Path, analyzed_commit: str
) -> tuple[str, ...]:
    """Paths determining the demo output that changed between a commit and HEAD.

    Empty when the published artefacts still describe the pipeline at HEAD.

    This is deliberately a diff and not a re-run. Re-running needs a clean
    worktree and three minutes; a diff needs neither and answers the only
    question that matters — whether anything the result depends on has moved.

    Args:
        repo_root: the repository checkout.
        analyzed_commit: the commit the published artefacts record.

    Returns:
        Changed paths, sorted, empty when the artefacts are current.

    Raises:
        ValueError: when `analyzed_commit` is not a commit in this repository.
    """
    root = Path(repo_root).resolve(strict=True)
    try:
        completed = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                f"{analyzed_commit}..HEAD",
                "--",
                *PIPELINE_INPUT_PATHS,
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            f"Cannot diff {analyzed_commit!r} against HEAD: {exc.stderr.strip()}"
        ) from exc
    return tuple(sorted(line for line in completed.stdout.splitlines() if line))
```

- [ ] **Step 4: Run the tests**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/test_judge_demo_manifest.py -k stale_pipeline_paths -v --no-cov
```

Expected: `test_stale_pipeline_paths_reports_nothing_when_analysed_at_head` PASSES.
`test_published_demo_artifacts_are_current` **FAILS**, listing
`services/ml/data/species_db.csv` and several `services/ml/pipeline/*` files. That
failure is the defect. Task 2 fixes it; do not weaken the test.

- [ ] **Step 5: Wire the gate into `check_manifest`**

In `check_manifest`, immediately after `_validate_public_manifest(manifest)`, add:

```python
    stale = stale_pipeline_paths(repo_root, manifest["analyzed_commit"])
    if stale:
        raise ValueError(
            "Published demo artefacts are stale: analysed at "
            f"{manifest['analyzed_commit'][:12]}, and these have changed since — "
            + ", ".join(stale)
        )
```

- [ ] **Step 6: Confirm the CLI now fails**

```bash
services/ml/.venv/Scripts/python.exe scripts/judge_demo_manifest.py check
```

Expected: non-zero exit, message naming the changed paths. It printed
`{"command": "check", "status": "ok"}` before this task.

- [ ] **Step 7: Commit**

```bash
git add scripts/judge_demo_manifest.py scripts/tests/test_judge_demo_manifest.py
git commit -F - <<'MSG'
feat(evidence): the demo check validated the past it pinned, not the present

check_manifest reads the core manifest with _git_blob_bytes at the artefact's own
analyzed_commit. Everything it compares is therefore internally consistent with
the commit the artefacts were made at, and no amount of subsequent change can
make it fail. It reported ok on artefacts 28 commits behind HEAD.

stale_pipeline_paths asks the question it could not: has anything determining the
output moved since that commit. A diff, not a re-run - no clean worktree and no
three-minute pipeline run, because the only thing worth knowing is whether the
result's inputs changed.

species_db.csv is in the watched set because 8cf3058 changed five wood densities
and moved the demo's CO2e from 4748.95 to 3798.38 without touching pipeline code.

The published artefacts fail this check. That is the point; the next commit
regenerates them.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 2: Regenerate the published demo artefacts at HEAD

**Requires a clean working tree.** See Preconditions.

**Files:**
- Modify: `apps/web/public/demo/manifest.json`, `result.json`, `input.ply`, `segmented.ply`
- Modify: `docs/evidence/judge_demo_manifest.json`
- Modify: `apps/web/src/generated/judge-demo-evidence.ts`

- [ ] **Step 1: Confirm the tree is clean**

```bash
git status --porcelain
```

Expected: no output. If anything is listed, commit or stash it before continuing —
`run_judge_demo.py` records `git_dirty` and the seal step rejects a dirty candidate.

- [ ] **Step 2: Record the figure that is about to change**

```bash
services/ml/.venv/Scripts/python.exe -c "import json,io; d=json.load(io.open('apps/web/public/demo/result.json',encoding='utf-8')); print(d['summary']['total_carbon_kg'], d['summary']['total_co2eq_kg'])"
```

Expected: `1295.17 4748.95`. Write these down; step 5 compares against them.

- [ ] **Step 3: Run the demo generator**

```bash
services/ml/.venv/Scripts/python.exe services/ml/scripts/run_judge_demo.py --output-dir temp/judge-regen --repo-root .
```

Expected: exit 0, and `temp/judge-regen/candidate.json` exists.

- [ ] **Step 4: Seal the new artefacts**

```bash
services/ml/.venv/Scripts/python.exe scripts/judge_demo_manifest.py seal --artifact-dir temp/judge-regen
```

Expected: `{"command": "seal", "status": "ok"}`. This writes
`apps/web/public/demo/`, `docs/evidence/judge_demo_manifest.json` and
`apps/web/src/generated/judge-demo-evidence.ts` together.

- [ ] **Step 5: Verify the CO₂e figure moved to the value `8cf3058` predicted**

```bash
services/ml/.venv/Scripts/python.exe -c "import json,io; d=json.load(io.open('apps/web/public/demo/result.json',encoding='utf-8')); print(d['summary']['total_carbon_kg'], d['summary']['total_co2eq_kg'])"
```

Expected: `total_co2eq_kg` is **3798.38**, matching the figure `8cf3058`'s commit
message states.

If it is not 3798.38, stop and investigate before committing. Either a later
commit changed the result again — in which case record which, and why, in the
commit message — or the regeneration did not do what it should. Do not adjust the
expected value to match whatever came out.

- [ ] **Step 6: Both checks now pass**

```bash
services/ml/.venv/Scripts/python.exe scripts/judge_demo_manifest.py check
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/test_judge_demo_manifest.py -v --no-cov
```

Expected: `{"command": "check", "status": "ok"}`, and every test passes including
`test_published_demo_artifacts_are_current`.

- [ ] **Step 7: Commit**

```bash
git add apps/web/public/demo docs/evidence/judge_demo_manifest.json apps/web/src/generated/judge-demo-evidence.ts
git commit -F - <<'MSG'
fix(evidence): the public CO2e figure was 25 percent high for 28 commits

treeqcarbon.vercel.app/demo served 4748.95 kg CO2e under a CHECKSUM VERIFIED
badge. The checksums were correct. They verified artefacts built by a pipeline
that has since been fixed - a verification badge proves an artefact is
unaltered, not that it is current.

The correct figure was known and written down at the time. 8cf3058, which
replaced five air-dry wood densities with basic ones, states it: "the judge demo
goes 4748.95 -> 3798.38". The artefacts were never regenerated, so the site kept
serving a carbon number computed from densities this project had already
established were the wrong quantity.

Regenerated at HEAD and resealed. The gate from the previous commit now passes
because the artefacts are current, not because it cannot tell.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 3: Guard accuracy figures quoted in prose

`docs/PROJECT_SPEC.md` contains the correct DBH MAE at line 18, inside its
generated `TREEQ_TRUTH` block, and the superseded one at line 234 in hand-written
prose. The same file disagrees with itself. `README.md:85-87`, `AGENTS.md:103` and
`docs/ml/PIPELINE.md:148` carry the superseded values too.

`sync_truth.py` regenerates the block between the markers and never looks at the
rest of the document. This gate looks at the rest.

**Files:**
- Modify: `scripts/sync_truth.py`
- Test: `scripts/tests/test_sync_truth.py`

- [ ] **Step 1: Write the failing test**

Append to `scripts/tests/test_sync_truth.py`:

```python
def _repo_manifest() -> tuple[Path, dict[str, object]]:
    """The checkout and its committed manifest, loaded the way sync uses it."""
    repo_root = Path(__file__).resolve().parents[2]
    manifest = load_manifest(
        repo_root / "docs/evidence/core_demo_manifest.json", repo_root=repo_root
    )
    return repo_root, manifest


def test_stale_figures_accepts_a_manifest_value():
    """A figure that equals a manifest field is not stale."""
    _, manifest = _repo_manifest()
    demol = manifest["validation"]["demol_65"]
    document = f"Demol 65 trees give DBH MAE {demol['dbh_mae_cm']} cm.\n"

    assert stale_figures_in_text(document, manifest) == ()


def test_stale_figures_reports_a_superseded_value():
    """1.1673846154 is the pre-derivation DBH MAE and must be caught."""
    _, manifest = _repo_manifest()
    document = "Demol 65 trees give DBH MAE 1.1673846154 cm.\n"

    assert stale_figures_in_text(document, manifest) == (
        (1, "DBH MAE", "1.1673846154"),
    )


def test_no_controlled_document_quotes_a_stale_figure():
    """Every accuracy figure in prose must equal one the manifest records.

    docs/ml/DEMOL_EVIDENCE_CHAIN.md:97 labels 1.1674 and 18.77 "published
    before"; the derived values are 0.8983 and 11.52. Both were in the tree at
    once, in the same documents, and sync_truth --check passed because it
    compares the manifest against an artefact and never against the markdown
    that quotes it.
    """
    repo_root, manifest = _repo_manifest()
    offences = []
    for relative in FIGURE_PROSE_DOCS:
        text = (repo_root / relative).read_text(encoding="utf-8")
        for lineno, label, raw in stale_figures_in_text(text, manifest):
            offences.append(f"{relative.as_posix()}:{lineno} {label} = {raw}")

    assert offences == [], "Figures not found in the manifest:\n" + "\n".join(offences)
```

Extend the existing import block at the top of the file — it already imports
`load_manifest` and uses `from scripts.sync_truth import (...)`:

```python
from scripts.sync_truth import (
    DEMOL_PUBLISHED_FIELDS,
    DEMOL_RESULT_PATH,
    FIGURE_PROSE_DOCS,
    PROMOTION_POLICY,
    load_manifest,
    render_capability_matrix,
    render_typescript,
    replace_truth_block,
    stale_figures_in_text,
)
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/test_sync_truth.py -k stale_accuracy -v --no-cov
```

Expected: all three FAIL with `AttributeError: module 'sync_truth' has no attribute
'stale_figures_in_text'`.

- [ ] **Step 3: Implement the gate**

In `scripts/sync_truth.py`, after `DEMOL_RESULT_PATH` near line 77, add:

```python
#: Documents that quote accuracy figures in hand-written prose.
#:
#: The TREEQ_TRUTH block is regenerated from the manifest, so the numbers inside
#: it are correct by construction. Everything outside it is typed by hand and
#: drifts. docs/PROJECT_SPEC.md carried both at once: the derived 0.898318 at
#: line 18 and the superseded 1.1673846154 at line 234.
FIGURE_PROSE_DOCS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/PROJECT_SPEC.md"),
    Path("docs/ml/PIPELINE.md"),
)

#: A metric name followed by its value, however the document spaces or marks it up.
_FIGURE_PATTERN = re.compile(
    r"(DBH MAE|Height MAE|Volume MAPE)[^0-9\n]{0,24}([0-9]+\.[0-9]+)"
)


def published_figure_values(manifest: dict[str, Any]) -> frozenset[float]:
    """Every DBH MAE, Height MAE and Volume MAPE the manifest records.

    Both evaluations are included. The Demol block and the independent PointNet
    review measure the same cohort by different routes and legitimately differ,
    and both are quoted in prose, so a figure matching either one is current.
    """
    demol = manifest["validation"]["demol_65"]
    values = {
        float(demol["dbh_mae_cm"]),
        float(demol["height_mae_m"]),
        float(demol["volume_mape_pct"]),
    }
    independent = manifest["validation"].get("pointnet_independent")
    if independent is not None:
        for side in ("baseline", "candidate"):
            block = independent[side]
            values |= {
                float(block["dbh_mae_cm"]),
                float(block["height_mae_m"]),
                float(block["volume_mape_pct"]),
            }
    return frozenset(values)


def stale_figures_in_text(
    text: str, manifest: dict[str, Any]
) -> tuple[tuple[int, str, str], ...]:
    """Accuracy figures in `text` that no manifest field records.

    Args:
        text: a document's full contents.
        manifest: the parsed core demo manifest.

    Returns:
        `(line_number, metric_name, value_as_written)` for each offending figure,
        empty when every figure quoted is one the manifest holds.
    """
    allowed = published_figure_values(manifest)
    found: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, raw in _FIGURE_PATTERN.findall(line):
            if float(raw) not in allowed:
                found.append((lineno, label, raw))
    return tuple(found)
```

Add `import re` to the imports at the top of the file if it is not already there.

- [ ] **Step 4: Run the tests**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/test_sync_truth.py -k stale_accuracy -v --no-cov
```

Expected: the first two PASS. `test_no_controlled_document_quotes_a_stale_accuracy_figure`
**FAILS**, listing `README.md:85`, `README.md:86`, `README.md:87`,
`AGENTS.md:103`, `docs/PROJECT_SPEC.md:234` and `docs/ml/PIPELINE.md:148`.

- [ ] **Step 5: Correct README.md**

Replace lines 85-87 of `README.md`:

```markdown
| DBH MAE | **0.898318 cm** |
| Height MAE | **0.543323 m** |
| Volume MAPE | **11.520556%** |
```

- [ ] **Step 6: Correct the other three documents**

`AGENTS.md:103` — replace the three values on that line:

```markdown
65 ต้น DBH MAE `0.898318 cm`, Height MAE `0.543323 m`, Volume MAPE `11.520556%`;
```

`docs/PROJECT_SPEC.md:234`:

```markdown
- **Demol geometry validation:** isolated-tree 65 ต้น, DBH MAE **0.898318 cm**, Height MAE **0.543323 m**,
```

`docs/ml/PIPELINE.md:148`:

```markdown
Demol isolated-tree validation 65 ต้นให้ DBH MAE 0.898318 cm, Height MAE 0.543323 m
```

- [ ] **Step 7: Run the gate and the existing suite**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/ -v --no-cov
services/ml/.venv/Scripts/python.exe scripts/sync_truth.py --check
```

Expected: every test passes, and `{"status": "ok", "mode": "check"}`.

- [ ] **Step 8: Commit**

```bash
git add scripts/sync_truth.py scripts/tests/test_sync_truth.py README.md AGENTS.md docs/PROJECT_SPEC.md docs/ml/PIPELINE.md
git commit -F - <<'MSG'
fix(docs): PROJECT_SPEC held the derived DBH MAE and the superseded one at once

Line 18, inside the generated TREEQ_TRUTH block, read 0.898318 cm. Line 234, in
hand-written prose, read 1.1673846154 cm. DEMOL_EVIDENCE_CHAIN.md:97 labels the
second one "published before" and shows the derived figure is 23% better; volume
MAPE was 39% out the same way. README, AGENTS and PIPELINE carried the old
values too.

sync_truth --check passed throughout, and correctly: validate_demol compares the
manifest against a re-derivable artefact, which was the right fix for the defect
that motivated it. What nothing compared was the manifest against the markdown
quoting it, so the block between the markers stayed true while the prose around
it went stale.

stale_figures_in_text closes that. It accepts a figure equal to any DBH MAE,
Height MAE or Volume MAPE the manifest records - the Demol block and the
independent review measure the same cohort by different routes and both are
legitimately quoted - and rejects everything else.

The direction of this error is worth naming: the pipeline measures better than
the documents claimed. Under-selling is a smaller ethical problem than
over-selling and exactly the same truth problem, and README is listed as current
truth in DOCUMENT_STATUS.md.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 4: Guard capability claims against deleted files

`docs/CAPABILITY_MATRIX.md:21` claims a mobile capture flow and cites
`apps/mobile/lib/main.dart` as its evidence. `apps/mobile` has zero tracked files
and does not exist on disk; `8ce6021` removed it under
`docs/decisions/0007-drop-the-photo-path.md`.

The matrix is generated from `core_demo_manifest.json`, so the evidence path is
data and can be checked.

**Files:**
- Modify: `scripts/sync_truth.py`
- Modify: `docs/evidence/core_demo_manifest.json`
- Modify: `docs/CAPABILITY_MATRIX.md` (generated)
- Modify: `README.md`, `AGENTS.md`
- Modify: `apps/web/src/app/page.tsx`
- Modify: `.github/workflows/ci-ml.yml`
- Test: `scripts/tests/test_sync_truth.py`

- [ ] **Step 1: Write the failing test**

Append to `scripts/tests/test_sync_truth.py`:

```python
def test_missing_evidence_paths_accepts_a_file_that_exists():
    repo_root = Path(__file__).resolve().parents[2]
    capabilities = [{"name": "x", "evidence": "scripts/sync_truth.py"}]

    assert missing_evidence_paths(repo_root, capabilities) == ()


def test_missing_evidence_paths_reports_a_file_that_does_not():
    repo_root = Path(__file__).resolve().parents[2]
    capabilities = [{"name": "Mobile", "evidence": "apps/mobile/lib/main.dart"}]

    assert missing_evidence_paths(repo_root, capabilities) == (
        ("Mobile", "apps/mobile/lib/main.dart"),
    )


def test_missing_evidence_paths_ignores_a_hash_beside_a_path():
    """The evidence column mixes paths with SHA-256 text; only paths resolve."""
    repo_root = Path(__file__).resolve().parents[2]
    capabilities = [
        {"name": "x", "evidence": "scripts/sync_truth.py; SHA-256 5892abc"}
    ]

    assert missing_evidence_paths(repo_root, capabilities) == ()


def test_no_capability_cites_evidence_that_does_not_exist():
    """A capability whose evidence file is gone is a claim with nothing behind it."""
    repo_root, manifest = _repo_manifest()

    missing = missing_evidence_paths(repo_root, manifest["capabilities"])

    assert missing == (), "Capabilities citing files that do not exist: " + "; ".join(
        f"{name} -> {path}" for name, path in missing
    )
```

Add `missing_evidence_paths` to the `from scripts.sync_truth import (...)` block,
keeping it alphabetical.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/test_sync_truth.py -k evidence_path -v --no-cov
```

Expected: all three FAIL with `AttributeError: module 'sync_truth' has no attribute
'missing_evidence_paths'`.

- [ ] **Step 3: Implement the gate**

In `scripts/sync_truth.py`, below `stale_figures_in_text`, add:

```python
#: An evidence entry that names a file rather than a hash or a sentence.
#:
#: The evidence column mixes both - "docs/evidence/x.json; SHA-256 5892..." - so
#: only entries shaped like a repository path are resolved.
_EVIDENCE_FILE = re.compile(r"^[A-Za-z0-9_./-]+\.(?:py|ts|tsx|json|csv|md|dart)$")


def missing_evidence_paths(
    repo_root: str | Path, capabilities: list[dict[str, Any]]
) -> tuple[tuple[str, str], ...]:
    """Capability evidence files that are not in the checkout.

    A capability is a claim, and the evidence column is where the claim is meant
    to be checkable. When the file is gone the row is an assertion with nothing
    behind it, which is how a mobile capture flow stayed in the matrix for ten
    days after `8ce6021` deleted the application.

    Args:
        repo_root: the repository checkout.
        capabilities: the manifest's `capabilities` list.

    Returns:
        `(capability_name, missing_path)` pairs, empty when every cited file
        exists.
    """
    root = Path(repo_root)
    missing: list[tuple[str, str]] = []
    for capability in capabilities:
        for entry in str(capability.get("evidence", "")).split(";"):
            candidate = entry.strip()
            if _EVIDENCE_FILE.match(candidate) and not (root / candidate).exists():
                missing.append((str(capability.get("name", "")), candidate))
    return tuple(missing)
```

- [ ] **Step 4: Run the tests**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/test_sync_truth.py -k evidence_path -v --no-cov
```

Expected: the first two PASS. `test_no_capability_cites_evidence_that_does_not_exist`
**FAILS**, naming the mobile capability and `apps/mobile/lib/main.dart`.

- [ ] **Step 5: Remove the mobile capability from the manifest**

Delete the object whose `"name"` is `"Mobile capture flow"` from the
`"capabilities"` array in `docs/evidence/core_demo_manifest.json`. Change nothing
else in that file.

- [ ] **Step 6: Regenerate the matrix and confirm the gate passes**

```bash
services/ml/.venv/Scripts/python.exe scripts/sync_truth.py --write
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/test_sync_truth.py -v --no-cov
```

Expected: `docs/CAPABILITY_MATRIX.md` no longer has a mobile row, and every test
passes.

- [ ] **Step 7: Remove the remaining mobile and photo claims**

`README.md` — delete the capability-table row beginning `| Mobile capture flow`
(line 57), delete the line `apps/mobile/     Flutter capture/results prototype`
from the repo-structure block (line 156), and rewrite the next-steps item at line
178 so it no longer depends on a mobile end-to-end:

```markdown
5. เปิด independent tropical validation (Cameroon 61) ก่อนเริ่ม marketplace/GIS/certificate
```

`AGENTS.md` — delete the line `apps/mobile/     Flutter (Riverpod, go_router,
camera, Supabase) — สแกน/ถ่ายภาพ → คาร์บอน` (line 31), and delete **lines 72-79**:
the `### Mobile (\`apps/mobile\`)` heading, the four-line ```` ```bash ```` block
beneath it, and the blank line that follows, leaving the `---` that came after it
in place. Also delete the stale rebrand note at line 107, which lists `mobile` as
outstanding work:

```markdown
- Rebrand core surface แล้ว · เหลือ legacy docs/proposal/GitHub-repo-name/logo assets
```

`apps/web/src/app/page.tsx:34` — the system takes scanner point clouds only, per
ADR 0007:

```tsx
      'รองรับข้อมูล Point Cloud จากเครื่องสแกน LiDAR ภาคพื้นดิน (TLS)',
```

`.github/workflows/ci-ml.yml` — delete the two `- "apps/mobile/README.md"` lines,
one under `push.paths` and one under `pull_request.paths`. The file has not
existed since `8ce6021`, so the trigger can never fire.

- [ ] **Step 8: Verify the web build and tests still pass**

```bash
cd apps/web && npm run type-check && npx vitest run
```

Expected: type-check clean, all tests pass. If a test asserts the old landing
copy, update the expected string to the new one — the copy is the thing under
test, and it changed on purpose.

- [ ] **Step 9: Commit**

```bash
cd ../.. && git add scripts/sync_truth.py scripts/tests/test_sync_truth.py docs/evidence/core_demo_manifest.json docs/CAPABILITY_MATRIX.md README.md AGENTS.md apps/web/src/app/page.tsx .github/workflows/ci-ml.yml
git commit -F - <<'MSG'
fix(docs): the capability matrix cited a file deleted ten days earlier

CAPABILITY_MATRIX.md:21 claimed a mobile capture flow and gave
apps/mobile/lib/main.dart as the evidence. 8ce6021 deleted the application under
ADR 0007; apps/mobile has zero tracked files and is not on disk. README's
capability table, its repo-structure block, its next-steps list and two sections
of AGENTS.md said the same.

The matrix is generated from the manifest, so the evidence column is data and
can be resolved. missing_evidence_paths does that. A capability is a claim and
the evidence column is where the claim is meant to be checkable; when the file
is gone the row asserts something with nothing behind it, and nothing noticed
for ten days.

The landing page also told visitors the system accepts ภาพถ่ายทางอากาศ. The same
ADR removed the photograph path, and the gate cannot see prose, so that one was
found by reading the deployed site.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 5: Acquire the Cameroon cohort and write down what is in it

Spec §12 step 2: no evaluation code is written until this exists, because §5
assumes a layout nobody has seen. This task produces the document the evaluation
plan is written from.

**Files:**
- Create: `services/ml/data/raw/dryad_cameroon/` (gitignored)
- Create: `docs/ml/CAMEROON_EVIDENCE_CHAIN.md`
- Modify: `.gitignore`

- [ ] **Step 1: Exclude the cohort from git before downloading it**

`services/ml/data/raw/zenodo_belgium/` is already excluded. Add the new directory
beside it in the same `.gitignore` stanza:

```gitignore
services/ml/data/raw/dryad_cameroon/
```

Verify:

```bash
git check-ignore -v services/ml/data/raw/dryad_cameroon/anything.ply
```

Expected: a line naming `.gitignore` and the rule. A 1.15 GB archive must not be
stageable by accident.

- [ ] **Step 2: Download the archive through a browser**

**Scripted download does not work, and this was tested rather than assumed.**
`https://datadryad.org/api/v2/files/67847/download` answers
`401 {"error":"Unauthorized, must have current bearer token"}`, and
`https://datadryad.org/downloads/file_stream/67847` answers `403` without a
browser User-Agent and serves an HTML page with one. Do not spend time scripting
around it.

Open <https://datadryad.org/dataset/doi:10.5061/dryad.10hq7> and use the download
control on the page. Save the result to
`services/ml/data/raw/dryad_cameroon/Trees.rar`.

- [ ] **Step 3: Verify the download against Dryad's published digest**

Dryad publishes the file's size and MD5 through its API, so integrity is checked
against the source rather than against a hash we invented:

| property | expected |
|---|---|
| size | `1018816227` bytes |
| MD5 | `8a847165f17e1e08ab5139db3a3cdf9c` |

```bash
services/ml/.venv/Scripts/python.exe -c "
import hashlib, pathlib
p = pathlib.Path('services/ml/data/raw/dryad_cameroon/Trees.rar')
digest = hashlib.md5()
with p.open('rb') as handle:
    for chunk in iter(lambda: handle.read(1 << 20), b''):
        digest.update(chunk)
print('size', p.stat().st_size)
print('md5 ', digest.hexdigest())
"
```

Expected: both match the table exactly. If either differs, the download is
incomplete or was served an error page — delete it and retry before extracting.
Re-read the current values if the dataset has been versioned since:

```bash
services/ml/.venv/Scripts/python.exe -c "
import json, urllib.request
base = 'https://datadryad.org/api/v2'
d = json.load(urllib.request.urlopen(base + '/datasets/doi%3A10.5061%2Fdryad.10hq7'))
version = d['_links']['stash:version']['href'].split('/')[-1]
files = json.load(urllib.request.urlopen(f'{base}/versions/{version}/files'))
for f in files['_embedded']['stash:files']:
    print(f['path'], f['size'], f['digestType'], f['digest'])
"
```

- [ ] **Step 4: Extract**

`.rar` needs a tool Windows does not ship. If `unrar` or 7-Zip is absent, install
7-Zip and use it:

```bash
"/c/Program Files/7-Zip/7z.exe" x services/ml/data/raw/dryad_cameroon/Trees.rar -oservices/ml/data/raw/dryad_cameroon/
```

Expected: exit 0, `Everything is Ok`.

- [ ] **Step 5: Inventory the archive**

```bash
services/ml/.venv/Scripts/python.exe -c "
import collections, pathlib
root = pathlib.Path('services/ml/data/raw/dryad_cameroon')
by_ext = collections.Counter()
total = 0
for f in root.rglob('*'):
    if f.is_file():
        by_ext[f.suffix.lower()] += 1
        total += f.stat().st_size
print('total bytes:', total)
for ext, n in by_ext.most_common():
    print(f'{ext or \"(none)\"}: {n}')
print()
for f in sorted(root.rglob('*'))[:40]:
    print(('D ' if f.is_dir() else '  '), f.relative_to(root))
"
```

- [ ] **Step 6: Read the ground-truth table**

The archive's own layout decides which file this is, so find it rather than
assume it. This prints the first four rows of every tabular file in the archive,
which is few enough to read:

```bash
services/ml/.venv/Scripts/python.exe -c "
import csv, io, pathlib
root = pathlib.Path('services/ml/data/raw/dryad_cameroon')
for path in sorted(root.rglob('*')):
    if path.suffix.lower() not in {'.csv', '.txt', '.tsv', '.dat'}:
        continue
    if path.stat().st_size > 5_000_000:
        continue  # a table of 61 trees is small; anything larger is a cloud
    print('=====', path.relative_to(root), path.stat().st_size)
    with io.open(path, encoding='utf-8', errors='replace', newline='') as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        for i, row in enumerate(csv.reader(handle, dialect)):
            print(row)
            if i == 3:
                break
    print()
"
```

If the measurements are in a spreadsheet instead, `.xlsx` will have shown up in
step 5's inventory; read it with `pandas.read_excel`. pandas is already a
`services/ml` dependency (`pyproject.toml:19`, 3.0.3 in the venv), but `openpyxl`
is not, so `pip install openpyxl` into the venv first — as a read-only
convenience, not a project dependency.

Identify, and record verbatim in step 8: the tree identifier column, the taped DBH
column and its unit, the felled height column and its unit, the harvested AGB
column and its unit, and whether AGB is reported dry or fresh.

**Dry against fresh matters more than anything else here.** Chave 2014 predicts
oven-dry above-ground biomass. Scoring it against a fresh mass would make the
pipeline look wrong by roughly the moisture content of green wood. If the column
is fresh mass, find the moisture factor the paper used and record it; if the
archive does not say, record that it does not.

- [ ] **Step 7: Confirm the point clouds pair with the table**

```bash
services/ml/.venv/Scripts/python.exe -c "
import pathlib
root = pathlib.Path('services/ml/data/raw/dryad_cameroon')
clouds = [f for f in root.rglob('*') if f.suffix.lower() in {'.ply','.txt','.xyz','.las','.laz','.asc'}]
print('candidate cloud files:', len(clouds))
for f in clouds[:10]:
    print(f.relative_to(root), f.stat().st_size)
if clouds:
    with open(clouds[0], 'rb') as handle:
        print(repr(handle.read(400)))
"
```

Record the point-cloud format, whether coordinates carry a header, the unit (m or
mm), and how a file maps to a row in the ground-truth table.

- [ ] **Step 8: Write `docs/ml/CAMEROON_EVIDENCE_CHAIN.md`**

Follow `docs/ml/DEMOL_EVIDENCE_CHAIN.md`'s shape. It must record, from what was
observed rather than from the paper:

1. Citation, DOI, licence (CC0 1.0), download date, and the SHA-256 of `Trees.rar`.
2. The directory layout, with file counts by extension.
3. The ground-truth table: every column used, its unit, and dry against fresh.
4. The point-cloud format, unit, and the file-to-row mapping rule.
5. Trees present in one place and not the other, by identifier. The paper says 61;
   if the archive holds a different number, that discrepancy is the finding and
   goes at the top.
6. Anything the archive does not answer — spelled out, not omitted.

Compute the archive hash:

```bash
services/ml/.venv/Scripts/python.exe -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('services/ml/data/raw/dryad_cameroon/Trees.rar').read_bytes()).hexdigest())"
```

- [ ] **Step 9: Commit the document only**

```bash
git status --porcelain
```

Expected: `docs/ml/CAMEROON_EVIDENCE_CHAIN.md` and `.gitignore`, and nothing under
`services/ml/data/raw/`. If cohort files appear, step 1 failed — fix the ignore
rule before committing.

```bash
git add .gitignore docs/ml/CAMEROON_EVIDENCE_CHAIN.md
git commit -F - <<'MSG'
docs(ml): what is actually inside the Cameroon archive

61 trees scanned, felled and weighed in semi-deciduous forest in eastern
Cameroon - Momo Takoudjou et al. 2018, Dryad 10.5061/dryad.10hq7, CC0. The
tropical cohort the spec is built on.

Recorded from the extracted archive rather than from the paper: the layout, the
ground-truth columns and their units, the point-cloud format, the file-to-row
mapping, and whether the harvested mass is dry or fresh. That last one decides
whether the allometric comparison is meaningful at all, since Chave 2014
predicts oven-dry biomass.

The spec forbids writing evaluation code before this document exists, because
section 5 assumes a layout nobody had seen. Now somebody has.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 6: Run the gates in CI

The three gates are worthless if they only run when somebody remembers. None of
them needs a cohort, so none of them can skip.

**Files:**
- Modify: `.github/workflows/ci-ml.yml`

- [ ] **Step 1: Add the gate step**

In `.github/workflows/ci-ml.yml`, after the existing
`Run repository truth and report contract tests` step, add:

```yaml
      - name: Verify published artifacts and documents are current
        # These compare committed artefacts and committed text against the
        # manifest. No cohort, no pipeline run, so they cannot skip - unlike the
        # accuracy tests in docs/ml/WHAT_CI_DOES_NOT_CHECK.md.
        run: |
          python -m pytest scripts/tests/test_judge_demo_manifest.py -v --no-cov
          python scripts/judge_demo_manifest.py check
```

`scripts/tests/test_sync_truth.py` already runs inside the existing
`python -m pytest scripts/tests/ -v --no-cov` step, so the two gates from Tasks 3
and 4 are covered by it.

- [ ] **Step 2: Add the paths that can invalidate the artefacts**

The `CI ML` workflow triggers on `services/ml/**`, which already covers the
pipeline and `species_db.csv`. Add the published artefacts themselves under both
`push.paths` and `pull_request.paths`, so a hand-edit to them is checked:

```yaml
      - "apps/web/public/demo/**"
      - "docs/evidence/judge_demo_manifest.json"
```

- [ ] **Step 3: Verify the workflow parses**

```bash
services/ml/.venv/Scripts/python.exe -c "import yaml,io; d=yaml.safe_load(io.open('.github/workflows/ci-ml.yml',encoding='utf-8')); print([s['name'] for s in d['jobs']['lint-and-test']['steps']])"
```

Expected: a list including `Verify published artifacts and documents are current`.

- [ ] **Step 4: Run everything the gate step will run**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/ -v --no-cov
services/ml/.venv/Scripts/python.exe scripts/judge_demo_manifest.py check
services/ml/.venv/Scripts/python.exe scripts/sync_truth.py --check
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci-ml.yml
git commit -F - <<'MSG'
ci(ml): run the currency gates, which until now ran when somebody remembered

The three gates added in this branch compare committed artefacts and committed
text against the manifest. They need no cohort and no pipeline run, so unlike
the accuracy tests in WHAT_CI_DOES_NOT_CHECK.md they cannot skip, and a green
tick means they actually ran.

The published demo artefacts are added to the trigger paths so a hand-edit to
them is checked too.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

---

## Task 7: Verify the whole branch

- [ ] **Step 1: Full suite**

```bash
services/ml/.venv/Scripts/python.exe -m pytest scripts/tests/ -v --no-cov
cd services/ml && .venv/Scripts/python.exe -m pytest tests/ -q -rs && cd ../..
```

Expected: `scripts/tests/` all pass. `services/ml/tests/` passes with the skip
count `-rs` reports unchanged from before this branch — this plan touches no
pipeline code, so any change in that number needs explaining before merge.

- [ ] **Step 2: Lint**

```bash
cd services/ml && .venv/Scripts/ruff.exe check pipeline/ training/ scripts/ tests/ ../../scripts/*.py ../../scripts/tests/ && cd ../..
```

Expected: `All checks passed!`

- [ ] **Step 3: Truth sync and demo check**

```bash
services/ml/.venv/Scripts/python.exe scripts/sync_truth.py --check
services/ml/.venv/Scripts/python.exe scripts/judge_demo_manifest.py check
```

Expected: `{"status": "ok", "mode": "check"}` and
`{"command": "check", "status": "ok"}` — the second now meaning current, not
merely self-consistent.

- [ ] **Step 4: Web**

```bash
cd apps/web && npm run type-check && npx vitest run && npm run build && cd ../..
```

Expected: all clean.

- [ ] **Step 5: Confirm the public figure changed**

```bash
services/ml/.venv/Scripts/python.exe -c "import json,io; print(json.load(io.open('apps/web/public/demo/result.json',encoding='utf-8'))['summary']['total_co2eq_kg'])"
```

Expected: `3798.38`.

The deployed site still serves 4748.95 until a Vercel deploy runs. Deploying is a
separate decision and is not part of this plan.

---

## What this plan does not do

- **No evaluation code.** Spec §12 step 2 forbids it before Task 5's document
  exists. `cameroon_eval.py`, `derive_cameroon_evidence.py` and the mass metrics
  are planned separately, from the layout Task 5 records.
- **No deploy.** Task 2 corrects the committed artefacts. Publishing them to
  `treeqcarbon.vercel.app` needs a Vercel deploy, and the live site also points at
  a dead Cloudflare tunnel (`tradition-exam-films-parties.trycloudflare.com`,
  which no longer resolves) pinned into the CSP. Fixing the deployment is its own
  piece of work.
- **No answer to who the user is.** The landing page's economic argument was built
  for the photograph path ADR 0007 removed. Step 7 of Task 4 removes the false
  input claim; it does not resolve the larger question recorded at the end of the
  spec.
