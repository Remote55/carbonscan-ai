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
});
