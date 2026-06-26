"use client";

import { useCallback, useMemo, useRef, useState } from "react";

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

export default function ViewerPage() {
  const demoTree = useMemo(() => generateDemoTree({ seed: 42 }), []);

  const [loaded, setLoaded] = useState<PointCloud | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const cloud = loaded ?? demoTree;
  const nPoints = cloud.classes.length;

  const loadFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".ply")) {
      setError("รองรับเฉพาะไฟล์ .ply เท่านั้น");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const buffer = await file.arrayBuffer();
      const parsed = decimate(parsePly(buffer), MAX_POINTS);
      if (parsed.classes.length === 0) {
        setError("ไฟล์นี้ไม่มีจุด (point) ที่อ่านได้");
        return;
      }
      setLoaded(parsed);
      setFileName(file.name);
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
      const file = e.dataTransfer.files?.[0];
      if (file) void loadFile(file);
    },
    [loadFile],
  );

  const resetToDemo = useCallback(() => {
    setLoaded(null);
    setFileName(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

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
                {isLoading
                  ? "กำลังอ่านไฟล์…"
                  : "ลากไฟล์ .ply มาวางที่นี่ หรือ"}
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
                  const file = e.target.files?.[0];
                  if (file) void loadFile(file);
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
      </div>
    </main>
  );
}
