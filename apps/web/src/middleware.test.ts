import { describe, expect, it } from 'vitest';

import { PUBLIC_DASHBOARD_ROUTES, isPublicDashboardRoute } from './middleware';

describe('isPublicDashboardRoute', () => {
  it('opens the 3D viewer, which a judge is handed cold', () => {
    expect(isPublicDashboardRoute('/dashboard/viewer')).toBe(true);
  });

  it('keeps the rest of the dashboard signed-in only', () => {
    // Opening the viewer must not open anything that shows one account's data.
    expect(isPublicDashboardRoute('/dashboard')).toBe(false);
    expect(isPublicDashboardRoute('/dashboard/settings')).toBe(false);
    expect(isPublicDashboardRoute('/dashboard/trees')).toBe(false);
  });

  it('does not extend the exemption to anything nested under the viewer', () => {
    // A prefix match here would hand the same pass to routes that do not exist
    // yet, so a later page under this path would ship public by accident.
    expect(isPublicDashboardRoute('/dashboard/viewer/admin')).toBe(false);
    expect(isPublicDashboardRoute('/dashboard/viewer-secrets')).toBe(false);
  });

  it('treats a trailing slash as the same route', () => {
    expect(isPublicDashboardRoute('/dashboard/viewer/')).toBe(true);
  });

  it('exempts exactly one route, so the list cannot grow unnoticed', () => {
    expect([...PUBLIC_DASHBOARD_ROUTES]).toEqual(['/dashboard/viewer']);
  });
});
