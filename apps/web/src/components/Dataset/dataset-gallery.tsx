'use client';

import Image, { type StaticImageData } from 'next/image';
import { useMemo, useState } from 'react';
import {
  TransformComponent,
  TransformWrapper,
} from 'react-zoom-pan-pinch';

import FEXC1Model from './FEXC1_model.png';
import FEXC1Overlay from './FEXC1_overlay.png';
import FEXC1PointCloud from './FEXC1_pointcloud.png';

import FEXC2Model from './FEXC2_model.png';
import FEXC2Overlay from './FEXC2_overlay.png';
import FEXC2PointCloud from './FEXC2_pointcloud.png';

import FEXC3Model from './FEXC3_model.png';
import FEXC3Overlay from './FEXC3_overlay.png';
import FEXC3PointCloud from './FEXC3_pointcloud.png';

import FEXC4Model from './FEXC4_model.png';
import FEXC4Overlay from './FEXC4_overlay.png';
import FEXC4PointCloud from './FEXC4_pointcloud.png';

import FEXC5Model from './FEXC5_model.png';
import FEXC5Overlay from './FEXC5_overlay.png';
import FEXC5PointCloud from './FEXC5_pointcloud.png';

import FEXC6Model from './FEXC6_model.png';
import FEXC6Overlay from './FEXC6_overlay.png';
import FEXC6PointCloud from './FEXC6_pointcloud.png';

type DatasetImageType = 'pointcloud' | 'overlay' | 'model';

interface DatasetImage {
  type: DatasetImageType;
  label: string;
  shortLabel: string;
  description: string;
  image: StaticImageData;
}

interface DatasetItem {
  id: string;
  description: string;
  images: DatasetImage[];
}

function createDataset(
  id: string,
  pointCloud: StaticImageData,
  overlay: StaticImageData,
  model: StaticImageData,
): DatasetItem {
  return {
    id,
    description:
      'แสดงลำดับข้อมูลตั้งแต่ Point Cloud ต้นฉบับ ผลการซ้อนทับสำหรับตรวจสอบโครงสร้าง และแบบจำลองสามมิติหลังการประมวลผล',
    images: [
      {
        type: 'pointcloud',
        label: 'ข้อมูล Point Cloud',
        shortLabel: 'Point Cloud',
        description:
          'ข้อมูลจุดสามมิติต้นฉบับที่ใช้เป็นข้อมูลนำเข้าสู่ระบบ',
        image: pointCloud,
      },
      {
        type: 'overlay',
        label: 'ผลการซ้อนทับ',
        shortLabel: 'Overlay',
        description:
          'ภาพซ้อนทับสำหรับตรวจสอบตำแหน่งและความสอดคล้องของโครงสร้างต้นไม้',
        image: overlay,
      },
      {
        type: 'model',
        label: 'แบบจำลองโครงสร้าง',
        shortLabel: 'Model',
        description:
          'แบบจำลองโครงสร้างสามมิติที่สร้างขึ้นหลังการประมวลผลข้อมูล',
        image: model,
      },
    ],
  };
}

const DATASETS: DatasetItem[] = [
  createDataset('FEXC1', FEXC1PointCloud, FEXC1Overlay, FEXC1Model),
  createDataset('FEXC2', FEXC2PointCloud, FEXC2Overlay, FEXC2Model),
  createDataset('FEXC3', FEXC3PointCloud, FEXC3Overlay, FEXC3Model),
  createDataset('FEXC4', FEXC4PointCloud, FEXC4Overlay, FEXC4Model),
  createDataset('FEXC5', FEXC5PointCloud, FEXC5Overlay, FEXC5Model),
  createDataset('FEXC6', FEXC6PointCloud, FEXC6Overlay, FEXC6Model),
];

export function DatasetGallery() {
  const [datasetIndex, setDatasetIndex] = useState(0);
  const [imageType, setImageType] =
    useState<DatasetImageType>('pointcloud');

  const dataset = DATASETS[datasetIndex];

  const selectedImage = useMemo(() => {
    return (
      dataset.images.find((item) => item.type === imageType) ??
      dataset.images[0]
    );
  }, [dataset, imageType]);

  function selectDataset(index: number) {
    setDatasetIndex(index);
    setImageType('pointcloud');
  }

  function previousDataset() {
    const previousIndex =
      datasetIndex === 0
        ? DATASETS.length - 1
        : datasetIndex - 1;

    selectDataset(previousIndex);
  }

  function nextDataset() {
    const nextIndex =
      datasetIndex === DATASETS.length - 1
        ? 0
        : datasetIndex + 1;

    selectDataset(nextIndex);
  }

  return (
    <div className="overflow-hidden rounded-[1.75rem] bg-deep-forest text-paper shadow-[0_24px_60px_-24px_rgba(14,42,29,0.45)]">
      <div className="grid lg:grid-cols-12">
        <div className="border-b border-paper/15 lg:col-span-8 lg:border-b-0 lg:border-r">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-paper/15 px-5 py-4 sm:px-6">
            <div>
              <p className="editorial-eyebrow-th text-lichen">
                ตัวอย่างชุดข้อมูล
              </p>

              <h3 className="mt-1 font-display text-2xl font-semibold text-paper">
                {dataset.id}
              </h3>
            </div>

            <span className="rounded-full border border-moss/50 bg-moss/15 px-3 py-1.5 text-xs font-medium text-lichen">
              ชุดที่ {datasetIndex + 1} จาก {DATASETS.length}
            </span>
          </div>
          <TransformWrapper
  key={`${dataset.id}-${selectedImage.type}`}
  initialScale={1}
  minScale={1}
  maxScale={10}
  centerOnInit
  centerZoomedOut={false}
  limitToBounds
  wheel={{
    step: 0.05,
  }}
  pinch={{
    step: 5,
  }}
  doubleClick={{
    mode: 'zoomIn',
    step: 2,
  }}
  panning={{
    velocityDisabled: true,
  }}
>
  {() => (
    <div className="relative h-[36rem] cursor-grab overflow-hidden bg-[#f5f4ef] active:cursor-grabbing">
      <TransformComponent
        wrapperClass="!h-full !w-full"
        contentClass="!flex !h-full !w-full !items-center !justify-center"
      >
        <Image
          key={`${dataset.id}-${selectedImage.type}`}
          src={selectedImage.image}
          alt={`${dataset.id} — ${selectedImage.label}`}
          width={1600}
          height={1600}
          priority
          unoptimized
          draggable={false}
          className="pointer-events-none h-auto max-h-[34rem] w-auto max-w-[94%] select-none object-contain"
        />
      </TransformComponent>
    </div>
  )}
</TransformWrapper>

  

          <div className="border-t border-paper/15 p-4 sm:p-5">
            <div className="grid gap-2 sm:grid-cols-3">
              {dataset.images.map((item) => {
                const isSelected = item.type === imageType;

                return (
                  <button
                    key={item.type}
                    type="button"
                    onClick={() => setImageType(item.type)}
                    aria-pressed={isSelected}
                    className={
                      isSelected
                        ? 'focus-ring rounded-xl border border-moss bg-moss/20 px-4 py-3 text-left text-paper'
                        : 'focus-ring rounded-xl border border-paper/15 bg-paper/5 px-4 py-3 text-left text-mist transition-colors hover:border-paper/30 hover:bg-paper/10 hover:text-paper'
                    }
                  >
                    <span className="block text-sm font-semibold">
                      {item.label}
                    </span>

                    <span className="mt-1 block text-xs opacity-70">
                      {item.shortLabel}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <aside className="flex min-h-[32rem] flex-col p-6 sm:p-8 lg:col-span-4">
          <div>
            <p className="editorial-eyebrow-th text-lichen">
              รายละเอียดชุดข้อมูล
            </p>

            <h3 className="mt-2 font-display text-3xl font-semibold text-paper">
              {dataset.id}
            </h3>

            <p className="mt-4 text-sm leading-7 text-mist">
              {dataset.description}
            </p>
          </div>

          <div className="mt-7 space-y-3">
            <div className="rounded-xl border border-paper/15 bg-paper/5 p-4">
              <p className="editorial-eyebrow-th text-lichen">
                ขั้นตอนที่กำลังแสดง
              </p>

              <h4 className="mt-2 font-display text-xl font-semibold text-paper">
                {selectedImage.label}
              </h4>

              <p className="mt-2 text-xs leading-6 text-mist">
                {selectedImage.description}
              </p>
            </div>

            <div className="rounded-xl border border-paper/15 bg-paper/5 p-4">
              <p className="editorial-eyebrow-th text-lichen">
                ลำดับของข้อมูล
              </p>

              <p className="mt-2 text-sm leading-6 text-mist">
                Point Cloud → Overlay → แบบจำลองโครงสร้าง
              </p>
            </div>

            <div className="rounded-xl border border-paper/15 bg-paper/5 p-4">
              <p className="editorial-eyebrow-th text-lichen">
                การนำไปใช้
              </p>

              <p className="mt-2 text-sm leading-6 text-mist">
                ใช้ตรวจสอบการเตรียมข้อมูล เปรียบเทียบรูปทรงต้นไม้
                และประเมินผลลัพธ์หลังสร้างแบบจำลอง
              </p>
            </div>
          </div>

          <div className="mt-auto pt-8">
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={previousDataset}
                className="focus-ring rounded-full border border-paper/20 px-4 py-2.5 text-sm font-medium text-paper transition-colors hover:bg-paper/10"
              >
                ก่อนหน้า
              </button>

              <button
                type="button"
                onClick={nextDataset}
                className="focus-ring rounded-full bg-moss px-4 py-2.5 text-sm font-medium text-paper transition-colors hover:bg-moss/80"
              >
                ถัดไป
              </button>
            </div>

            <div className="mt-5 flex flex-wrap justify-center gap-2">
              {DATASETS.map((item, index) => {
                const isSelected = index === datasetIndex;

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => selectDataset(index)}
                    aria-label={`เปิดชุดข้อมูล ${item.id}`}
                    aria-pressed={isSelected}
                    className={
                      isSelected
                        ? 'focus-ring h-2.5 w-8 rounded-full bg-lichen transition-all'
                        : 'focus-ring h-2.5 w-2.5 rounded-full bg-paper/25 transition-all hover:bg-paper/50'
                    }
                  />
                );
              })}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}