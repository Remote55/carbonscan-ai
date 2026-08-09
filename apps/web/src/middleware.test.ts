import { NextRequest } from 'next/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { isProtectedDashboardRoute, isPublicDashboardRoute, middleware } from './middleware';

/**
 * The middleware had no tests at all, and its one interesting branch — what to
 * do when the Supabase env is missing — served every /dashboard/* route
 * unauthenticated to everyone. In production that is not a degraded mode, it is
 * the absence of the thing the file exists for.
 */

const ORIGINAL_ENV = { ...process.env };

function request(pathname: string): NextRequest {
  return new NextRequest(new URL(pathname, 'https://treeq.example'));
}

beforeEach(() => {
  vi.resetModules();
});

afterEach(() => {
  process.env = { ...ORIGINAL_ENV };
});

function clearSupabaseEnv() {
  delete process.env.NEXT_PUBLIC_SUPABASE_URL;
  delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
}

function setNodeEnv(value: string) {
  Object.defineProperty(process.env, 'NODE_ENV', {
    value,
    configurable: true,
    writable: true,
  });
}

describe('route classification', () => {
  it('treats the viewer as public', () => {
    expect(isPublicDashboardRoute('/dashboard/viewer')).toBe(true);
    expect(isProtectedDashboardRoute('/dashboard/viewer')).toBe(false);
  });

  it('treats a trailing slash as the same route', () => {
    expect(isPublicDashboardRoute('/dashboard/viewer/')).toBe(true);
  });

  it('does not extend the exemption to anything nested under the viewer', () => {
    expect(isPublicDashboardRoute('/dashboard/viewer/secret')).toBe(false);
    expect(isProtectedDashboardRoute('/dashboard/viewer/secret')).toBe(true);
  });

  it('protects the rest of the dashboard', () => {
    for (const route of ['/dashboard', '/dashboard/projects', '/dashboard/settings']) {
      expect(isProtectedDashboardRoute(route)).toBe(true);
    }
  });

  it('leaves non-dashboard routes alone', () => {
    for (const route of ['/', '/login', '/demo', '/pricing']) {
      expect(isProtectedDashboardRoute(route)).toBe(false);
    }
  });
});

describe('when the Supabase env is missing', () => {
  it('sends a protected dashboard route to login in production', async () => {
    clearSupabaseEnv();
    setNodeEnv('production');

    const response = await middleware(request('/dashboard/projects'));

    expect(response.status).toBe(307);
    const location = new URL(response.headers.get('location') ?? '');
    expect(location.pathname).toBe('/login');
    expect(location.searchParams.get('redirect')).toBe('/dashboard/projects');
  });

  it('does not serve the dashboard to an anonymous visitor in production', async () => {
    clearSupabaseEnv();
    setNodeEnv('production');

    const response = await middleware(request('/dashboard'));

    expect(response.status).toBe(307);
  });

  it('still serves public pages in production', async () => {
    clearSupabaseEnv();
    setNodeEnv('production');

    for (const route of ['/', '/login', '/dashboard/viewer']) {
      const response = await middleware(request(route));
      expect(response.status, `${route} should render`).toBe(200);
    }
  });

  it('keeps local development working without secrets', async () => {
    clearSupabaseEnv();
    setNodeEnv('development');

    const response = await middleware(request('/dashboard/projects'));

    expect(response.status).toBe(200);
  });
});

describe('/demo', () => {
  it('is exempt before any Supabase work happens', async () => {
    clearSupabaseEnv();
    setNodeEnv('production');

    for (const route of ['/demo', '/demo/anything']) {
      const response = await middleware(request(route));
      expect(response.status).toBe(200);
    }
  });
});
