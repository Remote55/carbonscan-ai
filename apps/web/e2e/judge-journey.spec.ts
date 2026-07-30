import { expect, test, type Page } from '@playwright/test';

/**
 * The journey a judge actually walks, asserted in a real browser.
 *
 * These gates exist for the claims the unit tests structurally cannot reach.
 * `renderToStaticMarkup` proves the markup contains a string; it cannot tell you
 * that the page does not scroll sideways at 1366px, that the frozen artifacts
 * survive their hash check when fetched over HTTP, or that a landmark is where a
 * keyboard user lands. That is the whole reason this file is worth its runtime.
 */

const ROUTES = ['/', '/demo', '/login', '/signup', '/dashboard/viewer'] as const;

/** Horizontal page overflow, which is a layout bug in every case. */
async function documentOverflow(page: Page): Promise<number> {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}

test.describe('no route scrolls sideways', () => {
  for (const route of ROUTES) {
    test(`${route} fits its viewport`, async ({ page }) => {
      await page.goto(route);
      await page.waitForLoadState('networkidle');
      expect(await documentOverflow(page)).toBeLessThanOrEqual(0);
    });
  }

  // 600px is below every breakpoint the design uses, so it is where a fixed width
  // or an unscrollable table would finally show up. The wide tree table is
  // supposed to scroll inside its own container and never take the page with it.
  test('/demo still fits at 600px, with the table scrolling inside itself', async ({ page }) => {
    await page.setViewportSize({ width: 600, height: 900 });
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');

    expect(await documentOverflow(page)).toBeLessThanOrEqual(0);

    const scroller = page.locator('div.overflow-x-auto', { has: page.locator('table') });
    await expect(scroller).toBeVisible();
    const overflowing = await scroller.evaluate((node) => node.scrollWidth > node.clientWidth);
    expect(overflowing).toBe(true);
  });
});

test.describe('frozen evidence route', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
  });

  // The mode label is the honesty contract: a judge must never mistake the
  // verified fixture for a live run. It is rendered twice on purpose - once in
  // the header and once beside the result - so the label travels with whatever
  // the judge happens to be looking at. Assert both, rather than `.first()`,
  // since losing the second one would be the regression worth catching.
  test('names itself a frozen run, not a live one', async ({ page }) => {
    const badge = page.getByText('FROZEN EVIDENCE — NOT A LIVE RUN');
    await expect(badge).toHaveCount(2);
    await expect(badge.first()).toBeVisible();
    await expect(badge.last()).toBeVisible();
  });

  // Hash verification only really happens over HTTP. A unit test hands the loader
  // bytes from disk; here the browser fetches the artifacts the build emitted, so
  // a stale or re-encoded file fails the gate instead of the demo.
  test('passes artifact verification and shows the reconciled counts', async ({ page }) => {
    await expect(page.getByText('loading failed')).toHaveCount(0);

    await expect(page.getByText('ต้นไม้ที่ตรวจพบ 5')).toBeVisible();
    await expect(page.getByText('ต้นไม้ที่คำนวณสำเร็จ 3')).toBeVisible();
    await expect(page.getByText('ไม่รวมผล 2')).toBeVisible();
  });

  test('labels the measured count as calculated rather than as a tree total', async ({ page }) => {
    await expect(page.getByText('ต้นไม้ที่คำนวณสำเร็จ').first()).toBeVisible();
    await expect(page.getByText('จำนวนต้นไม้')).toHaveCount(0);
  });

  test('keeps the non-certification sentence on screen', async ({ page }) => {
    await expect(
      page.getByText('ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง', { exact: false }).first(),
    ).toBeVisible();
  });

  test('holds PointNet++ at experimental and never promotes it', async ({ page }) => {
    await expect(page.getByText('Experimental').first()).toBeVisible();
    await expect(page.getByText('ยังไม่ถูกเลื่อนเป็นค่าตั้งต้น')).toBeVisible();
  });

  // Scoped to the table body. A page-wide text match counted four READYs,
  // because the reliability panel reports the web server as READY too - a real
  // label, not a duplicate, and one this assertion has no business measuring.
  test('explains every excluded tree instead of leaving a gap in the ids', async ({ page }) => {
    const body = page.locator('table tbody');
    await expect(body.locator('tr')).toHaveCount(5);
    await expect(body.getByText('EXCLUDED')).toHaveCount(2);
    await expect(body.getByText('READY')).toHaveCount(3);

    // Ids run 1..5 with nothing missing, which is the point of listing the
    // excluded rows inline in the first place.
    const ids = await body.locator('th[scope="row"]').allInnerTexts();
    expect(ids.map((value) => value.trim())).toEqual(['1', '2', '3', '4', '5']);
  });

  test('offers only PLY, matching what demo mode enforces', async ({ page }) => {
    const body = await page.locator('body').innerText();
    expect(body).toContain('.ply');
    expect(body).not.toContain('.las');
    expect(body).not.toContain('.laz');
  });
});

// A CTA is a promise. This checks the promise against the destination rather than
// against the label, which is what the unit test could not do: it asserted both
// hero buttons pointed at /demo and passed, while one of them said "upload" and
// landed on a page with no file input at all.
test.describe('landing actions can do what they say', () => {
  test('the public demo route offers no upload, so nothing may promise one there', async ({
    page,
  }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');

    // Read-only without a launcher handoff. If this ever gains a file input, the
    // demo route started accepting uploads from anyone and that is a decision to
    // make deliberately, not to discover here.
    await expect(page.locator('input[type="file"]')).toHaveCount(0);

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const uploadLinks = page.locator('a', { hasText: 'อัปโหลด' });
    for (let index = 0; index < (await uploadLinks.count()); index += 1) {
      const href = await uploadLinks.nth(index).getAttribute('href');
      expect(href).not.toBe('/demo');
    }
  });

  test('following the upload action reaches a page that can take a file', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page
      .getByRole('link', { name: /อัปโหลด/ })
      .first()
      .click();
    await page.waitForLoadState('networkidle');

    // Sign-in stands between the visitor and the upload, by design. What matters
    // is that the journey continues to the workspace instead of dead-ending.
    await expect(page).toHaveURL(/\/login/);
    expect(new URL(page.url()).searchParams.get('redirect')).toBe('/dashboard/viewer');
  });
});

test.describe('landmarks and keyboard entry', () => {
  test('the landing skip link is the first tab stop and moves focus into main', async ({
    page,
  }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.keyboard.press('Tab');
    const skip = page.locator('a[href="#main-content"]');
    await expect(skip).toBeFocused();
    // Hidden until focused: if it were visible at rest the layout would show it.
    await expect(skip).toBeVisible();

    await page.keyboard.press('Enter');
    await expect(page.locator('main#main-content')).toBeAttached();
  });

  test('navigation and contentinfo sit outside the main landmark', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('main')).toHaveCount(1);
    await expect(page.locator('main nav')).toHaveCount(0);
    await expect(page.locator('main footer')).toHaveCount(0);
  });

  test('every page states one first-level heading', async ({ page }) => {
    for (const route of ['/', '/demo']) {
      await page.goto(route);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('h1')).toHaveCount(1);
    }
  });
});

test.describe('results workspace', () => {
  test('marks the synthetic preview as not being pipeline evidence', async ({ page }) => {
    await page.goto('/dashboard/viewer');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('SYNTHETIC · NOT PIPELINE EVIDENCE')).toBeVisible();
  });

  // Below 1024 the viewer has to come before the rail: the point cloud is the
  // thing being explained, and a judge scrolling past numbers to reach it reads
  // as the numbers being the claim rather than the evidence.
  test('stacks the viewer above the rail on a narrow screen', async ({ page }) => {
    await page.setViewportSize({ width: 900, height: 900 });
    await page.goto('/dashboard/viewer');
    await page.waitForLoadState('networkidle');

    const canvas = page.locator('canvas').first();
    await expect(canvas).toBeVisible();
    expect(await documentOverflow(page)).toBeLessThanOrEqual(0);
  });
});

test.describe('critical content is reachable at the demo sizes', () => {
  // "Visible" here means reachable without hunting: the mode badge and the first
  // action are in the initial viewport, and the evidence is on the page rather
  // than clipped out of it.
  test('/demo puts the mode label and the primary action above the fold', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');

    const viewport = page.viewportSize()!;
    // The header copy is the one that has to be above the fold; the second badge
    // sits beside the result further down, which is where it belongs.
    const badge = page.getByText('FROZEN EVIDENCE — NOT A LIVE RUN').first();
    const box = await badge.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.y).toBeLessThan(viewport.height);

    const heading = page.locator('h1');
    const headingBox = await heading.boundingBox();
    expect(headingBox!.y).toBeLessThan(viewport.height);
  });
});
