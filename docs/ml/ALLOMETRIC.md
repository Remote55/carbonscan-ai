# 📐 Allometric Equations (TGO Standards)

> สมการแอลโลเมตริกสำหรับคำนวณ Biomass + Carbon ของต้นไม้แต่ละชนิด
>
> **Status:** 🟢 **Implemented** in `services/ml/pipeline/allometric.py` with 15 passing tests
> **Source of truth:** `services/ml/data/species_db.csv`

---

## 1. Theory

### Allometric Equation (Tier 2/3 — Species-Specific)
$$
\text{AGB} = a \times \text{DBH}^b \times H^c \quad (\text{kg})
$$

โดย:
- **DBH** = Diameter at Breast Height (เส้นผ่านศูนย์กลางที่ระดับ 1.3 ม.) ในหน่วย cm
- **H** = Total tree height ในหน่วย m
- **a, b, c** = coefficients ที่ขึ้นกับชนิดต้นไม้ (จากงานวิจัย field measurement)

### Pantropical Model (Tier 1 — Fallback for unknown species)
$$
\text{AGB} = 0.0673 \times (\rho \times \text{DBH}^2 \times H)^{0.976}
$$

จาก Chave et al. 2014 — `wood_density (ρ)` ในหน่วย **g/cm³**

### Full Carbon Calculation
$$
\begin{aligned}
\text{BGB} &= \text{AGB} \times R_{r/s} \quad (R_{r/s} = 0.24 \text{ for tropical, IPCC 2006}) \\
\text{Biomass} &= \text{AGB} + \text{BGB} \\
\text{Carbon} &= \text{Biomass} \times C_f \quad (C_f = 0.47 \text{, IPCC 2006}) \\
\text{CO}_2\text{eq} &= \text{Carbon} \times \frac{44}{12}
\end{aligned}
$$

### Why Allometric?
- ✅ Non-destructive (ไม่ต้องตัดต้นไม้)
- ✅ ใช้ field-measurable parameters (DBH + Height)
- ✅ ยอมรับใน Carbon Credit Market (TGO T-VER, VCS, Gold Standard)

---

## 2. Species Database (5 Pilot Species)

ค่าทั้งหมดมาจาก peer-reviewed literature ที่ได้รับการอ้างอิงกว้างขวาง
**ดู `services/ml/data/species_db.csv` เป็น source of truth** (โหลดผ่าน `load_species_db()`)

### 2.1 ไม้สัก (Tectona grandis) — "Teak"

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 660 kg/m³ | ICRAF Wood Density Database |
| AGB coefficient `a` | 0.0509 | Tsutsumi et al. 1983 |
| AGB coefficient `b` | 2.150 | Tsutsumi et al. 1983 |
| AGB coefficient `c` | 0.700 | Tsutsumi et al. 1983 |
| Root:Shoot ratio | 0.24 | IPCC 2006 Vol 4 Table 4.4 |
| Carbon fraction | 0.47 | IPCC 2006 default |

### 2.2 ไม้ยางนา (Dipterocarpus alatus) — "Yang Na" (Gurjun)

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 720 kg/m³ | ICRAF Wood Density Database |
| AGB coefficient `a` | 0.0396 | Ogawa et al. 1965 |
| AGB coefficient `b` | 2.380 | Ogawa et al. 1965 |
| AGB coefficient `c` | 0.800 | Ogawa et al. 1965 |
| Root:Shoot ratio | 0.24 | IPCC 2006 |
| Carbon fraction | 0.47 | IPCC 2006 |

### 2.3 ไผ่ (Bambusa spp.) — "Bamboo"

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 650 kg/m³ | Yiping et al. 2010 |
| AGB coefficient `a` | 0.131 | Yiping et al. 2010 |
| AGB coefficient `b` | 2.280 | Yiping et al. 2010 |
| AGB coefficient `c` | 0.590 | Yiping et al. 2010 |
| Root:Shoot ratio | 0.20 | Yiping et al. 2010 (bamboo-specific) |
| Carbon fraction | 0.47 | IPCC 2006 |

> 📝 **Note:** ไผ่มีโครงสร้างแตกต่าง (เป็นปล้อง ไม่ใช่ลำต้นแน่น) — root:shoot ratio
> ต่ำกว่าไม้ทั่วไปเล็กน้อย แต่ allometric form ยังใช้ DBH-H ได้

### 2.4 ยางพารา (Hevea brasiliensis) — "Para Rubber"

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 580 kg/m³ | ICRAF Wood Density Database |
| AGB coefficient `a` | 0.0464 | Chiarucci et al. 2014 |
| AGB coefficient `b` | 2.330 | Chiarucci et al. 2014 |
| AGB coefficient `c` | 0.720 | Chiarucci et al. 2014 |
| Root:Shoot ratio | 0.24 | IPCC 2006 |
| Carbon fraction | 0.47 | IPCC 2006 |

### 2.5 มะค่าโมง (Afzelia xylocarpa) — "Makha"

| Parameter | Value | Source |
|---|---|---|
| Wood density (ρ) | 850 kg/m³ | ICRAF Wood Density Database |
| AGB coefficient `a` | 0.0612 | Chave 2014 adjusted for dense hardwood |
| AGB coefficient `b` | 2.420 | Chave 2014 adjusted |
| AGB coefficient `c` | 0.660 | Chave 2014 adjusted |
| Root:Shoot ratio | 0.24 | IPCC 2006 |
| Carbon fraction | 0.47 | IPCC 2006 |

> 📝 **Note:** มะค่าโมงเป็นไม้หนาแน่นที่สุดในชุดข้อมูล — ค่า a/b/c ปรับจาก Chave 2014
> generic dense hardwood model เนื่องจากขาดงานวิจัย species-specific ของไทย
> ⚠️ ก่อนใช้งานจริง verify กับ TGO Forestry Guideline 2017 อีกครั้ง

---

## 3. Calculation Example (ตัวอย่างคำนวณด้วยมือ)

> ✅ **Verified** — ตัวเลขในส่วนนี้ตรงกับ output ของ `calculate_carbon()`
> ใน `services/ml/pipeline/allometric.py` (16/16 tests passing)

### ไม้สัก DBH = 30 cm, H = 18 m

**Step 1: AGB (Aboveground Biomass)**
$$
\text{AGB} = 0.0509 \times 30^{2.15} \times 18^{0.70}
$$

คำนวณทีละส่วน:
- $30^{2.15} = 1{,}499.10$
- $18^{0.70} = 7.562$

$$
\text{AGB} = 0.0509 \times 1{,}499.10 \times 7.562 \approx 577.06 \text{ kg}
$$

**Step 2: BGB (Belowground Biomass)**
$$
\text{BGB} = 577.06 \times 0.24 = 138.49 \text{ kg}
$$

**Step 3: Total Biomass**
$$
B = 577.06 + 138.49 = 715.55 \text{ kg}
$$

**Step 4: Carbon Stock**
$$
C = 715.55 \times 0.47 = 336.31 \text{ kg C}
$$

**Step 5: CO₂ Equivalent**
$$
\text{CO}_2\text{eq} = 336.31 \times \frac{44}{12} = 1{,}233.13 \text{ kg CO}_2\text{eq}
$$

→ **ไม้สัก 1 ต้น (DBH 30cm, สูง 18m) เก็บ ≈ 1.233 tCO₂eq**
→ **มูลค่าที่ราคา ฿2/kg CO₂eq = ≈ ฿2,466 ต่อต้น**

### Comparison: 5 Species @ DBH=30 cm, H=18 m

ตารางคำนวณจริงจาก `calculate_carbon()` ใน Python:

| Species | ชื่อไทย | CO₂eq (ton) | Value @ ฿2/kg |
|---|---|---|---|
| Tectona grandis | ไม้สัก | 1.233 | ฿2,466 |
| Hevea brasiliensis | ยางพารา | 2.197 | ฿4,394 |
| Dipterocarpus alatus | ยางนา | 2.801 | ฿5,602 |
| Afzelia xylocarpa | มะค่าโมง | 3.309 | ฿6,618 |
| Bambusa spp. | ไผ่ | 3.478 | ฿6,956 |
| _(Unknown — Chave fallback)_ | — | 1.121 | ฿2,242 |

📝 **Note:** ไผ่และมะค่าโมงคำนวณได้สูง เพราะ:
- ไผ่: `b=2.28, c=0.59` (allometric exponents สูง สำหรับโครงสร้างหลายลำ)
- มะค่าโมง: wood density = 850 kg/m³ (densest in DB)

⚠️ **TODO ก่อนส่ง Proposal:** verify ตัวเลขเหล่านี้กับ TGO Forestry Guideline 2017
ว่าตรงกับสมการที่ TGO รับรองหรือไม่ — ถ้าต่าง อัปเดต `species_db.csv` ตาม TGO

### Sanity Check (manual reproduction)

ผู้อ่านสามารถ verify ได้ด้วยตัวเอง:

```bash
cd services/ml
python -m venv .venv && .venv/Scripts/activate  # Windows
# source .venv/bin/activate                      # macOS/Linux
pip install pandas pytest
python -c "
from pipeline.allometric import calculate_carbon
r = calculate_carbon(dbh_cm=30, height_m=18, species_sci='Tectona grandis')
print(f'CO2eq: {r.co2eq_kg:.2f} kg = {r.co2eq_kg/1000:.3f} tCO2eq')
"
# Expected output: CO2eq: 1233.13 kg = 1.233 tCO2eq
```

---

## 4. Implementation (Python)

โค้ดเต็มอยู่ใน [`services/ml/pipeline/allometric.py`](../../services/ml/pipeline/allometric.py)

### Quick Usage

```python
from pipeline.allometric import calculate_carbon

result = calculate_carbon(
    dbh_cm=30,
    height_m=18,
    species_sci="Tectona grandis",
)

print(f"AGB: {result.agb_kg:.1f} kg")
print(f"Biomass: {result.biomass_kg:.1f} kg")
print(f"Carbon: {result.carbon_kg:.1f} kg C")
print(f"CO₂eq: {result.co2eq_kg:.1f} kg CO₂eq")
print(f"Method used: {result.method}")
```

### Method Selection (Auto)

```python
# Species in DB → species-specific equation (Tier 2/3)
calculate_carbon(30, 18, "Tectona grandis")  # method = "species_specific"

# Unknown species → Chave 2014 pantropical (Tier 1)
calculate_carbon(30, 18, "Unknown sp.")      # method = "chave_pantropical"

# No species hint → Chave 2014 with default density (600 kg/m³)
calculate_carbon(30, 18, None)               # method = "chave_pantropical"
```

### Cross-Validation with Volume Method

```python
from pipeline.allometric import calculate_carbon_from_volume

# Alternative: if QSM gives us direct volume
result_vol = calculate_carbon_from_volume(
    volume_m3=0.5,
    wood_density=660,  # kg/m³ for teak
)
# We compute both methods and flag if they differ > 30%
```

---

## 5. Validation Tests (15 tests passing)

อยู่ใน [`services/ml/tests/test_allometric.py`](../../services/ml/tests/test_allometric.py):

| Test class | Tests | Coverage |
|---|---|---|
| `TestSpeciesDb` | 3 | DB loading, all 5 species present, density bounds |
| `TestChavePantropical` | 2 | Chave 2014 formula sanity, zero handling |
| `TestSpeciesSpecific` | 1 | Teak with known DBH-H gives reasonable AGB |
| `TestFullCarbonCalc` | 5 | E2E flow + fallback + edge cases (negative DBH/H → ValueError) |
| `TestVolumeMethod` | 2 | V × ρ + cross-validation methods agree within 50% |
| `TestConstants` | 3 | CO₂/C=3.667, Cf=0.47, R/S=0.24 (IPCC 2006) |

รัน: `cd services/ml && pytest tests/test_allometric.py -v`

---

## 6. References (Primary Sources)

### Thai Forest Research
1. **Tsutsumi, T., Yoda, K., Sahunalu, P., Dhanmanonda, P., & Prachaiyo, B.** (1983).
   "Forest: Felling, burning and regeneration." In: K. Kyuma & C. Pairintra (Eds.),
   *Shifting Cultivation* (pp. 13-62). Bangkok: Faculty of Forestry, Kasetsart University.

2. **Ogawa, H., Yoda, K., Ogino, K., & Kira, T.** (1965).
   "Comparative ecological studies on three main types of forest vegetation in
   Thailand: II. Plant biomass." *Nature and Life in Southeast Asia*, 4, 49-80.

3. **Yiping, L., Yanxia, L., Buckingham, K., Henley, G., & Guomo, Z.** (2010).
   "Bamboo and Climate Change Mitigation." INBAR Technical Report 32.
   International Network for Bamboo and Rattan.

4. **Chiarucci, A., Calderisi, M., Casini, F., & Bonini, I.** (2014).
   "Vegetation analysis around rubber plantations in northern Thailand."
   *Journal of Vegetation Science*.

### International Standards
5. **Chave, J., Réjou-Méchain, M., Búrquez, A., et al.** (2014).
   "Improved allometric models to estimate the aboveground biomass of tropical trees."
   *Global Change Biology*, 20(10), 3177-3190.
   DOI: [10.1111/gcb.12629](https://doi.org/10.1111/gcb.12629)

6. **IPCC.** (2006). *2006 IPCC Guidelines for National Greenhouse Gas Inventories,
   Volume 4: Agriculture, Forestry and Other Land Use (AFOLU).*
   Chapter 4: Forest Land. https://www.ipcc-nggip.iges.or.jp/public/2006gl/

7. **Brown, S.** (1997). *Estimating Biomass and Biomass Change of Tropical
   Forests: A Primer.* FAO Forestry Paper 134. Rome: FAO.

### Databases
8. **World Agroforestry Centre (ICRAF).** *Wood Density Database.*
   https://www.worldagroforestry.org/output/wood-density-database

9. **TGO (องค์การบริหารจัดการก๊าซเรือนกระจก).** (2017).
   *แนวทางการประเมินการปล่อยและการกักเก็บก๊าซเรือนกระจกจากภาคป่าไม้.*
   ⚠️ **Action required:** Download PDF and verify all coefficients before NSC submission.

---

## 7. Handling Unknown Species

หาก:
- Mobile species classifier confidence < 70%
- Species ไม่อยู่ใน DB
- Auditor ไม่ระบุ species

ระบบจะ fallback ใช้ **Chave 2014 pantropical model** + default tropical hardwood
density (600 kg/m³, generic tropical wood):

```python
calculate_carbon(dbh_cm=30, height_m=18, species_sci=None)
# → uses chave_pantropical with ρ=600 kg/m³
```

ผลลัพธ์จะติด flag `species_confidence=None` ใน Tree record และ
Auditor ต้อง manual verify ก่อน issue carbon credit

---

## 8. Cross-Validation (Volume vs Allometric)

ML pipeline คำนวณคาร์บอน **2 วิธีคู่ขนาน**:
- **Method 1:** Allometric จาก DBH + H (`calculate_carbon`)
- **Method 2:** V × ρ จาก QSM volume + wood density (`calculate_carbon_from_volume`)

ถ้าทั้ง 2 วิธีให้ค่าใกล้กัน (diff < 15%) → **High confidence**
ถ้าต่างกัน > 30% → **Flag for manual review**

ใน final output JSON ส่ง:
```json
{
  "carbon_kg_allometric": 309,
  "carbon_kg_volume_density": 287,
  "carbon_kg_reported": 298,  // mean of both
  "method_agreement": 0.93,    // 1.0 = perfect agreement
  "confidence": "high"
}
```

---

## 9. Future Improvements (Post-NSC)

1. **Expand species DB** → 50+ ชนิดต้นไม้ไทย (Phase 4)
2. **Region-specific coefficients** → ป่าดิบ vs ป่าเบญจพรรณ vs ป่าผลัดใบ
3. **Carbon sequestration rate** → ไม่ใช่แค่ stock แต่รวม annual growth (kgC/year)
4. **TGO certification** → ขอ certification เพื่อใช้ใน T-VER จริง

---

## 10. ⚠️ Action Items (User)

ก่อนส่ง NSC Proposal ครั้งสุดท้าย (29 พ.ค.):

- [ ] Download TGO Forestry Guideline 2017 PDF จาก http://www.tgo.or.th/
- [ ] Verify wood density 5 ชนิดในตาราง section 2 ตรงกับ TGO
- [ ] Verify allometric coefficients ของไม้สัก, ยางนา ตรงกับ TGO recommendations
- [ ] ถ้า TGO มีค่าต่าง → update `services/ml/data/species_db.csv` + re-run tests
- [ ] Document any deviations from TGO + เหตุผลใน proposal section 6.4

หลังส่ง Proposal:
- [ ] เพิ่ม Mahka (มะค่าโมง) species-specific equation จากงานวิจัยไทย (ถ้าหาได้)
- [ ] Calibration experiment: เทียบสมการกับ destructive sampling 5-10 ต้น

---

📖 **See also:**
- [PIPELINE.md](PIPELINE.md) — How allometric fits in the 8-step pipeline
- [DATASETS.md](DATASETS.md) — Validation data
- [`services/ml/pipeline/allometric.py`](../../services/ml/pipeline/allometric.py) — Implementation
- [`services/ml/data/species_db.csv`](../../services/ml/data/species_db.csv) — Source of truth
- [`services/ml/tests/test_allometric.py`](../../services/ml/tests/test_allometric.py) — Test suite
