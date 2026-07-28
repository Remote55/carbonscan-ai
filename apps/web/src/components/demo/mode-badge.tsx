import type { DemoModeState } from '@/lib/demo-mode';

export const FROZEN_EVIDENCE_LABEL = 'FROZEN EVIDENCE — NOT A LIVE RUN';

export function ModeBadge({ state }: { state: DemoModeState }) {
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
      ? 'border-amber-300 bg-amber-50 text-amber-950'
      : 'border-emerald-300 bg-emerald-50 text-emerald-950';

  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 font-mono text-xs font-bold tracking-[0.08em] ${tone}`}
    >
      {label}
    </span>
  );
}
