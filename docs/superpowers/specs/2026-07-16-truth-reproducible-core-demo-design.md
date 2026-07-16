# Truth + Reproducible Core Demo Sprint — Design Specification

**วันที่:** 2026-07-16
**สถานะ:** Approved design; implementation not started
**แนวทางที่เลือก:** Integrity-first vertical slice + evidence-gated model promotion

## 1. บริบทและปัญหา

TreeQ Carbon Platform มีองค์ประกอบหลักที่ใช้งานได้แล้วหลายส่วน ได้แก่ pipeline ประมวลผล point cloud, การวัด DBH/ความสูง/ปริมาตร, allometric calculation, API, web viewer และ async-job prototype แต่สถานะจริงของแต่ละความสามารถยังถูกสื่อสารไม่ตรงกันระหว่างโค้ด เอกสาร เว็บไซต์ และเล่มโครงงาน NSC

ปัญหาหลักไม่ใช่การขาดฟีเจอร์ แต่คือการขาดเส้นทางสาธิตที่รันซ้ำได้และมีหลักฐานพอให้ตรวจว่า:

- input ใดถูกประมวลผลด้วยโค้ดและ algorithm ใด
- segmentation ใช้ `tlsep` หรือ PointNet++ จริง
- checkpoint และเวอร์ชันของ pipeline คืออะไร
- ตัวเลข DBH, height, volume, carbon และ CO2e มาจากผลรันใด
- claim ในเอกสารและหน้าเว็บสอดคล้องกับหลักฐานเดียวกันหรือไม่

Sprint นี้จึงทำ “แกนสาธิตแนวตั้ง” เพียงเส้นทางเดียวให้เชื่อถือได้ก่อนขยายฟีเจอร์ โดยกำหนดให้ `tlsep` เป็น production baseline และให้ PointNet++ เป็นเพียง candidate จนกว่าจะผ่าน evidence gate ครบทุกเงื่อนไข

## 2. เป้าหมาย

1. สร้าง deterministic core demo ที่รัน input และ config เดิมซ้ำแล้วได้ผลเชิงตัวเลขและ normalized artifact hash เดิม
2. สร้าง provenance ที่บอก input, code version, backend, algorithm map, checkpoint และผลลัพธ์อย่างตรวจสอบได้
3. สร้าง evidence gate ที่ไม่ยอม promote PointNet++ จาก Wood IoU เพียงตัวเดียว
4. ทำให้ API และ web viewer แสดง backend/evidence status ตามสิ่งที่รันจริง
5. ทำให้เอกสารใน repo, web copy และเล่ม NSC ฉบับใหม่อ้างอิง truth manifest เดียวกัน
6. ทำให้ CI ล้มเหลวเมื่อ core demo, truth consistency หรือ ML tests ล้มเหลว โดยไม่มีการกลบผลด้วย `|| true`

## 3. สิ่งที่ไม่อยู่ในขอบเขต

Sprint นี้ไม่รวม:

- การเทรน species classifier จริง; ขั้นที่ 7 ยังคงเป็น `Stub`
- การเทรน PointNet++ รอบใหญ่หรือการรับรองว่าโมเดลพร้อม production
- Marketplace, payment, certificate, GIS และ carbon-credit issuance
- mobile camera/scanning workflow ที่สมบูรณ์
- WebSocket progress แบบ real time
- production deployment ของ API/worker บน Railway หรือ RunPod
- การเปลี่ยนสูตรหรือ coefficient ใน `species_db.csv` โดยไม่มีการตรวจแหล่งอ้างอิงแยก

## 4. หลักการออกแบบ

### 4.1 Code and evidence are the truth

เมื่อเอกสารขัดกับ implementation ให้ยึดโค้ดและผลรันที่ตรวจได้เป็นความจริง เอกสารเป็นคำอธิบายของสถานะนั้น ไม่ใช่แหล่งสร้าง claim ใหม่

### 4.2 One claim, one evidence source

ตัวเลขและสถานะสำคัญต้องมาจาก `docs/evidence/core_demo_manifest.json` หรือ artifact ที่ manifest อ้างถึง ห้ามคัดลอกตัวเลขไปหลายแห่งแล้วแก้ด้วยมือโดยไม่มี consistency check

### 4.3 Baseline before candidate

`tlsep` เป็น baseline ที่ใช้สาธิตได้ในปัจจุบัน PointNet++ มีสถานะ `Experimental` จนกว่าจะผ่าน gate ครบทุกมิติและมี checkpoint provenance ที่ตรวจได้

### 4.4 Explicit failure

dependency, checkpoint, anchor ใน Word หรือ evidence ที่หายต้องทำให้ขั้นตรวจที่เกี่ยวข้องล้มเหลวพร้อมคำอธิบาย ห้าม silent fallback ที่ทำให้ผู้ใช้เข้าใจว่าโมเดลหรือการทดสอบถูกรันแล้ว

### 4.5 Reproducible result, auditable run

ค่าที่เป็นผลลัพธ์ต้อง deterministic ภายใต้ input/config/runtime ที่ระบุ ส่วน timestamp และข้อมูลแวดล้อมที่เปลี่ยนแต่ละครั้งต้องแยกออกจาก normalized result เพื่อไม่ทำลาย reproducibility

## 5. Capability Matrix

สร้าง `docs/CAPABILITY_MATRIX.md` เพื่อระบุแต่ละความสามารถด้วยสถานะมาตรฐานสี่ค่า:

- `Implemented` — มี code path ที่รันและทดสอบได้ใน scope ที่ระบุ
- `Experimental` — มี implementation แต่ evidence ยังไม่พอสำหรับ default/production claim
- `Stub` — มี interface หรือ placeholder แต่ยังไม่มีความสามารถจริงตามชื่อ
- `Planned` — ยังไม่มี implementation ที่ใช้งานได้

Matrix ต้องระบุอย่างน้อย: component, status, implementation จริง, evidence, ข้อจำกัด และ claim ที่อนุญาตให้ใช้

สถานะตั้งต้นตาม code audit:

| ความสามารถ | สถานะ | ความจริงที่ต้องสื่อสาร |
|---|---|---|
| Ground segmentation | Implemented | percentile grid ไม่ใช่ CSF |
| Height normalization | Implemented | KNN inverse-distance weighting |
| CHM | Implemented | max-Z grid + morphology ไม่ใช่ pit-free CHM |
| Tree segmentation | Implemented | watershed segmentation |
| Wood/leaf via `tlsep` | Implemented | default production baseline ของ sprint |
| Wood/leaf via PointNet++ | Experimental | ยังไม่มี verified best checkpoint และ validation design ยังไม่พอสำหรับ promotion |
| QSM-derived metrics | Implemented with limitations | DBH RANSAC, max-Z height, taper volume; branch count ยังเป็น 0 และไม่ใช่ TreeQSM |
| Species classification | Stub | ไม่ได้ infer species จริง |
| Allometric calculation | Implemented | ใช้ `species_db.csv`; เมื่อไม่มี species ใช้ fallback ตามโค้ด |
| Carbon-credit issuance | Planned | ระบบประเมิน carbon stock/CO2e ไม่เท่ากับการออกเครดิตที่รับรองแล้ว |

## 6. สถาปัตยกรรมของ core demo

เส้นทางสาธิตหลักมีเพียงเส้นทางเดียว:

```text
fixed point-cloud fixture
  -> deterministic pipeline config
  -> tlsep wood/leaf segmentation
  -> QSM metrics
  -> allometric calculation
  -> result.json + segmented.ply
  -> evidence.json
  -> normalized reproducibility check
  -> truth manifest / API / web / documents
```

`services/ml/scripts/run_core_demo.py` เป็น entry point ของเส้นทางนี้ ต้องกำหนด random seed, config, input fixture และ output layout ชัดเจน ไม่พึ่ง current working directory หรือไฟล์ลับนอก repo

PointNet++ ไม่อยู่ใน critical path ของ baseline demo หากไม่มี checkpoint ที่ตรวจได้ ระบบต้องรายงาน `candidate_not_evaluated` และยังทำ baseline demo สำเร็จได้

## 7. Provenance และ artifact contract

สร้าง `services/ml/pipeline/provenance.py` เป็นเจ้าของ schema และฟังก์ชัน normalize/hash โดย artifact อย่างน้อยประกอบด้วย:

```json
{
  "schema_version": "1",
  "run": {
    "input_sha256": "<sha256>",
    "git_commit": "<commit>",
    "pipeline_version": "<version>",
    "backend": "tlsep",
    "checkpoint_sha256": null
  },
  "algorithms": {
    "ground_segmentation": "percentile_grid",
    "height_normalization": "knn_idw",
    "chm": "max_z_morphology",
    "tree_segmentation": "watershed",
    "wood_leaf": "tlsep",
    "qsm": "ransac_dbh_maxz_height_taper_volume",
    "species": "stub",
    "allometric": "species_db_or_chave_fallback"
  },
  "results": {
    "dbh_cm": 0.0,
    "height_m": 0.0,
    "volume_m3": 0.0,
    "carbon_kg": 0.0,
    "co2eq_kg": 0.0
  },
  "evidence": {
    "dataset": "<fixture name>",
    "scope": "deterministic core demo",
    "candidate_status": "candidate_not_evaluated"
  },
  "runtime": {
    "created_at": "<ISO-8601>",
    "environment": "<summary>"
  }
}
```

ค่าตัวอย่าง `0.0` เป็น shape ของ schema ไม่ใช่ expected result การ implementation ต้องบันทึกค่าจริงจาก fixture และล็อก expected values จากผลรันที่ตรวจแล้วเท่านั้น

การคำนวณ normalized hash ต้องตัด field ที่แปรตามการรัน เช่น `runtime.created_at`, absolute paths และ temporary output location ออก แต่ห้ามตัด input hash, algorithm map, backend, checkpoint hash, config หรือผลเชิงตัวเลข

Artifact หลัก:

- `result.json` — ผลเชิงตัวเลขใน machine-readable form
- `segmented.ply` — point cloud สำหรับ viewer
- `evidence.json` — provenance ของ run นั้น
- `verification-summary.json` — ผลเปรียบเทียบการรันซ้ำและ gate decision
- `docs/evidence/core_demo_manifest.json` — manifest ที่ผ่านการตรวจและใช้สื่อสารข้าม component

## 8. Evidence gate สำหรับ PointNet++

PointNet++ จะถูก promote เป็น default ได้ต่อเมื่อเงื่อนไขต่อไปนี้ผ่านทั้งหมด:

1. มี checkpoint file และ SHA-256 ที่ตรงกับ training record
2. มี training provenance ได้แก่ code version, dataset/version, split definition, seed และ config
3. ประเมินบน independent real-tree test set ที่ไม่ถูกใช้เลือก best epoch หรือ tune hyperparameter
4. Wood IoU สูงกว่า `tlsep` baseline บน test scope เดียวกัน
5. DBH MAE ไม่แย่ลงจาก baseline
6. Height MAE ไม่แย่ลงจาก baseline
7. Volume MAPE ไม่แย่ลงจาก baseline
8. จำนวนต้นไม้ที่วัดสำเร็จไม่ลดลง
9. คำสั่งประเมินรันซ้ำได้และสร้าง evidence artifact ครบ
10. gate decision ระบุ metric, sample count, dataset scope และเหตุผลแบบ machine-readable

ห้ามใช้ Mean IoU, accuracy หรือผล synthetic เพียงอย่างเดียวเพื่อ promote โมเดล

สถานะปัจจุบันต้องรายงานตามจริง:

- Wan 2021 held-out: Wood IoU `0.418`, Leaf IoU `0.808`, Mean IoU `0.613`, accuracy `0.831`
- การเลือก best epoch ใช้ held-out loader เดียวกับที่รายงานผล จึงยังไม่ใช่ independent final test
- ยังไม่มี verified best PointNet++ checkpoint ที่ติดตามพร้อม provenance ใน repo
- ผล synthetic PCA mean IoU `0.7692083333` และ PointNet mean IoU `0.977625` เป็น synthetic benchmark เท่านั้น ไม่ใช่หลักฐาน production

ดังนั้น PointNet++ เริ่ม sprint ด้วยสถานะ `Experimental` และ `promotion_decision: reject` หรือ `candidate_not_evaluated` ตามหลักฐานที่มีจริง

## 9. ตัวเลข validation ที่อนุญาตให้รายงาน

ตัวเลขต้องระบุ dataset และ scope ทุกครั้ง ห้ามปัดเพื่อให้ดูดี

### 9.1 Wood/leaf segmentation — Wan 2021 held-out

- Wood IoU: `0.418`
- Leaf IoU: `0.808`
- Mean IoU: `0.613`
- Accuracy: `0.831`

ข้อจำกัด: held-out set ถูกใช้เลือก best epoch และไม่มี tree-ID split provenance ที่เพียงพอ จึงต้องเรียกว่า held-out validation ไม่ใช่ independent final test

### 9.2 QSM validation — Demol isolated-tree benchmark, 65 trees

- DBH MAE: `1.1673846154 cm`
- DBH RMSE: `2.0749561627 cm`
- DBH bias: `-0.5166153846 cm`
- DBH MAPE: `3.7936383616%`
- DBH within 10%: `64/65`
- DBH worst error: `34.02865%` หรือ `13.54 cm`
- Height MAE: `0.5446153846 m`
- Height RMSE: `0.7580541893 m`
- Height bias: `-0.052 m`
- Height MAPE: `2.6025892131%`
- Height within 10%: `63/65`
- Volume MAE: `0.2005569231 m³`
- Volume MAPE: `18.7650916186%`
- Volume bias: `-0.1710246154 m³`
- Volume within 10%: `18/65`
- Volume worst error: `58.113609%`

ข้อจำกัด: validation script เริ่มจาก isolated tree, subsample ไม่เกิน 20,000 points, normalize ด้วย minimum Z และใช้ PCA wood/leaf ก่อน QSM จึงไม่ใช่ validation ของ pipeline 8 ขั้นแบบ end-to-end และไม่ได้ validate carbon/allometric output

## 10. API และ web contract

API response ของเส้นทาง demo ต้องเพิ่ม metadata โดยไม่ทำลาย field เดิมที่ผู้ใช้ปัจจุบันพึ่งพา อย่างน้อยต้องแสดง:

- backend ที่ใช้จริง
- algorithm map หรือ reference ไปยัง evidence
- pipeline version/Git commit
- input hash
- checkpoint hash เมื่อใช้ model
- evidence status และ candidate promotion status

หน้า viewer ต้องแสดงสถานะให้มนุษย์เข้าใจได้ เช่น `Baseline: tlsep` หรือ `Experimental candidate: PointNet++` ห้ามใช้คำว่า AI model แบบกำกวมเมื่อผลจริงมาจาก rule-based baseline

หน้า landing และข้อความ marketing ต้องแยกสิ่งต่อไปนี้ออกจากกัน:

- ความสามารถที่ implemented และ demo ได้
- ผลทดลองที่มี scope จำกัด
- roadmap/planned feature
- carbon stock estimate กับ certified carbon credit

## 11. Truth manifest และเอกสาร

`docs/evidence/core_demo_manifest.json` เป็นแหล่งข้อมูลกลางสำหรับตัวเลขและสถานะที่ต้องปรากฏซ้ำ การแก้ข้อมูลสำคัญต้องผ่าน `scripts/sync_truth.py` ซึ่งมีสองโหมด:

- `--check` ตรวจว่า generated web evidence และ marker-controlled documentation สอดคล้องกับ manifest โดยไม่เขียนไฟล์
- `--write` สร้างหรืออัปเดตเฉพาะส่วนที่มี marker ชัดเจน

เอกสารที่ต้องสอดคล้อง:

- `docs/PROJECT_SPEC.md`
- `docs/ml/PIPELINE.md`
- `docs/ml/WOODLEAF_RESULTS.md`
- `docs/CAPABILITY_MATRIX.md`
- README และข้อความ rebrand ที่อยู่ใน core-demo path
- `apps/web/src/generated/core-demo-evidence.ts`
- เล่มโครงงาน NSC ฉบับใหม่

เอกสารต้องใช้สถานะ `Implemented`, `Experimental`, `Stub`, `Planned` อย่างสม่ำเสมอ และต้องไม่อ้าง algorithm เป้าหมายแทน algorithm ที่โค้ดใช้อยู่จริง

## 12. กลยุทธ์แก้เล่มโครงงาน NSC

ไฟล์ต้นฉบับ:

`C:\Users\Acer\Downloads\เล่มโครงงานNSC_แก้ไขแล้ว_ปรับปรุง (3).docx`

ไฟล์ผลลัพธ์ใหม่:

`C:\Users\Acer\Downloads\เล่มโครงงานNSC_ฉบับTruth-Reproducible-Core-Demo.docx`

ห้ามเขียนทับต้นฉบับ ต้องบันทึก SHA-256 ก่อนและหลังเพื่อยืนยันว่าไฟล์เดิมไม่เปลี่ยน

ใช้วิธีแก้แบบอนุรักษ์รูปแบบเดิม:

- คงลำดับบท ตาราง ภาพ และ direct formatting เดิมเท่าที่ทำได้
- แก้ pipeline 8 ขั้นให้ตรงกับ implementation และใส่สถานะ
- ใส่ตัวเลข Wood/Leaf และ Demol validation แบบไม่ปัดให้ดูดี พร้อมข้อจำกัด
- อธิบาย PointNet++ validation limitation และ evidence gate
- แยก carbon stock estimation ออกจาก certified carbon credit
- เปลี่ยน Marketplace, GIS, WebSocket และ mobile workflow ที่ยังไม่เสร็จเป็น `Planned`
- เติมประโยค Tree Segmentation ที่ค้าง
- ตรวจและแก้ reference ของ Wan, Demol และ TGO
- ลบ claim “TGO ±10%” หากไม่มีแหล่งอ้างอิงรองรับ
- ไม่นำข้อมูลส่วนบุคคลจากเล่มเข้าสู่ repo หรือ test fixture

ปรับ A4 หรือ heading style เฉพาะเมื่อ render ตรวจแล้วว่า pagination, ตารางและภาพไม่เสีย หาก environment ไม่มี renderer ที่เชื่อถือได้ ให้คง layout เดิมและรายงานข้อจำกัดแทนการแก้แบบเดา

`scripts/build_truth_aligned_report.py` ต้องค้นหา anchor ที่คาดหวัง หาก anchor สำคัญหายหรือซ้ำแบบกำกวม ให้หยุดโดยไม่สร้างไฟล์ผลลัพธ์ครึ่งสำเร็จ

## 13. Failure handling

| เหตุการณ์ | พฤติกรรมที่ต้องเกิด |
|---|---|
| ไม่มี PointNet++ checkpoint | baseline demo สำเร็จ; candidate เป็น `candidate_not_evaluated` |
| checkpoint hash ไม่ตรง | ปฏิเสธ candidate และทำ gate fail |
| normalized result จากสองรอบต่างกัน | reproducibility test และ CI fail |
| manifest ไม่ตรง web/docs | truth-consistency check fail |
| Word anchor สำคัญหาย | หยุดสร้าง DOCX; ต้นฉบับไม่เปลี่ยน |
| dependency ที่ต้องใช้หาย | fail พร้อมคำสั่งแก้; ห้ามรายงานว่าทดสอบผ่าน |
| ML full test ล้มเหลว | CI เป็นสีแดง; ห้าม `|| true` |
| output มี NaN/Infinity หรือหน่วยผิด contract | schema validation fail |

## 14. Testing และ CI gates

### 14.1 Unit tests

- provenance schema validation
- stable normalization และ SHA-256
- dynamic field exclusion ที่จำกัดเฉพาะ allowlist
- promotion decision ผ่าน/ไม่ผ่านทุกเงื่อนไข
- checkpoint mismatch rejection
- algorithm map ตรงกับ backend ที่เลือก

### 14.2 Integration tests

- รัน core demo สองครั้งด้วย fixture/config เดียวกัน
- เปรียบเทียบ normalized numeric result และ normalized artifact hash
- ตรวจว่า `result.json`, `segmented.ply`, `evidence.json` และ summary มีครบ
- ตรวจ API metadata response
- ตรวจ web rendering ของ backend และ evidence status
- ตรวจ manifest กับ generated web/docs

### 14.3 Existing project gates

- ML: full `pytest tests/` โดยไม่กลบ failure
- API: full `pytest`
- Web: unit tests, `npx tsc --noEmit`, lint และ production build
- Word: เปิดไฟล์ได้, image/table count ไม่ลดโดยไม่ตั้งใจ, source hash ไม่เปลี่ยน และ render compare เมื่อ runtime รองรับ

CI ต้องแยก failure ของ dependency/environment ออกจาก test assertion แต่ทั้งสองกรณีต้องไม่ถูกนับเป็น pass

## 15. Security, privacy และ operational limits

- ห้าม commit token, Supabase credential, tunnel URL ชั่วคราว หรือข้อมูลส่วนบุคคลจากเล่ม
- evidence ใช้ hash ของ input; ไม่ commit raw private point cloud โดยไม่มีสิทธิ์
- path ใน artifact ต้องเป็น repo-relative หรือ logical identifier เพื่อไม่เปิดเผยชื่อผู้ใช้และไม่ทำลาย reproducibility
- async job ที่เก็บไฟล์ local ไม่ถูก claim ว่ารองรับ multi-host production
- sync analyze endpoint ที่อ่าน upload ทั้งไฟล์และยังไม่มี rate-limit enforcement ต้องระบุเป็นข้อจำกัด ไม่ขยาย public production scope ใน sprint นี้

## 16. File map

### 16.1 ไฟล์ใหม่

- `docs/evidence/core_demo_manifest.json`
- `docs/CAPABILITY_MATRIX.md`
- `services/ml/pipeline/provenance.py`
- `services/ml/scripts/run_core_demo.py`
- `services/ml/tests/test_provenance.py`
- `services/ml/tests/test_core_demo.py`
- `services/ml/tests/test_evidence_gate.py`
- `scripts/sync_truth.py`
- `scripts/build_truth_aligned_report.py`
- `apps/web/src/generated/core-demo-evidence.ts`

### 16.2 ไฟล์ที่คาดว่าต้องแก้

- `services/ml/pipeline/main.py`
- `services/api/app/schemas/analyze.py`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/(dashboard)/dashboard/viewer/page.tsx`
- `.github/workflows/ci-ml.yml`
- `docs/PROJECT_SPEC.md`
- `docs/ml/PIPELINE.md`
- `docs/ml/WOODLEAF_RESULTS.md`
- README และ rebrand copy เฉพาะส่วนที่เกี่ยวข้องกับ core demo

File map นี้เป็นขอบเขตคาดการณ์ การ implementation อาจลดรายการได้เมื่อพบว่า contract เดิมรองรับอยู่แล้ว แต่ห้ามขยายไปยังฟีเจอร์นอก scope โดยไม่มีการทบทวน design

## 17. ลำดับ implementation

1. ล็อก truth schema และ capability statuses
2. เขียน failing tests ของ provenance, normalization และ promotion gate
3. ทำ provenance/evidence gate ให้ unit tests ผ่าน
4. สร้าง deterministic fixture และ core-demo runner
5. รันสองรอบและล็อก verified manifest จากผลจริง
6. เพิ่ม API metadata และ tests
7. สร้าง generated web evidence และปรับ viewer/landing copy
8. เพิ่ม truth consistency check และแก้ CI ให้ fail จริง
9. ทำเอกสารใน repo ให้ตรง manifest
10. สร้าง DOCX ฉบับใหม่และตรวจ source integrity/structure/render ตามความสามารถของ environment
11. รัน verification matrix ทั้งหมดและตรวจ scoped git diff

หากขั้นที่ 5 ยังไม่ deterministic ห้ามเดินหน้าสร้าง claim ใน web หรือ Word จากผลนั้น

## 18. Acceptance criteria

Sprint สำเร็จเมื่อครบทุกข้อ:

1. `tlsep` core demo รัน input/config เดิมสองครั้งแล้ว normalized results และ hash ตรงกัน
2. artifact ระบุ input SHA-256, Git commit/pipeline version, backend, algorithm map และ checkpoint hash/null
3. PointNet++ ไม่ถูก promote หากขาดเงื่อนไขใดเงื่อนไขหนึ่งของ evidence gate
4. API และ viewer แสดง backend/evidence status ที่ใช้จริง
5. `PROJECT_SPEC`, ML docs, web generated evidence และ Word ฉบับใหม่อ้างอิง manifest เดียวกัน
6. ML CI fail เมื่อ full tests fail และไม่มี `|| true`
7. Web tests, typecheck, lint และ build ผ่านใน environment ที่บันทึกไว้
8. API และ ML tests ผ่านใน environment ที่สร้างซ้ำได้; dependency ที่หายต้องถูกรายงานเป็น failure ไม่ใช่ pass
9. Word ฉบับใหม่เปิดได้ ภาพ/ตารางยังอยู่ ต้นฉบับมี SHA-256 เดิม และไม่มีข้อมูลส่วนบุคคลใหม่ถูก commit
10. ไม่มี claim ว่าระบบออก certified carbon credit หรือว่า PointNet++ เป็น production default โดยไม่มี evidence
11. git diff อยู่ใน scope และไม่มี secret, model binary หรือ raw private dataset หลุดเข้า commit

## 19. ความเสี่ยงและวิธีควบคุม

### 19.1 Determinism ของ third-party geometry library

Open3D, neighbor search หรือ parallel numeric kernels อาจให้ ordering ต่างกันเล็กน้อย ควบคุมด้วย seed, stable sort, fixed thread/config เท่าที่รองรับ และเปรียบเทียบค่าตัวเลขด้วย tolerance ที่ระบุ หากใช้ tolerance ห้ามอ้างว่า byte-identical

### 19.2 Fixture เล็กเกินไป

fixture ที่เล็กมากอาจ deterministic แต่ไม่แทน pipeline จริง ต้องเลือก fixture ที่ผ่านเส้นทาง `tlsep → QSM → allometric` ครบ และระบุว่าเป็น demo fixture ไม่ใช่ accuracy benchmark

### 19.3 Word automation ไม่เสถียรบน Windows

แก้ด้วย copy-first, anchor validation, source hash, structural validation และ optional render verification ห้ามทำ formatting rewrite ขนาดใหญ่เมื่อไม่มี renderer

### 19.4 Single manifest becomes stale

ลดความเสี่ยงด้วย generated artifacts, `sync_truth.py --check` ใน CI และการห้ามแก้ generated evidence ด้วยมือ

### 19.5 Gate ผ่านจาก sample ที่ไม่เป็นอิสระ

gate ต้องบังคับ dataset/split provenance และ independent real-tree test scope หากหลักฐานนี้ไม่มีให้ reject แม้ metric จะสูง

## 20. Definition of truthful demo

เดโมที่ถือว่า “truthful” ต้องทำให้กรรมการหรือผู้ตรวจตอบคำถามต่อไปนี้ได้จาก artifact โดยไม่ต้องเชื่อคำบรรยายของทีม:

- ใช้ input ใดและไฟล์เปลี่ยนหรือไม่
- ใช้ algorithm/backend ใดในแต่ละขั้น
- ใช้ model checkpoint ใด หรือไม่ได้ใช้ model
- ผลวัดและ carbon estimate เป็นเท่าไร หน่วยอะไร
- code version ใดสร้างผล
- ผลรันซ้ำตรงกันหรือไม่
- metric ที่อ้างมาจาก dataset/scope ใด
- ข้อจำกัดใดทำให้ผลนี้ยังไม่ใช่ certified carbon credit หรือ production proof

เมื่อคำตอบครบและตรวจซ้ำได้ Core Demo จึงทำหน้าที่เป็นหลักฐานของระบบ ไม่ใช่เพียง presentation path
