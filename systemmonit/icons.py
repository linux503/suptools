"""Shared icon paths and menu-bar title formatting."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .collector import Snapshot, format_bytes


def resource_dir() -> Path:
    env = os.environ.get("SUPTOOLS_APP_BUNDLE") or os.environ.get("SYSPULSE_APP_BUNDLE") or os.environ.get("SYSTEMMONIT_APP_BUNDLE")
    if env:
        p = Path(env) / "Contents" / "Resources"
        if p.is_dir():
            return p
    here = Path(__file__).resolve().parent
    for candidate in (
        here.parent / "Resources",
        Path("/Applications/SupTools.app/Contents/Resources"),
        Path("/Applications/SysPulse.app/Contents/Resources"),
    ):
        if candidate.is_dir():
            return candidate
    return here.parent / "Resources"


def status_icon_path() -> Optional[str]:
    res = resource_dir()
    for name in (
        "StatusGlyph@2x.png",
        "StatusGlyph.png",
        "StatusIcon@2x.png",
        "StatusIcon.png",
    ):
        p = res / name
        if p.is_file():
            return str(p)
    return None


def app_icon_path() -> Optional[str]:
    res = resource_dir()
    for name in ("SupToolsIcon.png", "SysPulseIcon.png", "SystemMonitIcon.png", "AppIcon.icns"):
        p = res / name
        if p.is_file():
            return str(p)
    return None


NAV_ICONS = {
    "overview": "◈",
    "cpu": "▣",
    "memory": "▦",
    "disk": "▤",
    "network": "⇄",
    "processes": "☰",
}

METRIC_ICONS = {
    "cpu": "▣",
    "memory": "▦",
    "disk": "▤",
    "network": "⇄",
    "down": "↓",
    "up": "↑",
}

MENUBAR_MODES = (
    ("net", "显示：网络吞吐"),
    ("net_m", "显示：网络(固定M)"),
    ("cpu_net", "显示：CPU · 网络"),
    ("cpu", "显示：CPU%"),
    ("memory", "显示：内存%"),
    ("compact", "显示：CPU·内存"),
    ("disk", "显示：磁盘可用"),
    ("battery", "显示：电池"),
    ("spark", "显示：CPU 波形"),
)

_SPARK = "▁▂▃▄▅▆▇"


def sparkline(values, width: int = 8) -> str:
    """Unicode sparkline like Stats / iStat mini graphs."""
    vals = [float(x) for x in list(values)[-width:]]
    if not vals:
        return _SPARK[0] * width
    while len(vals) < width:
        vals.insert(0, vals[0])
    lo = min(vals)
    hi = max(vals)
    if hi - lo < 0.5:
        # Flat history: map against 0–100 so idle/busy still show height
        lo, hi = 0.0, 100.0
    span = max(hi - lo, 1.0)
    out = []
    for v in vals:
        idx = int(round((v - lo) / span * (len(_SPARK) - 1)))
        out.append(_SPARK[max(0, min(len(_SPARK) - 1, idx))])
    return "".join(out)


def format_battery_menubar(percent: float, plugged: bool, has: bool) -> str:
    if not has:
        return "AC"
    pct = max(0, min(100, int(round(percent))))
    mark = "⚡" if plugged else "🔋"
    return f"{mark}{pct}%"


def format_disk_menubar(free: int, percent: float) -> str:
    """Show free space compactly, e.g. D128G or D82%."""
    if free <= 0 and percent <= 0:
        return "D—"
    # Prefer free bytes when we have them
    if free > 0:
        gb = free / (1024.0 ** 3)
        if gb >= 100:
            return f"D{gb:.0f}G"
        if gb >= 10:
            return f"D{gb:.0f}G"
        if gb >= 1:
            return f"D{gb:.1f}G"
        mb = free / (1024.0 ** 2)
        return f"D{mb:.0f}M"
    return f"D{100 - percent:.0f}%"


def format_net_menubar(n: float, fixed_m: bool = False) -> str:
    """Ultra-compact menubar rate — short digits, no figure-space padding."""
    v = max(0.0, float(n))

    if fixed_m:
        mb = v / (1024.0 * 1024.0)
        if mb < 0.05:
            return "0M"
        if mb < 9.95:
            return f"{mb:.1f}M"
        if mb < 99.5:
            return f"{mb:.0f}M"
        if mb < 999.5:
            return f"{mb:.0f}M"
        return f"{mb / 1024.0:.1f}G"

    # Auto unit, prefer ≤4 visible chars (e.g. 1.2K / 12M / 1.1G)
    if v < 512:
        return "0"
    if v < 1024 * 9.95:
        return f"{v / 1024.0:.1f}K"
    if v < 1024 * 999.5:
        return f"{v / 1024.0:.0f}K"
    if v < 1024 * 1024 * 9.95:
        return f"{v / (1024.0 * 1024.0):.1f}M"
    if v < 1024 * 1024 * 999.5:
        return f"{v / (1024.0 * 1024.0):.0f}M"
    if v < 1024 ** 3 * 9.95:
        return f"{v / (1024.0 ** 3):.1f}G"
    return f"{v / (1024.0 ** 3):.0f}G"


def format_net_m(n: float) -> str:
    """Megabyte rate with stable width for menubar / UI."""
    return format_net_menubar(n, fixed_m=True)


def format_net_compact(n: float) -> str:
    """Readable rate for tooltips / dropdown (variable width OK)."""
    v = max(0.0, float(n))
    if v < 1024:
        return f"{int(v)}B"
    if v < 1024 * 1024:
        kb = v / 1024.0
        return f"{kb:.0f}K" if kb >= 10 else f"{kb:.1f}K"
    if v < 1024 * 1024 * 1024:
        mb = v / (1024.0 * 1024.0)
        if mb < 10:
            return f"{mb:.2f}M"
        if mb < 100:
            return f"{mb:.1f}M"
        return f"{mb:.0f}M"
    gb = v / (1024.0 * 1024.0 * 1024.0)
    return f"{gb:.2f}G" if gb < 10 else f"{gb:.1f}G"


def format_net_pair(down: float, up: float, fixed_m: bool = False) -> str:
    """Tight ↓/↑ pair for the status item (no gaps)."""
    return f"↓{format_net_menubar(down, fixed_m)}↑{format_net_menubar(up, fixed_m)}"


def menubar_title(snap: Snapshot, paused: bool = False, mode: str = "net", history=None) -> str:
    """Menu bar title by display mode (stable width for net modes)."""
    if mode == "cpu":
        text = f"{snap.cpu_percent:4.0f}%"
    elif mode == "memory":
        text = f"M{snap.mem_percent:4.0f}%"
    elif mode == "compact":
        text = f"{snap.cpu_percent:3.0f}·{snap.mem_percent:3.0f}"
    elif mode == "cpu_net":
        text = f"{snap.cpu_percent:.0f}%{format_net_pair(snap.net_down_bps, snap.net_up_bps)}"
    elif mode == "net_m":
        text = format_net_pair(snap.net_down_bps, snap.net_up_bps, fixed_m=True)
    elif mode == "disk":
        text = format_disk_menubar(
            getattr(snap, "primary_disk_free", 0) or max(0, snap.primary_disk_total - snap.primary_disk_used),
            snap.primary_disk_percent,
        )
    elif mode == "battery":
        text = format_battery_menubar(
            snap.battery_percent, snap.battery_plugged, snap.has_battery
        )
    elif mode == "spark":
        hist = history if history is not None else []
        text = f"{sparkline(hist, 7)}{snap.cpu_percent:3.0f}"
    else:
        text = format_net_pair(snap.net_down_bps, snap.net_up_bps, fixed_m=False)
    if paused:
        text = f"❚{text}"
    return text


def menubar_tooltip(snap: Snapshot) -> str:
    pressure = {"normal": "正常", "warn": "警告", "critical": "严重"}.get(
        getattr(snap, "mem_pressure", "normal"), "正常"
    )
    lines = [
        "SupTools",
        f"▣ CPU   {snap.cpu_percent:.1f}%",
        f"▦ 内存  {snap.mem_percent:.1f}%  ({format_bytes(snap.mem_used)})  压力 {pressure}",
        f"↓ 下行  {format_net_compact(snap.net_down_bps)}/s",
        f"↑ 上行  {format_net_compact(snap.net_up_bps)}/s",
        f"▤ 磁盘  {snap.primary_disk_percent:.0f}%",
        f"负载    {snap.load_avg[0]:.2f}",
    ]
    if getattr(snap, "top_process_name", ""):
        lines.append(f"TOP   {snap.top_process_name}  {snap.top_process_cpu:.0f}%")
    if getattr(snap, "has_battery", False):
        plug = "充电中" if snap.battery_plugged else "使用电池"
        lines.append(f"电池  {snap.battery_percent:.0f}%  ·  {plug}")
    return "\n".join(lines)
