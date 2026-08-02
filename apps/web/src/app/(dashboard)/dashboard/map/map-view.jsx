'use client';

import { useEffect } from 'react';
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

import 'leaflet/dist/leaflet.css';

const customIcon = L.icon({
  iconUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function ResizeMap() {
  const map = useMap();

  useEffect(() => {
    const updateMapSize = () => {
      map.invalidateSize(true);
    };

    const timer1 = setTimeout(updateMapSize, 100);
    const timer2 = setTimeout(updateMapSize, 500);

    window.addEventListener('resize', updateMapSize);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      window.removeEventListener('resize', updateMapSize);
    };
  }, [map]);

  return null;
}

export default function MapView() {
  const hatYaiCenter = [7.0086, 100.4747];

  const hatYaiBounds = [
    [6.85, 100.35],
    [7.18, 100.6],
  ];

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        backgroundColor: '#d8d8d8',
      }}
    >
      <MapContainer
        center={hatYaiCenter}
        zoom={12}
        minZoom={10}
        maxZoom={18}
        maxBounds={hatYaiBounds}
        maxBoundsViscosity={1}
        scrollWheelZoom
        zoomControl
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          zIndex: 1,
        }}
      >
        <ResizeMap />

        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <Marker position={hatYaiCenter} icon={customIcon}>
          <Popup>
            <div>
              <strong>แปลงสำรวจหาดใหญ่ #1</strong>
              <p>พิกัด: 7.0086, 100.4747</p>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}