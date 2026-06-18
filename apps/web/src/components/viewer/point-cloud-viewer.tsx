"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";

import { CLASS_GROUND, CLASS_LEAF, CLASS_WOOD } from "@/lib/demo-pointcloud";

/** RGB (0–1) per class — wood (brown), leaf (green), ground (tan). */
export const CLASS_COLORS: Record<number, [number, number, number]> = {
  [CLASS_WOOD]: [0.55, 0.36, 0.22],
  [CLASS_LEAF]: [0.3, 0.6, 0.36],
  [CLASS_GROUND]: [0.72, 0.64, 0.49],
};

export interface PointCloudViewerProps {
  /** flat XYZ (length = n*3), Z-up (as produced by the pipeline) */
  positions: Float32Array;
  /** per-point class id (0=wood, 1=leaf, 2=ground) */
  classes: Uint8Array;
  pointSize?: number;
  className?: string;
}

function PointCloud({
  positions,
  classes,
  pointSize = 0.05,
}: Pick<PointCloudViewerProps, "positions" | "classes" | "pointSize">) {
  const colors = useMemo(() => {
    const arr = new Float32Array(classes.length * 3);
    for (let i = 0; i < classes.length; i++) {
      const [r, g, b] = CLASS_COLORS[classes[i]] ?? CLASS_COLORS[CLASS_GROUND];
      arr[i * 3] = r;
      arr[i * 3 + 1] = g;
      arr[i * 3 + 2] = b;
    }
    return arr;
  }, [classes]);

  // Pipeline clouds are Z-up; rotate -90° about X so the tree stands up (Y-up).
  return (
    <points rotation={[-Math.PI / 2, 0, 0]} key={positions.length}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial vertexColors size={pointSize} sizeAttenuation />
    </points>
  );
}

/**
 * Interactive 3D point-cloud viewer (orbit/zoom/pan) colouring points by their
 * wood/leaf/ground class. Feed it pipeline output or the demo tree.
 */
export function PointCloudViewer({
  positions,
  classes,
  pointSize,
  className,
}: PointCloudViewerProps) {
  return (
    <div className={className}>
      <Canvas
        camera={{ position: [10, 8, 14], fov: 50 }}
        style={{ background: "#0f1411" }}
        dpr={[1, 2]}
      >
        <PointCloud positions={positions} classes={classes} pointSize={pointSize} />
        <OrbitControls target={[0, 5, 0]} enableDamping makeDefault />
      </Canvas>
    </div>
  );
}
