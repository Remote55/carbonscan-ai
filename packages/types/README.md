# 📦 Shared Types

> **Purpose:** TypeScript types แชร์ระหว่าง Web และ packages
>
> **Source of truth:** OpenAPI spec จาก services/api (FastAPI auto-gen)

---

## How It Works

```
services/api (Python)
    │
    ▼ (FastAPI auto-generates)
http://localhost:8000/openapi.json
    │
    ▼ (run: pnpm --filter types generate)
packages/types/src/api.ts (TypeScript)
    │
    ▼ (import)
apps/web (Person A uses)
```

---

## Generate Types

```bash
# Start API first
pnpm api:dev

# In another terminal
pnpm --filter types generate
# → updates packages/types/src/api.ts
```

หรือใส่ใน `package.json`:
```json
{
  "scripts": {
    "generate": "openapi-typescript http://localhost:8000/openapi.json -o src/api.ts"
  }
}
```

---

## Usage in Web

```tsx
// apps/web/src/hooks/useTrees.ts
import type { components } from '@carbonscan/types';

type Tree = components['schemas']['TreeOut'];

export function useTrees() {
  const { data } = useQuery<Tree[]>(...);
}
```

---

## Custom Types (not from API)

```ts
// packages/types/src/index.ts
export * from './api';
export * from './custom';   // domain types not in API

// packages/types/src/custom.ts
export type ViewerSettings = {
  cameraPosition: [number, number, number];
  showWoodOnly: boolean;
  pointSize: number;
};
```
