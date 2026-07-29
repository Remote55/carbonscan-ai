import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { ViewerAnalysisBadge } from '../../../../components/demo/mode-badge';

function visibleText(markup: string) {
  return markup.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

describe('viewer analysis badge truth semantics', () => {
  it('renders exactly the neutral analysis status without fabricated runtime claims', () => {
    const markup = renderToStaticMarkup(
      <ViewerAnalysisBadge analysis={{ metadata: { pipeline_version: 'test' } }} fallback={null} />,
    );

    expect(visibleText(markup)).toBe('LIVE ANALYSIS');
    expect(markup).not.toMatch(
      /local[\s_-]*live|runtime[\s_-]*location|confirmed-analysis-runtime|endpoint|token|credentials/i,
    );
  });

  it('renders the supplied preview status before an analysis exists', () => {
    const markup = renderToStaticMarkup(
      <ViewerAnalysisBadge analysis={null} fallback={<span>Synthetic</span>} />,
    );

    expect(visibleText(markup)).toBe('Synthetic');
  });
});
