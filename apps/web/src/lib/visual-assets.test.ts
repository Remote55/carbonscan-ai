import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { VISUAL_ASSETS } from './visual-assets';

describe('Forest Observatory visual assets', () => {
  it('keeps every production image local and rights-documented', () => {
    expect(VISUAL_ASSETS).toEqual({
      landing: {
        src: '/visual/forest-observatory/landing-mist.webp',
        rights: 'generated',
      },
      judge: {
        src: '/visual/forest-observatory/judge-road.webp',
        rights: 'generated',
      },
      auth: {
        src: '/visual/forest-observatory/auth-lake.webp',
        rights: 'generated',
      },
      dashboard: {
        src: '/visual/forest-observatory/dashboard-road.webp',
        rights: 'generated',
      },
    });

    for (const asset of Object.values(VISUAL_ASSETS)) {
      expect(asset.src.startsWith('/visual/forest-observatory/')).toBe(true);
      expect(['team-owned', 'generated', 'CC0', 'explicit-license']).toContain(asset.rights);
      expect(existsSync(join(process.cwd(), 'public', asset.src.slice(1)))).toBe(true);
    }
  });
});
