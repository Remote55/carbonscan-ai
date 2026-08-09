"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";
import { Color, SRGBColorSpace } from "three";

import { CLASS_GROUND, CLASS_LEAF, CLASS_WOOD } from "@/lib/demo-pointcloud";
import { frameCloud } from "@/lib/viewer-framing";

/** RGB (0–1) per class — wood (brown), leaf (green), ground (tan). sRGB, matches the legend. */
export const CLASS_COLORS: Record<number, [number, number, number]> = {
  [CLASS_WOOD]: [0.55, 0.36, 0.22],
  [CLASS_LEAF]: [0.3, 0.6, 0.36],
  [CLASS_GROUND]: [0.72, 0.64, 0.49],
};

/**
 * The colour of "not classified yet".
 *
 * Deliberately cool and deliberately none of the three above: a raw scan drawn
 * in any class colour reads as a classification, and a plot rendered entirely
 * in ground-tan reads as the system having decided the forest is floor.
 */
export const UNLABELLED_COLOR: [number, number, number] = [0.62, 0.66, 0.7];

/**
 * three.js stores vertex colours in LINEAR space and the canvas outputs sRGB,
 * so feeding it the sRGB palette above washes browns out to tan. Pre-convert
 * the palette sRGB → linear once so the rendered colours match the legend.
 */
const LINEAR_CLASS_COLORS = Object.fromEntries(
  Object.entries(CLASS_COLORS).map(([key, [r, g, b]]) => {
    const c = new Color().setRGB(r, g, b, SRGBColorSpace);
    return [key, [c.r, c.g, c.b]];
  }),
) as Record<number, [number, number, number]>;

const LINEAR_UNLABELLED = (() => {
  const [r, g, b] = UNLABELLED_COLOR;
  const c = new Color().setRGB(r, g, b, SRGBColorSpace);
  return [c.r, c.g, c.b] as [number, number, number];
})();

export interface PointCloudViewerProps {
  /** flat XYZ (length = n*3), Z-up (as produced by the pipeline) */
  positions: Float32Array;
  /** per-point class id (0=wood, 1=leaf, 2=ground) */
  classes: Uint8Array;
  /** Whether `classes` is real. False for a raw scan; see PointCloud.labelled. */
  labelled: boolean;
  pointSize?: number;
  className?: string;
}

function PointCloud({
  positions,
  classes,
  labelled,
  pointSize,
}: Pick<PointCloudViewerProps, "positions" | "classes" | "labelled"> & { pointSize: number }) {
  const colors = useMemo(() => {
    const arr = new Float32Array(classes.length * 3);
    for (let i = 0; i < classes.length; i++) {
      const [r, g, b] = labelled
        ? (LINEAR_CLASS_COLORS[classes[i]] ?? LINEAR_CLASS_COLORS[CLASS_GROUND])
        : LINEAR_UNLABELLED;
      arr[i * 3] = r;
      arr[i * 3 + 1] = g;
      arr[i * 3 + 2] = b;
    }
    return arr;
  }, [classes, labelled]);

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
  labelled,
  pointSize,
  className,
}: PointCloudViewerProps) {
  const box = useRef<HTMLDivElement>(null);
  // Measured, not assumed. Null until the element exists, which is why the
  // canvas waits: the camera is read once at creation, so mounting before the
  // real aspect is known would bake in the wrong distance for good.
  const [aspect, setAspect] = useState<number | null>(null);

  // useEffect, not useLayoutEffect: this component is server-rendered for the
  // initial HTML, where a layout effect is a no-op React warns about. Measuring
  // after paint costs one frame of empty stage, which is nothing next to the
  // time WebGL takes to come up anyway.
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const measure = () => {
      const { clientWidth, clientHeight } = el;
      if (clientWidth > 0 && clientHeight > 0) setAspect(clientWidth / clientHeight);
    };
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const framing = useMemo(
    () => frameCloud(positions, aspect ?? 1),
    [positions, aspect],
  );

  // What this picture says, in words.
  //
  // A WebGL canvas is a blank element to anything that is not a pair of eyes:
  // no role, no name, no text. The centrepiece of the product simply did not
  // exist for a screen reader. It cannot be made to convey a point cloud, but
  // it can say what it is showing and how much of it, and the measurements it
  // illustrates are in the results table either way.
  const description = useMemo(() => {
    const count = Math.floor(positions.length / 3);
    const points = count.toLocaleString("th-TH");
    return labelled
      ? `ภาพสามมิติของกลุ่มจุด ${points} จุด แยกสีตามลำต้น ใบ และพื้นดิน ` +
          `ตัวเลขที่วัดได้อยู่ในตารางผลลัพธ์`
      : `ภาพสามมิติของกลุ่มจุด ${points} จุด ยังไม่ได้แยกลำต้นกับใบ`;
  }, [positions.length, labelled]);

  return (
    <div className={className} ref={box} role="img" aria-label={description}>
      <p className="sr-only">{description}</p>
      {/* The camera prop is read when the canvas is created and ignored after,
          so a differently framed cloud has to remount it. That is the same
          moment the geometry is replaced anyway. */}
      {aspect === null ? null : (
        <Canvas
          aria-hidden="true"
          key={`${framing.position.join()}|${framing.target.join()}`}
          camera={{ position: framing.position, fov: 50 }}
          style={{ background: "#0f1411" }}
          dpr={[1, 2]}
        >
          <PointCloud
            positions={positions}
            classes={classes}
            labelled={labelled}
            pointSize={pointSize ?? framing.pointSize}
          />
          <OrbitControls target={framing.target} enableDamping makeDefault />
        </Canvas>
      )}
    </div>
  );
}
