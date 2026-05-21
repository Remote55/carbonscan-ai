# ADR 0003: Tech Stack Selection

- **Status:** Accepted
- **Date:** 2026-05-20
- **Deciders:** User (Team Lead)

---

## Context

ต้องเลือก tech stack หลักของโปรเจกต์โดยพิจารณา:
- ทีม 3 คน ทักษะที่มี (Python, TypeScript, Flutter)
- งบจำกัด (free tier เป็นหลัก)
- Timeline ตึง (5-6 สัปดาห์ development)
- กรรมการ NSC เป็นสาย IT (ชอบ Modern tech)
- ต้องการ Production-ready ไม่ใช่ prototype throwaway

---

## Decision

### Web Frontend
| Layer | Choice | Reason |
|---|---|---|
| Framework | **Next.js 14** | App Router, Server Components, SEO, deployment ง่าย |
| Language | **TypeScript** | Type safety, mature ecosystem |
| CSS | **Tailwind CSS** | Speed, consistency |
| Components | **shadcn/ui** | Accessible, customizable, ไม่ lock-in |
| 3D | **Three.js + React Three Fiber** | Industry standard |
| Maps | **Leaflet + react-leaflet** | Open source, simpler than Mapbox |
| State | **TanStack Query + Zustand** | Best-in-class for server + client state |

### Mobile
| Layer | Choice | Reason |
|---|---|---|
| Framework | **Flutter** | Best camera performance, single codebase |
| Language | **Dart** | Type-safe, hot reload |
| State | **Riverpod** | Modern, testable |
| ML | **TFLite** | Native support, fast on-device |

### Backend
| Layer | Choice | Reason |
|---|---|---|
| Framework | **FastAPI** | Async, auto-Swagger, Pydantic v2 |
| Language | **Python 3.11** | Same as ML, mature, team knows |
| ORM | **SQLAlchemy 2.0 + asyncpg** | Mature, async-ready |
| Auth | **Supabase Auth** | Free, ready, social login |

### Database
| Layer | Choice | Reason |
|---|---|---|
| DB | **PostgreSQL 16** | Mature, supports JSON, ACID |
| Spatial | **PostGIS 3.4** | Required for spatial queries |
| Hosting | **Supabase** | Free tier, all-in-one (DB + Auth + Storage) |

### ML / AI
| Layer | Choice | Reason |
|---|---|---|
| Framework | **PyTorch** | Better research ecosystem than TF |
| Point Cloud | **PointNet++** | Mature, good baseline |
| 3D Library | **Open3D** | Best Python point cloud library |
| LAS I/O | **laspy + PDAL** | Industry standard |
| Photogrammetry | **COLMAP + OpenMVS** | Open source, scriptable |
| Tracking | **Weights & Biases** | Free tier, beautiful dashboards |

### DevOps
| Layer | Choice | Reason |
|---|---|---|
| Monorepo | **pnpm + Turborepo** | Fast, modern |
| Deploy Web | **Vercel** | Free, perfect for Next.js |
| Deploy API | **Railway** | $5/mo, super easy |
| Deploy ML | **RunPod Serverless** | Pay-per-second GPU |
| CI | **GitHub Actions** | Free for public repos |

---

## Alternatives Considered

### Web: Vite + React vs Next.js
- Vite faster dev experience
- แต่ Next.js ดีกว่าสำหรับ SEO, ISR, file-based routing
- → Next.js ✅

### Mobile: Flutter vs React Native
- React Native: ทีมรู้ React อยู่แล้ว
- แต่ Flutter render performance ดีกว่ามากสำหรับ camera-heavy app
- → Flutter ✅

### Backend: FastAPI vs Django REST vs Node.js (Express/Nest)
- Django: too heavy, sync by default
- Node.js: ต้องใช้ pythonต่อกับ ML pipeline อยู่แล้ว
- FastAPI: native async, auto-docs, Pydantic v2 = match กับ Python ML
- → FastAPI ✅

### DB: PostgreSQL+PostGIS vs MongoDB
- MongoDB: schema-less, ดีสำหรับ rapid iteration
- แต่: ต้องใช้ spatial queries (PostGIS unbeatable)
- + financial records (transactions) ต้อง ACID
- → PostgreSQL + PostGIS ✅

### ML: PyTorch vs TensorFlow
- TF: deployment ecosystem ดี (TFLite, TF Serving)
- PyTorch: research community ดีกว่า, ส่วนใหญ่ pretrained models บน PyTorch
- → PyTorch (export TFLite ก่อนใช้ Mobile) ✅

### GPU: RunPod vs Modal vs AWS SageMaker
- AWS SageMaker: ราคาแพง, complex
- Modal.com: ดี แต่ใหม่
- RunPod Serverless: ราคาถูก, simple
- → RunPod ✅

---

## Consequences

### Positive
- ทีมรู้ technology หลัก ๆ อยู่แล้ว
- ทุกอย่าง open source / free tier
- Modern stack → กรรมการ NSC ชอบ
- Vendor lock-in ต่ำ (Supabase = open source, RunPod = easy migrate)

### Trade-offs
- ⚠️ ต้องเรียน new things: React Three Fiber, Open3D, FastAPI async
- ⚠️ Cross-platform iOS build ต้องใช้ Codemagic (เพราะไม่มี Mac)
- ⚠️ Supabase free tier มี limit (500MB DB, 1GB storage) — พอสำหรับ NSC

### Neutral
- ℹ️ ถ้าโปรเจกต์ขยาย production scale ต้อง upgrade Supabase Pro ($25/mo)

---

## Decision Matrix

| Criterion | Weight | Score 1-5 | Weighted |
|---|---|---|---|
| Team skills match | 5 | 4 | 20 |
| Cost (free/cheap) | 5 | 5 | 25 |
| Speed of development | 4 | 4 | 16 |
| Production readiness | 4 | 4 | 16 |
| NSC "wow factor" | 3 | 4 | 12 |
| Vendor lock-in (lower better) | 3 | 4 | 12 |
| **Total** | | | **101/120** |

---

## Follow-up Actions

- [x] Setup `package.json` with dependencies
- [x] Setup `pyproject.toml` for both Python services
- [x] Setup `pubspec.yaml` for Flutter
- [ ] Document each library's purpose in respective README
- [ ] Track major version upgrades carefully (semantic versioning)

---

## References

- [Next.js docs](https://nextjs.org/docs)
- [FastAPI docs](https://fastapi.tiangolo.com/)
- [Flutter docs](https://docs.flutter.dev/)
- [PostGIS docs](https://postgis.net/)
- [PointNet++ paper](https://arxiv.org/abs/1706.02413)
- [Supabase free tier](https://supabase.com/pricing)
- [RunPod pricing](https://www.runpod.io/pricing)
