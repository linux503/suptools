#!/bin/bash
# Build Apple Silicon + Intel apps and wrap each as a drag-to-Applications DMG.
# Output:
#   dist/release/SupTools-<ver>-AppleSilicon.dmg
#   dist/release/SupTools-<ver>-Intel.dmg
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RELEASE="$ROOT/dist/release"
STAGE="$ROOT/dist/dmg-stage"
APP_NAME="SupTools"

VERSION="$(
  /usr/bin/python3 - <<PY
import plistlib
from pathlib import Path
p = Path(r"$ROOT") / "Resources" / "Info.plist"
print(plistlib.loads(p.read_bytes()).get("CFBundleShortVersionString", "0.0.0"))
PY
)"

echo "════════════════════════════════════════"
echo " ${APP_NAME} $VERSION — 双架构安装包"
echo "════════════════════════════════════════"
echo ""

"$ROOT/Scripts/package-app.sh" arm64
echo ""
"$ROOT/Scripts/package-app.sh" x86_64
echo ""

rm -rf "$RELEASE" "$STAGE"
mkdir -p "$RELEASE"

make_dmg() {
  local arch="$1"
  local tag="$2"
  local label="$3"
  local app="$ROOT/dist/$arch/${APP_NAME}.app"
  local volname="${APP_NAME} ${label}"
  local dmg="$RELEASE/${APP_NAME}-${VERSION}-${tag}.dmg"
  local work="$STAGE/$arch"

  rm -rf "$work"
  mkdir -p "$work"
  cp -R "$app" "$work/${APP_NAME}.app"
  ln -s /Applications "$work/Applications"

  # Install readme (UTF-8)
  /usr/bin/python3 - <<PY
from pathlib import Path
text = """${APP_NAME} ${VERSION} — ${label} 版 · 超级工具箱

安装方法：
1. 打开本磁盘映像
2. 将 ${APP_NAME} 拖到「应用程序」文件夹
3. 打开「应用程序」→ ${APP_NAME}

系统要求：
• macOS 13.0 或更高
• 本包架构：${label}
• 需要系统自带 Python 3（或 Homebrew Python）
• 首次启动会自动安装必要依赖（psutil / PyObjC）

若提示「无法打开，因为无法验证开发者」：
  系统设置 → 隐私与安全性 → 仍要打开
  或在终端执行：
  xattr -dr com.apple.quarantine /Applications/${APP_NAME}.app

官网包仅 ad-hoc 签名，适合本机/内部分发。
"""
Path("$work/安装说明.txt").write_text(text, encoding="utf-8")
PY

  # Clear quarantine on staged app
  xattr -dr com.apple.quarantine "$work" 2>/dev/null || true

  rm -f "$dmg"
  hdiutil create \
    -volname "$volname" \
    -srcfolder "$work" \
    -ov -format UDZO \
    -imagekey zlib-level=9 \
    "$dmg" >/dev/null

  echo "  ✓ $dmg ($(du -h "$dmg" | awk '{print $1}'))"
  file "$app/Contents/MacOS/${APP_NAME}" | sed 's|^|    |'
}

echo "→ 打包 DMG…"
make_dmg arm64 "AppleSilicon" "Apple Silicon (M芯片)"
make_dmg x86_64 "Intel" "Intel"

# SHA256 checksums
(
  cd "$RELEASE"
  shasum -a 256 *.dmg > SHA256SUMS.txt
)

rm -rf "$STAGE"

# Point convenience symlink at this Mac's native arch
HOST_ARCH="$(uname -m)"
case "$HOST_ARCH" in
  arm64|x86_64) ;;
  *) HOST_ARCH="arm64" ;;
esac
for name in SupTools SysPulse SystemMonit; do
  if [ -e "$ROOT/dist/${name}.app" ] || [ -L "$ROOT/dist/${name}.app" ]; then
    rm -rf "$ROOT/dist/${name}.app"
  fi
  ln -sfn "$HOST_ARCH/${APP_NAME}.app" "$ROOT/dist/${name}.app"
done
find "$ROOT/dist" -name '.DS_Store' -delete 2>/dev/null || true

echo ""
echo "════════════════════════════════════════"
echo " 完成。安装包目录："
echo "   $RELEASE"
ls -lh "$RELEASE"
echo "════════════════════════════════════════"
echo ""
echo "使用方式：把对应芯片的 .dmg 发给用户，打开后拖到「应用程序」即可。"
