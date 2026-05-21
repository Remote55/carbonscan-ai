# 📧 Email/Line Template — ส่ง Proposal ให้ที่ปรึกษา

> วิธีใช้: Copy ส่วนที่เหมาะกับ medium ของคุณ (Email หรือ Line) แล้วแก้ใน `[placeholder]` ให้ตรงกับสถานการณ์จริง
>
> ผมแนะนำ: ส่ง **Email หลัก** + ส่ง **Line ตามแจ้งสั้นๆ**

---

## 🅰️ Option A: Email (Formal)

### Subject (เลือก 1):
- `[NSC 2026] ขอความกรุณาตรวจร่างข้อเสนอโครงการ — CarbonScan AI`
- `[ด่วน] ข้อเสนอ NSC 2026 — ขอที่ปรึกษาช่วยตรวจครับ/ค่ะ`

### Body:

```
เรียน อาจารย์[ชื่ออาจารย์]

ตามที่อาจารย์ได้ให้คำแนะนำเรื่องโครงการประกวด NSC 2026
หมวดที่ 14 (โปรแกรมเพื่องานการพัฒนาด้านวิทยาศาสตร์และเทคโนโลยี)
ระดับอุดมศึกษา ทางทีมของพวกผม/หนู (ทีม 3 คน) ได้ร่างข้อเสนอ
โครงการชื่อ "CarbonScan AI" เสร็จเรียบร้อยแล้ว

โครงการนี้คือแพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้ด้วย
LiDAR Point Cloud + AI Wood-Leaf Segmentation + ระบบ B2B
จับคู่ Carbon Offset โดยตอบโจทย์ปัญหาที่อาจารย์เคยตั้งไว้
และตอบครบ 5 คำถามที่อาจารย์ขอให้เตรียม (GPU, Inference cost,
ประโยชน์, หมวดการแข่งขัน, แรงจูงใจ)

ขอความกรุณาอาจารย์ช่วยตรวจร่างเอกสารแนบ และให้ feedback
ภายในวันที่ [24 พ.ค. 2569] เพื่อให้ทีมมีเวลาแก้ไขก่อนเริ่ม
เดินขอลายเซ็นในวันที่ 25 พ.ค. (deadline ส่ง SIMs คือ 29 พ.ค.
17:00 น.)

สรุปประเด็นสำคัญในเอกสาร:
- ✅ ใช้สมการแอลโลเมตริกตามมาตรฐาน TGO (Tsutsumi 1983, Ogawa 1965,
  Chave 2014) — ทดสอบใน Python ผ่าน 16 unit tests แล้ว
- ✅ Pivot จาก iPhone LiDAR เดิม → ใช้ Dual-input architecture
  (LiDAR upload + Mobile Photogrammetry) เพื่อแก้ปัญหาทีมไม่มี
  iPhone Pro
- ✅ Tech Stack ละเอียดทั้ง Frontend/Mobile/Backend/ML/Cloud GPU
- ✅ ระบุ Wood-Leaf Semantic Segmentation ด้วย PointNet++
  เป็น Deep Tech core
- ✅ มี Anti-Fraud Mechanism 4 ชั้น (GPS, EXIF, Camera-only,
  server dedup)
- ✅ Risk & Mitigation 10+ ข้อ + Q&A defense 5 ข้อ
- ✅ Lock Scope ไม้เศรษฐกิจ 5 ชนิด (สัก, ยางนา, ไผ่,
  ยางพารา, มะค่าโมง)

ทีมงาน (3 คน, สถาบันเดียวกัน):
1. [User ชื่อ-สกุล] — Team Lead / AI/ML / Backend / Mobile
2. [Person A ชื่อ-สกุล] — Web Development (Next.js)
3. [Person B ชื่อ-สกุล] — UI/UX Design / Content

เอกสารแนบ:
- CarbonScan_AI_Proposal_v1.docx (ร่างฉบับเต็ม 8-10 หน้า)
- หรือลิงก์ Google Doc: [ใส่ลิงก์ที่นี่]

นอกจากนี้ ทีมได้สร้าง prototype repository พร้อม:
- Repo: https://github.com/Remote55/carbonscan-ai
- Backend (FastAPI + PostgreSQL + PostGIS) — ทำงานได้แล้ว
- Web Landing + Auth pages — boot ได้
- ML allometric calculator — 16/16 tests pass

หากอาจารย์ต้องการดูตัวอย่าง code หรือ live demo สามารถนัด
[เวลา/ช่องทาง] ได้ครับ/ค่ะ

ขอบพระคุณอาจารย์ที่กรุณาให้คำแนะนำมาตลอดครับ/ค่ะ

ด้วยความเคารพ
[User ชื่อ-สกุล]
[หมายเลขโทรศัพท์]
[Line ID]
[Email]
```

---

## 🅱️ Option B: Line / Chat (Casual)

### Format 1 — แจ้งสั้น + ส่งไฟล์

```
สวัสดีครับ/ค่ะ อาจารย์

ทีม NSC 2026 ส่งร่างข้อเสนอโครงการ "CarbonScan AI"
มาให้อาจารย์ตรวจครับ/ค่ะ 📄

ขอความกรุณาช่วยดูภายในวันที่ 24 พ.ค. นะครับ/ค่ะ
เพราะ deadline ส่งระบบ SIMs คือ 29 พ.ค. 17:00 น.
ทีมจะเริ่มเดินขอลายเซ็นวันที่ 25

ประเด็นสำคัญในเอกสาร:
- ตอบครบ 5 คำถามที่อาจารย์ให้มา
- Pivot ไป Dual-input (LiDAR + Mobile Photogrammetry)
- Wood-Leaf Segmentation ด้วย PointNet++ เป็น Deep Tech core
- รองรับไม้เศรษฐกิจ 5 ชนิด (สัก ยางนา ไผ่ ยางพารา มะค่าโมง)
- มี Anti-Fraud 4 ชั้น

[แนบไฟล์ CarbonScan_AI_Proposal_v1.docx]

ขอบคุณอาจารย์ครับ/ค่ะ 🙏
```

### Format 2 — แจ้งก่อนส่ง Email

```
สวัสดีครับ/ค่ะ อาจารย์

ทีม NSC 2026 ส่งร่าง Proposal มาทางอีเมลครับ/ค่ะ
รบกวนอาจารย์ตรวจให้ feedback ภายใน 24 พ.ค.
เพื่อให้ทีมมีเวลาแก้ไขก่อน deadline 29 พ.ค.

ขอบคุณครับ/ค่ะ 🙏
```

---

## 🅲 Follow-up Messages

### หากอาจารย์ยังไม่ตอบใน 24 ชม. (ส่ง Line):

```
สวัสดีครับ/ค่ะ อาจารย์

รบกวนสอบถามว่าอาจารย์ได้รับร่าง Proposal CarbonScan AI
ที่ส่งไปแล้วหรือยังครับ/ค่ะ มี feedback หรือต้องการ
ข้อมูลเพิ่มเติมตรงไหนหรือเปล่า

(ทีมเร่งเพราะต้องเดินขอลายเซ็น 25 พ.ค.)

ขอบคุณครับ/ค่ะ 🙏
```

### หลังอาจารย์ตอบ + ทีมแก้แล้ว (ส่งกลับ):

```
เรียน อาจารย์[ชื่อ]

ทีมได้แก้ไข Proposal ตามคำแนะนำของอาจารย์เรียบร้อยแล้ว
รายการที่แก้:
1. [แก้อะไรตามที่อาจารย์บอก]
2. [...]
3. [...]

แนบเอกสารฉบับแก้ไข (v2) มาด้วยครับ/ค่ะ
หากอาจารย์ approve แล้ว ทีมจะเริ่มเดินขอลายเซ็น
ในวันที่ [25 พ.ค.]

ขอบคุณอาจารย์ครับ/ค่ะ

[User]
```

---

## 🅳 ขอนัดเซ็นเอกสาร (วันที่ 25 พ.ค.)

```
เรียน อาจารย์

ทีมจะนำเอกสาร CarbonScan AI Proposal (final) มาให้
อาจารย์เซ็นรับรอง โดยจะแวะมาที่ [ห้องทำงาน/คณะ]
ในวันที่ [25 พ.ค.] เวลา [HH:MM น.] ครับ/ค่ะ

ถ้าอาจารย์ไม่สะดวกเวลานี้ รบกวนแจ้งเวลาที่สะดวก
อีกครั้งครับ/ค่ะ — ทีมต้องเร่งเพราะหลังเซ็นแล้ว
ต้องเดินเอกสารต่อไปที่[คณบดี/ผอ.] อีกขั้นนึงครับ/ค่ะ

ขอบคุณอาจารย์ที่กรุณาให้คำแนะนำตลอดครับ/ค่ะ 🙏
```

---

## ✅ Checklist ก่อนส่ง

ก่อน paste + ส่ง:

- [ ] แก้ `[ชื่ออาจารย์]` ทุกที่
- [ ] ใส่ชื่อทีม 3 คน + แทน `[User/Person A/Person B ชื่อ-สกุล]`
- [ ] ใส่เบอร์โทร / Line ID / Email ของคุณ
- [ ] แนบไฟล์ Proposal (.docx) จริง
- [ ] หรือ paste link Google Doc (เปลี่ยน sharing เป็น "anyone with link")
- [ ] เช็คว่าใช้คำนำ/ลงท้ายตรงกับ gender (ครับ/ค่ะ)
- [ ] ถ้าอาจารย์อายุห่างมาก ใช้คำว่า "อาจารย์" + "อาจารย์ครับ/ค่ะ" สม่ำเสมอ

---

## 💡 Tips

### เลือก Medium ตามนิสัยอาจารย์

| อาจารย์ประเภท | แนะนำใช้ |
|---|---|
| Formal / Senior | Email (Option A) + แจ้ง Line สั้น |
| Casual / รู้จักกันดี | Line (Option B Format 1) ตรงเลย |
| ตอบช้า / busy | Line + ใส่ "🙏 รบกวนตอบภายใน X" |
| ชอบ video call | + นัด Zoom/Google Meet 15 นาที review |

### Timing ที่ดี

- ส่งช่วง 9:00-11:00 น. หรือ 14:00-16:00 น. (เวลา office)
- หลีกเลี่ยงคืนวันศุกร์-อาทิตย์ (อาจไม่อ่านจนวันจันทร์)
- ถ้าด่วน → ส่ง Email + Line ตามแจ้ง ก่อน 17:00 น.

### ถ้าอาจารย์ไม่อยู่ในประเทศ / ไม่สะดวก signed paper

- เสนอ Digital Signature ผ่าน Adobe Sign / DocuSign
- หรือ scan ลายเซ็น + ใส่ใน PDF (ตามที่ TPQI/NSC อนุญาต)
- ตรวจระเบียบ NSC ว่ารับ digital signature ไหม

---

📖 **เอกสารที่เกี่ยวข้อง:**
- [proposal/outline.md](outline.md) — เนื้อหา Proposal เต็ม
- [proposal/5-questions-answers.md](5-questions-answers.md) — คำตอบ 5 คำถาม
- [proposal/references.md](references.md) — 20+ citations
- [proposal/README.md](README.md) — Proposal workflow
- [TASKS.md](../TASKS.md) — งานที่เหลือก่อน 29 พ.ค.
