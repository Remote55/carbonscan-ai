# Flutter Setup Instructions

> First-time setup for the mobile app after cloning the repo.

---

## Prerequisites

- **Flutter 3.22+** — https://docs.flutter.dev/get-started/install
- **Android Studio** (for Android emulator + SDK)
- **VS Code** with Flutter extension (recommended)
- **(Optional) Xcode** — only on macOS, for iOS builds

Verify install:
```bash
flutter doctor
```

Resolve any ❌ shown before continuing.

---

## First-Time Setup

```bash
cd apps/mobile

# 1. Generate platform-specific files (android/, ios/)
#    This is needed because we don't commit those folders
flutter create . --platforms=android,ios --project-name=carbonscan_mobile

# 2. Install Dart deps
flutter pub get

# 3. Run code generation (Freezed, JSON, Riverpod)
dart run build_runner build --delete-conflicting-outputs

# 4. Verify
flutter analyze
flutter test
```

---

## Run the App

### Android Emulator
```bash
# List devices
flutter devices

# Run (auto-detects emulator)
flutter run

# Or specify device
flutter run -d emulator-5554
```

### Physical Android Device
1. Enable Developer Options + USB Debugging on phone
2. Connect via USB
3. Run `flutter devices` to verify
4. `flutter run`

### iOS (Mac only)
```bash
cd ios && pod install && cd ..
flutter run -d <ios-device-id>
```

---

## Configure Backend URL

The default `apiBaseUrl` points to `http://10.0.2.2:8000` (Android emulator's
localhost). For other scenarios:

```bash
# Physical Android device on same WiFi (replace IP with your laptop's)
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000

# Production
flutter run --dart-define=API_BASE_URL=https://api.carbonscan-ai.com
```

---

## Build Releases

### Android APK
```bash
# Debug
flutter build apk --debug

# Release (requires signing — see below)
flutter build apk --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

### Sign Android Release
```bash
# 1. Generate keystore (once)
keytool -genkey -v -keystore ~/upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias upload

# 2. Configure android/key.properties (gitignored):
cat > android/key.properties <<EOF
storePassword=<password>
keyPassword=<password>
keyAlias=upload
storeFile=/path/to/upload-keystore.jks
EOF

# 3. Edit android/app/build.gradle.kts to use key.properties
# (See https://docs.flutter.dev/deployment/android#signing-the-app)

flutter build apk --release
```

### iOS IPA (via Codemagic, no Mac needed)
1. Sign up at codemagic.io
2. Connect this GitHub repo
3. Configure `codemagic.yaml` (template in repo root)
4. Trigger build → IPA artifact downloadable

---

## Code Generation Watch Mode

Some files (Freezed, JSON, Riverpod) are auto-generated. Run watch mode during
active development:

```bash
dart run build_runner watch --delete-conflicting-outputs
```

---

## Troubleshooting

### "Target of URI doesn't exist: 'package:carbonscan_mobile/...'"
Run `flutter pub get` again.

### "Pod install failed" on iOS
```bash
cd ios
pod repo update
pod install
cd ..
```

### Android build fails with Java version
Use Java 17 (default in Android Studio Iguana+).

### "Multidex" error on Android
Edit `android/app/build.gradle`:
```gradle
defaultConfig {
    multiDexEnabled true
}
```

### Camera permission denied on real device
- Android: Settings → Apps → CarbonScan AI → Permissions → Camera
- iOS: Settings → CarbonScan AI → Camera

---

## Project Structure

```
apps/mobile/
├── lib/
│   ├── main.dart           ← Entry point
│   ├── app.dart            ← Root widget + routing
│   ├── core/               ← App-wide infra (config, theme, network)
│   ├── features/           ← Feature modules (camera, scan, results, etc.)
│   └── shared/             ← Reusable widgets + providers
├── test/                   ← Unit + widget tests
├── assets/                 ← Images, icons, ML models
├── pubspec.yaml            ← Deps
└── android/, ios/          ← Platform-specific (generated, not in git)
```

📖 ดูเพิ่ม:
- [apps/mobile/README.md](README.md) — Code architecture
- [docs/ONBOARDING.md](../../docs/ONBOARDING.md) — Team onboarding
