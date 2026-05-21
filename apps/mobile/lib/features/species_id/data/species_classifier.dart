import 'dart:io';

/// On-device tree species classifier using TensorFlow Lite.
///
/// TODO Phase 2-3:
/// - Load tflite model from assets/ml_models/tree_species_v1.tflite
/// - Pre-process image (resize 224×224, normalize)
/// - Run inference via tflite_flutter package
/// - Return top-K predictions with confidence
class SpeciesClassifier {
  SpeciesClassifier._();

  /// Supported species (matches services/ml/data/species_db.csv).
  static const List<String> species = [
    'Tectona grandis', // ไม้สัก
    'Dipterocarpus alatus', // ยางนา
    'Bambusa spp.', // ไผ่
    'Hevea brasiliensis', // ยางพารา
    'Afzelia xylocarpa', // มะค่าโมง
    'Unknown',
  ];

  static final SpeciesClassifier instance = SpeciesClassifier._();

  bool _loaded = false;

  /// Load the TFLite model into memory. Call before first classify().
  Future<void> load() async {
    if (_loaded) return;
    // TODO Phase 2: load via tflite_flutter Interpreter.fromAsset
    // _interpreter = await Interpreter.fromAsset('assets/ml_models/tree_species_v1.tflite');
    _loaded = true;
  }

  /// Classify a single image.
  ///
  /// Returns a map of {species: probability} sorted by confidence.
  Future<Map<String, double>> classify(File imageFile) async {
    await load();

    // TODO Phase 2: implement
    // 1. Decode image (`image` package)
    // 2. Resize to 224×224
    // 3. Normalize: [-1, 1] or [0, 1]
    // 4. Run inference: _interpreter.run(input, output)
    // 5. Apply softmax + return sorted

    // Stub: return uniform probabilities
    final uniform = 1.0 / species.length;
    return {for (final s in species) s: uniform};
  }

  /// Get the top-1 prediction for an image.
  Future<({String species, double confidence})> classifyTop1(File imageFile) async {
    final results = await classify(imageFile);
    final sorted = results.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return (species: sorted.first.key, confidence: sorted.first.value);
  }
}
