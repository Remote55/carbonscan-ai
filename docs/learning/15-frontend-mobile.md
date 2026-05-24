# บท 15 — Frontend Mobile (Flutter + Riverpod + Camera)

> 🎯 **เป้าหมาย:** เข้าใจ Mobile app stack + วิธีถ่ายภาพ + Anti-fraud
> 📚 **พื้นฐาน:** [บท 03 — Architecture](03-architecture.md)
> ⏱️ **เวลา:** ~25 นาที

---

## 1. Mobile App ทำอะไร

📂 **`apps/mobile/`** — Flutter cross-platform (Android + iOS)

**Screens (Phase 0 — UI ready):**
1. **HomeScreen** — Logo + hero + "เริ่มสแกนต้นไม้" CTA + stats
2. **TreeScanScreen** — Checklist 4 ข้อก่อนสแกน
3. **CameraScreen** — Camera preview + counter + shutter
4. **ResultsScreen** — Pipeline progress + final results

**Future screens (Phase 1-3):**
- Login / Signup
- History
- Carbon Report

---

## 2. ทำไม Flutter

| Reason | Detail |
|---|---|
| **Cross-platform** | 1 codebase = Android + iOS (save 50% time) |
| **Near-native performance** | Compile to native ARM code |
| **Hot reload** | < 1 sec dev feedback loop |
| **Camera/sensor APIs** | Mature plugins (better than React Native) |
| **TFLite support** | Built-in ML inference |

**ไม่ใช้ React Native** เพราะ:
- ❌ Camera/sensor APIs less stable
- ❌ Performance สู้ Flutter ไม่ได้สำหรับ heavy work

**ไม่ใช้ Native Android (Kotlin) แยก** เพราะ:
- ❌ ต้อง maintain Android + iOS codebase แยก
- ❌ ทีมไม่มี Mac สำหรับ iOS

---

## 3. Tech Stack

### 3.1 Core

| Package | Purpose |
|---|---|
| **Flutter** 3.44 | Framework |
| **Dart** 3.12 | Language |

### 3.2 State Management

| Package | Purpose |
|---|---|
| **flutter_riverpod** 2.6 | Type-safe state management |
| **riverpod_annotation** 2.6 | Code-gen helpers |

**ทำไม Riverpod ไม่ใช่ Provider:**
- ✅ **Compile-time safe** — error ก่อน runtime
- ✅ **Better testing** — providers ตรวจเองได้
- ✅ **Code generation** — ลด boilerplate

### 3.3 Routing

| Package | Purpose |
|---|---|
| **go_router** 14 | Declarative routing |

**Routes:**
```dart
routes: [
    GoRoute(path: '/', builder: ... HomeScreen()),
    GoRoute(path: '/scan', builder: ... TreeScanScreen()),
    GoRoute(path: '/scan/camera', builder: ... CameraScreen()),
    GoRoute(path: '/scan/results/:jobId', builder: (ctx, state) => ResultsScreen(jobId: state.pathParameters['jobId']!)),
]
```

### 3.4 Camera + Sensors

| Package | Purpose |
|---|---|
| **camera** 0.11 | Native camera access |
| **geolocator** 12 | GPS coordinates |
| **permission_handler** 11 | Runtime permissions |
| **exif** 3 | Read/write EXIF metadata |
| **image** 4 | Image manipulation |
| **path_provider** 2 | File system paths |

**Capture flow:**
```dart
// 1. Request permissions
await Permission.camera.request();
await Permission.location.request();

// 2. Initialize camera
final cameras = await availableCameras();
final controller = CameraController(cameras[0], ResolutionPreset.high);
await controller.initialize();

// 3. Capture
final image = await controller.takePicture();

// 4. Get GPS
final position = await Geolocator.getCurrentPosition(
    desiredAccuracy: LocationAccuracy.best,
);

// 5. Embed EXIF
await embedGpsExif(image.path, position.latitude, position.longitude);

// 6. Upload
await dio.post('/api/v1/jobs/photogrammetry', data: formData);
```

### 3.5 Networking

| Package | Purpose |
|---|---|
| **dio** 5 | HTTP client (auth interceptor + retry) |
| **dio_cache_interceptor** 3 | Response caching |

### 3.6 Cloud / Backend

| Package | Purpose |
|---|---|
| **supabase_flutter** 2 | Supabase client (auth + storage) |
| **shared_preferences** 2 | Local key-value store |

### 3.7 UI

| Package | Purpose |
|---|---|
| **google_fonts** | Web fonts (Sarabun for Thai) |
| **cached_network_image** | Image caching |
| **shimmer** | Loading skeletons |
| **flutter_animate** | Animations |
| **fl_chart** | Charts |

### 3.8 ML (Phase 2)

| Package | Status |
|---|---|
| **tflite_flutter** | Deferred (AGP 9 namespace conflict) — re-enable Phase 2 |

---

## 4. Anti-Fraud — Multi-layer Protection

### 4.1 Layer 1 — Camera-only (no gallery upload)

```dart
// ❌ NOT allowed:
final image = await picker.pickImage(source: ImageSource.gallery);

// ✅ Only camera:
final image = await picker.pickImage(source: ImageSource.camera);
```

### 4.2 Layer 2 — GPS Embedded EXIF

ทุกภาพต้องมี:
- GPS latitude + longitude (6 ทศนิยม = ~10 cm precision)
- Timestamp from device
- Server time check (กัน fake timestamp)

### 4.3 Layer 3 — Server-side Dedup

```sql
-- ก่อน insert tree ใหม่
SELECT id FROM trees
WHERE plot_id = $plot_id
  AND ST_DWithin(location, $new_location::geography, 2.0);
-- ถ้ามี row กลับมา → duplicate warning
```

### 4.4 Layer 4 — Audit Log

ทุก mutation (insert/update tree) → ลง `audit_log` table immutable

---

## 5. Build Quirks (สำคัญสำหรับ Android)

### 5.1 Kotlin 2.3 + AGP 9 Incremental Cache Bug

ในไฟล์ `android/gradle.properties`:

```properties
kotlin.incremental=false
kotlin.compiler.execution.strategy=in-process
kotlin.daemon.jvmargs=-Xmx4G -XX:MaxMetaspaceSize=2G
```

**Why:** Kotlin 2.3 on Windows + Build Tools API มี bug — "Could not close incremental caches"

### 5.2 tflite_flutter Namespace Conflict (Deferred)

```yaml
# pubspec.yaml
# tflite_flutter: ^0.10.4  # ⚠️ commented — namespace conflict with AGP 9
```

Will re-enable in Phase 2 with `litert` or newer version.

### 5.3 AndroidManifest.xml Required Permissions

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
```

---

## 6. Running Locally

```bash
cd apps/mobile

# Setup
flutter pub get
flutter doctor               # check setup

# Run on emulator
flutter emulators --launch <id>
flutter run

# Build APK
flutter build apk --debug    # output: build/app/outputs/flutter-apk/
```

---

## 7. ❓ คำถามตรวจสอบความเข้าใจ

1. **ทำไมเลือก Flutter ไม่ใช่ React Native?**
2. **Riverpod ดีกว่า Provider ตรงไหน?**
3. **Anti-fraud มี 4 layers — แต่ละ layer ป้องกันอะไร?**
4. **kotlin.incremental=false แก้ปัญหาอะไร?**
5. **ทำไม tflite_flutter ถูก disable ใน Phase 1?**

---

## 8. อ่านต่อ

- [บท 16 — Backend API](16-backend-api.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
