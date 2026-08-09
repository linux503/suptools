#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="$(uname -m)"
case "$ARCH" in
  arm64|aarch64) ARCH=arm64 ;;
  x86_64) ARCH=x86_64 ;;
  *) ARCH=arm64 ;;
esac
"$ROOT/Scripts/package-app.sh" "$ARCH"
APP="$ROOT/dist/$ARCH/SupTools.app"
DEST="/Applications/SupTools.app"
# Remove previous brand installs if present
rm -rf "$DEST" "/Applications/SysPulse.app" "/Applications/SystemMonit.app"
cp -R "$APP" "$DEST"
xattr -dr com.apple.quarantine "$DEST" 2>/dev/null || true
codesign --force --deep --sign - "$DEST" >/dev/null 2>&1 || true
echo "✓ Installed to $DEST ($ARCH)"
open "$DEST"
