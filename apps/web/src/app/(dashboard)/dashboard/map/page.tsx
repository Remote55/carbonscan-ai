'use client';

import dynamic from 'next/dynamic';

import { CompactWorkspaceHeader } from '@/components/layout/compact-workspace-header';

// Leaflet reaches for `window` at import time, so it cannot be server-rendered.
const MapView = dynamic(() => import('./map-view'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-sm text-canopy">
      กำลังโหลดแผนที่…
    </div>
  ),
});

export default function MapPage() {
  return (
    // 100dvh minus the 4rem dashboard header. Using the full viewport height
    // here pushed the page 65px past the bottom and made it scroll for nothing.
    <div className="flex h-[calc(100dvh-4rem)] w-full flex-col overflow-hidden">
      <div className="shrink-0">
        {/* This page draws a base map and one example pin. It is not reading
            survey plots, scanned trees or computed carbon from anywhere, and
            the label has to say so - the previous one claimed all three. */}
        <CompactWorkspaceHeader
          title="แผนที่พื้นที่สำรวจ"
          mode="ตัวอย่างการแสดงผลบนแผนที่ · ยังไม่ได้เชื่อมข้อมูลแปลงจริง"
          backHref="/dashboard"
        />
      </div>

      <main className="relative w-full min-h-0 flex-1 overflow-hidden">
        <MapView />
      </main>
    </div>
  );
}
