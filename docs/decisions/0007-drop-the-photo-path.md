# 0007 — Take input from a scanner only; drop photogrammetry and the mobile app

Date: 2026-08-09
Status: Accepted
Supersedes: [0004 — Dual-input architecture](0004-dual-input-architecture.md)

## Decision

This platform measures point clouds produced by a laser scanner: `.ply`, `.las`,
`.laz`. The path from phone photographs to a point cloud is removed, along with
the Flutter app whose purpose was to capture those photographs.

Removed:

- `services/ml/photogrammetry/` — COLMAP and OpenMVS wrappers, and the ArUco
  scale module written the same week
- `services/ml/scripts/photogrammetry_gate.py` and its tests
- `apps/mobile/` and `.github/workflows/ci-mobile.yml`
- `POST /api/v1/upload/photos`, which returned 501 with "TODO: implement"

## Why

Decision 0004 chose photogrammetry because the team had no LiDAR hardware. The
reasoning was about acquisition cost. It never established that the method
works.

Three things were true when this was decided:

1. **The gate had never passed, because it had never run.** The question it
   exists to answer — whether photographs of a real trunk yield enough points to
   fit a circle at 1.3 m — was open. `colmap`, `InterfaceCOLMAP` and
   `DensifyPointCloud` are not installed and `pycolmap` is not importable, so
   the gate reported BLOCKED at its first step. Dense reconstruction may need a
   GPU this project has decided not to buy.

2. **Scale had never been addressed at all.** SfM reconstructs shape, not size:
   two photo sets of one trunk produce clouds differing by an arbitrary factor,
   with identical reprojection error. Nothing in the package mentioned a marker,
   a reference length, or a control point. Every diameter it could have produced
   was a number with no unit. A marker module was written to close that gap and
   is removed with the rest of the path.

3. **The path that does work has a measured, unfixed error.** Against the 65
   trees in the Demol cohort that were weighed after felling, the shipped carbon
   configuration is **41.0% out with a +40.8% bias**. About 21 points of that is
   not knowing the wood density; the rest is Chave applied outside its stated
   domain.

Spending effort widening the front to a path whose physics is unverified, while
the working path is 41% out, is the wrong order. Depth before breadth.

## What this costs

Someone without a laser scanner cannot use the platform. That is a real
narrowing, and it is the point: the product now claims one thing it can do
rather than two things, one of which was never demonstrated.

## What it buys, immediately

Naming the species is now possible end to end — `POST /upload/analyze` takes a
`species` field, `GET /upload/species` lists what the pipeline knows, and the
viewer offers a picker. The pipeline has accepted a species since it was
written; nothing had ever passed one. On the reference cohort that replaces an
assumed density with a measured one and takes the carbon error from 41.0% to
20.0%.

An unknown species name is refused with 422 rather than falling back to the
default, because a silent fallback answers with a number that looks like it used
the species the caller asked for and is 40% out without saying so.

## What is now stale

These still describe the two-input architecture and have not been rewritten:
`AI_AGENT_CONTEXT.md`, `API.md`, `ARCHITECTURE.md`, `DATASET_REQUEST.md`,
`DATA_MODEL.md`, `DEPLOYMENT.md`, `DEVELOPMENT.md`. Read them against this
record. `CAPABILITY_MATRIX.md`, `PROJECT_SPEC.md` and `ml/PIPELINE.md` are
generated from `docs/evidence/core_demo_manifest.json` and were regenerated.

The `source_type` column still permits `'photogrammetry'` and `JobType` still
has the member. Both are left alone: rows written earlier may carry the value,
and rejecting them on read would break history to tidy an enum.

## Reversing this

Everything is in git. `git revert` the removal commit restores the wrappers, the
scale module, the gate and the app. The reasoning above is what would have to
change first — in particular, somebody photographing one real tree with a
tape-measured diameter and a marker in frame, and the gate reporting PASS.
