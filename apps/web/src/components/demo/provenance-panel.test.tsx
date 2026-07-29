import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import manifestJson from '../../../public/demo/manifest.json';
import type { FrozenDemoManifest } from '../../lib/frozen-demo';
import { ProvenancePanel } from './provenance-panel';

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
    expect(markup).toContain('ยังไม่ถูกเลื่อนเป็นค่าตั้งต้น');
    expect(markup).toContain('Dataset scope');
    expect(markup).toContain('deterministic fixture');
    expect(markup).toContain('Allometric source');
    expect(markup).toContain('species_db.csv');
    expect(markup).toContain('Limitations');
    expect(markup).toContain('ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรองหรือซื้อขายได้');
  });
});
