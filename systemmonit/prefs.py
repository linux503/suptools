"""Persistent user preferences for SupTools."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .brand import (
    BUNDLE_ENV,
    BUNDLE_ID,
    DEFAULT_APP_PATH,
    LEGACY_BUNDLE_ENV,
    migrate_support_dir,
)

CONFIG_DIR = migrate_support_dir()
CONFIG_PATH = CONFIG_DIR / "config.json"
LAUNCH_AGENT = Path.home() / "Library" / "LaunchAgents" / f"{BUNDLE_ID}.plist"

DEFAULTS: Dict[str, Any] = {
    "theme": "light",  # dark | light | system
    "glass": "medium",  # opaque | medium | clear
    "menubar_mode": "net",  # net | net_m | cpu_net | cpu | memory | compact | disk | battery | spark
    "refresh_ms": 1000,
    "clean_move_to_trash": True,
    "clean_confirm": True,
    "clean_history": [],
    "start_hidden": False,
    "launch_at_login": False,
    "show_alerts": True,
    "notify_alerts": True,
    "alert_cpu": 85,
    "alert_mem": 85,
    "alert_disk": 90,
    "alert_battery": 15,
    "confirm_proc_kill": True,
    "allow_force_kill": True,
    "menubar_show_icon": True,
    "screenshot_hide_self": True,
    "screenshot_clipboard": False,
    "screenshot_cursor": False,
    "screenshot_delay": 0.5,
    "hotkey_shot_selection": "ctrl+cmd+4",
    "hotkey_shot_window": "ctrl+cmd+5",
    "hotkey_shot_full": "ctrl+cmd+3",
    "recording_hide_self": True,
    "recording_mic": False,
    "recording_system_audio": False,
    "recording_clicks": True,
    "recording_countdown": 3,
    "recording_max_seconds": 0,
    "recording_open_after": False,
    "hotkey_rec_selection": "ctrl+cmd+6",
    "hotkey_rec_full": "ctrl+cmd+7",
    "hotkey_rec_stop": "ctrl+cmd+8",
    "finder_new_txt": False,
    "finder_new_txt_open": True,
}

_MENUBAR_MODES = (
    "net", "net_m", "cpu_net", "cpu", "memory", "compact", "disk", "battery", "spark",
)

_cache: Optional[Dict[str, Any]] = None


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(DEFAULTS)
    out.update({k: data[k] for k in DEFAULTS if k in data})
    if out.get("theme") not in ("dark", "light", "system"):
        out["theme"] = "light"
    if out.get("glass") not in ("opaque", "medium", "clear"):
        out["glass"] = "medium"
    if out.get("menubar_mode") not in _MENUBAR_MODES:
        out["menubar_mode"] = "net"
    try:
        out["refresh_ms"] = max(500, min(5000, int(out.get("refresh_ms", 1000))))
    except Exception:
        out["refresh_ms"] = 1000
    for thresh, lo, hi, default in (
        ("alert_cpu", 50, 100, 85),
        ("alert_mem", 50, 100, 85),
        ("alert_disk", 50, 100, 90),
        ("alert_battery", 5, 50, 15),
    ):
        try:
            out[thresh] = max(lo, min(hi, int(out.get(thresh, default))))
        except Exception:
            out[thresh] = default
    if not isinstance(out.get("clean_history"), list):
        out["clean_history"] = []
    for key in (
        "clean_move_to_trash",
        "clean_confirm",
        "start_hidden",
        "launch_at_login",
        "show_alerts",
        "notify_alerts",
        "confirm_proc_kill",
        "allow_force_kill",
        "menubar_show_icon",
        "screenshot_hide_self",
        "screenshot_clipboard",
        "screenshot_cursor",
        "recording_hide_self",
        "recording_mic",
        "recording_system_audio",
        "recording_clicks",
        "recording_open_after",
    ):
        out[key] = bool(out.get(key, DEFAULTS[key]))
    for key in ("finder_new_txt", "finder_new_txt_open"):
        out[key] = bool(out.get(key, DEFAULTS[key]))
    try:
        out["screenshot_delay"] = max(0.0, min(5.0, float(out.get("screenshot_delay", 0.5))))
    except Exception:
        out["screenshot_delay"] = 0.5
    try:
        out["recording_countdown"] = max(0, min(10, int(out.get("recording_countdown", 3))))
    except Exception:
        out["recording_countdown"] = 3
    try:
        out["recording_max_seconds"] = max(0, min(3600, int(out.get("recording_max_seconds", 0))))
    except Exception:
        out["recording_max_seconds"] = 0
    from .hotkeys import DEFAULT_HOTKEYS, normalize_hotkey

    for hk in DEFAULT_HOTKEYS:
        out[hk] = normalize_hotkey(out.get(hk, DEFAULT_HOTKEYS[hk]))
    out["launch_at_login"] = LAUNCH_AGENT.exists()
    return out


def load(*, force: bool = False) -> Dict[str, Any]:
    global _cache
    if _cache is not None and not force:
        # Keep login flag in sync cheaply
        _cache["launch_at_login"] = LAUNCH_AGENT.exists()
        return dict(_cache)
    data = dict(DEFAULTS)
    try:
        if CONFIG_PATH.exists():
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update(raw)
    except Exception:
        pass
    _cache = _normalize(data)
    return dict(_cache)


def save(cfg: Dict[str, Any]) -> None:
    global _cache
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        current = _normalize({**(_cache or DEFAULTS), **cfg})
        _cache = current
        out = {k: current.get(k, DEFAULTS[k]) for k in DEFAULTS}
        CONFIG_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def get(key: str, default=None):
    cfg = load()
    return cfg.get(key, default if default is not None else DEFAULTS.get(key))


def set_pref(key: str, value: Any) -> Dict[str, Any]:
    cfg = load()
    if key == "launch_at_login":
        ok = set_launch_at_login(bool(value))
        cfg["launch_at_login"] = ok and bool(value)
    else:
        cfg[key] = value
    save(cfg)
    return load()


def update_prefs(values: Dict[str, Any]) -> Dict[str, Any]:
    cfg = load()
    for key, value in values.items():
        if key not in DEFAULTS:
            continue
        if key == "launch_at_login":
            ok = set_launch_at_login(bool(value))
            cfg[key] = ok and bool(value)
        elif key == "finder_new_txt":
            from . import finder_newtxt as fnt

            ok = fnt.set_service_enabled(bool(value))
            cfg[key] = bool(ok and value)
        elif key == "refresh_ms":
            try:
                cfg[key] = max(500, min(5000, int(value)))
            except Exception:
                pass
        elif key == "theme":
            cfg[key] = value if value in ("dark", "light", "system") else "light"
        elif key == "glass":
            cfg[key] = value if value in ("opaque", "medium", "clear") else "medium"
        elif key == "menubar_mode":
            if value in _MENUBAR_MODES:
                cfg[key] = value
        elif key in ("alert_cpu", "alert_mem", "alert_disk", "alert_battery"):
            try:
                lo, hi = (5, 50) if key == "alert_battery" else (50, 100)
                cfg[key] = max(lo, min(hi, int(value)))
            except Exception:
                pass
        elif key == "screenshot_delay":
            try:
                cfg[key] = max(0.0, min(5.0, float(value)))
            except Exception:
                pass
        elif key == "recording_countdown":
            try:
                cfg[key] = max(0, min(10, int(value)))
            except Exception:
                pass
        elif key == "recording_max_seconds":
            try:
                cfg[key] = max(0, min(3600, int(value)))
            except Exception:
                pass
        elif key.startswith("hotkey_"):
            from .hotkeys import normalize_hotkey

            cfg[key] = normalize_hotkey(value)
        elif key == "clean_history":
            continue
        elif isinstance(DEFAULTS[key], bool):
            cfg[key] = bool(value)
        else:
            cfg[key] = value
    save(cfg)
    return load()


def push_clean_history(entry: Dict[str, Any], limit: int = 12) -> List[Dict[str, Any]]:
    cfg = load()
    hist = list(cfg.get("clean_history") or [])
    hist.insert(0, entry)
    hist = hist[:limit]
    cfg["clean_history"] = hist
    save(cfg)
    return hist


def reset_prefs() -> Dict[str, Any]:
    global _cache
    set_launch_at_login(False)
    try:
        from . import finder_newtxt as fnt

        fnt.uninstall_service()
    except Exception:
        pass
    try:
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
    except Exception:
        pass
    _cache = None
    return load(force=True)


def _app_path() -> str:
    for key in (BUNDLE_ENV, LEGACY_BUNDLE_ENV, "SYSTEMMONIT_APP_BUNDLE"):
        env = os.environ.get(key)
        if env and Path(env).exists():
            return env
    candidate = DEFAULT_APP_PATH
    if Path(candidate).exists():
        return candidate
    for legacy in ("/Applications/SysPulse.app", "/Applications/SystemMonit.app"):
        if Path(legacy).exists():
            return legacy
    return candidate


def set_launch_at_login(enabled: bool) -> bool:
    """Install/remove a per-user LaunchAgent that opens SupTools at login."""
    try:
        LAUNCH_AGENT.parent.mkdir(parents=True, exist_ok=True)
        label = BUNDLE_ID
        if not enabled:
            if LAUNCH_AGENT.exists():
                subprocess.run(
                    ["launchctl", "unload", str(LAUNCH_AGENT)],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                LAUNCH_AGENT.unlink(missing_ok=True)
            return True

        app = _app_path()
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/open</string>
    <string>-a</string>
    <string>{app}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>LimitLoadToSessionType</key>
  <string>Aqua</string>
</dict>
</plist>
"""
        LAUNCH_AGENT.write_text(plist, encoding="utf-8")
        subprocess.run(
            ["launchctl", "unload", str(LAUNCH_AGENT)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["launchctl", "load", str(LAUNCH_AGENT)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return LAUNCH_AGENT.exists()
    except Exception:
        return False


def settings_payload() -> Dict[str, Any]:
    cfg = load()
    payload = {
        "theme": cfg["theme"],
        "glass": cfg["glass"],
        "menubar_mode": cfg["menubar_mode"],
        "refresh_ms": cfg["refresh_ms"],
        "clean_move_to_trash": cfg["clean_move_to_trash"],
        "clean_confirm": cfg["clean_confirm"],
        "start_hidden": cfg["start_hidden"],
        "launch_at_login": cfg["launch_at_login"],
        "show_alerts": cfg["show_alerts"],
        "notify_alerts": cfg["notify_alerts"],
        "alert_cpu": cfg["alert_cpu"],
        "alert_mem": cfg["alert_mem"],
        "alert_disk": cfg["alert_disk"],
        "alert_battery": cfg["alert_battery"],
        "confirm_proc_kill": cfg["confirm_proc_kill"],
        "allow_force_kill": cfg["allow_force_kill"],
        "menubar_show_icon": cfg["menubar_show_icon"],
        "screenshot_hide_self": cfg["screenshot_hide_self"],
        "screenshot_clipboard": cfg["screenshot_clipboard"],
        "screenshot_cursor": cfg["screenshot_cursor"],
        "screenshot_delay": cfg["screenshot_delay"],
        "hotkey_shot_selection": cfg["hotkey_shot_selection"],
        "hotkey_shot_window": cfg["hotkey_shot_window"],
        "hotkey_shot_full": cfg["hotkey_shot_full"],
        "recording_hide_self": cfg["recording_hide_self"],
        "recording_mic": cfg["recording_mic"],
        "recording_system_audio": cfg["recording_system_audio"],
        "recording_clicks": cfg["recording_clicks"],
        "recording_countdown": cfg["recording_countdown"],
        "recording_max_seconds": cfg["recording_max_seconds"],
        "recording_open_after": cfg["recording_open_after"],
        "hotkey_rec_selection": cfg["hotkey_rec_selection"],
        "hotkey_rec_full": cfg["hotkey_rec_full"],
        "hotkey_rec_stop": cfg["hotkey_rec_stop"],
        "finder_new_txt": cfg["finder_new_txt"],
        "finder_new_txt_open": cfg["finder_new_txt_open"],
        "app_path": _app_path(),
        "config_path": str(CONFIG_PATH),
        "version": "1.27.1",
    }
    try:
        from . import finder_newtxt as fnt

        st = fnt.service_status()
        payload["finder_new_txt_installed"] = bool(st.get("installed"))
        payload["finder_new_txt"] = bool(cfg["finder_new_txt"] and st.get("installed"))
        payload["finder_new_txt_hint"] = st.get("menu_hint") or ""
    except Exception:
        payload["finder_new_txt_installed"] = False
        payload["finder_new_txt_hint"] = ""
    return payload
