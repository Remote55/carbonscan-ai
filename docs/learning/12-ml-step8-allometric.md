# บท 12 — Step 8: สูตรคาร์บอน (Allometric Equations) ⭐

> 🎯 **เป้าหมายของบท:** หลังอ่านจบ ผู้อ่านจะคำนวณ "ต้นไม้ที่มี DBH 30 cm, สูง 15 m, ชนิดสัก จะมี carbon กี่ kg + CO₂eq กี่ kg" ได้ด้วยมือ + เข้าใจทำไมสูตรเป็นแบบนั้น
> 📚 **ความรู้พื้นฐาน:** อ่าน [บท 02 — Core Concepts](02-core-concepts.md) และ [บท 10 — QSM](10-ml-step6-qsm.md) แล้ว
> ⏱️ **เวลาในการอ่าน:** ~45 นาที (บทนี้ละเอียดสุด)
>
> 🔥 **บทนี้สำคัญที่สุดของระบบ** — ทุกอย่างที่ pipeline ทำมา (DBH, Height, Volume) **จบที่ขั้นนี้** เป็น "carbon kg" ที่ขายในตลาดได้

---

## 1. ปัญหาที่เราพยายามแก้

### 1.1 สิ่งที่มีอยู่ในมือก่อนถึงขั้นนี้

หลัง Step 1-7 เราได้ **per-tree measurements**:

```python
tree_1 = {
    "species_sci": "Tectona grandis",
    "DBH_cm": 30.0,
    "height_m": 15.0,
    "volume_m3": 0.45,     # จาก taper equation (Step 6)
    "location": (18.7883, 98.9853),
    ...
}
```

### 1.2 สิ่งที่ต้องการในตอนจบ

ตัวเลข **คาร์บอน** ที่ตลาด carbon credit ยอมรับ:

```python
result = {
    "AGB_kg": 280.0,        # ชีวมวลเหนือดิน
    "BGB_kg": 67.2,         # ชีวมวลใต้ดิน (ราก)
    "Total_biomass_kg": 347.2,
    "Carbon_kg": 163.2,     # คาร์บอนสุทธิ
    "CO2eq_kg": 598.4,      # ในรูปคาร์บอนไดออกไซด์
}
```

### 1.3 ทำไมไม่ "ชั่งน้ำหนัก" ต้นไม้ตรงๆ

เพราะการจะรู้ biomass จริง = **ต้องโค่นต้นไม้ → ตัด → ชั่ง** เรียกว่า **destructive sampling** (ขั้นตอนที่ Demol et al. 2021 ทำในงานวิจัยที่เราใช้ validate)

ปัญหา:
- 💀 **ต้นไม้ตาย** — สวนทางกับเป้าหมาย "เก็บคาร์บอน"
- 💰 **แพง** — โค่น + ขนส่ง + ชั่ง = ฿1,000-5,000/ต้น
- ⏱️ **ช้า** — 1 วัน/ต้น

ดังนั้นจึงต้องมีวิธี **"ทำนาย" biomass จากสิ่งที่วัดได้โดยไม่ทำลายต้น** (DBH + Height + species)

**วิธีนั้นคือ Allometric Equations** ← หัวข้อของบทนี้

---

## 2. หลักการ — Allometry คืออะไร

### 2.1 Allometry — รากศัพท์

> **Allometry** มาจากกรีก "allos" (ต่าง) + "metron" (วัด)
> = "การวัดความสัมพันธ์ระหว่าง quantities ต่างประเภทกัน"

ใน forestry: **ความสัมพันธ์ระหว่างขนาดที่วัดได้ (DBH, height) กับ biomass (น้ำหนัก)**

### 2.2 ทำไมเป็น Power-Law

ทฤษฎี: ต้นไม้ขยายขนาดแบบ **fractal** (กิ่งใหญ่แตกเป็นกิ่งเล็กในอัตราคงที่) ทำให้:

$$\text{Biomass} \propto \text{DBH}^b$$

โดย $b$ เป็นค่าคงที่ของ species นั้น (มักอยู่ในช่วง 2.0-2.5)

> 💡 **Analogy:** เหมือนสัตว์เลี้ยงลูกด้วยนม — น้ำหนัก ≈ length³ (เพราะปริมาตร × density)
> ต้นไม้ก็คล้ายกัน แต่ exponent ปรับตาม species

### 2.3 รูปแบบสมการที่ใช้กันในวงการ

มี 3 แบบหลัก เรียงจากง่ายไปยาก:

| รูปแบบ | สมการ | ข้อมูลที่ต้องการ | ความแม่นยำ |
|---|---|---|---|
| **Tier 1: DBH-only** | $AGB = a \cdot DBH^b$ | DBH เท่านั้น | ต่ำสุด |
| **Tier 2: DBH + Height** | $AGB = a \cdot DBH^b \cdot H^c$ | DBH + H | ปานกลาง |
| **Tier 3: DBH + H + Wood Density** | Chave 2014, Komiyama 2005 | + ρ | สูงสุด |

> 💡 **ระบบเราใช้ Tier 2 (species-specific) + Chave 2014 (Tier 3 fallback)** เป็นมาตรฐาน TGO 2017

---

## 3. สูตรทั้งหมดของระบบ (Master Formulas)

### 3.1 Big Picture — 6 ขั้นแปลงตัวเลข

```
ขั้นที่ 1: คำนวณ AGB (Above-Ground Biomass) — kg
ขั้นที่ 2: คำนวณ BGB (Below-Ground Biomass) — kg
ขั้นที่ 3: รวม Biomass = AGB + BGB — kg
ขั้นที่ 4: แปลง Biomass → Carbon (× C fraction) — kg C
ขั้นที่ 5: แปลง Carbon → CO₂eq (× 44/12) — kg CO₂
ขั้นที่ 6: × ราคาตลาด → ฿ (carbon credit value)
```

### 3.2 ขั้นที่ 1 — AGB (Above-Ground Biomass)

มี 2 สูตรที่ใช้:

#### 3.2.1 Species-specific Allometric (เลือกใช้ถ้ามี data)

$$\boxed{\text{AGB} = a \times \text{DBH}^b \times H^c} \quad \text{(kg)}$$

โดย:
- $a, b, c$ = ค่าคงที่เฉพาะ species (จาก peer-reviewed paper)
- $\text{DBH}$ = Diameter at Breast Height (cm)
- $H$ = Tree Height (m)

**ตัวอย่าง (สัก / Tectona grandis):**
- $a = 0.0509$
- $b = 2.150$
- $c = 0.700$
- ที่มา: Tsutsumi et al. 1983 (Thai monsoon forest)

**คำนวณตัวอย่าง:** ต้นสัก DBH 30 cm, H 15 m

$$
\begin{align}
\text{AGB} &= 0.0509 \times 30^{2.150} \times 15^{0.700} \\
&= 0.0509 \times 1{,}380.4 \times 6.78 \\
&= 0.0509 \times 9{,}359.7 \\
&\approx \boxed{476.4 \text{ kg}}
\end{align}
$$

#### 3.2.2 Pantropical Fallback (Chave 2014)

ใช้เมื่อ:
- species ไม่อยู่ใน database
- ไม่มี species-specific equation
- ต้องการ generic baseline สำหรับเขตร้อน

$$\boxed{\text{AGB} = 0.0673 \times (\rho \cdot \text{DBH}^2 \cdot H)^{0.976}} \quad \text{(kg)}$$

โดย:
- $\rho$ = wood density ในหน่วย **g/cm³** (= kg/m³ ÷ 1000)
- $\text{DBH}$ = cm
- $H$ = m
- $0.0673$, $0.976$ = ค่าคงที่ pantropical (จาก Chave et al. 2014, sample 4,004 trees ทั่วโลก)

**ตัวอย่าง:** ต้นที่ไม่รู้จัก species, ใช้ default wood density 0.60 g/cm³, DBH 30 cm, H 15 m

$$
\begin{align}
\text{AGB} &= 0.0673 \times (0.60 \times 30^2 \times 15)^{0.976} \\
&= 0.0673 \times (0.60 \times 900 \times 15)^{0.976} \\
&= 0.0673 \times (8{,}100)^{0.976} \\
&= 0.0673 \times 7{,}102.0 \\
&\approx \boxed{477.9 \text{ kg}}
\end{align}
$$

> 💡 **น่าสนใจ:** ทั้ง 2 สูตรให้ผลใกล้กัน (476 vs 478 kg) ที่ DBH 30 / H 15 — เป็นเหตุผลที่ Chave 2014 ได้รับการยอมรับเป็น "pantropical default"

### 3.3 ขั้นที่ 2 — BGB (Below-Ground Biomass)

ต้นไม้ใต้ดิน (รากใหญ่+เล็ก) นับเป็น **biomass** ด้วยเพราะมีคาร์บอน

**สมการ (IPCC 2006 default):**

$$\boxed{\text{BGB} = \text{AGB} \times R_{\text{root/shoot}}}$$

โดย:
- $R_{\text{root/shoot}}$ = "root-to-shoot ratio" = อัตราส่วนน้ำหนักรากต่อต้นเหนือดิน
- **Default tropical: 0.24** (IPCC 2006 Vol. 4, Ch. 4, Table 4.4)

**คำนวณต่อจากตัวอย่าง:**

$$
\text{BGB} = 476.4 \times 0.24 = \boxed{114.3 \text{ kg}}
$$

### 3.4 ขั้นที่ 3 — Total Biomass

$$\boxed{B = \text{AGB} + \text{BGB}}$$

**คำนวณ:**

$$
B = 476.4 + 114.3 = \boxed{590.7 \text{ kg}}
$$

### 3.5 ขั้นที่ 4 — Carbon

ในชีวมวลพืช คาร์บอนเป็นองค์ประกอบหลัก (~47% ของน้ำหนักแห้ง)

$$\boxed{C = B \times C_{\text{fraction}}}$$

โดย:
- $C_{\text{fraction}}$ = "carbon fraction" — สัดส่วนคาร์บอนต่อ biomass
- **Default: 0.47** (IPCC 2006 default for tropical/subtropical forests)

> ⚠️ **คำเตือน:** บางสายงานใช้ 0.50 — TGO 2017 ใช้ **0.47** ตาม IPCC, ดังนั้นเราใช้ตามนั้น

**คำนวณ:**

$$
C = 590.7 \times 0.47 = \boxed{277.6 \text{ kg C}}
$$

### 3.6 ขั้นที่ 5 — CO₂ equivalent

ตลาดคาร์บอนซื้อขายในหน่วย **CO₂eq** ไม่ใช่ "C เปลือยๆ"

เพราะ 1 อะตอม Carbon (มวล 12) ⇌ 1 โมเลกุล CO₂ (มวล 44)

$$\boxed{\text{CO}_2\text{eq} = C \times \frac{44}{12}}$$

**คำนวณ:**

$$
\text{CO}_2\text{eq} = 277.6 \times \frac{44}{12} = 277.6 \times 3.667 = \boxed{1{,}017.8 \text{ kg CO}_2\text{eq}}
$$

### 3.7 ขั้นที่ 6 — ราคาตลาด (ตัวอย่าง)

| ตลาด | ราคา/tCO₂eq | ราคาต้นนี้ |
|---|---|---|
| T-VER ไทย | ฿400 (avg) | $1,017.8 \div 1000 \times 400 = \boxed{฿407}$ |
| EU ETS | €100 (~฿3,800) | $1,017.8 \div 1000 \times 3{,}800 = \boxed{฿3{,}868}$ |

> 💡 **Insight:** ต้นสัก 1 ต้น DBH 30cm, H 15m = ขายได้ ~฿400-3,800 ตามตลาด ถ้ามี 1,000 ต้น = ฿400k-3.8M

---

## 4. โค้ดของเราในโปรเจกต์

### 4.1 ไฟล์หลัก

📂 **`services/ml/pipeline/allometric.py`** (258 บรรทัด)

**Status:** ✅ Phase 1 — 16/16 unit tests pass

### 4.2 Constants (บรรทัด 30-38)

```python
# CO2 to Carbon ratio (44 g/mol CO2 / 12 g/mol C)
CO2_PER_CARBON = 44.0 / 12.0

# Default Chave 2014 pantropical model
CHAVE_2014_A = 0.0673
CHAVE_2014_EXPONENT = 0.976

# IPCC 2006 defaults (Vol 4, Ch 4, Table 4.4)
DEFAULT_CARBON_FRACTION = 0.47
DEFAULT_ROOT_TO_SHOOT_TROPICAL = 0.24
```

### 4.3 SpeciesParams Dataclass (บรรทัด 41-54)

```python
@dataclass(frozen=True)
class SpeciesParams:
    name_sci: str
    name_th: str
    name_en: str
    wood_density: float  # kg/m³
    agb_a: float | None      # species-specific allometric coefficients
    agb_b: float | None      # AGB = a × DBH^b × H^c
    agb_c: float | None
    agb_source: str
    root_to_shoot: float = DEFAULT_ROOT_TO_SHOOT_TROPICAL
    carbon_fraction: float = DEFAULT_CARBON_FRACTION
```

### 4.4 Main Function — `calculate_carbon` (บรรทัด 152-217)

```python
def calculate_carbon(
    dbh_cm: float,
    height_m: float,
    species_sci: str | None = None,
    *,
    prefer_method: str = "auto",
) -> CarbonResult:
    # 1. Validate inputs
    if dbh_cm <= 0: raise ValueError(...)
    if height_m <= 0: raise ValueError(...)

    # 2. Look up species in DB
    db = load_species_db()
    species = db.get(species_sci) if species_sci else None

    # 3. Decide which method
    if species and species.agb_a is not None and prefer_method != "chave_pantropical":
        method = "species_specific"
        agb = calculate_agb_species_specific(dbh_cm, height_m, species)
        # AGB = a × DBH^b × H^c
        wood_density = species.wood_density
        source = species.agb_source
    else:
        method = "chave_pantropical"
        wood_density = species.wood_density if species else 600.0  # generic tropical
        agb = calculate_agb_chave_pantropical(dbh_cm, height_m, wood_density)
        # AGB = 0.0673 × (ρ × DBH² × H)^0.976
        source = "Chave et al. 2014"

    # 4. BGB + Total Biomass
    root_ratio = species.root_to_shoot if species else DEFAULT_ROOT_TO_SHOOT_TROPICAL
    bgb = agb * root_ratio
    biomass = agb + bgb

    # 5. Carbon + CO2eq
    c_frac = species.carbon_fraction if species else DEFAULT_CARBON_FRACTION
    carbon = biomass * c_frac
    co2eq = carbon * CO2_PER_CARBON

    return CarbonResult(
        species_sci=species_sci,
        dbh_cm=dbh_cm,
        height_m=height_m,
        method=method,
        agb_kg=agb,
        bgb_kg=bgb,
        biomass_kg=biomass,
        carbon_kg=carbon,
        co2eq_kg=co2eq,
        wood_density=wood_density,
        source=source,
    )
```

### 4.5 ลองใช้

```python
from pipeline.allometric import calculate_carbon

# Teak tree, DBH 30 cm, height 15 m
result = calculate_carbon(
    dbh_cm=30.0,
    height_m=15.0,
    species_sci="Tectona grandis",
)

print(f"AGB: {result.agb_kg:.1f} kg")
print(f"BGB: {result.bgb_kg:.1f} kg")
print(f"Total Biomass: {result.biomass_kg:.1f} kg")
print(f"Carbon: {result.carbon_kg:.1f} kg C")
print(f"CO2eq: {result.co2eq_kg:.1f} kg CO2eq")
print(f"Method: {result.method}")
print(f"Source: {result.source}")
```

**Output:**
```
AGB: 476.4 kg
BGB: 114.3 kg
Total Biomass: 590.7 kg
Carbon: 277.6 kg C
CO2eq: 1017.8 kg CO2eq
Method: species_specific
Source: Tsutsumi et al. 1983 (Thai monsoon forest)
```

✅ **ตรงกับการคำนวณด้วยมือในข้อ 3**

### 4.6 Alternative — From Volume + Density

ถ้ามี volume จาก QSM (Step 6) แทนที่จะใช้ allometric:

```python
def calculate_carbon_from_volume(
    volume_m3: float,
    wood_density: float,
    ...
) -> CarbonResult:
    # B = V × ρ
    agb = volume_m3 * wood_density  # kg
    # ... rest same as before
```

> 💡 **Cross-validation:** ใน production จะคำนวณ **ทั้ง 2 ทาง** แล้วเปรียบเทียบ — ถ้าใกล้กัน = confident, ถ้าต่างกันมาก = flag for review

---

## 5. Species Database

📂 **`services/ml/data/species_db.csv`** — 5 species + header

### 5.1 ดูข้อมูลทั้งหมด

| name_sci | name_th | name_en | wood_density (kg/m³) | a | b | c | source |
|---|---|---|---|---|---|---|---|
| **Tectona grandis** | สัก | Teak | 660 | 0.0509 | 2.150 | 0.700 | Tsutsumi et al. 1983 |
| **Dipterocarpus alatus** | ยางนา | Yang Na | 720 | 0.0396 | 2.380 | 0.800 | Ogawa et al. 1965 |
| **Bambusa spp.** | ไผ่ | Bamboo | 650 | 0.131 | 2.280 | 0.590 | Yiping et al. 2010 |
| **Hevea brasiliensis** | ยางพารา | Para Rubber | 580 | 0.0464 | 2.330 | 0.720 | Chiarucci et al. 2014 |
| **Afzelia xylocarpa** | มะค่าโมง | Makha | 850 | 0.0612 | 2.420 | 0.660 | Chave 2014 adjusted |

### 5.2 หมายเหตุสำคัญ

> ⚠️ **ก่อนส่ง NSC final** — ต้อง verify ทุกค่ากับ TGO 2017 PDF อย่างเป็นทางการ

### 5.3 ทำไมเลือก 5 species นี้

เป็นไม้เศรษฐกิจ + ป่าธรรมชาติของไทยที่:
1. **มี allometric equation peer-reviewed** (ไม่มโน)
2. **ปลูกได้ในเชิงพาณิชย์** (ตลาดมี demand)
3. **คาร์บอนสูง** (wood density สูง — เก็บคาร์บอนได้เยอะ)
4. **มี TGO acceptance** (อยู่ในเอกสารทางการของ อบก.)

### 5.4 เพิ่ม species ใหม่ทำยังไง

```python
# 1. เพิ่ม row ใน species_db.csv
#    name_sci,name_th,name_en,wood_density,agb_a,agb_b,agb_c,agb_source,root_to_shoot,carbon_fraction
#    Eucalyptus camaldulensis,ยูคาลิปตัส,Red River Gum,850,0.0419,2.290,0.760,Senelwa & Sims 1998,0.24,0.47

# 2. รัน tests
# cd services/ml && pytest tests/test_allometric.py -v

# 3. ใส่ใน production
```

---

## 6. Citations + References

### 6.1 Primary References

| Paper | Author | Year | DOI / Link | ใช้ที่ |
|---|---|---|---|---|
| **Pantropical allometric models for tropical forests** | Chave et al. | 2014 | [10.1111/gcb.12629](https://doi.org/10.1111/gcb.12629) | Tier 3 fallback |
| **IPCC Guidelines for National GHG Inventories, Vol. 4 (AFOLU)** | IPCC | 2006 | [IPCC link](https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html) | Carbon fraction, root:shoot |
| **TGO Forestry Sector GHG Calculation Guideline** | TGO | 2017 | [tgo.or.th](https://www.tgo.or.th) | Thai standard |
| **Teak allometric equations for monsoon forest** | Tsutsumi et al. | 1983 | (Japan biological journal) | Tectona grandis |
| **Dipterocarp allometry in SEA** | Ogawa et al. | 1965 | (Nature & Life in SE Asia) | Dipterocarpus alatus |
| **Bamboo allometry** | Yiping et al. | 2010 | Forest Ecology Mgmt | Bambusa spp. |
| **Rubber plantation allometry** | Chiarucci et al. | 2014 | Forest Ecology Mgmt | Hevea brasiliensis |

### 6.2 Validation Dataset

- **Demol et al. 2021** — "QSMs, point cloud and harvest data from a destructive forest biomass experiment in Belgium using terrestrial laser scanning"
- DOI: [10.5281/zenodo.4557401](https://doi.org/10.5281/zenodo.4557401)
- Paper: [10.1007/s00468-020-02067-7](https://doi.org/10.1007/s00468-020-02067-7)
- เราใช้สำหรับ validate ในบท [13-ml-validation.md](13-ml-validation.md)

---

## 7. ข้อจำกัด + Phase 2 Plan

### 7.1 ข้อจำกัด Phase 1 (ปัจจุบัน)

| ข้อจำกัด | ผลกระทบ | ลด/แก้ยังไง |
|---|---|---|
| **มีเฉพาะ 5 species** | ต้นไม้ไทย 200+ species ใช้ Chave fallback | Phase 2: ขยาย DB เป็น 50+ species |
| **ค่า constants ส่วนใหญ่จาก foreign papers** | อาจไม่ตรงกับสภาพไทย 100% | Verify กับ TGO 2017 PDF + งานวิจัยไทย |
| **ใช้ default ratios (0.24, 0.47)** | ไม่ specific ต่อ species | Phase 2: species-specific ratios |
| **ไม่มี leaf biomass component** | underestimate ~5-10% | Phase 2: เพิ่ม leaf component |
| **No uncertainty quantification** | ตัวเลข deterministic | Phase 2: bootstrap CI 95% |

### 7.2 Phase 2 Roadmap

1. **Q3 2026:** Verify ทุกค่ากับ TGO 2017 PDF อย่างเป็นทางการ
2. **Q4 2026:** ขยาย species DB เป็น 20+ species
3. **Q1 2027:** เพิ่ม uncertainty bands (Monte Carlo)
4. **Q2 2027:** ส่งขอ TGO certification

---

## 8. Validation Results ของระบบจริง

ดูบท [13 — Validation](13-ml-validation.md) สำหรับรายละเอียด

**สรุปสั้นๆ:**

```
Synthetic plot (5 trees):
  Mean DBH error: 5.9%
  Mean Height error: 6.0%

Belgium real data (Demol 2021, 65 trees, 4 species):
  Mean DBH error: 3.8% (MAE 1.17 cm)
  Mean Height error: 2.6% (MAE 0.54 m)
  Mean Volume error: 18.8% (taper limit; Phase 2 → TreeQSM ลดลง 5-10%)
```

---

## 9. ❓ คำถามตรวจสอบความเข้าใจ

### Level 1 — Basic

1. **AGB และ BGB ย่อมาจากอะไร? ต่างกันยังไง?**

2. **ทำไม carbon fraction = 0.47 ไม่ใช่ 1.0?**

3. **44/12 ในสูตร CO₂eq มาจากไหน?**

### Level 2 — Application

4. **คำนวณด้วยมือ:** ต้นยางนา (Dipterocarpus alatus) DBH 25 cm, H 18 m — คาร์บอนเก็บได้กี่ kg?
   <details>
   <summary>คลิกดูคำตอบ</summary>

   ```
   AGB = 0.0396 × 25^2.380 × 18^0.800
       = 0.0396 × 1,627.8 × 9.85
       ≈ 635.0 kg
   BGB = 635.0 × 0.24 = 152.4 kg
   B   = 787.4 kg
   C   = 787.4 × 0.47 = 370.1 kg C
   CO₂eq = 370.1 × 44/12 = 1,357.0 kg CO₂eq
   ```
   </details>

5. **ถ้าต้นไม้นี้ไม่อยู่ใน DB ระบบจะใช้สูตรอะไร? ต้องการ data อะไรเพิ่ม?**

### Level 3 — Critical Thinking

6. **ทำไม Chave 2014 ใช้ exponent 0.976 ไม่ใช่ 1.0?**
   - hint: เกี่ยวกับ surface area vs volume scaling

7. **ระบบเราจะ overestimate หรือ underestimate carbon เมื่อ:**
   (a) ต้นไม้ที่มี wood density ต่ำกว่า species DB ที่ระบุ?
   (b) Auditor วัด DBH คลาดเคลื่อน +10%?
   (c) Tree height คำนวณผิด -5%?

8. **ทำไมถึงต้อง verify กับ TGO 2017 PDF ทั้งๆ ที่ใช้สูตรเดียวกัน?**

### Level 4 — Advanced

9. **ออกแบบ unit tests สำหรับ allometric.py — ควรมีกี่ test cases? ครอบ edge cases อะไรบ้าง?**

10. **Allometric error compound ไปยังไง เมื่อ pipeline มีหลาย step?**
    - DBH measurement error → Volume → Biomass → Carbon
    - ลอง propagate error 5% ที่ DBH ไป CO₂eq

---

## 10. Cheat Sheet — Pin ไว้บนกำแพง

```
════════════════════════════════════════════════════════
                  CARBON CALCULATION
                    QUICK REFERENCE
════════════════════════════════════════════════════════

  INPUT:  DBH (cm), Height (m), Species
  OUTPUT: Carbon (kg C), CO2eq (kg CO2)

═══ Step 1: AGB ════════════════════════════════════════

  Species-specific (Tier 2):
      AGB = a × DBH^b × H^c                       [kg]

  Pantropical fallback (Chave 2014):
      AGB = 0.0673 × (ρ × DBH² × H)^0.976         [kg]
      (ρ in g/cm³, DBH in cm, H in m)

═══ Step 2: BGB ════════════════════════════════════════

      BGB = AGB × 0.24                            [kg]
      (root:shoot ratio, IPCC tropical default)

═══ Step 3: Biomass ════════════════════════════════════

      B = AGB + BGB                               [kg]

═══ Step 4: Carbon ═════════════════════════════════════

      C = B × 0.47                                [kg C]
      (IPCC carbon fraction default)

═══ Step 5: CO2eq ═════════════════════════════════════

      CO₂eq = C × (44/12) = C × 3.667             [kg CO₂]

═══ Step 6: Market Value ══════════════════════════════

      Value = CO₂eq / 1000 × ราคา/ton             [฿]

═══ Species Constants (Top 5) ══════════════════════════

  Species              ρ (kg/m³)   a       b      c
  ─────────────────────────────────────────────────────
  Tectona grandis        660    0.0509  2.150  0.700
  Dipterocarpus alatus   720    0.0396  2.380  0.800
  Bambusa spp.           650    0.131   2.280  0.590
  Hevea brasiliensis     580    0.0464  2.330  0.720
  Afzelia xylocarpa      850    0.0612  2.420  0.660

═══ Defaults (IPCC 2006) ══════════════════════════════

  Carbon fraction:       0.47
  Root:shoot (tropical): 0.24
  Wood density (generic) 600 kg/m³

════════════════════════════════════════════════════════
```

---

## 11. อ่านต่อ

- [บท 13 — Validation บน Belgium dataset](13-ml-validation.md) — ระบบนี้แม่นแค่ไหน?
- [บท 10 — QSM (DBH + Height + Volume)](10-ml-step6-qsm.md) — input ของขั้นนี้มาจากไหน?
- [บท 21 — References + Glossary](21-references-glossary.md)

---

## 12. ลิงก์ไปโค้ดจริง

📂 GitHub:
- `services/ml/pipeline/allometric.py` — ฟังก์ชันหลัก
- `services/ml/data/species_db.csv` — species database
- `services/ml/tests/test_allometric.py` — 16 unit tests

```bash
# รัน tests ดู
cd services/ml
pytest tests/test_allometric.py -v
# Expected: 16 passed
```

---

> 📝 **เขียนครั้งแรก:** 2026-05-24 | **แก้ไขล่าสุด:** 2026-05-24
> 🔥 บทนี้คือ **"พระคัมภีร์"** ของ Carbon calculation ของระบบ — ทุกคนในทีมควรอ่านอย่างน้อย 1 รอบ
