# Plain-language copy rewrite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the TreeQ Carbon site so a reader who is not on the team can say what each section is for, without weakening a single truth claim.

**Architecture:** Copy-only. Section headings become the question a reader actually has, jargon moves under a native `<details>` closed by default, and one new CSS class keeps Thai out of a font that has no Thai glyphs. No new routes, no logic, no layout rework — five days before the competition, structure is the expensive thing to change and copy is not.

**Tech Stack:** Next.js 14 App Router, TypeScript, Tailwind, vitest (node environment, `renderToStaticMarkup` — no jsdom), Playwright.

**Spec:** `docs/superpowers/specs/2026-07-31-plain-language-copy-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `apps/web/src/app/globals.css` | Add `.editorial-eyebrow-th`. The existing `.editorial-eyebrow` stays for Latin labels. |
| `apps/web/src/components/editorial/technical-detail.tsx` | **New.** One disclosure component, no state, wraps native `<details>`. |
| `apps/web/src/components/editorial/technical-detail.test.tsx` | **New.** Closed by default, renders its label and children. |
| `apps/web/src/app/page.tsx` | Landing: hero, CTAs, four section headings, four journey steps, evidence section. |
| `apps/web/src/app/page.test.tsx` | Existing assertions on the old headings must move to the new ones; add the font-trap guard. |
| `apps/web/src/components/demo/judge-demo-header.tsx` | `/demo` heading + eyebrow. Fixes the overclaim the supervisor caught. |
| `apps/web/src/components/demo/demo-shell.tsx` | The manifest/hash sentence the supervisor quoted. |
| `apps/web/e2e/judge-journey.spec.ts` | Upload-journey test now that `/dashboard/viewer` is public. |

---

### Task 1: A Thai-safe eyebrow class

`.editorial-eyebrow` is `font-mono`. JetBrains Mono carries no Thai glyphs, so Thai under it falls
through to a substitute face at 11px. This project already shipped that bug in
`evidence-metric.tsx` and had it reported as unreadable. Every eyebrow is about to become Thai, so
the class comes first.

**Files:**
- Modify: `apps/web/src/app/globals.css:118-120`
- Test: `apps/web/src/app/page.test.tsx`

- [ ] **Step 1: Write the failing test**

Add to `apps/web/src/app/page.test.tsx`, inside the existing top-level `describe`:

```tsx
  // JetBrains Mono has no Thai glyphs. Thai set in it silently falls back to
  // another face at 11px, which is how this project shipped an unreadable
  // label once already. This scans the rendered markup rather than the source,
  // because the source is where the mistake looks correct.
  it('never sets Thai text in the monospace face', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    // Direct text inside an element carrying font-mono. Eyebrows and badges are
    // all plain <p>/<span> with no nested markup, which is exactly this shape.
    const monoWithText = /<(?:p|span|dt|dd)[^>]*class="[^"]*font-mono[^"]*"[^>]*>([^<]+)</g;
    const THAI = /[฀-๿]/;
    const offenders: string[] = [];
    for (const match of markup.matchAll(monoWithText)) {
      if (THAI.test(match[1])) offenders.push(match[1].trim());
    }

    expect(offenders).toEqual([]);
  });
```

- [ ] **Step 2: Run it and watch it pass for now**

```bash
cd apps/web && npx vitest run src/app/page.test.tsx -t "monospace"
```

Expected: PASS. Every eyebrow is still English at this point. The test earns its keep in Task 4
and Task 5, where it fails the moment Thai lands in a mono class. Confirm it can fail before
trusting it:

- [ ] **Step 3: Prove the test can fail**

Temporarily change `apps/web/src/app/page.tsx:61` from
`<p className="editorial-eyebrow">TreeQ Carbon / NSC 2026 / Deep Tech</p>` to
`<p className="font-mono">ทดสอบ</p>`, run the command from Step 2, and confirm it FAILS with
`ทดสอบ` listed. Then revert that edit.

- [ ] **Step 4: Add the Thai eyebrow class**

In `apps/web/src/app/globals.css`, directly after the existing `.editorial-eyebrow` block:

```css
  /* Thai companion to .editorial-eyebrow. Same job, three differences that
     matter: a sans face because JetBrains Mono has no Thai glyphs, no
     uppercase because Thai has no case, and far less tracking because letter
     spacing pushes vowels and tone marks away from the consonant they belong
     to.

     No colour here on purpose. These labels sit on ivory, on paper and on
     deep forest, so the caller sets it. Baking one in would mean every dark
     surface fighting the class with an override that may or may not win. */
  .editorial-eyebrow-th {
    @apply text-xs font-semibold tracking-[0.04em];
  }
```

- [ ] **Step 5: Run the full unit suite**

```bash
cd apps/web && npx vitest run
```

Expected: PASS, count one higher than before.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/app/globals.css apps/web/src/app/page.test.tsx
git commit -m "style(web): give Thai eyebrows a face that has Thai glyphs"
```

---

### Task 2: The TechnicalDetail disclosure

**Files:**
- Create: `apps/web/src/components/editorial/technical-detail.tsx`
- Test: `apps/web/src/components/editorial/technical-detail.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/editorial/technical-detail.test.tsx`:

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { TechnicalDetail } from './technical-detail';

describe('TechnicalDetail', () => {
  // Closed is the whole point. A reader who does not want the jargon should
  // never meet it, and a disclosure that ships open is just a paragraph.
  it('is closed until someone opens it', () => {
    const markup = renderToStaticMarkup(<TechnicalDetail>tlsep</TechnicalDetail>);

    expect(markup).toContain('<details');
    expect(markup).not.toContain('open');
  });

  it('carries one label across the whole site', () => {
    const markup = renderToStaticMarkup(<TechnicalDetail>tlsep</TechnicalDetail>);

    expect(markup).toContain('<summary');
    expect(markup).toContain('รายละเอียดทางเทคนิค');
  });

  it('renders what it was given', () => {
    const markup = renderToStaticMarkup(
      <TechnicalDetail>Wood IoU 0.418</TechnicalDetail>,
    );

    expect(markup).toContain('Wood IoU 0.418');
  });
});
```

- [ ] **Step 2: Run it and watch it fail**

```bash
cd apps/web && npx vitest run src/components/editorial/technical-detail.test.tsx
```

Expected: FAIL — `Failed to resolve import "./technical-detail"`.

- [ ] **Step 3: Write the component**

Create `apps/web/src/components/editorial/technical-detail.tsx`:

```tsx
import type { ReactNode } from 'react';

/**
 * The technical reading of the section above it.
 *
 * Native <details> rather than a hand-built accordion: it gives a control that
 * responds to Enter and Space, announces its own open state to a screen
 * reader, and works before any JavaScript has loaded. Building the same thing
 * by hand means owning aria-expanded and focus for no gain.
 *
 * One label for the whole site, so a reader learns once where the jargon
 * lives instead of decoding a different phrase in every section.
 */
export function TechnicalDetail({ children }: { children: ReactNode }) {
  return (
    <details className="mt-4 rounded-xl border border-hairline bg-paper px-4 py-3">
      <summary className="cursor-pointer text-sm font-medium text-canopy marker:text-evidence-amber">
        รายละเอียดทางเทคนิค
      </summary>
      <div className="mt-3 text-sm leading-7 text-canopy">{children}</div>
    </details>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd apps/web && npx vitest run src/components/editorial/technical-detail.test.tsx
```

Expected: PASS, 3 tests.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/editorial/technical-detail.tsx apps/web/src/components/editorial/technical-detail.test.tsx
git commit -m "feat(web): add the technical-detail disclosure"
```

---

### Task 3: Hero copy, and a CTA that is no longer true

The hero sub-line stacks five borrowed terms. Separately, the second CTA reads
"เข้าสู่ระบบเพื่ออัปโหลดไฟล์" and points at `/login` — which stopped being true when
`/dashboard/viewer` was opened to visitors. A page arguing that it reports its own limits cannot
also tell people to sign in for something that no longer needs signing in.

**Files:**
- Modify: `apps/web/src/app/page.tsx:75-95`, `:153`, `:143-147`
- Test: `apps/web/src/app/page.test.tsx:23-24`

- [ ] **Step 1: Update the failing test first**

In `apps/web/src/app/page.test.tsx`, replace lines 23-24:

```tsx
    expect(getAnchorHrefByLabel(markup, 'ดูหลักฐานที่ตรวจแฮชแล้ว')).toBe('/demo');
    expect(getAnchorHrefByLabel(markup, 'ลองอัปโหลดไฟล์ของคุณ')).toBe('/dashboard/viewer');
```

- [ ] **Step 2: Run it and watch it fail**

```bash
cd apps/web && npx vitest run src/app/page.test.tsx
```

Expected: FAIL — no anchor labelled `ลองอัปโหลดไฟล์ของคุณ`.

- [ ] **Step 3: Rewrite the hero sub-line**

In `apps/web/src/app/page.tsx`, replace the `<p>` at lines 75-78 with:

```tsx
              <p className="mt-7 max-w-xl text-base leading-8 text-canopy sm:text-lg">
                ใส่ภาพสามมิติของต้นไม้เข้าไป ระบบจะวัดขนาดลำต้นกับความสูง
                แล้วคำนวณว่าต้นไม้ต้นนั้นเก็บคาร์บอนไว้เท่าไร พร้อมบอกที่มาของตัวเลขทุกตัว
              </p>
```

- [ ] **Step 4: Point the upload CTA where uploading now works**

Replace the second `<Button>` at lines 88-94 with:

```tsx
                <Button
                  render={<Link href="/dashboard/viewer" />}
                  variant="editorialOutline"
                  size="xl"
                >
                  ลองอัปโหลดไฟล์ของคุณ
                </Button>
```

Delete the stale comment above the CTA block at lines 79-83 — it describes a redirect that no
longer exists — and replace it with:

```tsx
              {/* The viewer is open to visitors, so this goes straight there.
                  It used to route through /login, which was true until the
                  sign-in requirement was lifted and then quietly was not. */}
```

- [ ] **Step 5: Replace the two developer notes rendered to visitors**

Line 153, an instruction to whoever wrote the code:

```tsx
            <p className="editorial-eyebrow-th px-1 pb-3 text-canopy">ตัวเลขที่วัดได้จริง — ไม่ปัดเศษ</p>
```

Lines 143-148, a decorative caption that says nothing. Delete the whole `<div>` holding
`Field observation / 01` and `จากโครงสร้าง 3D สู่คาร์บอน`, leaving the image and its gradient.

- [ ] **Step 6: Run the unit suite**

```bash
cd apps/web && npx vitest run
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/app/page.tsx apps/web/src/app/page.test.tsx
git commit -m "fix(web): say what the platform does, and send the upload CTA where uploading works"
```

---

### Task 4: The four steps of "วัดยังไง"

Step 02 currently reads `tlsep เป็น default baseline; PointNet++ ยังเป็น Experimental`, which
tells a reader nothing about what the step does. The honest fact underneath — that the shipped
separator is geometric and not AI — is hidden behind a word nobody knows.

**Files:**
- Modify: `apps/web/src/app/page.tsx:14-37` (the `JOURNEY` constant), `:200-211` (the list)

- [ ] **Step 1: Replace the JOURNEY constant**

```tsx
const JOURNEY = [
  {
    step: '01',
    title: 'รับภาพสามมิติของต้นไม้',
    description:
      'ไฟล์จากเครื่องสแกนเลเซอร์ หรือจากการถ่ายต้นไม้หลายมุมแล้วประกอบเป็นทรงสามมิติ ระบบแสดงเป็นกลุ่มจุดที่หมุนดูได้',
    technical: 'point cloud รูปแบบ .ply · จำกัด 2 ล้านจุด หรือ 100 MB ต่อไฟล์',
  },
  {
    step: '02',
    title: 'แยกลำต้นออกจากใบ',
    description:
      'ต้องรู้ก่อนว่าจุดไหนคือเนื้อไม้ จุดไหนคือใบ เพราะคาร์บอนเก็บอยู่ในเนื้อไม้เป็นหลัก ตอนนี้ใช้วิธีคำนวณจากรูปทรง ยังไม่ได้ใช้ AI',
    technical: `${baseline.backend} เป็นตัวที่ใช้จริง · ${candidate.displayName} ยังเป็น ${candidate.status} ไม่ได้ถูกนำมาใช้ · Wood IoU ${wanHeldOut.woodIoU}`,
  },
  {
    step: '03',
    title: 'วัดขนาดต้นไม้',
    description:
      'วัดเส้นผ่านศูนย์กลางลำต้นที่ระดับอก ความสูงทั้งต้น และปริมาตรเนื้อไม้ จากรูปทรงที่แยกได้',
    technical: `DBH ที่ระดับ 1.3 เมตร · ปริมาตรจาก QSM ทรงกระบอก · คลาดเคลื่อนเฉลี่ย ${demol65.dbhMaeCm} ซม. บนต้นไม้จริง 65 ต้น`,
  },
  {
    step: '04',
    title: 'คำนวณคาร์บอน',
    description:
      'เอาขนาดที่วัดได้เข้าสมการมาตรฐาน ได้เป็นน้ำหนักชีวมวล คาร์บอน และ CO₂ พร้อมบันทึกว่าใช้สมการไหน',
    technical:
      'สมการ Chave 2014 · ชีวมวลใต้ดิน = เหนือดิน × 0.24 · คาร์บอน = ชีวมวล × 0.47 · CO₂e = คาร์บอน × 44/12 (IPCC 2006) · การแยกชนิดพันธุ์ยังเป็นโครงเปล่า',
  },
] as const;
```

- [ ] **Step 2: Render the technical line inside the disclosure**

Replace the `<li>` body at lines 202-209 with:

```tsx
                <li
                  key={item.step}
                  className="grid gap-3 border-b border-hairline py-6 last:border-b-0 sm:grid-cols-[5rem_minmax(0,0.7fr)_minmax(0,1.3fr)] sm:items-baseline"
                >
                  <span className="font-mono text-xs text-evidence-amber">{item.step}</span>
                  <h3 className="font-display text-2xl text-forest-ink">{item.title}</h3>
                  <div className="max-w-2xl">
                    <p className="text-base leading-7 text-canopy">{item.description}</p>
                    <TechnicalDetail>{item.technical}</TechnicalDetail>
                  </div>
                </li>
```

- [ ] **Step 3: Add the import**

At the top of `apps/web/src/app/page.tsx`, after the `EditorialSection` import:

```tsx
import { TechnicalDetail } from '../components/editorial/technical-detail';
```

- [ ] **Step 4: Run the unit suite**

```bash
cd apps/web && npx vitest run
```

Expected: PASS. `page.test.tsx` still finds `tlsep`, `PointNet++`, `Experimental` and `Stub` in the
markup — `<details>` renders its children on the server, so moving jargon into it does not remove
it from the page, only from the reader's first pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/app/page.tsx
git commit -m "feat(web): describe each measurement step in words a visitor knows"
```

---

### Task 5: Section headings become the reader's questions

**Files:**
- Modify: `apps/web/src/app/page.tsx:174-316`
- Test: `apps/web/src/app/page.test.tsx:72-76`

- [ ] **Step 1: Update the heading assertions first**

Replace `apps/web/src/app/page.test.tsx` lines 73-76 with:

```tsx
    expect(markup).toContain('ทำไมต้องวัดใหม่');
    expect(markup).toContain('วัดยังไง');
    expect(markup).toContain('ขอดูของจริง');
    expect(markup).toContain('เชื่อได้แค่ไหน');
```

- [ ] **Step 2: Run it and watch it fail**

```bash
cd apps/web && npx vitest run src/app/page.test.tsx
```

Expected: FAIL on all four.

- [ ] **Step 3: Rewrite the four sections**

`EditorialSection` renders `eyebrow` through the `.editorial-eyebrow` class inside the component,
so pass Thai eyebrows only after switching that class. Since the component is shared, keep the
eyebrows numeric and Latin-free by dropping them entirely — the heading now carries the meaning.

Section 01, lines 175-179 — replace the `eyebrow`, `title` and `description` props:

```tsx
            eyebrow="01"
            title="ทำไมต้องวัดใหม่"
            description="การวัดคาร์บอนต้นไม้ทุกวันนี้ต้องส่งคนเข้าไปวัดทีละต้น ใช้เวลา และพอได้ตัวเลขมาแล้วก็ตรวจย้อนไม่ได้ว่ามาจากต้นไหน วัดด้วยวิธีอะไร"
```

Line 183, one word inside the pull quote — a visitor is not a judge:

```tsx
                เราไม่ได้เริ่มจากคำว่า “AI แม่นยำ” แต่เริ่มจากหลักฐานที่ใครก็เปิดดู แล้วถามต่อได้
```

Section 02, lines 195-198:

```tsx
            eyebrow="02"
            title="วัดยังไง"
            description="จากกลุ่มจุดสามมิติ กลายเป็นตัวเลขคาร์บอนได้ด้วยสี่ขั้น แต่ละขั้นบอกได้ว่าทำอะไรและใช้อะไรคำนวณ"
```

Section 03, lines 217-220:

```tsx
            eyebrow="03"
            title="ขอดูของจริง"
            description="หมุนดูต้นไม้ได้เอง จุดสีน้ำตาลคือส่วนที่ระบบตัดสินว่าเป็นเนื้อไม้ สีเขียวคือใบ ถ้าไม่เห็นด้วยกับที่ระบบแบ่ง จะเห็นตั้งแต่ตรงนี้ ก่อนไปดูตัวเลข"
```

Section 04, lines 274-277:

```tsx
            eyebrow="04"
            title="เชื่อได้แค่ไหน"
            description="เราทดสอบไปสามชุด แต่ละชุดบอกได้แค่บางเรื่อง และมีขั้นที่ยังไม่ได้ทดสอบเลย"
```

- [ ] **Step 4: Replace the closing paragraph of section 04**

Lines 306-310 currently run four claims together. Split tested from untested, because that
distinction is the answer to the question the supervisor asked. Replace that `<p>` with:

```tsx
              <div className="max-w-3xl space-y-4 text-base leading-7 text-canopy">
                <div>
                  <p className="font-semibold text-forest-ink">ทดสอบแล้ว</p>
                  <p className="mt-1">
                    การแยกลำต้นกับใบ — แต่ใช้ชุดข้อมูลเดียวกันนี้ตอนเลือกรอบเทรนที่ดีที่สุด
                    ค่าที่ได้จึงเข้าข้างตัวเอง · การวัดขนาดต้นไม้จริง 65 ต้น — วัดขนาดอย่างเดียว
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-ember">ยังไม่ได้ทดสอบ</p>
                  <p className="mt-1">
                    ระบบทั้งเส้นตั้งแต่รับไฟล์จนได้ค่าคาร์บอน · สมการชีวมวลกับข้อมูลต้นไม้จริงในไทย ·
                    การแยกชนิดพันธุ์ที่ยังเป็นโครงเปล่า
                  </p>
                </div>
                <p>
                  ค่าคาร์บอนและ CO₂e ที่แสดงเป็นค่าประมาณ ไม่ใช่เครดิตคาร์บอนที่ผ่านการรับรอง
                  และเราไม่ได้กล่าวอ้างเรื่องตลาดซื้อขายเครดิต
                </p>
              </div>
```

- [ ] **Step 5: Delete the layout rationale in section 02's description**

Confirm the string `แทนการแยก feature` no longer appears anywhere:

```bash
cd apps/web && grep -rn "narrative\|แทนการแยก feature\|do not round\|Field observation" src/ || echo "clean"
```

Expected: `clean`.

- [ ] **Step 6: Run the unit suite**

```bash
cd apps/web && npx vitest run
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/app/page.tsx apps/web/src/app/page.test.tsx
git commit -m "feat(web): name each section after the question it answers"
```

---

### Task 6: The two sentences the supervisor quoted

**Files:**
- Modify: `apps/web/src/components/demo/judge-demo-header.tsx:39-41`, `:50-54`
- Modify: `apps/web/src/components/demo/demo-shell.tsx:359-365`

- [ ] **Step 1: Fix the overclaim in the demo heading**

`judge-demo-header.tsx` lines 50-54 currently promise limits at every step. There are limits for
three validation sets and several stages with none, so the sentence is false. Replace the `else`
branch:

```tsx
                <>
                  ชุดหลักฐานที่ล็อกไว้
                  <br />
                  ตรวจไฟล์ก่อนแสดงทุกครั้ง
                </>
```

- [ ] **Step 2: Replace the eyebrow above it**

Lines 39-41:

```tsx
            <p className="editorial-eyebrow-th text-lichen">โหมดสาธิต · ใช้ไฟล์ชุดที่ล็อกไว้</p>
```

- [ ] **Step 3: Rewrite the manifest sentence**

`demo-shell.tsx` lines 359-365. The claim is true — `frozen-demo.ts` calls
`crypto.subtle.digest('SHA-256', …)` and throws when the value differs — so this says the same
thing in words a reader can check:

```tsx
            <p className="editorial-eyebrow-th text-moss">แนะนำ · ไม่ต้องพึ่งเครือข่าย</p>
            <h3 className="mt-3 font-display text-xl">ชุดตัวอย่างที่ตรวจแล้ว</h3>
            <p className="mt-2 text-sm leading-6 text-canopy">
              ไฟล์ตัวอย่างและผลลัพธ์ในหน้านี้ เป็นชุดเดียวกับตอนที่เราทดสอบไว้
              เบราว์เซอร์จะคำนวณลายนิ้วมือไฟล์เทียบกับที่บันทึกไว้ก่อนทุกครั้ง ถ้าไม่ตรง
              หน้านี้จะไม่แสดงตัวเลขเลย
            </p>
```

- [ ] **Step 4: Run the unit suite**

```bash
cd apps/web && npx vitest run
```

Expected: PASS. `demo-shell.test.tsx` asserts mode semantics, not this copy.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/demo/judge-demo-header.tsx apps/web/src/components/demo/demo-shell.tsx
git commit -m "fix(web): stop claiming the demo states its limits at every step"
```

---

### Task 7: The browser journey, and the upload claim it checks

`e2e/judge-journey.spec.ts:143-156` follows the upload CTA and asserts it lands on `/login`. That
was correct until `/dashboard/viewer` was opened to visitors. The test should now assert the
stronger thing it was always trying to check: the journey reaches a page that can actually take a
file.

**Files:**
- Modify: `apps/web/e2e/judge-journey.spec.ts:143-156`

- [ ] **Step 1: Rewrite the upload-journey test**

```tsx
  test('following the upload action reaches a page that can take a file', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page
      .getByRole('link', { name: /อัปโหลด/ })
      .first()
      .click();
    await page.waitForLoadState('networkidle');

    // The viewer is open to visitors now, so the journey ends at the workspace
    // rather than at a sign-in form. What matters is unchanged: the action that
    // says upload arrives somewhere that accepts a file.
    await expect(page).toHaveURL(/\/dashboard\/viewer/);
    await expect(page.locator('input[type="file"]')).toHaveCount(1);
  });
```

- [ ] **Step 2: Build and run the browser journey**

```bash
cd apps/web && npm run build && npx playwright test
```

Expected: 42 passed across both viewports. If a test fails on changed copy, fix the test to match
the new wording — never by loosening what it checks.

- [ ] **Step 3: Commit**

```bash
git add apps/web/e2e/judge-journey.spec.ts
git commit -m "test(web): the upload journey ends at the workspace, not at sign-in"
```

---

### Task 8: Verify nothing true went missing

Rewriting copy is the easiest way to delete a claim by accident. This task exists to catch that.

**Files:** none modified unless a check fails.

- [ ] **Step 1: Run every gate**

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File run-gates.ps1
```

Expected: `All gates passed.` — tests, type-check, lint, build, journey, and the forbidden-claim
scan.

- [ ] **Step 2: Check the five non-negotiables by hand**

Serve the build and read the page. Every one of these must still be on screen:

1. carbon and CO₂e are estimates, **not certified credits**
2. PointNet++ is experimental and **not in use**
3. species classification is **a stub**
4. frozen mode still prints **NOT A LIVE RUN**
5. Wood IoU `0.418`, Leaf IoU `0.808`, DBH MAE `1.1673846154` shown **unrounded**

```bash
cd apps/web && grep -c "0.418\|0.808\|1.1673846154" src/app/page.tsx
```

Expected: at least 1 — the metrics come from `CORE_DEMO_EVIDENCE`, so confirm the card at
`page.tsx:154-170` still renders all three.

- [ ] **Step 3: The reader test the spec asks for**

Ask someone who has not read the code to open the landing page and say, in their own words, what
each of the four sections is for. If they cannot, the rewrite has not worked yet and the wording
needs another pass — this is the acceptance criterion, not the test suite.

- [ ] **Step 4: Open the PR**

```bash
git push -u origin HEAD
gh pr create --base main --title "feat(web): rewrite the site in plain Thai" --body "See docs/superpowers/specs/2026-07-31-plain-language-copy-design.md"
```

---

## Order and fallback

Tasks 1-5 are the landing page and matter most: that is the URL the supervisor opened. Task 6 is
`/demo`, Task 7 is the test that a merged change made stale, Task 8 is the safety net.

If Monday arrives with the work unfinished, stop after Task 5 and ship. The landing page is what
was reviewed; `/demo` can follow.
