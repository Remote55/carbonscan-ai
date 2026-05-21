# 🧩 Shared UI Components

> **Owner:** Person A (primary), Person B (review)
> **Purpose:** Reusable React components ที่ใช้ทั้งใน Web

---

## Why Shared Package?

ตอนนี้ apps/web เป็น app เดียวที่ใช้ — แต่หากในอนาคต:
- เพิ่ม Admin Dashboard (separate app)
- ทำ Storybook
- Open-source component library

จะ refactor ยาก ถ้าไม่แยกตั้งแต่ต้น

---

## Folder Structure

```
packages/ui/
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts                Re-exports
│   ├── components/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── index.ts
│   │   ├── Card/
│   │   ├── Dialog/
│   │   └── ...
│   ├── hooks/
│   │   ├── useMediaQuery.ts
│   │   └── ...
│   └── lib/
│       └── utils.ts            cn() helper
└── tests/
```

---

## Note for NSC Phase

ใน Phase แรก แนะนำ:
- ใช้ **shadcn/ui** ใน `apps/web/src/components/ui/` ตรง ๆ
- ย้ายมาใช้ shared package เมื่อมี 2nd consumer (e.g., admin dashboard)

ดังนั้น `packages/ui/` ยังไม่ active ตอนนี้ — แค่ scaffold ไว้
