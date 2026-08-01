'use client';

import React, { useCallback, useEffect, useReducer, useRef, useState } from 'react';

import { createDemoApiClient, DemoApiError } from '../../lib/demo-api';
import { demoModeReducer, type DemoModeState } from '../../lib/demo-mode';
import { consumeRuntimeHandoff } from '../../lib/demo-runtime';
import { uploadReducer, type UploadState } from '../../lib/demo-upload';
import { loadFrozenDemo, type FrozenDemoBundle } from '../../lib/frozen-demo';
import { toResultViewModel, type ResultViewModel } from '../../lib/result-view-model';
import { Button } from '../ui/button';
import { JudgeDemoHeader } from './judge-demo-header';
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
    return <main className="min-h-screen bg-gallery-ivory" aria-busy="true" />;
  }

  if (mode.kind === 'checking') {
    return (
      <main className="min-h-screen bg-gallery-ivory px-4 py-5 text-forest-ink sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <JudgeDemoHeader state={mode} />
          <section
            className="mt-6 rounded-[1.25rem] border border-hairline bg-paper p-8 text-center"
            aria-busy="true"
          >
            <p className="editorial-eyebrow">Pre-flight / runtime</p>
            <h2 className="mt-3 font-display text-2xl">กำลังตรวจ readiness ของ runtime</h2>
            <p className="mt-3 text-sm text-canopy">
              ถ้าติดต่อไม่ได้ ระบบจะกลับสู่ Frozen Evidence โดยอัตโนมัติ
            </p>
          </section>
        </div>
      </main>
    );
  }

  if (mode.kind === 'production-live' || mode.kind === 'local-live') {
    return (
      <main className="min-h-screen bg-gallery-ivory px-4 py-5 text-forest-ink sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <JudgeDemoHeader state={mode} />

          <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(18rem,0.95fr)]">
            <div className="space-y-5">
              <ModeChoice mode={mode} onUseFrozen={onUseFrozen} />
              <UploadPanel
                state={upload}
                onSelect={onSelectFile}
                onStart={onStartAnalysis}
                onReset={onResetUpload}
              />
            </div>
            <ReliabilityPanel mode={mode} frozenLoad={frozenLoad} />
          </div>

          {upload.kind === 'complete' && (
            <section className="mt-6 rounded-[1.25rem] border border-hairline bg-paper p-5 sm:p-8">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="editorial-eyebrow">Result / live runtime</p>
                  <h2 className="mt-2 font-display text-3xl">ผลจากไฟล์ {upload.file.name}</h2>
                </div>
                <p className="font-mono text-[0.6875rem] uppercase tracking-[0.12em] text-canopy">
                  pipeline {mode.pipelineVersion}
                </p>
              </div>
              <ResultSummary view={toResultViewModel(upload.result)} />

              {/* A live run has no manifest to check, so it gets no provenance
                  panel. Saying that plainly is the point: the frozen route is
                  the one whose bytes were verified, and a judge should be able
                  to tell which of the two they are looking at. */}
              <p className="mt-8 rounded-2xl border border-hairline bg-gallery-ivory p-4 text-sm leading-6 text-canopy">
                ผลนี้มาจากการรันสดกับไฟล์ที่เพิ่งอัปโหลด จึง{' '}
                <strong className="font-semibold">ไม่มี manifest ให้ตรวจแฮช</strong> เหมือนชุด
                Frozen Evidence — และเป็นค่าประมาณชีวมวล ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง
              </p>
            </section>
          )}
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gallery-ivory px-4 py-5 text-forest-ink sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <JudgeDemoHeader state={mode} />

        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(18rem,0.95fr)]">
          <ModeChoice mode={mode} onUseFrozen={onUseFrozen} />
          <ReliabilityPanel mode={mode} frozenLoad={frozenLoad} />
        </div>

        {frozenLoad.kind === 'failed' ? (
          <section className="mt-6 rounded-[1.25rem] border border-clay bg-paper p-6 sm:p-8">
            <p className="editorial-eyebrow text-clay">Artifact verification</p>
            {/* The outcome replaces "Verifying every evidence byte…" after the
                page has already settled, so without a live region a screen
                reader is left on the pending message and never learns that the
                evidence failed its hash check. Scoped to this line rather than
                the section, so the announcement is the verdict and not the
                whole panel. */}
            <p className="mt-3 font-mono text-sm font-semibold text-clay" role="status">
              loading failed
            </p>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-canopy">
              ระบบปิดผลลัพธ์ไว้ เพราะยืนยัน bytes ของหลักฐาน frozen ไม่สำเร็จ
            </p>
          </section>
        ) : frozenLoad.kind === 'loading' ? (
          <section
            className="mt-6 rounded-[1.25rem] border border-hairline bg-paper p-6 sm:p-8"
            aria-busy="true"
          >
            <p className="editorial-eyebrow">Validate / artifact</p>
            <p className="mt-3 text-sm text-canopy">Verifying every evidence byte…</p>
          </section>
        ) : (
          <section className="mt-6 rounded-[1.25rem] border border-hairline bg-paper p-5 sm:p-8">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="editorial-eyebrow">Result / verified frozen artifact</p>
                <h2 className="mt-2 font-display text-3xl">ผลการวัดที่ตรวจ checksum แล้ว</h2>
              </div>
              <ModeBadge state={mode} />
            </div>
            <ResultSummary view={toResultViewModel(frozenLoad.bundle.result)} />

            <div className="mt-8 border-t border-hairline pt-6">
              <ProvenancePanel manifest={frozenLoad.bundle.manifest} />
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

function ModeChoice({
  mode,
  onUseFrozen,
}: {
  mode: Exclude<DemoModeState, { kind: 'booting' | 'checking' }>;
  onUseFrozen: () => void;
}) {
  const isLive = mode.kind === 'production-live' || mode.kind === 'local-live';

  return (
    <section className="rounded-[1.25rem] border border-hairline bg-paper p-5 sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="editorial-eyebrow">Input mode</p>
          <h2 className="mt-2 font-display text-2xl text-forest-ink">เลือกวิธีเริ่มวิเคราะห์</h2>
        </div>

        {/* A current-state readout plus the one action that exists - not a tab
            set. Live mode can only be entered by a runtime handoff, so a tablist
            or a pair of pressed toggles would advertise a control the page does
            not have. The previous markup put `aria-current="page"` on a span,
            which claimed "page" about something that is not a page and still
            left assistive tech no way to tell that the other label was the
            alternative; the active mode is now announced as text instead. */}
        <div className="flex items-center gap-2 rounded-full bg-gallery-ivory p-1">
          {isLive ? (
            <>
              <Button
                type="button"
                variant="editorial"
                size="xl"
                onClick={onUseFrozen}
                aria-label="สลับไปใช้ Frozen Sample"
              >
                Frozen Sample
              </Button>
              <p className="rounded-full px-5 py-3 text-sm font-medium text-canopy">
                <span className="sr-only">โหมดปัจจุบัน: </span>
                Live Upload
              </p>
            </>
          ) : (
            <p className="rounded-full bg-canopy px-5 py-3 text-sm font-medium text-paper">
              <span className="sr-only">โหมดปัจจุบัน: </span>
              Frozen Sample
            </p>
          )}
        </div>
      </div>

      {isLive ? (
        <div className="bg-lichen/35 mt-5 rounded-xl border border-lichen p-4">
          <p className="font-mono text-[0.625rem] uppercase tracking-[0.12em] text-moss">
            pipeline {mode.pipelineVersion}
          </p>
          <p className="mt-2 text-sm leading-6 text-canopy">
            Runtime ผ่าน readiness แล้ว จึงเปิด Live Upload; Frozen Sample ยังเป็นเส้นทางหลักที่ตรวจ
            checksum ได้
          </p>
        </div>
      ) : (
        <div className="mt-5 grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
          <div className="rounded-xl border border-moss bg-gallery-ivory p-5">
            <p className="editorial-eyebrow-th text-moss">แนะนำ ไม่ต้องพึ่งเครือข่าย</p>
            <h3 className="mt-3 font-display text-xl">ชุดตัวอย่างที่ตรวจแล้ว</h3>
            <p className="mt-2 text-sm leading-6 text-canopy">
              แสดงผลจากชุดทดสอบที่ยืนยันแล้ว เบราว์เซอร์จะตรวจสอบค่าแฮชทุกครั้ง
              หากข้อมูลไม่ตรงกันระบบจะไม่แสดงผลลัพธ์
            </p>
          </div>
          <p className="max-w-xs text-sm leading-6 text-canopy">{frozenReason(mode.reason)}</p>
        </div>
      )}
    </section>
  );
}

function frozenReason(reason: Extract<DemoModeState, { kind: 'frozen' }>['reason']): string {
  if (reason === 'invalid-handoff') {
    return 'Live Upload ไม่เปิด เพราะ runtime handoff ไม่ถูกต้อง; Frozen Evidence ยังใช้งานได้';
  }
  if (reason === 'unreachable') {
    return 'Live Upload ไม่เปิด เพราะ API readiness ไม่ผ่าน; ระบบ fallback มาที่ Frozen Evidence';
  }
  if (reason === 'manual') {
    return 'กำลังดู Frozen Evidence ตามที่เลือก; การรันสดก่อนหน้านี้ไม่ถูกนำมาปะปนกับหลักฐานชุดนี้';
  }
  return 'หน้านี้เริ่มจาก Frozen Evidence; Live Upload จะเปิดเฉพาะเมื่อมี runtime ที่ผ่าน readiness';
}

function ReliabilityPanel({
  mode,
  frozenLoad,
}: {
  mode: Exclude<DemoModeState, { kind: 'booting' | 'checking' }>;
  frozenLoad: FrozenDemoLoadState;
}) {
  const isLive = mode.kind === 'production-live' || mode.kind === 'local-live';
  // In live mode the frozen bundle is never fetched - that effect is gated on the
  // frozen mode - so `loading` here does not mean a check is running, it means one
  // was never started. Reporting VERIFYING would have this panel, whose whole
  // claim is that it does not hide status, assert an action that is not happening,
  // and it would sit there for the length of the demo.
  const artifactStatus =
    frozenLoad.kind === 'ready'
      ? 'CHECKSUM VERIFIED'
      : frozenLoad.kind === 'failed'
        ? 'VERIFICATION FAILED'
        : isLive
          ? 'NOT CHECKED IN LIVE MODE'
          : 'VERIFYING';
  const rows = [
    ['WEB', 'READY'],
    ['API', isLive ? 'READINESS PASSED' : 'OPTIONAL IN FROZEN MODE'],
    ['DATASET', 'LOCKED'],
    ['ARTIFACT', artifactStatus],
    ['FALLBACK', 'AVAILABLE'],
  ] as const;

  return (
    <aside className="rounded-[1.25rem] bg-deep-forest p-6 text-paper sm:p-7">
      <p className="editorial-eyebrow-th text-lichen">ตรวจก่อนเริ่มสาธิต</p>
      <h2 className="mt-3 font-display text-2xl">สถานะความพร้อมของระบบ</h2>
      <p className="mt-3 text-sm leading-6 text-mist">
        ตรวจสอบความพร้อมการทำงานแยกส่วนระหว่าง Frontend, API และชุดข้อมูลอ้างอิง
      </p>

      <dl className="mt-6 space-y-2">
        {rows.map(([label, value]) => (
          <div
            key={label}
            className="bg-canopy/70 grid grid-cols-[6rem_1fr] gap-3 rounded-xl px-4 py-3 font-mono text-[0.625rem]"
          >
            <dt className="text-lichen">{label}</dt>
            <dd className={value === 'VERIFICATION FAILED' ? 'text-[#efad91]' : 'text-lichen'}>
              {value}
            </dd>
          </div>
        ))}
      </dl>

      {/* "ไม่ถูกแทนที่ด้วยผล live โดยอัตโนมัติ" is kept on the end of the
          supplied line. Independence from the API is half the promise; the
          other half is that a live run never silently overwrites the frozen
          evidence, which is what lets a presenter fall back mid-demo. */}
      <p className="mt-5 text-xs leading-5 text-mist">
        โหมด Frozen Evidence ทำงานโดยอิสระจาก API เพื่อรับประกันความเสถียรระหว่างการสาธิต
        และไม่ถูกแทนที่ด้วยผล live โดยอัตโนมัติ
      </p>
    </aside>
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
      <div className="mt-8 grid gap-3 sm:grid-cols-3">
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
        <div className="bg-gallery-ivory/55 mt-4 rounded-2xl border border-hairline p-4 text-sm">
          <p className="font-medium text-forest-ink">
            {view.countsLabel.detected} {number.format(view.counts.detected ?? 0)} ·{' '}
            {view.countsLabel.measured} {number.format(view.counts.measured)} ·{' '}
            {view.countsLabel.excluded} {number.format(view.counts.excluded ?? 0)}
          </p>
          {/* Three definitions on one line, each wrapped in quotation marks and
              joined by semicolons, at the designer's report that it reads as
              machine-written. It does. A definition list is what this was. */}
          <dl className="mt-2 space-y-1 leading-6 text-canopy">
            <div className="flex gap-2">
              <dt className="font-medium text-forest-ink">{view.countsLabel.detected}</dt>
              <dd>ต้นไม้ทั้งหมดที่ระบบจำแนกได้</dd>
            </div>
            <div className="flex gap-2">
              <dt className="font-medium text-forest-ink">{view.countsLabel.measured}</dt>
              <dd>ต้นที่วัดขนาดและความสูงสำเร็จ</dd>
            </div>
            <div className="flex gap-2">
              <dt className="font-medium text-forest-ink">{view.countsLabel.excluded}</dt>
              <dd>ต้นที่วัดไม่ได้ และไม่ถูกนำไปรวมยอดคาร์บอน</dd>
            </div>
          </dl>
          {view.excludedRows.length > 0 && (
            <ul className="mt-3 space-y-1 text-canopy">
              {view.excludedRows.map((row) => (
                <li key={row.treeId} className="flex gap-2">
                  <span className="font-mono text-xs text-moss">#{row.treeId}</span>
                  <span>{row.reasonTh}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <p className="mt-4 rounded-2xl border border-evidence-amber bg-gallery-ivory p-4 text-sm text-deep-forest">
          ไม่มี diagnostics จาก run นี้ — จำนวนที่ตรวจพบและที่ไม่รวมผลจึงแสดงไม่ได้
        </p>
      )}

      <div className="mt-8 border-t border-hairline pt-6">
        <h2 className="font-display text-xl text-forest-ink">ผลรายต้น</h2>
        <div className="mt-4">
          <TreeResultTable view={view} />
        </div>
      </div>
    </>
  );
}

function EvidenceMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-deep-forest p-5 text-paper">
      <p className="font-mono text-[0.625rem] uppercase tracking-[0.12em] text-lichen">{label}</p>
      <p className="mt-3 font-display text-2xl tabular-nums">{value}</p>
    </div>
  );
}
