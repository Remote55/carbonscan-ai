# Glossary — CarbonScan AI

## Forest Science / Carbon Domain
| Term | Expansion | Notes |
|---|---|---|
| **DBH** | Diameter at Breast Height | เส้นผ่านศูนย์กลางลำต้นที่ระดับอก (1.3 ม.) — input หลักของสมการ Allometric |
| **Height (H)** | ความสูงของต้นไม้ | input ที่สองของสมการ |
| **Volume (V)** | ปริมาตรไม้ | คำนวณจาก QSM หรือสมการ V = f(DBH, H) |
| **Biomass (B)** | มวลชีวภาพ (kg) | B = V × Wood Density |
| **Allometric Equation** | สมการแอลโลเมตริก | สมการที่ใช้แปลง dimension ต้นไม้ → biomass — ของไทยใช้ตาม TGO Guideline |
| **Wood Density (ρ)** | ความหนาแน่นเนื้อไม้ (kg/m³) | ค่าต่างกันตามชนิดไม้ — สัก ~650, ยางพารา ~580 |
| **Carbon Content** | สัดส่วนคาร์บอนใน biomass | มาตรฐาน IPCC ใช้ 0.47 |
| **Carbon Stock** | ปริมาณคาร์บอนกักเก็บ | C = B × Carbon Content |
| **CO₂ Equivalent** | ค่าเทียบเท่า CO₂ | CO₂eq = C × (44/12) |
| **Carbon Credit** | หน่วยซื้อ-ขาย | 1 credit = 1 tCO₂eq |
| **Additionality** | ส่วนต่างคาร์บอนที่เพิ่ม | ปีปัจจุบัน - ปีฐาน (สำคัญสำหรับตลาด) |
| **TGO** | องค์การบริหารจัดการก๊าซเรือนกระจก | ผู้ออก/รับรอง Carbon Credit ของไทย |
| **CBAM** | Carbon Border Adjustment Mechanism | EU Carbon Tax (มีผล 2026) |
| **Greenwashing** | การฟอกเขียว | บริษัทอวด CSR แต่ผลจริงไม่มี |

## LiDAR / Point Cloud
| Term | Expansion | Notes |
|---|---|---|
| **LiDAR** | Light Detection and Ranging | Sensor ยิง laser วัดระยะ → สร้าง point cloud |
| **Point Cloud** | กลุ่มของจุด 3D | data หลักของ LiDAR — แต่ละจุดมี (x, y, z) |
| **.las / .laz** | LAS file format | มาตรฐาน LiDAR file — .laz คือ compressed |
| **.ply** | Polygon File Format | open-source point cloud format |
| **TLS** | Terrestrial Laser Scanning | LiDAR แบบ ground-based (precision สูง) |
| **ALS** | Airborne Laser Scanning | LiDAR จาก aircraft/drone |
| **MLS** | Mobile Laser Scanning | LiDAR จาก vehicle/handheld |
| **ITD** | Individual Tree Detection | algorithm หาต้นไม้ทีละต้นจาก point cloud |
| **CHM** | Canopy Height Model | raster สูง = canopy height ของพื้นที่ |
| **DTM** | Digital Terrain Model | raster ของพื้นดิน |
| **CSF** | Cloth Simulation Filter | algorithm แยก ground points |

## AI / ML
| Term | Expansion | Notes |
|---|---|---|
| **PointNet++** | Point Cloud Deep Learning Architecture | Standard model สำหรับ point cloud segmentation |
| **KPConv** | Kernel Point Convolution | Modern alternative to PointNet++ |
| **RandLA-Net** | Random Large-scale Network | Scale ได้ดีสำหรับ point cloud ใหญ่ |
| **Semantic Segmentation** | จำแนกแต่ละจุดเป็น class | เช่น wood/leaf/ground |
| **Wood-Leaf Separation** | แยกใบออกจากลำต้น/กิ่ง | งานหลักของ AI core |
| **TLSeparation** | Rule-based wood-leaf separation | Baseline ก่อนใช้ DL |
| **QSM** | Quantitative Structure Model | สร้างทรงกระบอกครอบลำต้น+กิ่ง → ปริมาตร |
| **IoU** | Intersection over Union | metric วัดความแม่นยำของ segmentation |
| **RMSE** | Root Mean Square Error | metric วัดความคลาดเคลื่อนเทียบกับ ground truth |

## Photogrammetry (LiDAR Alternative)
| Term | Expansion | Notes |
|---|---|---|
| **SfM** | Structure from Motion | สร้าง 3D จาก multiple 2D images |
| **MVS** | Multi-View Stereo | Dense reconstruction จาก SfM output |
| **COLMAP** | Open-source SfM pipeline | https://colmap.github.io |
| **OpenMVS** | Open-source MVS library | คู่กับ COLMAP |
| **Meshroom** | All-in-one photogrammetry GUI | จาก AliceVision |
| **NeRF** | Neural Radiance Fields | AI-based 3D reconstruction |
| **Gaussian Splatting** | Real-time 3D rendering | เทคโนโลยีใหม่ปี 2023 |
| **Depth Anything V2** | Monocular Depth Estimation | AI ประมาณ depth จากภาพเดี่ยว |

## Web / Mobile Tech
| Term | Expansion | Notes |
|---|---|---|
| **Next.js 14** | React framework | App Router architecture |
| **shadcn/ui** | Pre-built UI components | ใช้ Tailwind + Radix |
| **React Three Fiber** | Three.js wrapper for React | ใช้ทำ 3D Viewer |
| **potree-core** | Point cloud renderer for browser | ใช้ดู .las/.laz |
| **PostGIS** | PostgreSQL geospatial extension | เก็บ tree coordinates + spatial queries |
| **Supabase** | Backend-as-a-Service | DB + Auth + Storage + Queues |
| **FastAPI** | Python web framework | REST + async + auto Swagger docs |
| **RunPod** | Cloud GPU rental | Serverless GPU (pay-per-second) |
| **Riverpod** | Flutter state management | Modern alternative to Provider |
| **TFLite** | TensorFlow Lite | on-device ML inference |

## Competition / Process
| Term | Expansion | Notes |
|---|---|---|
| **NSC** | National Software Contest | จัดโดย NSTDA / สวทช. ปีนี้ครั้งที่ 28 |
| **SIMs** | ระบบลงทะเบียน NSC | https://www.nstda.or.th/sims |
| **NSTDA** | สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ | สวทช. |
| **Proposal** | ข้อเสนอโครงการ | ส่ง 29 พ.ค. 2569 |
| **Final Report** | รายงานฉบับสมบูรณ์ | ส่ง 17 ก.ค. 2569 |
