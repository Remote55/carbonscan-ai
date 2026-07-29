import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { VISUAL_ASSETS } from './visual-assets';

describe('Forest Observatory visual assets', () => {
  it('keeps every production image local and rights-documented', () => {
    for (const asset of Object.values(VISUAL_ASSETS)) {
      expect(asset.src.startsWith('/visual/forest-observatory/')).toBe(true);
      expect(['team-owned', 'generated', 'CC0', 'explicit-license']).toContain(asset.rights);
      expect(existsSync(join(process.cwd(), 'public', asset.src.slice(1)))).toBe(true);
    }
  });
});
