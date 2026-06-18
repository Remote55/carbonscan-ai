# Photogrammetry: ภาพถ่าย → Point Cloud (.ply)

แปลงรูปถ่ายต้นไม้ 30–50 รูป (จากภาคสนาม) → dense point cloud `.ply` ด้วย **COLMAP (SfM) + OpenMVS (MVS)** แล้วป้อนเข้า ML pipeline ต่อ

> ส่วนนี้คือ "ขั้นกลับมาจากภาคสนาม" ของ [FIELD_DATA_COLLECTION.md](FIELD_DATA_COLLECTION.md) — เก็บรูปยังไงดู doc นั้น

---

## 0. ภาพรวม flow

```
รูป 30-50 ใบ/ต้น  ──COLMAP──▶  sparse + undistorted  ──OpenMVS──▶  tree.ply
                                                                      │
                                                          python -m pipeline.main process
                                                                      ▼
                                                          DBH · Height · Carbon (JSON)
```

---

## 1. ติดตั้ง binary (ครั้งเดียว)

COLMAP + OpenMVS เป็น **โปรแกรมภายนอก** (ไม่ใช่ pip) — ต้องลงแยกแล้วให้อยู่ใน PATH

### Windows (ง่ายสุด — ใช้ prebuilt)
- **COLMAP:** ดาวน์โหลด zip จาก https://github.com/colmap/colmap/releases (เลือกตัว `-windows-cuda` ถ้ามี NVIDIA GPU, ไม่งั้น `-windows-no-cuda`) → แตกไฟล์ → เพิ่มโฟลเดอร์ลง PATH
- **OpenMVS:** prebuilt จาก https://github.com/cdcseacave/openMVS/releases → แตก → เพิ่ม PATH (ต้องมี `InterfaceCOLMAP.exe`, `DensifyPointCloud.exe`)

### ตรวจว่าลงครบ
```bash
cd services/ml
python -c "from photogrammetry.run import check_binaries; print(check_binaries())"
```
ควรเห็น path ของทั้ง 3 (`colmap`, `InterfaceCOLMAP`, `DensifyPointCloud`) ถ้าเป็น `None` = ยังไม่อยู่ใน PATH

> ไม่อยากลงในเครื่อง? รันบน **Google Colab** ได้ (`!apt install colmap`) — แต่ OpenMVS ต้อง build เอง; ทางเลือกง่ายกว่าคือใช้ COLMAP dense (`patch_match_stereo` + `stereo_fusion`) แทน OpenMVS

---

## 2. รัน

```bash
cd services/ml

# preview คำสั่งก่อน (ไม่ต้องมี binary) — เช็คว่า path ถูก
python -m photogrammetry.run --images path/to/tree01_photos --out tree01.ply --dry-run

# รันจริง (ต้องมี COLMAP + OpenMVS)
python -m photogrammetry.run --images path/to/tree01_photos --out tree01.ply
#   --no-gpu   ถ้าไม่มี NVIDIA GPU
#   --work-dir ระบุ scratch dir (default = temp)
```

ได้ `tree01.ply` แล้วป้อนเข้า pipeline:
```bash
python -m pipeline.main process --input tree01.ply --backend pointnet \
    --model woodleaf_pn2.pt --species "Tectona grandis" --output tree01_result.json
```

---

## 3. เคล็ดลับให้ reconstruct สำเร็จ

| ประเด็น | คำแนะนำ |
|---|---|
| จำนวนรูป | ≥ 30–50/ต้น (ระบบเตือนถ้า < 15) |
| overlap | รูปติดกันเหลื่อม 60–80% — เดินรอบถ่ายถี่ๆ |
| แสง/ลม | แสงสม่ำเสมอ (เมฆครึ้ม), ไม่มีลม (ใบไหว = พัง) |
| โฟกัส | คมทุกรูป ไม่เบลอ |
| ถ้า mapper ล้มเหลว (สร้าง sparse ไม่ได้) | รูป overlap น้อยไป/เบลอ/ลมแรง → ถ่ายใหม่ให้ถี่ขึ้น |

---

## 4. โครงสร้างโค้ด

| ไฟล์ | หน้าที่ |
|---|---|
| `photogrammetry/colmap_wrapper.py` | `find_images`, `build_sfm_commands`, `run_sfm` (COLMAP) |
| `photogrammetry/openmvs_wrapper.py` | `build_densify_commands`, `densify` (OpenMVS) |
| `photogrammetry/run.py` | orchestrator + CLI + `check_binaries` + `--dry-run` |
| `tests/test_photogrammetry.py` | unit tests (หา images + สร้างคำสั่ง) — รันได้แม้ไม่มี binary |

> command-builders เป็น pure functions (test ได้โดยไม่ต้องลง COLMAP); การรัน subprocess จริงต้องมี binary
