import React, { type ReactNode } from 'react';

import type { DemoModeState } from '../../lib/demo-mode';

export const FROZEN_EVIDENCE_LABEL = 'FROZEN EVIDENCE — NOT A LIVE RUN';

export function ViewerAnalysisBadge({
  analysis,
  fallback,
}: {
  analysis: object | null;
  fallback: ReactNode;
}) {
  return analysis !== null ? <ModeBadge label={'LIVE ANALYSIS'} /> : <>{fallback}</>;
}

type ModeBadgeProps =
  | { state: DemoModeState; label?: never }
  | { state?: never; label: 'LIVE ANALYSIS' };

export function ModeBadge(props: ModeBadgeProps) {
  if (props.label) {
    return <Badge label={props.label} tone="border-lichen bg-canopy text-paper" />;
  }

  const { state } = props;
  if (state.kind === 'booting') return null;

  const label =
    state.kind === 'frozen'
      ? FROZEN_EVIDENCE_LABEL
      : state.kind === 'checking'
        ? 'VERIFYING LIVE RUNTIME'
        : state.kind === 'local-live'
          ? 'LOCAL LIVE RUNTIME'
          : 'PRODUCTION LIVE RUNTIME';
  const tone =
    state.kind === 'frozen'
      ? 'border-moss bg-lichen text-deep-forest'
      : state.kind === 'checking'
        ? 'border-evidence-amber bg-gallery-ivory text-deep-forest'
        : 'border-lichen bg-canopy text-paper';

  return <Badge label={label} tone={tone} />;
}

function Badge({ label, tone }: { label: string; tone: string }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 font-mono text-[0.625rem] font-medium tracking-[0.08em] ${tone}`}
    >
      <span className="size-1.5 rounded-full bg-current" aria-hidden="true" />
      {label}
    </span>
  );
}
