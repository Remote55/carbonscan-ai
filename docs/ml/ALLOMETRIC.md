# 📐 Allometric Equations (TGO Standards)

> สมการแอลโลเมตริกสำหรับคำนวณ Biomass + Carbon ของต้นไม้แต่ละชนิด
>
> **Owner:** User
> **Status:** ⚠️ ต้อง research เพิ่มเติม — current values เป็น placeholder จากงานวิจัย

---

## Theory

### Allometric Equation
$$
\text{Biomass} = a \times \text{DBH}^b \times H^c
$$

โดย:
- **DBH** = Diameter at Breast Height (เส้นผ่านศูนย์กลางที่ระดับ 1.3 ม.) ในหน่วย cm
- **H** = Total tree height ในหน่วย m
- **a, b, c** = coefficients ขึ้นกับชนิดต้นไม้

### Why Allometric?
- ไม่ต้องตัดต้นไม้เพื่อชั่ง (non-destructive)
- ใช้ field-measurable parameters
- ได้รับการยอมรับใน Carbon Credit Market (TGO, VCS, Gold Standard)

---

## Species Database (5 Pilot Species)

⚠️ **Values below ต้อง verify จาก TGO Forestry Sector Guideline 2017**
⚠️ **User ต้อง download official PDF และอัปเดตค่าก่อน Proposal submit**

### 1. ไม้สัก (Tectona grandis)

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 650 kg/m³ | TGO 2017 |
| AGB coefficient `a` | 0.0673 | TGO 2017 (verify) |
| AGB coefficient `b` | 2.43 | TGO 2017 (verify) |
| AGB coefficient `c` | 0.65 | TGO 2017 (verify) |
| Root:Shoot ratio | 0.25 | IPCC 2006 |
| Carbon fraction | 0.47 | IPCC 2006 |

### 2. ไม้ยางนา (Dipterocarpus alatus)

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 620 kg/m³ | TGO 2017 |
| AGB coefficient `a` | 0.0509 | (placeholder — verify) |
| AGB coefficient `b` | 2.35 | (placeholder — verify) |
| AGB coefficient `c` | 0.72 | (placeholder — verify) |
| Root:Shoot ratio | 0.25 | IPCC 2006 |
| Carbon fraction | 0.47 | IPCC 2006 |

### 3. ไผ่ (Bambusa spp.)

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 500 kg/m³ | (placeholder) |
| AGB coefficient `a` | 0.131 | (placeholder) |
| AGB coefficient `b` | 2.28 | (placeholder) |
| AGB coefficient `c` | 0.59 | (placeholder) |
| Note | ไผ่ใช้สูตรพิเศษ (มีปล้อง) | — |

⚠️ ไผ่อาจต้องใช้ allometric แบบพิเศษ — research เพิ่ม

### 4. ยางพารา (Hevea brasiliensis)

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 580 kg/m³ | (placeholder) |
| AGB coefficient `a` | 0.058 | (placeholder) |
| AGB coefficient `b` | 2.39 | (placeholder) |
| AGB coefficient `c` | 0.68 | (placeholder) |

### 5. มะค่าโมง (Afzelia xylocarpa)

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 750 kg/m³ | (placeholder) |
| AGB coefficient `a` | 0.067 | (placeholder) |
| AGB coefficient `b` | 2.42 | (placeholder) |
| AGB coefficient `c` | 0.66 | (placeholder) |

---

## Calculation Example

### ไม้สัก DBH = 30 cm, H = 18 m

**Step 1: AGB**
$$
\text{AGB} = 0.0673 \times 30^{2.43} \times 18^{0.65} \\
\text{AGB} = 0.0673 \times 4291.8 \times 6.94 \\
\text{AGB} \approx 2003 \text{ kg}
$$

**Step 2: BGB**
$$
\text{BGB} = 2003 \times 0.25 = 501 \text{ kg}
$$

**Step 3: Total Biomass**
$$
B = 2003 + 501 = 2504 \text{ kg}
$$

**Step 4: Carbon**
$$
C = 2504 \times 0.47 = 1177 \text{ kg C}
$$

**Step 5: CO2 equivalent**
$$
\text{CO}_2\text{eq} = 1177 \times \frac{44}{12} = 4316 \text{ kg CO}_2\text{eq}
$$

→ **ไม้สัก 1 ต้น (DBH 30cm, สูง 18m) เก็บ ~4.3 tCO₂eq**
→ **มูลค่าที่ราคา ฿2/kg = ~฿8,632**

---

## Alternative: Volume-Based

ถ้าเรามีปริมาตรไม้ (V) จาก QSM:
$$
B = V \times \rho \quad (\text{kg})
$$

Then continue: $C = B \times 0.47$, $\text{CO}_2\text{eq} = C \times 44/12$

### Cross-validation
เราคำนวณทั้ง 2 วิธี → เปรียบเทียบ:
- ถ้าใกล้กัน (diff < 15%) → confidence สูง
- ถ้าต่างมาก → flag for manual review

---

## Confidence Levels

| Method | Confidence | Use When |
|---|---|---|
| Volume-based (QSM) | High | มี clean LiDAR scan |
| Allometric (DBH + H) | Medium-High | DBH/H วัดได้ดี |
| Mean of both | Highest | ทั้ง 2 ใกล้กัน |

---

## Sources & References

### Primary (ต้อง download + read)
1. **TGO (อบก.) Forestry Sector Greenhouse Gas Emission Calculation Guideline 2017**
   - URL: http://www.tgo.or.th/2020/index.php/th/page/แนวทางการประเมิน (TBD)
   - PDF: เก็บไว้ใน `proposal/references/tgo-forestry-guideline-2017.pdf`

2. **IPCC Guidelines for National Greenhouse Gas Inventories 2006**
   - Volume 4: Agriculture, Forestry and Other Land Use (AFOLU)
   - URL: https://www.ipcc-nggip.iges.or.jp/public/2006gl/

### Secondary
3. Chave et al. 2014: "Improved allometric models to estimate the aboveground biomass of tropical trees"
4. Brown 1997: "Estimating Biomass and Biomass Change of Tropical Forests"

### Wood Density Database
5. **World Agroforestry Centre (ICRAF) Wood Density Database**
   - URL: https://www.worldagroforestry.org/output/wood-density-database

### Thailand-specific Research
6. Khun, K. et al. (Mahidol University) — research on Thai forest biomass
7. คณะวนศาสตร์ ม.เกษตรศาสตร์ — papers on forest carbon

---

## Implementation Notes

### Code Location
- DB: `services/api/migrations/` (insert seed data)
- Logic: `services/ml/pipeline/allometric.py`
- DB schema: `species_db` table (see [DATA_MODEL.md](../DATA_MODEL.md))

### Loading Data
```python
import pandas as pd

SPECIES_DB = pd.read_csv("services/ml/data/species_db.csv").set_index("name_sci")

def get_species_params(species_sci: str) -> pd.Series:
    return SPECIES_DB.loc[species_sci]
```

### Handling Unknown Species
ถ้า classifier confidence < 70% หรือ species ไม่อยู่ใน DB:
- Fall back to **generic tropical broadleaf** equation (Chave 2014):
  $$\text{AGB} = 0.0673 \times (\rho \times \text{DBH}^2 \times H)^{0.976}$$
- Flag `species_confidence` ใน output

---

## Future Improvements

1. **Expand species DB** — รองรับ 50+ ชนิดต้นไม้ไทย (Phase 4)
2. **Region-specific coefficients** — ป่าดิบ vs ป่าเบญจพรรณ vs ป่าผลัดใบ (different climate factors)
3. **Carbon sequestration rate** — ไม่ใช่แค่ stock แต่รวม growth rate (kgC/year)

---

## ⚠️ Action Items (User)

- [ ] Download TGO Forestry Guideline 2017 PDF (research ก่อน 22 พ.ค.)
- [ ] Verify values ในตาราง 5 ชนิดข้างต้น
- [ ] Update `species_db.csv`
- [ ] Document each equation with proper citation
- [ ] Email อาจารย์ขอ feedback equations (ถ้าจำเป็น)

---

📖 **See also:**
- [PIPELINE.md](PIPELINE.md) — How allometric fits in pipeline
- [DATASETS.md](DATASETS.md) — Validation data
- [docs/DATA_MODEL.md](../DATA_MODEL.md) — DB schema for species_db
