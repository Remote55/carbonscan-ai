import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { DemoShell, resolveFrozenDemoLoad } from './demo-shell';

describe('DemoShell frozen evidence failure', () => {
  it('shows loading failed without tree, carbon, or CO2e totals after the frozen load rejects', async () => {
    const frozenLoad = await resolveFrozenDemoLoad(async () => {
      throw new Error('Frozen demo result hash mismatch');
    });

    const markup = renderToStaticMarkup(
      <DemoShell
        mode={{ kind: 'frozen', reason: 'sample-first' }}
        frozenLoad={frozenLoad}
        onUseFrozen={() => undefined}
      />,
    );

    expect(markup).toContain('>loading failed</p>');
    expect(markup).not.toContain('Detected trees');
    expect(markup).not.toContain('Carbon stock estimate');
    expect(markup).not.toContain('CO₂e estimate');
    expect(markup).not.toContain('1,289.74');
    expect(markup).not.toContain('4,729.06');
  });
});
