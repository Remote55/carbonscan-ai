# บท 19 — DevOps / CI / CD

> 🎯 **เป้าหมาย:** เข้าใจ Git workflow + CI pipelines + Deploy process
> 📚 **พื้นฐาน:** [บท 18 — Tools & Hardware](18-tools-hardware.md)
> ⏱️ **เวลา:** ~20 นาที

---

## 1. Git Workflow

### 1.1 Branching Strategy

```
main                    ← Production-ready
  ↑ (merge via PR)
feat/sprint0-foundations  ← Feature branches
feat/api-real-upload
fix/mobile-build-issue
docs/learning-guide
```

**Naming convention:**
- `feat/<name>` — new features
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation
- `chore/<name>` — refactor, deps, etc.

### 1.2 Branch Protection

`main` is protected:
- ✅ Require PR (no direct push)
- ✅ Require status checks (CI must pass)
- ✅ Require linear history (no merge commits)
- ✅ Code owner review (CODEOWNERS)
- ❌ Force pushes (disabled)

### 1.3 Commit Convention

```
<type>(<scope>): <subject>

[body]

[footer]
```

**Types:** `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `ci`

**Examples:**
```
feat(ml): validate pipeline on Demol 2021 Belgium dataset

Runs full pipeline on 65 trees from peer-reviewed
destructive sampling reference dataset.

Co-Authored-By: ...
```

### 1.4 PR Workflow

```
1. Branch off main: git checkout -b feat/foo
2. Commit changes: git commit -m "feat(scope): ..."
3. Push: git push origin feat/foo
4. Create PR via gh CLI: gh pr create
5. CI runs automatically
6. Reviewer reviews
7. Merge via squash (keeps main clean)
```

---

## 2. CI/CD with GitHub Actions

### 2.1 5 Workflows ใน `.github/workflows/`

| File | Triggers | What it does |
|---|---|---|
| `ci-api.yml` | PR / push to main, changes in `services/api/` | Lint + type-check + pytest + Supabase migrations |
| `ci-ml.yml` | PR / push, `services/ml/` | Lint + pytest (25 tests) |
| `ci-mobile.yml` | PR / push, `apps/mobile/` | `flutter analyze` + `flutter test` + `flutter build apk` |
| `ci-web.yml` | PR / push, `apps/web/` | `pnpm lint` + `pnpm type-check` + `pnpm test` + `pnpm build` |
| `codeql.yml` | PR / push / weekly | GitHub security scanning (SAST) |

### 2.2 Job Structure (typical)

```yaml
name: CI API
on:
  push:
    branches: [main]
    paths: ['services/api/**', '.github/workflows/ci-api.yml']
  pull_request:
    paths: ['services/api/**']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install poetry
      - run: poetry install
      - run: poetry run alembic upgrade head
      - run: poetry run ruff check app/
      - run: poetry run mypy app/
      - run: poetry run pytest --cov
```

### 2.3 CI Performance

| Workflow | Avg duration | Notes |
|---|---|---|
| ci-ml | 1-2 min | Most tests are unit (no GPU) |
| ci-api | 2-3 min | Includes Postgres + migrations |
| ci-mobile | 5-7 min | Flutter build APK is slow |
| ci-web | 2-3 min | Next.js build |
| codeql | 10-15 min | Security scan all langs |

---

## 3. Deploy Pipeline

### 3.1 Web → Vercel

```
1. Push to main
2. Vercel webhook triggers
3. Vercel pulls latest, runs pnpm build
4. Deploy to edge network globally
5. Custom domain auto-routed
```

**Preview deploys:** Every PR gets a preview URL — review เปลี่ยนแปลงก่อน merge

### 3.2 API → Railway

```
1. Push to main
2. Railway pulls Dockerfile
3. Build image
4. Run alembic migrations
5. Deploy + health check
```

### 3.3 Mobile → Manual

Phase 1: Build APK locally, share via Google Drive

Phase 2:
- **Codemagic / Bitrise** for CI build + signed release
- **Firebase App Distribution** for beta testers
- **Google Play Console** for production

### 3.4 ML Worker → RunPod

Docker image hosted on **Docker Hub** or **GitHub Container Registry**:

```dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

RUN apt update && apt install -y python3.11 python3-pip
COPY services/ml/pyproject.toml /app/
RUN cd /app && poetry install

COPY services/ml /app/services/ml
WORKDIR /app/services/ml

CMD ["python", "worker.py"]
```

RunPod pulls image + auto-scales based on queue depth

---

## 4. Environment Management

### 4.1 .env Files

```
apps/web/.env.local        ← Local dev (gitignored)
apps/web/.env.example      ← Template (committed)
services/api/.env          ← Local dev (gitignored)
services/api/.env.example  ← Template (committed)
```

### 4.2 Secrets in Production

| Platform | Secrets storage |
|---|---|
| Vercel | Project settings → Environment Variables |
| Railway | Service settings → Variables |
| Supabase | Project settings → API keys |
| GitHub Actions | Repo settings → Secrets |

---

## 5. Monitoring

### 5.1 Sentry (Errors)

```typescript
// apps/web/src/lib/sentry.ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
});
```

Captures:
- JS errors (Web)
- Python exceptions (API + ML)
- Flutter crashes (Mobile)

### 5.2 Supabase Logs

Dashboard → Logs Explorer
- Database queries
- Auth events
- Storage operations

### 5.3 GitHub Actions Logs

Every CI run logged in Actions tab — debug fails

---

## 6. CODEOWNERS

```
# .github/CODEOWNERS
* @user
apps/web/        @person-a
apps/mobile/     @user
services/api/    @user
services/ml/     @user
docs/design/     @person-b
```

**Effect:** PR ที่แตะ `apps/web/` ต้องมี Person A approve

---

## 7. ตัวอย่าง PR Flow

```
1. git checkout -b feat/api-real-upload
2. Edit code...
3. git add . && git commit -m "feat(api): real upload endpoint"
4. git push origin feat/api-real-upload
5. gh pr create --title "..." --body "..."
6. CI runs (5-10 min)
7. Self-review on GitHub
8. Request review จาก Person A (ถ้าแตะ web)
9. Fix feedback
10. Squash merge to main
11. Vercel + Railway auto-deploy
12. Monitor Sentry for 30 min
```

---

## 8. ❓ คำถามตรวจสอบความเข้าใจ

1. **ทำไม main branch ต้อง protect?**
2. **5 CI workflows ทำอะไรบ้าง?**
3. **Preview deploys (Vercel) ดียังไง?**
4. **CODEOWNERS ใช้ทำอะไร?**
5. **Sentry vs Supabase Logs — ต่างกันยังไง?**

---

## 9. อ่านต่อ

- [บท 20 — Datasets](20-datasets.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
