'use client';

import React, { useCallback, useEffect, useReducer, useRef, useState } from 'react';

import { createDemoApiClient, DemoApiError } from '../../lib/demo-api';
import { demoModeReducer, type DemoModeState } from '../../lib/demo-mode';
import { consumeRuntimeHandoff } from '../../lib/demo-runtime';
import { uploadReducer, type UploadState } from '../../lib/demo-upload';
import { loadFrozenDemo, type FrozenDemoBundle } from '../../lib/frozen-demo';
import { toResultViewModel, type ResultViewModel } from '../../lib/result-view-model';
import { ModeBadge } from './mode-badge';
import { ProvenancePanel } from './provenance-panel';
import { TreeResultTable } from './tree-result-table';
import { UploadPanel } from './upload-panel';

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

/**
 * Turns a failed analysis into something a judge can act on. The API's own
 * details are English and deliberately vague about internals, so each status is
 * mapped to the one thing the person at the keyboard can do about it.
 */
export function uploadErrorMessageTh(error: unknown): string {
  const status = error instanceof DemoApiError ? error.status : 0;
  if (status === 413) return 'ไฟล์ใหญ่หรือมีจุดมากเกินกว่าที่เซิร์ฟเวอร์เดโมรับได้';
  if (status === 400) return 'เซิร์ฟเวอร์ปฏิเสธไฟล์นี้ — ตรวจว่าเป็น .ply ที่ header ถูกต้อง';
  if (status === 401) return 'โทเคนของรอบสาธิตหมดอายุแล้ว ต้องเปิดลิงก์จาก launcher ใหม่';
  if (status === 429) return 'ส่งคำขอถี่เกินไป รอสักครู่แล้วลองใหม่';
  if (status >= 500) return 'ประมวลผลไม่สำเร็จที่ฝั่งเซิร์ฟเวอร์';
  return 'ติดต่อบริการวิเคราะห์ไม่ได้';
}

export function DemoShellController() {
  const [mode, dispatch] = useReducer(demoModeReducer, initialMode);
  const [frozenLoad, setFrozenLoad] = useState<FrozenDemoLoadState>({ kind: 'loading' });
  const [upload, dispatchUpload] = useReducer(uploadReducer, { kind: 'idle' } as UploadState);

  // The reducer holds only a name and a size, so the File itself lives here.
  const pickedFile = useRef<File | null>(null);
  // A run id, because the reducer alone cannot tell a late reply from the
  // current one once a second run has started: both arrive while in flight.
  const runId = useRef(0);

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

  const handleSelect = useCallback((file: File) => {
    pickedFile.current = file;
    dispatchUpload({ type: 'SELECT', name: file.name, sizeBytes: file.size });
  }, []);

  const handleStart = useCallback(() => {
    const file = pickedFile.current;
    if (!file) return;
    if (mode.kind !== 'production-live' && mode.kind !== 'local-live') return;

    runId.current += 1;
    const thisRun = runId.current;
    const isCurrent = () => runId.current === thisRun;

    dispatchUpload({ type: 'START' });
    createDemoApiClient(mode.credentials)
      .analyze(file, (phase) => {
        if (isCurrent()) dispatchUpload({ type: 'PHASE', phase });
      })
      .then((result) => {
        if (isCurrent()) dispatchUpload({ type: 'SUCCEEDED', result });
      })
      .catch((error: unknown) => {
        if (isCurrent()) dispatchUpload({ type: 'FAILED', messageTh: uploadErrorMessageTh(error) });
      });
  }, [mode]);

  const handleReset = useCallback(() => {
    runId.current += 1;
    pickedFile.current = null;
    dispatchUpload({ type: 'RESET' });
  }, []);

  return (
    <DemoShell
      mode={mode}
      frozenLoad={frozenLoad}
      upload={upload}
      onUseFrozen={() => dispatch({ type: 'USE_FROZEN' })}
      onSelectFile={handleSelect}
      onStartAnalysis={handleStart}
      onResetUpload={handleReset}
    />
  );
}

export function DemoShell({
  mode,
  frozenLoad,
  upload = { kind: 'idle' },
  onUseFrozen,
  onSelectFile = () => undefined,
  onStartAnalysis = () => undefined,
  onResetUpload = () => undefined,
}: {
  mode: DemoModeState;
  frozenLoad: FrozenDemoLoadState;
  upload?: UploadState;
  onUseFrozen: () => void;
  onSelectFile?: (file: File) => void;
  onStartAnalysis?: () => void;
  onResetUpload?: () => void;
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
      <main className="min-h-screen bg-[#f5f2e9] px-6 py-12 text-slate-950">
        <div className="mx-auto max-w-5xl">
          <header className="mb-8">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-emerald-800">
              TreeQ Carbon Platform · Judge Demo
            </p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
              รันจริงบน pipeline {mode.pipelineVersion}
            </h1>
            <div className="mt-4">
              <ModeBadge state={mode} />
            </div>
          </header>

          <UploadPanel
            state={upload}
            onSelect={onSelectFile}
            onStart={onStartAnalysis}
            onReset={onResetUpload}
          />

          {upload.kind === 'complete' && (
            <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <ResultSummary view={toResultViewModel(upload.result)} />

              {/* A live run has no manifest to check, so it gets no provenance
                  panel. Saying that plainly is the point: the frozen route is
                  the one whose bytes were verified, and a judge should be able
                  to tell which of the two they are looking at. */}
              <p className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                ผลนี้มาจากการรันสดกับไฟล์ที่เพิ่งอัปโหลด จึง{' '}
                <strong className="font-semibold">ไม่มี manifest ให้ตรวจแฮช</strong> เหมือนชุด
                Frozen Evidence — และเป็นค่าประมาณชีวมวล ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง
              </p>
            </section>
          )}

          <button
            type="button"
            className="mt-6 rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-white"
            onClick={onUseFrozen}
          >
            ดูชุดหลักฐานที่ตรวจแฮชแล้ว
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
              <ResultSummary view={toResultViewModel(frozenLoad.bundle.result)} />

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

/**
 * One renderer for both routes. A live run and the frozen fixture reach it
 * through the same `toResultViewModel`, so the live path cannot drift into
 * showing a number the evidence route refuses to show - which is precisely what
 * a second, "just for live" summary block would have allowed.
 */
function ResultSummary({ view }: { view: ResultViewModel }) {
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
                  <span className="font-mono text-xs text-slate-500">#{row.treeId}</span>
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
}

function EvidenceMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-emerald-950 p-5 text-white">
      <p className="text-xs uppercase tracking-[0.12em] text-emerald-200">{label}</p>
      <p className="mt-3 text-2xl font-semibold">{value}</p>
    </div>
  );
}

