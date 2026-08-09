"""SupTools dashboard — text-first layout that always shows live metrics."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import List, Optional

import tkinter as tk
from tkinter import ttk

from .collector import (
    MetricsCollector,
    Snapshot,
    format_bps,
    format_bytes,
    format_uptime,
)
from .icons import METRIC_ICONS, NAV_ICONS, format_net_m
from .menubar import MenuBarController
from .widgets import DualSparkline, RingGauge, Sparkline, StackedBar, Theme, UsageBar, card, metric_tile

FONT = ("Helvetica Neue", 12)
FONT_BOLD = ("Helvetica Neue", 12, "bold")
FONT_TITLE = ("Helvetica Neue", 18, "bold")
FONT_HERO = ("Helvetica Neue", 28, "bold")
FONT_BIG = ("Helvetica Neue", 22, "bold")
FONT_MONO = ("Menlo", 12)
FONT_SMALL = ("Helvetica Neue", 11)
FONT_TINY = ("Helvetica Neue", 10)

PAGES = [
    ("overview", "总览"),
    ("cpu", "CPU"),
    ("memory", "内存"),
    ("disk", "硬盘"),
    ("network", "网络"),
    ("processes", "进程"),
]

_STATUS_CN = {
    "running": "运行中",
    "sleeping": "睡眠",
    "disk-sleep": "磁盘等待",
    "stopped": "停止",
    "zombie": "僵尸",
    "dead": "结束",
    "idle": "空闲",
}

LOG = Path.home() / "Library" / "Logs" / "SupTools-dashboard.log"


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


class SupToolsApp(tk.Tk):
    def __init__(self, enable_menubar: bool = False) -> None:
        super().__init__()
        self.title("SupTools")
        self.geometry("1200x780")
        self.minsize(1020, 660)
        self.configure(bg=Theme.BG)

        self.collector = MetricsCollector()
        self.snap: Optional[Snapshot] = None
        self.page = "overview"
        self.refresh_ms = 1000
        self.paused = False
        self._nav_buttons = {}
        self.core_bars: List[tuple] = []
        self.disk_vol_widgets: List[dict] = []
        self._tick_count = 0
        self._want_menubar = enable_menubar
        self.menubar = None

        # StringVars — always readable even if canvas widgets fail to paint.
        self.var_status = tk.StringVar(value="正在采集本机数据…")
        self.var_host = tk.StringVar(value="…")
        self.var_meta = tk.StringVar(value="")
        self.var_title = tk.StringVar(value="总览")
        self.var_ov_header = tk.StringVar(value="加载中…")
        self.var_ov_sub = tk.StringVar(value="")
        self.var_cpu_detail = tk.StringVar(value="—")
        self.var_mem_detail = tk.StringVar(value="—")
        self.var_mem_legend = tk.StringVar(value="")
        self.var_net_down = tk.StringVar(value="↓  —")
        self.var_net_up = tk.StringVar(value="↑  —")
        self.var_net_iface = tk.StringVar(value="")
        self.var_disk_name = tk.StringVar(value="—")
        self.var_disk_text = tk.StringVar(value="—")
        self.var_disk_read = tk.StringVar(value="读  —")
        self.var_disk_write = tk.StringVar(value="写  —")
        self.var_proc_list = tk.StringVar(value="正在加载进程…")

        self._build_style()
        self._build()

        # Collect + paint BEFORE touching AppKit (menubar), which can break first paint.
        try:
            self.collector.sample(include_processes=False, include_interfaces=False)
            self.snap = self.collector.sample(include_processes=True, include_interfaces=True)
            self._render()
            _log(f"first paint ok cpu={self.snap.cpu_percent} mem={self.snap.mem_percent}")
        except Exception as exc:  # noqa: BLE001
            self.var_status.set(f"首次采集失败: {exc}")
            _log("first paint failed:\n" + traceback.format_exc())

        self.after(self.refresh_ms, self._tick)
        self.after(80, self._safe_render)
        self.after(250, self._safe_render)
        if self._want_menubar:
            # Defer AppKit status item until Tk has painted at least once.
            self.after(700, self._attach_menubar)
            self.protocol("WM_DELETE_WINDOW", self.hide_panel)

        self.lift()
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))
        self.focus_force()
        self.update_idletasks()

    def _attach_menubar(self) -> None:
        if self.menubar is not None:
            return
        try:
            self.menubar = MenuBarController(
                on_show=lambda: self.after(0, self.show_panel),
                on_hide=lambda: self.after(0, self.hide_panel),
                on_toggle_pause=lambda: self.after(0, self._toggle_pause),
                on_quit=lambda: self.after(0, self.quit_app),
                is_paused=lambda: self.paused,
            )
            if self.snap:
                self.menubar.update(self.snap)
            _log(f"menubar attached available={self.menubar.available}")
        except Exception:  # noqa: BLE001
            _log("menubar attach failed:\n" + traceback.format_exc())

    def _safe_render(self) -> None:
        try:
            if self.snap is None:
                self.snap = self.collector.sample()
            self._render()
        except Exception as exc:  # noqa: BLE001
            self.var_status.set(f"刷新失败: {exc}")
            _log("safe_render failed:\n" + traceback.format_exc())

    def _build_style(self) -> None:
        style = ttk.Style(self)
        # Prefer aqua for Treeview readability on macOS; fall back to clam.
        for theme in ("aqua", "clam", style.theme_use()):
            try:
                style.theme_use(theme)
                break
            except tk.TclError:
                continue
        style.configure(
            "Treeview",
            background=Theme.PANEL,
            foreground=Theme.TEXT,
            fieldbackground=Theme.PANEL,
            borderwidth=0,
            rowheight=28,
            font=FONT_MONO,
        )
        style.configure(
            "Treeview.Heading",
            background=Theme.PANEL_2,
            foreground=Theme.MUTED,
            relief="flat",
            font=FONT_BOLD,
        )
        style.map(
            "Treeview",
            background=[("selected", Theme.SELECT)],
            foreground=[("selected", Theme.TEXT)],
        )

    def _build(self) -> None:
        root = tk.Frame(self, bg=Theme.BG)
        root.pack(fill="both", expand=True)

        sidebar = tk.Frame(root, bg=Theme.SIDEBAR, width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="SupTools", bg=Theme.SIDEBAR, fg=Theme.ACCENT,
            font=("Helvetica Neue", 17, "bold"), anchor="w",
        ).pack(fill="x", padx=18, pady=(22, 2))
        tk.Label(
            sidebar, text="本机实时监控", bg=Theme.SIDEBAR, fg=Theme.MUTED,
            font=FONT_TINY, anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 18))

        for key, label in PAGES:
            icon = NAV_ICONS.get(key, "•")
            btn = tk.Button(
                sidebar, text=f"  {icon}   {label}", anchor="w", bd=0, highlightthickness=0,
                padx=10, pady=11, font=FONT,
                command=lambda k=key: self._show(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn

        tk.Label(
            sidebar, textvariable=self.var_host, bg=Theme.SIDEBAR, fg=Theme.TEXT,
            font=FONT_BOLD, anchor="w", wraplength=150, justify="left",
        ).pack(side="bottom", fill="x", padx=16, pady=(0, 12))
        tk.Label(
            sidebar, textvariable=self.var_meta, bg=Theme.SIDEBAR, fg=Theme.MUTED,
            font=FONT_TINY, anchor="w", wraplength=150, justify="left",
        ).pack(side="bottom", fill="x", padx=16, pady=(0, 4))

        main = tk.Frame(root, bg=Theme.BG)
        main.pack(side="left", fill="both", expand=True)

        # Pack bottom status FIRST so content always gets remaining space.
        status = tk.Frame(main, bg=Theme.PANEL_2, height=32)
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)
        tk.Label(
            status, textvariable=self.var_status, bg=Theme.PANEL_2, fg=Theme.ACCENT,
            font=FONT_MONO, anchor="w",
        ).pack(fill="both", padx=14, pady=4)

        toolbar = tk.Frame(main, bg=Theme.PANEL, height=54)
        toolbar.pack(side="top", fill="x")
        toolbar.pack_propagate(False)
        tk.Label(
            toolbar, textvariable=self.var_title, bg=Theme.PANEL, fg=Theme.TEXT, font=FONT_TITLE,
        ).pack(side="left", padx=20)
        self.pause_btn = tk.Button(
            toolbar, text="暂停", command=self._toggle_pause,
            bg=Theme.PANEL_2, fg=Theme.TEXT, bd=0, padx=14, pady=6, font=FONT,
            activebackground=Theme.SELECT, activeforeground=Theme.TEXT,
        )
        self.pause_btn.pack(side="right", padx=(8, 18), pady=11)
        self.interval_var = tk.StringVar(value="1s")
        for label, ms in (("0.5s", 500), ("1s", 1000), ("2s", 2000)):
            tk.Radiobutton(
                toolbar, text=label, variable=self.interval_var, value=label,
                command=lambda m=ms: self._set_interval(m),
                bg=Theme.PANEL, fg=Theme.TEXT, selectcolor=Theme.PANEL_2,
                activebackground=Theme.PANEL, activeforeground=Theme.ACCENT,
                font=FONT_TINY, highlightthickness=0,
            ).pack(side="right", padx=2)
        tk.Label(toolbar, text="刷新", bg=Theme.PANEL, fg=Theme.MUTED, font=FONT_TINY).pack(
            side="right", padx=(0, 6)
        )

        hero = tk.Frame(main, bg=Theme.BG, padx=14, pady=10)
        hero.pack(side="top", fill="x")
        for i in range(4):
            hero.columnconfigure(i, weight=1, uniform="h")
        self.hero_cpu_box, self.hero_cpu, self.hero_cpu_sub = metric_tile(
            hero, f"{METRIC_ICONS['cpu']}  CPU", Theme.CPU
        )
        self.hero_mem_box, self.hero_mem, self.hero_mem_sub = metric_tile(
            hero, f"{METRIC_ICONS['memory']}  内存", Theme.MEM
        )
        self.hero_net_box, self.hero_net, self.hero_net_sub = metric_tile(
            hero, f"{METRIC_ICONS['network']}  网络", Theme.NET_DOWN
        )
        self.hero_disk_box, self.hero_disk, self.hero_disk_sub = metric_tile(
            hero, f"{METRIC_ICONS['disk']}  磁盘", Theme.DISK
        )
        self.hero_cpu_box.grid(row=0, column=0, sticky="nsew", padx=5)
        self.hero_mem_box.grid(row=0, column=1, sticky="nsew", padx=5)
        self.hero_net_box.grid(row=0, column=2, sticky="nsew", padx=5)
        self.hero_disk_box.grid(row=0, column=3, sticky="nsew", padx=5)

        self.content = tk.Frame(main, bg=Theme.BG)
        self.content.pack(fill="both", expand=True)
        self.pages = {
            "overview": self._build_overview(self.content),
            "cpu": self._build_cpu(self.content),
            "memory": self._build_memory(self.content),
            "disk": self._build_disk(self.content),
            "network": self._build_network(self.content),
            "processes": self._build_processes(self.content),
        }
        self._show("overview")

    def _set_interval(self, ms: int) -> None:
        self.refresh_ms = ms

    def show_panel(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        self.after(50, self._safe_render)

    def hide_panel(self) -> None:
        self.withdraw()

    def quit_app(self) -> None:
        try:
            self.destroy()
        except tk.TclError:
            pass

    def _toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_btn.configure(text="继续" if self.paused else "暂停")

    def _show(self, key: str) -> None:
        self.page = key
        self.var_title.set(next(label for k, label in PAGES if k == key))
        for k, frame in self.pages.items():
            if k == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        for k, btn in self._nav_buttons.items():
            active = k == key
            btn.configure(
                bg=Theme.SELECT if active else Theme.SIDEBAR,
                fg=Theme.ACCENT if active else Theme.TEXT,
                activebackground=Theme.SELECT,
                activeforeground=Theme.ACCENT,
            )
        self.after(30, self._safe_render)

    # ---------- pages ----------

    def _build_overview(self, parent: tk.Frame) -> tk.Frame:
        page = tk.Frame(parent, bg=Theme.BG)
        body = tk.Frame(page, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        tk.Label(
            body, textvariable=self.var_ov_header, bg=Theme.BG, fg=Theme.TEXT,
            font=FONT_BIG, anchor="w",
        ).pack(fill="x")
        tk.Label(
            body, textvariable=self.var_ov_sub, bg=Theme.BG, fg=Theme.MUTED,
            font=FONT, anchor="w",
        ).pack(fill="x", pady=(2, 10))

        # Top summary strip — big numbers, no canvas dependency.
        strip = tk.Frame(body, bg=Theme.PANEL, padx=16, pady=14)
        strip.pack(fill="x", pady=(0, 10))
        for i in range(4):
            strip.columnconfigure(i, weight=1, uniform="s")

        def _cell(col, title, var, color):
            box = tk.Frame(strip, bg=Theme.PANEL)
            box.grid(row=0, column=col, sticky="nsew", padx=8)
            tk.Label(box, text=title, bg=Theme.PANEL, fg=Theme.MUTED, font=FONT_SMALL, anchor="w").pack(fill="x")
            tk.Label(box, textvariable=var, bg=Theme.PANEL, fg=color, font=FONT_HERO, anchor="w").pack(fill="x")

        self.var_strip_cpu = tk.StringVar(value="—")
        self.var_strip_mem = tk.StringVar(value="—")
        self.var_strip_net = tk.StringVar(value="—")
        self.var_strip_disk = tk.StringVar(value="—")
        _cell(0, f"{METRIC_ICONS['cpu']}  CPU 占用", self.var_strip_cpu, Theme.CPU)
        _cell(1, f"{METRIC_ICONS['memory']}  内存压力", self.var_strip_mem, Theme.MEM)
        _cell(2, f"{METRIC_ICONS['network']}  网络下行", self.var_strip_net, Theme.NET_DOWN)
        _cell(3, f"{METRIC_ICONS['disk']}  磁盘占用", self.var_strip_disk, Theme.DISK)

        grid = tk.Frame(body, bg=Theme.BG)
        grid.pack(fill="both", expand=True)
        for i in range(2):
            grid.columnconfigure(i, weight=1, uniform="a")
            grid.rowconfigure(i, weight=1)

        cpu_card = card(grid, f"{METRIC_ICONS['cpu']}  CPU", Theme.CPU)
        cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7), pady=6)
        cpu_row = tk.Frame(cpu_card.body, bg=Theme.PANEL)
        cpu_row.pack(fill="both", expand=True)
        self.ov_cpu_ring = RingGauge(cpu_row, size=120, color=Theme.CPU)
        self.ov_cpu_ring.pack(side="left", padx=(0, 12))
        cpu_right = tk.Frame(cpu_row, bg=Theme.PANEL)
        cpu_right.pack(side="left", fill="both", expand=True)
        tk.Label(
            cpu_right, textvariable=self.var_cpu_detail, bg=Theme.PANEL, fg=Theme.TEXT,
            font=FONT_MONO, justify="left", anchor="nw",
        ).pack(fill="both", expand=True)
        self.ov_cpu_spark = Sparkline(cpu_right, width=240, height=44, color=Theme.CPU)
        self.ov_cpu_spark.pack(fill="x", pady=(8, 0))

        mem_card = card(grid, f"{METRIC_ICONS['memory']}  内存", Theme.MEM)
        mem_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0), pady=6)
        mem_row = tk.Frame(mem_card.body, bg=Theme.PANEL)
        mem_row.pack(fill="both", expand=True)
        self.ov_mem_ring = RingGauge(mem_row, size=120, color=Theme.MEM)
        self.ov_mem_ring.pack(side="left", padx=(0, 12))
        mem_right = tk.Frame(mem_row, bg=Theme.PANEL)
        mem_right.pack(side="left", fill="both", expand=True)
        tk.Label(
            mem_right, textvariable=self.var_mem_detail, bg=Theme.PANEL, fg=Theme.TEXT,
            font=FONT_MONO, justify="left", anchor="nw",
        ).pack(fill="x")
        self.ov_mem_stack = StackedBar(mem_right, width=240, height=12)
        self.ov_mem_stack.pack(fill="x", pady=(8, 4))
        tk.Label(
            mem_right, textvariable=self.var_mem_legend, bg=Theme.PANEL, fg=Theme.MUTED,
            font=FONT_TINY, anchor="w",
        ).pack(fill="x")

        net_card = card(grid, f"{METRIC_ICONS['network']}  网络", Theme.NET_DOWN)
        net_card.grid(row=1, column=0, sticky="nsew", padx=(0, 7), pady=6)
        rates = tk.Frame(net_card.body, bg=Theme.PANEL)
        rates.pack(fill="x")
        tk.Label(
            rates, textvariable=self.var_net_down, bg=Theme.PANEL, fg=Theme.NET_DOWN,
            font=FONT_BIG, anchor="w",
        ).pack(side="left", expand=True, fill="x")
        tk.Label(
            rates, textvariable=self.var_net_up, bg=Theme.PANEL, fg=Theme.NET_UP,
            font=FONT_BIG, anchor="w",
        ).pack(side="left", expand=True, fill="x")
        tk.Label(
            net_card.body, textvariable=self.var_net_iface, bg=Theme.PANEL, fg=Theme.MUTED,
            font=FONT_TINY, anchor="w",
        ).pack(fill="x", pady=(4, 6))
        self.ov_net_spark = DualSparkline(net_card.body, width=400, height=64)
        self.ov_net_spark.pack(fill="both", expand=True)

        disk_card = card(grid, f"{METRIC_ICONS['disk']}  硬盘", Theme.DISK)
        disk_card.grid(row=1, column=1, sticky="nsew", padx=(7, 0), pady=6)
        tk.Label(
            disk_card.body, textvariable=self.var_disk_name, bg=Theme.PANEL, fg=Theme.TEXT,
            font=FONT_BOLD, anchor="w",
        ).pack(fill="x")
        self.ov_disk_bar = UsageBar(disk_card.body, width=380, height=12, color=Theme.DISK)
        self.ov_disk_bar.pack(fill="x", pady=(8, 6))
        tk.Label(
            disk_card.body, textvariable=self.var_disk_text, bg=Theme.PANEL, fg=Theme.MUTED,
            font=FONT_MONO, anchor="w",
        ).pack(fill="x")
        io = tk.Frame(disk_card.body, bg=Theme.PANEL)
        io.pack(fill="x", pady=(12, 0))
        tk.Label(
            io, textvariable=self.var_disk_read, bg=Theme.PANEL, fg=Theme.DISK,
            font=FONT, anchor="w",
        ).pack(side="left", expand=True, fill="x")
        tk.Label(
            io, textvariable=self.var_disk_write, bg=Theme.PANEL, fg=Theme.WARN,
            font=FONT, anchor="w",
        ).pack(side="left", expand=True, fill="x")

        proc_card = card(body, "占用最高进程")
        proc_card.pack(fill="both", expand=True, pady=(8, 0))
        # Plain Text widget — more reliable than ttk.Treeview on macOS + dark theme.
        self.ov_proc = tk.Text(
            proc_card.body, height=8, bg=Theme.PANEL_2, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat", font=FONT_MONO,
            highlightthickness=0, padx=10, pady=8, wrap="none",
        )
        self.ov_proc.pack(fill="both", expand=True)
        self.ov_proc.configure(state="disabled")
        return page

    def _build_cpu(self, parent: tk.Frame) -> tk.Frame:
        page = tk.Frame(parent, bg=Theme.BG)
        body = tk.Frame(page, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        top = tk.Frame(body, bg=Theme.BG)
        top.pack(fill="x")
        for i in range(3):
            top.columnconfigure(i, weight=1, uniform="c")

        c1 = card(top, "总占用", Theme.CPU)
        c1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.cpu_ring = RingGauge(c1.body, size=160, color=Theme.CPU)
        self.cpu_ring.pack(pady=8)

        c2 = card(top, "组成", Theme.WARN)
        c2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.var_cpu_user = tk.StringVar(value="")
        self.var_cpu_sys = tk.StringVar(value="")
        self.var_cpu_idle = tk.StringVar(value="")
        self.var_cpu_load = tk.StringVar(value="")
        for var, color in (
            (self.var_cpu_user, Theme.CPU),
            (self.var_cpu_sys, Theme.WARN),
            (self.var_cpu_idle, Theme.ACCENT),
            (self.var_cpu_load, Theme.MUTED),
        ):
            tk.Label(
                c2.body, textvariable=var, bg=Theme.PANEL, fg=color,
                font=("Helvetica Neue", 15), anchor="w",
            ).pack(fill="x", pady=8)

        c3 = card(top, "近 90 秒趋势", Theme.CPU)
        c3.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.cpu_spark = Sparkline(c3.body, width=300, height=150, color=Theme.CPU)
        self.cpu_spark.pack(fill="both", expand=True)

        cores = card(body, "每核心占用")
        cores.pack(fill="both", expand=True, pady=8)
        self.core_frame = tk.Frame(cores.body, bg=Theme.PANEL)
        self.core_frame.pack(fill="both", expand=True)
        return page

    def _build_memory(self, parent: tk.Frame) -> tk.Frame:
        page = tk.Frame(parent, bg=Theme.BG)
        body = tk.Frame(page, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        top = tk.Frame(body, bg=Theme.BG)
        top.pack(fill="x")
        for i in range(3):
            top.columnconfigure(i, weight=1, uniform="m")

        c1 = card(top, "内存压力", Theme.MEM)
        c1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.mem_ring = RingGauge(c1.body, size=160, color=Theme.MEM)
        self.mem_ring.pack(pady=8)

        c2 = card(top, "容量", Theme.MEM)
        c2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.mem_line_vars = [tk.StringVar(value="") for _ in range(4)]
        for var in self.mem_line_vars:
            tk.Label(
                c2.body, textvariable=var, bg=Theme.PANEL, fg=Theme.TEXT,
                font=("Helvetica Neue", 14), anchor="w",
            ).pack(fill="x", pady=8)

        c3 = card(top, "趋势", Theme.MEM)
        c3.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.mem_spark = Sparkline(c3.body, width=300, height=150, color=Theme.MEM)
        self.mem_spark.pack(fill="both", expand=True)

        detail = card(body, "细分构成")
        detail.pack(fill="x", pady=8)
        self.mem_used_bar = StackedBar(detail.body, width=800, height=16)
        self.mem_used_bar.pack(fill="x", pady=6)
        self.var_mem_breakdown = tk.StringVar(value="")
        tk.Label(
            detail.body, textvariable=self.var_mem_breakdown, bg=Theme.PANEL, fg=Theme.MUTED,
            font=FONT_MONO, anchor="w",
        ).pack(fill="x")
        return page

    def _build_disk(self, parent: tk.Frame) -> tk.Frame:
        page = tk.Frame(parent, bg=Theme.BG)
        body = tk.Frame(page, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        stats = tk.Frame(body, bg=Theme.BG)
        stats.pack(fill="x")
        for i in range(2):
            stats.columnconfigure(i, weight=1, uniform="d")
        self.disk_stat_vars = []
        for i, (title, color) in enumerate((("读取速度", Theme.DISK), ("写入速度", Theme.WARN))):
            c = card(stats, title, color)
            c.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            var = tk.StringVar(value="—")
            tk.Label(c.body, textvariable=var, bg=Theme.PANEL, fg=color, font=FONT_BIG, anchor="w").pack(fill="x")
            self.disk_stat_vars.append(var)

        hist = card(body, "磁盘吞吐")
        hist.pack(fill="x", pady=8)
        self.disk_read_spark = Sparkline(hist.body, width=900, height=64, color=Theme.DISK)
        self.disk_read_spark.pack(fill="x")
        self.disk_write_spark = Sparkline(hist.body, width=900, height=64, color=Theme.WARN)
        self.disk_write_spark.pack(fill="x", pady=(6, 0))

        vols = card(body, "存储卷")
        vols.pack(fill="both", expand=True, pady=8)
        self.disk_vol_frame = tk.Frame(vols.body, bg=Theme.PANEL)
        self.disk_vol_frame.pack(fill="both", expand=True)
        return page

    def _build_network(self, parent: tk.Frame) -> tk.Frame:
        page = tk.Frame(parent, bg=Theme.BG)
        body = tk.Frame(page, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        top = tk.Frame(body, bg=Theme.BG)
        top.pack(fill="x")
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)
        self.var_net_down_big = tk.StringVar(value="—")
        self.var_net_up_big = tk.StringVar(value="—")
        down = card(top, "下载", Theme.NET_DOWN)
        down.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=5)
        tk.Label(
            down.body, textvariable=self.var_net_down_big, bg=Theme.PANEL, fg=Theme.NET_DOWN,
            font=("Helvetica Neue", 30, "bold"), anchor="w",
        ).pack(fill="x")
        self.net_down_spark = Sparkline(down.body, width=420, height=84, color=Theme.NET_DOWN)
        self.net_down_spark.pack(fill="x", pady=(8, 0))

        up = card(top, "上传", Theme.NET_UP)
        up.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=5)
        tk.Label(
            up.body, textvariable=self.var_net_up_big, bg=Theme.PANEL, fg=Theme.NET_UP,
            font=("Helvetica Neue", 30, "bold"), anchor="w",
        ).pack(fill="x")
        self.net_up_spark = Sparkline(up.body, width=420, height=84, color=Theme.NET_UP)
        self.net_up_spark.pack(fill="x", pady=(8, 0))

        ifaces = card(body, "活跃网卡")
        ifaces.pack(fill="both", expand=True, pady=8)
        self.net_list = tk.Text(
            ifaces.body, height=12, bg=Theme.PANEL_2, fg=Theme.TEXT,
            relief="flat", font=FONT_MONO, highlightthickness=0, padx=10, pady=8, wrap="none",
        )
        self.net_list.pack(fill="both", expand=True)
        self.net_list.configure(state="disabled")
        return page

    def _build_processes(self, parent: tk.Frame) -> tk.Frame:
        page = tk.Frame(parent, bg=Theme.BG)
        bar = tk.Frame(page, bg=Theme.BG)
        bar.pack(fill="x", padx=16, pady=(12, 8))
        tk.Label(bar, text="搜索", bg=Theme.BG, fg=Theme.MUTED, font=FONT).pack(side="left")
        self.proc_query = tk.StringVar()
        entry = tk.Entry(
            bar, textvariable=self.proc_query, bg=Theme.PANEL_2, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat", font=FONT, width=28,
        )
        entry.pack(side="left", padx=10, ipady=6, ipadx=8)
        entry.bind("<KeyRelease>", lambda e: self._render_processes())
        self.proc_sort = tk.StringVar(value="cpu")
        for label, val in (("按 CPU", "cpu"), ("按内存", "mem")):
            tk.Radiobutton(
                bar, text=label, variable=self.proc_sort, value=val,
                command=self._render_processes, bg=Theme.BG, fg=Theme.TEXT,
                selectcolor=Theme.PANEL_2, activebackground=Theme.BG, font=FONT, highlightthickness=0,
            ).pack(side="right", padx=4)

        wrap = tk.Frame(page, bg=Theme.BG)
        wrap.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        header = tk.Label(
            wrap,
            text=f"{'PID':>7}  {'进程':<28}  {'CPU':>7}  {'内存':>10}  {'线程':>5}  状态",
            bg=Theme.PANEL_2, fg=Theme.MUTED, font=FONT_MONO, anchor="w", padx=10, pady=6,
        )
        header.pack(fill="x")
        self.proc_list = tk.Text(
            wrap, height=22, bg=Theme.PANEL, fg=Theme.TEXT,
            relief="flat", font=FONT_MONO, highlightthickness=0, padx=10, pady=8, wrap="none",
        )
        self.proc_list.pack(fill="both", expand=True)
        self.proc_list.configure(state="disabled")
        return page

    # ---------- update loop ----------

    def _tick(self) -> None:
        if not self.paused:
            try:
                self._tick_count += 1
                include_procs = self._tick_count % 2 == 0 or self.page == "processes"
                self.snap = self.collector.sample(include_processes=include_procs)
                self._render()
            except Exception as exc:  # noqa: BLE001
                self.var_status.set(f"采集错误: {exc}")
                _log("tick failed:\n" + traceback.format_exc())
        self.after(self.refresh_ms, self._tick)

    def _set_text(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _render(self) -> None:
        s = self.snap
        if not s:
            return

        def section(name: str, fn) -> None:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                self.var_status.set(f"{name}显示异常: {exc}")
                _log(f"{name} failed: {exc}\n{traceback.format_exc()}")

        user, system, idle = s.cpu_times
        active_net = _active_ifaces(s.net_interfaces)
        top_iface = active_net[0] if active_net else None
        total = max(s.mem_total, 1)

        def sidebar() -> None:
            self.var_host.set(s.hostname or "本机")
            self.var_meta.set(f"{s.chip}\n{s.platform}")
            self.var_ov_header.set(s.hostname or "本机")
            self.var_ov_sub.set(
                f"{s.platform}  ·  {s.logical_cores} 核  ·  负载 {s.load_avg[0]:.2f}  ·  已运行 {format_uptime(s.uptime)}"
            )

        def hero() -> None:
            self.hero_cpu.configure(text=_pct(s.cpu_percent, 0))
            self.hero_cpu_sub.configure(text=f"用户 {_pct(user, 0)}  系统 {_pct(system, 0)}")
            self.hero_mem.configure(text=_pct(s.mem_percent, 0))
            self.hero_mem_sub.configure(text=f"{format_bytes(s.mem_used)} / {format_bytes(s.mem_total)}")
            self.hero_net.configure(text=f"{METRIC_ICONS['down']}{format_net_m(s.net_down_bps)}")
            self.hero_net_sub.configure(text=f"{METRIC_ICONS['up']} {format_net_m(s.net_up_bps)}")
            self.hero_disk.configure(text=_pct(s.primary_disk_percent, 0))
            self.hero_disk_sub.configure(
                text=f"{format_bytes(s.primary_disk_used)} / {format_bytes(s.primary_disk_total)}"
                if s.primary_disk_total else "—"
            )
            self.var_strip_cpu.set(_pct(s.cpu_percent, 0))
            self.var_strip_mem.set(_pct(s.mem_percent, 0))
            self.var_strip_net.set(format_bps(s.net_down_bps))
            self.var_strip_disk.set(_pct(s.primary_disk_percent, 0))
            self.var_status.set(
                f"CPU {_pct(s.cpu_percent)}   "
                f"内存 {_pct(s.mem_percent)} ({format_bytes(s.mem_used)}/{format_bytes(s.mem_total)})   "
                f"↓{format_bps(s.net_down_bps)} ↑{format_bps(s.net_up_bps)}   "
                f"磁盘 {_pct(s.primary_disk_percent)}   "
                f"读 {format_bps(s.disk_read_bps)} 写 {format_bps(s.disk_write_bps)}"
            )

        def overview() -> None:
            self.ov_cpu_ring.set(s.cpu_percent, _pct(s.cpu_percent, 0), "总占用")
            self.var_cpu_detail.set(
                f"用户   {_pct(user)}\n系统   {_pct(system)}\n空闲   {_pct(idle)}\n负载   {s.load_avg[0]:.2f} / {s.load_avg[1]:.2f}"
            )
            self.ov_cpu_spark.set_values(list(self.collector.cpu_history), Theme.CPU)

            self.ov_mem_ring.set(s.mem_percent, _pct(s.mem_percent, 0), format_bytes(s.mem_used))
            self.var_mem_detail.set(
                f"已用   {format_bytes(s.mem_used)}\n可用   {format_bytes(s.mem_available)}\n总计   {format_bytes(s.mem_total)}"
            )
            self.ov_mem_stack.set_segments([
                (s.mem_wired / total, Theme.WARN),
                (s.mem_active / total, Theme.MEM),
                (s.mem_compressed / total, Theme.DISK),
                (max(0, s.mem_available) / total, Theme.TRACK),
            ])
            self.var_mem_legend.set(
                f"Wired {format_bytes(s.mem_wired)}   Active {format_bytes(s.mem_active)}   压缩 {format_bytes(s.mem_compressed)}"
            )

            self.var_net_down.set(f"↓  {format_bps(s.net_down_bps)}")
            self.var_net_up.set(f"↑  {format_bps(s.net_up_bps)}")
            if top_iface:
                self.var_net_iface.set(
                    f"主接口 {top_iface.get('display') or top_iface['name']}  ·  {top_iface.get('ip') or '无 IP'}"
                )
            else:
                self.var_net_iface.set("暂无活跃网卡")
            self.ov_net_spark.set_values(
                list(self.collector.net_down_history),
                list(self.collector.net_up_history),
                Theme.NET_DOWN,
                Theme.NET_UP,
            )

            self.var_disk_name.set(s.primary_disk_label or "主磁盘")
            self.ov_disk_bar.set(
                s.primary_disk_percent,
                Theme.DANGER if s.primary_disk_percent > 90 else Theme.DISK,
            )
            if s.primary_disk_total:
                free = max(0, s.primary_disk_total - s.primary_disk_used)
                self.var_disk_text.set(
                    f"{format_bytes(s.primary_disk_used)} / {format_bytes(s.primary_disk_total)}"
                    f"   ·   可用 {format_bytes(free)}   ·   {_pct(s.primary_disk_percent)}"
                )
            else:
                self.var_disk_text.set("—")
            self.var_disk_read.set(f"读  {format_bps(s.disk_read_bps)}")
            self.var_disk_write.set(f"写  {format_bps(s.disk_write_bps)}")

            lines = [f"{'PID':>7}  {'进程':<32}  {'CPU':>7}  {'内存':>10}"]
            for p in s.processes[:8]:
                name = (p["name"] or "")[:32]
                lines.append(
                    f"{p['pid']:>7}  {name:<32}  {_pct(p['cpu']):>7}  {format_bytes(p['memory']):>10}"
                )
            self._set_text(self.ov_proc, "\n".join(lines) if len(lines) > 1 else "暂无进程数据")

        def details() -> None:
            self.cpu_ring.set(s.cpu_percent, _pct(s.cpu_percent), "全部核心")
            self.var_cpu_user.set(f"用户态    {_pct(user)}")
            self.var_cpu_sys.set(f"系统态    {_pct(system)}")
            self.var_cpu_idle.set(f"空闲      {_pct(idle)}")
            self.var_cpu_load.set(f"负载      {s.load_avg[0]:.2f}  {s.load_avg[1]:.2f}  {s.load_avg[2]:.2f}")
            self.cpu_spark.set_values(list(self.collector.cpu_history), Theme.CPU)
            self._render_cores(s.cpu_per_core)

            self.mem_ring.set(s.mem_percent, _pct(s.mem_percent), "压力")
            self.mem_line_vars[0].set(f"物理内存    {format_bytes(s.mem_total)}")
            self.mem_line_vars[1].set(f"已用        {format_bytes(s.mem_used)}   ({_pct(s.mem_percent)})")
            self.mem_line_vars[2].set(f"可用        {format_bytes(s.mem_available)}")
            self.mem_line_vars[3].set(f"交换        {format_bytes(s.swap_used)} / {format_bytes(s.swap_total)}")
            self.mem_spark.set_values(list(self.collector.mem_history), Theme.MEM)
            self.mem_used_bar.set_segments([
                (s.mem_wired / total, Theme.WARN),
                (s.mem_active / total, Theme.MEM),
                (s.mem_compressed / total, Theme.DISK),
                (max(0, s.mem_available) / total, Theme.TRACK),
            ])
            self.var_mem_breakdown.set(
                f"Wired {format_bytes(s.mem_wired)}   "
                f"Active {format_bytes(s.mem_active)}   "
                f"压缩 {format_bytes(s.mem_compressed)}   "
                f"缓存约 {format_bytes(s.mem_cached)}"
            )

            self.disk_stat_vars[0].set(format_bps(s.disk_read_bps))
            self.disk_stat_vars[1].set(format_bps(s.disk_write_bps))
            self.disk_read_spark.set_values(list(self.collector.disk_read_history), Theme.DISK)
            self.disk_write_spark.set_values(list(self.collector.disk_write_history), Theme.WARN)
            self._render_volumes(s.disk_partitions)

            self.var_net_down_big.set(format_bps(s.net_down_bps))
            self.var_net_up_big.set(format_bps(s.net_up_bps))
            self.net_down_spark.set_values(list(self.collector.net_down_history), Theme.NET_DOWN)
            self.net_up_spark.set_values(list(self.collector.net_up_history), Theme.NET_UP)
            net_lines = [f"{'接口':<18} {'IP':<16} {'下行':>10} {'上行':>10} {'累计↓':>10} {'累计↑':>10}"]
            for i in active_net:
                net_lines.append(
                    f"{(i.get('display') or i['name'])[:18]:<18} "
                    f"{(i.get('ip') or '—')[:16]:<16} "
                    f"{format_bps(i.get('down_bps', 0)):>10} "
                    f"{format_bps(i.get('up_bps', 0)):>10} "
                    f"{format_bytes(i['bytes_recv']):>10} "
                    f"{format_bytes(i['bytes_sent']):>10}"
                )
            self._set_text(self.net_list, "\n".join(net_lines) if len(net_lines) > 1 else "暂无活跃网卡")
            self._render_processes()

        def menubar() -> None:
            if getattr(self, "menubar", None):
                self.menubar.update(s)

        section("基础信息", sidebar)
        section("顶部指标", hero)
        section("总览卡片", overview)
        section("详情页", details)
        section("菜单栏", menubar)
        try:
            self.update_idletasks()
        except tk.TclError:
            pass

    def _render_cores(self, cores: List[float]) -> None:
        if len(self.core_bars) != len(cores):
            for child in self.core_frame.winfo_children():
                child.destroy()
            self.core_bars = []
            cols = 4
            for idx, _ in enumerate(cores):
                cell = tk.Frame(self.core_frame, bg=Theme.PANEL_2, padx=10, pady=10)
                cell.grid(row=idx // cols, column=idx % cols, sticky="nsew", padx=4, pady=4)
                tk.Label(cell, text=f"核心 {idx}", bg=Theme.PANEL_2, fg=Theme.MUTED, font=FONT_TINY).pack(anchor="w")
                val = tk.Label(cell, text="0%", bg=Theme.PANEL_2, fg=Theme.TEXT, font=FONT_MONO)
                val.pack(anchor="e")
                bar = UsageBar(cell, width=160, height=8, color=Theme.CPU)
                bar.pack(fill="x", pady=(6, 0))
                self.core_bars.append((val, bar))
            for c in range(4):
                self.core_frame.columnconfigure(c, weight=1)
        for (val, bar), pct in zip(self.core_bars, cores):
            color = Theme.DANGER if pct > 85 else Theme.WARN if pct > 60 else Theme.CPU
            val.configure(text=_pct(pct, 0))
            bar.set(pct, color)

    def _render_volumes(self, partitions: List[dict]) -> None:
        has_container = any(p.get("is_container") for p in partitions)
        shown = []
        for p in partitions:
            if has_container and (p.get("is_root") or p.get("is_data")):
                continue
            shown.append(p)

        if len(self.disk_vol_widgets) != len(shown):
            for child in self.disk_vol_frame.winfo_children():
                child.destroy()
            self.disk_vol_widgets = []
            for _part in shown:
                row = tk.Frame(self.disk_vol_frame, bg=Theme.PANEL, pady=10)
                row.pack(fill="x")
                title_var = tk.StringVar(value="")
                detail_var = tk.StringVar(value="")
                tk.Label(row, textvariable=title_var, bg=Theme.PANEL, fg=Theme.TEXT, font=FONT_BOLD, anchor="w").pack(fill="x")
                bar = UsageBar(row, width=700, height=11, color=Theme.DISK)
                bar.pack(fill="x", pady=6)
                tk.Label(row, textvariable=detail_var, bg=Theme.PANEL, fg=Theme.MUTED, font=FONT_MONO, anchor="w").pack(fill="x")
                self.disk_vol_widgets.append({"bar": bar, "detail": detail_var, "title": title_var})

        for widgets, part in zip(self.disk_vol_widgets, shown):
            color = Theme.DANGER if part["percent"] > 90 else Theme.DISK
            label = part.get("label") or part["mount"]
            tag = "整盘" if part.get("is_container") else part["mount"]
            widgets["title"].set(f"{label}    {tag}")
            widgets["bar"].set(part["percent"], color)
            widgets["detail"].set(
                f"{format_bytes(part['used'])} / {format_bytes(part['total'])}"
                f"    可用 {format_bytes(part['free'])}"
                f"    {_pct(part['percent'])}"
            )

    def _render_processes(self) -> None:
        s = self.snap
        if not s:
            return
        q = self.proc_query.get().strip().lower()
        items = list(s.processes)
        if q:
            items = [p for p in items if q in p["name"].lower() or q in str(p["pid"])]
        if self.proc_sort.get() == "mem":
            items.sort(key=lambda p: p["memory"], reverse=True)
        else:
            items.sort(key=lambda p: p["cpu"], reverse=True)
        lines = []
        for p in items[:40]:
            name = (p["name"] or "")[:28]
            lines.append(
                f"{p['pid']:>7}  {name:<28}  {_pct(p['cpu']):>7}  {format_bytes(p['memory']):>10}  "
                f"{p['threads']:>5}  {_status_cn(p['status'])}"
            )
        self._set_text(self.proc_list, "\n".join(lines) if lines else "暂无匹配进程")


def run_dashboard_tk() -> None:
    """Tk fallback dashboard (used if WebKit native UI unavailable)."""
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text("", encoding="utf-8")
    except Exception:
        pass

    try:
        _log("starting tk dashboard")
        app = SupToolsApp(enable_menubar=True)
        app.protocol("WM_DELETE_WINDOW", app.hide_panel)
        app.after(50, app._safe_render)
        app.after(300, app._safe_render)
        app.mainloop()
        _log("mainloop exited")
    except Exception:
        _log("fatal:\n" + traceback.format_exc())
        raise


def run_dashboard() -> None:
    """Preferred entry: native WebKit UI, Tk fallback."""
    from .native_app import run as run_native_app

    run_native_app()


def run() -> None:
    """Default entry used by .app launcher."""
    run_dashboard()
