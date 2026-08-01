import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

import manifestJson from '../../../public/demo/manifest.json';
import type { FrozenDemoManifest } from '../../lib/frozen-demo';
import { ProvenancePanel } from './provenance-panel';

function tokenHex(css: string, token: string): string {
  const match = css.match(new RegExp(`--${token}:\\s*(#[0-9a-f]{6})`, 'i'));
  if (!match) throw new Error(`Missing color token: ${token}`);
  return match[1];
}

function relativeLuminance(hex: string): number {
  const channels = hex
    .slice(1)
    .match(/.{2}/g)!
    .map((value) => parseInt(value, 16) / 255)
    .map((value) => (value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4)));
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(foreground: string, background: string): number {
  const first = relativeLuminance(foreground);
  const second = relativeLuminance(background);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

function renderedElement(markup: string, text: string): string {
  const escaped = text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = markup.match(new RegExp(`<[^>]+>${escaped}<\\/[^>]+>`));
  if (!match) throw new Error(`Missing rendered text: ${text}`);
  return match[0];
}

function renderedTextToken(element: string, css: string): string {
  const explicitToken = element.match(/text-(canopy|moss)/)?.[1];
  if (explicitToken) return explicitToken;
  if (element.includes('editorial-eyebrow')) {
    const utilityRule = css.match(/\.editorial-eyebrow\s*{([^}]*)}/s)?.[1] ?? '';
    const utilityToken = utilityRule.match(/text-(canopy|moss)/)?.[1];
    if (utilityToken) return utilityToken;
  }
  throw new Error(`Missing resolvable light-surface text token: ${element}`);
}

describe('ProvenancePanel', () => {
  it('groups the verified manifest identities and artifact hashes for audit', () => {
    const markup = renderToStaticMarkup(
      <ProvenancePanel manifest={manifestJson as FrozenDemoManifest} />,
    );

    expect(markup).toContain('Run identity');
    expect(markup).toContain('Input / artifact hashes');
    expect(markup).toContain('Pipeline / backend');
    expect(markup).toContain('Git commit');
    expect(markup).toContain('9aaf68d4f65c');
    expect(markup).toContain(manifestJson.artifacts.input.sha256);
    expect(markup).toContain(manifestJson.artifacts.result.sha256);
    expect(markup).toContain(manifestJson.artifacts.segmented.sha256);
    expect(markup).toContain('0.4.0');
    expect(markup).toContain('tlsep');
  });

  it('keeps model status, dataset scope, allometric boundary, and certification limits visible', () => {
    const markup = renderToStaticMarkup(
      <ProvenancePanel manifest={manifestJson as FrozenDemoManifest} />,
    );

    expect(markup).toContain('Species status');
    expect(markup).toContain('stub');
    expect(markup).toContain('PointNet++');
    expect(markup).toContain('Experimental');
    // The claim moved from "not promoted to default" to naming the backend the
    // run actually used. Both halves have to be present for that to say the
    // same thing: the candidate is Experimental, and these numbers came from
    // somewhere else.
    expect(markup).toContain('กำหนดสิทธิ์อยู่ในระดับ');
    expect(markup).toContain('อ้างอิงการประมวลผลผ่าน tlsep');
    // The species line must still deny an AI inference, however it is worded.
    expect(markup).toContain('ไม่อ้างอิงจากการอนุมานของโมเดล AI');
    expect(markup).toContain('Dataset scope');
    expect(markup).toContain('deterministic fixture');
    expect(markup).toContain('Allometric source');
    expect(markup).toContain('species_db.csv');
    expect(markup).toContain('Limitations');
    expect(markup).toContain('ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรองหรือซื้อขายได้');
  });

  it('keeps critical small audit labels at WCAG AA contrast on light evidence surfaces', () => {
    const markup = renderToStaticMarkup(
      <ProvenancePanel manifest={manifestJson as FrozenDemoManifest} />,
    );
    const css = readFileSync(path.resolve(process.cwd(), 'src/app/globals.css'), 'utf8');

    const lightSurfaceLabels = [
      'Audit / provenance / reproducibility',
      'Run identity',
      'Git commit',
      'Input / artifact hashes',
      'input',
      'Pipeline / backend',
      'Species status',
      'Allometric source',
    ];
    for (const label of lightSurfaceLabels) {
      const element = renderedElement(markup, label);
      const foreground = tokenHex(css, renderedTextToken(element, css));

      expect(element).not.toContain('text-moss');
      expect(contrastRatio(foreground, tokenHex(css, 'paper'))).toBeGreaterThanOrEqual(4.5);
      expect(contrastRatio(foreground, tokenHex(css, 'gallery-ivory'))).toBeGreaterThanOrEqual(4.5);
    }
  });
});
