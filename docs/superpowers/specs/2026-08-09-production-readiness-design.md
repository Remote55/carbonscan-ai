# TreeQ Carbon — from demo to working product

**Date:** 2026-08-09 · **Status:** design, awaiting review

The competition is over. The goal is no longer a rehearsed ten minutes; it is a
tool a stranger can use. This document records what four parallel audits found,
what has already been fixed, and what the remaining work is in the order it
should be done.

Every claim here is anchored to a file, a line, or a number that was measured.
Where something could not be determined, it says so.

---

## 1. What the audits changed about our own understanding

Three things this project believed — and that I repeated to the team — turned
out to be wrong. They are listed first because they invalidate work that was
already planned.

### 1.1 Wood IoU 0.418 does not describe the shipped separation

0.418 is the trained PointNet++ candidate's score on the Wan 2021 held-out
split, and `docs/PROJECT_SPEC.md:15` records that the same split also selected
its best epoch — so it is selection-contaminated.

**tlsep, the default that actually runs, scores macro wood IoU 0.196** on the
external cohort it never saw
(`docs/evidence/pointnet_independent_eval/result.json`,
`/baseline/external_segmentation/macro/wood_iou`).

The landing page quoted 0.418 in a section headed ความแม่นยำ. Fixed in `ade3427`.

### 1.2 "Volume is 18.77% wrong because branch volume is zero" — and fixing that alone makes it worse

Measured from the harvest columns of all 65 Demol trees:

| term | value |
|---|---|
| branch share of true whole-tree volume | 30.29% (median 28.91, range 8.07–55.59) |
| corroboration via `Fresh_mass_crown/Fresh_mass_total` | 30.84% |
| true **stem** form factor for this cohort | 0.4028 |
| true **whole-tree** form factor | 0.5865 |
| shipped constant `qsm.py:27` | **0.50** |

The shipped 0.50 sits between the two, so an unjustified constant is silently
cancelling about 56% of the branch omission:

```
branches omitted                    −30.29 %
form factor 0.50 vs true 0.4028     +16.85 %
                                    ───────
net bias                            −13.44 %
```

Consequence, measured:

| counterfactual | MAPE |
|---|---|
| current pipeline | 18.77% |
| **+ correct branch volume, form factor untouched** | **21.57%** |
| re-derived single form factor 0.571 | **~9.7%** |

So the planned "model branch volume" task would have made accuracy worse. The
cheap, high-leverage change is re-deriving the form factor — with the caveat
that 0.571 is fitted in-sample on 65 temperate trees and entrenches the
conceptual error of calling a whole-tree estimate a stem volume.

The principled version has **no predictable gain**: the existing sectional path
scores **+920% MAPE** on real TLS wood points.

### 1.3 The volume number never reaches the carbon number

`main.py:203-205` computes carbon from DBH and height via Chave.
`allometric.calculate_carbon_from_volume` has **zero callers**. The 18.77%
headline propagates nowhere the user can see.

**What does drive carbon error**, never previously quantified:

| path | AGB MAPE vs destructive truth | bias |
|---|---|---|
| production default (Chave, ρ=600, pipeline DBH+H) | **37.28%** | +36.88% |
| same, with per-tree true wood density | **18.28%** | +15.43% |

`allometric.py:191` hardcodes `wood_density = 600.0`; the cohort's true mean is
508. Quadrature of DBH and height error predicts only 7.82% of that 37.28% —
the rest is model and density bias.

And four of five entries in `species_db.csv` diverge from Chave by
**1.67×–3.05×** at matched density, with the divergence growing with diameter
(their exponent b = 2.28–2.42 against Chave's effective 1.952). That signature
means both coefficients are off, not just scale — a unit error or a
transcription from a different functional form. `Afzelia` cites its own source
as "Chave 2014 adjusted" while returning 2.0–2.5× Chave.

**Nothing about carbon should be claimed until that is resolved.**

---

## 2. Already fixed

| Ref | Defect | Commit |
|---|---|---|
| — | Segmented cloud 404s under >1 uvicorn worker; then a mid-write read race | `a50f27b` |
| — | Landing page had no link to the evidence page; 3 tests had said so since PR #73 | `aa87c24` |
| — | Analyse button dead for every visitor; no sample file; no plot-vs-single-tree warning; DBH printed to 11 significant figures | `0711234` |
| 1.1 | Separation figure was the candidate's contaminated number | `ade3427` |
| S2 | 200-byte file could request 75 GB — `ground_classification` sized its grid from map extent, not point count | `0a1e2cc` |
| S1 | Any signed-up user could set their own role to `admin`; "Auditor" was offered in a dropdown and could verify any tree | `c85e0ef` |
| S5 | Non-ASCII token header raised an unhandled 500 from the pre-auth path | `6597395` |

Suites after: **ML 509**, **API 70**, **web 170 unit + 50 browser**, type-check,
lint and build clean.

---

## 3. Remaining work, in order

The ordering rule is: correctness of what we already claim, then the ability for
anyone to use it, then new capability.

### Phase A — stop claiming what is not true

**A1. Settle the species coefficients.** Retrieve Tsutsumi 1983, Ogawa 1965 and
the TGO 2017 guideline; verify units and functional form for all five entries in
`species_db.csv`. This is a correctness bug, not tuning: if they are wrong,
every carbon figure is wrong by up to 3×. Gain is unquantifiable in advance and
that is the point — it must be settled before any carbon claim stands.

**A2. Replace the hardcoded wood density.** `allometric.py:191`. Measured gain
on Demol: 37.28% → 18.28% AGB MAPE. Requires species to be known, which today
means user-supplied.

**A3. Re-derive the form factor, and say what it is.** `qsm.py:27`. Either fit
it honestly against whole-tree truth and rename the field, or model branches
properly and re-fit — but not one without the other (§1.2).

**A4. Make RANSAC converge or report its spread.** `qsm.py:47`. Per-tree DBH
varies **1.053 cm** across seeds — comparable to the 1.167 cm MAE itself, ≈7%
of per-tree carbon. Raising iterations 200→5000 barely moves it, so the
estimator itself needs changing, not its budget. Production seeds on `tree_id`
(`main.py:197`), so a tree's DBH changes when watershed relabels it.

**A5. Validate stages 1–4, or stop implying they are validated.**
`validate_belgium.py:94-98` substitutes `z -= z.min()` for ground
classification, height normalisation, CHM and watershed. The headline accuracy
is stages 5–6 only, on pre-cleaned isolated trees. Datum sensitivity is real:
+0.10 m of breast-height error takes DBH MAPE from 3.79% to 8.27%.

### Phase B — let anyone use it

**B1. Decide what provenance means in a container.** `main.py:252-253` shells
out to `git` with `check=True` on every run; in an image there is no `.git` and
often no `git`, and it fails *after* the compute. `metadata.git_commit` is part
of the contract the frontend displays. Bake the commit at build time.

**B2. Close the anonymous-upload hole before any URL is public.** With
`TREEQ_DEMO_MODE=false` the guard is a pass-through (`demo_security.py:82-84`),
`/upload/analyze` has no auth, the point-count cap is demo-only, the size limit
defaults to 500 MB, ingestion buffers ~2×, and the subprocess timeout is 600 s.
One anonymous request can hold the instance for ten minutes.

**B3. Build an image that can actually serve a request.**
`services/api/Dockerfile:53-55` ships the API without the ML pipeline, so every
analyse call fails. Minimal merged image ≈0.9–1.2 GB; `open3d` is unavoidable
because `.ply` loading goes through it. **No GPU is needed** — the production
path is tlsep, pure numpy and cKDTree, and torch is not a base dependency. The
`RUNPOD_*` settings are dead.

**B4. Deploy.** Hugging Face Spaces (Docker) is the strongest genuinely-free
fit: 16 GB RAM, no card, sleeps after ~48 h rather than 15 minutes. Railway or
Fly at roughly $5/month if a stable hostname matters more.

**B5. Retire or keep the tunnel handoff deliberately.**
`demo-runtime.ts:34-43` accepts only `*.trycloudflare.com` or loopback, so a
permanent backend cannot arrive through it. Keeping both paths doubles the auth
surface; a permanent `NEXT_PUBLIC_DEMO_TOKEN` is a public standing credential.

**B6. Fix async job file leakage.** `job_input.py:24-28` writes uploads that
nothing ever deletes.

### Phase C — complete the process (the chosen direction)

Photos → point cloud, so someone without a laser scanner can measure a tree.

The wrappers exist (`services/ml/photogrammetry/`, COLMAP + OpenMVS, dry-run
tested). Three things are missing, and the first is the real one.

**C1. Metric scale.** There is no mention of scale, marker, GCP or reference
length anywhere in the package. SfM output is scale-free, so a cloud built from
photos has arbitrary units and any DBH from it is meaningless. `cv2.aruco` is
already available in the ML venv — a printed marker of known size is the
cheapest workable answer and doubles as a self-check.

**C2. Prove the physics before building the plumbing.** Whether photogrammetry
of a real trunk yields enough points to fit a circle at 1.3 m is **unknown**.
`pycolmap` installs as a wheel, so sparse SfM needs no external binary; dense
reconstruction needs CUDA or an external binary and may not be available at all.

> **Gate:** photograph one real tree whose DBH is tape-measured, with a marker
> in frame; run it through; compare. If the error exceeds ~10%, or there are too
> few points to fit a circle, stop and report that this path needs dense
> reconstruction — do not build the rest first.

**C3. A reusable single-tree measurement path.** Photos capture one tree, and
the plot pipeline is wrong for one tree by roughly 4×. The recipe exists inside
`demol_eval.py` but there is no `measure_single_tree()` to call. Note this also
implies the async job path, since COLMAP takes minutes.

### Phase D — the quality floor

**D1. Pin the arithmetic, not the orchestration.** The evidence tripwire pins
`sha256(pipeline/main.py)`; `allometric.py`, `qsm.py`, `wood_leaf_separation.py`
and the rest are unpinned. Changing `CHAVE_2014_A` from 0.0673 to 0.5 leaves it
green. Its stated backstop is also false: `run_core_demo.py` compares run 1
against run 2 of the same code — determinism, never regression. There is no
pinned expected output hash anywhere. *(I asserted that backstop was real in a
commit message. It was not.)*

**D2. Replace tests that assert on their own mocks.**
`test_upload_analyze.py:121` stubs the pipeline then asserts the stub's own
number. `test_allometric.py:78-94` re-derives every expectation from the
implementation's intermediates. `test_chave_zero_inputs_handled` cannot fail.
`test_segmented_cloud_endpoint.py:25-30` sends no token and asserts 200.

**D3. Cover what has no tests.** Height normalisation (62%), tree segmentation,
CHM, `pipeline_runner`, and the web `middleware()` function — whose fail-open at
`middleware.ts:45-47` makes every `/dashboard/*` route public if an env var is
missing, with no test and no alarm.

**D4. Put Playwright in CI.** `ci-web.yml` runs vitest only, with
`--passWithNoTests`. The 50 browser tests are a local ritual. No workflow builds
a Docker image either.

### Phase E — product surface

Ranked from the product audit: PLY header count is trusted and fabricates a
point total; the viewer enforces none of the limits the site advertises; live
results are labelled "ผ่านการยืนยันความสมบูรณ์" with no manifest to verify; a
failed email-confirmation link dead-ends with no resend and no forgot-password;
the 3D canvas has no role, label or tab stop, so the centrepiece does not exist
for a screen reader; `/demo` downloads 3.54 MB of PLY that is hashed and never
rendered; `logo.png` is 1.28 MB served at 32 px.

**The mobile app is a static mockup** — no network call anywhere, camera is a
placeholder string, results screen hardcodes fake stage states, and its hero
reads "แปลงต้นไม้ของคุณ เป็นรายได้" while every web surface disclaims exactly
that. Decide whether to finish it or retire it; leaving it is the worst option.

---

## 4. Two things only a person can do

1. **Check Supabase → Authentication → URL Configuration.**
   `NEXT_PUBLIC_SITE_URL` is not set in production and is absent from
   `.env.example`, so `auth.ts:35-38` falls back to `window.location.origin` and
   Supabase may substitute its project Site URL — `localhost:3000` on a fresh
   project. If that is wrong, **no new user can ever confirm an account**, and
   because a failed callback dead-ends silently, nobody would find out.

2. **Rotate the service_role key.** `docs/HANDOFF.md:154` flagged it months ago
   as exposed in chat and it is still in place. It bypasses RLS entirely, so it
   is the master override for everything §2 just fixed. Verified: it was never
   committed — exposure is the dev machine plus wherever that chat went.

Also worth one statement: run step 4 of
`services/api/scripts/remediate_escalated_roles.sql` to find out whether the RLS
script was ever applied to the live project. That decides whether §2's S1 was
exploitable or merely possible.

---

## 5. Open questions this design does not answer

- Whether the species coefficients are wrong or merely surprising (no access to
  the primary sources).
- The magnitude of stage 1–4 error (no plot-level cloud with per-tree truth
  exists in the repo).
- Accuracy in the intended domain — all destructive validation is four
  temperate European species; no Thai or tropical destructive dataset exists.
- Whether the 30.29% branch fraction transfers to tropical broadleaf.
- Whether dense reconstruction is reachable without a GPU (decides C2).
