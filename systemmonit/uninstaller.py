"""Software uninstaller — list apps, find leftovers, remove like CleanMyMac-class tools."""

from __future__ import annotations

import os
import plistlib
import re
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .cleaner import CancelToken, format_size, _dir_size, _trash_path

HOME = Path.home()
ProgressCb = Callable[[Dict[str, Any]], None]

# Never offer these for uninstall
_PROTECTED_BUNDLE_IDS = {
    "com.apple.finder",
    "com.apple.dock",
    "com.apple.systempreferences",
    "com.apple.loginwindow",
    "com.apple.Safari",
    "com.apple.Terminal",
    "com.apple.dt.Xcode",
    "com.suptools.app",
}

_PROTECTED_NAME_HINTS = {
    "finder",
    "dock",
    "system settings",
    "system preferences",
    "suptools",
}

_LEFTOVER_ROOTS: List[Tuple[str, Path, str]] = [
    ("preferences", HOME / "Library" / "Preferences", "偏好设置"),
    ("caches", HOME / "Library" / "Caches", "缓存"),
    ("support", HOME / "Library" / "Application Support", "应用支持"),
    ("containers", HOME / "Library" / "Containers", "沙盒容器"),
    ("group_containers", HOME / "Library" / "Group Containers", "共享容器"),
    ("saved_state", HOME / "Library" / "Saved Application State", "已保存状态"),
    ("logs", HOME / "Library" / "Logs", "日志"),
    ("launch_agents", HOME / "Library" / "LaunchAgents", "登录项"),
    ("http_storages", HOME / "Library" / "HTTPStorages", "网络存储"),
    ("cookies", HOME / "Library" / "Cookies", "Cookies"),
    ("webkit", HOME / "Library" / "WebKit", "WebKit"),
    ("scripts", HOME / "Library" / "Application Scripts", "应用脚本"),
    ("quicklook", HOME / "Library" / "QuickLook", "Quick Look"),
    ("services", HOME / "Library" / "Services", "服务"),
    ("internet_plugins", HOME / "Library" / "Internet Plug-Ins", "浏览器插件"),
    ("preference_panes", HOME / "Library" / "PreferencePanes", "设置面板"),
    ("fonts", HOME / "Library" / "Fonts", "字体"),
    ("color_pickers", HOME / "Library" / "ColorPickers", "取色器"),
    ("input_methods", HOME / "Library" / "Input Methods", "输入法"),
    ("screen_savers", HOME / "Library" / "Screen Savers", "屏保"),
]


@dataclass
class UninstallResult:
    freed_bytes: int = 0
    removed_items: int = 0
    errors: List[str] = field(default_factory=list)
    moved_to_trash: bool = True
    cancelled: bool = False


def _fmt(n: int) -> str:
    return format_size(n)


def _emit(progress: Optional[ProgressCb], **kwargs) -> None:
    if progress:
        try:
            progress(kwargs)
        except Exception:
            pass


def _rel_display(path: Path) -> str:
    try:
        return str(path).replace(str(HOME), "~")
    except Exception:
        return str(path)


def _read_plist(path: Path) -> Dict[str, Any]:
    try:
        with path.open("rb") as fh:
            data = plistlib.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalize_token(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _app_tokens(name: str, bundle_id: str) -> Set[str]:
    tokens: Set[str] = set()
    if name:
        tokens.add(_normalize_token(name))
        tokens.add(name.lower().strip())
        # Drop common suffixes for matching "Google Chrome" → also "chrome"
        for part in re.split(r"[\s_\-]+", name):
            if len(part) >= 3:
                tokens.add(part.lower())
                tokens.add(_normalize_token(part))
    if bundle_id:
        bid = bundle_id.lower().strip()
        tokens.add(bid)
        tokens.add(_normalize_token(bid))
        parts = [p for p in bid.split(".") if p]
        for p in parts:
            if len(p) >= 3 and p not in {"com", "org", "net", "app", "macos", "osx", "desktop"}:
                tokens.add(p)
                tokens.add(_normalize_token(p))
        if parts:
            tokens.add(parts[-1])
            tokens.add(_normalize_token(parts[-1]))
        if len(parts) >= 2:
            tokens.add(".".join(parts[-2:]))
        if len(parts) >= 3:
            tokens.add(".".join(parts[-3:]))
    return {t for t in tokens if t and len(t) >= 3}


def _is_protected(bundle_id: str, name: str, path: Path) -> bool:
    bid = (bundle_id or "").lower()
    if bid in _PROTECTED_BUNDLE_IDS:
        return True
    if bid.startswith("com.apple.") and str(path).startswith("/System/"):
        return True
    n = _normalize_token(name)
    if n in {_normalize_token(x) for x in _PROTECTED_NAME_HINTS}:
        return True
    if "suptools" in n or "syspulse" in n or "systemmonit" in n:
        return True
    try:
        if path.resolve() == Path("/Applications/SupTools.app").resolve():
            return True
    except Exception:
        pass
    return False


def _strong_tokens(name: str, bundle_id: str) -> Set[str]:
    """Tokens that uniquely identify the app (not shared vendor names)."""
    strong: Set[str] = set()
    if name:
        strong.add(_normalize_token(name))
        strong.add(name.lower().strip())
    if bundle_id:
        bid = bundle_id.lower().strip()
        strong.add(bid)
        strong.add(_normalize_token(bid))
        parts = [p for p in bid.split(".") if p]
        if parts:
            strong.add(parts[-1])
            strong.add(_normalize_token(parts[-1]))
        if len(parts) >= 2:
            strong.add(".".join(parts[-2:]))
    return {t for t in strong if t and len(t) >= 3}


def _is_strong_match(child_name: str, strong: Set[str], bundle_id: str) -> bool:
    low = child_name.lower()
    norm = _normalize_token(child_name)
    bid = (bundle_id or "").lower()
    if bid and (low == bid or low == f"{bid}.plist" or low.startswith(bid + ".") or low == bid + ".savedstate"):
        return True
    if bid and bid in low:
        return True
    for t in strong:
        if low == t or norm == _normalize_token(t):
            return True
        if len(t) >= 5 and (t in low or _normalize_token(t) in norm):
            return True
    return False


def _match_score(child_name: str, tokens: Set[str], bundle_id: str, strong: Optional[Set[str]] = None) -> Tuple[bool, str]:
    """Return (matched, risk) where risk is safe|caution."""
    strong = strong or set()
    if _is_strong_match(child_name, strong, bundle_id):
        return True, "safe"
    name = child_name
    low = name.lower()
    norm = _normalize_token(name)
    for t in tokens:
        if not t:
            continue
        if low == t or norm == _normalize_token(t):
            return True, "caution" if t not in strong else "safe"
        if len(t) >= 4 and (t in low or _normalize_token(t) in norm):
            if len(t) < 5 or t not in strong:
                return True, "caution"
            return True, "safe"
    return False, "safe"


def _icon_data_url(app_path: Path, max_px: int = 48) -> str:
    """Best-effort app icon as a small PNG data URL for the UI.

    NSWorkspace icons are high-DPI; exporting TIFFRepresentation() raw can be
    1–2MB each and break the WKWebView bridge. Always rasterize to max_px.
    """
    try:
        import base64

        from AppKit import (  # type: ignore
            NSBitmapImageRep,
            NSGraphicsContext,
            NSImageInterpolationHigh,
            NSWorkspace,
        )

        icon = NSWorkspace.sharedWorkspace().iconForFile_(str(app_path))
        if icon is None:
            return ""
        icon = icon.copy()
        w = h = max(16, int(max_px))
        icon.setSize_((float(w), float(h)))
        rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None,
            w,
            h,
            8,
            4,
            True,
            False,
            "NSDeviceRGBColorSpace",
            0,
            0,
        )
        if rep is None:
            return ""
        NSGraphicsContext.saveGraphicsState()
        try:
            ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
            if ctx is None:
                return ""
            NSGraphicsContext.setCurrentContext_(ctx)
            ctx.setImageInterpolation_(NSImageInterpolationHigh)
            icon.drawInRect_fromRect_operation_fraction_(
                ((0.0, 0.0), (float(w), float(h))),
                ((0.0, 0.0), (0.0, 0.0)),
                2,  # NSCompositingOperationSourceOver
                1.0,
            )
        finally:
            NSGraphicsContext.restoreGraphicsState()
        # NSPNGFileType == 4
        png = rep.representationUsingType_properties_(4, None)
        if png is None:
            return ""
        data = bytes(png)
        # Guard against accidental huge payloads
        if len(data) > 80_000:
            return ""
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")
    except Exception:
        return ""


def _last_used(path: Path) -> Optional[float]:
    try:
        import subprocess

        out = subprocess.check_output(
            ["mdls", "-name", "kMDItemLastUsedDate", "-raw", str(path)],
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        text = out.decode("utf-8", "ignore").strip()
        if not text or text == "(null)":
            return None
        # 2024-01-15 12:34:56 +0000
        from datetime import datetime

        for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).timestamp()
            except ValueError:
                continue
    except Exception:
        pass
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _discover_app_dirs() -> List[Path]:
    roots = [
        Path("/Applications"),
        HOME / "Applications",
    ]
    # One level of vendor folders under /Applications (e.g. Utilities already separate)
    extras: List[Path] = []
    for root in list(roots):
        if not root.is_dir():
            continue
        try:
            for child in root.iterdir():
                if child.is_dir() and not child.name.endswith(".app") and not child.name.startswith("."):
                    extras.append(child)
        except OSError:
            pass
    return roots + extras


def list_apps(
    progress: Optional[ProgressCb] = None,
    cancel: Optional[CancelToken] = None,
    include_icons: bool = True,
) -> Dict[str, Any]:
    """Enumerate third-party-ish apps in Applications folders."""
    started = time.time()
    apps: List[Dict[str, Any]] = []
    cancelled = False
    seen: Set[str] = set()

    candidates: List[Path] = []
    for root in _discover_app_dirs():
        if cancel and cancel.cancelled:
            cancelled = True
            break
        if not root.is_dir():
            continue
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for child in children:
            if child.name.endswith(".app") and child.is_dir():
                try:
                    key = str(child.resolve())
                except Exception:
                    key = str(child)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(child)

    total = max(1, len(candidates))
    for i, path in enumerate(candidates):
        if cancel and cancel.cancelled:
            cancelled = True
            break
        _emit(
            progress,
            phase="list",
            percent=int(i * 100 / total),
            current=_rel_display(path),
            found=len(apps),
            index=i + 1,
            total=total,
        )
        info = _read_plist(path / "Contents" / "Info.plist")
        bundle_id = str(info.get("CFBundleIdentifier") or "")
        name = str(
            info.get("CFBundleDisplayName")
            or info.get("CFBundleName")
            or path.stem
        )
        version = str(info.get("CFBundleShortVersionString") or info.get("CFBundleVersion") or "")
        protected = _is_protected(bundle_id, name, path)
        # Skip pure system apps under /System
        if str(path).startswith("/System/"):
            continue
        size = _dir_size(path, cancel=cancel)
        if cancel and cancel.cancelled:
            cancelled = True
            break
        last_used = _last_used(path)
        item = {
            "id": f"app:{uuid.uuid4().hex[:10]}",
            "name": name,
            "path": str(path),
            "path_display": _rel_display(path),
            "bundle_id": bundle_id,
            "version": version,
            "bytes": int(size),
            "size_text": _fmt(int(size)),
            "protected": protected,
            "apple": bundle_id.startswith("com.apple."),
            "location": "用户" if str(path).startswith(str(HOME)) else "系统盘",
            "last_used": last_used,
            "last_used_text": "",
            "icon": _icon_data_url(path) if include_icons else "",
        }
        if last_used:
            try:
                from datetime import datetime

                item["last_used_text"] = datetime.fromtimestamp(last_used).strftime("%Y-%m-%d")
            except Exception:
                item["last_used_text"] = ""
        apps.append(item)

    apps.sort(key=lambda a: (-int(a.get("bytes") or 0), str(a.get("name") or "").lower()))

    total_bytes = sum(int(a["bytes"]) for a in apps)
    removable = [a for a in apps if not a.get("protected")]
    _emit(
        progress,
        phase="list_done" if not cancelled else "list_cancelled",
        percent=100 if not cancelled else 99,
        current="扫描完成" if not cancelled else "已取消",
        found=len(apps),
    )
    return {
        "apps": apps,
        "app_count": len(apps),
        "removable_count": len(removable),
        "total_bytes": total_bytes,
        "total_text": _fmt(total_bytes),
        "elapsed": round(time.time() - started, 2),
        "cancelled": cancelled,
    }


def scan_leftovers(
    app_path: str,
    bundle_id: str = "",
    app_name: str = "",
    progress: Optional[ProgressCb] = None,
    cancel: Optional[CancelToken] = None,
) -> Dict[str, Any]:
    """Find leftover files related to an application."""
    started = time.time()
    path = Path(app_path)
    if not app_name:
        app_name = path.stem
    if not bundle_id:
        info = _read_plist(path / "Contents" / "Info.plist")
        bundle_id = str(info.get("CFBundleIdentifier") or "")
        app_name = str(
            info.get("CFBundleDisplayName")
            or info.get("CFBundleName")
            or app_name
        )

    tokens = _app_tokens(app_name, bundle_id)
    strong = _strong_tokens(app_name, bundle_id)
    items: List[Dict[str, Any]] = []
    cancelled = False
    seen_paths: Set[str] = set()

    def add_item(child: Path, key: str, title: str, risk: str, selected: bool) -> None:
        try:
            keyp = str(child.resolve())
        except Exception:
            keyp = str(child)
        if keyp in seen_paths:
            return
        size = _dir_size(child, cancel=cancel)
        # Still list matched paths even if TCC / permissions hide size (size==0)
        if size <= 0 and not child.exists() and not child.is_symlink():
            return
        if risk == "caution" and size < 8 * 1024 and size > 0 and key == "preferences":
            if bundle_id and bundle_id.lower() not in child.name.lower():
                return
        if size <= 0 and child.is_dir():
            # Permission-denied trees still matter for uninstall
            size = 0
        seen_paths.add(keyp)
        display_name = child.name
        parent_name = child.parent.name if child.parent else ""
        if parent_name and parent_name not in {
            "Preferences", "Caches", "Containers", "Group Containers",
            "Logs", "LaunchAgents", "HTTPStorages", "Cookies", "WebKit",
            "Application Scripts", "QuickLook", "Services", "Internet Plug-Ins",
            "PreferencePanes", "Fonts", "ColorPickers", "Input Methods",
            "Screen Savers", "Saved Application State", "Application Support",
        }:
            display_name = f"{parent_name}/{child.name}"
        items.append({
            "id": f"{key}:{uuid.uuid4().hex[:10]}",
            "kind": "leftover",
            "category": key,
            "category_title": title,
            "name": display_name,
            "path": str(child),
            "path_display": _rel_display(child),
            "bytes": int(size),
            "size_text": _fmt(int(size)),
            "risk": risk,
            "selected": selected,
            "required": False,
            "hint": "关联文件" if risk == "safe" else "可能相关 · 请确认",
        })

    # The .app itself first
    app_size = _dir_size(path, cancel=cancel) if path.exists() else 0
    items.append({
        "id": f"bundle:{uuid.uuid4().hex[:10]}",
        "kind": "app",
        "category": "application",
        "category_title": "应用程序",
        "name": path.name,
        "path": str(path),
        "path_display": _rel_display(path),
        "bytes": int(app_size),
        "size_text": _fmt(int(app_size)),
        "risk": "caution",
        "selected": True,
        "required": True,
        "hint": "主程序",
    })
    seen_paths.add(str(path))

    roots = list(_LEFTOVER_ROOTS)
    total_roots = max(1, len(roots))
    for idx, (key, root, title) in enumerate(roots):
        if cancel and cancel.cancelled:
            cancelled = True
            break
        _emit(
            progress,
            phase="leftovers",
            percent=int(idx * 100 / total_roots),
            category=title,
            current=_rel_display(root),
            found=max(0, len(items) - 1),
        )
        if not root.is_dir():
            continue
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for child in children:
            if cancel and cancel.cancelled:
                cancelled = True
                break
            if child.name.startswith("."):
                continue
            matched, risk = _match_score(child.name, tokens, bundle_id, strong=strong)
            if not matched:
                continue
            # Vendor folder only (weak): dig one level for strong app matches
            if (
                risk == "caution"
                and child.is_dir()
                and key in ("support", "caches", "logs", "http_storages", "webkit")
                and not _is_strong_match(child.name, strong, bundle_id)
            ):
                try:
                    nested = list(child.iterdir())
                except OSError:
                    nested = []
                nested_hits = 0
                for sub in nested:
                    if sub.name.startswith("."):
                        continue
                    if _is_strong_match(sub.name, strong, bundle_id) or _match_score(sub.name, strong, bundle_id, strong=strong)[0]:
                        add_item(sub, key, title, "safe", True)
                        nested_hits += 1
                if nested_hits:
                    continue
                # No nested strong hit — keep weak folder as caution / unselected
                add_item(child, key, title, "caution", False)
                continue
            add_item(child, key, title, risk, risk == "safe")

    items.sort(key=lambda x: (
        0 if x.get("kind") == "app" else 1,
        0 if x.get("risk") == "safe" else 1,
        -int(x.get("bytes") or 0),
    ))

    leftover_items = [i for i in items if i.get("kind") != "app"]
    leftover_bytes = sum(int(i["bytes"]) for i in leftover_items)
    selected_bytes = sum(int(i["bytes"]) for i in items if i.get("selected"))
    categories: List[Dict[str, Any]] = []
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        by_cat.setdefault(str(it["category"]), []).append(it)
    for key, group in by_cat.items():
        categories.append({
            "key": key,
            "title": group[0].get("category_title") or key,
            "bytes": sum(int(i["bytes"]) for i in group),
            "size_text": _fmt(sum(int(i["bytes"]) for i in group)),
            "count": len(group),
        })

    _emit(
        progress,
        phase="leftovers_done" if not cancelled else "leftovers_cancelled",
        percent=100 if not cancelled else 99,
        current="关联文件扫描完成" if not cancelled else "已取消",
        found=len(leftover_items),
    )

    return {
        "app": {
            "name": app_name,
            "path": str(path),
            "path_display": _rel_display(path),
            "bundle_id": bundle_id,
            "bytes": int(app_size),
            "size_text": _fmt(int(app_size)),
            "protected": _is_protected(bundle_id, app_name, path),
            "icon": _icon_data_url(path),
        },
        "items": items,
        "categories": categories,
        "leftover_count": len(leftover_items),
        "leftover_bytes": leftover_bytes,
        "leftover_text": _fmt(leftover_bytes),
        "selected_bytes": selected_bytes,
        "selected_text": _fmt(selected_bytes),
        "total_bytes": sum(int(i["bytes"]) for i in items),
        "total_text": _fmt(sum(int(i["bytes"]) for i in items)),
        "elapsed": round(time.time() - started, 2),
        "cancelled": cancelled,
    }


def _rm_one(path: Path, result: UninstallResult, move_to_trash: bool) -> None:
    try:
        if not path.exists() and not path.is_symlink():
            return
        if move_to_trash:
            size = path.lstat().st_size if path.is_file() or path.is_symlink() else _dir_size(path)
            if _trash_path(path):
                result.freed_bytes += size
                result.removed_items += 1
                return
        if path.is_symlink() or path.is_file():
            size = path.lstat().st_size
            path.unlink(missing_ok=True)
            result.freed_bytes += size
            result.removed_items += 1
            return
        if path.is_dir():
            size_before = _dir_size(path)
            shutil.rmtree(path, ignore_errors=False)
            result.freed_bytes += size_before
            result.removed_items += 1
    except Exception as exc:  # noqa: BLE001
        # Partial delete fallback
        try:
            if path.is_dir():
                size_before = _dir_size(path)
                shutil.rmtree(path, ignore_errors=True)
                if not path.exists():
                    result.freed_bytes += size_before
                    result.removed_items += 1
                    return
            result.errors.append(f"{path}: {exc}")
        except Exception as exc2:  # noqa: BLE001
            result.errors.append(f"{path}: {exc2}")


def uninstall_items(
    items: List[Dict[str, Any]],
    progress: Optional[ProgressCb] = None,
    move_to_trash: bool = True,
    cancel: Optional[CancelToken] = None,
) -> UninstallResult:
    """Remove selected app + leftover paths."""
    result = UninstallResult(moved_to_trash=bool(move_to_trash))
    # App bundle last so leftovers can still be read if needed; actually app first is fine
    ordered = sorted(items, key=lambda x: 0 if x.get("kind") == "app" else 1)
    total = max(1, len(ordered))
    for i, it in enumerate(ordered):
        if cancel and cancel.cancelled:
            result.cancelled = True
            break
        path = Path(str(it.get("path") or ""))
        # Safety: refuse protected system paths
        if str(path).startswith("/System/") or str(path).startswith("/usr/"):
            result.errors.append(f"{path}: 受保护的系统路径，已跳过")
            continue
        bid = ""
        if path.suffix == ".app":
            info = _read_plist(path / "Contents" / "Info.plist")
            bid = str(info.get("CFBundleIdentifier") or "")
            if _is_protected(bid, path.stem, path):
                result.errors.append(f"{path.name}: 受保护应用，已跳过")
                continue
        _emit(
            progress,
            phase="uninstall",
            percent=int(i * 100 / total),
            current=_rel_display(path),
            category=it.get("category_title") or "",
            cleaned_items=result.removed_items,
            freed_bytes=result.freed_bytes,
            index=i + 1,
            total=total,
        )
        _rm_one(path, result, move_to_trash=move_to_trash)

    _emit(
        progress,
        phase="uninstall_done" if not result.cancelled else "uninstall_cancelled",
        percent=100 if not result.cancelled else int(result.removed_items * 100 / total),
        current="卸载完成" if not result.cancelled else "已取消",
        cleaned_items=result.removed_items,
        freed_bytes=result.freed_bytes,
    )
    return result
