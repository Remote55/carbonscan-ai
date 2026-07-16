# 🔌 API Reference

> [!CAUTION]
> **Target API reference.** เอกสารนี้รวม endpoint ที่วางแผนไว้ด้วย ไม่ใช่ทุก endpoint ที่ implement แล้ว.
> ปัจจุบันเส้นทางที่ตรวจสอบแล้วคือ health, synchronous `/upload/analyze`, async `/jobs/analyze`
> และการอ่านรายการ/สถานะ jobs ด้วย polling; direct storage uploads, tree/spatial/marketplace endpoints
> และ WebSocket ยังเป็น Stub/Planned. ดู `docs/PROJECT_SPEC.md` และ `docs/CAPABILITY_MATRIX.md`.

> Backend REST API + WebSocket endpoints
>
> **Base URL (dev):** `http://localhost:8000/api/v1`
> **Base URL (prod):** `https://api.carbonscan-ai.com/api/v1`
> **Auto-generated docs:** `/docs` (Swagger) and `/redoc` (ReDoc)

---

## Authentication

All endpoints require `Authorization: Bearer <jwt_token>` header except public endpoints (marked with 🌐).

### POST /auth/signup
สมัครสมาชิก
```json
{
  "email": "user@example.com",
  "password": "string (min 8 chars)",
  "role": "community" | "industrial" | "auditor"
}
```

### POST /auth/login
```json
{
  "email": "user@example.com",
  "password": "string"
}
```
**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600
}
```

### POST /auth/refresh
แลก access token ใหม่ด้วย refresh token

---

## Upload

### POST /upload/las
อัปโหลดไฟล์ LiDAR .las/.laz
- **Content-Type:** `multipart/form-data`
- **Body:** `file` (binary)
- **Max size:** 500MB

**Response:**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "input_url": "https://..."
}
```

### POST /upload/photos
อัปโหลดรูปถ่าย (Photogrammetry path)
- **Body:** `files[]` (multiple .jpg/.png), `gps_lat`, `gps_lon`, `species_hint` (optional)

**Response:** Same as `/upload/las`

---

## Jobs

### GET /jobs/{job_id}
สถานะ job

**Response:**
```json
{
  "id": "uuid",
  "type": "las_upload" | "photogrammetry",
  "status": "queued" | "processing" | "completed" | "failed",
  "progress": 75,
  "started_at": "2026-07-01T10:00:00Z",
  "completed_at": null,
  "result_url": null,
  "error": null
}
```

### GET /jobs
รายการ jobs ของ user (paginated)
```
GET /jobs?status=completed&page=1&limit=20
```

---

## Trees

### POST /trees
สร้าง tree record (หลัง pipeline เสร็จ)
```json
{
  "plot_id": "uuid",
  "species": "Tectona grandis",
  "location": {"lat": 18.7883, "lon": 98.9853},
  "dbh_cm": 25.3,
  "height_m": 15.8,
  "volume_m3": 0.45,
  "biomass_kg": 292.5,
  "carbon_kg": 137.5,
  "co2eq_kg": 504.2,
  "point_cloud_url": "https://..."
}
```

### GET /trees
รายการต้นไม้ (with spatial query support)
```
GET /trees?lat=18.7883&lon=98.9853&radius_km=5&species=Tectona
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "species": "Tectona grandis",
      "location": {"lat": 18.7883, "lon": 98.9853},
      "dbh_cm": 25.3,
      "carbon_kg": 137.5,
      "scanned_at": "2026-07-01T10:00:00Z"
    }
  ],
  "total": 142,
  "page": 1
}
```

### GET /trees/{id}
รายละเอียดต้นไม้ + ผลลัพธ์ pipeline เต็ม

### GET /trees/{id}/point-cloud 🌐
URL ของ .ply file (pre-signed, expires in 15 min)

---

## Plots

### POST /plots
สร้างแปลง (boundary polygon)
```json
{
  "name": "ป่าชุมชนบ้านดง",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lon, lat], ...]]
  }
}
```

### GET /plots/{id}/summary
สรุปแปลง (จำนวนต้น, total carbon, species breakdown)

---

## Marketplace (B2B)

### GET /marketplace/listings 🌐
รายการ trees ที่พร้อมขาย credits
```
GET /marketplace/listings?min_carbon=100&max_price=1000
```

### POST /marketplace/purchase
ซื้อ carbon credits
```json
{
  "tree_id": "uuid",
  "amount_co2eq_kg": 500
}
```

**Response:**
```json
{
  "transaction_id": "uuid",
  "tree_id": "uuid",
  "amount_co2eq_kg": 500,
  "price_thb": 1000,
  "payment_url": "https://stripe.com/..."
}
```

### GET /marketplace/transactions
ประวัติการซื้อ (ของ user)

---

## Reports

### POST /reports/generate
สร้าง PDF report
```json
{
  "type": "tree" | "plot" | "transaction",
  "id": "uuid"
}
```

**Response:**
```json
{
  "report_url": "https://...pdf",
  "expires_at": "..."
}
```

---

## WebSocket Endpoints

### /ws/jobs/{job_id}
Stream progress updates

**Client → Server:** (subscribe)
```json
{"action": "subscribe"}
```

**Server → Client:** (progress events)
```json
{
  "type": "progress",
  "job_id": "uuid",
  "stage": "wood_leaf_segmentation",
  "progress": 65,
  "message": "Processing tree 12/18"
}
```

```json
{
  "type": "complete",
  "job_id": "uuid",
  "result_url": "https://..."
}
```

```json
{
  "type": "error",
  "job_id": "uuid",
  "error": "Out of memory"
}
```

---

## Error Responses

ทุก error ใช้ format นี้:
```json
{
  "error": "ValidationError",
  "message": "Invalid file format. Expected .las or .laz.",
  "details": {
    "field": "file",
    "received": "image/jpeg"
  }
}
```

### HTTP Status Codes
- `200` OK
- `201` Created
- `400` Bad Request (validation)
- `401` Unauthorized
- `403` Forbidden (role)
- `404` Not Found
- `409` Conflict (e.g., duplicate)
- `413` Payload Too Large
- `422` Unprocessable Entity
- `429` Rate Limit
- `500` Internal Server Error
- `503` Service Unavailable (GPU worker down)

---

## Rate Limits

- **Authenticated:** 60 req/min/user
- **Upload:** 5/hour/user
- **Public:** 20 req/min/IP

Headers ที่ส่งกลับ:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1719902400
```

---

## Pagination

ทุก list endpoint รองรับ:
```
?page=1&limit=20&sort=created_at&order=desc
```

Response:
```json
{
  "items": [...],
  "total": 142,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

---

## Versioning

- ปัจจุบัน: `v1`
- Breaking changes → bump เป็น `v2` (keep `v1` alive 6 months)

---

📖 **See also:**
- [docs/DATA_MODEL.md](DATA_MODEL.md) — Database schema
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [services/api/README.md](../services/api/README.md) — API service docs
