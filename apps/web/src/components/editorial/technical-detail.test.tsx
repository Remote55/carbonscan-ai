import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { TechnicalDetail } from './technical-detail';

describe('TechnicalDetail', () => {
  // Closed is the whole point. A reader who does not want the jargon should
  // never meet it, and a disclosure that ships open is just a paragraph.
  it('is closed until someone opens it', () => {
    const markup = renderToStaticMarkup(<TechnicalDetail>tlsep</TechnicalDetail>);

    expect(markup).toContain('<details');
    expect(markup).not.toContain('open');
  });

  it('carries one label across the whole site', () => {
    const markup = renderToStaticMarkup(<TechnicalDetail>tlsep</TechnicalDetail>);

    expect(markup).toContain('<summary');
    expect(markup).toContain('รายละเอียดทางเทคนิค');
  });

  it('renders what it was given', () => {
    const markup = renderToStaticMarkup(
      <TechnicalDetail>Wood IoU 0.418</TechnicalDetail>,
    );

    expect(markup).toContain('Wood IoU 0.418');
  });
});
