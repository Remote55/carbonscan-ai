#!/usr/bin/env bash
# Run Flutter app in dev mode with dart-defines from a .env file.
#
# Usage:
#   ./scripts/run-dev.sh                    # default device
#   ./scripts/run-dev.sh -d emulator-5554   # specific device
#
# Requires a .env file in apps/mobile/ (copy from .env.example)

set -e

# Find this script's dir → mobile root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

if [ ! -f .env ]; then
    echo "❌ apps/mobile/.env not found. Copy .env.example to .env first."
    exit 1
fi

# Read .env, strip comments, build --dart-define args
DEFINES=$(grep -v '^#' .env | grep -v '^\s*$' | sed 's/^/--dart-define=/' | tr '\n' ' ')

echo "▶ Running with defines:"
echo "$DEFINES" | tr ' ' '\n' | sed 's/^/  /' | head -10

flutter run $DEFINES "$@"
