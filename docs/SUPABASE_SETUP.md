# 🗄 Supabase Setup Guide

> [!CAUTION]
> **ส่วน schema/migration ในเอกสารนี้ล้าสมัยแล้ว — อย่าทำตาม**
>
> API ไม่มีฐานข้อมูลแล้ว ตาราง `users` `plots` `jobs` `trees` `transactions`
> `species_db` ไม่มีโค้ดไหนอ่านหรือเขียนเลย และถูกถอดออกทั้งชุดพร้อม SQLAlchemy
> กับ alembic — คำสั่ง `alembic upgrade head` ข้างล่างรันไม่ได้แล้วเพราะ alembic
> ไม่อยู่ในรีโปแล้ว
>
> ถ้าเคยทำตามเอกสารนี้ ตารางยังค้างอยู่บน Supabase — ดู
> **`docs/DATABASE_TEARDOWN.md`** ว่ามีอะไรอยู่และ SQL ที่ใช้ลบ
>
> **ส่วนที่ยังใช้ได้:** การสร้าง project, การตั้งค่า Authentication และการเก็บ
> `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_KEY` — auth คือสิ่ง
> เดียวที่ระบบยังใช้ Supabase ทำ

> Step-by-step guide สำหรับ User สร้าง Supabase project + ใส่ schema
>
> เวลาทั้งหมด: **~15 นาที**

---

## ⚡ Quick Overview

```
1. สร้าง Supabase project (free tier)         5 min
2. เปิด PostGIS extension                      1 min
3. รัน Alembic migrations (สร้าง tables)       3 min
4. Seed species_db (5 ชนิดต้นไม้)              1 min
5. สร้าง Storage buckets                       2 min
6. ใส่ env vars ใน .env files                  2 min
7. Test connection                             1 min
```

---

## Step 1: สร้าง Supabase Project

1. ไปที่ **https://supabase.com/dashboard/sign-up** สมัครด้วย GitHub
2. คลิก **New Project**
3. กรอกข้อมูล:

| Field | Value |
|---|---|
| **Project name** | `carbonscan-ai` |
| **Database password** | สร้าง strong password — **บันทึกไว้!** (จะหายไม่ได้เพราะใช้ใน DATABASE_URL) |
| **Region** | `Southeast Asia (Singapore) — ap-southeast-1` (latency ดีที่สุดจากไทย) |
| **Pricing Plan** | **Free** |

4. กด **Create new project** → รอ ~2 นาทีให้ provision เสร็จ

---

## Step 2: เก็บ Credentials

หลัง project พร้อม ไปที่ **Project Settings → API**:

| Variable | ที่หา | ใช้ที่ |
|---|---|---|
| **Project URL** | "Project URL" | `SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL` |
| **anon public key** | "Project API keys → anon public" | `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_ANON_KEY` |
| **service_role secret** | "Project API keys → service_role" ⚠️ | `SUPABASE_SERVICE_KEY` |

> ⚠️ **service_role key ห้ามใส่ใน Web frontend!** ใช้ใน Backend (`services/api/.env`) เท่านั้น

ไปที่ **Project Settings → Database**:

| Variable | ที่หา |
|---|---|
| **Connection string** (URI format) | "Connection string → URI" — แทน `[YOUR-PASSWORD]` ด้วย password ที่บันทึกใน Step 1 |

---

## Step 3: เปิด PostGIS Extension

ไปที่ **SQL Editor → New Query** → paste + Run:

```bash
# Copy from repo
cat services/api/scripts/setup_supabase.sql
```

หรือ paste โดยตรง:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

SELECT extname, extversion FROM pg_extension
WHERE extname IN ('postgis', 'pg_trgm', 'pgcrypto', 'unaccent')
ORDER BY extname;
```

ผลที่ต้องเห็น:
```
extname        | extversion
---------------+-----------
pg_trgm        | 1.6
pgcrypto       | 1.3
postgis        | 3.4.x
unaccent       | 1.1
```

---

## Step 4: รัน Alembic Migrations

ใส่ DATABASE_URL ใน `services/api/.env` แล้วรัน:

```bash
cd services/api

# Setup venv (ถ้ายังไม่มี)
python -m venv .venv
source .venv/Scripts/activate    # Windows
# source .venv/bin/activate      # macOS/Linux

# Install deps
pip install -e ".[dev]"

# Apply migrations
alembic upgrade head
```

ผลที่ต้องเห็น:
```
INFO  [alembic.runtime.migration] Context impl PostgreSQLImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial schema
```

ตรวจ tables ใน Supabase Dashboard → **Database → Tables**:
- ✅ users
- ✅ plots
- ✅ trees
- ✅ jobs
- ✅ transactions
- ✅ species_db
- ✅ alembic_version (Alembic's own tracker)

---

## Step 5: Seed Species DB

ไปที่ **SQL Editor → New Query** → paste:

```sql
-- Copy content from services/api/scripts/seed_species_db.sql
-- (5 species INSERT + verify SELECT)
```

หรือเปิดไฟล์ใน editor:
```bash
cat services/api/scripts/seed_species_db.sql
```

ผลที่ต้องเห็น:
```
name_sci             | name_th     | wood_density | agb_a  | agb_b | agb_c
---------------------+-------------+--------------+--------+-------+------
Afzelia xylocarpa    | มะค่าโมง    | 850          | 0.0612 | 2.42  | 0.66
Dipterocarpus alatus | ยางนา       | 720          | 0.0396 | 2.38  | 0.8
Tectona grandis      | สัก         | 660          | 0.0509 | 2.15  | 0.7
Bambusa spp.         | ไผ่         | 650          | 0.131  | 2.28  | 0.59
Hevea brasiliensis   | ยางพารา     | 580          | 0.0464 | 2.33  | 0.72
```

---

## Step 6: สร้าง Storage Buckets

ไปที่ **Storage → Create bucket** (4 buckets):

| Bucket Name | Public? | File Size Limit |
|---|---|---|
| `point-clouds` | 🔒 Private | 500 MB |
| `photos` | 🔒 Private | 20 MB |
| `reports` | 🌐 Public | 5 MB |
| `brand-assets` | 🌐 Public | 5 MB |

แต่ละ bucket: คลิก **New bucket** → ใส่ name → toggle "Public bucket" ตามตาราง → Save

---

## Step 7: ใส่ Env Vars

### `services/api/.env`
```env
APP_ENV=development
APP_DEBUG=true

DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...
SUPABASE_SERVICE_KEY=eyJhbGciOi...

JWT_SECRET=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256

CORS_ORIGINS=http://localhost:3000
```

### `apps/web/.env.local`
```env
NEXT_PUBLIC_SUPABASE_URL=https://[PROJECT-REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### `services/ml/.env`
```env
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOi...
```

---

## Step 7b: Apply RLS Policies (after migrations succeed)

After `alembic upgrade head` and `seed_species_db.sql` succeed, apply
Row-Level Security policies + auth sync trigger:

### Via SQL Editor

1. Open Supabase SQL Editor → New Query
2. Paste content of `services/api/scripts/rls_policies.sql`
3. Run

### Via asyncpg (Python)

```bash
cd services/api
.venv/Scripts/python.exe -c "
import asyncio, asyncpg
from pathlib import Path

async def main():
    sql = Path('scripts/rls_policies.sql').read_text(encoding='utf-8')
    setup_sql = sql.split('-- 10. Verification')[0]

    conn = await asyncpg.connect(
        host='aws-1-ap-southeast-1.pooler.supabase.com', port=5432,
        user='postgres.umuszxwwwxyvqxwhlpxf', password='YOUR-PASSWORD',
        database='postgres', statement_cache_size=0)
    await conn.execute(setup_sql)
    print('RLS applied')
    await conn.close()
asyncio.run(main())
"
```

What this does:
- Creates trigger `on_auth_user_created` (auto-syncs new auth users → public.users)
- Creates helper functions `is_admin()`, `is_auditor_or_admin()`
- Enables RLS on 5 tables (users, plots, trees, jobs, transactions)
- Adds 15 policies covering owner-only access + marketplace public read + auditor verify
- Adds storage bucket policies (point-clouds + photos private; reports + brand-assets writable by owners)

species_db stays open (reference data — no RLS).

---

## Step 8: Test Connection

### From Backend (`services/api/`)
```bash
.venv/Scripts/python.exe -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv
load_dotenv()

async def test():
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT count(*) FROM species_db'))
        print('species_db row count:', result.scalar())
    await engine.dispose()

asyncio.run(test())
"
```

ผลที่ต้องเห็น: `species_db row count: 5`

### From Web (`apps/web/`)
```bash
pnpm dev
# → http://localhost:3000 ควรโหลดได้ไม่ error
```

---

## ❓ Troubleshooting

### `psycopg.OperationalError: connection refused`
- เช็คว่า DATABASE_URL ถูกต้อง (password, project-ref)
- เช็คว่า Supabase project status = "ACTIVE_HEALTHY" (ไม่ใช่ paused)
- Free tier auto-pause หลังไม่ใช้ 1 สัปดาห์ → กด "Restore" ใน Dashboard

### `extension "postgis" does not exist`
- ทำ Step 3 ใหม่ — บางครั้ง extension ต้อง enable ผ่าน Database → Extensions UI
- ไป **Database → Extensions** → ค้น "postgis" → Enable

### `permission denied for table users` (RLS error)
- RLS เปิดอยู่แต่ policy ยังไม่ set
- ตอน dev ใช้ **service_role key** (bypass RLS) — ไม่ใช่ anon key
- Production ต้อง set policies (ดู section "Row Level Security" ใน `setup_supabase.sql`)

### Migration ค้างที่ "Running upgrade -> 0001"
- เช็คว่า PostGIS เปิดแล้ว
- ลอง `alembic downgrade base` แล้ว `alembic upgrade head` ใหม่

---

## 📚 Cost Awareness

**Free tier (Hobby) limits:**
- 500 MB database storage
- 1 GB file storage
- 5 GB bandwidth/month
- 50,000 monthly active users
- Auto-pause after 1 week of inactivity

สำหรับ NSC Prototype/Demo phase นี้พอ.

**ถ้าจะ scale Phase 4+:** Pro plan $25/mo:
- 8 GB DB
- 100 GB storage
- 250 GB bandwidth
- No auto-pause

---

📖 **See also:**
- [docs/DATA_MODEL.md](DATA_MODEL.md) — Database schema details
- [docs/decisions/0003-tech-stack-selection.md](decisions/0003-tech-stack-selection.md) — Why Supabase
- [services/api/scripts/setup_supabase.sql](../services/api/scripts/setup_supabase.sql)
- [services/api/scripts/seed_species_db.sql](../services/api/scripts/seed_species_db.sql)
- [services/api/alembic/versions/0001_initial_schema.py](../services/api/alembic/versions/0001_initial_schema.py)
