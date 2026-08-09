"""Native macOS dashboard using AppKit + WKWebView (reliable painting)."""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .collector import (
    MetricsCollector,
    Snapshot,
    format_bps,
    format_bytes,
    format_runtime,
    format_uptime,
)
from .dashboard_html import DASHBOARD_HTML
from .icons import format_net_m
from .menubar import MenuBarController
from . import prefs
from .notify import build_threshold_alerts, maybe_notify_alerts
from . import screenshot as shot_mod
from . import hotkeys as hotkey_mod
from . import finder_newtxt as finder_txt
from . import connectivity as conn_mod
from . import recording as rec_mod
from . import permissions as perm_mod
from .brand import APP_NAME

LOG = Path.home() / "Library" / "Logs" / "SupTools-dashboard.log"

_STATUS_CN = {
    "running": "运行中",
    "sleeping": "睡眠",
    "disk-sleep": "磁盘等待",
    "stopped": "停止",
    "zombie": "僵尸",
    "dead": "结束",
    "idle": "空闲",
}


def _log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(msg.rstrip() + "\n")
    except Exception:
        pass


def _pct(v: float, digits: int = 1) -> str:
    return f"{v:.{digits}f}%"


def _status_cn(s: str) -> str:
    return _STATUS_CN.get(s, s or "—")


def _active_ifaces(ifaces: list) -> list:
    out = []
    for i in ifaces:
        if not i.get("isup"):
            continue
        has_ip = bool(i.get("ip"))
        busy = (i.get("down_bps", 0) + i.get("up_bps", 0)) > 256
        heavy = (i.get("bytes_recv", 0) + i.get("bytes_sent", 0)) > 10_000_000
        if has_ip or busy or heavy:
            out.append(i)
    return out or [i for i in ifaces if i.get("isup")][:3]


def snapshot_to_payload(
    collector: MetricsCollector,
    s: Snapshot,
    *,
    page: str = "overview",
    panel_visible: bool = True,
) -> Dict[str, Any]:
    user, system, idle = s.cpu_times
    total = max(s.mem_total, 1)
    active = _active_ifaces(s.net_interfaces)
    top = active[0] if active else None
    free = max(0, s.primary_disk_total - s.primary_disk_used) if s.primary_disk_total else 0
    want_procs = panel_visible and page in ("overview", "processes", "cpu", "memory")
    want_disk_detail = panel_visible and page in ("overview", "disk")
    want_net_detail = panel_visible and page in ("overview", "network")
    hist_n = 40 if panel_visible else 16

    def _hist(dq):
        vals = list(dq)
        return [float(x) for x in vals[-hist_n:]]

    has_container = any(p.get("is_container") for p in s.disk_partitions)
    volumes = []
    if want_disk_detail:
        for p in s.disk_partitions:
            if has_container and (p.get("is_root") or p.get("is_data")):
                continue
            label = p.get("label") or p["mount"]
            tag = "整盘" if p.get("is_container") else p["mount"]
            volumes.append({
                "title": f"{label}    {tag}",
                "percent": round(float(p["percent"]), 1),
                "fstype": p.get("fstype") or "?",
                "device": p.get("device") or "—",
                "used": format_bytes(p["used"]),
                "total": format_bytes(p["total"]),
                "free": format_bytes(p["free"]),
                "detail": (
                    f"{format_bytes(p['used'])} / {format_bytes(p['total'])}"
                    f"    可用 {format_bytes(p['free'])}"
                    f"    {_pct(p['percent'])}"
                    f"    ·  {p.get('fstype') or '?'}"
                ),
                "color": "#ef6b6b" if p["percent"] > 90 else "#5ecfc0",
                "warn": float(p["percent"]) >= 85,
            })

    processes = []
    top_mem = []
    if want_procs and s.processes:
        processes = [
            {
                "pid": p["pid"],
                "name": p["name"],
                "cpu": float(p["cpu"]),
                "memory": format_bytes(p["memory"]),
                "memory_bytes": int(p["memory"]),
                "threads": p["threads"],
                "status": _status_cn(p["status"]),
                "user": p.get("user") or "—",
                "runtime": format_runtime(float(p.get("runtime") or 0)),
                "cmd": p.get("cmd") or "",
            }
            for p in s.processes
        ]
        top_mem = sorted(processes, key=lambda x: -x["memory_bytes"])[:6]

    alerts = []
    if prefs.get("show_alerts", True):
        alerts = build_threshold_alerts(
            cpu=float(s.cpu_percent),
            mem=float(s.mem_percent),
            mem_pressure=str(getattr(s, "mem_pressure", "normal") or "normal"),
            disk=float(s.primary_disk_percent),
            load0=float(s.load_avg[0]),
            cores=int(s.logical_cores or 1),
            battery_percent=float(getattr(s, "battery_percent", 0) or 0),
            has_battery=bool(getattr(s, "has_battery", False)),
            battery_plugged=bool(getattr(s, "battery_plugged", False)),
            alert_cpu=float(prefs.get("alert_cpu", 85)),
            alert_mem=float(prefs.get("alert_mem", 85)),
            alert_disk=float(prefs.get("alert_disk", 90)),
            alert_battery=float(prefs.get("alert_battery", 15)),
        )

    pressure_cn = {"normal": "正常", "warn": "警告", "critical": "严重"}.get(
        getattr(s, "mem_pressure", "normal"), "正常"
    )
    batt_text = "—"
    if getattr(s, "has_battery", False):
        plug = "充电中" if s.battery_plugged else "使用电池"
        batt_text = f"{s.battery_percent:.0f}% · {plug}"
        secs = int(getattr(s, "battery_secs_left", -1) or -1)
        if secs > 0 and not s.battery_plugged:
            hrs, rem = divmod(secs, 3600)
            mins = rem // 60
            batt_text += f" · 约 {hrs}小时{mins}分" if hrs else f" · 约 {mins} 分钟"
    else:
        batt_text = "外接供电"

    boot_str = "—"
    try:
        boot_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(s.boot_time))
    except Exception:
        pass

    cores_label = f"{s.physical_cores} 物理 / {s.logical_cores} 逻辑"
    if s.physical_cores == s.logical_cores:
        cores_label = f"{s.logical_cores} 核"

    ifaces = []
    if want_net_detail:
        ifaces = [
            {
                "name": i.get("display") or i["name"],
                "ip": i.get("ip") or "—",
                "down": format_bps(i.get("down_bps", 0)),
                "up": format_bps(i.get("up_bps", 0)),
                "recv": format_bytes(i["bytes_recv"]),
                "sent": format_bytes(i["bytes_sent"]),
                "speed": int(i.get("speed") or 0),
                "speed_text": f"{int(i.get('speed') or 0)} Mbps" if i.get("speed") else "—",
                "packets_recv": int(i.get("packets_recv") or 0),
                "packets_sent": int(i.get("packets_sent") or 0),
                "isup": bool(i.get("isup")),
            }
            for i in active
        ]

    return {
        "hostname": s.hostname or "本机",
        "chip": s.chip,
        "platform": s.platform,
        "cores_label": cores_label,
        "logical_cores": s.logical_cores,
        "physical_cores": s.physical_cores,
        "uptime": format_uptime(s.uptime),
        "boot_time": boot_str,
        "load": [round(float(x), 2) for x in s.load_avg],
        "subtitle": (
            f"{s.platform}  ·  {cores_label}  ·  "
            f"负载 {s.load_avg[0]:.2f}  ·  已运行 {format_uptime(s.uptime)}"
        ),
        "alerts": alerts,
        "page": page,
        "cpu_percent": float(s.cpu_percent),
        "cpu_user": float(user),
        "cpu_system": float(system),
        "cpu_idle": float(idle),
        "cpu_detail": (
            f"用户   {_pct(user)}\n系统   {_pct(system)}\n"
            f"空闲   {_pct(idle)}\n负载   {s.load_avg[0]:.2f} / {s.load_avg[1]:.2f} / {s.load_avg[2]:.2f}"
        ),
        "cpu_compose": (
            f"用户态    {_pct(user)}\n系统态    {_pct(system)}\n"
            f"空闲      {_pct(idle)}\n"
            f"核心      {cores_label}\n"
            f"负载      {s.load_avg[0]:.2f}  {s.load_avg[1]:.2f}  {s.load_avg[2]:.2f}\n"
            f"启动于    {boot_str}"
        ),
        "cpu_per_core": [float(x) for x in s.cpu_per_core] if page in ("overview", "cpu") else [],
        "cpu_history": _hist(collector.cpu_history),
        "mem_percent": float(s.mem_percent),
        "mem_used": format_bytes(s.mem_used),
        "mem_total": format_bytes(s.mem_total),
        "mem_available": format_bytes(s.mem_available),
        "mem_pressure": getattr(s, "mem_pressure", "normal"),
        "mem_pressure_cn": pressure_cn,
        "mem_pressure_score": float(getattr(s, "mem_pressure_score", 0) or 0),
        "swap_percent": float(getattr(s, "swap_percent", 0) or 0),
        "swap_used": format_bytes(s.swap_used),
        "swap_total": format_bytes(s.swap_total),
        "has_battery": bool(getattr(s, "has_battery", False)),
        "battery_percent": float(getattr(s, "battery_percent", 0) or 0),
        "battery_plugged": bool(getattr(s, "battery_plugged", False)),
        "battery_text": batt_text,
        "top_process_name": getattr(s, "top_process_name", "") or "",
        "top_process_cpu": float(getattr(s, "top_process_cpu", 0) or 0),
        "mem_detail": (
            f"已用   {format_bytes(s.mem_used)}\n"
            f"可用   {format_bytes(s.mem_available)}\n"
            f"压力   {pressure_cn}\n"
            f"总计   {format_bytes(s.mem_total)}"
        ),
        "mem_lines": (
            f"物理内存    {format_bytes(s.mem_total)}\n"
            f"已用        {format_bytes(s.mem_used)}   ({_pct(s.mem_percent)})\n"
            f"可用        {format_bytes(s.mem_available)}\n"
            f"压力        {pressure_cn}   ({getattr(s, 'mem_pressure_score', 0):.0f})\n"
            f"交换        {format_bytes(s.swap_used)} / {format_bytes(s.swap_total)}"
        ),
        "mem_legend": (
            f"压力 {pressure_cn}   "
            f"Wired {format_bytes(s.mem_wired)}   "
            f"Active {format_bytes(s.mem_active)}   "
            f"压缩 {format_bytes(s.mem_compressed)}"
        ),
        "mem_breakdown": (
            f"压力 {pressure_cn}   "
            f"Wired {format_bytes(s.mem_wired)}   "
            f"Active {format_bytes(s.mem_active)}   "
            f"压缩 {format_bytes(s.mem_compressed)}   "
            f"缓存约 {format_bytes(s.mem_cached)}"
        ),
        "mem_segments": [
            [min(1.0, s.mem_wired / total), "#fbbf24"],
            [min(1.0, s.mem_active / total), "#38bdf8"],
            [min(1.0, s.mem_compressed / total), "#5ecfc0"],
            [min(1.0, max(0, total - s.mem_wired - s.mem_active - s.mem_compressed) / total), "#2a3545"],
        ],
        "mem_history": _hist(collector.mem_history),
        "top_mem": top_mem,
        "net_down": format_bps(s.net_down_bps),
        "net_up": format_bps(s.net_up_bps),
        "net_down_m": format_net_m(s.net_down_bps),
        "net_up_m": format_net_m(s.net_up_bps),
        "net_iface": (
            f"主接口 {top.get('display') or top['name']}  ·  {top.get('ip') or '无 IP'}"
            + (f"  ·  {int(top.get('speed') or 0)} Mbps" if top and top.get("speed") else "")
            if top else "暂无活跃网卡"
        ),
        "net_down_history": _hist(collector.net_down_history),
        "net_up_history": _hist(collector.net_up_history),
        "ifaces": ifaces,
        "disk_percent": float(s.primary_disk_percent),
        "disk_used": format_bytes(s.primary_disk_used) if s.primary_disk_total else "—",
        "disk_total": format_bytes(s.primary_disk_total) if s.primary_disk_total else "—",
        "disk_free": format_bytes(free) if s.primary_disk_total else "—",
        "disk_label": s.primary_disk_label or "主磁盘",
        "disk_text": (
            f"{format_bytes(s.primary_disk_used)} / {format_bytes(s.primary_disk_total)}"
            f"   ·   可用 {format_bytes(free)}   ·   {_pct(s.primary_disk_percent)}"
            if s.primary_disk_total else "—"
        ),
        "disk_read": format_bps(s.disk_read_bps),
        "disk_write": format_bps(s.disk_write_bps),
        "disk_read_history": _hist(collector.disk_read_history),
        "disk_write_history": _hist(collector.disk_write_history),
        "volumes": volumes,
        "processes": processes,
        "status_line": (
            f"CPU {_pct(s.cpu_percent)}   "
            f"内存 {_pct(s.mem_percent)}/{pressure_cn}   "
            f"↓{format_bps(s.net_down_bps)} ↑{format_bps(s.net_up_bps)}   "
            f"磁盘 {_pct(s.primary_disk_percent)}"
            + (f"   电池 {batt_text}" if getattr(s, "has_battery", False) else "")
        ),
    }


def _notify_from_snap(s: Snapshot) -> None:
    if not prefs.get("show_alerts", True):
        return
    alerts = build_threshold_alerts(
        cpu=float(s.cpu_percent),
        mem=float(s.mem_percent),
        mem_pressure=str(getattr(s, "mem_pressure", "normal") or "normal"),
        disk=float(s.primary_disk_percent),
        load0=float(s.load_avg[0]),
        cores=int(s.logical_cores or 1),
        battery_percent=float(getattr(s, "battery_percent", 0) or 0),
        has_battery=bool(getattr(s, "has_battery", False)),
        battery_plugged=bool(getattr(s, "battery_plugged", False)),
        alert_cpu=float(prefs.get("alert_cpu", 85)),
        alert_mem=float(prefs.get("alert_mem", 85)),
        alert_disk=float(prefs.get("alert_disk", 90)),
        alert_battery=float(prefs.get("alert_battery", 15)),
    )
    maybe_notify_alerts(alerts, enabled=bool(prefs.get("notify_alerts", True)))


def _js_body_to_dict(body) -> Dict[str, Any]:
    """Convert WKScriptMessage body (NSDictionary / dict / JSON str) to a plain dict."""
    coerced = _js_coerce(body)
    return coerced if isinstance(coerced, dict) else {}


def _js_coerce(value: Any) -> Any:
    """Deep-convert PyObjC / JS bridge values into plain Python types."""
    if value is None or isinstance(value, (str, bytes, int, float, bool)):
        return value
    # Already-plain containers
    if isinstance(value, dict):
        return {str(k): _js_coerce(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_js_coerce(v) for v in value]
    # NSDictionary
    try:
        if hasattr(value, "allKeys"):
            out: Dict[str, Any] = {}
            for key in value.allKeys():
                out[str(key)] = _js_coerce(value.objectForKey_(key))
            return out
    except Exception:
        pass
    # NSArray / other iterables (but not string-like)
    try:
        if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, dict)):
            return [_js_coerce(v) for v in list(value)]
    except Exception:
        pass
    # NSNumber
    try:
        if hasattr(value, "doubleValue") and hasattr(value, "boolValue"):
            # Distinguish booleans from numbers when possible
            try:
                cls_name = type(value).__name__
                if "Boolean" in cls_name or cls_name in ("__NSCFBoolean",):
                    return bool(value.boolValue())
            except Exception:
                pass
            try:
                as_int = int(value)
                as_float = float(value.doubleValue())
                if as_float == as_int:
                    return as_int
                return as_float
            except Exception:
                return bool(value.boolValue())
    except Exception:
        pass
    try:
        return dict(value)  # type: ignore[arg-type]
    except Exception:
        pass
    try:
        parsed = json.loads(str(value))
        return _js_coerce(parsed)
    except Exception:
        return value


def _coerce_clean_items(raw: Any) -> List[Dict[str, Any]]:
    """Normalize selected clean items from UI / cache into plain dicts with paths."""
    if not raw:
        return []
    values = _js_coerce(raw)
    if not isinstance(values, list):
        return []
    out: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for it in values:
        if not isinstance(it, dict):
            continue
        path = str(it.get("path") or "").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        try:
            cutoff = int(it.get("cutoff_days") or 7)
        except Exception:
            cutoff = 7
        try:
            nbytes = int(it.get("bytes") or 0)
        except Exception:
            nbytes = 0
        out.append({
            "id": str(it.get("id") or path),
            "path": path,
            "name": str(it.get("name") or Path(path).name),
            "category": str(it.get("category") or ""),
            "category_title": str(it.get("category_title") or ""),
            "mode": str(it.get("mode") or "all"),
            "cutoff_days": cutoff,
            "risk": str(it.get("risk") or "safe"),
            "bytes": nbytes,
            "selected": True,
        })
    return out


def run_native() -> None:
    import base64
    import os
    import queue
    import threading

    from AppKit import (  # type: ignore
        NSAlert,
        NSAlertFirstButtonReturn,
        NSApp,
        NSAppearance,
        NSApplication,
        NSApplicationActivationPolicyRegular,
        NSBackingStoreBuffered,
        NSColor,
        NSMakeRect,
        NSObject,
        NSScreen,
        NSView,
        NSViewHeightSizable,
        NSViewMaxXMargin,
        NSViewMaxYMargin,
        NSViewMinXMargin,
        NSViewMinYMargin,
        NSViewWidthSizable,
        NSVisualEffectBlendingModeBehindWindow,
        NSVisualEffectStateActive,
        NSVisualEffectView,
        NSWindow,
        NSWindowStyleMaskClosable,
        NSWindowStyleMaskFullSizeContentView,
        NSWindowStyleMaskMiniaturizable,
        NSWindowStyleMaskResizable,
        NSWindowStyleMaskTitled,
    )
    from Foundation import NSDistributedNotificationCenter, NSTimer, NSURL  # type: ignore
    from WebKit import WKWebView, WKWebViewConfiguration  # type: ignore

    from .singleton import SHOW_NOTIFICATION, release_singleton

    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text("", encoding="utf-8")
    except Exception:
        pass
    _log("starting native webkit dashboard")

    collector = MetricsCollector()
    collector.sample(include_processes=False, include_interfaces=False)
    snap: Optional[Snapshot] = collector.sample(include_processes=False, include_interfaces=True)

    state = {
        "paused": False,
        "interval": 1.0,
        "tick": 0,
        "page": "overview",
        "ready": False,
        "timer_started": False,
        "latest": snap,
        "clean_busy": False,
        "shot_busy": False,
        "shot_draft": "",
        "rec_busy": False,
        "rec_draft": "",
        "rec_proc": None,
        "rec_started_at": 0.0,
        "rec_mode": "",
        "conn_busy": False,
        "conn_cancel": False,
        "clean_events": queue.Queue(),
        "last_scan_items": [],
        "last_scan_result": None,
        "clean_cancel": None,
        "uninstall_busy": False,
        "uninstall_cancel": None,
        "last_uninstall_apps": None,
        "last_uninstall_detail": None,
        "startup_busy": False,
        "startup_cancel": None,
        "last_startup_result": None,
        "perms_busy": False,
        "perms_push_at": 0.0,
        "last_perms": None,
    }

    def apply_window_appearance(theme: Optional[str] = None, glass: Optional[str] = None) -> None:
        """Keep native vibrancy / chrome in sync with theme + glass level."""
        win = state.get("ns_window")
        vib = state.get("ns_vibrancy")
        if win is None:
            return
        t = theme if theme is not None else str(prefs.get("theme", "light") or "light")
        g = glass if glass is not None else str(prefs.get("glass", "medium") or "medium")
        if g not in ("opaque", "medium", "clear"):
            g = "medium"
        try:
            if t == "system":
                win.setAppearance_(None)
                if vib is not None:
                    vib.setAppearance_(None)
            else:
                name = "NSAppearanceNameDarkAqua" if t == "dark" else "NSAppearanceNameAqua"
                appearance = NSAppearance.appearanceNamed_(name)
                if appearance is not None:
                    win.setAppearance_(appearance)
                    if vib is not None:
                        vib.setAppearance_(appearance)
        except Exception:
            pass
        if vib is None:
            return
        try:
            from AppKit import (  # type: ignore
                NSVisualEffectMaterialContentBackground,
                NSVisualEffectMaterialHUDWindow,
                NSVisualEffectMaterialPopover,
                NSVisualEffectMaterialSidebar,
                NSVisualEffectMaterialUnderWindowBackground,
            )

            if g == "opaque":
                try:
                    vib.setMaterial_(NSVisualEffectMaterialContentBackground)
                except Exception:
                    vib.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
            elif g == "clear":
                try:
                    vib.setMaterial_(NSVisualEffectMaterialHUDWindow)
                except Exception:
                    try:
                        vib.setMaterial_(NSVisualEffectMaterialPopover)
                    except Exception:
                        vib.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
            else:
                try:
                    vib.setMaterial_(NSVisualEffectMaterialSidebar)
                except Exception:
                    try:
                        vib.setMaterial_(NSVisualEffectMaterialHUDWindow)
                    except Exception:
                        vib.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
        except Exception:
            pass

    def push_settings() -> None:
        payload = prefs.settings_payload()
        try:
            hk = hotkey_mod.hotkey_payload(
                payload,
                global_ok=bool(getattr(state.get("hotkeys"), "global_ok", True)),
            )
            payload.update(hk)
        except Exception:
            pass
        try:
            granted = perm_mod.screen_capture_granted()
            payload["screen_granted"] = granted
            payload["screen_ok"] = True if granted is None else bool(granted)
        except Exception:
            payload["screen_granted"] = None
            payload["screen_ok"] = True
        try:
            ax = perm_mod.accessibility_granted()
            payload["accessibility_granted"] = ax
            payload["accessibility_ok"] = True if ax is None else bool(ax)
        except Exception:
            payload["accessibility_granted"] = None
            payload["accessibility_ok"] = True
        call_js("__setSettings", payload)
        call_js("__setTheme", {
            "theme": payload.get("theme", "light"),
            "glass": payload.get("glass", "medium"),
        })
        apply_window_appearance(payload.get("theme", "light"), payload.get("glass", "medium"))
        call_js("__setCleanPrefs", {
            "move_to_trash": bool(payload.get("clean_move_to_trash", True)),
            "clean_confirm": bool(payload.get("clean_confirm", True)),
            "history": list(prefs.get("clean_history") or [])[:8],
        })
        try:
            ms = int(payload.get("refresh_ms", 1000))
            state["interval"] = max(0.4, min(5.0, ms / 1000.0))
            call_js("__setInterval", {
                "ms": int(round(float(state["interval"]) * 1000)),
                "paused": bool(state["paused"]),
            })
        except Exception:
            pass

    def apply_runtime_prefs(cfg: Dict[str, Any]) -> None:
        try:
            ms = int(cfg.get("refresh_ms", 1000))
            state["interval"] = max(0.4, min(5.0, ms / 1000.0))
        except Exception:
            pass
        try:
            apply_window_appearance(
                str(cfg.get("theme") or prefs.get("theme", "light")),
                str(cfg.get("glass") or prefs.get("glass", "medium")),
            )
        except Exception:
            pass
        try:
            mode = str(cfg.get("menubar_mode") or "net")
            if getattr(menubar, "mode", None) != mode:
                menubar.set_mode(mode, persist=False)
            menubar.apply_icon_pref()
        except Exception:
            pass
        try:
            reload_hotkeys()
        except Exception:
            pass
        if state["latest"] is not None:
            try:
                menubar.update(state["latest"])
            except Exception:
                pass

    def start_screenshot(data: Optional[Dict[str, Any]] = None) -> None:
        """Shared entry for UI + global hotkeys."""
        data = dict(data or {})
        mode = str(data.get("mode") or "selection")
        if mode not in ("selection", "window", "full"):
            mode = "selection"
        also_copy = bool(data.get("clipboard", prefs.get("screenshot_clipboard", False)))
        include_cursor = bool(data.get("cursor", prefs.get("screenshot_cursor", False)))
        hide_self = bool(data.get("hide_self", prefs.get("screenshot_hide_self", True)))
        try:
            delay = float(data.get("delay", prefs.get("screenshot_delay", 0.5)))
        except Exception:
            delay = 0.5
        delay = max(0.0, min(5.0, delay))
        try:
            prefs.update_prefs({
                "screenshot_clipboard": also_copy,
                "screenshot_cursor": include_cursor,
                "screenshot_hide_self": hide_self,
                "screenshot_delay": delay,
            })
        except Exception:
            pass

        if state.get("shot_busy"):
            call_js("__setScreenshotToast", {"ok": False, "message": "正在截图中…"})
            return

        # Proactively surface Screen Recording permission guide
        granted = perm_mod.screen_capture_granted()
        if granted is False:
            try:
                perm_mod.request_screen_capture()
            except Exception:
                pass
            call_js(
                "__showPermissionGuide",
                perm_mod.permission_guide_payload("screen", app_name=APP_NAME),
            )
            call_js("__setScreenshotToast", {
                "ok": False,
                "message": "请先在系统设置中允许屏幕录制权限",
            })
            return

        # Discard previous unfinished draft
        prev = str(state.get("shot_draft") or "")
        if prev:
            try:
                shot_mod.discard_draft(prev)
            except Exception:
                pass
            state["shot_draft"] = ""

        state["shot_busy"] = True
        call_js("__setScreenshotProgress", {"busy": True, "message": "准备截图…"})

        def run_capture():
            try:
                extra = 0.35 if hide_self else 0.0
                result = shot_mod.capture(
                    mode=mode,
                    to_clipboard=False,
                    include_cursor=include_cursor,
                    delay=delay + extra,
                    hide_shadow=True,
                    draft=True,
                )
            except Exception:
                _log("screenshot failed:\n" + traceback.format_exc())
                result = {"ok": False, "error": "截图失败", "path": "", "mode": mode}
            result = dict(result or {})
            result["_hidden"] = hide_self
            result["also_copy"] = also_copy
            if result.get("ok") and result.get("path"):
                preview = shot_mod.read_preview_base64(str(result["path"]))
                if preview:
                    result["preview"] = preview
                    result["annotate"] = True
                else:
                    # Too large for in-app editor — commit original directly
                    try:
                        from pathlib import Path as _Path

                        src = _Path(str(result["path"]))
                        dest = shot_mod.default_save_path()
                        src.replace(dest)
                        info = shot_mod.file_info(dest)
                        if also_copy:
                            shot_mod.copy_to_clipboard(str(dest))
                        result = {
                            "ok": True,
                            "path": str(dest),
                            "file": info,
                            "annotate": False,
                            "message": "图片较大，已直接保存" + ("并复制" if also_copy else ""),
                            "preview": shot_mod.read_preview_base64(str(dest)),
                            "_hidden": hide_self,
                            "also_copy": also_copy,
                        }
                    except Exception:
                        result["annotate"] = False
                        result["message"] = "截图已保存（无法打开标记）"
            try:
                state["clean_events"].put({"kind": "shot_done", "data": result})
            except Exception:
                _log("shot queue failed:\n" + traceback.format_exc())

        if hide_self:
            try:
                window.orderOut_(None)
            except Exception:
                pass

        threading.Thread(target=run_capture, daemon=True).start()

    def finish_annotate_save(data: Dict[str, Any]) -> None:
        data_url = str(data.get("data_url") or data.get("data") or "")
        draft = str(data.get("draft") or state.get("shot_draft") or "")
        copy = bool(data.get("copy", prefs.get("screenshot_clipboard", False)))
        result = shot_mod.save_annotated(data_url, draft_path_str=draft, copy=copy)
        if result.get("ok"):
            state["shot_draft"] = ""
            call_js("__closeScreenshotEditor", {})
            call_js("__setScreenshotResult", result)
            call_js("__setScreenshotList", shot_mod.folder_payload())
            call_js("__setScreenshotToast", {
                "ok": True,
                "message": result.get("message") or "截图已保存",
            })
        else:
            call_js("__setScreenshotToast", {
                "ok": False,
                "message": result.get("error") or "保存失败",
            })

    def finish_annotate_copy(data: Dict[str, Any]) -> None:
        data_url = str(data.get("data_url") or data.get("data") or "")
        raw = shot_mod._decode_data_url(data_url)
        ok = bool(raw) and shot_mod.copy_png_bytes(raw or b"")
        call_js("__setScreenshotToast", {
            "ok": ok,
            "message": "已复制到剪贴板" if ok else "复制失败",
        })

    def finish_annotate_cancel(data: Optional[Dict[str, Any]] = None) -> None:
        data = dict(data or {})
        draft = str(data.get("draft") or state.get("shot_draft") or "")
        if draft:
            shot_mod.discard_draft(draft)
        state["shot_draft"] = ""
        call_js("__closeScreenshotEditor", {})
        call_js("__setScreenshotToast", {"ok": True, "message": "已取消，未保存"})
        call_js("__setScreenshotList", shot_mod.folder_payload())

    def start_recording(data: Optional[Dict[str, Any]] = None) -> None:
        data = dict(data or {})
        mode = str(data.get("mode") or "selection")
        if mode not in ("selection", "full"):
            mode = "selection"
        mic = bool(data.get("mic", prefs.get("recording_mic", False)))
        system_audio = bool(data.get("system_audio", prefs.get("recording_system_audio", False)))
        clicks = bool(data.get("clicks", prefs.get("recording_clicks", True)))
        hide_self = bool(data.get("hide_self", prefs.get("recording_hide_self", True)))
        try:
            countdown = int(data.get("countdown", prefs.get("recording_countdown", 3)))
        except Exception:
            countdown = 3
        countdown = max(0, min(10, countdown))
        try:
            max_seconds = int(data.get("max_seconds", prefs.get("recording_max_seconds", 0)))
        except Exception:
            max_seconds = 0
        max_seconds = max(0, min(3600, max_seconds))
        try:
            prefs.update_prefs({
                "recording_mic": mic,
                "recording_system_audio": system_audio,
                "recording_clicks": clicks,
                "recording_hide_self": hide_self,
                "recording_countdown": countdown,
                "recording_max_seconds": max_seconds,
            })
        except Exception:
            pass

        if state.get("rec_busy") or state.get("shot_busy"):
            call_js("__setRecordingToast", {"ok": False, "message": "当前有任务进行中…"})
            return

        granted = perm_mod.screen_capture_granted()
        if granted is False:
            try:
                perm_mod.request_screen_capture()
            except Exception:
                pass
            call_js(
                "__showPermissionGuide",
                perm_mod.permission_guide_payload("screen", app_name=APP_NAME),
            )
            call_js("__setRecordingToast", {
                "ok": False,
                "message": "请先在系统设置中允许屏幕录制权限",
            })
            return

        prev = str(state.get("rec_draft") or "")
        if prev:
            try:
                rec_mod.discard_draft(prev)
            except Exception:
                pass
            state["rec_draft"] = ""

        state["rec_busy"] = True
        state["rec_mode"] = mode
        state["rec_proc"] = None
        state["rec_started_at"] = 0.0
        call_js("__setRecordingState", {
            "busy": True,
            "phase": "starting",
            "mode": mode,
            "message": "正在启动录制…",
            "elapsed": 0,
        })

        def run_rec() -> None:
            try:
                extra = 0.35 if hide_self else 0.0
                # Countdown is primarily UI-driven; keep a short settle delay here.
                result = rec_mod.start_process(
                    mode=mode,
                    mic=mic,
                    system_audio=system_audio,
                    show_clicks=clicks,
                    max_seconds=float(max_seconds),
                    delay=extra,
                )
            except Exception:
                _log("recording start failed:\n" + traceback.format_exc())
                result = {"ok": False, "error": "无法开始录制"}

            if not result.get("ok"):
                state["rec_busy"] = False
                err = result.get("error") or "无法开始录制"
                perm = str(result.get("permission") or "")
                if not perm and (
                    perm_mod.looks_like_screen_permission_error(err)
                    or perm_mod.screen_capture_granted() is False
                ):
                    perm = "screen"
                    err = perm_mod.screen_permission_message(app_name=APP_NAME)
                state["clean_events"].put({
                    "kind": "rec_done",
                    "data": {
                        "ok": False,
                        "error": err,
                        "permission": perm,
                        "_hidden": hide_self,
                    },
                })
                return

            proc = result.pop("_proc", None)
            state["rec_proc"] = proc
            state["rec_draft"] = str(result.get("path") or "")
            state["rec_started_at"] = float(result.get("started_at") or time.time())
            state["clean_events"].put({
                "kind": "rec_started",
                "data": {
                    "ok": True,
                    "busy": True,
                    "phase": "recording" if mode == "full" else "selecting",
                    "mode": mode,
                    "path": result.get("path") or "",
                    "started_at": state["rec_started_at"],
                    "message": (
                        "正在全屏录制…" if mode == "full"
                        else "请选择录制区域，选完后自动开始"
                    ),
                    "_hidden": hide_self,
                },
            })

            # Wait until screencapture exits (user stop / toolbar / timed)
            wait = rec_mod.wait_process(proc)
            path = str(state.get("rec_draft") or result.get("path") or "")
            started_at = float(state.get("rec_started_at") or 0.0)
            state["rec_proc"] = None

            if wait.get("timed_out"):
                final = {"ok": False, "error": "录制超时", "path": path}
            else:
                # Interactive cancel often leaves empty/missing file
                final = rec_mod.finalize_draft(path, started_at=started_at)
                if not final.get("ok"):
                    err = wait.get("stderr") or final.get("error") or "已取消录制"
                    need_perm = perm_mod.looks_like_screen_permission_error(err) or (
                        perm_mod.screen_capture_granted() is False
                        and "取消" not in str(err)
                    )
                    if need_perm:
                        err = perm_mod.screen_permission_message(app_name=APP_NAME)
                        final = {
                            "ok": False,
                            "error": err,
                            "path": "",
                            "permission": "screen",
                        }
                    else:
                        final = {"ok": False, "error": err, "path": ""}

            final = dict(final or {})
            final["_hidden"] = hide_self
            final["mode"] = mode
            state["clean_events"].put({"kind": "rec_done", "data": final})

        if hide_self:
            try:
                window.orderOut_(None)
            except Exception:
                pass
        threading.Thread(target=run_rec, daemon=True).start()

    def stop_recording() -> None:
        if not state.get("rec_busy"):
            call_js("__setRecordingToast", {"ok": False, "message": "当前没有在录制"})
            return
        proc = state.get("rec_proc")
        call_js("__setRecordingState", {
            "busy": True,
            "phase": "stopping",
            "message": "正在停止并生成文件…",
            "mode": state.get("rec_mode") or "",
        })
        if proc is None:
            return
        def _stop() -> None:
            try:
                rec_mod.stop_process(proc)
            except Exception:
                _log("recording stop failed:\n" + traceback.format_exc())
        threading.Thread(target=_stop, daemon=True).start()

    def finish_recording_save(data: Dict[str, Any]) -> None:
        draft = str(data.get("draft") or state.get("rec_draft") or "")
        open_after = bool(data.get("open_after", prefs.get("recording_open_after", False)))
        result = rec_mod.save_recording(draft, open_after=open_after)
        if result.get("ok"):
            state["rec_draft"] = ""
            call_js("__closeRecordingEditor", {})
            call_js("__setRecordingResult", result)
            call_js("__setRecordingList", rec_mod.folder_payload())
            call_js("__setRecordingToast", {
                "ok": True,
                "message": result.get("message") or "录屏已保存",
            })
        else:
            call_js("__setRecordingToast", {
                "ok": False,
                "message": result.get("error") or "保存失败",
            })

    def finish_recording_cancel(data: Optional[Dict[str, Any]] = None) -> None:
        data = dict(data or {})
        draft = str(data.get("draft") or state.get("rec_draft") or "")
        if draft:
            rec_mod.discard_draft(draft)
        state["rec_draft"] = ""
        call_js("__closeRecordingEditor", {})
        call_js("__setRecordingToast", {"ok": True, "message": "已丢弃录制"})
        call_js("__setRecordingList", rec_mod.folder_payload())

    def reload_hotkeys() -> None:
        center = state.get("hotkeys")
        if center is None:
            return
        cfg = prefs.load()

        def make_cb(mode: str):
            def _cb() -> None:
                try:
                    start_screenshot({"mode": mode})
                except Exception:
                    _log("hotkey screenshot failed:\n" + traceback.format_exc())

            return _cb

        def make_rec_cb(mode: str):
            def _cb() -> None:
                try:
                    start_recording({"mode": mode})
                except Exception:
                    _log("hotkey recording failed:\n" + traceback.format_exc())

            return _cb

        def stop_cb() -> None:
            try:
                stop_recording()
            except Exception:
                _log("hotkey stop recording failed:\n" + traceback.format_exc())

        center.set_bindings({
            "hotkey_shot_selection": (
                str(cfg.get("hotkey_shot_selection") or ""),
                make_cb("selection"),
            ),
            "hotkey_shot_window": (
                str(cfg.get("hotkey_shot_window") or ""),
                make_cb("window"),
            ),
            "hotkey_shot_full": (
                str(cfg.get("hotkey_shot_full") or ""),
                make_cb("full"),
            ),
            "hotkey_rec_selection": (
                str(cfg.get("hotkey_rec_selection") or ""),
                make_rec_cb("selection"),
            ),
            "hotkey_rec_full": (
                str(cfg.get("hotkey_rec_full") or ""),
                make_rec_cb("full"),
            ),
            "hotkey_rec_stop": (
                str(cfg.get("hotkey_rec_stop") or ""),
                stop_cb,
            ),
        })
        center.set_enabled(True)

    def call_js(fn: str, payload: Dict[str, Any]) -> None:
        """Push JSON via base64. Use ASCII-only JSON so atob never mangling UTF-8."""
        try:
            # ensure_ascii=True → \uXXXX escapes; atob + JSON.parse is always safe for CJK
            raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
            b64 = base64.b64encode(raw.encode("ascii")).decode("ascii")
            js = (
                "(function(){try{"
                f'var d=JSON.parse(atob("{b64}"));'
                f"if(typeof window.{fn}==='function'){{window.{fn}(d);}}"
                "else{window.__pending=window.__pending||[];"
                f'window.__pending.push(["{fn}",d]);'
                "}"
                "}catch(e){try{document.getElementById('status').textContent='JS:'+e;}catch(_){}}})();"
            )
            webview.evaluateJavaScript_completionHandler_(js, None)
        except Exception:
            _log(f"call_js {fn} failed:\n" + traceback.format_exc())

    def push_permissions_status(*, force: bool = False) -> None:
        """Refresh permission page off the main thread so nav stays responsive.

        Desktop/Documents/Downloads probes can stall on TCC prompts; running them
        synchronously on the bridge thread made「权限」feel stuck / unclickable.
        """
        now = time.time()
        last_at = float(state.get("perms_push_at") or 0.0)
        if not force and state.get("perms_busy") and (now - last_at) < 8.0:
            return
        if not force and (now - last_at) < 0.4 and state.get("last_perms"):
            call_js("__setPermissionsStatus", state["last_perms"])
            return
        state["perms_busy"] = True
        state["perms_push_at"] = now

        def work() -> None:
            try:
                status = perm_mod.permissions_status(app_name=APP_NAME)
                state["last_perms"] = status
                call_js("__setPermissionsStatus", status)
            except Exception:
                _log("permissions_status failed:\n" + traceback.format_exc())
            finally:
                state["perms_busy"] = False

        threading.Thread(target=work, daemon=True).start()

    def push_metrics(s: Snapshot) -> None:
        state["latest"] = s
        visible = False
        try:
            visible = bool(window.isVisible())
        except Exception:
            visible = True
        page = str(state.get("page") or "overview")
        call_js(
            "__setMetrics",
            snapshot_to_payload(collector, s, page=page, panel_visible=visible),
        )

    def start_timer_if_needed() -> None:
        if state["timer_started"]:
            return
        state["timer_started"] = True
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            float(state["interval"]), ticker, "onTick:", None, False
        )

    class Bridge(NSObject):
        def userContentController_didReceiveScriptMessage_(self, _controller, message):  # noqa: N802
            try:
                body = message.body()
                data = _js_body_to_dict(body)
            except Exception:
                _log("bridge parse failed:\n" + traceback.format_exc())
                return
            if not data:
                return
            typ = data.get("type")
            if typ == "ui_ready":
                state["ready"] = True
                _log("ui_ready received")
                push_settings()
                if state["latest"] is not None:
                    push_metrics(state["latest"])
                start_timer_if_needed()
            elif typ == "window_drag":
                # Fallback when CSS regions / overlays miss a hit; works if button still down
                try:
                    ev = NSApp.currentEvent()
                    if ev is not None:
                        window.performWindowDragWithEvent_(ev)
                except Exception:
                    pass
            elif typ == "theme":
                theme = data.get("theme")
                if theme not in ("dark", "light", "system"):
                    theme = "dark" if theme == "dark" else "light"
                prefs.set_pref("theme", theme)
                glass = data.get("glass")
                if glass in ("opaque", "medium", "clear"):
                    prefs.set_pref("glass", glass)
                apply_window_appearance(theme, prefs.get("glass", "medium"))
                call_js("__setTheme", {
                    "theme": theme,
                    "glass": prefs.get("glass", "medium"),
                })
                call_js("__setSettings", prefs.settings_payload())
            elif typ == "pause":
                state["paused"] = bool(data.get("paused"))
                call_js("__setInterval", {
                    "ms": int(round(float(state["interval"]) * 1000)),
                    "paused": bool(state["paused"]),
                })
                if state["latest"] is not None:
                    menubar.update(state["latest"])
            elif typ == "interval":
                try:
                    ms = max(400, min(5000, int(data.get("ms", 1000))))
                    state["interval"] = ms / 1000.0
                    prefs.set_pref("refresh_ms", ms)
                    call_js("__setSettings", prefs.settings_payload())
                except Exception:
                    pass
            elif typ == "settings_get":
                push_settings()
            elif typ == "settings_set":
                values = data.get("values") if isinstance(data.get("values"), dict) else {
                    k: v for k, v in data.items() if k != "type"
                }
                cfg = prefs.update_prefs(values or {})
                apply_runtime_prefs(cfg)
                push_settings()
            elif typ == "settings_reset":
                cfg = prefs.reset_prefs()
                apply_runtime_prefs(cfg)
                push_settings()
            elif typ == "page":
                state["page"] = str(data.get("page") or "overview")
                if state["page"] == "shot":
                    call_js("__setScreenshotList", shot_mod.folder_payload())
                elif state["page"] == "rec":
                    call_js("__setRecordingList", rec_mod.folder_payload())
                # perms: handled by permissions_status message from showPage (async)
            elif typ == "open_privacy_settings":
                kind = str(data.get("kind") or "screen")
                nk = perm_mod._normalize_kind(kind)
                try:
                    if nk == "screen":
                        perm_mod.request_screen_capture()
                    elif nk == "accessibility":
                        perm_mod.request_accessibility(prompt=True)
                    elif nk == "microphone":
                        perm_mod.request_microphone()
                except Exception:
                    pass
                result = perm_mod.open_privacy_settings(kind)

                def _after_open() -> None:
                    status = perm_mod.permissions_status(app_name=APP_NAME)
                    state["last_perms"] = status
                    call_js("__setPermissionGuideResult", {
                        "ok": bool(result.get("ok")),
                        "kind": result.get("kind") or nk,
                        "message": (
                            "已打开系统设置，请勾选后返回本页查看结果"
                            if result.get("ok")
                            else (result.get("error") or "无法打开系统设置")
                        ),
                        "status": status,
                    })
                    call_js("__setPermissionsStatus", status)

                threading.Thread(target=_after_open, daemon=True).start()
            elif typ == "permission_guide":
                kind = str(data.get("kind") or "screen")
                call_js(
                    "__showPermissionGuide",
                    perm_mod.permission_guide_payload(kind, app_name=APP_NAME),
                )
            elif typ == "permissions_status":
                push_permissions_status(force=True)
            elif typ == "permission_request":
                kind = str(data.get("kind") or "screen")

                def _req() -> None:
                    result = perm_mod.request_permission(kind)
                    # Always open settings as well so user can confirm the toggle
                    try:
                        perm_mod.open_privacy_settings(kind)
                    except Exception:
                        pass
                    status = result.get("status") or perm_mod.permissions_status(app_name=APP_NAME)
                    state["last_perms"] = status
                    granted = result.get("granted")
                    call_js("__setPermissionsStatus", status)
                    call_js("__setPermissionGuideResult", {
                        "ok": True,
                        "kind": result.get("kind") or kind,
                        "granted": granted,
                        "message": (
                            "已开启，权限生效"
                            if granted is True
                            else "已发起授权，请在系统设置中勾选后点「重新检测」"
                        ),
                        "status": status,
                    })

                threading.Thread(target=_req, daemon=True).start()
            elif typ == "finder_new_txt":
                create_finder_txt()
            elif typ == "finder_new_txt_install":
                enabled = bool(data.get("enabled", True))
                cfg = prefs.update_prefs({"finder_new_txt": enabled})
                apply_runtime_prefs(cfg)
                push_settings()
                call_js("__setScreenshotToast", {
                    "ok": bool(cfg.get("finder_new_txt")) == enabled or not enabled,
                    "message": (
                        "已启用 Finder 右键「新建文本文档」" if enabled and cfg.get("finder_new_txt")
                        else ("已关闭 Finder 右键服务" if not enabled else "启用失败，请重试")
                    ),
                })
            elif typ == "connectivity_run":
                self._connectivity_run()
            elif typ == "connectivity_cancel":
                state["conn_cancel"] = True
            elif typ == "screenshot_list":
                call_js("__setScreenshotList", shot_mod.folder_payload())
            elif typ == "screenshot_capture":
                start_screenshot(data)
            elif typ == "hotkey_record":
                binding = str(data.get("id") or "")
                if binding not in (
                    "hotkey_shot_selection",
                    "hotkey_shot_window",
                    "hotkey_shot_full",
                    "hotkey_rec_selection",
                    "hotkey_rec_full",
                    "hotkey_rec_stop",
                ):
                    return
                center = state.get("hotkeys")
                if center is None:
                    return

                def on_recorded(bid: str, spec: str) -> None:
                    try:
                        prefs.update_prefs({bid: spec})
                        reload_hotkeys()
                        push_settings()
                        label = hotkey_mod.format_hotkey(spec)
                        call_js("__setHotkeyRecord", {
                            "id": bid,
                            "spec": spec,
                            "label": label,
                            "recording": False,
                        })
                        call_js("__setScreenshotToast", {
                            "ok": True,
                            "message": ("已清除快捷键" if not spec else ("已设置 " + label)),
                        })
                    except Exception:
                        _log("hotkey record save failed:\n" + traceback.format_exc())

                def on_cancel() -> None:
                    call_js("__setHotkeyRecord", {
                        "id": binding,
                        "recording": False,
                        "cancelled": True,
                    })

                center.start_record(binding, on_recorded=on_recorded, on_cancel=on_cancel)
                call_js("__setHotkeyRecord", {"id": binding, "recording": True})
            elif typ == "hotkey_clear":
                binding = str(data.get("id") or "")
                if binding not in (
                    "hotkey_shot_selection",
                    "hotkey_shot_window",
                    "hotkey_shot_full",
                    "hotkey_rec_selection",
                    "hotkey_rec_full",
                    "hotkey_rec_stop",
                ):
                    return
                prefs.update_prefs({binding: ""})
                reload_hotkeys()
                push_settings()
                call_js("__setHotkeyRecord", {
                    "id": binding,
                    "spec": "",
                    "label": "未设置",
                    "recording": False,
                })
            elif typ == "hotkey_cancel":
                center = state.get("hotkeys")
                if center is not None:
                    center.cancel_record()
                call_js("__setHotkeyRecord", {"recording": False, "cancelled": True})
            elif typ == "screenshot_reveal":
                shot_mod.reveal(str(data.get("path") or ""))
            elif typ == "screenshot_open":
                shot_mod.open_file(str(data.get("path") or ""))
            elif typ == "screenshot_folder":
                shot_mod.open_folder()
            elif typ == "screenshot_copy":
                ok = shot_mod.copy_to_clipboard(str(data.get("path") or ""))
                call_js("__setScreenshotToast", {
                    "ok": ok,
                    "message": "已复制到剪贴板" if ok else "复制失败",
                })
            elif typ == "screenshot_delete":
                ok = shot_mod.delete_file(str(data.get("path") or ""))
                call_js("__setScreenshotList", shot_mod.folder_payload())
                call_js("__setScreenshotToast", {
                    "ok": ok,
                    "message": "已删除" if ok else "删除失败",
                })
            elif typ == "screenshot_annotate_save":
                finish_annotate_save(data)
            elif typ == "screenshot_annotate_copy":
                finish_annotate_copy(data)
            elif typ == "screenshot_annotate_cancel":
                finish_annotate_cancel(data)
            elif typ == "recording_start":
                start_recording(data)
            elif typ == "recording_stop":
                stop_recording()
            elif typ == "recording_list":
                call_js("__setRecordingList", rec_mod.folder_payload())
            elif typ == "recording_folder":
                rec_mod.open_folder()
            elif typ == "recording_open":
                rec_mod.open_file(str(data.get("path") or ""))
            elif typ == "recording_reveal":
                rec_mod.reveal(str(data.get("path") or ""))
            elif typ == "recording_copy":
                ok = rec_mod.copy_file_to_clipboard(str(data.get("path") or ""))
                call_js("__setRecordingToast", {
                    "ok": ok,
                    "message": "已复制文件到剪贴板" if ok else "复制失败",
                })
            elif typ == "recording_delete":
                ok = rec_mod.delete_file(str(data.get("path") or ""))
                call_js("__setRecordingList", rec_mod.folder_payload())
                call_js("__setRecordingToast", {
                    "ok": ok,
                    "message": "已删除" if ok else "删除失败",
                })
            elif typ == "recording_save":
                finish_recording_save(data)
            elif typ == "recording_cancel":
                finish_recording_cancel(data)
            elif typ == "clean_scan":
                self._do_clean_scan()
            elif typ == "clean_cancel":
                tok = state.get("clean_cancel")
                if tok is not None:
                    try:
                        tok.cancel()
                    except Exception:
                        pass
            elif typ == "clean_reveal":
                path = str(data.get("path") or "")
                self._reveal_path(path)
            elif typ == "proc_action":
                try:
                    pid = int(data.get("pid") or 0)
                except Exception:
                    pid = 0
                action = str(data.get("action") or "")
                self._proc_action(pid, action)
            elif typ == "proc_batch":
                raw_pids = data.get("pids") or []
                if not isinstance(raw_pids, (list, tuple)):
                    try:
                        raw_pids = list(raw_pids)
                    except Exception:
                        raw_pids = []
                pids = []
                for x in raw_pids:
                    try:
                        pids.append(int(x))
                    except Exception:
                        pass
                action = str(data.get("action") or "terminate")
                self._proc_batch(pids, action)
            elif typ == "clean_pref":
                patch = {}
                if "move_to_trash" in data:
                    patch["clean_move_to_trash"] = bool(data.get("move_to_trash"))
                if "clean_confirm" in data:
                    patch["clean_confirm"] = bool(data.get("clean_confirm"))
                if patch:
                    prefs.update_prefs(patch)
                call_js("__setCleanPrefs", {
                    "move_to_trash": bool(prefs.get("clean_move_to_trash", True)),
                    "clean_confirm": bool(prefs.get("clean_confirm", True)),
                    "history": list(prefs.get("clean_history") or [])[:8],
                })
                call_js("__setSettings", prefs.settings_payload())
            elif typ == "clean_history":
                call_js("__setCleanPrefs", {
                    "move_to_trash": bool(prefs.get("clean_move_to_trash", True)),
                    "clean_confirm": bool(prefs.get("clean_confirm", True)),
                    "history": list(prefs.get("clean_history") or [])[:8],
                })
                # Re-push last scan if available so tab switch doesn't lose results
                if state.get("last_scan_result"):
                    call_js("__setCleanScan", state["last_scan_result"])
            elif typ == "clean_empty_trash":
                self._do_empty_trash()
            elif typ == "clean_run":
                item_ids = data.get("item_ids") or data.get("ids") or []
                if not isinstance(item_ids, (list, tuple)):
                    try:
                        item_ids = list(item_ids)
                    except Exception:
                        item_ids = []
                keys = data.get("keys") or []
                if not isinstance(keys, (list, tuple)):
                    try:
                        keys = list(keys)
                    except Exception:
                        keys = []
                move_to_trash = data.get("move_to_trash")
                if move_to_trash is None:
                    move_to_trash = bool(prefs.get("clean_move_to_trash", True))
                client_items = _coerce_clean_items(data.get("items"))
                # Also accept a bare path list as fallback
                if not client_items:
                    paths = data.get("paths") or []
                    if not isinstance(paths, (list, tuple)):
                        try:
                            paths = list(paths)
                        except Exception:
                            paths = []
                    client_items = _coerce_clean_items([
                        {"path": str(p), "name": Path(str(p)).name} for p in paths if str(p).strip()
                    ])
                _log(
                    f"clean_run request ids={len(item_ids)} "
                    f"client_items={len(client_items)} trash={bool(move_to_trash)}"
                )
                self._do_clean_run(
                    [str(x) for x in item_ids],
                    [str(k) for k in keys],
                    bool(move_to_trash),
                    client_items=client_items,
                )
            elif typ == "uninstall_list":
                # Re-push cached list if available
                if state.get("last_uninstall_apps") and not state.get("uninstall_busy"):
                    call_js("__setUninstallApps", state["last_uninstall_apps"])
                else:
                    self._do_uninstall_list()
            elif typ == "uninstall_scan":
                self._do_uninstall_list(force=True)
            elif typ == "uninstall_leftovers":
                self._do_uninstall_leftovers(data)
            elif typ == "uninstall_run":
                self._do_uninstall_run(data)
            elif typ == "uninstall_cancel":
                tok = state.get("uninstall_cancel")
                if tok is not None:
                    try:
                        tok.cancel()
                    except Exception:
                        pass
            elif typ == "uninstall_reveal":
                path = str(data.get("path") or "")
                self._reveal_path(path)
            elif typ == "startup_list":
                if state.get("last_startup_result") and not state.get("startup_busy"):
                    call_js("__setStartupList", state["last_startup_result"])
                else:
                    self._do_startup_list()
            elif typ == "startup_scan":
                self._do_startup_list(force=True)
            elif typ == "startup_set":
                self._do_startup_set(data)
            elif typ == "startup_cancel":
                tok = state.get("startup_cancel")
                if tok is not None:
                    try:
                        tok.cancel()
                    except Exception:
                        pass
            elif typ == "startup_open_settings":
                try:
                    from .startup import open_login_items_settings
                    open_login_items_settings()
                except Exception:
                    _log("startup_open_settings failed:\n" + traceback.format_exc())
            elif typ == "startup_reveal":
                path = str(data.get("path") or "")
                self._reveal_path(path)

        def _screenshot_capture(self, data: Dict[str, Any]) -> None:
            start_screenshot(data)

        def _connectivity_run(self) -> None:
            if state.get("conn_busy"):
                call_js("__setConnectivityProgress", {
                    "phase": "progress",
                    "message": "正在检测中…",
                    "busy": True,
                })
                return
            state["conn_busy"] = True
            state["conn_cancel"] = False
            call_js("__setConnectivityProgress", {
                "phase": "start",
                "percent": 0,
                "busy": True,
                "message": "准备检测…",
                "results": [],
            })

            def work() -> None:
                def on_progress(payload: Dict[str, Any]) -> None:
                    try:
                        data = dict(payload or {})
                        data["busy"] = data.get("phase") not in ("done", "cancelled")
                        state["clean_events"].put({"kind": "conn_progress", "data": data})
                    except Exception:
                        pass

                try:
                    result = conn_mod.run_connectivity_test(
                        on_progress=on_progress,
                        cancel_check=lambda: bool(state.get("conn_cancel")),
                    )
                    state["clean_events"].put({"kind": "conn_done", "data": result})
                except Exception:
                    _log("connectivity failed:\n" + traceback.format_exc())
                    state["clean_events"].put({
                        "kind": "conn_done",
                        "data": {
                            "phase": "done",
                            "busy": False,
                            "score": 0,
                            "label": "异常",
                            "tone": "fail",
                            "message": "检测失败",
                            "results": [],
                            "groups": [],
                        },
                    })

            threading.Thread(target=work, daemon=True).start()

        def _reveal_path(self, path: str) -> None:
            if not path:
                return
            try:
                from AppKit import NSWorkspace  # type: ignore
                from Foundation import NSURL  # type: ignore

                url = NSURL.fileURLWithPath_(path)
                NSWorkspace.sharedWorkspace().activateFileViewerSelectingURLs_([url])
            except Exception:
                _log("reveal failed:\n" + traceback.format_exc())

        def _proc_action(self, pid: int, action: str) -> None:
            result = self._proc_action_result(pid, action)
            call_js("__setProcResult", result)

        def _proc_action_result(self, pid: int, action: str) -> Dict[str, Any]:
            if pid <= 0:
                return {"ok": False, "pid": pid, "error": "无效 PID"}
            # Never allow killing ourselves / launchd
            if pid in (0, 1, os.getpid()):
                return {"ok": False, "pid": pid, "error": "不能操作该进程"}
            try:
                import psutil

                proc = psutil.Process(pid)
                name = proc.name()
                if action == "terminate":
                    proc.terminate()
                    return {"ok": True, "pid": pid, "action": "terminate", "name": name}
                if action == "kill":
                    if not prefs.get("allow_force_kill", True):
                        return {"ok": False, "pid": pid, "error": "已在设置中禁用强制结束"}
                    proc.kill()
                    return {"ok": True, "pid": pid, "action": "kill", "name": name}
                if action == "reveal":
                    exe = ""
                    try:
                        exe = proc.exe() or ""
                    except Exception:
                        exe = ""
                    if exe:
                        self._reveal_path(exe)
                        return {"ok": True, "pid": pid, "action": "reveal", "name": name}
                    return {"ok": False, "pid": pid, "error": "无法定位可执行文件"}
                return {"ok": False, "pid": pid, "error": "未知操作"}
            except Exception as exc:
                _log(f"proc_action failed pid={pid}:\n" + traceback.format_exc())
                return {"ok": False, "pid": pid, "error": str(exc)}

        def _proc_batch(self, pids: list, action: str) -> None:
            action = "kill" if action == "kill" else "terminate"
            if action == "kill" and not prefs.get("allow_force_kill", True):
                call_js("__setProcBatchResult", {
                    "ok_count": 0,
                    "fail_count": len(pids or []),
                    "action": action,
                    "ok_pids": [],
                    "error": "已在设置中禁用强制结束",
                })
                return
            ok_pids = []
            fail_count = 0
            seen = set()
            for raw in pids or []:
                try:
                    pid = int(raw)
                except Exception:
                    fail_count += 1
                    continue
                if pid in seen:
                    continue
                seen.add(pid)
                result = self._proc_action_result(pid, action)
                if result.get("ok"):
                    ok_pids.append(pid)
                else:
                    fail_count += 1
            call_js("__setProcBatchResult", {
                "ok_count": len(ok_pids),
                "fail_count": fail_count,
                "action": action,
                "ok_pids": ok_pids,
            })
            _log(f"proc_batch action={action} ok={len(ok_pids)} fail={fail_count}")

        def _queue_event(self, payload: Dict[str, Any]) -> None:
            try:
                state["clean_events"].put(payload)
            except Exception:
                pass

        def _do_clean_scan(self) -> None:
            if state["clean_busy"]:
                call_js("__setCleanProgress", {
                    "phase": "scan",
                    "percent": 0,
                    "current": "已有清理任务进行中…",
                })
                return
            from .cleaner import CancelToken

            state["clean_busy"] = True
            token = CancelToken()
            state["clean_cancel"] = token

            def work() -> None:
                from .cleaner import scan_detailed

                try:
                    def on_progress(info: Dict[str, Any]) -> None:
                        self._queue_event({"kind": "progress", "data": info})

                    result = scan_detailed(progress=on_progress, cancel=token)
                    state["last_scan_items"] = list(result.get("items") or [])
                    state["last_scan_result"] = result
                    self._queue_event({"kind": "scan_result", "data": result})
                    _log(
                        f"clean_scan ok items={result.get('item_count')} "
                        f"total={result.get('total_text')} cancelled={result.get('cancelled')}"
                    )
                except Exception:
                    _log("clean_scan failed:\n" + traceback.format_exc())
                    self._queue_event({
                        "kind": "scan_result",
                        "data": {
                            "items": [],
                            "categories": [],
                            "total_text": "扫描失败",
                            "selected_text": "0 B",
                            "safe_text": "0 B",
                            "item_count": 0,
                            "error": "scan failed",
                        },
                    })
                finally:
                    state["clean_busy"] = False
                    state["clean_cancel"] = None

            threading.Thread(target=work, daemon=True).start()

        def _do_empty_trash(self) -> None:
            if state["clean_busy"]:
                call_js("__setCleanProgress", {
                    "phase": "clean",
                    "percent": 0,
                    "current": "已有清理任务进行中…",
                })
                return
            from .cleaner import CancelToken

            state["clean_busy"] = True
            token = CancelToken()
            state["clean_cancel"] = token

            def work() -> None:
                from .cleaner import empty_trash, format_size, scan_detailed

                try:
                    def on_progress(info: Dict[str, Any]) -> None:
                        self._queue_event({"kind": "progress", "data": info})

                    result = empty_trash(progress=on_progress, cancel=token)
                    self._queue_event({
                        "kind": "clean_result",
                        "data": {
                            "freed_bytes": result.freed_bytes,
                            "freed_text": format_size(result.freed_bytes),
                            "removed_items": result.removed_items,
                            "errors": list(result.errors or [])[:8],
                            "moved_to_trash": False,
                            "emptied_trash": True,
                            "cancelled": bool(result.cancelled),
                            "requested": result.removed_items,
                            "action_label": "已清空废纸篓",
                            "will_rescan": bool(result.removed_items > 0 and not result.cancelled),
                        },
                    })
                    if result.removed_items > 0 and not result.cancelled:
                        try:
                            refresh_token = CancelToken()
                            state["clean_cancel"] = refresh_token
                            refreshed = scan_detailed(progress=on_progress, cancel=refresh_token)
                            state["last_scan_items"] = list(refreshed.get("items") or [])
                            state["last_scan_result"] = refreshed
                            self._queue_event({"kind": "scan_result", "data": refreshed})
                        except Exception:
                            pass
                except Exception:
                    _log("empty_trash failed:\n" + traceback.format_exc())
                    self._queue_event({
                        "kind": "clean_result",
                        "data": {
                            "freed_text": "0 B",
                            "errors": ["清空废纸篓失败"],
                            "removed_items": 0,
                        },
                    })
                finally:
                    state["clean_busy"] = False
                    state["clean_cancel"] = None

            threading.Thread(target=work, daemon=True).start()

        def _do_clean_run(
            self,
            item_ids: list,
            keys: list,
            move_to_trash: bool,
            client_items: Optional[list] = None,
        ) -> None:
            if state["clean_busy"]:
                call_js("__setCleanProgress", {
                    "phase": "clean",
                    "percent": 0,
                    "current": "已有清理任务进行中…",
                })
                return

            from .cleaner import CancelToken

            state["clean_busy"] = True
            token = CancelToken()
            state["clean_cancel"] = token

            def work() -> None:
                from .cleaner import clean_items, format_size, scan_detailed

                try:
                    id_set = {str(x) for x in (item_ids or []) if str(x)}
                    key_set = {str(k) for k in (keys or []) if str(k)}
                    cached = list(state.get("last_scan_items") or [])
                    selected: list = []

                    # Prefer explicit items from UI (path-accurate, survives ID refresh)
                    if client_items:
                        selected = _coerce_clean_items(client_items)
                    elif id_set:
                        selected = [i for i in cached if str(i.get("id") or "") in id_set]
                    elif key_set:
                        selected = [i for i in cached if str(i.get("category") or "") in key_set]
                    else:
                        selected = [i for i in cached if i.get("selected")]

                    if not selected and id_set and cached:
                        _log(f"clean_run id mismatch ids={len(id_set)} cached={len(cached)}")

                    if not selected and not client_items and key_set and not id_set:
                        data = scan_detailed(selected_categories=list(key_set) or None, cancel=token)
                        cached = list(data.get("items") or [])
                        state["last_scan_items"] = cached
                        selected = [i for i in cached if str(i.get("category") or "") in key_set]

                    if not selected:
                        self._queue_event({
                            "kind": "clean_result",
                            "data": {
                                "freed_bytes": 0,
                                "freed_text": "0 B",
                                "removed_items": 0,
                                "errors": ["未找到要清理的项目，请重新扫描后再勾选"],
                                "details": [],
                                "requested": 0,
                                "moved_to_trash": bool(move_to_trash),
                                "cancelled": False,
                            },
                        })
                        return

                    def on_progress(info: Dict[str, Any]) -> None:
                        self._queue_event({"kind": "progress", "data": info})

                    _log(f"clean_run start selected={len(selected)} trash={move_to_trash}")
                    result = clean_items(
                        selected,
                        progress=on_progress,
                        move_to_trash=move_to_trash,
                        cancel=token,
                    )
                    payload = {
                        "freed_bytes": result.freed_bytes,
                        "freed_text": format_size(result.freed_bytes),
                        "removed_items": result.removed_items,
                        "errors": result.errors[:12],
                        "details": result.details[:80],
                        "requested": len(selected),
                        "moved_to_trash": result.moved_to_trash,
                        "cancelled": result.cancelled,
                        "will_rescan": bool(result.removed_items > 0 and not result.cancelled),
                        "action_label": (
                            "已移至废纸篓（清空后才真正释放磁盘）"
                            if result.moved_to_trash else "已永久删除并释放空间"
                        ),
                    }
                    self._queue_event({"kind": "clean_result", "data": payload})
                    if result.removed_items > 0 or result.freed_bytes > 0:
                        try:
                            import time as _time

                            hist = prefs.push_clean_history({
                                "ts": int(_time.time()),
                                "freed_bytes": result.freed_bytes,
                                "freed_text": format_size(result.freed_bytes),
                                "removed_items": result.removed_items,
                                "moved_to_trash": result.moved_to_trash,
                            })
                            self._queue_event({
                                "kind": "prefs",
                                "data": {
                                    "move_to_trash": bool(prefs.get("clean_move_to_trash", True)),
                                    "clean_confirm": bool(prefs.get("clean_confirm", True)),
                                    "history": hist[:8],
                                },
                            })
                        except Exception:
                            pass
                    _log(
                        f"clean_run ok freed={result.freed_bytes} items={result.removed_items} "
                        f"errors={len(result.errors)}"
                    )
                    # Auto-rescan after successful clean with a FRESH cancel token
                    if result.removed_items > 0 and not result.cancelled:
                        try:
                            refresh_token = CancelToken()
                            state["clean_cancel"] = refresh_token
                            refreshed = scan_detailed(progress=on_progress, cancel=refresh_token)
                            state["last_scan_items"] = list(refreshed.get("items") or [])
                            state["last_scan_result"] = refreshed
                            self._queue_event({"kind": "scan_result", "data": refreshed})
                        except Exception:
                            pass
                except Exception:
                    _log("clean_run failed:\n" + traceback.format_exc())
                    self._queue_event({
                        "kind": "clean_result",
                        "data": {
                            "freed_text": "0 B",
                            "details": [],
                            "errors": ["清理失败"],
                            "removed_items": 0,
                        },
                    })
                finally:
                    state["clean_busy"] = False
                    state["clean_cancel"] = None

            threading.Thread(target=work, daemon=True).start()

        def _do_uninstall_list(self, force: bool = False) -> None:
            if state.get("uninstall_busy"):
                call_js("__setUninstallProgress", {
                    "phase": "list",
                    "percent": 0,
                    "current": "正在扫描应用…",
                    "busy": True,
                })
                return
            if state.get("last_uninstall_apps") and not force:
                call_js("__setUninstallApps", state["last_uninstall_apps"])
                return
            from .cleaner import CancelToken

            state["uninstall_busy"] = True
            token = CancelToken()
            state["uninstall_cancel"] = token

            def work() -> None:
                from .uninstaller import list_apps

                try:
                    def on_progress(info: Dict[str, Any]) -> None:
                        payload = dict(info or {})
                        payload["busy"] = True
                        self._queue_event({"kind": "uninstall_progress", "data": payload})

                    result = list_apps(progress=on_progress, cancel=token, include_icons=True)
                    state["last_uninstall_apps"] = result
                    self._queue_event({"kind": "uninstall_apps", "data": result})
                except Exception:
                    _log("uninstall_list failed:\n" + traceback.format_exc())
                    self._queue_event({
                        "kind": "uninstall_apps",
                        "data": {"apps": [], "error": "扫描应用失败", "app_count": 0},
                    })
                finally:
                    state["uninstall_busy"] = False
                    state["uninstall_cancel"] = None

            threading.Thread(target=work, daemon=True).start()

        def _do_uninstall_leftovers(self, data: Dict[str, Any]) -> None:
            if state.get("uninstall_busy"):
                call_js("__setUninstallProgress", {
                    "phase": "leftovers",
                    "percent": 0,
                    "current": "已有卸载任务进行中…",
                    "busy": True,
                })
                return
            app_path = str(data.get("path") or "")
            if not app_path:
                call_js("__setUninstallLeftovers", {"items": [], "error": "未指定应用"})
                return
            from .cleaner import CancelToken

            state["uninstall_busy"] = True
            token = CancelToken()
            state["uninstall_cancel"] = token

            def work() -> None:
                from .uninstaller import scan_leftovers

                try:
                    def on_progress(info: Dict[str, Any]) -> None:
                        payload = dict(info or {})
                        payload["busy"] = True
                        self._queue_event({"kind": "uninstall_progress", "data": payload})

                    result = scan_leftovers(
                        app_path=app_path,
                        bundle_id=str(data.get("bundle_id") or ""),
                        app_name=str(data.get("name") or ""),
                        progress=on_progress,
                        cancel=token,
                    )
                    state["last_uninstall_detail"] = result
                    self._queue_event({"kind": "uninstall_leftovers", "data": result})
                except Exception:
                    _log("uninstall_leftovers failed:\n" + traceback.format_exc())
                    self._queue_event({
                        "kind": "uninstall_leftovers",
                        "data": {"items": [], "error": "扫描关联文件失败"},
                    })
                finally:
                    state["uninstall_busy"] = False
                    state["uninstall_cancel"] = None

            threading.Thread(target=work, daemon=True).start()

        def _do_uninstall_run(self, data: Dict[str, Any]) -> None:
            if state.get("uninstall_busy"):
                call_js("__setUninstallProgress", {
                    "phase": "uninstall",
                    "percent": 0,
                    "current": "已有卸载任务进行中…",
                    "busy": True,
                })
                return
            raw_items = data.get("items") or []
            if not isinstance(raw_items, (list, tuple)):
                try:
                    raw_items = list(raw_items)
                except Exception:
                    raw_items = []
            items = []
            for it in raw_items:
                if not isinstance(it, dict):
                    continue
                path = str(it.get("path") or "").strip()
                if not path:
                    continue
                items.append({
                    "path": path,
                    "name": str(it.get("name") or Path(path).name),
                    "kind": str(it.get("kind") or "leftover"),
                    "category_title": str(it.get("category_title") or ""),
                    "bytes": int(it.get("bytes") or 0),
                })
            if not items:
                call_js("__setUninstallResult", {
                    "freed_text": "0 B",
                    "removed_items": 0,
                    "errors": ["未选择要卸载的项目"],
                })
                return
            move_to_trash = data.get("move_to_trash")
            if move_to_trash is None:
                move_to_trash = True
            from .cleaner import CancelToken

            state["uninstall_busy"] = True
            token = CancelToken()
            state["uninstall_cancel"] = token

            def work() -> None:
                from .cleaner import format_size as fmt
                from .uninstaller import list_apps, uninstall_items

                try:
                    def on_progress(info: Dict[str, Any]) -> None:
                        payload = dict(info or {})
                        payload["busy"] = True
                        self._queue_event({"kind": "uninstall_progress", "data": payload})

                    result = uninstall_items(
                        items,
                        progress=on_progress,
                        move_to_trash=bool(move_to_trash),
                        cancel=token,
                    )
                    self._queue_event({
                        "kind": "uninstall_result",
                        "data": {
                            "freed_bytes": result.freed_bytes,
                            "freed_text": fmt(result.freed_bytes),
                            "removed_items": result.removed_items,
                            "errors": list(result.errors or [])[:8],
                            "moved_to_trash": bool(result.moved_to_trash),
                            "cancelled": bool(result.cancelled),
                            "requested": len(items),
                            "action_label": "已移至废纸篓" if result.moved_to_trash else "已永久删除",
                            "will_refresh": bool(result.removed_items > 0 and not result.cancelled),
                        },
                    })
                    if result.removed_items > 0 and not result.cancelled:
                        try:
                            refresh_token = CancelToken()
                            state["uninstall_cancel"] = refresh_token
                            refreshed = list_apps(
                                progress=on_progress,
                                cancel=refresh_token,
                                include_icons=True,
                            )
                            state["last_uninstall_apps"] = refreshed
                            state["last_uninstall_detail"] = None
                            self._queue_event({"kind": "uninstall_apps", "data": refreshed})
                        except Exception:
                            pass
                except Exception:
                    _log("uninstall_run failed:\n" + traceback.format_exc())
                    self._queue_event({
                        "kind": "uninstall_result",
                        "data": {
                            "freed_text": "0 B",
                            "removed_items": 0,
                            "errors": ["卸载失败"],
                        },
                    })
                finally:
                    state["uninstall_busy"] = False
                    state["uninstall_cancel"] = None

            threading.Thread(target=work, daemon=True).start()

        def _do_startup_list(self, force: bool = False) -> None:
            if state.get("startup_busy"):
                call_js("__setStartupProgress", {
                    "phase": "list",
                    "percent": 0,
                    "current": "正在扫描启动项…",
                    "busy": True,
                })
                return
            if state.get("last_startup_result") and not force:
                call_js("__setStartupList", state["last_startup_result"])
                return
            from .cleaner import CancelToken

            state["startup_busy"] = True
            token = CancelToken()
            state["startup_cancel"] = token

            def work() -> None:
                from .startup import list_startup

                try:
                    def on_progress(info: Dict[str, Any]) -> None:
                        payload = dict(info or {})
                        payload["busy"] = True
                        self._queue_event({"kind": "startup_progress", "data": payload})

                    result = list_startup(progress=on_progress, cancel=token)
                    state["last_startup_result"] = result
                    self._queue_event({"kind": "startup_list", "data": result})
                except Exception:
                    _log("startup_list failed:\n" + traceback.format_exc())
                    self._queue_event({
                        "kind": "startup_list",
                        "data": {"items": [], "error": "扫描启动项失败", "item_count": 0},
                    })
                finally:
                    state["startup_busy"] = False
                    state["startup_cancel"] = None

            threading.Thread(target=work, daemon=True).start()

        def _do_startup_set(self, data: Dict[str, Any]) -> None:
            if state.get("startup_busy"):
                call_js("__setStartupProgress", {
                    "phase": "set",
                    "current": "请稍候…",
                    "busy": True,
                })
                return
            item = data.get("item") if isinstance(data.get("item"), dict) else {}
            enabled = bool(data.get("enabled"))
            if not item:
                call_js("__setStartupResult", {"ok": False, "error": "未指定启动项"})
                return

            state["startup_busy"] = True

            def work() -> None:
                from .startup import list_startup, set_item_enabled

                try:
                    result = set_item_enabled(item, enabled=enabled)
                    self._queue_event({"kind": "startup_result", "data": result})
                    if result.get("ok"):
                        refreshed = list_startup()
                        state["last_startup_result"] = refreshed
                        self._queue_event({"kind": "startup_list", "data": refreshed})
                except Exception:
                    _log("startup_set failed:\n" + traceback.format_exc())
                    self._queue_event({
                        "kind": "startup_result",
                        "data": {"ok": False, "error": "操作失败"},
                    })
                finally:
                    state["startup_busy"] = False

            threading.Thread(target=work, daemon=True).start()

    class Delegate(NSObject):
        def windowShouldClose_(self, sender):  # noqa: N802
            sender.orderOut_(None)
            return False

        def applicationShouldTerminateAfterLastWindowClosed_(self, _app):  # noqa: N802
            return False

    class NavDelegate(NSObject):
        def webView_didFinishNavigation_(self, _webview, _nav):  # noqa: N802
            _log("webview didFinishNavigation")
            # Fallback if ui_ready message is missed
            if not state["ready"] and state["latest"] is not None:
                push_metrics(state["latest"])
                start_timer_if_needed()

    class UIDelegate(NSObject):
        """WKWebView does not show JS alert/confirm unless UIDelegate is set."""

        def webView_runJavaScriptAlertPanelWithMessage_initiatedByFrame_completionHandler_(  # noqa: N802
            self, web_view, message, _frame, completion_handler
        ):
            try:
                alert = NSAlert.alloc().init()
                alert.setMessageText_(APP_NAME)
                alert.setInformativeText_(str(message or ""))
                alert.addButtonWithTitle_("好")
                win = web_view.window() if web_view is not None else None
                if win is not None:
                    alert.beginSheetModalForWindow_completionHandler_(
                        win, lambda _resp: completion_handler()
                    )
                else:
                    alert.runModal()
                    completion_handler()
            except Exception:
                try:
                    completion_handler()
                except Exception:
                    pass

        def webView_runJavaScriptConfirmPanelWithMessage_initiatedByFrame_completionHandler_(  # noqa: N802
            self, web_view, message, _frame, completion_handler
        ):
            try:
                alert = NSAlert.alloc().init()
                alert.setMessageText_("请确认")
                alert.setInformativeText_(str(message or ""))
                alert.addButtonWithTitle_("确定")
                alert.addButtonWithTitle_("取消")
                win = web_view.window() if web_view is not None else None

                def _done(resp) -> None:
                    try:
                        completion_handler(bool(resp == NSAlertFirstButtonReturn))
                    except Exception:
                        try:
                            completion_handler(False)
                        except Exception:
                            pass

                if win is not None:
                    alert.beginSheetModalForWindow_completionHandler_(win, _done)
                else:
                    _done(alert.runModal())
            except Exception:
                try:
                    completion_handler(False)
                except Exception:
                    pass

    NSApplication.sharedApplication()
    NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    style = (
        NSWindowStyleMaskTitled
        | NSWindowStyleMaskClosable
        | NSWindowStyleMaskMiniaturizable
        | NSWindowStyleMaskResizable
        | NSWindowStyleMaskFullSizeContentView
    )
    frame = NSMakeRect(120, 80, 1200, 780)
    try:
        screen = NSScreen.mainScreen().visibleFrame()
        frame = NSMakeRect(
            screen.origin.x + 80,
            screen.origin.y + 60,
            min(1200, screen.size.width - 120),
            min(780, screen.size.height - 100),
        )
    except Exception:
        pass

    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        frame, style, NSBackingStoreBuffered, False
    )
    window.setTitle_("SupTools")
    window.setMinSize_((1020, 640))
    try:
        window.setTitlebarAppearsTransparent_(True)
        window.setTitleVisibility_(1)  # NSWindowTitleHidden
        window.setMovable_(True)
        window.setMovableByWindowBackground_(True)
        window.setOpaque_(False)
        window.setBackgroundColor_(NSColor.clearColor())
    except Exception:
        pass
    delegate = Delegate.alloc().init()
    window.setDelegate_(delegate)

    # WKWebView swallows mouse events; CSS -webkit-app-region does not move
    # AppKit windows. Transparent NSView strips call performWindowDragWithEvent_.
    class WindowDragView(NSView):
        def hitTest_(self, point):  # noqa: N802
            hit = NSView.hitTest_(self, point)
            return hit

        def acceptsFirstMouse_(self, _event):  # noqa: N802
            return True

        def mouseDown_(self, event):  # noqa: N802
            win = self.window()
            if win is not None:
                try:
                    win.performWindowDragWithEvent_(event)
                except Exception:
                    pass

    config = WKWebViewConfiguration.alloc().init()
    controller = config.userContentController()
    bridge = Bridge.alloc().init()
    controller.addScriptMessageHandler_name_(bridge, "suptools")

    root_bounds = window.contentView().bounds()
    container = NSView.alloc().initWithFrame_(root_bounds)
    container.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
    try:
        container.setWantsLayer_(True)
    except Exception:
        pass

    # Native system glass behind the transparent WKWebView
    vibrancy = NSVisualEffectView.alloc().initWithFrame_(root_bounds)
    vibrancy.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
    vibrancy.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
    vibrancy.setState_(NSVisualEffectStateActive)
    try:
        # HUD / fullscreen materials read darker; fall back to under-window
        from AppKit import (  # type: ignore
            NSVisualEffectMaterialHUDWindow,
            NSVisualEffectMaterialUnderWindowBackground,
        )

        try:
            vibrancy.setMaterial_(NSVisualEffectMaterialHUDWindow)
        except Exception:
            vibrancy.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
    except Exception:
        try:
            vibrancy.setMaterial_(3)  # ultraDark-ish legacy
        except Exception:
            pass
    container.addSubview_(vibrancy)
    state["ns_window"] = window
    state["ns_vibrancy"] = vibrancy
    apply_window_appearance(
        str(prefs.get("theme", "light") or "light"),
        str(prefs.get("glass", "medium") or "medium"),
    )

    webview = WKWebView.alloc().initWithFrame_configuration_(root_bounds, config)
    webview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
    try:
        webview.setValue_forKey_(False, "drawsBackground")
    except Exception:
        try:
            webview.setOpaque_(False)
        except Exception:
            pass
    nav_delegate = NavDelegate.alloc().init()
    ui_delegate = UIDelegate.alloc().init()
    webview.setNavigationDelegate_(nav_delegate)
    webview.setUIDelegate_(ui_delegate)
    container.addSubview_(webview)

    def _add_drag_strip(rect, mask):
        strip = WindowDragView.alloc().initWithFrame_(rect)
        strip.setAutoresizingMask_(mask)
        try:
            strip.setWantsLayer_(True)
            strip.layer().setBackgroundColor_(None)
        except Exception:
            pass
        container.addSubview_(strip)
        return strip

    W = float(root_bounds.size.width)
    H = float(root_bounds.size.height)
    sidebar_w = 220.0
    title_h = 52.0
    controls_w = 310.0
    lights_w = 78.0  # leave traffic-light hit targets alone
    # Main toolbar (title text area) — full width minus sidebar & right controls
    _add_drag_strip(
        NSMakeRect(
            sidebar_w,
            H - title_h,
            max(80.0, W - sidebar_w - controls_w),
            title_h,
        ),
        NSViewWidthSizable | NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin,
    )
    # Sidebar title / brand under the traffic lights
    _add_drag_strip(
        NSMakeRect(lights_w, H - title_h, max(40.0, sidebar_w - lights_w), title_h),
        NSViewMaxXMargin | NSViewMinYMargin,
    )
    _add_drag_strip(
        NSMakeRect(8.0, H - 128.0, sidebar_w - 16.0, 56.0),
        NSViewMaxXMargin | NSViewMinYMargin,
    )
    # Sidebar host footer
    _add_drag_strip(
        NSMakeRect(0.0, 0.0, sidebar_w, 96.0),
        NSViewMaxXMargin | NSViewMaxYMargin,
    )

    window.setContentView_(container)
    webview.loadHTMLString_baseURL_(DASHBOARD_HTML, NSURL.URLWithString_("about:blank"))

    def show_panel() -> None:
        window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        # Force a fresh full sample when the panel opens
        try:
            page = str(state.get("page") or "overview")
            snap_now = collector.sample(
                include_processes=page in ("processes", "overview", "cpu", "memory"),
                include_interfaces=True,
            )
            push_metrics(snap_now)
            menubar.update(snap_now, history=collector.cpu_history)
        except Exception:
            if state["latest"] is not None:
                push_metrics(state["latest"])

    def hide_panel() -> None:
        window.orderOut_(None)

    def quit_app() -> None:
        release_singleton()
        NSApp.terminate_(None)

    def toggle_pause() -> None:
        state["paused"] = not state["paused"]
        call_js("__setInterval", {
            "ms": int(round(float(state["interval"]) * 1000)),
            "paused": bool(state["paused"]),
        })
        if state["latest"] is not None:
            menubar.update(state["latest"])

    def open_clean() -> None:
        show_panel()
        call_js("__navigate", {"page": "clean"})

    def open_uninstall() -> None:
        show_panel()
        call_js("__navigate", {"page": "uninstall"})

    def open_startup() -> None:
        show_panel()
        call_js("__navigate", {"page": "startup"})

    def open_perms() -> None:
        show_panel()
        call_js("__navigate", {"page": "perms"})
        push_permissions_status(force=True)

    def open_settings() -> None:
        show_panel()
        call_js("__navigate", {"page": "settings"})
        push_settings()

    def open_processes() -> None:
        show_panel()
        call_js("__navigate", {"page": "processes"})

    def open_shot() -> None:
        show_panel()
        call_js("__navigate", {"page": "shot"})
        call_js("__setScreenshotList", shot_mod.folder_payload())

    def open_recording() -> None:
        show_panel()
        call_js("__navigate", {"page": "rec"})
        call_js("__setRecordingList", rec_mod.folder_payload())

    def open_connectivity() -> None:
        show_panel()
        call_js("__navigate", {"page": "conn"})

    def create_finder_txt(paths: Optional[List[str]] = None) -> Dict[str, Any]:
        open_file = bool(prefs.get("finder_new_txt_open", True))
        result = finder_txt.create_new_text_file(
            paths=paths,
            open_file=open_file,
            reveal=True,
        )
        try:
            call_js("__setScreenshotToast", {
                "ok": bool(result.get("ok")),
                "message": result.get("message") or result.get("error") or "",
            })
        except Exception:
            pass
        return result

    def toggle_theme() -> None:
        cur = str(prefs.get("theme", "light") or "light")
        order = ("light", "dark", "system")
        try:
            nxt = order[(order.index(cur) + 1) % len(order)]
        except ValueError:
            nxt = "dark"
        prefs.set_pref("theme", nxt)
        apply_window_appearance(nxt)
        call_js("__setTheme", {"theme": nxt})
        call_js("__setSettings", prefs.settings_payload())

    class ActivateObserver(NSObject):
        def onActivate_(self, _note):  # noqa: N802
            show_panel()

        def onAppActive_(self, _note):  # noqa: N802
            # Refresh permission badges when returning from System Settings
            try:
                if str(state.get("page") or "") == "perms":
                    push_permissions_status(force=True)
                else:
                    push_settings()
            except Exception:
                pass

    activate_observer = ActivateObserver.alloc().init()
    try:
        NSDistributedNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            activate_observer,
            "onActivate:",
            SHOW_NOTIFICATION,
            None,
        )
    except Exception:
        _log("activate observer failed:\n" + traceback.format_exc())
    try:
        from Foundation import NSNotificationCenter  # type: ignore

        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            activate_observer,
            "onAppActive:",
            "NSApplicationDidBecomeActiveNotification",
            None,
        )
    except Exception:
        _log("app-active observer failed:\n" + traceback.format_exc())

    # Restore preferred refresh
    try:
        state["interval"] = max(0.5, float(prefs.get("refresh_ms", 1000)) / 1000.0)
    except Exception:
        pass

    menubar = MenuBarController(
        on_show=show_panel,
        on_hide=hide_panel,
        on_toggle_pause=toggle_pause,
        on_quit=quit_app,
        is_paused=lambda: bool(state["paused"]),
        on_open_clean=open_clean,
        on_open_uninstall=open_uninstall,
        on_open_startup=open_startup,
        on_open_perms=open_perms,
        on_open_settings=open_settings,
        on_open_processes=open_processes,
        on_open_shot=open_shot,
        on_open_recording=open_recording,
        on_stop_recording=stop_recording,
        on_open_connectivity=open_connectivity,
        on_theme_toggle=toggle_theme,
        on_new_txt=lambda: create_finder_txt(),
        on_mode_changed=lambda _mode: push_settings(),
    )

    hotkey_center = hotkey_mod.HotkeyCenter()
    state["hotkeys"] = hotkey_center
    try:
        reload_hotkeys()
        hotkey_center.install()
    except Exception:
        _log("hotkey install failed:\n" + traceback.format_exc())

    # Finder Services: 新建文本文档 / 在此新建文本文档
    class FinderTextService(NSObject):
        def createNewTextFile_userData_error_(self, pboard, _userData, _error):  # noqa: N802
            paths = finder_txt.paths_from_pasteboard(pboard)
            create_finder_txt(paths)
            return None

        def createNewTextFileHere_userData_error_(self, _pboard, _userData, _error):  # noqa: N802
            create_finder_txt(None)
            return None

    try:
        service_provider = FinderTextService.alloc().init()
        NSApp.setServicesProvider_(service_provider)
        state["service_provider"] = service_provider
        try:
            from AppKit import NSUpdateDynamicServices  # type: ignore

            NSUpdateDynamicServices()
        except Exception:
            pass
    except Exception:
        _log("services provider failed:\n" + traceback.format_exc())
        service_provider = None

    # Re-install Finder quick action if user previously enabled it
    try:
        if bool(prefs.get("finder_new_txt", False)) and not finder_txt.is_service_installed():
            finder_txt.install_service()
        elif bool(prefs.get("finder_new_txt", False)):
            # Refresh helper script in place
            finder_txt.install_service()
    except Exception:
        _log("finder service sync failed:\n" + traceback.format_exc())

    def flush_clean_events() -> int:
        """Drain cleaner progress/results onto the main thread for WKWebView."""
        drained = 0
        while drained < 40:
            try:
                evt = state["clean_events"].get_nowait()
            except queue.Empty:
                break
            drained += 1
            kind = evt.get("kind")
            data = evt.get("data") or {}
            if kind == "progress":
                call_js("__setCleanProgress", data)
            elif kind == "scan_result":
                call_js("__setCleanScan", data)
            elif kind == "clean_result":
                call_js("__setCleanResult", data)
            elif kind == "prefs":
                call_js("__setCleanPrefs", data)
            elif kind == "uninstall_progress":
                call_js("__setUninstallProgress", data)
            elif kind == "uninstall_apps":
                call_js("__setUninstallApps", data)
            elif kind == "uninstall_leftovers":
                call_js("__setUninstallLeftovers", data)
            elif kind == "uninstall_result":
                call_js("__setUninstallResult", data)
            elif kind == "startup_progress":
                call_js("__setStartupProgress", data)
            elif kind == "startup_list":
                call_js("__setStartupList", data)
            elif kind == "startup_result":
                call_js("__setStartupResult", data)
            elif kind == "shot_done":
                state["shot_busy"] = False
                if data.get("_hidden"):
                    try:
                        show_panel()
                        call_js("__navigate", {"page": "shot"})
                    except Exception:
                        pass
                call_js("__setScreenshotProgress", {"busy": False, "message": ""})
                if data.get("ok") and data.get("annotate") and data.get("preview"):
                    state["shot_draft"] = str(data.get("path") or "")
                    call_js("__openScreenshotEditor", {
                        "preview": data.get("preview"),
                        "draft": data.get("path") or "",
                        "also_copy": bool(data.get("also_copy")),
                        "mode": data.get("mode") or "",
                        "file": data.get("file"),
                    })
                else:
                    call_js("__setScreenshotResult", data)
                    call_js("__setScreenshotList", shot_mod.folder_payload())
                    msg = data.get("message") or data.get("error") or ""
                    if msg:
                        call_js("__setScreenshotToast", {
                            "ok": bool(data.get("ok")),
                            "message": msg,
                        })
                    if (not data.get("ok")) and (
                        data.get("permission") == "screen"
                        or perm_mod.looks_like_screen_permission_error(msg)
                    ):
                        call_js(
                            "__showPermissionGuide",
                            perm_mod.permission_guide_payload("screen", app_name=APP_NAME),
                        )
            elif kind == "conn_progress":
                call_js("__setConnectivityProgress", data)
            elif kind == "conn_done":
                state["conn_busy"] = False
                state["conn_cancel"] = False
                data = dict(data or {})
                data["busy"] = False
                data["phase"] = data.get("phase") or "done"
                call_js("__setConnectivityResult", data)
            elif kind == "rec_started":
                state["rec_busy"] = True
                if data.get("_hidden") and str(data.get("mode") or "") == "full":
                    try:
                        show_panel()
                        call_js("__navigate", {"page": "rec"})
                    except Exception:
                        pass
                elif not data.get("_hidden"):
                    try:
                        call_js("__navigate", {"page": "rec"})
                    except Exception:
                        pass
                call_js("__setRecordingState", data)
                try:
                    if menubar and "rec_stop" in getattr(menubar, "_items", {}):
                        menubar._items["rec_stop"].setEnabled_(True)
                        menubar._items["rec_stop"].setTitle_("⏹  停止录屏")
                except Exception:
                    pass
            elif kind == "rec_done":
                state["rec_busy"] = False
                state["rec_proc"] = None
                try:
                    if menubar and "rec_stop" in getattr(menubar, "_items", {}):
                        menubar._items["rec_stop"].setEnabled_(False)
                        menubar._items["rec_stop"].setTitle_("⏹  停止录屏")
                except Exception:
                    pass
                if data.get("_hidden") or data.get("ok"):
                    try:
                        show_panel()
                        call_js("__navigate", {"page": "rec"})
                    except Exception:
                        pass
                call_js("__setRecordingState", {
                    "busy": False,
                    "phase": "idle",
                    "message": "",
                    "elapsed": 0,
                })
                if data.get("ok") and data.get("path"):
                    state["rec_draft"] = str(data.get("path") or "")
                    call_js("__openRecordingEditor", {
                        "draft": data.get("path") or "",
                        "file": data.get("file"),
                        "poster": data.get("poster"),
                        "mode": data.get("mode") or "",
                    })
                else:
                    state["rec_draft"] = ""
                    msg = data.get("message") or data.get("error") or ""
                    if msg:
                        call_js("__setRecordingToast", {
                            "ok": bool(data.get("ok")),
                            "message": msg,
                        })
                    call_js("__setRecordingList", rec_mod.folder_payload())
                    if (not data.get("ok")) and (
                        data.get("permission") == "screen"
                        or perm_mod.looks_like_screen_permission_error(msg)
                    ):
                        call_js(
                            "__showPermissionGuide",
                            perm_mod.permission_guide_payload("screen", app_name=APP_NAME),
                        )
        return drained

    def tick(_timer=None) -> None:
        try:
            flush_clean_events()
            if not state["paused"]:
                state["tick"] += 1
                visible = False
                try:
                    visible = bool(window.isVisible())
                except Exception:
                    visible = True
                page = str(state.get("page") or "overview")
                if not visible:
                    # Panel hidden: cheap sample for menubar only
                    nonlocal_snap = collector.sample_light()
                    state["latest"] = nonlocal_snap
                    menubar.update(nonlocal_snap, history=collector.cpu_history)
                    _notify_from_snap(nonlocal_snap)
                else:
                    need_procs = page in ("processes", "overview", "cpu", "memory")
                    include_procs = need_procs and (state["tick"] % 3 == 0 or page == "processes")
                    include_ifaces = page in ("overview", "network")
                    nonlocal_snap = collector.sample(
                        include_processes=include_procs,
                        include_interfaces=include_ifaces or (state["tick"] % 5 == 0),
                    )
                    push_metrics(nonlocal_snap)
                    menubar.update(nonlocal_snap, history=collector.cpu_history)
                    _notify_from_snap(nonlocal_snap)
                    if state["tick"] == 1:
                        _log(
                            f"first web push ok cpu={nonlocal_snap.cpu_percent} "
                            f"mem={nonlocal_snap.mem_percent}"
                        )
            elif state["latest"] is not None:
                # Keep pause glyph / tooltip in sync while metrics are frozen
                menubar.update(state["latest"], history=collector.cpu_history)
        except Exception:
            _log("tick failed:\n" + traceback.format_exc())
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            float(state["interval"]), ticker, "onTick:", None, False
        )

    class Ticker(NSObject):
        def onTick_(self, timer):  # noqa: N802
            tick(timer)

    class CleanPump(NSObject):
        def onPump_(self, timer):  # noqa: N802
            drained = 0
            try:
                drained = flush_clean_events()
            except Exception:
                pass
            # Idle: slow pump to save CPU; busy/clean: stay responsive
            if drained:
                delay = 0.08
            elif state.get("clean_busy") or state.get("shot_busy") or state.get("conn_busy") or state.get("rec_busy"):
                delay = 0.2
            else:
                delay = 0.75
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                delay, clean_pump, "onPump:", None, False
            )

    ticker = Ticker.alloc().init()
    clean_pump = CleanPump.alloc().init()
    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        0.12, clean_pump, "onPump:", None, False
    )

    # Safety: if ui_ready never arrives, still start after 1.2s
    class Starter(NSObject):
        def onStart_(self, timer):  # noqa: N802
            if state["latest"] is not None:
                push_metrics(state["latest"])
            start_timer_if_needed()
            _log("starter fallback fired")

    starter = Starter.alloc().init()
    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        1.2, starter, "onStart:", None, False
    )

    # Immediate menubar update
    if snap is not None:
        menubar.update(snap, history=collector.cpu_history)

    if prefs.get("start_hidden", False):
        window.orderOut_(None)
        _log("start_hidden: panel kept hidden")
    else:
        show_panel()
    _KEEP = [
        delegate,
        bridge,
        ticker,
        clean_pump,
        starter,
        activate_observer,
        menubar,
        hotkey_center,
        state.get("service_provider"),
        collector,
        window,
        container,
        vibrancy,
        webview,
        config,
        nav_delegate,
        WindowDragView,
    ]
    globals()["_SUPTOOLS_KEEPALIVE"] = _KEEP
    NSApp.run()


def run() -> None:
    """Start native AppKit + WebKit UI. Never import Tk in this process."""
    from .singleton import release_singleton

    # Singleton is acquired in systemmonit_launcher before deps/bootstrap.
    # Do not acquire again here (idempotent now, but launcher is the gate).
    try:
        run_native()
    finally:
        release_singleton()
