#!/usr/bin/env python3
"""Capture SupTools marketing screenshots via WKWebView.takeSnapshot."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from AppKit import (  # type: ignore
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyRegular,
    NSBackingStoreBuffered,
    NSBitmapImageRep,
    NSColor,
    NSMakeRect,
    NSWindow,
    NSWindowStyleMaskTitled,
)
from Foundation import NSDate, NSRunLoop, NSURL  # type: ignore
from WebKit import WKSnapshotConfiguration, WKWebView, WKWebViewConfiguration  # type: ignore

from systemmonit import permissions as perm_mod
from systemmonit.brand import APP_NAME
from systemmonit.collector import MetricsCollector
from systemmonit.dashboard_html import DASHBOARD_HTML
from systemmonit.native_app import snapshot_to_payload

OUT = ROOT / "docs" / "assets"
SIZE = (1280, 900)

FIX_CSS = """
<style id="capture-fix">
  * { backdrop-filter: none !important; -webkit-backdrop-filter: none !important; }
  body, #app, main, .content, .page {
    background: #f3f6f9 !important;
    opacity: 1 !important;
  }
  .hero { display: none !important; }
  .kpi, .card, .info-pill, .clean-hero, .un-hero, .su-hero, .perm-page-hero,
  .su-list, .perm-list, .un-apps, .shot-actions, .settings-group {
    background: #ffffff !important;
    color: #1c1c1e !important;
    box-shadow: 0 8px 28px rgba(15, 35, 55, 0.08) !important;
  }
  .kpi .value, .kpi .label, .kpi .sub, .card, .card * { color: inherit; }
  aside {
    background: rgba(255,255,255,0.92) !important;
  }
</style>
"""


def pump(seconds: float = 0.4) -> None:
    end = time.time() + seconds
    while time.time() < end:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))


def save_nsimage(image, path: Path) -> bool:
    if image is None:
        return False
    tiff = image.TIFFRepresentation()
    if not tiff:
        return False
    rep = NSBitmapImageRep.imageRepWithData_(tiff)
    if not rep:
        return False
    png = rep.representationUsingType_properties_(4, None)
    if not png:
        return False
    path.write_bytes(bytes(png))
    return path.exists() and path.stat().st_size > 8000


def boot_html(page: str, bundle: dict) -> str:
    payload = json.dumps(bundle, ensure_ascii=True)
    script = f"""
{FIX_CSS}
<script>
(function(){{
  const PAGE = {json.dumps(page)};
  const DATA = {payload};
  function apply() {{
    try {{
      document.body.setAttribute('data-theme','light');
      document.body.setAttribute('data-glass','opaque');
      if (window.__setTheme) window.__setTheme({{theme:'light', glass:'opaque'}});
      if (DATA.metrics && window.__setMetrics) window.__setMetrics(DATA.metrics);
      if (DATA.clean && window.__setCleanScan) window.__setCleanScan(DATA.clean);
      if (DATA.uninstall && window.__setUninstallApps) window.__setUninstallApps(DATA.uninstall);
      if (DATA.startup && window.__setStartupList) window.__setStartupList(DATA.startup);
      if (DATA.perms && window.__setPermissionsStatus) window.__setPermissionsStatus(DATA.perms);
      const titles = (typeof TITLES !== 'undefined') ? TITLES : {{
        overview:'总览',clean:'清理',uninstall:'卸载',startup:'启动项',perms:'权限',shot:'截图'
      }};
      page = PAGE;
      document.body.setAttribute('data-page', PAGE);
      document.querySelectorAll('.nav button[data-page]').forEach(b => {{
        b.classList.toggle('active', b.getAttribute('data-page') === PAGE);
      }});
      document.querySelectorAll('.page').forEach(p => {{
        p.classList.toggle('active', p.id === 'page-' + PAGE);
      }});
      const t = document.getElementById('title');
      if (t) t.textContent = titles[PAGE] || PAGE;
      const content = document.querySelector('.content');
      if (content) content.scrollTop = 0;
      window.__CAPTURE_READY = true;
    }} catch (e) {{
      window.__CAPTURE_ERR = String(e);
      window.__CAPTURE_READY = true;
    }}
  }}
  function wait() {{
    if (typeof window.__setMetrics === 'function') setTimeout(apply, 200);
    else setTimeout(wait, 60);
  }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wait);
  else wait();
}})();
</script>
"""
    return DASHBOARD_HTML.replace("</body>", script + "\n</body>")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    NSApplication.sharedApplication()
    NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(40, 40, SIZE[0], SIZE[1]),
        NSWindowStyleMaskTitled,
        NSBackingStoreBuffered,
        False,
    )
    window.setTitle_(APP_NAME)
    window.setBackgroundColor_(NSColor.windowBackgroundColor())
    webview = WKWebView.alloc().initWithFrame_configuration_(
        window.contentView().bounds(),
        WKWebViewConfiguration.alloc().init(),
    )
    try:
        webview.setValue_forKey_(True, "drawsBackground")
    except Exception:
        pass
    window.setContentView_(webview)
    window.makeKeyAndOrderFront_(None)
    NSApp.activateIgnoringOtherApps_(True)

    collector = MetricsCollector()
    metrics = snapshot_to_payload(
        collector,
        collector.sample(include_processes=True, include_interfaces=True),
        page="overview",
        panel_visible=True,
    )
    clean = {
        "items": [
            {"id": "c1", "name": "Xcode DerivedData", "path": "~/Library/Developer/Xcode/DerivedData", "path_display": "~/Library/Developer/Xcode/DerivedData", "category": "dev", "category_title": "开发者", "bytes": 2100000000, "size_text": "2.0 GB", "selected": True, "risk": "safe", "files": 4200},
            {"id": "c2", "name": "系统缓存", "path": "~/Library/Caches", "path_display": "~/Library/Caches", "category": "cache", "category_title": "系统缓存", "bytes": 860000000, "size_text": "820 MB", "selected": True, "risk": "safe", "files": 1800},
            {"id": "c3", "name": "Chrome 缓存", "path": "~/Library/Caches/Google/Chrome", "path_display": "~/Library/Caches/Google/Chrome", "category": "browser", "category_title": "浏览器", "bytes": 410000000, "size_text": "391 MB", "selected": True, "risk": "safe", "files": 960},
            {"id": "c4", "name": "废纸篓", "path": "~/.Trash", "path_display": "~/.Trash", "category": "trash", "category_title": "废纸篓", "bytes": 220000000, "size_text": "210 MB", "selected": False, "risk": "caution", "files": 48},
        ],
        "categories": [
            {"key": "dev", "title": "开发者", "bytes": 2100000000, "size_text": "2.0 GB", "count": 1, "icon": "dev", "risk": "safe"},
            {"key": "cache", "title": "系统缓存", "bytes": 860000000, "size_text": "820 MB", "count": 1, "icon": "cache", "risk": "safe"},
            {"key": "browser", "title": "浏览器", "bytes": 410000000, "size_text": "391 MB", "count": 1, "icon": "browser", "risk": "safe"},
            {"key": "trash", "title": "废纸篓", "bytes": 220000000, "size_text": "210 MB", "count": 1, "icon": "trash", "risk": "caution"},
        ],
        "recommend_ids": ["c1", "c2", "c3"],
        "total_bytes": 3590000000,
        "total_text": "3.3 GB",
        "safe_bytes": 3370000000,
        "safe_text": "3.1 GB",
        "selected_bytes": 3370000000,
        "selected_text": "3.1 GB",
        "item_count": 4,
        "selected_count": 3,
        "trash_bytes": 220000000,
        "elapsed": 2.1,
    }
    uninstall = {
        "apps": [
            {"name": "Google Chrome", "path": "/Applications/Google Chrome.app", "size_text": "512 MB", "bytes": 536870912, "location": "系统盘", "version": "128.0", "icon": "", "protected": False, "bundle_id": "com.google.Chrome"},
            {"name": "Telegram", "path": "/Applications/Telegram.app", "size_text": "186 MB", "bytes": 195035136, "location": "系统盘", "version": "11.0", "icon": "", "protected": False, "bundle_id": "ru.keepcoder.Telegram"},
            {"name": "Visual Studio Code", "path": "/Applications/Visual Studio Code.app", "size_text": "428 MB", "bytes": 449050624, "location": "系统盘", "version": "1.92", "icon": "", "protected": False, "bundle_id": "com.microsoft.VSCode"},
            {"name": "SupTools", "path": "/Applications/SupTools.app", "size_text": "12 MB", "bytes": 12582912, "location": "系统盘", "version": "1.27.0", "icon": "", "protected": True, "bundle_id": "com.suptools.app"},
        ],
        "app_count": 4,
        "removable_count": 3,
        "total_bytes": 1193739264,
        "total_text": "1.1 GB",
    }
    startup = {
        "items": [
            {"id": "a1", "name": "Google Updater", "label": "com.google.GoogleUpdater.wake", "kind": "launch_agent", "scope": "user", "path": "~/Library/LaunchAgents/x.plist", "path_display": "~/Library/LaunchAgents/…", "enabled": True, "disabled": False, "protected": False, "detail": "运行中 · 登录启动", "risk": "safe"},
            {"id": "a2", "name": "千问", "label": "千问", "kind": "login_item", "scope": "user", "path": "/Applications/Qianwen.app", "path_display": "/Applications/Qianwen.app", "enabled": True, "disabled": False, "protected": False, "detail": "登录时打开", "risk": "safe"},
            {"id": "a3", "name": "LemonMonitor", "label": "com.tencent.LemonMonitor", "kind": "launch_agent", "scope": "system", "path": "/Library/LaunchAgents/y.plist", "path_display": "/Library/LaunchAgents/…", "enabled": True, "disabled": False, "protected": False, "detail": "运行中", "risk": "caution"},
            {"id": "a4", "name": "caffeinate", "label": "ai.openclaw.keepawake", "kind": "launch_agent", "scope": "user", "path": "~/Library/LaunchAgents/z.plist", "path_display": "~/Library/LaunchAgents/…", "enabled": False, "disabled": True, "protected": False, "detail": "已禁用", "risk": "safe"},
        ],
        "item_count": 4,
        "enabled_count": 3,
        "disabled_count": 1,
        "login_count": 1,
        "agent_count": 3,
        "elapsed": 0.4,
    }
    try:
        perms = perm_mod.permissions_status(app_name=APP_NAME)
    except Exception:
        perms = {"items": [], "summary": "—", "required_granted": 0, "required_count": 3, "granted_count": 0, "item_count": 0}

    pages = {
        "overview": {"metrics": metrics},
        "clean": {"metrics": metrics, "clean": clean},
        "uninstall": {"metrics": metrics, "uninstall": uninstall},
        "startup": {"metrics": metrics, "startup": startup},
        "perms": {"metrics": metrics, "perms": perms},
        "shot": {"metrics": metrics},
    }

    saved: list[Path] = []
    for page, bundle in pages.items():
        webview.loadHTMLString_baseURL_(boot_html(page, bundle), NSURL.URLWithString_("about:blank"))
        ready = False
        for _ in range(60):
            pump(0.08)
            box = {"v": False}

            def cb(res, _err, _box=box):
                _box["v"] = bool(res)

            webview.evaluateJavaScript_completionHandler_("window.__CAPTURE_READY===true", cb)
            pump(0.04)
            if box["v"]:
                ready = True
                break
        pump(1.0)
        dest = OUT / f"shot-{page}.png"
        state = {"done": False, "ok": False}

        def handler(image, error, _dest=dest, _state=state):
            try:
                _state["ok"] = save_nsimage(image, _dest)
            except Exception as exc:
                print("save err", exc)
            _state["done"] = True

        cfg = WKSnapshotConfiguration.alloc().init()
        try:
            cfg.setRect_(webview.bounds())
        except Exception:
            pass
        webview.takeSnapshotWithConfiguration_completionHandler_(cfg, handler)
        for _ in range(100):
            if state["done"]:
                break
            pump(0.05)
        print(("✓" if state["ok"] else "✗"), dest.name, "ready=", ready, dest.stat().st_size if dest.exists() else 0)
        if state["ok"]:
            saved.append(dest)

    try:
        from PIL import Image, ImageDraw, ImageFilter

        for path in saved:
            img = Image.open(path).convert("RGBA")
            pad = 40
            canvas = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (243, 250, 248, 255))
            shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.rounded_rectangle(
                [pad - 4, pad + 8, pad + img.width + 4, pad + img.height + 14],
                radius=22,
                fill=(8, 30, 50, 50),
            )
            shadow = shadow.filter(ImageFilter.GaussianBlur(18))
            canvas = Image.alpha_composite(canvas, shadow)
            canvas.paste(img, (pad, pad), img)
            jpg = path.with_name(path.stem + "-web.jpg")
            canvas.convert("RGB").save(jpg, "JPEG", quality=90, optimize=True)
            print("jpg", jpg.name, jpg.stat().st_size)
    except Exception as exc:
        print("jpeg skip", exc)

    window.orderOut_(None)
    print(f"captured {len(saved)}/{len(pages)} → {OUT}")


if __name__ == "__main__":
    main()
