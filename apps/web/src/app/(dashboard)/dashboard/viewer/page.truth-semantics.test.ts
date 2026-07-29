import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

function analysisBadgeCallSite() {
  const pageSource = readFileSync(
    resolve(process.cwd(), 'src/app/(dashboard)/dashboard/viewer/page.tsx'),
    'utf8',
  );
  const branchStart = pageSource.indexOf('{analysis ? (');
  const branchEnd = pageSource.indexOf(') : (', branchStart);

  if (branchStart === -1 || branchEnd === -1) {
    throw new Error('Expected the viewer analysis badge conditional at its render call-site');
  }

  return pageSource.slice(branchStart, branchEnd);
}

describe('viewer analysis badge truth semantics', () => {
  it('renders the neutral LIVE ANALYSIS badge without fabricated runtime claims', () => {
    const callSite = analysisBadgeCallSite();

    expect(callSite).toMatch(/<ModeBadge\s+label="LIVE ANALYSIS"\s*\/>/);
    expect(callSite).not.toMatch(/LOCAL LIVE|local-live|endpoint|token|credentials/i);
  });
});
