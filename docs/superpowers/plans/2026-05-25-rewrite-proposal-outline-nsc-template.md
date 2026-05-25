# Rewrite proposal/outline.md to NSC 2026 Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `proposal/outline.md` so its structure matches the NSC 2026 Booklet Section 7 sub-template (7.1–7.5) and reflects the v2 pivot (LiDAR-primary) + Belgium validation results.

**Architecture:** Single-file rewrite. Keep existing strong content (Abstract, Background, Objectives, Timeline, Outcomes, Risks, Budget, References) but restructure the technical sections (5, 6) into a new top-level "Section 7: รายละเอียดของการพัฒนา" with sub-sections 7.1–7.5 exactly as the NSC booklet requires. Add Belgium validation numbers and citations that are missing.

**Tech Stack:** Markdown only. Source content already exists in `docs/proposal/SYSTEM_OVERVIEW.md`, `docs/learning/12-ml-step8-allometric.md`, `docs/learning/13-ml-validation.md` — synthesize from these.

---

## Context

Reviewing the current `proposal/outline.md` against the NSC 2026 Booklet (page 25–26, Section 7) revealed five structural gaps:

1. **No Section 7** — content is scattered across Sections 5 (Scope) and 6 (Methodology). NSC requires a top-level Section 7 with explicit sub-headings 7.1, 7.2, 7.3, 7.4, 7.5.
2. **Abstract still v1** — describes Mobile photogrammetry as the primary path. Advisor feedback (May 24) flagged this as unrealistic; team pivoted to LiDAR-primary on the same day.
3. **No Belgium validation numbers** in the proposal text — even though we have 65-tree results (DBH MAE 1.17 cm, Height MAE 0.54 m) that are the strongest "proof of work" we can show.
4. **Software Specification missing** — NSC 7.4 wants explicit Input/Output Spec, Functional Spec, and Software Design sub-sections. Currently zero coverage.
5. **Citations incomplete** — Demol 2021, Tsutsumi 1983, Ogawa 1965, Yiping 2010, Chiarucci 2014 are referenced in code but absent from the proposal reference list.

Deadline pressure: Proposal must reach advisor for review-round-2 by 26 May 2569 (~24 hours from now) so they can sign by 27–28 May before SIMs upload on 29 May 17:00.

---

## File Structure

**Modify:**
- `proposal/outline.md` — full rewrite of Sections 5, 6, 11; insert new Section 7

**Reference (read-only sources):**
- `docs/proposal/SYSTEM_OVERVIEW.md` — already has v2 pivot positioning + Belgium results
- `docs/learning/12-ml-step8-allometric.md` — allometric formulas with worked examples
- `docs/learning/13-ml-validation.md` — Belgium validation numbers
- `docs/learning/21-references-glossary.md` — full bibliography with DOIs

**Outputs:**
- One updated `outline.md` (~600-700 lines, was 513)
- One commit on `feat/proposal-nsc-template` branch (or `main` if signoffs cleared)

---

## Tasks

### Task 1: Add new "Section 7" skeleton with NSC sub-headings

**Files:**
- Modify: `proposal/outline.md` — insert new section between current Section 6 and Section 7 (the existing Timeline section will renumber to 8, and so on)

- [ ] **Step 1: Insert Section 7 header + 5 sub-section placeholders**

After the existing "ส่วนที่ 6: วิธีดำเนินการ" block ends (line ~280), insert:

```markdown
---

## ส่วนที่ 7: รายละเอียดของการพัฒนา (Development Details)

> หมายเหตุ: หัวข้อย่อยใน Section นี้ตรงตาม template ของ NSC 2026 Booklet (หน้า 25-26)

### 7.1 เนื้อเรื่องย่อ (Story Board)
*(เนื้อหาในขั้นต่อไป)*

### 7.2 เทคนิคหรือเทคโนโลยีที่ใช้
*(เนื้อหาในขั้นต่อไป)*

### 7.3 เครื่องมือที่ใช้ในการพัฒนา
*(เนื้อหาในขั้นต่อไป)*

### 7.4 รายละเอียดโปรแกรมที่จะพัฒนา (Software Specification)
*(เนื้อหาในขั้นต่อไป)*

### 7.5 ขอบเขตและข้อจำกัดของโปรแกรมที่พัฒนา
*(เนื้อหาในขั้นต่อไป)*

---
```

- [ ] **Step 2: Renumber downstream sections**

Bump current sections 7→8 (Timeline), 8→9 (Outcomes), 9→10 (Risks), 10→11 (Budget), 11→12 (References), 12→13 (Appendices). Update the master "Checklist ก่อนส่ง" cross-references.

---

### Task 2: Fill Section 7.1 (Story Board)

**Files:**
- Modify: `proposal/outline.md` — replace the 7.1 placeholder

- [ ] **Step 1: Write 2-persona narrative + figure references**

Two perspectives:
- เกษตรกร: เปิด mobile → scan → ได้รายได้
- โรงงาน: เปิด web → browse marketplace → ซื้อ carbon credit

Reference figures (already exist in `docs/proposal/figures/`):
- `fig09_architecture.png` (system overview)
- `fig10_user_flow.png` (end-to-end journey)
- `fig01_raw_point_cloud.png` (data input)
- `fig06_wood_leaf.png` (AI segmentation result)

Cite theoretical foundations: PointNet++ (Qi 2017), TGO Allometric (TGO 2017), CSF (Zhang 2016).

---

### Task 3: Fill Section 7.2 (Techniques / Technologies)

**Files:**
- Modify: `proposal/outline.md`

- [ ] **Step 1: Re-use content from existing Section 6.2 (ML Pipeline 8 steps) but DEEPEN each step**

For each step, add:
- Algorithm name
- Data structures (KD-tree, raster grid, eigenvalue matrix, etc.)
- Key parameters (e.g., grid_resolution=1m, k_neighbors=15, RANSAC iterations=200)
- Citation

- [ ] **Step 2: Insert Belgium validation results as Section 7.2.9**

Add `7.2.9 — Preliminary Validation Results (Demol et al. 2021)` with the table:

| Metric | Mean Error | MAE | RMSE | Literature Range |
|---|---|---|---|---|
| DBH | 3.8% | 1.17 cm | 2.07 cm | 1-3 cm ✓ |
| Tree Height | 2.6% | 0.54 m | 0.76 m | 0.5-1.5 m ✓ |
| Volume (taper) | 18.8% | 0.20 m³ | 0.28 m³ | Phase 2 → 5-10% |

Reference `fig11_belgium_dbh_parity.png`, `fig12_belgium_height_parity.png`, `fig13_belgium_volume_parity.png`.

---

### Task 4: Fill Section 7.3 (Tools)

**Files:**
- Modify: `proposal/outline.md`

- [ ] **Step 1: Split current Tech Stack into 3 tables**

Reorganize current Section 6.4 into:

```
7.3.1 ภาษาโปรแกรมที่ใช้: Python 3.11, TypeScript 5, Dart 3.12, SQL
7.3.2 Frameworks + Libraries: (table — Next.js, Flutter, FastAPI, PyTorch, Open3D, ...)
7.3.3 Development Tools: (table — Git, GitHub, VS Code, Docker, pnpm, poetry, Jupyter, RunPod, Vercel, Railway, Supabase, Sentry)
```

---

### Task 5: Fill Section 7.4 (Software Specification)

**Files:**
- Modify: `proposal/outline.md`

- [ ] **Step 1: Write 7.4.1 Input Specification**

Table format:

| Input | Format | Source | Constraints |
|---|---|---|---|
| LiDAR file | `.las` / `.laz` (ASPRS) | TLS / Drone scanner | ≤ 500 MB |
| Mobile photos | JPG (30-50 ภาพ) + GPS EXIF | smartphone camera | 1920×1080 min |
| Plot polygon | GeoJSON / WKT | user-drawn or imported | WGS84 (SRID 4326) |
| Existing CSV inventory | CSV | TGO / forestry department | UTF-8, has tree_id + species |

- [ ] **Step 2: Write 7.4.2 Output Specification**

```
JSON per tree: {tree_id, species_sci, dbh_cm, height_m, volume_m3, biomass_kg, carbon_kg, co2eq_kg, location: {lat, lon, alt}}
PDF certificate: A4, Thai+English, TGO-aligned format, QR verify code
3D PLY: segmented point cloud with wood/leaf/ground class colors
CSV summary: per-plot aggregate (n_trees, total_carbon_kg, total_co2eq_kg, by-species breakdown)
```

- [ ] **Step 3: Write 7.4.3 Functional Specification (10 features)**

Numbered list of user-facing functions:
1. Auth (signup/login via Supabase)
2. LiDAR file upload (chunked, resumable, tus protocol)
3. Mobile photo capture (camera-only, GPS-embedded EXIF)
4. Pipeline job dispatch + WebSocket progress
5. 3D Point Cloud Viewer (Three.js + R3F)
6. GIS Map view (Leaflet + PostGIS spatial queries)
7. Per-tree results dashboard (DBH/H/V/Carbon)
8. Marketplace browsing + filtering
9. Carbon credit checkout (mock payment for NSC)
10. PDF certificate generation + download

- [ ] **Step 4: Write 7.4.4 Software Design (Architecture)**

Reference existing `fig09_architecture.png` (4-layer diagram). Describe each layer briefly. Add module map:

```
apps/web/         Next.js 14 frontend
apps/mobile/      Flutter mobile
services/api/     FastAPI backend
services/ml/      ML pipeline (Python)
packages/         shared types + design tokens
```

Add data model summary (link to `docs/DATA_MODEL.md`).

---

### Task 6: Fill Section 7.5 (Scope and Limitations)

**Files:**
- Modify: `proposal/outline.md`

- [ ] **Step 1: Copy/move existing Section 5 content into 7.5**

Tables for:
- 7.5.1 In-scope (Prototype)
- 7.5.2 Out-of-scope
- 7.5.3 Constraints (team size, timeline, budget)
- 7.5.4 Assumptions (internet speed, Android version, dataset access)

Optionally: delete old Section 5 to avoid duplication, OR keep Section 5 as a short "executive summary" pointing to 7.5 for details.

---

### Task 7: Pivot Abstract + Background to v2 LiDAR-primary

**Files:**
- Modify: `proposal/outline.md` — current lines 64-72 (Abstract) and 78-120 (Background)

- [ ] **Step 1: Rewrite Abstract**

Change from "Mobile + Web dashboard" framing to:

> CarbonScan AI = software platform between **LiDAR Point Cloud** ↔ **Carbon Credit Marketplace**
>
> Primary input: LiDAR (.las/.laz) from TLS/Drone scanners
> Secondary input: Mobile photogrammetry (for smallholders < 1 rai)
> 5 unique differentiators vs existing LiDAR services: Thai-localized, end-to-end pipeline, B2B marketplace, multi-temporal Additionality, anti-fraud verification

Keep target accuracy claims (DBH MAE ≤ 5 cm, Wood-Leaf IoU ≥ 0.70) but ADD already-achieved: "DBH MAE = 1.17 cm on Demol 2021 Belgium dataset".

- [ ] **Step 2: Update Section 3.5 (Research Gap)**

Reframe gap as: "missing software layer in Thai carbon market" (not "missing mobile-friendly tools").

---

### Task 8: Update References (citations + DOIs)

**Files:**
- Modify: `proposal/outline.md` — Section 11 → renumbered to 12

- [ ] **Step 1: Add 5 missing critical citations**

Insert at appropriate numbers:

```
Demol, M. et al. 2021. Estimating forest above-ground biomass with TLS — current status and future directions. Trees 35, 671-685. DOI: 10.1007/s00468-020-02067-7
Tsutsumi, T. et al. 1983. Forest biomass and productivity in dry evergreen forests, Thailand. Japanese Journal of Ecology, 33(2), 213-227.
Ogawa, H. et al. 1965. Comparative ecological study on three main types of forest vegetation in Thailand. Nature & Life in SE Asia, 4, 49-80.
Yiping, L. et al. 2010. Bamboo and climate change mitigation: Comparative analysis of carbon sequestration. INBAR Technical Report 32.
Chiarucci, A. et al. 2014. Biomass estimation in rubber plantations using allometric models. Forest Ecology and Management, 318, 220-228.
```

- [ ] **Step 2: Add DOIs to existing citations**

Use `docs/learning/21-references-glossary.md` as source-of-truth for DOI links.

---

### Task 9: Self-Review + Final Polish

**Files:**
- Modify: `proposal/outline.md`

- [ ] **Step 1: Check the Checklist ก่อนส่ง section**

Verify the existing checklist (lines ~483-512) still matches the new structure. Update any references to "Section 6.X" that now point to "Section 7.X".

- [ ] **Step 2: Check figure references**

Confirm each figure name in the markdown matches an actual file in `docs/proposal/figures/`. List of expected figures:
- fig01_raw_point_cloud.png
- fig02_ground_classification.png
- fig03_height_normalization.png
- fig04_chm.png
- fig05_tree_segmentation.png
- fig06_wood_leaf.png
- fig07_carbon_bars.png
- fig08_accuracy.png
- fig09_architecture.png
- fig10_user_flow.png
- fig11_belgium_dbh_parity.png
- fig12_belgium_height_parity.png
- fig13_belgium_volume_parity.png

- [ ] **Step 3: Spell-check Thai content**

Manual scan for typos in restructured sections.

---

### Task 10: Commit + Push

**Files:**
- Commit: `proposal/outline.md`

- [ ] **Step 1: Stage and commit**

```bash
cd D:/Project_Carbon
git add proposal/outline.md docs/superpowers/plans/2026-05-25-rewrite-proposal-outline-nsc-template.md
git commit -m "docs(proposal): rewrite outline.md to NSC 2026 Section 7 template

- Add new Section 7 with sub-sections 7.1-7.5 matching NSC booklet
- Pivot Abstract + Background to v2 LiDAR-primary positioning
- Insert Belgium validation results (Demol 2021, 65 trees, MAE 1.17 cm DBH)
- Add Software Specification (Input/Output/Functional/Design) — was missing
- Move Scope content into 7.5
- Add 5 missing citations + DOIs to existing references

Closes the structural gaps blocking advisor review round 2."
```

- [ ] **Step 2: Push (decide branch first)**

If feat/sprint0-foundations PR #12 has been merged: push to main (or a new branch + PR). Otherwise: create new branch `docs/proposal-nsc-template-rewrite` to keep PR #12 unblocked.

---

## Self-Review

**Spec coverage:** Each NSC Section 7 sub-heading has a dedicated task (Tasks 2, 3, 4, 5, 6). Pivot to v2 (Task 7) and citations (Task 8) close the non-structural gaps. ✓

**Placeholder scan:** No TBDs, all content sources cited. The "fill from existing source" pattern is intentional — we already have the content in `docs/learning/` and `docs/proposal/SYSTEM_OVERVIEW.md`. ✓

**Type consistency:** Section numbering 7.1–7.5 used consistently. Figure names match `docs/proposal/figures/` exactly. Citation format uses author-year-DOI pattern throughout. ✓
