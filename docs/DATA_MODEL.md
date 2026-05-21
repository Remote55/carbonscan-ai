# 🗄 Data Model

> Database schema, relationships, and design rationale

**Database:** PostgreSQL 16 + PostGIS 3.4 (hosted on Supabase)

---

## Entity Relationship Diagram

```
┌──────────────┐         ┌──────────────┐
│    users     │◄────────│    plots     │
│              │ 1     N │              │
└──────┬───────┘         └──────┬───────┘
       │ 1                      │ 1
       │                        │
       │ N                      │ N
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│    jobs      │         │    trees     │
│              │         │              │
└──────────────┘         └──────┬───────┘
                                │ 1
                                │
                                │ N
                                ▼
                         ┌──────────────┐
                         │ transactions │
                         │              │
                         └──────────────┘

         ┌──────────────┐
         │  species_db  │  (reference table — wood density, allometric coeffs)
         │              │
         └──────────────┘
```

---

## Tables

### `users`
ผู้ใช้ระบบ — Community, Industrial, Auditor, Admin

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT NOT NULL CHECK (role IN ('community', 'industrial', 'auditor', 'admin')),
    organization TEXT,
    phone TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

**Notes:**
- ใช้ Supabase Auth สำหรับ password (เก็บแยกใน `auth.users`)
- `role` กำหนด permissions:
  - `community` — เกษตรกร/ชุมชน, อัปโหลดต้นไม้ของตัวเอง
  - `industrial` — โรงงาน, ซื้อ carbon credits
  - `auditor` — ตรวจสอบ + อนุมัติ
  - `admin` — เต็มสิทธิ์

---

### `plots`
แปลงที่ดิน/ป่า

```sql
CREATE TABLE plots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    area_hectare FLOAT GENERATED ALWAYS AS (ST_Area(geometry::geography) / 10000) STORED,
    province TEXT,
    district TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_plots_owner ON plots(owner_id);
CREATE INDEX idx_plots_geometry ON plots USING GIST(geometry);
CREATE INDEX idx_plots_province ON plots(province);
```

**Notes:**
- `geometry` ใช้ SRID 4326 (WGS84 standard for GPS)
- `area_hectare` คำนวณอัตโนมัติ (generated column)

---

### `trees`
ต้นไม้แต่ละต้น (Core table)

```sql
CREATE TABLE trees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plot_id UUID REFERENCES plots(id) ON DELETE SET NULL,
    owner_id UUID NOT NULL REFERENCES users(id),

    -- Identification
    species_name_th TEXT,
    species_name_sci TEXT REFERENCES species_db(name_sci),
    species_confidence FLOAT,  -- 0.0 - 1.0 from AI classifier

    -- Location
    location GEOMETRY(POINT, 4326) NOT NULL,
    elevation_m FLOAT,

    -- Measurements
    dbh_cm FLOAT NOT NULL,
    height_m FLOAT NOT NULL,
    crown_radius_m FLOAT,

    -- Computed values
    volume_m3 FLOAT,
    biomass_kg FLOAT,
    carbon_kg FLOAT,
    co2eq_kg FLOAT,

    -- Source
    source_type TEXT NOT NULL CHECK (source_type IN ('lidar', 'photogrammetry', 'manual')),
    point_cloud_url TEXT,
    job_id UUID REFERENCES jobs(id),

    -- Verification
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMPTZ,

    -- Marketplace
    is_available BOOLEAN DEFAULT TRUE,  -- ยังไม่ถูกขาย
    price_per_co2eq_kg FLOAT DEFAULT 2.0,  -- THB

    scanned_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trees_plot ON trees(plot_id);
CREATE INDEX idx_trees_owner ON trees(owner_id);
CREATE INDEX idx_trees_location ON trees USING GIST(location);
CREATE INDEX idx_trees_species ON trees(species_name_sci);
CREATE INDEX idx_trees_available ON trees(is_available) WHERE is_available = TRUE;
```

**Notes:**
- `species_confidence` มาจาก AI classifier (RGB) — ถ้า < 0.7 ต้อง manual verify
- `source_type`:
  - `lidar` — จากไฟล์ .las/.laz
  - `photogrammetry` — จากการ reconstruct รูปถ่าย
  - `manual` — กรอกเอง (Phase 4+)
- `is_available = FALSE` หลังขายแล้วทั้งหมด

---

### `jobs`
งาน async processing (LAS pipeline หรือ Photogrammetry)

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    plot_id UUID REFERENCES plots(id),

    type TEXT NOT NULL CHECK (type IN ('las_upload', 'photogrammetry')),
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')),

    input_url TEXT NOT NULL,  -- Supabase Storage URL
    output_url TEXT,          -- .ply (point cloud) + result.json

    progress INT DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    current_stage TEXT,       -- e.g., 'wood_leaf_segmentation'

    -- Stats
    total_trees_detected INT,
    total_carbon_kg FLOAT,

    error_message TEXT,
    error_traceback TEXT,

    -- Worker tracking
    worker_id TEXT,
    gpu_seconds_used FLOAT,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created ON jobs(created_at DESC);
```

---

### `transactions`
ประวัติการซื้อ-ขาย carbon credits

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    buyer_id UUID NOT NULL REFERENCES users(id),
    seller_id UUID NOT NULL REFERENCES users(id),  -- owner of tree
    tree_id UUID NOT NULL REFERENCES trees(id),

    co2eq_kg FLOAT NOT NULL,
    price_per_kg_thb FLOAT NOT NULL,
    total_amount_thb FLOAT GENERATED ALWAYS AS (co2eq_kg * price_per_kg_thb) STORED,

    -- Payment
    payment_provider TEXT,    -- 'stripe' | 'omise' | 'bank_transfer'
    payment_status TEXT DEFAULT 'pending'
        CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
    payment_reference TEXT,

    -- Certificate
    certificate_url TEXT,     -- PDF certificate
    certificate_serial TEXT UNIQUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_tx_buyer ON transactions(buyer_id);
CREATE INDEX idx_tx_seller ON transactions(seller_id);
CREATE INDEX idx_tx_tree ON transactions(tree_id);
CREATE INDEX idx_tx_status ON transactions(payment_status);
```

---

### `species_db` (Reference Data)
สมการแอลโลเมตริก + ความหนาแน่นเนื้อไม้

```sql
CREATE TABLE species_db (
    name_sci TEXT PRIMARY KEY,
    name_th TEXT NOT NULL,
    name_en TEXT,
    family TEXT,

    -- Wood Density (kg/m³)
    wood_density FLOAT NOT NULL,
    wood_density_source TEXT,

    -- Allometric Equation: Biomass = a × DBH^b × H^c
    -- Aboveground biomass (AGB) in kg
    agb_a FLOAT,
    agb_b FLOAT,
    agb_c FLOAT,
    agb_source TEXT,

    -- Belowground (root) biomass coefficient
    root_to_shoot_ratio FLOAT DEFAULT 0.25,

    -- Carbon fraction (default IPCC 0.47)
    carbon_fraction FLOAT DEFAULT 0.47,

    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sample data (Phase 0 deliverable)
-- จะเติมหลัง User research จาก TGO
INSERT INTO species_db (name_sci, name_th, wood_density, agb_a, agb_b, agb_c, agb_source) VALUES
('Tectona grandis', 'สัก', 650, 0.0673, 2.43, 0.65, 'TGO 2017'),
('Dipterocarpus alatus', 'ยางนา', 620, 0.0509, 2.35, 0.72, 'TGO 2017'),
('Bambusa spp.', 'ไผ่', 500, 0.131, 2.28, 0.59, 'TGO 2017'),
('Hevea brasiliensis', 'ยางพารา', 580, 0.058, 2.39, 0.68, 'Research paper xxx'),
('Afzelia xylocarpa', 'มะค่าโมง', 750, 0.067, 2.42, 0.66, 'Research paper xxx');
```

---

### Indexes Summary
```sql
-- Performance-critical indexes
CREATE INDEX idx_trees_location ON trees USING GIST(location);
CREATE INDEX idx_plots_geometry ON plots USING GIST(geometry);
CREATE INDEX idx_jobs_status_created ON jobs(status, created_at DESC);
CREATE INDEX idx_trees_available ON trees(is_available) WHERE is_available = TRUE;
```

---

## Triggers

### Auto-update `updated_at`
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plots_updated_at BEFORE UPDATE ON plots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trees_updated_at BEFORE UPDATE ON trees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Auto-calculate carbon when tree updated
```sql
CREATE OR REPLACE FUNCTION calculate_tree_carbon()
RETURNS TRIGGER AS $$
DECLARE
    sp species_db%ROWTYPE;
BEGIN
    SELECT * INTO sp FROM species_db WHERE name_sci = NEW.species_name_sci;

    IF sp IS NOT NULL AND NEW.dbh_cm IS NOT NULL AND NEW.height_m IS NOT NULL THEN
        -- AGB = a × DBH^b × H^c
        NEW.biomass_kg = sp.agb_a * POWER(NEW.dbh_cm, sp.agb_b) * POWER(NEW.height_m, sp.agb_c);
        -- Add belowground biomass
        NEW.biomass_kg = NEW.biomass_kg * (1 + sp.root_to_shoot_ratio);
        -- Carbon = biomass × carbon fraction
        NEW.carbon_kg = NEW.biomass_kg * sp.carbon_fraction;
        -- CO2 equivalent (44/12)
        NEW.co2eq_kg = NEW.carbon_kg * 3.667;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_tree_carbon_trigger BEFORE INSERT OR UPDATE ON trees
    FOR EACH ROW EXECUTE FUNCTION calculate_tree_carbon();
```

---

## Common Queries

### หาต้นไม้ที่อยู่ใน radius 5km
```sql
SELECT * FROM trees
WHERE ST_DWithin(
    location::geography,
    ST_MakePoint(98.9853, 18.7883)::geography,  -- เชียงใหม่
    5000  -- 5 km in meters
);
```

### Carbon รวมของแปลง
```sql
SELECT
    p.name,
    p.area_hectare,
    COUNT(t.id) AS tree_count,
    SUM(t.carbon_kg) / 1000 AS total_carbon_tonnes,
    SUM(t.co2eq_kg) / 1000 AS total_co2eq_tonnes
FROM plots p
LEFT JOIN trees t ON ST_Contains(p.geometry, t.location)
WHERE p.id = $1
GROUP BY p.id;
```

### Marketplace listings พร้อมขาย
```sql
SELECT
    t.id, t.species_name_th, t.dbh_cm, t.height_m, t.co2eq_kg,
    t.price_per_co2eq_kg,
    u.organization AS owner_org,
    ST_AsGeoJSON(t.location) AS location_geojson
FROM trees t
JOIN users u ON t.owner_id = u.id
WHERE t.is_available = TRUE
    AND t.verified_at IS NOT NULL
ORDER BY t.co2eq_kg DESC
LIMIT 20;
```

---

## Migrations Strategy

ใช้ **Alembic** สำหรับ schema migrations:

```bash
cd services/api
alembic init alembic
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

แต่ละ migration เป็น Python script ใน `alembic/versions/`

---

## Backup Strategy

- **Production:** Supabase auto daily backup (7 days retention)
- **Pre-major-changes:** Manual snapshot
- **Critical:** `transactions` table → daily export to S3 separate bucket

---

📖 **See also:**
- [services/api/README.md](../services/api/README.md) — API service
- [docs/ml/ALLOMETRIC.md](ml/ALLOMETRIC.md) — Allometric equations explained
- [docs/API.md](API.md) — API endpoints
