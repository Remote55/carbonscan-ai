"use client";

import { useMemo } from "react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PointCloudLegend } from "@/components/viewer/point-cloud-legend";
import { PointCloudViewer } from "@/components/viewer/point-cloud-viewer";
import { generateDemoTree } from "@/lib/demo-pointcloud";

export default function ViewerPage() {
  const tree = useMemo(() => generateDemoTree({ seed: 42 }), []);
  const nPoints = tree.classes.length;

  return (
    <main className="container mx-auto px-4 py-12">
      <div className="mx-auto max-w-5xl">
        <h1 className="font-display text-3xl font-bold tracking-tight">
          3D Point Cloud Viewer
        </h1>
        <p className="mt-2 text-muted-foreground">
          ดูต้นไม้แบบ 3 มิติ พร้อมสีแยกลำต้น / ใบ / พื้นดิน — หมุน ซูม เลื่อนได้
          (ตัวอย่าง {nPoints.toLocaleString()} จุด)
        </p>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>ตัวอย่างต้นไม้ (synthetic)</CardTitle>
            <CardDescription>
              เชื่อมต่อผลจริงจาก ML pipeline ได้ภายหลัง — ส่ง positions + class
              ที่ได้จาก segmented .ply เข้า component เดียวกันนี้
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <PointCloudViewer
              positions={tree.positions}
              classes={tree.classes}
              className="h-[480px] w-full overflow-hidden rounded-lg ring-1 ring-foreground/10"
            />
            <PointCloudLegend />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
