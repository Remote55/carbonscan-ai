'use client';

import { useCallback, useMemo, useRef, useState } from 'react';

import { analyzePointCloud, ApiError, IS_API_CONFIGURED, type AnalyzeResponse } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ResultRail } from '@/components/demo/result-rail';
import { ModeBadge } from '@/components/demo/mode-badge';
import { TreeResultTable } from '@/components/demo/tree-result-table';
import { CompactWorkspaceHeader } from '@/components/layout/compact-workspace-header';
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
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const cloud = loaded ?? demoTree;
  const nPoints = cloud.classes.length;
  const resultView = useMemo(
    () => (analysis === null ? null : toResultViewModel(analysis)),
    [analysis],
  );

  const loadFile = useCallback(async (f: File) => {
    if (!f.name.toLowerCase().endsWith('.ply')) {
      setError('รองรับเฉพาะไฟล์ .ply เท่านั้น');
      return;
    }
    setIsLoading(true);
    setError(null);
    setAnalysis(null);
    setAnalyzeError(null);
    try {
      const buffer = await f.arrayBuffer();
      const parsed = decimate(parsePly(buffer), MAX_POINTS);
      if (parsed.classes.length === 0) {
        setError('ไฟล์นี้ไม่มีจุด (point) ที่อ่านได้');
        return;
      }
      setLoaded(parsed);
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
    if (inputRef.current) inputRef.current.value = '';
  }, []);

  const runAnalysis = useCallback(async () => {
    if (!file) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      setAnalysis(await analyzePointCloud(file));
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = `(${err.status}) ${(err.body as { detail?: string })?.detail ?? err.statusText}`;
        setAnalyzeError(`วิเคราะห์ไม่สำเร็จ: ${detail}`);
      } else {
        // Network error — backend unreachable (no API deployed / URL down).
        // Show a friendly note instead of a raw "Failed to fetch".
        setAnalyzeError(
          'ยังเชื่อมต่อ backend ไม่ได้ — การวิเคราะห์คาร์บอนทำงานเมื่อมี API รันอยู่ (สาธิตสดในการนำเสนอ) ส่วนแสดงผล 3D ใช้งานได้เต็มที่',
        );
      }
    } finally {
      setAnalyzing(false);
    }
  }, [file]);

  return (
    <>
      <CompactWorkspaceHeader
        title="ผลการวิเคราะห์ 3D Point Cloud"
        mode={
          loaded === null
            ? 'Synthetic preview'
            : analysis === null
              ? 'Browser PLY preview'
              : 'Live analysis'
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
                รองรับ segmented .ply และจำกัดการแสดงผลไว้ที่ {MAX_POINTS.toLocaleString()} จุด
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
                      กลับไปตัวอย่าง synthetic
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
            </CardContent>
          </Card>

          <div className={`mt-6 grid gap-6 ${resultView ? 'lg:grid-cols-12' : ''}`}>
            <div className={resultView ? 'lg:col-span-8' : ''}>
              <ViewerStage
                title={
                  loaded === null ? 'Synthetic preview tree' : (fileName ?? 'Uploaded point cloud')
                }
                evidenceLabel={
                  loaded === null
                    ? 'SYNTHETIC · NOT PIPELINE EVIDENCE'
                    : analysis === null
                      ? 'BROWSER PLY · NOT ANALYZED'
                      : 'LIVE ANALYSIS · VIEWER IDENTITY UNVERIFIED'
                }
                positions={cloud.positions}
                classes={cloud.classes}
              >
                {analysis ? (
                  <ModeBadge
                    state={{
                      kind: 'local-live',
                      credentials: { endpoint: 'confirmed-analysis-runtime', token: '' },
                      pipelineVersion: analysis.metadata.pipeline_version,
                    }}
                  />
                ) : (
                  <span className="rounded-full border border-moss px-3 py-1.5 font-mono text-[0.625rem] uppercase tracking-wide text-lichen">
                    {loaded === null ? 'Synthetic' : `${nPoints.toLocaleString()} points`}
                  </span>
                )}
              </ViewerStage>
            </div>

            {resultView ? (
              <div className="lg:col-span-4">
                <ResultRail view={resultView} modeLabel="Live analysis" />
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
                {IS_API_CONFIGURED ? (
                  <>
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
    </>
  );
}
