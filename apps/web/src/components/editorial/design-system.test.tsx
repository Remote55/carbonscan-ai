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
    const appHeaderMarkup = renderToStaticMarkup(<AppHeader tone="transparent" />);
    const workspaceMarkup = renderToStaticMarkup(
      <>
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

    expect(appHeaderMarkup).toContain('aria-label="Primary navigation"');
    expect(appHeaderMarkup).toContain('href="/"');
    expect(appHeaderMarkup).toContain('href="/#tech"');
    expect(appHeaderMarkup).toContain('href="/#how"');
    expect(appHeaderMarkup).toContain('href="/#proof"');
    // The workspace link left the menu; the hero button is now the only way in
    // from the landing page, and page.test.tsx is what holds that.
    expect(appHeaderMarkup).toContain('href="/demo"');
    expect(appHeaderMarkup).toContain('href="/login"');
    expect(appHeaderMarkup).toContain('href="/demo"');
    expect(workspaceMarkup).toContain('aria-label="Workspace navigation"');
    expect(workspaceMarkup).toContain('href="/demo"');
    expect(workspaceMarkup).toContain('Analysis workspace');
    expect(workspaceMarkup).toContain('Traceable assessment');
    expect(workspaceMarkup).toContain('Pipeline');
    expect(workspaceMarkup).toContain('Ready');
    expect(workspaceMarkup).toContain('Deterministic baseline');
    expect(workspaceMarkup).toContain('h-12');
  });
});
