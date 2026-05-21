/// Environment-specific configuration.
///
/// Currently uses const defaults. Phase 1: switch to flutter_dotenv or
/// `--dart-define` flags for proper environment management.

class AppConfig {
  AppConfig._();

  // --- Backend API ---
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
    // Note: 10.0.2.2 is Android emulator's localhost. Use real device IP
    // when testing on physical device.
  );

  // --- Supabase ---
  static const String supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: '',
  );
  static const String supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue: '',
  );

  // --- Pipeline limits ---
  static const int photoCountMin = 30;
  static const int photoCountMax = 50;
  static const int photoQuality = 85; // JPEG quality
  static const int photoMaxWidth = 1920;

  // --- GPS precision ---
  static const int gpsDecimalPrecision = 6; // ≈ 0.1m accuracy

  // --- Feature flags ---
  static const bool enableSpeciesClassifier = true;
  static const bool enableOfflineMode = false; // Phase 4

  /// Initialize app config (load any async resources).
  static Future<void> load() async {
    // TODO Phase 1: Load .env via flutter_dotenv or assert dart-defines present
    assert(
      apiBaseUrl.isNotEmpty,
      'API_BASE_URL must be set via --dart-define',
    );
  }

  /// True for dev builds with debug overlays.
  static bool get isDebug {
    var isDebug = false;
    assert(isDebug = true); // assert only runs in debug
    return isDebug;
  }
}
