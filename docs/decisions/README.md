# 📐 Architecture Decision Records (ADR)

> Documentation ของการตัดสินใจ architectural ที่สำคัญ
>
> **Why ADRs?** เพื่อให้คนที่มาทำงานต่อ (รวมถึงตัวเราเอง 6 เดือนถัดมา) เข้าใจว่า "ทำไมเลือกแบบนี้"

---

## What is an ADR?

**ADR (Architecture Decision Record)** = เอกสารสั้น ๆ บันทึก:
- Context (สถานการณ์)
- Decision (ตัดสินใจอะไร)
- Consequences (ผลที่ตามมา + trade-offs)

References: [Michael Nygard's ADR template](https://github.com/joelparkerhenderson/architecture-decision-record)

---

## Index

| # | Title | Status | Date |
|---|---|---|---|
| [0001](0001-monorepo-structure.md) | Monorepo Structure (pnpm + Turborepo) | ✅ Accepted | 2026-05-20 |
| [0002](0002-no-iphone-lidar.md) | Pivot away from iPhone LiDAR | ✅ Accepted | 2026-05-20 |
| [0003](0003-tech-stack-selection.md) | Tech Stack Selection | ✅ Accepted | 2026-05-20 |
| [0004](0004-dual-input-architecture.md) | Dual-Input Architecture | ✅ Accepted | 2026-05-20 |
| [0005](0005-cloud-gpu-strategy.md) | Cloud GPU Strategy (RunPod Serverless) | ✅ Accepted | 2026-05-20 |
| [0006](0006-team-ownership.md) | Team Ownership Model | ✅ Accepted | 2026-05-20 |

---

## How to Add New ADR

1. Copy `_template.md` → `XXXX-short-title.md` (next number)
2. ใส่เนื้อหา
3. Update index นี้
4. PR → ทีมรีวิว
5. หลัง merge สถานะเปลี่ยนเป็น "Accepted"

---

## Statuses

- **Proposed** — กำลังหารือ
- **Accepted** — เห็นพ้องและกำลังใช้
- **Deprecated** — ไม่ใช้แล้วแต่เก็บไว้เป็น history
- **Superseded by ADR XXXX** — ถูกแทนที่
