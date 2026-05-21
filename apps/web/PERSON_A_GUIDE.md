# 👤 Person A — Frontend Engineer Guide

> เอกสารฉบับเฉพาะสำหรับ Person A — รับผิดชอบ Web Dashboard ทั้งหมด

---

## 🎯 Your Mission

สร้าง **Web Dashboard** ที่:
1. กรรมการ NSC เห็นแล้วว้าว (3D Viewer + GIS Map สวย)
2. Industrial users เข้าใช้แล้วซื้อ Carbon Credits ได้จริง
3. Community users เข้าใจตัวเองมีต้นไม้กี่ต้น carbon เท่าไหร่

---

## 📅 Your 12-Week Timeline

| Week | Goal | Outputs |
|---|---|---|
| 1 (พ.ค.) | Next.js setup + Landing | Boilerplate + marketing page |
| 2 (พ.ค.) | Auth + Routing | Login/signup + protected routes |
| 3 (มิ.ย.) | Dashboard skeleton | Community + Industrial views |
| 4 (มิ.ย.) | File Upload + API connection | Upload .las working |
| 5 (มิ.ย.) | GIS Map | Leaflet + PostGIS tree pins |
| 6 (ก.ค.) | 3D Viewer (CORE) | Three.js + potree-core |
| 7 (ก.ค.) | Marketplace UI | Listings + checkout flow |
| 8 (ก.ค.) | Tree detail page | DBH chart, carbon stats |
| 9 (ก.ค.) | PDF Report | Generate downloadable reports |
| 10 (ก.ค.) | QA + Polish | Bug fixes, perf optimization |
| 11 (ส.ค.) | Demo prep | Final touches |
| 12 (ส.ค.) | Pitching support | Help record demo video |

---

## 🛠 Tech Stack You'll Master

### Required
- [x] **Next.js 14 App Router** — รู้ Server vs Client Components
- [x] **TypeScript** — Strict mode
- [x] **Tailwind CSS** — Utility-first
- [x] **shadcn/ui** — Pre-built accessible components
- [x] **TanStack React Query** — Server state
- [x] **Zustand** — Client state

### Stretch
- [ ] **React Three Fiber** — Three.js wrapper (Week 6)
- [ ] **Leaflet** — Maps (Week 5)
- [ ] **NextAuth** — Authentication (Week 2)
- [ ] **react-pdf** — PDF generation (Week 9)

---

## 📚 Learning Resources

### Must-Read (Week 1)
1. Next.js 14 App Router docs: https://nextjs.org/docs/app
2. shadcn/ui: https://ui.shadcn.com/
3. TypeScript Essentials: https://www.typescriptlang.org/docs/handbook/intro.html

### 3D / Map (Week 5-6)
1. Three.js Journey (free chapters): https://threejs-journey.com
2. R3F docs: https://docs.pmnd.rs/react-three-fiber
3. Leaflet quickstart: https://leafletjs.com/examples/quick-start/

### Recommended Channels
- **Lee Robinson** (Vercel VP) — YouTube
- **Wesley Bos** — JS courses
- **Bruno Simon** — Three.js

---

## 🏗 Week 1-2: Setup Steps

### Step 1: Initialize Next.js
```bash
cd apps/web

# Use shadcn CLI to bootstrap
pnpm dlx shadcn@latest init -d
# (เลือก: New York style, Slate base color, CSS variables)

# Add common components
pnpm dlx shadcn@latest add button card dialog input form toast
```

### Step 2: Folder Structure
ดูตาม `apps/web/README.md` section "Folder Structure"

### Step 3: Tailwind Config
```ts
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{ts,tsx,mdx}',
    '../../packages/ui/src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50: '#f0f9f4',
          // ... import from packages/design-tokens
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

### Step 4: First Component (Landing Hero)
```tsx
// src/app/page.tsx
import { Button } from '@/components/ui/button';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-forest-50">
      <section className="container mx-auto py-32 text-center">
        <h1 className="text-6xl font-bold tracking-tight text-forest-900">
          CarbonScan AI
        </h1>
        <p className="mt-6 text-xl text-forest-700">
          แปลงต้นไม้เป็น Carbon Credits ด้วย AI ที่โปร่งใส
        </p>
        <Button size="lg" className="mt-8">
          ลองใช้งานฟรี
        </Button>
      </section>
    </main>
  );
}
```

---

## 🎨 Working with Person B (Designer)

### Design Tokens
Person B จะ export tokens จาก Figma ใส่ `packages/design-tokens/`:
```ts
// packages/design-tokens/colors.json
{
  "forest": { "500": "#2D6A4F" },
  "sky": { "500": "#74C0FC" }
}
```

ใน Tailwind config import มาใช้ได้เลย

### Component Handoff Workflow
1. Person B ทำ Hi-fi mockup ใน Figma
2. Share link ให้ Person A
3. Person A ใช้ **shadcn/ui base** ปรับ style ตาม mockup
4. Person A demo ให้ Person B รีวิว
5. Adjust + iterate

### Communication
- ทุก Friday: 30-min review session
- Slack/Line: ถามได้ทันที สำหรับ small clarifications

---

## 🤝 Working with User (Backend)

### API Contract
User จะส่ง OpenAPI spec ใน `docs/API.md` + Swagger at `localhost:8000/docs`

### Type Safety
Generate TypeScript types จาก OpenAPI:
```bash
pnpm dlx openapi-typescript http://localhost:8000/openapi.json -o packages/types/src/api.ts
```

### Mock API (Week 1-3)
ระหว่างที่ User ทำ Backend ใช้ **MSW** (Mock Service Worker):
```ts
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/trees', () => {
    return HttpResponse.json({ items: mockTrees });
  }),
];
```

---

## ✅ Definition of Done (per feature)

ก่อนปิด task / merge PR เช็คทุกข้อ:

- [ ] Code compiles + ไม่มี TypeScript errors
- [ ] ESLint ผ่าน
- [ ] Component responsive (mobile + desktop)
- [ ] Loading + Error states
- [ ] Empty states (เมื่อไม่มีข้อมูล)
- [ ] Accessibility (keyboard nav, aria labels)
- [ ] Tested on Chrome + Safari + Firefox
- [ ] Lighthouse score > 80
- [ ] Docs updated (ถ้ามี breaking change)

---

## 🚨 Common Pitfalls

### 1. ใช้ Client Component เยอะเกินไป
**ผิด:**
```tsx
'use client';
// ทุกหน้าใช้
```

**ถูก:** Server Component default. Use Client only เมื่อต้อง:
- ใช้ hooks (useState, useEffect)
- Event handlers
- Browser APIs

### 2. Re-render เกินจำเป็น
ใช้ React DevTools Profiler หาส่วนที่ render บ่อย → memoize

### 3. ไม่ Handle Error States
ทุก API call ต้องมี:
- Loading skeleton
- Error fallback
- Empty state

### 4. Bundle Size ใหญ่
- Code-split heavy components (`dynamic(() => import(...))`)
- ไม่ import library ทั้งก้อน (`import { format } from 'date-fns/format'` แทน `import * as df from 'date-fns'`)

---

## 🎁 Bonus: Wow-factor Features

ถ้าเวลาเหลือ ทำพวกนี้ให้กรรมการตื่นเต้น:

1. **Skeleton screens** ใช้ shadcn `Skeleton` ทุกหน้า
2. **Page transitions** ด้วย Framer Motion
3. **Optimistic UI** สำหรับ marketplace purchase
4. **Dark mode** toggle
5. **i18n** Thai/English switcher
6. **PWA** (offline support)
7. **Real-time progress** UI ด้วย WebSocket
8. **Tooltips สวย ๆ** ด้วย Radix
9. **Charts** สวยด้วย Recharts หรือ visx
10. **Animation** เมื่อ tree counter เพิ่ม

---

## 🆘 Stuck? Resources

1. ดู `docs/DEVELOPMENT.md` สำหรับ setup issues
2. Search GitHub Issues
3. ถาม User ใน Line/Discord
4. Stack Overflow / Discord communities

**Happy hacking, Person A! 🚀**
