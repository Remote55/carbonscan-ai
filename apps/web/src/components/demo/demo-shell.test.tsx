import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

import { JUDGE_DEMO_EVIDENCE } from '../../generated/judge-demo-evidence';
import { loadFrozenDemo, type FrozenDemoFetcher } from '../../lib/frozen-demo';
import { DemoShell, resolveFrozenDemoLoad } from './demo-shell';

function copyToArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  return copy.buffer;
}

async function loadCurrentFrozenBundle() {
  const publicRoot = path.resolve(process.cwd(), 'public');
  const files = new Map<string, Uint8Array>(
    await Promise.all(
      [
        JUDGE_DEMO_EVIDENCE.manifestPath,
        JUDGE_DEMO_EVIDENCE.inputPath,
        JUDGE_DEMO_EVIDENCE.segmentedPath,
        JUDGE_DEMO_EVIDENCE.resultPath,
      ].map(
        async (resourcePath) =>
          [
            resourcePath,
            new Uint8Array(await readFile(path.join(publicRoot, resourcePath))),
          ] as const,
      ),
    ),
  );
  const fetcher: FrozenDemoFetcher = async (resource) => {
    const resourcePath = typeof resource === 'string' ? resource : resource.pathname;
    const bytes = files.get(resourcePath);
    return bytes
      ? new Response(copyToArrayBuffer(bytes), { status: 200 })
      : new Response('not found', { status: 404 });
  };

  return loadFrozenDemo(fetcher, JUDGE_DEMO_EVIDENCE.manifestSha256);
}

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
    expect(markup).not.toContain('ต้นไม้ที่คำนวณสำเร็จ');
    expect(markup).not.toContain('Carbon stock estimate');
    expect(markup).not.toContain('CO₂e estimate');
    expect(markup).not.toContain('1,295.17');
    expect(markup).not.toContain('4,748.95');
  });
});

describe('DemoShell frozen evidence result', () => {
  it('labels the frozen route plainly and renders the verified current artifact', async () => {
    const bundle = await loadCurrentFrozenBundle();
    const markup = renderToStaticMarkup(
      <DemoShell
        mode={{ kind: 'frozen', reason: 'sample-first' }}
        frozenLoad={{ kind: 'ready', bundle }}
        onUseFrozen={() => undefined}
      />,
    );

    expect(markup).toContain('FROZEN EVIDENCE — NOT A LIVE RUN');
    expect(markup).toContain('ต้นไม้ที่ตรวจพบ 5');
    expect(markup).toContain('ต้นไม้ที่คำนวณสำเร็จ 3');
    expect(markup).toContain('ไม่รวมผล 2');
    // Hardcoded on purpose. Reading these from the manifest would make the
    // test pass whatever the manifest said; typed out, changing the published
    // figure costs somebody a deliberate edit. It has moved twice:
    //   1,289.74 / 4,729.06 -> 1,295.17 / 4,748.95
    //     the ground estimator stopped putting the floor up the trunk
    //   1,295.17 / 4,748.95 -> 1,035.93 / 3,798.38
    //     the artefacts were regenerated after 8cf3058 replaced five air-dry
    //     wood densities with basic ones, which is the quantity Chave takes
    expect(markup).toContain('1,035.93 kg C');
    expect(markup).toContain('3,798.38 kg CO₂e');
  });

  it('guides the judge through the five evidence stages', () => {
    const markup = renderToStaticMarkup(
      <DemoShell
        mode={{ kind: 'frozen', reason: 'sample-first' }}
        frozenLoad={{ kind: 'loading' }}
        onUseFrozen={() => undefined}
      />,
    );

    expect(markup).toContain('INPUT');
    expect(markup).toContain('VALIDATE');
    expect(markup).toContain('PIPELINE');
    expect(markup).toContain('RESULT');
    expect(markup).toContain('PROVENANCE');
  });
});

describe('DemoShell input-mode semantics', () => {
  const credentials = { endpoint: 'http://127.0.0.1:8000', token: 'a'.repeat(64) } as const;

  // The active mode used to be a <span aria-current="page">, which claims "page"
  // about something that is not a page and still left assistive tech no way to
  // tell the two labels were alternatives. It is a state readout plus the single
  // action that exists, so it must read as exactly that.
  it('announces the current mode as text instead of misusing aria-current', () => {
    for (const mode of [
      { kind: 'frozen', reason: 'sample-first' } as const,
      { kind: 'local-live', credentials, pipelineVersion: '0.4.0' } as const,
    ]) {
      const markup = renderToStaticMarkup(
        <DemoShell mode={mode} frozenLoad={{ kind: 'loading' }} onUseFrozen={() => undefined} />,
      );

      expect(markup).not.toContain('aria-current');
      expect(markup).toContain('โหมดปัจจุบัน:');
    }
  });

  it('exposes switching back to the frozen route as a real labelled button', () => {
    const markup = renderToStaticMarkup(
      <DemoShell
        mode={{ kind: 'local-live', credentials, pipelineVersion: '0.4.0' }}
        frozenLoad={{ kind: 'loading' }}
        onUseFrozen={() => undefined}
      />,
    );

    const button = (markup.match(/<button\b[^>]*>/g) ?? []).find((tag) =>
      tag.includes('สลับไปใช้ Frozen Sample'),
    );
    expect(button).toBeDefined();
    expect(button).toContain('type="button"');
  });

  // The reliability panel's stated purpose is not hiding status, so it must not
  // claim a verification is in progress when none was ever started. In live mode
  // the frozen bundle is deliberately not fetched, and the old code read that as
  // VERIFYING for the whole length of the demo.
  it('does not claim to be verifying artifacts it never fetched in live mode', () => {
    const markup = renderToStaticMarkup(
      <DemoShell
        mode={{ kind: 'local-live', credentials, pipelineVersion: '0.4.0' }}
        frozenLoad={{ kind: 'loading' }}
        onUseFrozen={() => undefined}
      />,
    );

    expect(markup).toContain('NOT CHECKED IN LIVE MODE');
    expect(markup).not.toContain('VERIFYING');
  });

  it('still reports a real verification in progress on the frozen route', () => {
    const markup = renderToStaticMarkup(
      <DemoShell
        mode={{ kind: 'frozen', reason: 'sample-first' }}
        frozenLoad={{ kind: 'loading' }}
        onUseFrozen={() => undefined}
      />,
    );

    expect(markup).toContain('VERIFYING');
  });

  // Live mode is only reachable through a runtime handoff, so advertising a
  // control that could switch into it would be a lie about what the page can do.
  it('offers no control that claims to switch into live mode', () => {
    const markup = renderToStaticMarkup(
      <DemoShell
        mode={{ kind: 'frozen', reason: 'unreachable' }}
        frozenLoad={{ kind: 'loading' }}
        onUseFrozen={() => undefined}
      />,
    );

    expect(markup).not.toContain('role="tablist"');
    expect(markup).not.toContain('aria-pressed');
    const buttons = markup.match(/<button\b[^>]*>[^<]*/g) ?? [];
    expect(buttons.some((tag) => tag.includes('Live Upload'))).toBe(false);
  });
});
