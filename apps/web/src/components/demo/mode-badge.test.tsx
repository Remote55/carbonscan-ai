import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { ModeBadge } from './mode-badge';

describe('ModeBadge neutral analysis state', () => {
  it('renders a successful analysis without inventing its runtime location', () => {
    expect(() => renderToStaticMarkup(<ModeBadge label="LIVE ANALYSIS" />)).not.toThrow();

    const markup = renderToStaticMarkup(<ModeBadge label="LIVE ANALYSIS" />);
    expect(markup).toContain('LIVE ANALYSIS');
    expect(markup).not.toContain('LOCAL LIVE RUNTIME');
    expect(markup).not.toContain('PRODUCTION LIVE RUNTIME');
  });
});
