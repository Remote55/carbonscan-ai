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
  // The previous version of this test asserted that BOTH hero actions point at
  // /demo, and passed - which is how a button labelled "อัปโหลด Point Cloud"
  // shipped pointing at a page with no file input. /demo only grows an upload
  // panel once the launcher hands it a runtime token, so the public route is
  // read-only evidence. A CTA has to land somewhere that can do what it says.
  it('sends the evidence action to the demo and the upload action where uploading works', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(getAnchorHrefByLabel(markup, 'ดูหลักฐานที่ตรวจแฮชแล้ว')).toBe('/demo');
    expect(getAnchorHrefByLabel(markup, 'เข้าสู่ระบบเพื่ออัปโหลดไฟล์')).toBe(
      '/login?redirect=%2Fdashboard%2Fviewer',
    );
  });

  it('never points an upload promise at the read-only demo route', () => {
    const markup = renderToStaticMarkup(<HomePage />);
    const anchors = markup.match(/<a\b[^>]*>.*?<\/a>/g) ?? [];

    // Matching the whole anchor rather than stripping its tags to recover the
    // label. `replace(/<[^>]+>/g, '')` is the sanitise-by-regex antipattern - one
    // pass over `<<script>>` still leaves `<script` - and CodeQL rightly failed
    // the build over it. Nothing here is ever written back to a DOM, so it was
    // not exploitable, but the shorter form has no such argument to make.
    // Hrefs are ASCII paths, so a Thai label cannot be confused for one.
    const uploadAnchors = anchors.filter((anchor) => anchor.includes('อัปโหลด'));
    expect(uploadAnchors.length).toBeGreaterThan(0);

    for (const anchor of uploadAnchors) {
      const href = anchor.match(/\bhref="([^"]+)"/)?.[1];
      expect(href).toBeDefined();
      expect(href).not.toBe('/demo');
    }
  });

  it('reports validation without rounding or promoting incomplete stages', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup).toContain('0.418');
    expect(markup).toContain('0.808');
    expect(markup).toContain('1.1673846154');
    // The three facts moved from one cramped line into labelled cards after a
    // reviewer asked whether they mattered at all. Assert the facts, not the old
    // sentence: what must hold is that tlsep is the shipped backend, PointNet++ is
    // Experimental, and species is a stub - however they are laid out.
    expect(markup).toContain('tlsep');
    expect(markup).toContain('PointNet++');
    expect(markup).toContain('Experimental');
    expect(markup).toContain('Stub');
    expect(markup).not.toContain('93.135');

    // The one arrangement that would be a lie.
    expect(markup).not.toMatch(/PointNet\+\+[^<]*Default/);
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

  // JetBrains Mono has no Thai glyphs. Thai set in it silently falls back to
  // another face at 11px, which is how this project shipped an unreadable
  // label once already. This scans the rendered markup rather than the source,
  // because the source is where the mistake looks correct.
  it('never sets Thai text in the monospace face', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    // Direct text inside an element carrying font-mono. Eyebrows and badges are
    // all plain <p>/<span> with no nested markup, which is exactly this shape.
    const monoWithText = /<(?:p|span|dt|dd)[^>]*class="[^"]*font-mono[^"]*"[^>]*>([^<]+)</g;
    const THAI = /[\u0E00-\u0E7F]/;
    const offenders: string[] = [];
    for (const match of markup.matchAll(monoWithText)) {
      if (THAI.test(match[1])) offenders.push(match[1].trim());
    }

    expect(offenders).toEqual([]);
  });
});
