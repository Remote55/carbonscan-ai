# ADR 0004: Dual-Input Architecture (LAS + Photogrammetry)

- **Status:** Accepted
- **Date:** 2026-05-20
- **Deciders:** User (Team Lead)

---

## Context

ตามที่ [ADR 0002](0002-no-iphone-lidar.md) ตัดสินใจไม่ใช้ iPhone LiDAR เราต้องการให้ Platform เปิดรับข้อมูล input จากหลายแหล่ง:

1. **Auditor / Researcher** มีไฟล์ `.las/.laz` อยู่แล้ว (จาก TLS, drone LiDAR)
2. **Community / Farmer** มีแค่มือถือธรรมดา ต้องการสแกนต้นไม้

ถ้าทำ pipeline แยกกัน 2 อันจะซับซ้อน → ทำ unified pipeline ที่รับ input ได้ทั้งสองแบบ

---

## Decision

**Single ML Pipeline** ที่ output Point Cloud (`.ply` format) ก่อนเข้า Wood-Leaf Segmentation

ทุก input convert มาเป็น **Point Cloud format เดียว** ก่อน → ใช้ pipeline เดียวกัน

```
Input 1: .las/.laz (Auditor)
                          ┐
Input 2: Photos (Mobile)  ┤ ─── unified pipeline ───→ Carbon JSON
         │                │
         ▼                │
    COLMAP + OpenMVS      │
         │                │
         ▼                │
    .ply file ────────────┘
```

---

## Architecture Detail

### Path A: LAS Upload (Auditor)
```
1. User uploads .las/.laz via Web Dashboard
2. API → Supabase Storage
3. API → Job Queue (type: 'las_upload')
4. GPU Worker pulls job
5. Worker: laspy.read() → numpy array → pipeline.main()
```

### Path B: Photo Upload (Mobile/Community)
```
1. App uploads 30-50 photos + GPS via Mobile/Web
2. API → Supabase Storage
3. API → Job Queue (type: 'photogrammetry')
4. Photogrammetry Worker pulls job
   a. Run COLMAP (SfM, ~2 min)
   b. Run OpenMVS (Dense, ~3 min)
   c. Output: .ply file
5. After photogrammetry done → API auto-creates 2nd job (type: 'las_upload')
6. GPU Worker pulls .ply (works the same as .las after conversion)
```

### Why Separate Workers?
- **Photogrammetry** = CPU-heavy (COLMAP/OpenMVS)
- **Pipeline ML** = GPU-heavy (PointNet++)
- แยกกัน → optimize cost (photogrammetry on cheap CPU, ML on GPU)

---

## Alternatives Considered

### Option A: Separate Pipelines per Input Type
- Each input has its own end-to-end pipeline
- ❌ Duplication ของ code (Wood-leaf, QSM, allometric ทำซ้ำ)
- ❌ ยากต่อ maintenance

### Option B: Unified Pipeline with Conversion ✅ chosen
- Convert ทุก input → Point Cloud first
- ❌ Photo path มี overhead (extra processing)
- ✅ Single source of truth สำหรับ ML pipeline
- ✅ ง่ายต่อการเพิ่ม input types ในอนาคต (drone images, satellite, ฯลฯ)

### Option C: Hybrid (separate AI models per input)
- One AI for LAS, one for RGB-only images
- ❌ ต้องเทรน 2 models
- ❌ Output schema ต่างกัน

---

## Consequences

### Positive
- ✅ Single ML pipeline = บำรุงรักษาง่าย
- ✅ Result schema เหมือนกัน (JSON format)
- ✅ Web Dashboard เรนเดอร์ 3D Viewer เหมือนกันทั้ง 2 paths
- ✅ ในอนาคตเพิ่ม input ใหม่ (drone, satellite) ง่าย

### Trade-offs
- ⚠️ Path B (Photo) ใช้เวลานานกว่า (~5 นาที vs ~2 นาที สำหรับ Path A)
- ⚠️ Photogrammetry quality ขึ้นกับ photo quality (lighting, angle coverage)
- ⚠️ User experience ต้องชัดเจน: บอก user ว่า "Photo path ใช้เวลานานกว่า"

### Mitigations
- WebSocket progress updates → user เห็นความคืบหน้า
- Email/Notification เมื่อเสร็จ
- ใน UI explain: "ใช้เวลาประมาณ 5 นาที — เราจะแจ้งเตือนเมื่อเสร็จ"

---

## Quality Comparison

| Aspect | LiDAR (.las) | Photogrammetry |
|---|---|---|
| DBH accuracy | ±2-3 cm | ±5-10 cm |
| Height accuracy | ±0.5 m | ±1-2 m |
| Processing time | 2 min/tree | 5 min/tree |
| Required hardware | TLS / Drone LiDAR (expensive) | Smartphone (cheap) |
| Cost per scan | High ($$$) | Low ($) |

**Use case fit:**
- Industrial Auditor → Path A (high accuracy, has hardware)
- Community Farmer → Path B (low cost, no special hardware)

---

## Implementation Notes

### Job Type Schema
```python
# services/api/models/job.py
class JobType(str, Enum):
    LAS_UPLOAD = "las_upload"           # Direct .las processing
    PHOTOGRAMMETRY = "photogrammetry"   # Photo → .ply
    PIPELINE = "pipeline"               # .ply → Carbon JSON (final step)
```

### Job Chain
```python
# After photogrammetry completes
async def on_photogrammetry_complete(job_id: str, ply_url: str):
    # Auto-create pipeline job
    new_job = await create_job(
        type=JobType.PIPELINE,
        input_url=ply_url,
        parent_job_id=job_id,
    )
    await dispatch_to_gpu_worker(new_job.id)
```

---

## Follow-up Actions

- [x] Document in [docs/ARCHITECTURE.md](../ARCHITECTURE.md)
- [ ] Build COLMAP Docker image
- [ ] Build OpenMVS Docker image (or use combined image)
- [ ] Set up job chain logic in API
- [ ] Test end-to-end Path B with sample photos

---

## References

- [ADR 0002](0002-no-iphone-lidar.md) — Why no iPhone LiDAR
- [COLMAP](https://colmap.github.io/)
- [OpenMVS](https://github.com/cdcseacave/openMVS)
- Liang et al. 2019: photogrammetry accuracy benchmarks
