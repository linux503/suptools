"""macOS menu-bar app with live metrics and dashboard launcher."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

import rumps

from .collector import (
    MetricsCollector,
    Snapshot,
    format_bps,
    format_bps_short,
    format_bytes,
)

CONFIG_DIR = Path.home() / "Library" / "Application Support" / "SupTools"
CONFIG_PATH = CONFIG_DIR / "config.json"
MODES = ("cpu", "compact", "memory", "network")


def _load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"title_mode": "compact", "auto_open_panel": True, "refresh_sec": 1}


def _save_config(cfg: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class SupToolsBar(rumps.App):
    def __init__(self) -> None:
        self.cfg = _load_config()
        super().__init__(name="SupTools", title="--%", quit_button=None)

        self.collector = MetricsCollector()
        self.snap: Optional[Snapshot] = None
        self.paused = False
        self._dashboard_proc: Optional[subprocess.Popen] = None
        self._opening_panel = False
        self.title_mode = self.cfg.get("title_mode", "compact")
        if self.title_mode not in MODES:
            self.title_mode = "compact"

        self.cpu_item = rumps.MenuItem("CPU  —")
        self.mem_item = rumps.MenuItem("内存 —")
        self.load_item = rumps.MenuItem("负载 —")
        self.net_item = rumps.MenuItem("网络 —")
        self.disk_item = rumps.MenuItem("磁盘 —")

        self.mode_cpu = rumps.MenuItem("显示：CPU%", callback=self._set_mode_cpu)
        self.mode_compact = rumps.MenuItem("显示：CPU·内存", callback=self._set_mode_compact)
        self.mode_mem = rumps.MenuItem("显示：内存%", callback=self._set_mode_mem)
        self.mode_net = rumps.MenuItem("显示：网络吞吐", callback=self._set_mode_net)

        self.menu = [
            "SupTools",
            None,
            self.cpu_item,
            self.mem_item,
            self.load_item,
            self.net_item,
            self.disk_item,
            None,
            rumps.MenuItem("打开监控面板", callback=self.open_panel),
            rumps.MenuItem("暂停刷新", callback=self.toggle_pause),
            None,
            self.mode_cpu,
            self.mode_compact,
            self.mode_mem,
            self.mode_net,
            None,
            rumps.MenuItem("退出 SupTools", callback=self.quit_app),
        ]

        self._refresh()
        self._sync_mode_checks()
        self._did_autostart = False

    @rumps.timer(1)
    def on_timer(self, _):
        self._refresh()
        if not self._did_autostart and self.cfg.get("auto_open_panel", True):
            self._did_autostart = True
            self.open_panel(None)

    def _sync_mode_checks(self) -> None:
        mapping = {
            "cpu": self.mode_cpu,
            "compact": self.mode_compact,
            "memory": self.mode_mem,
            "network": self.mode_net,
        }
        for key, item in mapping.items():
            item.state = self.title_mode == key

    def _set_mode(self, mode: str) -> None:
        self.title_mode = mode
        self.cfg["title_mode"] = mode
        _save_config(self.cfg)
        self._sync_mode_checks()
        if self.snap:
            self._apply(self.snap)

    def _set_mode_cpu(self, _):
        self._set_mode("cpu")

    def _set_mode_compact(self, _):
        self._set_mode("compact")

    def _set_mode_mem(self, _):
        self._set_mode("memory")

    def _set_mode_net(self, _):
        self._set_mode("network")

    def _refresh(self) -> None:
        if self.paused:
            return
        try:
            self.snap = self.collector.sample_light()
            self._apply(self.snap)
        except Exception as exc:  # noqa: BLE001
            self.title = "ERR"
            self.cpu_item.title = f"采集失败: {exc}"

    def _apply(self, s: Snapshot) -> None:
        if self.title_mode == "cpu":
            self.title = f"{s.cpu_percent:.0f}%"
        elif self.title_mode == "memory":
            self.title = f"M{s.mem_percent:.0f}%"
        elif self.title_mode == "network":
            self.title = f"↓{format_bps_short(s.net_down_bps)} ↑{format_bps_short(s.net_up_bps)}"
        else:
            self.title = f"{s.cpu_percent:.0f}·{s.mem_percent:.0f}"

        self.cpu_item.title = f"CPU     {s.cpu_percent:.1f}%"
        self.mem_item.title = f"内存    {s.mem_percent:.1f}%   {format_bytes(s.mem_used)}"
        self.load_item.title = f"负载    {s.load_avg[0]:.2f}  {s.load_avg[1]:.2f}  {s.load_avg[2]:.2f}"
        self.net_item.title = f"网络    ↓{format_bps(s.net_down_bps)}  ↑{format_bps(s.net_up_bps)}"
        self.disk_item.title = (
            f"磁盘    {s.primary_disk_percent:.0f}%   "
            f"{format_bytes(s.primary_disk_used)}/{format_bytes(s.primary_disk_total)}"
            if s.primary_disk_total
            else f"磁盘    {s.primary_disk_percent:.0f}%"
        )

    def toggle_pause(self, sender):
        self.paused = not self.paused
        sender.title = "继续刷新" if self.paused else "暂停刷新"
        if self.paused:
            self.title = f"❚{self.title}"
        else:
            self._refresh()

    def open_panel(self, _):
        if self._dashboard_proc and self._dashboard_proc.poll() is None:
            rumps.notification(
                title="SupTools",
                subtitle="面板已在运行",
                message="请查看桌面窗口",
            )
            return
        if self._opening_panel:
            return
        self._opening_panel = True
        try:
            cmd = [
                sys.executable,
                "-c",
                "from systemmonit.app import run_dashboard; run_dashboard()",
            ]
            self._dashboard_proc = subprocess.Popen(cmd, env=dict(os.environ))
        finally:
            threading.Timer(2.0, self._clear_opening).start()

    def _clear_opening(self):
        self._opening_panel = False

    def quit_app(self, _):
        if self._dashboard_proc and self._dashboard_proc.poll() is None:
            try:
                self._dashboard_proc.terminate()
            except Exception:
                pass
        rumps.quit_application()


def run() -> None:
    SupToolsBar().run()
