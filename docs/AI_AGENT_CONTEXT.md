# 🤖 AI Agent Context — CarbonScan AI (อ่านไฟล์นี้ก่อนเริ่มงาน)

> [!CAUTION]
> **Historical context — superseded 2026-07-16.** ห้ามใช้ไฟล์นี้เป็นสถานะปัจจุบันหรือแหล่งตัวเลขสำหรับรายงาน
> ให้ยึด `docs/evidence/core_demo_manifest.json`, `docs/PROJECT_SPEC.md` และ
> `docs/CAPABILITY_MATRIX.md`: `tlsep` = Implemented default, PointNet++ = Experimental/not promoted,
> Wan Wood/Leaf/Mean IoU = `0.418/0.808/0.613`, Demol DBH MAE = `1.1673846154 cm`,
> Species Classification = Stub, งาน WebSocket/GIS/Marketplace/production RunPod = Planned.

> **จุดประสงค์:** ให้ AI agent (context ใหม่) เข้าใจโปรเจค + สถานะล่าสุด + งานที่เหลือ ได้ทันทีจากไฟล์เดียว
> **อัปเดตล่าสุด:** 2026-06-18 (หลัง Sprint P1 — PR #15–#25 merged หมด)
> อ่านคู่กับ: [HANDOFF.md](HANDOFF.md) · [P1_SPRINT_PLAN.md](P1_SPRINT_PLAN.md) · [FIELD_DATA_COLLECTION.md](FIELD_DATA_COLLECTION.md) · `CLAUDE.md` (auto-load)

---

## 1. โปรเจคคืออะไร
**CarbonScan AI** — แพลตฟอร์มประเมินคาร์บอนต้นไม้: LiDAR/photogrammetry point cloud → AI wood-leaf segmentation → DBH/Height/Volume → carbon (TGO allometric) → B2B marketplace
- **แข่ง:** NSC 2026 หมวด 14 อุดมศึกษา · **ทีม:** 3 คน (ม.สงขลานครินทร์ หาดใหญ่)
- **Repo:** https://github.com/Remote55/carbonscan-ai · **Backend:** Supabase (Singapore)
- **Deadlines:** Proposal ผ่านแล้ว · **Final Report 17 ก.ค. 2569** · Pitching ~21 ส.ค.

## 2. สถานะล่าสุด (2026-06-18)
- ✅ **Proposal ผ่าน (P)** พร้อม feedback กรรมการ 4 ข้อ (ดู §6)
- ✅ **Sprint P1 — code/ML เสร็จเกือบหมด** (PR #15–#25 merged): tests 25→73
- 🟡 **เหลือ 2 อย่างหลัก:** (1) เก็บ field data ไม้ไทย (ของ user) (2) เอา fixes ไปใส่ **Word report จริง**

## 3. Repo workflow (สำคัญ — กัน conflict ซ้ำ)
- main มี branch protection (require PR, linear history, **auto-delete head branches เปิดแล้ว**)
- **1 PR = 1 branch แตกจาก main สด → squash-merge → branch ลบเอง** อย่า reuse branch เก่า (เคยเกิด squash-divergence conflict หลายรอบ)
- เริ่มงานใหม่เสมอ: `git checkout main && git pull && git checkout -b feat/...`
- commit ลงท้าย: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` · merge ผ่าน `gh pr merge N --squash --delete-branch --admin`

## 4. ทำอะไรไปแล้ว (Sprint P1, PR #15–#25)
| ด้าน | สถานะ | หลักฐาน |
|---|---|---|
| Proposal fixes (4 cons) | ✅ ใน `proposal/outline.md` | §7.2.6, §7.4.5, §12.1, fig14/15 |
| **G2 PointNet++** | ✅ เทรน + เทียบ + integrate | `services/ml/training/`, fig17 |
| **G3 Volume** | ✅ ปิดคำถาม (taper) | `experiment_g3_pointnet_volume.py` |
| **Pipeline orchestrator** | ✅ end-to-end | `pipeline/main.py` `process_points()` |
| **Photogrammetry** | ✅ photos→.ply | `photogrammetry/run.py` |
| **3D viewer** | ✅ scaffold | `apps/web/src/components/viewer/` |
| Docs sync + Final Report §7.2.5 | ✅ | ARCHITECTURE/README/outline |

## 5. ⚠️ KEY FINDINGS — ห้าม overclaim (ความซื่อสัตย์คือจุดแข็งในเวทีวิจัย)
- **PointNet++ IoU 0.978** = บน **synthetic held-out เท่านั้น** (train+test สังเคราะห์) → พิสูจน์ว่า model เรียนรู้ได้ **ยังไม่ใช่ตัวเลขบนไม้จริง** ต้องมี manual-labelled real test set
- **G3 sectional QSM ถูกพิสูจน์แล้วว่าใช้กับต้นมีกิ่งไม่ได้** (เทสต์ด้วย PointNet++ clean wood แล้วยังได้ 373% > taper 23%) — สาเหตุคือ algorithm (slice แนวนอนจับการกระจายกิ่ง) → **คง taper 18.8%** (ใน TLS literature range 10–20%) · full TreeQSM (branch-axis cylinders) = future work
- **DBH/Height MAE 1.17cm/0.54m** = validate จริงบน Demol 2021 Belgium (TLS, 65 ต้น) ✅
- ในเอกสารทุกที่ตัวเลขควรตรง: ต้นทุน 50,000–200,000 บาท · เวลา 10–15 นาที · server ~$15/เดือน

## 6. งานเหลือ #1 — Field Data (ของ user)
เก็บ 5–10 ต้น (สัก/ยางนา) ตาม [FIELD_DATA_COLLECTION.md](FIELD_DATA_COLLECTION.md): DBH (สายวัด) + ความสูง (clinometer) + GPS + photogrammetry 30–50 รูป/ต้น
- ปลดล็อก: `fig16_thai_parity.png` (parity ไม้ไทย) + IoU บนไม้จริง = หลักฐานเด็ดรอบ pitching
- เครื่องมือพร้อมแล้ว: `notebooks/validate_thai.py` (มี `--demo`), `photogrammetry/run.py`, template `data/field/`

## 7. งานเหลือ #2 — แก้ Word Report จริง (4 cons)
**สำคัญ:** report ที่ส่งคือ Word แยก (`เล่มโครงงานNSC_แก้ไขแล้ว.docx` — ทีมจริง ม.อ., 16 รูป) **ไม่ใช่ `outline.md` ตรงๆ** เช็คล่าสุด (18 มิ.ย.) พบว่า report ฉบับ "แก้ไขแล้ว" **ยังไม่ปิด 4 cons**: ไม่มีเลขอ้างอิง [1], ไม่มี Demol/Zenodo, ไม่มีหัวข้อ Data Sources/Citation Map/Async-UX

**เนื้อหาแก้พร้อมก็อปจาก `proposal/outline.md`:**
| กรรมการบอก | แก้ที่ (report) | เอาเนื้อหาจาก |
|---|---|---|
| 1. LiDAR data ไม่อ้างอิงชัด | หัวข้อผลทดสอบ/แหล่งข้อมูล | outline §7.2.6 + Demol DOI/Zenodo + fix เลข Demol→[25] |
| 2. ประมวลผลนาน — UX | หัวข้อรายละเอียดโปรแกรม | outline §7.4.5 + ใส่รูป `fig15_processing_ux.png` |
| 3. system design ด้วย diagram | หัวข้อภาพรวมระบบ | ใส่รูป `fig14_system_simplified.png` |
| 4. ระบุ ref อ้างในส่วนใด | ท้ายบรรณานุกรม | outline §12.1 Citation Map + ใช้เลข [1]–[29] |
> + ใส่ผลใหม่เป็นจุดแข็ง: PointNet++ IoU 0.978 vs PCA 0.769 (`fig17`) + pipeline end-to-end
> รูปทั้งหมดอยู่ใน `docs/proposal/figures/` · **อ่าน .docx ด้วย python-docx (อย่าใช้ PDF — ฟอนต์ไทยใน PDF extract เพี้ยน)**

## 8. แผนที่ไฟล์สำคัญ
- **ML pipeline:** `services/ml/pipeline/` (main.py orchestrator, ground/height/chm/tree_segmentation/wood_leaf_separation/qsm/allometric/synthetic)
- **G2 training:** `services/ml/training/` (woodleaf_dataset, pointnet2_seg, train_woodleaf, eval_woodleaf, metrics) · model `woodleaf_pn2.pt` (gitignored)
- **Photogrammetry:** `services/ml/photogrammetry/` (colmap_wrapper, openmvs_wrapper, run)
- **Validation scripts:** `services/ml/notebooks/` (validate_belgium, validate_thai, compare_woodleaf, experiment_g3_pointnet_volume, make_diagrams)
- **Web:** `apps/web/src/` (components/viewer/, lib/demo-pointcloud.ts, app/(dashboard)/dashboard/viewer)
- **Backend:** `services/api/app/` (FastAPI) · **Proposal:** `proposal/outline.md` + `proposal/references.md`

## 9. วิธีรัน (ใช้ venv: `services/ml/.venv/Scripts/python.exe`)
```bash
cd services/ml
.venv/Scripts/python.exe -m pytest --no-cov -q          # 73 tests
.venv/Scripts/python.exe -m ruff check pipeline training tests notebooks photogrammetry
.venv/Scripts/python.exe -m pipeline.main process --input plot.ply --backend pointnet --model woodleaf_pn2.pt
.venv/Scripts/python.exe notebooks/validate_thai.py --demo
.venv/Scripts/python.exe -m photogrammetry.run --images photos/ --out tree.ply --dry-run
# web: cd apps/web && npx vitest run ; npx tsc --noEmit ; npx eslint src/...
# Colab train: ดู services/ml/training/README.md
```

## 10. Gotchas / สภาพแวดล้อม
- **Thai PDF extract เพี้ยน** (custom font encoding) → ใช้ `.docx` + `python-docx` แทน · `Read` tool render PDF ไม่ได้ (pdftoppm หาย)
- **Windows console = cp874** → ตั้ง `PYTHONIOENCODING=utf-8` เวลารัน script ที่ print ✓/³/m³/ไทย (ไม่งั้น UnicodeEncodeError) · เขียน print ใน script ให้ ASCII-safe
- **torch (CPU) ติดตั้งใน `services/ml/.venv` แล้ว** (local) แต่ gitignored + CI ไม่มี → tests ที่ต้อง torch ใช้ `pytest.importorskip("torch")` / skip ถ้าไม่มีโมเดล
- **api venv ไม่มี pytest/ruff** (รัน api tests ที่เครื่องนี้ไม่ได้) · data point clouds ใหญ่ + gitignored (`services/ml/data/`)
- `*.pt` gitignored — โมเดลไป Hugging Face/Release ไม่ commit

## 11. Conventions
- **TDD** (skill `superpowers:test-driven-development`): test ก่อน → ดู fail → implement
- **ตอบเป็นไทย** (technical terms EN ได้) · โฟกัส "ทำให้กรรมการ NSC ว้าว" + ซื่อสัตย์ ไม่ overclaim
- รายงานผลตามจริง (ถ้า test fail บอก, negative result = จุดแข็ง)
