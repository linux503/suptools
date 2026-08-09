"""Lightweight macOS notifications for threshold alerts (Stats / iStat-style)."""

from __future__ import annotations

import subprocess
import time
from typing import Dict, List

# Cooldown per alert key so we don't spam Notification Center
_last_sent: Dict[str, float] = {}
_COOLDOWN_SEC = 5 * 60


def _can_send(key: str) -> bool:
    now = time.time()
    prev = _last_sent.get(key, 0.0)
    if now - prev < _COOLDOWN_SEC:
        return False
    _last_sent[key] = now
    return True


def notify(title: str, body: str, *, key: str) -> None:
    if not _can_send(key):
        return
    title = (title or "SupTools").replace('"', "'")
    body = (body or "").replace('"', "'")
    script = f'display notification "{body}" with title "{title}"'
    try:
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def maybe_notify_alerts(alerts: List[dict], *, enabled: bool) -> None:
    if not enabled or not alerts:
        return
    for a in alerts:
        text = str(a.get("text") or "").strip()
        if not text:
            continue
        level = str(a.get("level") or "warn")
        key = str(a.get("key") or text)
        title = "SupTools 告警" if level == "danger" else "SupTools"
        notify(title, text, key=key)


def build_threshold_alerts(
    *,
    cpu: float,
    mem: float,
    mem_pressure: str,
    disk: float,
    load0: float,
    cores: int,
    battery_percent: float,
    has_battery: bool,
    battery_plugged: bool,
    alert_cpu: float,
    alert_mem: float,
    alert_disk: float,
    alert_battery: float,
) -> List[dict]:
    alerts: List[dict] = []
    if cpu >= alert_cpu:
        alerts.append({
            "level": "danger" if cpu >= min(98, alert_cpu + 10) else "warn",
            "key": "cpu",
            "text": f"CPU 占用较高 {cpu:.0f}%",
        })
    if mem_pressure == "critical" or mem >= alert_mem:
        alerts.append({
            "level": "danger" if mem_pressure == "critical" else "warn",
            "key": "mem",
            "text": (
                f"内存压力偏高（{mem_pressure}） {mem:.0f}%"
                if mem_pressure != "normal"
                else f"内存占用较高 {mem:.0f}%"
            ),
        })
    if disk >= alert_disk:
        alerts.append({
            "level": "danger" if disk >= min(98, alert_disk + 5) else "warn",
            "key": "disk",
            "text": f"磁盘空间紧张 {disk:.0f}%",
        })
    elif disk >= max(70.0, alert_disk - 10):
        alerts.append({
            "level": "warn",
            "key": "disk_warn",
            "text": f"磁盘占用偏高 {disk:.0f}%",
        })
    if load0 > max(1.0, cores * 1.5):
        alerts.append({
            "level": "warn",
            "key": "load",
            "text": f"系统负载偏高 {load0:.2f}",
        })
    if has_battery and not battery_plugged and battery_percent <= alert_battery:
        alerts.append({
            "level": "danger" if battery_percent <= 10 else "warn",
            "key": "battery",
            "text": f"电池电量偏低 {battery_percent:.0f}%",
        })
    return alerts
