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
  it('sends each landing action to the correct route', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(getAnchorHrefByLabel(markup, 'ดูผลการประเมิน')).toBe('/demo');

    expect(getAnchorHrefByLabel(markup, 'ทดลองอัปโหลดไฟล์')).toBe(
      '/dashboard/viewer',
    );

    // The ดูแผนที่ action is gone with the map route, which the supervisor
    // asked to be taken down until it is finished. Nothing on the landing page
    // may point at it while it does not exist.
    expect(markup).not.toContain('/dashboard/map');
  });

  it('never points an upload promise at the read-only demo route', () => {
    const markup = renderToStaticMarkup(<HomePage />);
    const anchors = markup.match(/<a\b[^>]*>.*?<\/a>/g) ?? [];

    const uploadAnchors = anchors.filter((anchor) =>
      anchor.includes('อัปโหลด'),
    );

    expect(uploadAnchors.length).toBeGreaterThan(0);

    for (const anchor of uploadAnchors) {
      const href = anchor.match(/\bhref="([^"]+)"/)?.[1];

      expect(href).toBeDefined();
      expect(href).not.toBe('/demo');
    }
  });

  it('reports the current validation values and implementation status honestly', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup).toContain('41.8%');
    expect(markup).toContain('80.8%');
    expect(markup).toContain('1.17');
    expect(markup).toContain('ซม.');

    expect(markup).toContain('ความแม่นยำการแยกลำต้น');
    expect(markup).toContain('ความแม่นยำการแยกใบไม้');
    expect(markup).toContain('ค่าคลาดเคลื่อนการวัดขนาดลำต้น');

    expect(markup).toContain('tlsep');
    expect(markup).toContain('PointNet++');
    expect(markup).toContain('Experimental');

    expect(markup).not.toContain('93.135');
    expect(markup).not.toMatch(/PointNet\+\+[^<]*Default/);
  });

  it('renders the five evidence-led editorial beats', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup.split('data-editorial-beat=').length - 1).toBe(5);

    expect(markup).toContain('ข้อจำกัดของการสำรวจแบบเดิม');
    expect(markup).toContain('เป้าหมายของโครงการ');
    expect(markup).toContain('วิธีทำงาน');
    expect(markup).toContain('ชุดข้อมูลและโมเดลสามมิติ');
    expect(markup).toContain('ความแม่นยำ');
  });

  it('renders each editorial beat exactly once', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(
      markup.match(/data-editorial-beat="problem"/g)?.length ?? 0,
    ).toBe(1);

    expect(
      markup.match(/data-editorial-beat="objectives"/g)?.length ?? 0,
    ).toBe(1);

    expect(
      markup.match(/data-editorial-beat="journey"/g)?.length ?? 0,
    ).toBe(1);

    expect(
      markup.match(
        /data-editorial-beat="three-dimensional-evidence"/g,
      )?.length ?? 0,
    ).toBe(1);

    expect(
      markup.match(/data-editorial-beat="validation"/g)?.length ?? 0,
    ).toBe(1);
  });

  it('shows the three project objectives', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(markup).toContain('ลดอุปสรรคทางภูมิศาสตร์');
    expect(markup).toContain('ลดต้นทุนและเวลา');
    expect(markup).toContain('ยกระดับความโปร่งใส');
  });

  it('describes the real PLY point cloud shown in the hero', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    /*
     * useEffect ยังไม่ทำงานระหว่าง renderToStaticMarkup
     * จึงตรวจข้อความสถานะเริ่มต้นแทนตัว Canvas ที่โหลดภายหลังใน browser
     */
    expect(markup).toContain('กำลังโหลด Point Cloud');
    expect(markup).toContain('กำลังเตรียมข้อมูลสามมิติสำหรับแสดงผล');
  });

  it('keeps navigation and contentinfo outside the main landmark', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    const mainStart = markup.indexOf('<main');
    const mainEnd = markup.indexOf('</main>');

    expect(mainStart).toBeGreaterThan(-1);
    expect(mainEnd).toBeGreaterThan(mainStart);

    const main = markup.slice(mainStart, mainEnd);

    expect(main).not.toContain('<nav');
    expect(main).not.toContain('<footer');

    const siteHeader = markup.indexOf('<header data-tone');

    expect(siteHeader).toBeGreaterThan(-1);
    expect(siteHeader).toBeLessThan(mainStart);
    expect(main).not.toContain('<header data-tone');
    expect(markup.indexOf('<footer')).toBeGreaterThan(mainEnd);
  });

  it('offers a keyboard skip link that targets the main landmark', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    expect(
      getAnchorHrefByLabel(markup, 'ข้ามไปยังเนื้อหาหลัก'),
    ).toBe('#main-content');

    expect(markup).toContain('id="main-content"');

    const skip = (
      markup.match(/<a\b[^>]*>.*?<\/a>/g) ?? []
    ).find((tag) => tag.includes('#main-content'));

    expect(skip).toBeDefined();
    expect(skip).toContain('sr-only');
    expect(skip).toContain('focus:not-sr-only');
  });

  it('never sets Thai text in the monospace face', () => {
    const markup = renderToStaticMarkup(<HomePage />);

    const monoWithText =
      /<(?:p|span|dt|dd)[^>]*class="[^"]*font-mono[^"]*"[^>]*>([^<]+)</g;

    const THAI = /[\u0E00-\u0E7F]/;
    const offenders: string[] = [];

    for (const match of markup.matchAll(monoWithText)) {
      const text = match[1].trim();

      if (THAI.test(text)) {
        offenders.push(text);
      }
    }

    expect(offenders).toEqual([]);
  });
});