import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { BrandMark } from '../brand/brand-mark';
import { EvidenceMetric } from '../evidence/evidence-metric';
import { StatusState } from '../evidence/status-state';
import { AppHeader } from '../layout/app-header';
import { CompactWorkspaceHeader } from '../layout/compact-workspace-header';
import { Button } from '../ui/button';
import { EditorialSection } from './editorial-section';

describe('TreeQ editorial primitives', () => {
  it('renders an accessible brand and explicit evidence labels', () => {
    const markup = renderToStaticMarkup(
      <>
        <BrandMark />
        <EvidenceMetric label="Wood IoU" value="0.418" note="Wan held-out" />
      </>,
    );

    expect(markup).toContain('TreeQ Carbon');
    expect(markup).toContain('Wood IoU');
    expect(markup).toContain('0.418');
    expect(markup).toContain('Wan held-out');
  });

  it('renders navigable workspace primitives and an explicit status', () => {
    const markup = renderToStaticMarkup(
      <>
        <AppHeader tone="transparent" />
        <CompactWorkspaceHeader title="Analysis workspace" mode="Frozen evidence" backHref="/demo" />
        <EditorialSection eyebrow="Method" title="Traceable assessment">
          <p>Every result keeps its provenance.</p>
        </EditorialSection>
        <StatusState label="Pipeline" value="Ready" note="Deterministic baseline" tone="ready" />
        <Button variant="editorial" size="xl">
          Start review
        </Button>
      </>,
    );

    expect(markup).toContain('aria-label="Primary navigation"');
    expect(markup).toContain('href="/"');
    expect(markup).toContain('href="/#tech"');
    expect(markup).toContain('href="/#how"');
    expect(markup).toContain('href="/#proof"');
    expect(markup).toContain('href="/dashboard/viewer"');
    expect(markup).toContain('href="/login"');
    expect(markup).toContain('href="/demo"');
    expect(markup).toContain('aria-label="Workspace navigation"');
    expect(markup).toContain('Analysis workspace');
    expect(markup).toContain('Traceable assessment');
    expect(markup).toContain('Pipeline');
    expect(markup).toContain('Ready');
    expect(markup).toContain('Deterministic baseline');
    expect(markup).toContain('h-12');
  });
});
