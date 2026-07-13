"use client";

import { useCallback, useMemo, useRef, useState } from "react";

import { analyzePointCloud, ApiError, IS_API_CONFIGURED, type AnalyzeResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PointCloudLegend } from "@/components/viewer/point-cloud-legend";
import { PointCloudViewer } from "@/components/viewer/point-cloud-viewer";
import { generateDemoTree, type PointCloud } from "@/lib/demo-pointcloud";
import { decimate, parsePly } from "@/lib/ply-loader";

const MAX_POINTS = 200_000;

const fmt = (n: number | null | undefined, d = 2) =>
  n == null ? "—" : n.toLocaleString(undefined, { maximumFractionDigits: d });

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

  const loadFile = useCallback(async (f: File) => {
    if (!f.name.toLowerCase().endsWith(".ply")) {
      setError("รองรับเฉพาะไฟล์ .ply เท่านั้น");
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
        setError("ไฟล์นี้ไม่มีจุด (point) ที่อ่านได้");
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
    if (inputRef.current) inputRef.current.value = "";
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
          "ยังเชื่อมต่อ backend ไม่ได้ — การวิเคราะห์คาร์บอนทำงานเมื่อมี API รันอยู่ (สาธิตสดในการนำเสนอ) ส่วนแสดงผล 3D ใช้งานได้เต็มที่",
        );
      }
    } finally {
      setAnalyzing(false);
    }
  }, [file]);

  return (
    <main className="container mx-auto px-4 py-12">
      <div className="mx-auto max-w-5xl">
        <h1 className="font-display text-3xl font-bold tracking-tight">
          3D Point Cloud Viewer
        </h1>
        <p className="mt-2 text-muted-foreground">
          ดูต้นไม้แบบ 3 มิติ พร้อมสีแยกลำต้น / ใบ / พื้นดิน — หมุน ซูม เลื่อนได้
        </p>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>
              {loaded ? `ไฟล์: ${fileName}` : "ตัวอย่างต้นไม้ (synthetic)"}
            </CardTitle>
            <CardDescription>
              {loaded
                ? `point cloud จาก segmented .ply จริง — ${nPoints.toLocaleString()} จุด`
                : "ลากไฟล์ .ply ที่ export จาก ML pipeline มาวาง หรือเลือกไฟล์ เพื่อดู point cloud จริง"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={onDrop}
              className={`flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-foreground/15 bg-muted/30"
              }`}
            >
              <p className="text-sm text-muted-foreground">
                {isLoading ? "กำลังอ่านไฟล์…" : "ลากไฟล์ .ply มาวางที่นี่ หรือ"}
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
                    กลับไปตัวอย่าง (demo tree)
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
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}

            <p className="text-sm text-muted-foreground">
              กำลังแสดง {nPoints.toLocaleString()} จุด
              {loaded ? "" : " (ตัวอย่าง synthetic)"}
            </p>

            <PointCloudViewer
              positions={cloud.positions}
              classes={cloud.classes}
              className="h-[480px] w-full overflow-hidden rounded-lg ring-1 ring-foreground/10"
            />
            <PointCloudLegend />
          </CardContent>
        </Card>

        {loaded ? (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>ผลวิเคราะห์คาร์บอน (ML pipeline จริง)</CardTitle>
              <CardDescription>
                ส่งไฟล์นี้เข้า backend → รัน pipeline (ground → tree → wood/leaf → QSM →
                allometric) → คืนค่าคาร์บอนจริง
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {IS_API_CONFIGURED ? (
                <>
                  <Button type="button" onClick={runAnalysis} disabled={analyzing}>
                    {analyzing ? "กำลังวิเคราะห์… (อาจใช้เวลาสักครู่)" : "วิเคราะห์คาร์บอน"}
                  </Button>

                  {analyzeError ? (
                    <p className="text-sm text-destructive" role="alert">
                      {analyzeError}
                    </p>
                  ) : null}
                </>
              ) : (
                <div className="rounded-lg border border-dashed border-foreground/20 bg-muted/30 p-4">
                  <p className="text-sm font-medium text-foreground">
                    การวิเคราะห์คาร์บอนทำงานผ่าน backend (ML pipeline จริง)
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    เวอร์ชันสาธิตออนไลน์นี้แสดงเฉพาะการแยก 3 มิติ (ลำต้น / ใบ / พื้นดิน) —
                    การคำนวณคาร์บอนสาธิตสดผ่าน API ในการนำเสนอ ตัวอย่างผลจริง: ต้นเดี่ยว DBH 28.3 ซม.
                    · สูง 13.6 ม. ·{" "}
                    <span className="font-semibold text-foreground">คาร์บอน 207 กก.</span>{" "}
                    (CO₂e 760 กก.)
                  </p>
                </div>
              )}

              {analysis ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <div className="rounded-lg border border-foreground/10 p-4">
                      <div className="text-2xl font-bold">{analysis.summary.total_trees}</div>
                      <div className="text-sm text-muted-foreground">จำนวนต้นไม้</div>
                    </div>
                    <div className="rounded-lg border border-foreground/10 p-4">
                      <div className="text-2xl font-bold">
                        {fmt(analysis.summary.total_carbon_kg)} <span className="text-base">kg</span>
                      </div>
                      <div className="text-sm text-muted-foreground">คาร์บอนรวม</div>
                    </div>
                    <div className="rounded-lg border border-foreground/10 p-4">
                      <div className="text-2xl font-bold">
                        {fmt(analysis.summary.total_co2eq_kg / 1000, 3)}{" "}
                        <span className="text-base">tCO₂e</span>
                      </div>
                      <div className="text-sm text-muted-foreground">CO₂ เทียบเท่า</div>
                    </div>
                  </div>

                  {analysis.trees.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="text-left text-muted-foreground">
                          <tr className="border-b border-foreground/10">
                            <th className="py-2 pr-4">ต้นที่</th>
                            <th className="py-2 pr-4">DBH (cm)</th>
                            <th className="py-2 pr-4">สูง (m)</th>
                            <th className="py-2 pr-4">ปริมาตร (m³)</th>
                            <th className="py-2 pr-4">คาร์บอน (kg)</th>
                            <th className="py-2">CO₂e (kg)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analysis.trees.map((t) => (
                            <tr key={t.tree_id} className="border-b border-foreground/5">
                              <td className="py-2 pr-4">{t.tree_id}</td>
                              <td className="py-2 pr-4">{fmt(t.dbh_cm)}</td>
                              <td className="py-2 pr-4">{fmt(t.height_m)}</td>
                              <td className="py-2 pr-4">{fmt(t.volume_m3, 4)}</td>
                              <td className="py-2 pr-4">{fmt(t.carbon_kg)}</td>
                              <td className="py-2">{fmt(t.co2eq_kg)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      ไม่พบต้นไม้ในไฟล์นี้ (ลองไฟล์ที่เป็น plot หลายต้น)
                    </p>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </div>
    </main>
  );
}
