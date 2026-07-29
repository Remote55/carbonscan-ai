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
      ].map(async (resourcePath) => [
        resourcePath,
        new Uint8Array(await readFile(path.join(publicRoot, resourcePath))),
      ] as const),
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
    expect(markup).not.toContain('1,289.74');
    expect(markup).not.toContain('4,729.06');
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
    expect(markup).toContain('1,289.74 kg C');
    expect(markup).toContain('4,729.06 kg CO₂e');
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
