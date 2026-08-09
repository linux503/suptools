"""macOS privacy permission helpers + System Settings deep links."""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HOME = Path.home()

# TCC pane identifiers (work across recent macOS releases with fallbacks)
_PRIVACY_URLS = {
    "screen": [
        "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        "x-apple.systempreferences:com.apple.Settings.PrivacySecurity.extension?Privacy_ScreenCapture",
        "x-apple.systempreferences:com.apple.settings.PrivacySecurity.Privacy_ScreenCapture",
    ],
    "accessibility": [
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        "x-apple.systempreferences:com.apple.Settings.PrivacySecurity.extension?Privacy_Accessibility",
    ],
    "microphone": [
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone",
        "x-apple.systempreferences:com.apple.Settings.PrivacySecurity.extension?Privacy_Microphone",
    ],
    "full_disk": [
        "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles",
        "x-apple.systempreferences:com.apple.Settings.PrivacySecurity.extension?Privacy_AllFiles",
    ],
    "automation": [
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation",
        "x-apple.systempreferences:com.apple.Settings.PrivacySecurity.extension?Privacy_Automation",
    ],
    "files": [
        "x-apple.systempreferences:com.apple.preference.security?Privacy_FilesAndFolders",
        "x-apple.systempreferences:com.apple.Settings.PrivacySecurity.extension?Privacy_FilesAndFolders",
    ],
    "notifications": [
        "x-apple.systempreferences:com.apple.preference.notifications",
        "x-apple.systempreferences:com.apple.Notifications-Settings.extension",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Notifications",
    ],
    "login_items": [
        "x-apple.systempreferences:com.apple.LoginItems-Settings.extension",
        "x-apple.systempreferences:com.apple.LoginItems-Settings.extension?key=loginItems",
    ],
    "privacy": [
        "x-apple.systempreferences:com.apple.preference.security",
        "x-apple.systempreferences:com.apple.Settings.PrivacySecurity.extension",
    ],
}


def _normalize_kind(kind: str) -> str:
    key = str(kind or "screen").lower().strip()
    aliases = {
        "screen_recording": "screen",
        "screencapture": "screen",
        "capture": "screen",
        "a11y": "accessibility",
        "ax": "accessibility",
        "hotkey": "accessibility",
        "hotkeys": "accessibility",
        "mic": "microphone",
        "audio_input": "microphone",
        "fda": "full_disk",
        "full_disk_access": "full_disk",
        "allfiles": "full_disk",
        "appleevents": "automation",
        "system_events": "automation",
        "files_folders": "files",
        "folders": "files",
        "notify": "notifications",
        "notification": "notifications",
        "login": "login_items",
        "loginitems": "login_items",
    }
    return aliases.get(key, key)


def _cg() -> Optional[ctypes.CDLL]:
    try:
        return ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    except Exception:
        return None


def _ax_lib() -> Optional[ctypes.CDLL]:
    for path in (
        "/System/Library/Frameworks/ApplicationServices.framework/Frameworks/HIServices.framework/HIServices",
        "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices",
    ):
        try:
            return ctypes.cdll.LoadLibrary(path)
        except Exception:
            continue
    return None


def screen_capture_granted() -> Optional[bool]:
    """Return True/False if API exists; None if unknown."""
    lib = _cg()
    if lib is None:
        return None
    fn = getattr(lib, "CGPreflightScreenCaptureAccess", None)
    if fn is None:
        return None
    try:
        fn.restype = ctypes.c_bool
        return bool(fn())
    except Exception:
        return None


def request_screen_capture() -> Optional[bool]:
    """Prompt the system Screen Recording permission sheet when possible."""
    lib = _cg()
    if lib is None:
        return None
    fn = getattr(lib, "CGRequestScreenCaptureAccess", None)
    if fn is None:
        return None
    try:
        fn.restype = ctypes.c_bool
        return bool(fn())
    except Exception:
        return None


def accessibility_granted() -> Optional[bool]:
    lib = _ax_lib()
    if lib is None:
        return None
    fn = getattr(lib, "AXIsProcessTrusted", None)
    if fn is None:
        return None
    try:
        fn.restype = ctypes.c_bool
        return bool(fn())
    except Exception:
        return None


def request_accessibility(prompt: bool = True) -> Optional[bool]:
    """Check Accessibility; optionally show the system prompt sheet."""
    lib = _ax_lib()
    if lib is None:
        return accessibility_granted()
    fn = getattr(lib, "AXIsProcessTrustedWithOptions", None)
    if fn is None:
        return accessibility_granted()
    try:
        import objc  # type: ignore
        from Foundation import NSDictionary, NSNumber  # type: ignore

        opts = NSDictionary.dictionaryWithObject_forKey_(
            NSNumber.numberWithBool_(bool(prompt)),
            "AXTrustedCheckOptionPrompt",
        )
        fn.argtypes = [ctypes.c_void_p]
        fn.restype = ctypes.c_bool
        return bool(fn(ctypes.c_void_p(int(objc.pyobjc_id(opts)))))
    except Exception:
        return accessibility_granted()


def microphone_status() -> Optional[int]:
    """AVAuthorizationStatus: 0 notDetermined, 1 restricted, 2 denied, 3 authorized."""
    try:
        import objc  # type: ignore
        from Foundation import NSBundle  # type: ignore

        bundle = NSBundle.bundleWithPath_("/System/Library/Frameworks/AVFoundation.framework")
        if bundle is not None:
            bundle.load()
        AVCaptureDevice = objc.lookUpClass("AVCaptureDevice")
        # AVMediaTypeAudio == "soun"
        return int(AVCaptureDevice.authorizationStatusForMediaType_("soun"))
    except Exception:
        return None


def microphone_granted() -> Optional[bool]:
    st = microphone_status()
    if st is None:
        return None
    if st == 3:
        return True
    if st in (1, 2):
        return False
    return False  # notDetermined → treat as not yet granted for UI


def request_microphone() -> Optional[bool]:
    """Trigger mic permission prompt (async under the hood; returns current status)."""
    try:
        import objc  # type: ignore
        from Foundation import NSBundle, NSRunLoop, NSDate  # type: ignore

        bundle = NSBundle.bundleWithPath_("/System/Library/Frameworks/AVFoundation.framework")
        if bundle is not None:
            bundle.load()
        AVCaptureDevice = objc.lookUpClass("AVCaptureDevice")
        done = {"v": None}

        def _cb(granted: bool) -> None:
            done["v"] = bool(granted)

        try:
            AVCaptureDevice.requestAccessForMediaType_completionHandler_("soun", _cb)
            for _ in range(40):
                if done["v"] is not None:
                    break
                NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
        except Exception:
            # Block signature may fail on some PyObjC builds — still poke status
            pass
        return microphone_granted()
    except Exception:
        return microphone_granted()


def _can_list(path: Path) -> Optional[bool]:
    try:
        if not path.exists():
            return None
        next(path.iterdir(), None)
        return True
    except PermissionError:
        return False
    except OSError:
        return False
    except Exception:
        return None


def runtime_tcc_identity() -> Dict[str, Any]:
    """What macOS TCC actually attributes this process to (often Python, not SupTools.app)."""
    bundle_id = ""
    bundle_path = ""
    exe_name = Path(sys.executable).name if getattr(sys, "executable", None) else "python3"
    display = exe_name
    try:
        from Foundation import NSBundle  # type: ignore

        nb = NSBundle.mainBundle()
        bundle_id = str(nb.bundleIdentifier() or "")
        bundle_path = str(nb.bundlePath() or "")
        info = nb.infoDictionary() or {}
        display = str(
            info.get("CFBundleDisplayName")
            or info.get("CFBundleName")
            or Path(bundle_path).stem
            or exe_name
        )
    except Exception:
        pass

    app_bundle = (
        os.environ.get("SUPTOOLS_APP_BUNDLE")
        or os.environ.get("SYSPULSE_APP_BUNDLE")
        or os.environ.get("SYSTEMMONIT_APP_BUNDLE")
        or ""
    )
    expected_id = "com.suptools.app"
    is_app_identity = bundle_id == expected_id or bundle_id.endswith(".suptools.app")
    # Common launcher case: NSBundle is Python.app while SUPTOOLS_APP_BUNDLE points at SupTools.app
    mismatch = bool(app_bundle) and not is_app_identity
    if "python" in (bundle_id or "").lower() or "python" in display.lower():
        look_for = "Python"
    elif mismatch:
        look_for = display or "Python"
    else:
        look_for = "SupTools"

    hint = ""
    if mismatch or not is_app_identity:
        hint = (
            f"当前进程身份是「{look_for}」（{bundle_id or exe_name}），"
            f"不是列表里的「SupTools」本身。"
            f"请在系统设置中勾选「{look_for}」，点「请求授权」可弹出对应授权框；"
            f"只勾选 SupTools 时，本页常会仍显示未开启。"
        )
    return {
        "bundle_id": bundle_id,
        "bundle_path": bundle_path,
        "executable": str(getattr(sys, "executable", "") or ""),
        "display_name": display,
        "look_for": look_for,
        "app_bundle": app_bundle,
        "is_app_identity": is_app_identity,
        "mismatch": mismatch or not is_app_identity,
        "hint": hint,
    }


def notifications_granted() -> Optional[bool]:
    """UNUserNotificationCenter authorization: 2=authorized, 3=provisional, 4=ephemeral."""
    try:
        from Foundation import NSBundle  # type: ignore
        import objc  # type: ignore

        b = NSBundle.bundleWithPath_("/System/Library/Frameworks/UserNotifications.framework")
        if b is not None:
            b.load()
        UNUserNotificationCenter = objc.lookUpClass("UserNotifications.UNUserNotificationCenter")
        if UNUserNotificationCenter is None:
            UNUserNotificationCenter = objc.lookUpClass("UNUserNotificationCenter")
        if UNUserNotificationCenter is None:
            return None
        center = UNUserNotificationCenter.currentNotificationCenter()
        box: Dict[str, Any] = {"v": None}

        def _cb(settings) -> None:
            try:
                box["v"] = int(settings.authorizationStatus())
            except Exception:
                box["v"] = None

        center.getNotificationSettingsWithCompletionHandler_(_cb)
        from Foundation import NSDate, NSRunLoop  # type: ignore

        for _ in range(40):
            if box["v"] is not None:
                break
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
        st = box["v"]
        if st is None:
            return None
        if st in (2, 3, 4):  # authorized / provisional / ephemeral
            return True
        if st == 1:  # denied
            return False
        return False  # notDetermined
    except Exception:
        return None


def full_disk_granted() -> Optional[bool]:
    """Heuristic: Full Disk Access usually unlocks Mail / Safari / Messages Library trees."""
    probes = [
        HOME / "Library" / "Mail",
        HOME / "Library" / "Safari",
        HOME / "Library" / "Messages",
        HOME / "Library" / "Cookies" / "Cookies.binarycookies",
        HOME / "Library" / "Containers" / "com.apple.mail",
    ]
    saw_deny = False
    saw_ok = False
    saw_missing = 0
    for p in probes:
        if not p.exists():
            saw_missing += 1
            continue
        if p.is_file():
            try:
                with open(p, "rb") as fh:
                    fh.read(1)
                saw_ok = True
            except PermissionError:
                saw_deny = True
            except Exception:
                continue
            continue
        r = _can_list(p)
        if r is True:
            saw_ok = True
        elif r is False:
            saw_deny = True
    if saw_ok:
        return True
    if saw_deny:
        return False
    # Nothing to probe (folders absent) → unknown, don't claim「未开启」
    if saw_missing >= len(probes):
        return None
    return None


def files_folders_granted() -> Optional[bool]:
    """Heuristic: Desktop / Documents / Downloads listing."""
    results = []
    for name in ("Desktop", "Documents", "Downloads"):
        r = _can_list(HOME / name)
        if r is not None:
            results.append(r)
    if not results:
        return None
    if all(results):
        return True
    if any(results):
        # Partial — still usable; show as granted with note via status text
        return True
    return False


def automation_granted() -> Optional[bool]:
    """Can we talk to System Events? Needed for login items / clipboard helpers."""
    try:
        r = subprocess.run(
            [
                "/usr/bin/osascript",
                "-e",
                'tell application "System Events" to get name',
            ],
            capture_output=True,
            text=True,
            timeout=6,
        )
        out = (r.stdout or "").strip().lower()
        err = (r.stderr or "").lower()
        if r.returncode == 0 and "system events" in out:
            return True
        if "not allowed" in err or "not authorised" in err or "not authorized" in err:
            return False
        if "(-1743)" in err or "not authorized to send apple events" in err:
            return False
        if r.returncode != 0:
            return False
        return None
    except Exception:
        return None


def open_privacy_settings(kind: str = "screen") -> Dict[str, Any]:
    """Open System Settings at the matching Privacy pane."""
    key = _normalize_kind(kind)
    urls = list(_PRIVACY_URLS.get(key) or _PRIVACY_URLS["privacy"])
    urls.append("x-apple.systempreferences:com.apple.systempreferences")
    last_err = ""
    for url in urls:
        try:
            r = subprocess.run(
                ["open", url],
                capture_output=True,
                text=True,
                timeout=8,
            )
            if r.returncode == 0:
                return {"ok": True, "kind": key, "url": url}
            last_err = (r.stderr or "").strip()
        except Exception as exc:
            last_err = str(exc)
    try:
        subprocess.Popen(["open", "-b", "com.apple.systempreferences"])
        return {"ok": True, "kind": key, "url": "System Settings", "fallback": True}
    except Exception as exc:
        return {"ok": False, "kind": key, "error": last_err or str(exc)}


def permission_guide_payload(kind: str, *, app_name: str = "SupTools") -> Dict[str, Any]:
    """Structured copy for the in-app permission modal."""
    key = _normalize_kind(kind)
    identity = runtime_tcc_identity()
    look = identity.get("look_for") or app_name
    mismatch = bool(identity.get("mismatch"))
    identity_note = ""
    if mismatch:
        identity_note = (
            f"注意：请勾选「{look}」，不要只勾选「{app_name}」。"
            f"本应用通过 Python 运行，系统按「{look}」记录权限。"
        )
    guides = {
        "screen": {
            "kind": "screen",
            "title": "需要屏幕录制权限",
            "subtitle": (
                "截图与录屏都依赖系统「屏幕录制」权限。"
                + (identity_note or f"请允许 {app_name} 后重试。")
            ),
            "steps": [
                "打开「系统设置 → 隐私与安全性 → 屏幕录制」",
                f"在列表中勾选「{look}」" + ("（不是只勾 SupTools）" if mismatch else ""),
                "也可点本页「请求授权」，用系统弹窗把当前进程加入列表",
                "勾选后若仍显示未开启，请完全退出应用再打开，然后点「重新检测」",
            ],
            "button": "打开屏幕录制设置",
        },
        "accessibility": {
            "kind": "accessibility",
            "title": "需要辅助功能权限",
            "subtitle": (
                "全局快捷键需要「辅助功能」权限。"
                + (identity_note or f"请允许 {app_name}。")
            ),
            "steps": [
                "打开「系统设置 → 隐私与安全性 → 辅助功能」",
                f"在列表中勾选「{look}」" + ("（不是只勾 SupTools）" if mismatch else ""),
                "返回后点「重新检测」；快捷键即可在其他应用前台时使用",
            ],
            "button": "打开辅助功能设置",
        },
        "microphone": {
            "kind": "microphone",
            "title": "需要麦克风权限",
            "subtitle": (
                "录屏开启「麦克风」时需要麦克风权限。"
                + (identity_note or f"请允许 {app_name}。")
            ),
            "steps": [
                "打开「系统设置 → 隐私与安全性 → 麦克风」",
                f"在列表中勾选「{look}」" + ("（不是只勾 SupTools）" if mismatch else ""),
                "或点「请求授权」弹出系统对话框，返回后重新录屏",
            ],
            "button": "打开麦克风设置",
        },
        "full_disk": {
            "kind": "full_disk",
            "title": "建议开启完全磁盘访问",
            "subtitle": "清理与卸载扫描系统库时，完全磁盘访问可避免扫不全。"
            + (f" {identity_note}" if identity_note else ""),
            "steps": [
                "打开「系统设置 → 隐私与安全性 → 完全磁盘访问权限」",
                f"点击「+」添加并勾选「{look}」",
                "按提示重启应用后再扫描，并点「重新检测」",
            ],
            "button": "打开完全磁盘访问",
        },
        "automation": {
            "kind": "automation",
            "title": "需要自动化权限",
            "subtitle": "启动项、剪贴板与 Finder 服务需要控制「系统事件 / Finder」。"
            + (f" {identity_note}" if identity_note else ""),
            "steps": [
                "打开「系统设置 → 隐私与安全性 → 自动化」",
                f"找到「{look}」，勾选「系统事件」和「Finder」",
                "返回后重新扫描启动项或使用相关功能",
            ],
            "button": "打开自动化设置",
        },
        "files": {
            "kind": "files",
            "title": "需要文件与文件夹权限",
            "subtitle": "清理大文件 / 安装包时可能需要桌面、文稿、下载权限。",
            "steps": [
                "打开「系统设置 → 隐私与安全性 → 文件与文件夹」",
                f"找到「{look}」，按需勾选桌面 / 文稿 / 下载",
                "返回后点「重新检测」",
            ],
            "button": "打开文件与文件夹",
        },
        "notifications": {
            "kind": "notifications",
            "title": "通知权限",
            "subtitle": "阈值告警需要系统通知权限。",
            "steps": [
                "打开「系统设置 → 通知」",
                f"在应用列表中找到「{look}」或「{app_name}」并允许通知",
                "返回后点「重新检测」",
            ],
            "button": "打开通知设置",
        },
        "login_items": {
            "kind": "login_items",
            "title": "登录项与后台项目",
            "subtitle": "这是系统设置入口，用于查看登录项；不是隐私开关状态。",
            "steps": [
                "打开「系统设置 → 通用 → 登录项与扩展」",
                "按需关闭不需要的登录项或后台项目",
                "也可在本应用「启动项」页管理 LaunchAgent",
            ],
            "button": "打开登录项设置",
        },
    }
    return dict(guides.get(key) or guides["screen"])



def request_permission(kind: str) -> Dict[str, Any]:
    """Best-effort system prompt for permissions that support it."""
    key = _normalize_kind(kind)
    granted: Optional[bool] = None
    if key == "screen":
        granted = request_screen_capture()
        if granted is None:
            granted = screen_capture_granted()
    elif key == "accessibility":
        granted = request_accessibility(prompt=True)
    elif key == "microphone":
        granted = request_microphone()
    else:
        # No direct prompt — open settings
        open_privacy_settings(key)
        granted = None
    status = permissions_status()
    item = next((x for x in status["items"] if x["id"] == key), None)
    return {
        "ok": True,
        "kind": key,
        "granted": granted if granted is not None else (item or {}).get("granted"),
        "item": item,
        "status": status,
    }


def _item(
    *,
    pid: str,
    title: str,
    used_by: str,
    desc: str,
    granted: Optional[bool],
    required: bool = True,
    can_request: bool = False,
    open_kind: Optional[str] = None,
) -> Dict[str, Any]:
    if granted is True:
        status = "granted"
        status_text = "已开启"
    elif granted is False:
        status = "denied"
        status_text = "未开启"
    else:
        status = "unknown"
        status_text = "需确认"
    return {
        "id": pid,
        "title": title,
        "used_by": used_by,
        "desc": desc,
        "granted": granted,
        "status": status,
        "status_text": status_text,
        "required": bool(required),
        "can_request": bool(can_request),
        "open_kind": open_kind or pid,
        "success": granted is True,
    }


def permissions_status(*, app_name: str = "SupTools") -> Dict[str, Any]:
    """Full checklist for the in-app permission guide page."""
    identity = runtime_tcc_identity()
    look = identity.get("look_for") or "Python"
    mismatch = bool(identity.get("mismatch"))
    screen_desc = "捕获屏幕画面；未开启时截图/录屏会失败。"
    if mismatch:
        screen_desc += f" 请在系统设置中勾选「{look}」，不要只勾 SupTools。"

    items: List[Dict[str, Any]] = [
        _item(
            pid="screen",
            title="屏幕录制",
            used_by="截图 · 录屏",
            desc=screen_desc,
            granted=screen_capture_granted(),
            required=True,
            can_request=True,
        ),
        _item(
            pid="accessibility",
            title="辅助功能",
            used_by="截图/录屏全局快捷键",
            desc=(
                "后台监听全局快捷键；仅应用内触发可不依赖此项。"
                + (f" 请勾选「{look}」。" if mismatch else "")
            ),
            granted=accessibility_granted(),
            required=True,
            can_request=True,
        ),
        _item(
            pid="microphone",
            title="麦克风",
            used_by="录屏（开启麦克风时）",
            desc="录制旁白/环境音。不需要人声时可保持关闭。",
            granted=microphone_granted(),
            required=False,
            can_request=True,
        ),
        _item(
            pid="full_disk",
            title="完全磁盘访问",
            used_by="清理 · 卸载",
            desc=(
                "完整扫描邮件、浏览器与部分系统库路径，避免扫不全。"
                + (f" 请给「{look}」开启。" if mismatch else "")
            ),
            granted=full_disk_granted(),
            required=False,
            can_request=False,
        ),
        _item(
            pid="files",
            title="文件与文件夹",
            used_by="清理（大文件 / 安装包）",
            desc="访问桌面、文稿、下载文件夹中的大文件与安装包。",
            granted=files_folders_granted(),
            required=False,
            can_request=False,
        ),
        _item(
            pid="automation",
            title="自动化",
            used_by="启动项 · 剪贴板 · Finder",
            desc="控制「系统事件 / Finder」以管理登录项、复制截图、新建文本文档。",
            granted=automation_granted(),
            required=True,
            can_request=False,
        ),
        _item(
            pid="notifications",
            title="通知",
            used_by="总览告警",
            desc="CPU/内存等超过阈值时推送系统通知。可在系统设置中开启。",
            granted=notifications_granted(),
            required=False,
            can_request=False,
        ),
    ]
    login = _item(
        pid="login_items",
        title="登录项（系统）",
        used_by="启动项管理",
        desc="系统设置入口，用于查看登录项；不表示隐私权限开关状态。",
        granted=None,
        required=False,
        can_request=False,
    )
    login["status"] = "info"
    login["status_text"] = "设置入口"
    items.append(login)

    required = [i for i in items if i.get("required")]
    required_ok = sum(1 for i in required if i.get("granted") is True)
    granted_n = sum(1 for i in items if i.get("granted") is True)
    pending = [i for i in items if i.get("required") and i.get("granted") is not True]

    return {
        "app_name": app_name,
        "identity": identity,
        "identity_hint": identity.get("hint") or "",
        "items": items,
        "item_count": len(items),
        "granted_count": granted_n,
        "required_count": len(required),
        "required_granted": required_ok,
        "all_required_ok": required_ok >= len(required) and len(required) > 0,
        "pending_required": [i["id"] for i in pending],
        "checked_at": time.time(),
        "summary": (
            f"推荐权限已开启 {required_ok}/{len(required)}"
            if required
            else f"已开启 {granted_n}/{len(items)}"
        ),
    }


def screen_permission_message(*, app_name: str = "SupTools") -> str:
    """User-facing screen-recording deny text that matches the real TCC identity."""
    look = runtime_tcc_identity().get("look_for") or app_name
    if look != app_name:
        return f"需要「屏幕录制」权限：请在系统设置中允许「{look}」（不要只勾 {app_name}）后重试"
    return f"需要「屏幕录制」权限：请允许 {app_name} 后重试"


def looks_like_screen_permission_error(message: str, *, code: Any = None) -> bool:
    text = str(message or "").lower()
    if "not authorized" in text or "notauthorized" in text:
        return True
    if "屏幕录制" in str(message or "") and ("权限" in str(message or "") or "允许" in str(message or "")):
        return True
    if "screen recording" in text or ("screencapture" in text and "author" in text):
        return True
    if "screencapture" in text and ("denied" in text or "permission" in text or "not permitted" in text):
        return True
    try:
        code_i = int(code)
    except Exception:
        code_i = None
    # screencapture often exits 1 with empty stderr when Screen Recording is denied
    if code_i == 1 and (not text or "author" in text or "permission" in text or "denied" in text):
        if not text:
            return True
        return "author" in text or "permission" in text or "denied" in text
    return False
