'use client';

import React, { useEffect, useReducer, useState } from 'react';

import { createDemoApiClient } from '../../lib/demo-api';
import { demoModeReducer, type DemoModeState } from '../../lib/demo-mode';
import { consumeRuntimeHandoff } from '../../lib/demo-runtime';
import { loadFrozenDemo, type FrozenDemoBundle } from '../../lib/frozen-demo';
import { toResultViewModel } from '../../lib/result-view-model';
import { ModeBadge } from './mode-badge';
import { ProvenancePanel } from './provenance-panel';
import { TreeResultTable } from './tree-result-table';

const initialMode: DemoModeState = { kind: 'booting' };
const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });

export type FrozenDemoLoadState =
  | { kind: 'loading' }
  | { kind: 'ready'; bundle: FrozenDemoBundle }
  | { kind: 'failed' };

export type FrozenDemoLoader = () => Promise<FrozenDemoBundle>;

export async function resolveFrozenDemoLoad(
  loader: FrozenDemoLoader = loadFrozenDemo,
): Promise<FrozenDemoLoadState> {
  try {
    return { kind: 'ready', bundle: await loader() };
  } catch {
    return { kind: 'failed' };
  }
}

export function DemoShellController() {
  const [mode, dispatch] = useReducer(demoModeReducer, initialMode);
  const [frozenLoad, setFrozenLoad] = useState<FrozenDemoLoadState>({ kind: 'loading' });

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
    setFrozenLoad({ kind: 'loading' });
    resolveFrozenDemoLoad().then((nextLoad) => {
      if (!cancelled) setFrozenLoad(nextLoad);
    });
    return () => {
      cancelled = true;
    };
  }, [mode]);

  return (
    <DemoShell
      mode={mode}
      frozenLoad={frozenLoad}
      onUseFrozen={() => dispatch({ type: 'USE_FROZEN' })}
    />
  );
}

export function DemoShell({
  mode,
  frozenLoad,
  onUseFrozen,
}: {
  mode: DemoModeState;
  frozenLoad: FrozenDemoLoadState;
  onUseFrozen: () => void;
}) {
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
            onClick={onUseFrozen}
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

          {frozenLoad.kind === 'failed' ? (
            <p className="mt-8 font-mono text-sm font-semibold text-red-800">loading failed</p>
          ) : frozenLoad.kind === 'loading' ? (
            <p className="mt-8 text-sm text-slate-600">Verifying every evidence byte…</p>
          ) : (
            <>
              {(() => {
                const view = toResultViewModel(frozenLoad.bundle.result);
                return (
                  <>
                    <div className="mt-8 grid gap-4 sm:grid-cols-3">
                      <EvidenceMetric
                        label={view.countsLabel.measured}
                        value={number.format(view.counts.measured)}
                      />
                      <EvidenceMetric
                        label="Carbon stock estimate"
                        value={`${number.format(view.totalCarbonKg)} kg C`}
                      />
                      <EvidenceMetric
                        label="CO₂e estimate"
                        value={`${number.format(view.totalCo2eqKg)} kg CO₂e`}
                      />
                    </div>

                    {view.diagnosticsStatus === 'available' ? (
                      <div className="mt-4 rounded-2xl border border-slate-200 p-4 text-sm">
                        <p className="text-slate-700">
                          {view.countsLabel.detected} {number.format(view.counts.detected ?? 0)} ·{' '}
                          {view.countsLabel.measured} {number.format(view.counts.measured)} ·{' '}
                          {view.countsLabel.excluded} {number.format(view.counts.excluded ?? 0)}
                        </p>
                        {view.excludedRows.length > 0 && (
                          <ul className="mt-3 space-y-1 text-slate-600">
                            {view.excludedRows.map((row) => (
                              <li key={row.treeId} className="flex gap-2">
                                <span className="font-mono text-xs text-slate-500">
                                  #{row.treeId}
                                </span>
                                <span>{row.reasonTh}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ) : (
                      <p className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                        ไม่มี diagnostics จาก run นี้ — จำนวนที่ตรวจพบและที่ไม่รวมผลจึงแสดงไม่ได้
                      </p>
                    )}

                    <div className="mt-8 border-t border-slate-200 pt-6">
                      <h2 className="text-base font-semibold text-slate-900">ผลรายต้น</h2>
                      <div className="mt-4">
                        <TreeResultTable view={view} />
                      </div>
                    </div>
                  </>
                );
              })()}

              <div className="mt-8 border-t border-slate-200 pt-6">
                <ProvenancePanel manifest={frozenLoad.bundle.manifest} />
              </div>
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

