# 📱 Mobile App (Flutter)

> **Owner:** User
> **Tech:** Flutter 3.x + Dart + Riverpod + TFLite

---

## Overview

Mobile App สำหรับ **Community users** ใช้สแกนต้นไม้ของตัวเอง:
1. ถ่ายภาพต้นไม้ 30-50 รูป (multi-angle)
2. เก็บ GPS coordinates (6-decimal precision)
3. AI Species Classification on-device (TFLite)
4. ส่งภาพขึ้น Cloud → Photogrammetry → Carbon calculation
5. แสดงผลลัพธ์: DBH, Height, Carbon kg

**Cross-platform:** Android ก่อน, iOS หลัง (ถ้ามี Mac/Codemagic)

---

## Folder Structure

```
apps/mobile/
├── README.md                         (this file)
├── pubspec.yaml
├── analysis_options.yaml
├── lib/
│   ├── main.dart                     Entry point
│   ├── app.dart                      Root widget + routing
│   ├── core/
│   │   ├── config/
│   │   │   ├── app_config.dart
│   │   │   └── routes.dart
│   │   ├── theme/
│   │   │   ├── app_theme.dart
│   │   │   └── colors.dart
│   │   ├── network/
│   │   │   ├── dio_client.dart
│   │   │   └── api_interceptors.dart
│   │   └── utils/
│   │       ├── permissions.dart
│   │       └── validators.dart
│   ├── features/
│   │   ├── auth/
│   │   │   ├── presentation/
│   │   │   ├── domain/
│   │   │   └── data/
│   │   ├── camera/
│   │   │   ├── presentation/
│   │   │   │   ├── camera_screen.dart
│   │   │   │   └── widgets/
│   │   │   ├── domain/
│   │   │   │   └── tree_capture.dart
│   │   │   └── data/
│   │   │       └── camera_service.dart
│   │   ├── tree_scan/
│   │   │   ├── presentation/
│   │   │   │   └── tree_scan_screen.dart
│   │   │   └── domain/
│   │   ├── species_id/
│   │   │   ├── data/
│   │   │   │   └── species_classifier.dart  (TFLite)
│   │   │   └── models/
│   │   │       └── tree_species_v1.tflite
│   │   ├── results/
│   │   │   └── presentation/
│   │   │       └── results_screen.dart
│   │   └── upload/
│   │       └── data/
│   │           └── upload_service.dart
│   └── shared/
│       ├── widgets/
│       │   ├── app_button.dart
│       │   └── loading_overlay.dart
│       └── providers/
│           └── auth_provider.dart
├── assets/
│   ├── images/
│   ├── icons/
│   └── ml_models/                    (gitignored if > 50MB)
├── test/
└── integration_test/
```

---

## Architecture

ใช้ **Clean Architecture** + Feature-based folder structure:

```
[Presentation Layer]    Widgets, Screens, Riverpod Providers
       ↓
[Domain Layer]          Entities, Use Cases, Repository Interfaces
       ↓
[Data Layer]            Repository Implementations, Data Sources (API, Local)
```

### Why?
- ทดสอบ unit ง่าย (mock dependencies)
- เปลี่ยน data source ง่าย (mock → real API)
- เพิ่ม feature ใหม่ไม่กระทบของเดิม

---

## Setup

### Prerequisites
- Flutter 3.x: https://docs.flutter.dev/get-started/install
- Android Studio / VS Code with Flutter extension
- Android device (or emulator) with API 26+
- (Optional) iOS device + Xcode

### Install
```bash
cd apps/mobile

# Install dependencies
flutter pub get

# Verify
flutter doctor
# (resolve any issues shown)

# Run on connected device
flutter run

# Run on specific device
flutter devices
flutter run -d <device-id>
```

### Build APK
```bash
# Debug
flutter build apk --debug

# Release (requires signing)
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

---

## Key Packages

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_riverpod: ^2.5.0
  riverpod_annotation: ^2.3.0

  # Routing
  go_router: ^14.0.0

  # Networking
  dio: ^5.4.0
  retrofit: ^4.1.0

  # Camera & Sensors
  camera: ^0.10.0
  geolocator: ^11.0.0
  permission_handler: ^11.3.0
  image: ^4.2.0
  exif: ^3.3.0

  # ML / AI
  tflite_flutter: ^0.10.0
  tflite_flutter_helper: ^0.4.0

  # Storage
  shared_preferences: ^2.2.0
  path_provider: ^2.1.0

  # UI
  google_fonts: ^6.2.0
  cached_network_image: ^3.3.0
  shimmer: ^3.0.0
  flutter_animate: ^4.5.0
  fl_chart: ^0.68.0

  # Auth
  supabase_flutter: ^2.5.0

  # Utility
  freezed_annotation: ^2.4.0
  json_annotation: ^4.9.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0
  build_runner: ^2.4.0
  freezed: ^2.5.0
  json_serializable: ^6.8.0
  riverpod_generator: ^2.4.0
```

---

## Core Features Implementation

### 1. Camera Capture (Multi-shot)

```dart
// lib/features/camera/data/camera_service.dart
class CameraService {
  late CameraController _controller;
  final List<XFile> _captures = [];

  Future<void> initialize() async {
    final cameras = await availableCameras();
    _controller = CameraController(cameras.first, ResolutionPreset.high);
    await _controller.initialize();
  }

  Future<XFile> capture() async {
    final image = await _controller.takePicture();
    _captures.add(image);
    return image;
  }

  Future<List<XFile>> captureSeries(int count, {Duration interval = const Duration(seconds: 1)}) async {
    for (var i = 0; i < count; i++) {
      await capture();
      await Future.delayed(interval);
    }
    return _captures;
  }
}
```

### 2. GPS with EXIF

```dart
// lib/core/utils/gps_service.dart
class GpsService {
  Future<Position> getCurrentPosition() async {
    // Check permissions
    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      await Geolocator.requestPermission();
    }

    return Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.best,
    );
  }

  /// Returns 6-decimal precision (≈ 0.1m accuracy)
  String formatCoord(double coord) => coord.toStringAsFixed(6);
}
```

### 3. Species Classification (TFLite)

```dart
// lib/features/species_id/data/species_classifier.dart
class SpeciesClassifier {
  late Interpreter _interpreter;
  static const _labels = ['Tectona', 'Dipterocarpus', 'Bambusa', 'Hevea', 'Afzelia'];

  Future<void> load() async {
    _interpreter = await Interpreter.fromAsset('assets/ml_models/tree_species_v1.tflite');
  }

  Future<Map<String, double>> classify(File imageFile) async {
    final image = img.decodeImage(imageFile.readAsBytesSync())!;
    final resized = img.copyResize(image, width: 224, height: 224);

    final input = _imageToTensor(resized);
    final output = List.filled(_labels.length, 0.0).reshape([1, _labels.length]);

    _interpreter.run(input, output);

    return Map.fromIterables(_labels, output[0]);
  }
}
```

### 4. Upload with Progress

```dart
// lib/features/upload/data/upload_service.dart
class UploadService {
  final Dio dio;

  UploadService(this.dio);

  Future<String> uploadTreeScan({
    required List<File> photos,
    required Position gpsPosition,
    required String speciesHint,
    void Function(double progress)? onProgress,
  }) async {
    final formData = FormData();
    for (final photo in photos) {
      formData.files.add(MapEntry('files[]', await MultipartFile.fromFile(photo.path)));
    }
    formData.fields.addAll([
      MapEntry('gps_lat', gpsPosition.latitude.toStringAsFixed(6)),
      MapEntry('gps_lon', gpsPosition.longitude.toStringAsFixed(6)),
      MapEntry('species_hint', speciesHint),
    ]);

    final response = await dio.post(
      '/upload/photos',
      data: formData,
      onSendProgress: (sent, total) => onProgress?.call(sent / total),
    );

    return response.data['job_id'];
  }
}
```

---

## Anti-Fraud Implementation

### 1. Camera-Only (No Gallery)
```dart
// Disable gallery picker entirely
// ห้าม ImagePicker.galleryImage()
// Use only camera
```

### 2. EXIF Validation
ฝัง GPS + timestamp ลงใน image metadata. Backend ตรวจสอบว่า:
- Timestamp อยู่ในช่วงไม่เก่าเกิน 24 ชม.
- GPS coordinates สอดคล้องกับที่อ้าง

### 3. Real-time Capture Lock
```dart
class _CameraScreenState extends State<CameraScreen> {
  bool _hasRecentPhoto = false;

  @override
  void initState() {
    super.initState();
    // ตรวจ device camera time matches network time
    // (ป้องกันการตั้งเวลาย้อนหลังเพื่อใช้รูปเก่า)
  }
}
```

---

## State Management (Riverpod)

```dart
// lib/features/tree_scan/presentation/providers.dart
@riverpod
class TreeScanController extends _$TreeScanController {
  @override
  TreeScanState build() => const TreeScanState.initial();

  Future<void> startScan() async {
    state = const TreeScanState.capturing();

    final photos = await ref.read(cameraServiceProvider).captureSeries(30);
    final gps = await ref.read(gpsServiceProvider).getCurrentPosition();
    final species = await ref.read(speciesClassifierProvider).classify(photos.first.file);

    state = TreeScanState.uploading(photos: photos, gps: gps, species: species);

    final jobId = await ref.read(uploadServiceProvider).uploadTreeScan(
      photos: photos.map((p) => File(p.path)).toList(),
      gpsPosition: gps,
      speciesHint: species.entries.reduce((a, b) => a.value > b.value ? a : b).key,
    );

    state = TreeScanState.processing(jobId: jobId);
  }
}
```

---

## Testing

```bash
# Unit tests
flutter test

# Widget tests
flutter test test/widget_test.dart

# Integration tests (real device)
flutter test integration_test/
```

---

## Performance Tips

- **Resize images** ก่อน upload (1080p พอ — ไม่จำเป็นต้อง 4K)
- **Compress** ด้วย `image` package ก่อนส่ง
- **Lazy load** TFLite model (เมื่อเข้าหน้าจอ scan)
- **Cache** API responses ด้วย `dio_cache_interceptor`

---

## Permissions (AndroidManifest.xml)

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

iOS `Info.plist`:
```xml
<key>NSCameraUsageDescription</key>
<string>ใช้กล้องเพื่อสแกนต้นไม้</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>ใช้ GPS เพื่อบันทึกพิกัดต้นไม้</string>
```

---

📖 **See also:**
- [docs/API.md](../../docs/API.md) — Backend API
- [services/ml/README.md](../../services/ml/README.md) — ML pipeline
- [docs/decisions/0003-tech-stack-selection.md](../../docs/decisions/0003-tech-stack-selection.md) — Why Flutter
