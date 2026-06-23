# Spec — Segmented .ply → 3D Viewer (real pipeline data)

> **Status:** Approved design, ready for implementation (do in a fresh session)
> **Date:** 2026-06-23 · **Topic:** ให้ 3D viewer โชว์ point cloud จริงจาก pipeline (ไม่ใช่แค่ demo tree)
> **Context:** ดู [AI_AGENT_CONTEXT.md](../../AI_AGENT_CONTEXT.md) ก่อนเริ่ม

## 1. Goal
ปิด loop: ML pipeline → **segmented .ply** (XYZ + class wood/leaf/ground) → ผู้ใช้ลากไฟล์ลง web viewer → เห็น point cloud จริงสีตาม class หมุน/ซูมได้ (ปัจจุบัน viewer แสดงแค่ synthetic demo tree)

## 2. Decisions (จาก brainstorming)
- Pipeline **export** segmented .ply เอง (ไม่ใช่อ่าน .ply ภายนอกอย่างเดียว)
- Loader ทำงาน **client-side** (file picker / drag-drop) — ไม่แตะ backend/Supabase
- LOD ใช้ **decimation** (ไม่ทำ octree/streaming)
- รองรับ PLY **binary_little_endian + ascii** (ไม่รับ big-endian)

## 3. Components (3 หน่วยอิสระ)

### 3.1 Python — `services/ml/pipeline/ply_export.py`
```
write_segmented_ply(points: np.ndarray (N,3), classes: np.ndarray (N,), path) -> Path
```
- เขียน **binary_little_endian PLY**: properties `float x, float y, float z, uchar class` (class: 0=wood, 1=leaf, 2=ground)
- wire เข้า `pipeline/main.py process_points(..., segmented_ply_out: str|None = None)`:
  ประกอบ class รายจุดของทั้ง plot — ground (จาก `ground_classification.classify_ground_array`) = 2; จุด non-ground แยก wood(0)/leaf(1) ด้วย segmenter เดียวกับที่ใช้อยู่ — แล้วเรียก `write_segmented_ply`
- เพิ่ม CLI flag `--segmented-ply PATH` ใน `process` command

### 3.2 TS — `apps/web/src/lib/ply-loader.ts`
```
parsePly(buffer: ArrayBuffer): { positions: Float32Array; classes: Uint8Array }
decimate(cloud, maxPoints = 200_000): { positions; classes }
```
- `parsePly`: อ่าน header → detect `format ascii|binary_little_endian`; หา property `x,y,z` (float) + `class` (uchar/uint8) ตามชื่อ; ถ้าไม่มี `class` → set ground (2) ทุกจุด
- `decimate`: ถ้า nPoints > maxPoints → สุ่ม uniform (seeded) ลดจุด คง index คู่ positions/classes ให้ตรง

### 3.3 UI — `apps/web/src/app/(dashboard)/dashboard/viewer/page.tsx`
- เพิ่ม `<input type="file" accept=".ply">` + drag-drop zone → `file.arrayBuffer()` → `parsePly` → `decimate` → `useState` → ส่งเข้า `<PointCloudViewer>` (มีอยู่แล้ว รับ positions+classes)
- แสดงจำนวนจุด + ปุ่ม "กลับไปตัวอย่าง (demo tree)" · default ยัง demo tree

## 4. Data flow
`python -m pipeline.main process --input plot.las --segmented-ply plot_seg.ply`
→ ผู้ใช้ลาก `plot_seg.ply` ลง `/dashboard/viewer`
→ parse + decimate ใน browser → `<PointCloudViewer>` render สี wood/leaf/ground

## 5. Testing (TDD)
- **Python (pytest):** `write_segmented_ply` roundtrip — เขียนแล้วอ่านกลับ (point count, มี property `class`, ค่าตรง); การประกอบ class รายจุดมีครบ 3 คลาส
- **TS (vitest):** `parsePly` ascii ตัวอย่างเล็ก → positions/classes ถูก; binary_le roundtrip (สร้าง buffer เอง); `decimate` ลดจำนวนจุดถูก + คงคู่ positions/classes; fallback ground เมื่อไม่มี class
- Full suite ต้องไม่ break ของเดิม (73 + ใหม่)

## 6. Out of scope (YAGNI)
ไม่ทำ: octree/potree streaming, backend upload/Supabase, binary_big_endian, RGB-per-point export (ใช้ class scalar พอ — viewer ลงสีเอง), per-tree separate clouds (export ทั้ง plot ก้อนเดียว)

## 7. Acceptance criteria
- [ ] `write_segmented_ply` + roundtrip test ผ่าน · `--segmented-ply` ใช้ได้
- [ ] `parsePly` (ascii+binary) + `decimate` + tests ผ่าน (vitest)
- [ ] viewer page โหลด .ply จริงผ่าน file picker → render สี wood/leaf/ground
- [ ] tsc + eslint + ruff clean · full suite ไม่ break

## 8. ไฟล์ที่จะแตะ
ใหม่: `pipeline/ply_export.py`, `tests/test_ply_export.py`, `apps/web/src/lib/ply-loader.ts`, `apps/web/src/lib/ply-loader.test.ts`
แก้: `pipeline/main.py` (process_points + CLI), `viewer/page.tsx`
