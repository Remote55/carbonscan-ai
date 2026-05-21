# ADR 0001: Monorepo Structure (pnpm + Turborepo)

- **Status:** Accepted
- **Date:** 2026-05-20
- **Deciders:** User (Team Lead)

---

## Context

CarbonScan AI ประกอบด้วย 4 ส่วนที่ทำงานร่วมกัน:
1. Web Dashboard (Next.js)
2. Mobile App (Flutter)
3. Backend API (Python/FastAPI)
4. ML Pipeline (Python/PyTorch)

นอกจากนี้ยังมี shared code:
- Design tokens (จาก Person B)
- TypeScript types (auto-gen จาก API)
- (อาจมี) Shared UI components

**คำถาม:** จัด repository ยังไง?

---

## Decision

ใช้ **Monorepo** structure ด้วย **pnpm workspaces** + **Turborepo** สำหรับ orchestration

```
carbonscan-ai/
├── apps/
│   ├── web/         (Next.js)
│   └── mobile/      (Flutter — outside Node but in folder)
├── services/
│   ├── api/         (Python)
│   └── ml/          (Python)
├── packages/
│   ├── design-tokens/
│   ├── ui/
│   └── types/
```

---

## Alternatives Considered

### Option A: Polyrepo (1 repo ต่อ project)
- ✅ Clear ownership
- ✅ Independent CI/CD
- ❌ ลำบากเรื่อง shared types
- ❌ Cross-repo PRs ลำบาก
- ❌ Setup ครั้งแรกเยอะ (clone 4 repos)

### Option B: Monorepo (pnpm + Turborepo) ✅ chosen
- ✅ Single source of truth
- ✅ Shared types auto-sync
- ✅ Onboard ง่าย (clone 1 repo)
- ✅ Atomic changes cross-services
- ⚠️ Larger repo (แต่ < 1GB คาดว่า)

### Option C: Nx (alternative monorepo tool)
- ✅ Powerful caching, code generation
- ❌ Learning curve สูงกว่า
- ❌ Overkill สำหรับทีม 3 คน

---

## Consequences

### Positive
- ทีม onboard เร็ว
- Refactor cross-package ปลอดภัย
- Single PR สามารถแก้ Backend + Frontend พร้อมกัน
- Turborepo cache ทำให้ CI เร็ว

### Trade-offs
- ⚠️ Flutter (apps/mobile) ไม่ได้รับประโยชน์จาก pnpm workspace (Dart ใช้ pubspec แยก)
- ⚠️ Python (services/*) ไม่ได้รับประโยชน์เต็มเช่นกัน (ใช้ pip/poetry แยก venv)
- ⚠️ Repo size อาจใหญ่ขึ้นเมื่อมี ML models / datasets — ใช้ Git LFS + .gitignore patterns

### Neutral
- ℹ️ ใช้ Conventional Commits + Changesets สำหรับ versioning (ถ้า open-source ภายหลัง)

---

## Follow-up Actions

- [x] Setup `pnpm-workspace.yaml`
- [x] Setup `turbo.json`
- [x] Add `.gitignore` รวมทุก language
- [ ] Setup GitHub Actions cache for Turborepo (ภายหลัง)

---

## References

- [pnpm workspaces docs](https://pnpm.io/workspaces)
- [Turborepo docs](https://turbo.build/repo/docs)
- [Vercel Monorepo template](https://vercel.com/templates/next.js/monorepo-turborepo)
