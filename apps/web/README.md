# 🌐 Web Dashboard (Next.js)

> **Owner:** Person A
> **Tech:** Next.js 14 + TypeScript + Tailwind + shadcn/ui + Three.js + Leaflet

---

## Overview

Web Dashboard เป็น primary interface สำหรับ:
- **Industrial users** (ซื้อ Carbon Credits)
- **Community users** (ดูต้นไม้ที่ตัวเองสแกน + รายได้)
- **Auditors** (ตรวจสอบ + อนุมัติ)
- **Public** (Marketplace browsing)

---

## Pages / Routes

```
/                           → Landing page (marketing)
/login, /signup             → Authentication
/dashboard                  → Authenticated home (role-based redirect)
/dashboard/community        → Community user view
/dashboard/industrial       → Industrial user view
/dashboard/auditor          → Auditor view (verification queue)
/dashboard/admin            → Admin (analytics, user mgmt)
/marketplace                → Public carbon marketplace
/trees/{id}                 → Tree detail (3D Viewer + stats)
/plots/{id}                 → Plot summary + map
/upload                     → File upload (.las/.laz)
/reports                    → Generated reports list
/api/...                    → API Route Handlers (for server-side ops)
```

---

## Folder Structure

```
apps/web/
├── README.md                         (this file)
├── PERSON_A_GUIDE.md                 ← Person A onboarding
├── package.json
├── next.config.js
├── tsconfig.json
├── tailwind.config.ts
├── components.json                   (shadcn config)
├── .env.example
├── .env.local                        (gitignored)
├── public/
│   ├── favicon.ico
│   ├── og-image.png                  (social sharing)
│   └── assets/                       (static images)
├── src/
│   ├── app/                          (Next.js App Router)
│   │   ├── layout.tsx                Root layout
│   │   ├── page.tsx                  Landing
│   │   ├── (auth)/                   Auth route group
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   ├── (dashboard)/              Protected route group
│   │   │   ├── layout.tsx            Sidebar layout
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── upload/page.tsx
│   │   │   └── trees/[id]/page.tsx
│   │   ├── marketplace/page.tsx
│   │   └── api/                      API routes
│   │       └── auth/[...nextauth]/route.ts
│   ├── components/
│   │   ├── ui/                       (shadcn primitives)
│   │   ├── viewer/                   3D viewer components
│   │   │   ├── PointCloudViewer.tsx
│   │   │   └── TreeMesh.tsx
│   │   ├── map/                      GIS components
│   │   │   ├── TreeMap.tsx
│   │   │   └── PlotPolygon.tsx
│   │   ├── marketplace/
│   │   │   ├── ListingCard.tsx
│   │   │   └── CheckoutDialog.tsx
│   │   ├── upload/
│   │   │   └── FileDropzone.tsx
│   │   └── shared/
│   │       ├── Sidebar.tsx
│   │       └── Header.tsx
│   ├── lib/
│   │   ├── api.ts                    (API client, axios/fetch wrapper)
│   │   ├── auth.ts                   (NextAuth config)
│   │   ├── supabase.ts               (Supabase client)
│   │   └── utils.ts
│   ├── hooks/
│   │   ├── useTrees.ts               (React Query hooks)
│   │   ├── useUpload.ts
│   │   └── useJobStatus.ts           (WebSocket)
│   ├── stores/                       (Zustand)
│   │   ├── userStore.ts
│   │   └── filterStore.ts
│   ├── types/                        (re-export from packages/types)
│   └── styles/
│       └── globals.css
└── tests/
    ├── unit/
    └── e2e/                          (Playwright)
```

---

## Setup

```bash
cd apps/web

# Install (from monorepo root)
pnpm install

# Env vars
cp .env.example .env.local
# Edit .env.local with real values (ขอจาก User)

# Dev server
pnpm dev
# → http://localhost:3000

# Build
pnpm build

# Production preview
pnpm start
```

---

## Key Dependencies

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",

    "tailwindcss": "^3.4.0",
    "@radix-ui/react-*": "(via shadcn/ui)",
    "lucide-react": "^0.378.0",
    "framer-motion": "^11.2.0",

    "three": "^0.164.0",
    "@react-three/fiber": "^8.16.0",
    "@react-three/drei": "^9.105.0",
    "three-stdlib": "^2.30.0",

    "leaflet": "^1.9.0",
    "react-leaflet": "^4.2.0",

    "@tanstack/react-query": "^5.40.0",
    "zustand": "^4.5.0",

    "@supabase/supabase-js": "^2.43.0",
    "next-auth": "^4.24.0",

    "react-pdf": "^9.0.0",
    "@react-pdf/renderer": "^3.4.0",

    "react-dropzone": "^14.2.0",
    "tus-js-client": "^4.1.0",

    "zod": "^3.23.0"
  }
}
```

---

## Component Architecture

### 3D Viewer Pattern
```tsx
// components/viewer/PointCloudViewer.tsx
'use client';

import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Suspense } from 'react';
import { PointCloud } from './PointCloud';

export function PointCloudViewer({ url }: { url: string }) {
  return (
    <Canvas camera={{ position: [10, 10, 10] }}>
      <ambientLight intensity={0.5} />
      <Suspense fallback={null}>
        <PointCloud url={url} />
      </Suspense>
      <OrbitControls />
    </Canvas>
  );
}
```

### Server Component Pattern (Data Fetching)
```tsx
// app/(dashboard)/trees/[id]/page.tsx
import { getTreeById } from '@/lib/api';
import { PointCloudViewer } from '@/components/viewer/PointCloudViewer';

export default async function TreePage({ params }: { params: { id: string } }) {
  const tree = await getTreeById(params.id);

  return (
    <div>
      <h1>{tree.species_name_th}</h1>
      <PointCloudViewer url={tree.point_cloud_url} />
    </div>
  );
}
```

### React Query Hook Pattern
```tsx
// hooks/useTrees.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useTrees(filters: TreeFilters) {
  return useQuery({
    queryKey: ['trees', filters],
    queryFn: () => api.get('/trees', { params: filters }),
    staleTime: 60 * 1000, // 1 min
  });
}
```

---

## Performance Best Practices

- ✅ Use Server Components by default, `'use client'` only when needed
- ✅ `next/image` for ทุก image
- ✅ Code-split heavy components (3D viewer, map) with `dynamic()`
- ✅ Memoize expensive computations (`useMemo`, `useCallback`)
- ✅ Virtualize long lists (`react-virtual`)

---

## Testing

```bash
# Unit
pnpm test

# E2E
pnpm test:e2e

# Watch mode
pnpm test:watch
```

---

📖 **See also:**
- [PERSON_A_GUIDE.md](PERSON_A_GUIDE.md) — Detailed guide for Person A
- [docs/API.md](../../docs/API.md) — Backend API
- [docs/design/DESIGN_SYSTEM.md](../../docs/design/DESIGN_SYSTEM.md) — Design system
