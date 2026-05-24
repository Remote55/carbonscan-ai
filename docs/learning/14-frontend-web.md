# บท 14 — Frontend Web (Next.js + Three.js + Leaflet)

> 🎯 **เป้าหมาย:** เข้าใจ tech stack ของ Web app + ทำไมเลือกแต่ละ library
> 📚 **พื้นฐาน:** [บท 03 — Architecture](03-architecture.md)
> ⏱️ **เวลา:** ~25 นาที

---

## 1. Web App ทำอะไร

📂 **`apps/web/`** — Next.js 14 application

**Pages หลัก:**
- `/` — Landing
- `/signup`, `/login` — Auth
- `/dashboard` — รายการ scans, สถิติ
- `/dashboard/scans/[id]` — 3D Viewer + tree details
- `/dashboard/map` — GIS Map ของทุกต้น
- `/dashboard/upload` — Upload .las file
- `/marketplace` — B2B carbon credit market
- `/marketplace/[plot_id]` — Detail + checkout

---

## 2. Tech Stack แบบละเอียด

### 2.1 Core Framework

| Library | Version | Purpose |
|---|---|---|
| **Next.js** | 14 (App Router) | React framework with SSR/RSC |
| **React** | 18 | UI library |
| **TypeScript** | 5 | Type safety |
| **pnpm** | 9 | Package manager (faster than npm) |
| **Turborepo** | 1.13 | Monorepo build orchestration |

**ทำไมเลือก Next.js 14 (App Router):**
- ✅ **React Server Components** — render บน server → ไม่ส่ง JS ลูกค้าเยอะ
- ✅ **Server Actions** — มี API ใน component file ได้เลย
- ✅ **SEO out-of-box** — สำคัญสำหรับ marketplace public pages
- ✅ **Edge runtime** — deploy ไป Vercel Edge
- ✅ **ระบบนิเวศ React** ใหญ่ที่สุด

### 2.2 UI / Styling

| Library | Purpose |
|---|---|
| **Tailwind CSS 3.4** | Utility-first styling |
| **shadcn/ui** | Component library (copy-paste, ไม่ใช่ npm package) |
| **@base-ui/react** | Headless components (radix-style) |
| **framer-motion** | Animations |
| **lucide-react** | Icon set |
| **sonner** | Toast notifications |
| **clsx + tailwind-merge** | Conditional className helpers |

**ทำไม shadcn/ui ไม่ใช่ Material UI:**
- ✅ **Copy-paste** — แก้ source code ได้เลย
- ✅ **Bundle size เล็ก** — เอาเฉพาะที่ใช้
- ✅ **Professional design** — minimal, modern

### 2.3 State Management

| Library | Purpose |
|---|---|
| **@tanstack/react-query** | Server state (API caching, refetching) |
| **react-hook-form** | Form state + validation |
| **zod** | Schema validation (with @hookform/resolvers) |

**ไม่ใช้ Redux** — เพราะ TanStack Query จัดการ server state ดีกว่า + local state ใช้ useState/useReducer พอ

### 2.4 Authentication

| Library | Purpose |
|---|---|
| **@supabase/ssr** | Server-side Supabase client |
| **@supabase/supabase-js** | Client-side Supabase client |

**Flow:**
```
1. User login → Supabase Auth → returns JWT
2. JWT stored in HTTP-only cookie (secure)
3. Middleware (apps/web/src/middleware.ts) verify JWT on each request
4. Server Components use createServerClient() to fetch user
5. API endpoints get user from JWT
```

### 2.5 3D Visualization ⭐ (Wow Feature)

| Library | Purpose |
|---|---|
| **three** | Core 3D library (WebGL) |
| **@react-three/fiber** (R3F) | React renderer for Three.js |
| **@react-three/drei** | R3F helpers (OrbitControls, Stats, etc.) |
| **three-stdlib** | Extra loaders |

**Usage example:**
```tsx
<Canvas>
  <ambientLight />
  <pointLight position={[10, 10, 10]} />
  <OrbitControls />
  <Points positions={pointCloudData} colors={woodLeafColors} size={0.05} />
</Canvas>
```

**Phase 3 enhancement:** ใช้ **potree-core** สำหรับ point clouds > 1M points (octree LOD)

### 2.6 GIS Map

| Library | Purpose |
|---|---|
| **leaflet** | Map library (free, mature) |
| **react-leaflet** | React wrapper |
| **leaflet.markercluster** | Cluster markers (Phase 2) |

**Tile source:** OpenStreetMap (free, no API key needed)

### 2.7 Charts + Data Viz

| Library | Purpose |
|---|---|
| **recharts** | React charts (bar, line, pie) |

**Usage:** Per-tree carbon bar chart, plot summary

### 2.8 File Upload

| Library | Purpose |
|---|---|
| **react-dropzone** | Drag-and-drop file picker |
| **tus-js-client** | Resumable upload protocol |

**Why tus protocol:**
- ✅ Resume after network drop
- ✅ Chunked upload (สำหรับ 500MB .las files)
- ✅ Supported by Supabase Storage

### 2.9 PDF Generation

| Library | Purpose |
|---|---|
| **@react-pdf/renderer** | Client-side PDF generation |

**Phase 2:** Generate Carbon Certificate PDF in browser

### 2.10 Date / Utility

| Library | Purpose |
|---|---|
| **date-fns** | Date formatting (smaller than moment.js) |

---

## 3. Folder Structure

```
apps/web/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # / (landing)
│   │   ├── layout.tsx
│   │   ├── (auth)/            # auth pages (group)
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── (dashboard)/       # logged-in pages (group)
│   │   │   ├── dashboard/
│   │   │   ├── upload/
│   │   │   └── scans/[id]/
│   │   ├── marketplace/
│   │   └── api/               # Route handlers
│   ├── components/             # Shared components
│   │   ├── ui/                # shadcn primitives
│   │   ├── viewer/            # 3D viewer
│   │   └── map/               # Leaflet map
│   ├── lib/
│   │   ├── supabase.ts        # Client-side Supabase
│   │   ├── supabase-server.ts # Server-side Supabase
│   │   └── utils.ts
│   ├── hooks/
│   └── middleware.ts          # Route protection
├── public/
├── package.json
└── next.config.mjs
```

---

## 4. Running Locally

```bash
cd apps/web
cp .env.example .env.local      # Edit with Supabase credentials
pnpm install                    # หรือ pnpm install จาก root (workspace)
pnpm dev                        # localhost:3000
```

---

## 5. Build + Deploy

| Command | Effect |
|---|---|
| `pnpm dev` | Dev server with hot reload |
| `pnpm build` | Production build |
| `pnpm start` | Run production build |
| `pnpm test` | Vitest unit tests |
| `pnpm lint` | ESLint |
| `pnpm type-check` | tsc --noEmit |

**Deploy:** Vercel auto-deploy from `main` branch (CI/CD ใน [บท 19](19-devops-cicd.md))

---

## 6. ❓ คำถามตรวจสอบความเข้าใจ

1. **App Router ของ Next.js 14 ต่างจาก Pages Router (Next.js 12) ยังไง?**
2. **ทำไม shadcn/ui ไม่ใช่ Material UI?**
3. **React Three Fiber (R3F) คืออะไร? ทำไมไม่ใช้ Three.js ตรงๆ?**
4. **TanStack Query (React Query) แก้ปัญหาอะไร?**
5. **tus protocol ดียังไงสำหรับ upload .las file?**

---

## 7. อ่านต่อ

- [บท 15 — Frontend Mobile (Flutter)](15-frontend-mobile.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
