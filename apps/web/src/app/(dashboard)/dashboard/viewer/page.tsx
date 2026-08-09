'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  analyzePointCloud,
  fetchSpecies,
  type SpeciesOption,
  ApiError,
  fetchSegmentedCloud,
  isApiConfigured,
  type AnalyzeResponse,
} from '@/lib/api';
import { consumeRuntimeHandoff } from '@/lib/demo-runtime';
import {
  headerMismatchNote,
  rejectCloudAfterParsing,
  rejectFileBeforeReading,
} from '@/lib/upload-limits';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ResultRail } from '@/components/demo/result-rail';
import { ViewerAnalysisBadge } from '@/components/demo/mode-badge';
import { TreeResultTable } from '@/components/demo/tree-result-table';
import { CompactWorkspaceHeader } from '@/components/layout/compact-workspace-header';
import { ScrollToTop } from '@/components/layout/scroll-to-top';
import { ViewerStage } from '@/components/viewer/viewer-stage';
import { CORE_DEMO_EVIDENCE } from '@/generated/core-demo-evidence';
import { generateDemoTree, type PointCloud } from '@/lib/demo-pointcloud';
import { formatBackendLabel, formatEvidenceStatus } from '@/lib/evidence';
import { decimate, parsePly } from '@/lib/ply-loader';
import { toResultViewModel } from '@/lib/result-view-model';

const MAX_POINTS = 200_000;

export default function ViewerPage() {
  const demoTree = useMemo(() => generateDemoTree({ seed: 42 }), []);

  const [loaded, setLoaded] = useState<PointCloud | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [headerNote, setHeaderNote] = useState<string | null>(null);
  // Naming the species replaces an assumed wood density with a measured one.
  // Against the 65 destructively weighed reference trees that assumption is
  // about half the carbon error, so this is the cheapest accuracy the product
  // has: one field. The pipeline has accepted a species since it was written;
  // nothing had ever offered the user a way to give one.
  const [species, setSpecies] = useState<string | null>(null);
  const [speciesOptions, setSpeciesOptions] = useState<SpeciesOption[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  // The classified cloud the pipeline returned. Separate from `loaded` on
  // purpose: `loaded` is what the browser parsed from the user's file, this is
  // what the backend measured. Null means we never got one, and the page has to
  // keep saying the picture is the upload rather than the result.
  const [analysedCloud, setAnalysedCloud] = useState<PointCloud | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  // Whether a backend is reachable is a browser fact, not a build fact, so it
  // cannot be read during render without the server and the client disagreeing
  // on the first paint. Start from what the build knows and correct it here.
  const [apiReady, setApiReady] = useState(false);
  useEffect(() => {
    // Accept a handoff addressed to this page as well as one already stored by
    // /demo, so the launcher link works wherever the visitor lands first.
    consumeRuntimeHandoff({
      location: window.location,
      history: window.history,
      storage: window.sessionStorage,
    });
    setApiReady(isApiConfigured());
  }, []);

  // Precedence is deliberate: the pipeline's own output beats the browser's
  // parse of the same file, which beats the sample tree.
  const cloud = analysedCloud ?? loaded ?? demoTree;
  const nPoints = cloud.classes.length;
  const resultView = useMemo(
    () => (analysis === null ? null : toResultViewModel(analysis)),
    [analysis],
  );

  const loadFile = useCallback(async (f: File) => {
    // Checked before the file is read. The size is known from the picker, so
    // an over-limit scan never has to be pulled into memory to be refused —
    // which is what used to happen, followed by an upload and a 413.
    const refusal = rejectFileBeforeReading(f);
    if (refusal) {
      setError(refusal.reason);
      return;
    }
    setIsLoading(true);
    setError(null);
    setAnalysis(null);
    setAnalyzeError(null);
    setAnalysedCloud(null);
    setHeaderNote(null);
    try {
      const buffer = await f.arrayBuffer();
      const cloud = parsePly(buffer);
      const trueCount = cloud.classes.length;
      const tooMany = rejectCloudAfterParsing(trueCount, cloud.declaredCount);
      if (tooMany) {
        setError(tooMany.reason);
        return;
      }
      const parsed = decimate(cloud, MAX_POINTS);
      setLoaded(parsed);
      setHeaderNote(headerMismatchNote(trueCount, cloud.declaredCount));
      setFile(f);
      setFileName(f.name);
    } catch (err) {
      setError(`อ่านไฟล์ไม่สำเร็จ: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const f = e.dataTransfer.files?.[0];
      if (f) void loadFile(f);
    },
    [loadFile],
  );

  const resetToDemo = useCallback(() => {
    setLoaded(null);
    setFile(null);
    setFileName(null);
    setError(null);
    setAnalysis(null);
    setAnalyzeError(null);
    setAnalysedCloud(null);
    if (inputRef.current) inputRef.current.value = '';
  }, []);

  useEffect(() => {
    // Best effort. A backend that cannot list species still measures trees, and
    // the picker simply does not appear.
    let cancelled = false;
    void fetchSpecies()
      .then((data) => {
        if (!cancelled) setSpeciesOptions(data.species);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const runAnalysis = useCallback(async () => {
    if (!file) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const result = await analyzePointCloud(file, species);
      setAnalysis(result);

      // Swap the picture for the pipeline's own classification. Failing to get
      // it is not a failed analysis - the numbers are already in hand - so this
      // never overwrites the result or raises. The viewer notices the missing
      // cloud and keeps describing what it is actually showing.
      if (result.segmented_cloud_id) {
        try {
          const buffer = await fetchSegmentedCloud(result.segmented_cloud_id);
          const parsed = decimate(parsePly(buffer), MAX_POINTS);
          if (parsed.classes.length > 0) setAnalysedCloud(parsed);
        } catch {
          setAnalysedCloud(null);
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = `(${err.status}) ${(err.body as { detail?: string })?.detail ?? err.statusText}`;
        setAnalyzeError(`วิเคราะห์ไม่สำเร็จ: ${detail}`);
      } else {
        // Network error — backend unreachable (no API deployed / URL down).
        // Show a friendly note instead of a raw "Failed to fetch".
        setAnalyzeError(
          // The old wording said this works "during the live presentation".
          // That competition is over, and a visitor reading it has no idea what
          // presentation is meant. Say what is true instead: the server that
          // does the computing is not running right now.
          'ยังเชื่อมต่อเซิร์ฟเวอร์ประมวลผลไม่ได้ในตอนนี้ — การแสดงผล 3 มิติยังใช้งานได้ตามปกติ ส่วนการคำนวณคาร์บอนต้องรอให้เซิร์ฟเวอร์กลับมา',
        );
      }
    } finally {
      setAnalyzing(false);
    }
  }, [file, species]);

  return (
    <>
      <CompactWorkspaceHeader
        title="ตรวจสอบแบบจำลอง 3 มิติ"
        mode={
          loaded === null
            ? 'ตัวอย่างจำลอง'
            : analysis === null
              ? 'ไฟล์ที่คุณเปิด ยังไม่ได้วิเคราะห์'
              : 'วิเคราะห์สดแล้ว'
        }
        backHref="/dashboard"
      />

      <main className="bg-gallery-ivory px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-7xl">
          <Card>
            <CardHeader>
              <CardTitle>
                {loaded ? `ไฟล์: ${fileName}` : 'เลือก point cloud สำหรับตรวจสอบ'}
              </CardTitle>
              <CardDescription>
                รองรับไฟล์ <code>.ply</code> และแสดงผลได้สูงสุด {MAX_POINTS.toLocaleString()} จุด
                {/* Without this link the page is a dead end for anyone who does
                    not already own a laser scanner, which is nearly everyone.
                    The file was already deployed and reachable - it just had no
                    link from anywhere on the site. */}
                <br />
                ยังไม่มีไฟล์?{' '}
                <a
                  href="/demo/input.ply"
                  download="ตัวอย่างแปลงป่า.ply"
                  className="focus-ring rounded font-medium text-primary underline underline-offset-2"
                >
                  ดาวน์โหลดแปลงตัวอย่าง (1.7 MB)
                </a>{' '}
                แล้วลากกลับเข้ามาที่นี่
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={onDrop}
                className={`flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-5 text-center transition-colors ${
                  isDragging ? 'bg-lichen/40 border-moss' : 'border-hairline bg-paper'
                }`}
              >
                <p className="text-sm text-canopy">
                  {isLoading ? 'กำลังอ่านไฟล์…' : 'ลากไฟล์ .ply มาวางที่นี่ หรือ'}
                </p>
                {/* The pipeline runs watershed segmentation over a canopy height
                    model (services/ml/pipeline/main.py:156) — it looks for
                    ground, then separates trees. Handed a single isolated tree
                    it finds one basin covering everything and reports a DBH
                    several times too large, with nothing on screen to say so.
                    Saying which input it wants is the cheapest guard there is. */}
                <p className="max-w-md text-xs leading-relaxed text-canopy/80">
                  ระบบนี้รับ<strong className="font-semibold text-forest-ink">แปลงป่าที่มีหลายต้น</strong>{' '}
                  ไม่ใช่ต้นไม้ต้นเดียว — ถ้าใส่ไฟล์ต้นเดียวเข้ามา
                  ค่าที่วัดได้จะผิดไปหลายเท่าโดยไม่มีอะไรเตือน
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => inputRef.current?.click()}
                    disabled={isLoading}
                  >
                    เลือกไฟล์ .ply
                  </Button>
                  {loaded ? (
                    <Button type="button" variant="outline" onClick={resetToDemo}>
                      กลับไปตัวอย่างจำลอง
                    </Button>
                  ) : null}
                </div>
                <input
                  ref={inputRef}
                  type="file"
                  accept=".ply"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void loadFile(f);
                  }}
                />
              </div>

              {error ? (
                <p className="mt-3 text-sm text-destructive" role="alert">
                  {error}
                </p>
              ) : null}

              {/* Not an error — the file is usable. But a point total is a
                  number somebody may write down, and when the header and the
                  body disagree they deserve to know which one they are
                  looking at. */}
              {headerNote ? (
                <p className="mt-3 text-sm text-forest-ink/70" role="status">
                  {headerNote}
                </p>
              ) : null}
            </CardContent>
          </Card>

          <div className={`mt-6 grid gap-6 ${resultView ? 'lg:grid-cols-12' : ''}`}>
            <div className={resultView ? 'lg:col-span-8' : ''}>
              <ViewerStage
                title={loaded === null ? 'ต้นไม้ตัวอย่างจำลอง' : (fileName ?? 'ไฟล์ที่อัปโหลด')}
                /* The designer asked for this line in Thai and shorter, and for
                   the SYNTHETIC pill beside it to go. What it may not lose is
                   what it is for: a judge must never take the sample tree for
                   pipeline output. So the disclosure moves into the Thai line
                   and the pill, which only repeated it, is now the point
                   count. */
                evidenceLabel={
                  loaded === null
                    ? 'ตัวอย่างการจำลอง · ไม่ใช่ผลจาก pipeline'
                    : analysedCloud !== null
                      ? 'ผลการแยกจาก pipeline · ชุดเดียวกับที่ใช้คำนวณ'
                      : analysis === null
                        ? cloud.labelled
                          ? 'ไฟล์จากเครื่องคุณ · ยังไม่ได้วิเคราะห์'
                          : 'ไฟล์จากเครื่องคุณ · ยังไม่ได้แยกลำต้น/ใบ'
                        : 'วิเคราะห์แล้ว · ภาพนี้คือไฟล์ต้นฉบับ ไม่ใช่ผลที่ระบายสี'
                }
                positions={cloud.positions}
                classes={cloud.classes}
                labelled={cloud.labelled}
                analysed={analysis !== null}
              >
                <ViewerAnalysisBadge
                  analysis={analysis}
                  fallback={
                    <span className="editorial-eyebrow-th rounded-full border border-moss px-3 py-1.5 text-lichen">
                      {nPoints.toLocaleString()} จุด
                    </span>
                  }
                />
              </ViewerStage>
            </div>

            {resultView ? (
              <div className="lg:col-span-4">
                <ResultRail view={resultView} modeLabel="Live analysis" integrity="live-run" />
              </div>
            ) : null}
          </div>

          {loaded ? (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>ผลประมาณการคาร์บอน (ML pipeline)</CardTitle>
                <CardDescription>
                  ส่งไฟล์นี้เข้า backend → รัน pipeline (ground → tree → wood/leaf → QSM →
                  allometric) → คืนค่าประมาณการคาร์บอนพร้อม provenance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {apiReady ? (
                  <>
                    {/* One field, and it is the largest accuracy gain the
                        product has. Wood density is otherwise assumed, and
                        against the 65 destructively weighed reference trees
                        that assumption is about half the carbon error. Left
                        optional because not knowing is legitimate — the result
                        then says the density was assumed. */}
                    {speciesOptions.length > 0 ? (
                      <div className="space-y-1.5">
                        <label
                          htmlFor="species-select"
                          className="block text-sm font-medium"
                        >
                          ชนิดไม้ (ถ้าทราบ)
                        </label>
                        <select
                          id="species-select"
                          value={species ?? ''}
                          onChange={(e) => setSpecies(e.target.value || null)}
                          disabled={analyzing}
                          className="w-full max-w-sm rounded-lg border border-hairline bg-paper px-3 py-2 text-sm"
                        >
                          <option value="">ไม่ทราบ — ใช้ความหนาแน่นมาตรฐาน</option>
                          {speciesOptions.map((option) => (
                            <option key={option.name_sci} value={option.name_sci}>
                              {option.name_th} ({option.name_sci}) ·{' '}
                              {option.wood_density_kg_m3} kg/m³
                            </option>
                          ))}
                        </select>
                        <p className="text-xs text-forest-ink/70">
                          ระบุชนิดไม้ช่วยลดความคลาดเคลื่อนของคาร์บอนได้ราวครึ่งหนึ่ง
                          เพราะได้ความหนาแน่นไม้จริงแทนค่าสมมติ
                        </p>
                      </div>
                    ) : null}

                    <Button type="button" onClick={runAnalysis} disabled={analyzing}>
                      {analyzing ? 'กำลังวิเคราะห์… (อาจใช้เวลาสักครู่)' : 'วิเคราะห์คาร์บอน'}
                    </Button>

                    {analyzeError ? (
                      <p className="text-sm text-destructive" role="alert">
                        {analyzeError}
                      </p>
                    ) : null}
                  </>
                ) : (
                  <div className="rounded-lg border border-dashed border-hairline bg-paper p-4">
                    <p className="text-sm font-medium text-forest-ink">
                      การวิเคราะห์คาร์บอนทำงานผ่าน backend (ML pipeline จริง)
                    </p>
                    <p className="mt-1 text-sm text-canopy">
                      เวอร์ชันสาธิตออนไลน์นี้แสดงเฉพาะการแยก 3 มิติ (ลำต้น / ใบ / พื้นดิน) —
                      การคำนวณคาร์บอนสาธิตสดผ่าน API ในการนำเสนอ Reviewed core demo แบบ synthetic
                      ที่ใช้ตรวจ reproducibility พบ {CORE_DEMO_EVIDENCE.coreDemo.totalTrees} ต้น ·
                      คาร์บอน {CORE_DEMO_EVIDENCE.coreDemo.totalCarbonKg} กก. · CO₂e{' '}
                      {CORE_DEMO_EVIDENCE.coreDemo.totalCo2eqKg} กก. ตัวเลขนี้ไม่ใช่ accuracy
                      benchmark หรือ carbon-credit certification
                    </p>
                  </div>
                )}

                {analysis && resultView ? (
                  <div className="space-y-5">
                    <div className="rounded-xl border border-hairline bg-paper p-5">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-deep-forest px-2.5 py-1 text-xs font-semibold text-paper">
                          {formatBackendLabel(analysis.metadata)}
                        </span>
                        <span className="text-sm text-canopy">
                          {formatEvidenceStatus(analysis.metadata)}
                        </span>
                      </div>
                      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                        <div>
                          <dt className="text-canopy">{resultView.countsLabel.measured}</dt>
                          <dd className="font-medium">
                            {resultView.counts.measured.toLocaleString()} ต้น
                          </dd>
                        </div>
                        <div>
                          <dt className="text-canopy">Pipeline / Git</dt>
                          <dd className="font-mono text-xs">
                            v{analysis.metadata.pipeline_version} ·{' '}
                            {analysis.metadata.git_commit.slice(0, 12)}
                            {analysis.metadata.git_dirty ? ' · dirty' : ' · clean'}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-canopy">Normalized XYZ input SHA-256</dt>
                          <dd className="font-mono text-xs">
                            {analysis.metadata.input_sha256.slice(0, 12)}…
                          </dd>
                        </div>
                        <div>
                          <dt className="text-canopy">Checkpoint</dt>
                          <dd className="font-mono text-xs">
                            {analysis.metadata.checkpoint_sha256
                              ? `${analysis.metadata.checkpoint_sha256.slice(0, 12)}…`
                              : 'ไม่มี checkpoint (tlsep baseline)'}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-canopy">Species algorithm</dt>
                          <dd className="font-medium">
                            {analysis.metadata.algorithms.species === 'stub'
                              ? 'Stub — ยังไม่มีโมเดลจำแนกชนิดไม้'
                              : analysis.metadata.algorithms.species}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-canopy">QSM artifact</dt>
                          <dd className="font-mono text-xs">QSM artifact unavailable</dd>
                        </div>
                      </dl>
                      <p className="mt-4 text-xs leading-relaxed text-canopy">
                        Provenance นี้ผูกกับ input ที่ส่งเข้า analysis backend ส่วนภาพ 3D
                        ด้านบนอ่านจากไฟล์ที่อัปโหลดในเบราว์เซอร์ และยังไม่ได้ตรวจว่า hash
                        ตรงกันด้วยขั้นตอน normalized XYZ เดียวกัน
                      </p>
                    </div>

                    <section className="rounded-xl border border-hairline bg-paper p-5">
                      <h2 className="font-display text-xl font-semibold text-forest-ink">
                        ผลการวัดรายต้น
                      </h2>
                      <div className="mt-3">
                        <TreeResultTable view={resultView} />
                      </div>
                    </section>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ) : null}
        </div>
      </main>
      <ScrollToTop />
    </>
  );
}