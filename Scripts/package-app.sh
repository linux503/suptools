#!/bin/bash
# Build SupTools.app for one architecture.
# Usage: package-app.sh [arm64|x86_64] [icon.png]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="${1:-arm64}"
ICON_SRC="${2:-}"
ASSETS="$ROOT/assets"
NATIVE="$ROOT/Native"
APP_NAME="SupTools"

case "$ARCH" in
  arm64|aarch64)
    ARCH="arm64"
    ARCH_LABEL="Apple Silicon (M 芯片)"
    SWIFT_TARGET="arm64-apple-macosx13.0"
    PLIST_ARCH="arm64"
    ;;
  x86_64|intel|amd64)
    ARCH="x86_64"
    ARCH_LABEL="Intel"
    SWIFT_TARGET="x86_64-apple-macosx13.0"
    PLIST_ARCH="x86_64"
    ;;
  *)
    echo "Usage: $0 [arm64|x86_64] [icon.png]" >&2
    exit 2
    ;;
esac

APP="$ROOT/dist/$ARCH/${APP_NAME}.app"
MACOS="$APP/Contents/MacOS"
RES="$APP/Contents/Resources"

echo "→ Building ${APP_NAME}.app for $ARCH_LABEL ($ARCH)..."

# Locate icon PNG
if [[ -z "$ICON_SRC" ]]; then
  for candidate in \
    "$ROOT/Resources/SupToolsIcon.png" \
    "$ROOT/Resources/SystemMonitIcon.png" \
    "$ASSETS/SupToolsIcon.png" \
    "$ASSETS/SystemMonitIcon.png"
  do
    if [[ -f "$candidate" ]]; then
      ICON_SRC="$candidate"
      break
    fi
  done
fi

rm -rf "$APP"
mkdir -p "$MACOS" "$RES" "$ASSETS" "$APP/Contents"

# --- Info.plist (architecture-specific) ---
python3 - <<PY
import plistlib
from pathlib import Path
src = Path("$ROOT/Resources/Info.plist")
dst = Path("$APP/Contents/Info.plist")
data = plistlib.loads(src.read_bytes())
data["LSArchitecturePriority"] = ["$PLIST_ARCH"]
data["LSRequiresNativeExecution"] = True
dst.write_bytes(plistlib.dumps(data))
print("  ✓ Info.plist ($PLIST_ARCH)")
PY

# --- App icon (.icns) ---
if [[ -n "$ICON_SRC" && -f "$ICON_SRC" ]]; then
  cp "$ICON_SRC" "$ASSETS/SupToolsIcon.png"
  cp "$ICON_SRC" "$ASSETS/SystemMonitIcon.png" 2>/dev/null || true
  ICONSET="$ROOT/build/AppIcon-$ARCH.iconset"
  rm -rf "$ICONSET"
  mkdir -p "$ICONSET"
  for size in 16 32 128 256 512; do
    sips -z $size $size "$ICON_SRC" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    sips -z $((size*2)) $((size*2)) "$ICON_SRC" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
  done
  cp "$ICONSET/icon_32x32.png" "$ICONSET/icon_16x16@2x.png" 2>/dev/null || true
  iconutil -c icns "$ICONSET" -o "$RES/AppIcon.icns"
  echo "  ✓ AppIcon.icns"
else
  echo "  ! No icon PNG found, continuing without custom icon"
fi

# --- Native launcher ---
swiftc -O -target "$SWIFT_TARGET" \
  "$NATIVE/Launcher.swift" \
  -o "$MACOS/${APP_NAME}"
chmod +x "$MACOS/${APP_NAME}"
echo "  ✓ $ARCH launcher ($(file -b "$MACOS/${APP_NAME}"))"

# --- Python package payload ---
rm -rf "$RES/systemmonit" "$RES/systemmonit_launcher.py"
cp -R "$ROOT/systemmonit" "$RES/systemmonit"
find "$RES/systemmonit" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
cp "$ROOT/systemmonit_launcher.py" "$RES/systemmonit_launcher.py"
echo "  ✓ Python payload"

# --- Status / brand icons ---
for f in SupToolsIcon.png SystemMonitIcon.png StatusIcon.png StatusIcon@2x.png StatusGlyph.png StatusGlyph@2x.png; do
  cp "$ROOT/Resources/$f" "$RES/$f" 2>/dev/null || true
done
# Ensure brand icon alias exists in Resources even if only legacy filename is present
if [[ -f "$RES/SystemMonitIcon.png" && ! -f "$RES/SupToolsIcon.png" ]]; then
  cp "$RES/SystemMonitIcon.png" "$RES/SupToolsIcon.png"
fi
echo "  ✓ status icons"

# Ad-hoc codesign for local Gatekeeper / transfer
if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || true
  echo "  ✓ ad-hoc signed"
fi
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

# Convenience symlink for older scripts (must not be a real directory)
mkdir -p "$ROOT/dist"
if [ -e "$ROOT/dist/${APP_NAME}.app" ] || [ -L "$ROOT/dist/${APP_NAME}.app" ]; then
  rm -rf "$ROOT/dist/${APP_NAME}.app"
fi
ln -sfn "$ARCH/${APP_NAME}.app" "$ROOT/dist/${APP_NAME}.app"
# Keep legacy symlink name for old tooling
if [ -e "$ROOT/dist/SystemMonit.app" ] || [ -L "$ROOT/dist/SystemMonit.app" ]; then
  rm -rf "$ROOT/dist/SystemMonit.app"
fi
ln -sfn "$ARCH/${APP_NAME}.app" "$ROOT/dist/SystemMonit.app"

echo ""
echo "✓ Built: $APP"
echo "  Architecture: $ARCH_LABEL ($ARCH)"
