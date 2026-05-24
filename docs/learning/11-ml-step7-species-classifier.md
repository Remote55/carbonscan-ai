# บท 11 — Step 7: Species Classification (จำแนกพันธุ์ไม้)

> 🎯 **เป้าหมาย:** เข้าใจวิธีจำแนกชนิดต้นไม้จากภาพ RGB ของเปลือกไม้/ใบ ใช้ Deep Learning
> 📚 **พื้นฐาน:** [บท 10 — QSM](10-ml-step6-qsm.md)
> ⏱️ **เวลา:** ~20 นาที
>
> ⚠️ **Status:** Phase 2 (ยังไม่ implement) — บทนี้อธิบาย design + plan

---

## 1. ปัญหา

LiDAR point cloud มีแค่ "รูปร่าง" — ไม่มี **สี** ไม่รู้ว่าเป็นต้นอะไร

ปัญหา: **Step 8 (Allometric)** ต้องการ species เพื่อเลือกสมการที่ถูก (สัก vs ยางนา ใช้ค่าคงที่ต่างกัน)

**ทางออก:**
- ถ่ายภาพ RGB ของต้น (เปลือก, ใบ, ดอก)
- ใช้ AI Image Classification → predict species

---

## 2. หลักการ — Transfer Learning + ResNet-50

### 2.1 Why ResNet-50

- ✅ **Proven** — ติดอันดับท็อปใน ImageNet classification (2015)
- ✅ **Mid-size** — ไม่เล็กเกินไป (accuracy), ไม่ใหญ่เกินไป (mobile)
- ✅ **Pretrained available** — มี weights pretrained บน ImageNet (1.4M images, 1000 classes)
- ✅ **TFLite export** — แปลงรันบนมือถือได้

### 2.2 Transfer Learning Workflow

```
Pretrained ResNet-50 (ImageNet, 1000 classes)
       ↓
Remove last classification head
       ↓
Add new head: 5 species (Teak, Yang Na, Bamboo, Rubber, Makha) + 1 "Unknown"
       ↓
Fine-tune on our species dataset (200 images × 6 classes = 1200 images)
       ↓
Export TFLite (int8 quantized) → < 20 MB
       ↓
Deploy to Flutter app
```

> 💡 **ทำไม Transfer Learning:** ไม่ต้อง train ResNet ทั้งตัว — แค่ปรับ "หาง" — เร็วและ data น้อย

---

## 3. Architecture

```
Input: RGB image (224 × 224 × 3)
       ↓
ResNet-50 backbone (frozen)
       ↓
Global Average Pooling → 2048-dim feature vector
       ↓
Fully Connected: 2048 → 256 (with ReLU + Dropout 0.5)
       ↓
Fully Connected: 256 → 6 (logits)
       ↓
Softmax → 6 probabilities
```

**Loss:** Cross-entropy
**Optimizer:** AdamW, lr=1e-4 (low because fine-tuning)
**Augmentation:** Rotation, color jitter, cutout

---

## 4. Dataset Plan (Phase 2)

| Source | Count | Notes |
|---|---|---|
| iNaturalist scrape | ~600 (100/species) | API + manual cleanup |
| Manual collection (field) | ~300 | Original photos |
| Stock photo verification | ~300 | License-cleared |
| **Total** | **~1,200** | 80/10/10 train/val/test |

**Classes:**
1. Tectona grandis (Teak)
2. Dipterocarpus alatus (Yang Na)
3. Bambusa spp. (Bamboo)
4. Hevea brasiliensis (Para Rubber)
5. Afzelia xylocarpa (Makha)
6. Unknown (catchall)

**Target:** Top-1 accuracy ≥ 85%

---

## 5. Mobile Inference

### 5.1 Why On-device

- ⚡ Latency < 500ms (no API call)
- 🔒 Privacy — ภาพไม่ออกจากมือถือ
- 📶 Offline support

### 5.2 TFLite Export

```python
import tensorflow as tf

# Convert SavedModel → TFLite
converter = tf.lite.TFLiteConverter.from_saved_model('export/')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = make_calibration_dataset  # for int8
tflite_model = converter.convert()

with open('tree_species_v1.tflite', 'wb') as f:
    f.write(tflite_model)

# Target: < 20 MB
```

### 5.3 Flutter Integration

```dart
// 📂 services/ml/pipeline/species_classifier.dart (Flutter, Phase 2)

final interpreter = await Interpreter.fromAsset('assets/ml_models/tree_species_v1.tflite');

Future<TopKResult> classifyTop3(File jpegFile) async {
    // 1. Preprocess: resize 224x224, normalize
    final input = await preprocess(jpegFile);

    // 2. Run inference
    final output = List.filled(speciesList.length, 0.0).reshape([1, speciesList.length]);
    interpreter.run(input, output);

    // 3. Softmax + top-K
    return topK(output[0], k: 3);
}
```

---

## 6. Phase 1 Stub

📂 **`services/ml/pipeline/species_classifier.py`**

```python
class SpeciesClassifier:
    @staticmethod
    def predict(image_path: str) -> dict:
        """Stub: returns uniform probabilities."""
        species_list = ['Tectona grandis', 'Dipterocarpus alatus',
                        'Bambusa spp.', 'Hevea brasiliensis',
                        'Afzelia xylocarpa', 'Unknown']
        prob = 1.0 / len(species_list)
        return {sp: prob for sp in species_list}
```

> ⚠️ **Phase 1:** Step 7 ส่ง Mock prediction → Step 8 (Allometric) ใช้ Chave 2014 fallback (species-agnostic)

---

## 7. Citation

- **He, K. et al. 2016**. "Deep Residual Learning for Image Recognition". *CVPR*. (ResNet paper)
- **Howard, A. et al. 2017**. "MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications". (Alternative if ResNet too big)

---

## 8. ข้อจำกัด

| Issue | Mitigation |
|---|---|
| Low data per species | Augmentation + transfer learning |
| Visual similarity (Yang Na vs other dipterocarps) | More training data + ensemble |
| Lighting variation in field | Color jitter + normalization |
| Out-of-distribution species (เกิดในป่าจริง) | "Unknown" class + confidence threshold |

---

## 9. ❓ คำถามตรวจสอบความเข้าใจ

1. **Transfer Learning ต่างจาก Train from scratch ยังไง?**
2. **ทำไมใช้ ResNet-50 ไม่ใช่ ResNet-152?**
3. **TFLite quantization int8 ลดขนาด model ลงเท่าไหร่?**
4. **ทำไม Phase 1 ใช้ Mock — Step 8 ทำงานยังไง?**
5. **ถ้า species classifier ผิด (Mock ส่ง wrong species) — Step 8 จะใช้สมการอะไร?**

---

## 10. อ่านต่อ

- [บท 12 — Step 8: Allometric Carbon ⭐](12-ml-step8-allometric.md) — สุดท้าย!

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
