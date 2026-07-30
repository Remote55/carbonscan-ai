import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import HomePage from './page';

function getAnchorHrefByLabel(markup: string, label: string) {
  const anchor = (markup.match(/<a\b[^>]*>.*?<\/a>/g) ?? []).find((tag) =>
    tag.includes(`>${label}</a>`),
  );

  return anchor?.match(/\bhref="([^"]+)"/)?.[1];
}

describe('Landing evidence contract', () => {
  it('routes each labelled hero action to the judge demo', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(getAnchorHrefByLabel(markup, 'ทดลอง Demo Dataset')).toBe('/demo');
    expect(getAnchorHrefByLabel(markup, 'อัปโหลด Point Cloud')).toBe('/demo');
  });

  it('reports validation without rounding or promoting incomplete stages', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup).toContain('0.418');
    expect(markup).toContain('0.808');
    expect(markup).toContain('1.1673846154');
    expect(markup).toContain('tlsep = Default');
    expect(markup).toContain('PointNet++ = Experimental');
    expect(markup).toContain('species stage = Stub');
    expect(markup).not.toContain('93.135');
  });

  it('renders exactly the four evidence-led editorial beats', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup.split('data-editorial-beat=').length - 1).toBe(4);
    expect(markup).toContain('ปัญหาที่การวัดแบบเดิมทิ้งไว้');
    expect(markup).toContain('เส้นทางการวัดจากจุดสู่คาร์บอน');
    expect(markup).toContain('หลักฐาน 3D ที่เปิดให้ตรวจสอบ');
    expect(markup).toContain('Validation ที่รายงานตามขอบเขต');
  });

  // The header and footer used to sit inside <main>, which put a navigation and
  // a contentinfo landmark inside the one landmark meant to hold only the page's
  // main content - so "jump to main" landed a screen reader at the top of the nav.
  it('keeps navigation and contentinfo outside the main landmark', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    const mainStart = markup.indexOf('<main');
    const mainEnd = markup.indexOf('</main>');
    expect(mainStart).toBeGreaterThan(-1);
    expect(mainEnd).toBeGreaterThan(mainStart);

    const main = markup.slice(mainStart, mainEnd);
    expect(main).not.toContain('<nav');
    expect(main).not.toContain('<footer');

    // Deliberately not asserting the absence of every <header>: EditorialSection
    // uses one per beat, and a <header> nested in sectioning content is not a
    // banner landmark, so those are correct. The site header is the one that
    // matters, and AppHeader is the only header carrying data-tone.
    const siteHeader = markup.indexOf('<header data-tone');
    expect(siteHeader).toBeGreaterThan(-1);
    expect(siteHeader).toBeLessThan(mainStart);
    expect(main).not.toContain('<header data-tone');
    expect(markup.indexOf('<footer')).toBeGreaterThan(mainEnd);
  });

  it('offers a keyboard skip link that targets the main landmark', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(getAnchorHrefByLabel(markup, 'ข้ามไปยังเนื้อหาหลัก')).toBe('#main-content');
    expect(markup).toContain('id="main-content"');

    const skip = (markup.match(/<a\b[^>]*>.*?<\/a>/g) ?? []).find((tag) =>
      tag.includes('#main-content'),
    );
    // Hidden until focused, then visible - not permanently hidden, which would
    // make it useless, and not permanently visible either.
    expect(skip).toContain('sr-only');
    expect(skip).toContain('focus:not-sr-only');
  });
});
