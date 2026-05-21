# ADR 0006: Team Ownership Model

- **Status:** Accepted
- **Date:** 2026-05-20
- **Deciders:** User (Team Lead)

---

## Context

ทีม CarbonScan AI มี 3 คน ทักษะต่างกัน:
- **User** (Team Lead): AI/ML, Python, Mobile, Backend
- **Person A**: Frontend / Web Dev
- **Person B**: UI/UX / Design / Content

ต้องตัดสินใจ:
- ใครเป็น owner ของ folder/area ไหน
- ใครรับผิดชอบ critical path
- ใครเป็น approver ของ PRs

---

## Decision

ใช้ **Code Ownership Model** กับ folder-level ownership และ designated reviewers

### Ownership Matrix

| Path | Primary Owner | Secondary | Reviewer |
|---|---|---|---|
| `apps/web/` | Person A | User | User + Person B (UX) |
| `apps/mobile/` | User | (none) | User |
| `services/api/` | User | (none) | User |
| `services/ml/` | User | (none) | User |
| `packages/design-tokens/` | Person B | Person A | Person A |
| `packages/ui/` | Person A | Person B | Person B |
| `packages/types/` | Person A (gen) | User (source) | User |
| `docs/` | All | — | User |
| `docs/design/` | Person B | — | Person A |
| `docs/ml/` | User | — | (Advisor) |
| `proposal/` | User | Person B | User + Advisor |
| `assets/brand/` | Person B | — | Person B |
| `infrastructure/` (CI, Docker) | User | — | User |

### Decision Authority

| Type | Who Decides | When to Consult |
|---|---|---|
| Architectural (cross-folder) | **User** | Always |
| Web technical (within apps/web) | **Person A** | Architectural ↑ |
| Design (visual, brand) | **Person B** | If breaks brand consistency |
| Proposal content | **User** | Person B (visual), Advisor (technical) |

---

## RACI Matrix

| Activity | User | Person A | Person B | Advisor |
|---|---|---|---|---|
| Architecture design | **R/A** | C | I | C |
| Proposal writing | **R/A** | C | C | A |
| Web development | C | **R/A** | C (UX) | I |
| Mobile development | **R/A** | I | C (design) | I |
| ML pipeline | **R/A** | I | I | C |
| Backend API | **R/A** | C (API contract) | I | I |
| Visual design | I | C (implementation) | **R/A** | I |
| Brand identity | I | C | **R/A** | I |
| Demo video | A | C | **R** | A |
| Final pitching | **R/A** | R | R | A |

**Legend:**
- **R** = Responsible (does the work)
- **A** = Accountable (final decision, signs off)
- **C** = Consulted (input gathered)
- **I** = Informed (kept in loop)

---

## PR Review Rules

### Default Rules
- ทุก PR ต้องมี approval อย่างน้อย 1 คน
- PR ที่แตะ `proposal/` หรือ `services/ml/` → User ต้อง approve
- PR ที่แตะ `apps/web/` → Person A ต้อง approve (ถ้าเขาเป็นผู้แก้, User approve)
- PR ที่แตะ design/visual → Person B ต้อง approve

### Auto-merge Conditions
- PR เปลี่ยน docs only (no code) → ใครก็ approve ได้
- Dependabot PRs → auto-merge ถ้า tests ผ่าน

### Escalation
- ถ้า reviewer ไม่ตอบใน 48 ชม. → escalate ใน Line/Discord
- ถ้ามี disagreement → User เป็น tiebreaker

---

## Workload Balancing

### Heuristic
- ถ้า 1 คนมี > 5 open PRs / > 10 in-progress tasks → ทีมช่วย rebalance
- ถ้ามี blocker > 24 ชม. → escalate ใน standup

### Standup
- ทุก Mon/Wed/Fri 21:00 น. (15 นาที)
- รูปแบบ:
  - เมื่อวาน: ทำอะไร
  - วันนี้: จะทำอะไร
  - Blockers: มีอะไรติด

---

## Conflict Resolution

### Disagreement on Approach
1. Discuss async ใน PR comments หรือ GitHub Discussions
2. ถ้ายังตกลงไม่ได้ ภายใน 24 ชม. → call sync (Line/Discord)
3. ถ้ายังตกลงไม่ได้ → User decides (final, but documents in ADR)

### Workload Imbalance
1. Raise ใน standup
2. ทบทวน scope → ตัดอะไรได้ไหม
3. ขอความช่วยเหลือจากที่ปรึกษา / external

### Quality Issues
- Be **kind, direct, specific** ในการ feedback
- "I noticed X, could we try Y because Z?" ดีกว่า "X is wrong"

---

## Cross-Team Dependencies

### Person A ↔ User (Frontend ↔ Backend)
- API contract: defined ใน `docs/API.md`
- Mock API ใน Phase 1 ขณะที่ Backend ยังไม่พร้อม
- Weekly sync (Friday) สำหรับ API changes

### Person A ↔ Person B (Frontend ↔ Design)
- Design handoff: Figma file shared with Person A
- Component spec: Figma annotation + Notion/Markdown
- Weekly design review (Friday)

### Person B ↔ User (Design ↔ Proposal/Mobile)
- Proposal: User writes, Person B layouts
- Mobile mockup: Person B design, User implements
- Brand assets: Person B exports, User integrates

---

## Knowledge Sharing

### Documentation Requirements
- **New feature** → update README ของ app/service นั้น
- **Major decision** → ADR ใน `docs/decisions/`
- **API change** → update `docs/API.md`
- **DB change** → migration + update `docs/DATA_MODEL.md`

### Pair Programming
- เมื่อ Person A ทำ 3D Viewer (week 6) → User pair 1-2 sessions
- เมื่อ User ทำ Mobile UI → Person B pair 1-2 sessions

---

## Consequences

### Positive
- ✅ Clear ownership = ไม่มี "ใครต้องทำ?"
- ✅ Code review balanced (ไม่ใช่ User คนเดียว approve)
- ✅ Person B มี ownership ของ design (ไม่ถูก override)
- ✅ User ยังคุม critical decisions

### Trade-offs
- ⚠️ User เป็น bottleneck สำหรับ approval หลายอย่าง — ต้อง batch review
- ⚠️ Person B may feel less involved in technical decisions — schedule sync

---

## Follow-up Actions

- [ ] Add `CODEOWNERS` file ใน `.github/`
- [ ] Setup PR auto-assignment ตาม path
- [ ] Schedule recurring Friday sync
- [ ] Create shared Notion/Linear for task tracking (ถ้าไม่ใช้ GitHub Issues)

---

## References

- [GitHub CODEOWNERS docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [RACI matrix explanation](https://en.wikipedia.org/wiki/Responsibility_assignment_matrix)
