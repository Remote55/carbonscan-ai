import { afterEach, describe, expect, it } from 'vitest';

import { GET } from './route';

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const DEMO_TOKEN = process.env.NEXT_PUBLIC_DEMO_TOKEN;

afterEach(() => {
  process.env.NEXT_PUBLIC_API_URL = API_URL;
  process.env.NEXT_PUBLIC_DEMO_TOKEN = DEMO_TOKEN;
});

describe('GET /api/runtime-config', () => {
  it('reports the endpoint this deployment was built against', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'https://green-tree.trycloudflare.com';
    process.env.NEXT_PUBLIC_DEMO_TOKEN = 'a'.repeat(64);

    const body = await GET().json();

    expect(body).toEqual({ apiUrl: 'https://green-tree.trycloudflare.com', hasToken: true });
  });

  it('never returns the token itself, only whether one is set', async () => {
    // The launcher needs to tell a finished publish from a half-finished one.
    // That question is answerable with a boolean, and a boolean cannot be
    // replayed against the API by whoever reads this route.
    const token = 'b'.repeat(64);
    process.env.NEXT_PUBLIC_DEMO_TOKEN = token;

    const raw = await GET().text();

    expect(raw).not.toContain(token);
    expect(JSON.parse(raw).hasToken).toBe(true);
  });

  it('says so plainly when nothing has been published yet', async () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    delete process.env.NEXT_PUBLIC_DEMO_TOKEN;

    expect(await GET().json()).toEqual({ apiUrl: null, hasToken: false });
  });

  it('forbids caching, or the launcher would verify a stale answer', async () => {
    expect(GET().headers.get('cache-control')).toBe('no-store');
  });
});
