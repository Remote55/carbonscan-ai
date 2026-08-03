'use client';

import L from 'leaflet';
import { useEffect, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';

import 'leaflet/dist/leaflet.css';

/**
 * Marker artwork is served from our own origin.
 *
 * It came from unpkg, which meant the pin silently broke on any network that
 * cannot reach a CDN - and the presenter says on stage that this site depends
 * on no external CDN. The three files are 4.5 kB together and now live in
 * public/leaflet.
 */
const markerIcon = L.icon({
  iconUrl: '/leaflet/marker-icon.png',
  iconRetinaUrl: '/leaflet/marker-icon-2x.png',
  shadowUrl: '/leaflet/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

/** Hat Yai, Songkhla. A view location, not a surveyed plot - see the note below. */
const CENTRE: [number, number] = [7.0086, 100.4747];
const BOUNDS: [[number, number], [number, number]] = [
  [6.85, 100.35],
  [7.18, 100.6],
];

/**
 * Leaflet measures its container once, at mount. Inside a flex column that
 * settles a frame later it reads zero and renders a sliver, so nudge it twice.
 */
function ResizeMap() {
  const map = useMap();

  useEffect(() => {
    const updateMapSize = () => map.invalidateSize(true);
    const first = setTimeout(updateMapSize, 100);
    const second = setTimeout(updateMapSize, 500);
    window.addEventListener('resize', updateMapSize);

    return () => {
      clearTimeout(first);
      clearTimeout(second);
      window.removeEventListener('resize', updateMapSize);
    };
  }, [map]);

  return null;
}

export default function MapView() {
  // Tiles come from OpenStreetMap over the internet; there is no offline copy.
  // Without this the page is a grey rectangle with nothing to explain it, which
  // on a bad venue connection reads as a broken product rather than a missing
  // network.
  const [tilesFailed, setTilesFailed] = useState(false);

  return (
    <div className="absolute inset-0 h-full w-full bg-[#dcdcdc]">
      <MapContainer
        center={CENTRE}
        zoom={12}
        minZoom={10}
        maxZoom={18}
        maxBounds={BOUNDS}
        maxBoundsViscosity={1}
        scrollWheelZoom
        zoomControl
        className="absolute inset-0 h-full w-full"
        style={{ zIndex: 1 }}
      >
        <ResizeMap />

        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          eventHandlers={{ tileerror: () => setTilesFailed(true) }}
        />

        <Marker position={CENTRE} icon={markerIcon}>
          <Popup>
            <strong>ตัวอย่างตำแหน่งบนแผนที่</strong>
            <br />
            พิกัด {CENTRE[0]}, {CENTRE[1]}
            <br />
            ยังไม่ได้เชื่อมกับข้อมูลแปลงสำรวจจริง
          </Popup>
        </Marker>
      </MapContainer>

      {tilesFailed ? (
        <div
          role="status"
          className="pointer-events-none absolute inset-x-0 top-4 z-[1000] mx-auto max-w-md rounded-xl border border-hairline bg-paper/95 px-4 py-3 text-center text-sm text-forest-ink shadow-lg"
        >
          โหลดแผนที่ไม่สำเร็จ — หน้านี้ต้องใช้อินเทอร์เน็ตเพื่อดึงภาพแผนที่จาก OpenStreetMap
          <br />
          <span className="text-canopy">ส่วนอื่นของระบบใช้งานได้ตามปกติโดยไม่ต้องต่อเน็ต</span>
        </div>
      ) : null}
    </div>
  );
}
