# AGENTS.md — TreeQ Carbon Platform

> ไฟล์นี้โหลดเข้า context อัตโนมัติ (Codex/Claude/agent อื่น) ทุกครั้งที่เปิด repo นี้
> **ภาษา:** ตอบผู้ใช้เป็น **ภาษาไทย** (technical terms เป็น EN ได้) · ผู้ใช้เป็น team lead (นักศึกษา)

---

## 👉 อ่านก่อนเริ่มงานเสมอ

**`docs/PROJECT_SPEC.md`** = context ฉบับเต็ม (22 sections) — อธิบายทั้งโปรเจกต์: pipeline, allometric,
backend, web, mobile, สถานะจริง, known bugs, roadmap. **อ่านไฟล์นั้นก่อนแตะโค้ด**

เอกสารนี้ (AGENTS.md) = orientation สั้นๆ + คำสั่ง build/run/test + กติกา

---

## โปรเจกต์คืออะไร (1 ย่อหน้า)

**TreeQ Carbon Platform** (เดิมชื่อ *CarbonScan AI*) — แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้จาก **3D point cloud**
ด้วย AI แยก **ลำต้น(wood)/ใบ(leaf)** → วัด **DBH + ความสูง** → คำนวณ **ชีวมวล→คาร์บอน→CO₂e** ด้วยสมการ
มาตรฐาน (TGO/Chave 2014/IPCC) แบบโปร่งใส ต่อยอดเป็น B2B carbon offset matchmaking
สร้างเพื่อแข่ง **NSC 2026 หมวด 14 (อุดมศึกษา)**

---

## โครงสร้าง Monorepo

```
apps/web/        Next.js 14 (App Router, TS, Tailwind, shadcn) — landing + dashboard + 3D viewer
apps/mobile/     Flutter (Riverpod, go_router, camera, Supabase) — สแกน/ถ่ายภาพ → คาร์บอน
services/api/    FastAPI (SQLAlchemy async, asyncpg, Pydantic v2, Alembic) — REST + async-job worker
services/ml/     PyTorch pipeline (PointNet++, Open3D, laspy) — 8-step ML pipeline + allometric
docs/            เอกสาร (PROJECT_SPEC.md, ml/, learning/, decisions/, superpowers/)
proposal/        NSC proposal
memory/          project memory
```

---

## Build / Run / Test (ต่อ service)

### Web (`apps/web`)
```bash
npm install
npm run dev            # ต้องมี NEXT_PUBLIC_SUPABASE_URL + ANON_KEY ใน .env.local
                       #   (ถ้าไม่มี middleware จะข้าม auth ให้ dev เปิดได้ — ดู middleware.ts)
npm run build          # gate ก่อน deploy เสมอ
npx tsc --noEmit       # typecheck
npm run lint
npx vercel --prod --archive=tgz --yes   # deploy → treeqcarbon.vercel.app
```

### API (`services/api`)
```bash
python -m venv .venv && .venv/Scripts/activate     # Windows (หรือ source .venv/bin/activate)
pip install -e .        # หรือ requirements
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m app.worker    # async job worker (คนละ process)
pytest                  # 34 tests (2 skip ถ้าไม่มี DATABASE_URL)
alembic upgrade head    # migrations
```

### ML (`services/ml`)
```bash
python -m venv .venv && .venv/Scripts/activate
pip install -e .
pytest tests/           # allometric 15+ tests ฯลฯ
# sanity check คาร์บอน:
python -c "from pipeline.allometric import calculate_carbon; print(calculate_carbon(30,18,'Tectona grandis').co2eq_kg)"  # ~1233
# pipeline เต็ม: ดู services/ml/pipeline/main.py + services/api/app/services/pipeline_runner.py
```

### Mobile (`apps/mobile`)
```bash
flutter pub get
.\scripts\run-dev.ps1   # Windows: อ่าน .env → --dart-define (ต้องมี Android emulator/device ก่อน)
# main.dart ยังไม่ init Supabase (TODO) → รันได้แม้ไม่มี key
# API URL: emulator=http://10.0.2.2:8000 · เครื่องจริง=IP LAN + uvicorn --host 0.0.0.0
```

---

## กติกา / Conventions (สำคัญ — กันพลาดซ้ำ)

1. **Web landing = Tailwind + server component เท่านั้น** — **ห้าม** styled-jsx หรือ canvas 3D
   (styled-jsx ไม่ SSR ใน App Router → เรนเดอร์ unstyled บน prod มาแล้ว)
2. **Vercel env var** ต้องตั้งด้วย `vercel env add NAME production --value "<v>" --no-sensitive --force --yes`
   (pipe/stdin ได้ค่าว่างเมื่อ agent รัน CLI)
3. **ห้าม emoji ใน `print()` ของ Python บน Windows** (cp874 → uvicorn crash) — ใช้ ASCII
4. **3D viewer:** vertex color ต้องแปลง sRGB→linear ด้วย `THREE.Color` (ไม่งั้นสีเพี้ยน)
5. **Honesty ethos:** รายงานตัวเลขจริง + ข้อจำกัด ห้าม oversell (เช่น wood IoU = 0.42 พูดตามจริง)
6. **species_db.csv** = source of truth ค่า allometric · **โค้ดคือความจริง** เอกสารเป็น target
7. อย่าทับไฟล์ report ต้นฉบับ — เซฟเป็นไฟล์ใหม่เสมอ

---

## สถานะปัจจุบัน (2026-07-16)

**✅ เสร็จ:** ML pipeline 8 ขั้น (species = stub), allometric (tests ผ่าน), wood-leaf เทรน Wan 2021
(mean IoU 0.61/wood 0.42), backend async-job (34 tests), web landing ใหม่ (nature-template) live,
3D viewer, E2E ผ่าน tunnel ได้คาร์บอนจริง

**⚠️ ค้าง:**
- Rebrand `CarbonScan AI → TreeQ Carbon Platform`: **เสร็จแค่ apps/web** · เหลือ mobile/docs/proposal/README/GitHub-repo-name/logo.png
- Species classifier (ขั้น 7) = stub → ต้องเทรน ResNet จริง
- Dataset: research+verify open dataset (LeWoS/FOR-instance) เพิ่ม → retrain ดัน wood IoU (อาจารย์สั่งเลิกเก็บข้อมูลไม้ไทยเอง ใช้ open dataset แทน)
- Deploy API+worker จริง (RunPod/Railway) — ตอนนี้ demo ผ่าน Cloudflare tunnel
- verify allometric coefficients กับ TGO Guideline 2017

---

## สิ่งที่ทำร่วมกันมาล่าสุด (session changelog — ให้ Codex เข้าใจ context ต่อเนื่อง)

เรียงใหม่→เก่า (ดู `git log` ประกอบ):
1. **Master spec** `docs/PROJECT_SPEC.md` (d033ed0) — เอกสาร context ฉบับเต็ม
2. **Rebrand → TreeQ Carbon Platform** บน web (aa1ea85) — verify live แล้ว
3. **Rebuild landing เป็น nature-template** Tailwind ไม่มี 3D (68f168b) — แก้บั๊ก styled-jsx ที่เรนเดอร์พังบน prod
4. **Premium landing เดิม (3D canvas)** (bcbeb3a) — *ถูกแทนแล้ว* แต่เป็นที่มาของบทเรียน styled-jsx
5. **แก้ emoji crash** uvicorn บน Windows (6ca8693)
6. **Async-job backend** (Phase 2) — jobs table, JobStore, worker, endpoints POST/GET /jobs (34 tests)
7. **Dataset pivot** — อาจารย์ให้ใช้ open dataset เทรน wood-leaf (เลิกเก็บไม้ไทยเอง)
8. **Wire web viewer → job API** + Supabase token (dbcb6df)

> เอกสารเชิงลึกเพิ่มเติม: `docs/ml/PIPELINE.md`, `docs/ml/ALLOMETRIC.md`, `docs/ml/WOODLEAF_RESULTS.md`,
> `docs/superpowers/plans/2026-07-10-async-job-pipeline.md`

---

## Deployment

| ส่วน | Prod | Demo |
|---|---|---|
| Web | Vercel `treeqcarbon.vercel.app` | เหมือนกัน |
| API+ML | (target Railway/RunPod GPU) | Cloudflare quick tunnel → local API |
| DB/Auth | Supabase | เหมือนกัน |

สคริปต์เปิด backend demo: `C:\Users\Acer\OneDrive\Desktop\CarbonScrip\start_backend.bat`

---

## Preferences ของผู้ใช้

- ตอบ **ภาษาไทย** (technical terms EN ได้)
- โฟกัส "ทำให้กรรมการ NSC ว้าว" — Deep Tech + visual storytelling
- **อย่า over-engineer** — prototype ที่เสร็จ > vision สมบูรณ์แต่ไม่เสร็จ
- ทุก decision ที่มีค่าใช้จ่าย → "นักศึกษาจ่ายไหวไหม"
- verify ก่อนเคลม — รันจริง/ดูผลจริง อย่าเดา
