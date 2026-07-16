# Document Status and Claim Authority

เอกสารใน repo มีทั้ง “ความจริงปัจจุบัน”, แผนเป้าหมาย และบันทึกย้อนหลัง การแยกสถานะนี้มีไว้ป้องกันการนำคำเคลมเก่ากลับมาใช้ในเล่มหรือเดโม

## Current truth — ใช้อ้างอิงได้

1. `docs/evidence/core_demo_manifest.json` — machine-readable source of reviewed metrics/status
2. `docs/CAPABILITY_MATRIX.md` — generated capability/status matrix
3. `docs/PROJECT_SPEC.md` — master project context
4. `docs/ml/PIPELINE.md` — pipeline ตามโค้ดจริง
5. `docs/ml/WOODLEAF_RESULTS.md` — experimental results และข้อจำกัด
6. `docs/ml/ALLOMETRIC.md` — สมการ/coefficients พร้อมสถานะ TGO verification
7. `README.md` และ `AGENTS.md` — orientation ที่ต้องสอดคล้องกับรายการข้างต้น

ถ้าเอกสารขัดกับโค้ด ให้ยึดโค้ด; ถ้าเอกสารขัดกับตัวเลข/status ให้ยึด evidence manifest จนกว่าจะมี reviewed evidence ชุดใหม่

## Mixed current/target — อ่าน banner ก่อนใช้

- `services/api/README.md`, `services/ml/README.md`, `apps/web/README.md`, `apps/mobile/README.md`
- `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DEPLOYMENT.md`, `docs/ROADMAP.md`

เอกสารเหล่านี้มีรายละเอียดเป้าหมายปะปนกับส่วนที่ implement แล้ว จึงติดป้ายสถานะด้านบนและห้ามใช้เป็นหลักฐาน completion โดยลำพัง

## Historical/superseded — เก็บเพื่อ trace การตัดสินใจ

- `docs/AI_AGENT_CONTEXT.md`, `docs/SESSION_HANDOFF.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/P1_SPRINT_PLAN.md`
- `docs/DATASET_REQUEST.md`, `proposal/outline.md`, `docs/proposal/`, `proposal/5-questions-answers.md`
- `docs/superpowers/plans/`, `docs/superpowers/specs/`, `docs/decisions/`, `docs/learning/`

คำว่า WebSocket, RunPod, GIS, Marketplace, full TreeQSM, ResNet หรือ metric ที่ปัดเศษในเอกสารกลุ่มนี้อาจเป็น historical target ไม่ใช่ current capability

## Non-negotiable truth snapshot

- Default wood/leaf backend: `tlsep` — **Implemented**
- PointNet++: **Experimental**, not promoted
- Wan held-out: Wood IoU `0.418`, Leaf IoU `0.808`, Mean IoU `0.613`, accuracy `0.831`; held-out loader ใช้เลือก best epoch ด้วย
- Demol isolated-tree 65 ต้น: DBH MAE `1.1673846154 cm`, Height MAE `0.5446153846 m`, Volume MAPE `18.7650916186%`; geometry only
- Species classification: **Stub**
- WebSocket, GIS, Marketplace/certificate และ production RunPod: **Planned**
- Carbon stock/CO2e เป็นค่าประมาณ ไม่ใช่ certified/tradable carbon credits
