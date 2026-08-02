'use client';

import dynamic from 'next/dynamic';

import { CompactWorkspaceHeader } from '@/components/layout/compact-workspace-header';

const MapView = dynamic(() => import('./map-view'), {
  ssr: false,
  loading: () => (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      กำลังโหลดแผนที่...
    </div>
  ),
});

export default function MapPage() {
  return (
    <div
      style={{
        width: '100%',
        height: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <div style={{ flexShrink: 0 }}>
        <CompactWorkspaceHeader
          title="แผนที่พื้นที่สำรวจ"
          mode="ต้นไม้ที่สแกนจำนวนคาร์บอนที่ปล่อยสำเร็จแล้ว"
          backHref="/dashboard"
        />
      </div>

      <main
        style={{
          position: 'relative',
          flex: 1,
          minHeight: 0,
          width: '100%',
          overflow: 'hidden',
        }}
      >
        <MapView />
      </main>
    </div>
  );
}