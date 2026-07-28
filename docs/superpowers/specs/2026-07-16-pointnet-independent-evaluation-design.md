# PointNet++ Independent Real-Data Evaluation — Design Specification

**วันที่:** 2026-07-16
**สถานะ:** Approved design; implementation not started
**แนวทางที่เลือก:** Freeze-before-final, two-cohort evidence gate
**Production baseline:** `tlsep`
**Candidate:** PointNet++ (`pointnet`)

## 1. บริบทและปัญหา

PointNet++ เคยให้ผลดีที่สุดที่บันทึกไว้บน Wan 2021 development loader เป็น Wood IoU
`0.418`, Leaf IoU `0.808`, Mean IoU `0.613` และ accuracy `0.831` แต่ผลชุดนั้นยังใช้
loader เดียวกันเลือก best epoch จึงไม่ใช่ independent final-test performance นอกจากนี้ checkpoint
ของ run `0.418` ไม่อยู่ในเครื่องแล้ว และ checkpoint ที่พบมีเพียง Wood IoU ประมาณ `0.2399`
และ `0.2312` พร้อม training provenance ไม่ครบ

โค้ดปัจจุบันยังมีข้อจำกัดที่ทำให้การทดสอบ PointNet++ โดยตรงไม่เป็นธรรมและตรวจซ้ำยาก:

- Wan NPZ เดิมมีเพียง `x`/`y` ไม่มี source hash, plot ID, tile ID หรือ split manifest
- training ไม่มี global deterministic seed และ checkpoint เก็บ metadata ไม่ครบ
- inference เดิม normalize point cloud ทั้งต้น ทั้งที่ training ใช้ normalized tiles 2,048 จุด
- evaluator เดิมสามารถเรียก Wan plot หนึ่งไฟล์ว่า “tree” ทั้งที่เป็น plot-level cloud
- Demol experiment เดิมเปลี่ยนทั้ง segmentation backend และ volume method พร้อมกัน
- เอกสารบางแห่งเรียก Wan spatial dev split ว่า leakage-free ทั้งที่ไม่มี native tree IDs พิสูจน์

งานนี้จึงต้องสร้าง checkpoint ใหม่พร้อม provenance, freeze ก่อนเปิด external labels และเปรียบเทียบ
candidate กับ baseline แบบ paired โดยเปลี่ยนเฉพาะ wood/leaf backend

## 2. เป้าหมาย

1. สร้าง PointNet++ checkpoint ใหม่จากสูตรที่กำหนดล่วงหน้าและรันซ้ำได้
2. วัด Wood IoU บน manually labelled TLS trees ที่ไม่ใช้ train/tune/select model
3. วัด DBH, height และ destructive-volume non-regression บน downstream cohort เดียวกันต่อ backend
4. ตัดสินด้วย fail-closed gate ที่ตรวจ checkpoint, training, dataset และ command provenance
5. รายงาน point estimates, uncertainty และข้อจำกัดครบ แม้ผลสุดท้ายจะไม่ผ่าน
6. คง `tlsep` เป็น default จนกว่าจะได้ verdict `PROMOTE_POINTNET`

## 3. สิ่งที่ไม่อยู่ในขอบเขต

- ไม่รับรอง eight-stage pipeline หรือ carbon/CO2e accuracy ทั้งระบบ
- ไม่เปลี่ยน species classifier ซึ่งยังเป็น stub
- ไม่เปลี่ยน QSM implementation เป็น TreeQSM หรือ sectional cylinders ใน gate นี้
- ไม่ใช้ external final cohort เพื่อเพิ่มข้อมูล train, tune threshold หรือเลือก hyperparameter
- ไม่ claim ว่า Demol เป็น blind dataset ใหม่
- ไม่เปลี่ยน production default อัตโนมัติจาก evaluator
- ไม่ commit raw point clouds หรือ model binaries เข้า Git

## 4. Evaluation contract

ตัวแปรทดลองมีเพียง wood/leaf backend:

```text
same input points + same deterministic indices + same downstream code
  baseline:  tlsep     -> RANSAC DBH -> max-Z height -> taper volume
  candidate: PointNet++ -> RANSAC DBH -> max-Z height -> taper volume
```

ห้ามใช้ผลจาก `PointNet++ + sectional volume` เทียบกับ `tlsep + taper volume` เป็น promotion
evidence เพราะเปลี่ยนสองตัวแปรพร้อมกัน

## 5. Cohort A — blind external segmentation

ใช้ชุดข้อมูล **Graph-based Leaf–Wood Separation Method for Individual Trees Using Terrestrial
Lidar Point Clouds: Labeled validation data**,
[DOI `10.5281/zenodo.6831378`](https://zenodo.org/records/6831378)

- 10 individual TLS tree point clouds
- manual wood/leaf labels แยกเป็นไฟล์ `_wood.pcd` และ `_leaf.pcd`
- ครอบคลุม tropical, temperate และ boreal species
- ขนาดรวมประมาณ 84.1 MB
- license CC BY 4.0

กติกา:

- การอ่านหน้า metadata และ license ไม่ถือว่าเปิด labels
- ห้ามดาวน์โหลดไฟล์ labelled PCD ก่อน freeze manifest ถูก commit
- ห้ามใช้ cohort นี้ใน training, best-epoch selection, seed selection หรือ preprocessing tuning
- external manifest ต้องเก็บ DOI, license, publisher filenames, publisher MD5 และ local SHA-256
- ต้องจับคู่ wood/leaf ได้ครบ 10 tree IDs โดยไม่มีชื่อซ้ำ
- รวมแต่ละต้นแบบ deterministic โดยคง row order ในไฟล์และ concatenate wood ก่อน leaf
- hash ไม่ตรงหรือไฟล์ไม่ครบให้ verdict `INVALID_EVIDENCE`

Primary claim ที่ cohort นี้รองรับคือ blind external wood/leaf segmentation เท่านั้น

## 6. Cohort B — locked downstream benchmark

ใช้ [Demol destructive-biomass dataset](https://zenodo.org/records/4557401) ที่มี point clouds และ
reference DBH, felled height และ destructive volume จำนวน matched trees 65 ต้น

Demol เป็น external non-training cohort สำหรับ PointNet++ แต่ไม่ใช่ blind dataset ใหม่ เพราะ repo
เคยใช้สร้าง baseline และมี experiment เก่าอยู่แล้ว Claim ที่อนุญาตคือ:

> blind external segmentation + locked Demol downstream non-regression

ห้ามเรียกผลรวมนี้ว่า fully blind end-to-end validation

กติกา:

- ล็อกรายชื่อ matched tree IDs ก่อนรัน candidate
- ใช้ deterministic sample สูงสุด 20,000 จุดต่อต้นด้วย seed `0` เพื่อรักษา baseline contract เดิม
- baseline และ candidate ใช้ point indices เดียวกันทุกต้น
- ใช้ `RANSAC DBH + max-Z height + taper volume` และ QSM seed `0` เหมือนกัน
- ล้มเหลวหนึ่งต้นต้องถูกนับใน measurable-tree count ห้ามตัดออกเงียบ ๆ
- historical metrics ต้องรายงานแยกจาก paired rerun; gate ใช้ค่าที่ recompute ใน run เดียวกันเท่านั้น

## 7. Wan training/development data

ไม่ใช้ `wan_train.npz` และ `wan_test.npz` เดิมเป็น provenance source แต่ regenerate จาก
[raw Wan 2021](https://datadryad.org/dataset/doi%3A10.5061/dryad.rfj6q5799) สาม plots
ด้วยค่าที่ล็อกไว้:

| Parameter | Value |
|---|---:|
| Source plots | White Birch, Dahurian Larch, Chinese scholar tree |
| `n_off` | 10,000 |
| `per` | 1,500 |
| tile size | 2.5 m |
| points/tile | 2,048 |
| minimum raw points/tile | 1,024 |
| spatial train fraction | 0.70 |
| excluded buffer | 2.5 m |
| resampling seed | 0 |

Builder ต้องสร้าง immutable split manifest ที่เก็บ:

- logical source ID, filename, byte size และ SHA-256 ของ raw plots
- tile ID, plot ID, grid coordinates, raw centre และ raw point count
- split (`train`, `dev`, `dropped_buffer`)
- resampling seed และ selected-index digest
- output NPZ SHA-256, shape, label convention และ wood fraction
- converter configuration และ code commit

Wan split เรียกว่า **spatially separated development split** เท่านั้น ไม่เรียก independent test หรือ
leakage-free เพราะไม่มี native tree IDs และ buffer 2.5 m ไม่พิสูจน์ว่า crown เดียวกันไม่ข้ามเขต

## 8. Training recipe

ใช้สูตร Variant 3 ที่เคยให้ผลดีที่สุด โดยไม่ทำ hyperparameter search เพิ่ม:

| Parameter | Value |
|---|---:|
| initialization | from scratch |
| real samples | Wan train split |
| synthetic augmentation | 200 samples |
| synthetic seed range | 50,000–50,199 |
| class weighting | none |
| epochs | 60 |
| batch size | 8 |
| optimizer | Adam |
| learning rate | `1e-3` |
| weight decay | `1e-4` |
| scheduler | StepLR, step 20, gamma 0.5 |
| model-selection metric | macro tile Wood IoU on Wan dev |

Training seeds ถูกกำหนดล่วงหน้าเป็น `20260716`, `20260717`, `20260718`

- ตั้ง seed ให้ Python, NumPy, PyTorch และ CUDA
- เปิด deterministic algorithms แบบ fail-fast
- เก็บ logs และ checkpoint ของทุก seed ห้ามลบรอบที่แย่
- เลือก best epoch ภายใน seed และ best seed ด้วย macro tile Wood IoU เท่านั้น
- หากคะแนนเท่ากัน ใช้ seed ตัวเลขต่ำกว่า
- pooled Wood/Leaf/Mean IoU และ accuracy เป็น secondary development metrics
- external cohort ไม่มีส่วนในการเลือกใด ๆ

## 9. Reproducibility verification และ checkpoint freeze

หลังเลือก seed ที่ชนะ ต้อง rerun seed นั้นจาก clean committed worktree อีกหนึ่งครั้ง และเปรียบเทียบ:

- selected epoch
- development metrics แบบ full precision
- canonical state-dict hash ซึ่งคำนวณจาก tensor keys ที่ sort แล้ว พร้อม dtype, shape และ raw bytes

หาก canonical state hash หรือ metrics ไม่ตรง ห้าม freeze และให้แก้ reproducibility ก่อน

Freeze manifest ต้องระบุ:

- checkpoint file SHA-256 และ canonical state-dict SHA-256
- architecture และ complete training configuration
- source/split/NPZ hashes
- seed, epoch และ development metrics ของทุก run
- winning-seed rerun evidence
- Python, NumPy, PyTorch, CUDA, cuDNN, GPU และ relevant package versions
- training command, working-tree cleanliness และ training-code Git commit
- logical artifact path โดยไม่บันทึกชื่อผู้ใช้หรือ absolute personal path

Freeze manifest ต้องถูก commit ก่อนดาวน์โหลด Cohort A หาก retrain หรือแก้ preprocessing หลังเปิด
Cohort A ผลใหม่เป็น diagnostic เท่านั้น และไม่มีสิทธิ์ใช้ cohort เดิมเพื่อ promotion อีก

## 10. PointNet++ tiled inference

ห้ามใช้ whole-cloud normalization สำหรับ formal evaluation การ inference ต้องสอดคล้องกับ training
distribution และให้ prediction coverage ครบทุก evaluation point:

1. สร้าง deterministic XY windows ขนาด 2.5 m, stride 1.25 m (50% overlap)
2. ใช้ stable original point index เป็น tie-breaker ทุกขั้น
3. สร้าง context-plus-query chunks ขนาดไม่เกิน 2,048 จุด
4. pad sparse chunks ด้วย deterministic resampling แต่บันทึกผลเฉพาะ original query points
5. normalize แต่ละ model input ด้วย training normalization function เดียวกัน
6. สะสม logits ของจุดที่ปรากฏหลาย windows แล้วหารด้วย coverage count
7. ตัดสิน class หลัง aggregate logits เสร็จเท่านั้น
8. coverage count ของทุกจุดต้องมากกว่าหรือเท่ากับหนึ่ง

ห้ามเติมจุดที่ PointNet++ ทำนายไม่ครบด้วย `tlsep` หาก coverage ไม่ครบให้ run เป็น
`INVALID_EVIDENCE`

Cohort A ใช้ labelled points ทั้งหมด Cohort B ใช้ deterministic 20,000-point view ที่ล็อกไว้

## 11. Metrics

Label convention ของ formal evaluator คือ `WOOD=0`, `LEAF=1`

### 11.1 Cohort A

Primary metric:

- **Macro Wood IoU** — คำนวณ Wood IoU แยกต่อต้นแล้วเฉลี่ย 10 ต้น

Secondary metrics:

- macro Leaf IoU, macro Mean IoU และ macro accuracy
- pooled per-point Wood/Leaf/Mean IoU และ accuracy
- per-tree confusion counts และ per-tree metric deltas

Macro metric ป้องกัน tree cloud ที่มีจุดมากครอบงำผลรวม

### 11.2 Cohort B

- DBH MAE (cm)
- Height MAE (m)
- destructive-volume MAPE (%)
- measurable-tree count

คำนวณจากค่าที่ไม่ปัดเศษ การปัดมีไว้เพื่อแสดงผลเท่านั้น

## 12. Formal gate และ statistical evidence layer

### 12.1 Formal point-estimate gate

PointNet++ ผ่าน formal gate เมื่อครบทุกข้อ:

1. checkpoint SHA-256 ถูกต้อง
2. training provenance ครบ
3. Cohort A เป็น independent external test ตาม protocol
4. reproducible command ถูกบันทึก
5. candidate macro Wood IoU มากกว่า baseline
6. candidate DBH MAE ไม่มากกว่า baseline
7. candidate Height MAE ไม่มากกว่า baseline
8. candidate Volume MAPE ไม่มากกว่า baseline
9. candidate measurable-tree count ไม่น้อยกว่า baseline

### 12.2 Statistical layer

ใช้ paired percentile bootstrap ตาม tree ID จำนวน 10,000 resamples ด้วย seed `20260716`

- Cohort A: bootstrap delta ของ macro Wood IoU (`candidate - baseline`)
- Cohort B: bootstrap mean delta ของ per-tree absolute DBH error, absolute height error และ
  absolute percentage volume error (`candidate - baseline`)

เงื่อนไข strong evidence:

- lower bound ของ 95% CI สำหรับ Wood IoU delta ต้องมากกว่า `0`
- upper bound ของ 95% CI สำหรับ downstream error deltas ทั้งสามต้องไม่มากกว่า `0`
- measurable-tree count ต้องผ่าน formal criterion

Verdict มีสี่ค่า:

| Verdict | ความหมาย | Default action |
|---|---|---|
| `INVALID_EVIDENCE` | hash/provenance/protocol/coverage ไม่ถูกต้อง | คง `tlsep` |
| `FAIL_METRICS` | formal criterion อย่างน้อยหนึ่งข้อไม่ผ่าน | คง `tlsep` |
| `POINT_ESTIMATE_PASS_ONLY` | formal gate ผ่าน แต่ CI ยังไม่สนับสนุน strong evidence | คง `tlsep` |
| `PROMOTE_POINTNET` | formal gate และ statistical layer ผ่านทั้งหมด | อนุญาตให้ทำ promotion PR แยก |

Evaluator ห้ามเปลี่ยน default อัตโนมัติ

## 13. Components และ expected artifacts

### 13.1 Components

1. Wan dataset builder + split-manifest writer
2. deterministic evidence trainer + run recorder + checkpoint selector
3. checkpoint/provenance validator + canonical tensor hasher
4. tile-wise PointNet++ inference engine
5. Zenodo PCD pair adapter
6. paired segmentation/downstream evaluator
7. bootstrap/statistical verdict module
8. evidence report writer

### 13.2 Git-tracked evidence

เก็บภายใต้ `docs/evidence/pointnet_independent_eval/`:

- `protocol.json`
- `wan_split_manifest.json`
- `training_runs.json`
- `freeze_manifest.json`
- `external_dataset_manifest.json` หลัง freeze เท่านั้น
- `segmentation_per_tree.csv`
- `downstream_per_tree.csv`
- `result.json`
- `REPORT.md`

ไฟล์ JSON ต้อง stable-sort keys และห้ามมี absolute personal paths/timestamps ใน normalized hashes

### 13.3 Git-ignored artifacts

- raw Wan/Demol/Zenodo point clouds
- generated NPZ files
- `.pt` checkpoints
- training logs ที่มีขนาดใหญ่

CLI ต้องรับ explicit data/artifact roots แต่ manifest เก็บ logical IDs และ hashes แทน local paths

## 14. Fail-closed behavior

เงื่อนไขต่อไปนี้ต้องให้ non-zero exit และ `INVALID_EVIDENCE`:

- source, NPZ หรือ checkpoint hash mismatch
- missing/duplicate tree ID หรือ wood/leaf pair ไม่ครบ
- label convention ไม่ตรง
- training provenance, environment หรือ command ขาด
- code commit ไม่ตรงกับ freeze manifest
- prediction coverage ไม่ครบ 100%
- baseline/candidate ใช้ point indices หรือ downstream algorithm ต่างกัน
- Demol matched set ไม่ครบตาม precommitted tree list
- metric เป็น NaN/Inf หรือ denominator ของ volume MAPE ไม่ valid

ห้าม silent fallback, skip failed trees, replace missing candidate predictions ด้วย baseline หรือเปลี่ยน
threshold หลังเห็นผล

## 15. TDD และ verification strategy

เขียน failing tests ก่อน implementation สำหรับ:

- deterministic Wan split และ stable manifest
- source/output hash validation
- checkpoint metadata และ canonical state hashing
- deterministic seed setup และ best-run/tie selection
- tiled inference coverage, overlap aggregation และ sparse padding
- การห้าม tlsep fallback ใน PointNet evaluation
- PCD pair parsing และ label mapping
- macro-vs-pooled metrics
- paired bootstrap reproducibility
- measurable failure counting
- formal gate และ verdict ทั้งสี่ค่า
- same-indices/same-QSM downstream contract

CI ใช้ CPU fixtures ขนาดเล็กและไม่ดาวน์โหลด external data หรือ train real model Real GPU verification
รันบน RTX 4060 จาก clean committed worktree พร้อมเก็บ command/environment จริง

ก่อนเริ่ม implementation baseline ที่ตรวจแล้วคือ:

- `scripts/tests/test_sync_truth.py`: 28 passed
- evidence-related ML subset: 24 passed

## 16. Documentation truth updates

ก่อนมีผลจริง PointNet++ ต้องคงสถานะ `Experimental` และ evidence gate เป็น `pending`

เมื่อ implementation พร้อม ต้องแก้คำที่ขัดกับ code/evidence:

- `realdata_dataset.py` ห้าม claim ว่า spatial buffer พิสูจน์ no shared tree
- `FINETUNE_REALDATA.md` ห้ามเรียก Wan dev split ว่า leakage-free independent test
- `WOODLEAF_RESULTS.md` ต้องคง `0.418` เป็น prior same-environment development result
- `experiment_g3_pointnet_volume.py` ต้องระบุชัดว่าเป็น confounded historical experiment และไม่ใช่ gate
- `PROJECT_SPEC.md`/`PIPELINE.md` อัปเดตตาม verdict จริงเท่านั้น

หากไม่ผ่าน ให้ commit ผลลบและข้อจำกัดตามจริง ห้ามลบ evidence artifacts

## 17. Execution order

1. เขียน implementation plan จาก design นี้
2. เขียน failing tests สำหรับ schemas, determinism, tiled inference และ verdict
3. implement data/provenance/training primitives ให้ tests ผ่าน
4. implement external/downstream adapters และ CPU integration fixtures
5. commit code ที่ผ่าน tests ก่อน real training
6. regenerate Wan train/dev + manifest จาก raw sources
7. train fixed three seeds และ rerun winning seed
8. commit freeze manifest
9. ดาวน์โหลดและ hash Cohort A หลัง freeze commit เท่านั้น
10. รัน Cohort A และ Cohort B paired evaluation ครั้งเดียวตาม protocol
11. commit raw results, report และ truth-aligned docs ไม่ว่าผลจะผ่านหรือไม่
12. หาก verdict เป็น `PROMOTE_POINTNET` จึงเปิด promotion PR แยก

## 18. Acceptance criteria

งาน independent evaluation สำเร็จเมื่อ:

1. checkpoint ใหม่มี verified file hash, canonical state hash และ complete training provenance
2. winning seed rerun ให้ canonical state hash และ metrics ตรงกัน
3. external labelled files ถูกเปิดหลัง freeze commit เท่านั้น
4. external manifest ตรวจครบ 10 trees และ hashes ตรง
5. baseline/candidate ใช้ paired input contract เดียวกัน
6. segmentation และ downstream artifacts เก็บ per-tree values ครบ
7. formal criteria, bootstrap intervals และ verdict สร้างจาก full-precision values
8. failure ใด ๆ ถูกบันทึกและไม่ถูกข้าม
9. tests และ truth-sync checks ผ่าน
10. docs และ NSC claims ตรงกับ result artifact
11. `tlsep` ไม่ถูกเปลี่ยน default เว้นแต่ verdict เป็น `PROMOTE_POINTNET`
12. ไม่มี raw dataset, model binary, secret หรือ personal absolute path หลุดเข้า Git

## 19. ข้อจำกัดที่ต้องรายงานเสมอ

- Cohort A มีเพียง 10 trees; CI จึงอาจกว้างแม้ point estimate ดีขึ้น
- Cohort A เป็น individual-tree TLS แต่ไม่ใช่ข้อมูลประเทศไทย
- Wan dev split ไม่มี native tree IDs และไม่ใช่ independent test
- Demol เป็น locked reused benchmark ไม่ใช่ newly blind downstream cohort
- downstream gate รับรองเฉพาะ DBH, height และ taper-volume behavior ของ code path นี้
- ผลนี้ไม่ validate species classification, allometric coefficients, carbon credits หรือ production deployment
- หากได้ `POINT_ESTIMATE_PASS_ONLY` ต้องสื่อว่า “ยังไม่พอเปลี่ยน default” ไม่ใช่ “เกือบ production-ready”

## 20. Claim ที่อนุญาตหลังจบงาน

รูปประโยคต้องขึ้นกับ artifact จริง:

- `INVALID_EVIDENCE`: การทดลองไม่สมบูรณ์และไม่มี metric claim ที่ใช้ promote ได้
- `FAIL_METRICS`: PointNet++ ไม่ผ่าน precommitted independent evidence gate; `tlsep` ยังคง default
- `POINT_ESTIMATE_PASS_ONLY`: point estimates ผ่าน แต่ uncertainty ยังไม่สนับสนุน promotion; `tlsep` ยังคง default
- `PROMOTE_POINTNET`: PointNet++ ผ่าน blind external segmentation และ locked Demol downstream
  non-regression ตาม protocol นี้; ยังไม่ใช่ full end-to-end carbon validation

ไม่ว่า verdict ใด ต้องรายงาน exact Wood IoU, DBH MAE, Height MAE, Volume MAPE, measurable count,
paired deltas, 95% CIs, dataset scope และ checkpoint SHA-256
