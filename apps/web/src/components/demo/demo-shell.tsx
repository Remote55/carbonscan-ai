'use client';

import { useEffect, useReducer, useState } from 'react';

import { createDemoApiClient } from '@/lib/demo-api';
import { demoModeReducer, type DemoModeState } from '@/lib/demo-mode';
import { consumeRuntimeHandoff } from '@/lib/demo-runtime';
import { loadFrozenDemo, type FrozenDemoBundle } from '@/lib/frozen-demo';
import { ModeBadge } from './mode-badge';

const initialMode: DemoModeState = { kind: 'booting' };
const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });

export function DemoShell() {
  const [mode, dispatch] = useReducer(demoModeReducer, initialMode);
  const [bundle, setBundle] = useState<FrozenDemoBundle | null>(null);
  const [loadingFailed, setLoadingFailed] = useState(false);

  useEffect(() => {
    const hadHandoff = window.location.hash.length > 0;
    const credentials = consumeRuntimeHandoff({
      location: window.location,
      history: window.history,
      storage: window.sessionStorage,
    });
    dispatch({
      type: 'BOOT',
      credentials,
      invalidHandoff: hadHandoff && credentials === null,
    });
  }, []);

  useEffect(() => {
    if (mode.kind !== 'checking') return;
    let cancelled = false;
    createDemoApiClient(mode.credentials)
      .checkReadiness()
      .then(({ pipelineVersion }) => {
        if (!cancelled) dispatch({ type: 'READINESS_OK', pipelineVersion });
      })
      .catch(() => {
        if (!cancelled) dispatch({ type: 'READINESS_FAILED' });
      });
    return () => {
      cancelled = true;
    };
  }, [mode]);

  useEffect(() => {
    if (mode.kind !== 'frozen') return;
    let cancelled = false;
    setBundle(null);
    setLoadingFailed(false);
    loadFrozenDemo()
      .then((verifiedBundle) => {
        if (!cancelled) setBundle(verifiedBundle);
      })
      .catch(() => {
        if (!cancelled) setLoadingFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [mode]);

  if (mode.kind === 'booting') {
    return <main className="min-h-screen bg-[#f5f2e9]" aria-busy="true" />;
  }

  if (mode.kind === 'checking') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f5f2e9] px-6">
        <div className="text-center">
          <ModeBadge state={mode} />
          <p className="mt-4 text-sm text-slate-600">Checking authenticated runtime readiness…</p>
        </div>
      </main>
    );
  }

  if (mode.kind === 'production-live' || mode.kind === 'local-live') {
    return (
      <main className="min-h-screen bg-[#f5f2e9] px-6 py-16 text-slate-900">
        <div className="mx-auto max-w-3xl rounded-3xl border border-emerald-200 bg-white p-8 shadow-sm">
          <ModeBadge state={mode} />
          <h1 className="mt-6 text-3xl font-semibold">Authenticated live runtime is ready</h1>
          <p className="mt-3 text-slate-600">
            Pipeline {mode.pipelineVersion}. Live analysis controls arrive in the next demo stage.
          </p>
          <button
            type="button"
            className="mt-8 rounded-full bg-emerald-950 px-5 py-2.5 text-sm font-semibold text-white"
            onClick={() => dispatch({ type: 'USE_FROZEN' })}
          >
            View verified frozen evidence
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f5f2e9] px-6 py-12 text-slate-950">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-emerald-800">
            TreeQ Carbon Platform · Judge Demo
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
            Hash-verified measurement evidence
          </h1>
          <p className="mt-4 max-w-3xl text-slate-600">
            A deterministic seed-42 fixture showing the implemented point-cloud pipeline with
            explicit provenance and limitations.
          </p>
        </header>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <ModeBadge state={mode} />

          {loadingFailed ? (
            <p className="mt-8 font-mono text-sm font-semibold text-red-800">loading failed</p>
          ) : !bundle ? (
            <p className="mt-8 text-sm text-slate-600">Verifying every evidence byte…</p>
          ) : (
            <>
              <div className="mt-8 grid gap-4 sm:grid-cols-3">
                <EvidenceMetric
                  label="Detected trees"
                  value={number.format(bundle.result.summary.total_trees)}
                />
                <EvidenceMetric
                  label="Carbon stock estimate"
                  value={`${number.format(bundle.result.summary.total_carbon_kg)} kg C`}
                />
                <EvidenceMetric
                  label="CO₂e estimate"
                  value={`${number.format(bundle.result.summary.total_co2eq_kg)} kg CO₂e`}
                />
              </div>

              <div className="mt-8 grid gap-3 border-t border-slate-200 pt-6 text-sm sm:grid-cols-2">
                <EvidenceFact
                  label="Wood/leaf backend"
                  value={`${bundle.result.metadata.wood_leaf_backend} · default baseline`}
                />
                <EvidenceFact label="PointNet++" value="Experimental · not promoted" />
                <EvidenceFact label="Species classification" value="Stub" />
                <EvidenceFact
                  label="Analyzed commit"
                  value={bundle.manifest.analyzed_commit.slice(0, 12)}
                  mono
                />
              </div>

              <p className="mt-8 rounded-2xl bg-slate-100 p-4 text-sm leading-6 text-slate-700">
                CO₂e is a biomass-based estimate, not a certified or tradable carbon credit. This
                deterministic fixture demonstrates reproducibility; it is not an accuracy or credit
                validation dataset.
              </p>
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function EvidenceMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-emerald-950 p-5 text-white">
      <p className="text-xs uppercase tracking-[0.12em] text-emerald-200">{label}</p>
      <p className="mt-3 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function EvidenceFact({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 rounded-xl border border-slate-200 px-4 py-3">
      <span className="text-slate-500">{label}</span>
      <span className={`text-right font-semibold ${mono ? 'font-mono text-xs' : ''}`}>{value}</span>
    </div>
  );
}
