# ADR 0005: Cloud GPU Strategy (RunPod Serverless)

- **Status:** Accepted
- **Date:** 2026-05-20
- **Deciders:** User (Team Lead)

---

## Context

ML Pipeline ต้องใช้ GPU (PyTorch + PointNet++) สำหรับ:
- **Training:** ~50-100 GPU-hours total
- **Inference (Production):** 5-15 นาที/job, intermittent traffic

ทีมเป็นนักศึกษา:
- ไม่มี workstation GPU
- งบจำกัด (~$20-30/mo cap)
- ต้องการ flexibility ขึ้น-ลง

---

## Decision

**Hybrid strategy** สำหรับ Training vs Inference:

### Training Phase
- **Google Colab Pro+** ($49.99/mo) → A100 40GB
- **Backup:** Kaggle Notebooks (P100 16GB, ฟรี 30 ชม./สัปดาห์)
- **Local:** เฉพาะ debugging code ก่อน train

### Inference / Production
- **RunPod Serverless GPU** (A10G 24GB)
- Pay-per-second (~$0.39/hr)
- Auto scale-to-zero ไม่มี idle cost
- Cold start ~30s (ยอมรับได้สำหรับ async job)

---

## Alternatives Considered

### Option A: Self-host GPU (Workstation)
- ✅ ไม่มี ongoing cost
- ❌ ต้องซื้อ RTX 4090 (~฿70,000)
- ❌ ไม่ scalable
- ❌ ใช้กระแสไฟฟ้าเยอะ

### Option B: AWS SageMaker
- ✅ Managed, integrated with AWS
- ❌ ราคาแพงสุด (~$0.75/hr คล้ายกัน + เพิ่ม overhead)
- ❌ Complex setup, learning curve

### Option C: Modal.com
- ✅ Python-native, ง่ายดี
- ❌ ยังใหม่ (less battle-tested)
- ❌ ราคาแพงกว่า RunPod เล็กน้อย

### Option D: RunPod Serverless ✅ chosen
- ✅ Cheapest pay-per-second
- ✅ Simple Docker deploy
- ✅ Auto scale-to-zero
- ⚠️ Cold start 20-30s
- ⚠️ ต้องสร้าง Docker image เอง

### Option E: Vast.ai / Lambda Cloud
- ✅ Marketplace, ราคาถูกบางครั้ง
- ❌ ไม่ serverless (เสีย cost ตลอดเวลา)
- ❌ Spot instances อาจถูก reclaim

---

## Cost Analysis

### Scenario: 100 jobs/month, 10 min/job

| Provider | Hours | Rate | Monthly Cost |
|---|---|---|---|
| AWS SageMaker (g5.xlarge) | 16.7 | $1.006/hr | $16.80 |
| Modal.com (A10G) | 16.7 | $0.59/hr | $9.85 |
| **RunPod Serverless A10G** | 16.7 | $0.39/hr | **$6.51** |
| Self-host RTX 4090 | — | — | $0 + ฿70k upfront |

→ RunPod ชนะใน $/job ratio

### Scenario: Training PointNet++ (50 GPU-hours)

| Provider | Hourly | Total |
|---|---|---|
| Colab Pro+ A100 (unlimited) | included | $49.99 |
| Kaggle P100 (free) | $0 | $0 |
| RunPod A100 | $1.69 | $84.50 |

→ Colab Pro+ ดีสุดสำหรับ training

---

## Architecture

### Training (Colab)
```
1. Push code to GitHub
2. Open Colab notebook (mounted from Drive or pulled from GitHub)
3. !pip install -e /content/services/ml
4. Train, save weights to Hugging Face Hub
```

### Inference (RunPod Serverless)
```
1. Build Docker image with PyTorch + model weights baked in
   docker build -f services/ml/Dockerfile.gpu -t carbonscan-ml:v1 .
2. Push to Docker Hub / GHCR
3. Create RunPod Serverless Endpoint
4. API → POST /v2/{endpoint_id}/run with input JSON
5. RunPod spins up worker (30s cold start)
6. Worker downloads input from URL, processes, uploads result
7. Webhook back to API when done
```

---

## Consequences

### Positive
- ✅ Total Phase 1-3 cost < $80 (Colab subscription + RunPod usage)
- ✅ ไม่มี upfront capex
- ✅ Scale 0 → 100 jobs/day อัตโนมัติ
- ✅ ลด complexity (ไม่ต้อง manage infra)

### Trade-offs
- ⚠️ Cold start 20-30s → ต้อง warmup pool ถ้า demo real-time
- ⚠️ Vendor lock-in (RunPod) — แต่ Docker-based ย้ายได้ง่าย
- ⚠️ Bandwidth cost: ดาวน์โหลด .las ขนาดใหญ่จาก Supabase → RunPod

### Mitigations
- Pre-warm RunPod worker 5 นาทีก่อน demo ในวันแข่ง
- ใช้ Supabase region เดียวกับ RunPod (Singapore) ลด bandwidth latency
- Implement caching ของ intermediate results

---

## Monitoring & Budget Control

- **Budget alert:** RunPod email เมื่อใช้ > $20/mo
- **Cost dashboard:** ใช้ runpod dashboard + Google Sheets
- **Idle timeout:** 5 seconds (default 30s → too slow to shut down)
- **Max workers:** 3 (ป้องกัน runaway parallel jobs)

---

## Follow-up Actions

- [x] Create Colab Pro+ account
- [ ] Create RunPod account
- [ ] Build Docker image (`services/ml/Dockerfile.gpu`)
- [ ] Test Docker locally with `nvidia-docker` before deploy
- [ ] Setup budget alerts
- [ ] Document cold start latency in benchmarks

---

## References

- [RunPod Serverless docs](https://docs.runpod.io/serverless/overview)
- [Colab pricing](https://colab.research.google.com/signup)
- [Kaggle Notebooks GPU policy](https://www.kaggle.com/docs/notebooks#technical-specifications)
