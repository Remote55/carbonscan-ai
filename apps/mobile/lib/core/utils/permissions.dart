import 'package:permission_handler/permission_handler.dart';

/// Helper for runtime permission requests.
///
/// On Android, permissions are also declared in AndroidManifest.xml.
/// On iOS, in Info.plist.
abstract final class AppPermissions {
  AppPermissions._();

  /// Request camera permission. Returns true if granted.
  static Future<bool> requestCamera() async {
    final status = await Permission.camera.request();
    return status.isGranted;
  }

  /// Request location (foreground) permission. Returns true if granted.
  static Future<bool> requestLocation() async {
    final status = await Permission.location.request();
    return status.isGranted;
  }

  /// Request both camera + location at once.
  /// Returns map of permission → granted.
  static Future<Map<Permission, bool>> requestAll() async {
    final statuses = await [
      Permission.camera,
      Permission.location,
    ].request();

    return {
      for (final entry in statuses.entries) entry.key: entry.value.isGranted,
    };
  }

  /// True if user has permanently denied a permission (must open settings).
  static Future<bool> isPermanentlyDenied(Permission permission) async {
    return permission.isPermanentlyDenied;
  }
}
