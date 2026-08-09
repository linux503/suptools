"""Reusable Tk drawing widgets — polished SupTools UI."""

from __future__ import annotations

import tkinter as tk
from typing import List, Optional, Sequence, Tuple


class Theme:
    BG = "#0B0E14"
    PANEL = "#141A22"
    PANEL_2 = "#1A222D"
    BORDER = "#2A3442"
    TEXT = "#F3F6FA"
    MUTED = "#8E9AAB"
    ACCENT = "#2DD4BF"
    CPU = "#F59E0B"
    MEM = "#38BDF8"
    DISK = "#A78BFA"
    NET_DOWN = "#34D399"
    NET_UP = "#FB7185"
    WARN = "#FBBF24"
    DANGER = "#F87171"
    SIDEBAR = "#070A10"
    SELECT = "#1E2A3A"
    TRACK = "#243041"


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _dim(hex_color: str, factor: float = 0.28) -> str:
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"


class RingGauge(tk.Canvas):
    def __init__(self, master, size=132, color=Theme.ACCENT, **kwargs):
        super().__init__(master, width=size, height=size, bg=Theme.PANEL, highlightthickness=0, **kwargs)
        self.size = size
        self.color = color
        pad = 12
        self.create_oval(pad, pad, size - pad, size - pad, outline=Theme.TRACK, width=11)
        self._arc = self.create_arc(
            pad, pad, size - pad, size - pad,
            start=90, extent=0, style="arc", outline=color, width=11,
        )
        self._label = self.create_text(
            size / 2, size / 2 - 6, text="0%", fill=Theme.TEXT,
            font=("Helvetica Neue", 24, "bold"),
        )
        self._detail = self.create_text(
            size / 2, size / 2 + 18, text="", fill=Theme.MUTED,
            font=("Helvetica Neue", 10),
        )

    def set(self, percent: float, label: Optional[str] = None, detail: str = "") -> None:
        p = _clamp(percent)
        color = Theme.DANGER if p >= 90 else Theme.WARN if p >= 75 else self.color
        self.itemconfigure(self._arc, extent=-p * 3.6, outline=color)
        self.itemconfigure(self._label, text=label if label is not None else f"{p:.0f}%")
        self.itemconfigure(self._detail, text=detail)


class Sparkline(tk.Canvas):
    def __init__(self, master, width=280, height=56, color=Theme.ACCENT, **kwargs):
        super().__init__(master, width=width, height=height, bg=Theme.PANEL, highlightthickness=0, **kwargs)
        self.w, self.h, self.color = width, height, color
        self._values: List[float] = []
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        if event.width > 20:
            self.w = event.width
        if event.height > 10:
            self.h = event.height
        if self._values:
            self.set_values(self._values, self.color)

    def set_values(self, values: Sequence[float], color: Optional[str] = None) -> None:
        if color:
            self.color = color
        self._values = list(values)
        self.delete("all")
        if len(self._values) < 2:
            return
        vmax = max(max(self._values), 0.001)
        pts: List[float] = []
        n = len(self._values)
        for i, v in enumerate(self._values):
            x = i * max(self.w - 2, 1) / (n - 1)
            y = self.h - 3 - (v / vmax) * max(self.h - 8, 1)
            pts.extend([x, y])
        self.create_polygon(*([0, self.h] + pts + [self.w, self.h]), fill=_dim(self.color, 0.32), outline="")
        self.create_line(*pts, fill=self.color, width=2, smooth=True)


class DualSparkline(tk.Canvas):
    def __init__(self, master, width=280, height=64, **kwargs):
        super().__init__(master, width=width, height=height, bg=Theme.PANEL, highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self._a: List[float] = []
        self._b: List[float] = []
        self._ca, self._cb = Theme.NET_DOWN, Theme.NET_UP
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        if event.width > 20:
            self.w = event.width
        if event.height > 10:
            self.h = event.height
        self.redraw()

    def set_values(self, a, b, color_a=Theme.NET_DOWN, color_b=Theme.NET_UP) -> None:
        self._a, self._b = list(a), list(b)
        self._ca, self._cb = color_a, color_b
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        vmax = max([0.001] + self._a + self._b)
        for values, color in ((self._a, self._ca), (self._b, self._cb)):
            if len(values) < 2:
                continue
            pts: List[float] = []
            n = len(values)
            for i, v in enumerate(values):
                x = i * max(self.w - 2, 1) / (n - 1)
                y = self.h - 3 - (v / vmax) * max(self.h - 8, 1)
                pts.extend([x, y])
            self.create_line(*pts, fill=color, width=2, smooth=True)


class UsageBar(tk.Canvas):
    def __init__(self, master, width=220, height=10, color=Theme.ACCENT, **kwargs):
        super().__init__(master, width=width, height=height, bg=Theme.PANEL, highlightthickness=0, **kwargs)
        self.w, self.h, self.color = width, height, color
        self._track = self.create_rectangle(0, 0, width, height, fill=Theme.TRACK, outline="")
        self._bar = self.create_rectangle(0, 0, 0, height, fill=color, outline="")
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        if event.width > 10:
            self.w = event.width
            self.coords(self._track, 0, 0, self.w, self.h)

    def set(self, percent: float, color: Optional[str] = None) -> None:
        width = max(int(self.winfo_width() or self.w), 40)
        self.w = width
        self.coords(self._track, 0, 0, self.w, self.h)
        p = _clamp(percent) / 100.0
        if color:
            self.color = color
            self.itemconfigure(self._bar, fill=color)
        self.coords(self._bar, 0, 0, max(4, self.w * p), self.h)


class StackedBar(tk.Canvas):
    """Multi-segment bar for memory breakdown."""

    def __init__(self, master, width=400, height=14, **kwargs):
        super().__init__(master, width=width, height=height, bg=Theme.PANEL, highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self._track = self.create_rectangle(0, 0, width, height, fill=Theme.TRACK, outline="")
        self._segs: List[int] = []
        self.bind("<Configure>", lambda e: setattr(self, "w", e.width) if e.width > 10 else None)

    def set_segments(self, parts: Sequence[Tuple[float, str]]) -> None:
        """parts: list of (fraction 0-1, color)."""
        self.delete("seg")
        width = max(int(self.winfo_width() or self.w), 40)
        height = max(int(self.winfo_height() or self.h), 8)
        self.w, self.h = width, height
        self.coords(self._track, 0, 0, self.w, self.h)
        x = 0.0
        total = sum(max(0.0, p) for p, _ in parts) or 1.0
        for frac, color in parts:
            w = self.w * (max(0.0, frac) / total)
            if w >= 1:
                self.create_rectangle(x, 0, x + w, self.h, fill=color, outline="", tags="seg")
            x += w


def card(parent, title: str, accent: Optional[str] = None) -> tk.Frame:
    outer = tk.Frame(parent, bg=accent or Theme.BORDER, padx=1, pady=1)
    inner = tk.Frame(outer, bg=Theme.PANEL, padx=14, pady=12)
    inner.pack(fill="both", expand=True)
    head = tk.Frame(inner, bg=Theme.PANEL)
    head.pack(fill="x", pady=(0, 8))
    if accent:
        tk.Frame(head, bg=accent, width=3, height=12).pack(side="left", padx=(0, 8))
    tk.Label(
        head, text=title, bg=Theme.PANEL, fg=Theme.MUTED,
        font=("Helvetica Neue", 11, "bold"), anchor="w",
    ).pack(side="left", fill="x")
    body = tk.Frame(inner, bg=Theme.PANEL)
    body.pack(fill="both", expand=True)
    outer.body = body  # type: ignore[attr-defined]
    outer.head = head  # type: ignore[attr-defined]
    return outer


def metric_tile(parent, title: str, color: str) -> Tuple[tk.Frame, tk.Label, tk.Label]:
    wrap = tk.Frame(parent, bg=color, padx=1, pady=1)
    box = tk.Frame(wrap, bg=Theme.PANEL_2, padx=14, pady=12)
    box.pack(fill="both", expand=True)
    tk.Label(box, text=title, bg=Theme.PANEL_2, fg=Theme.MUTED, font=("Helvetica Neue", 11), anchor="w").pack(fill="x")
    value = tk.Label(box, text="—", bg=Theme.PANEL_2, fg=color, font=("Helvetica Neue", 26, "bold"), anchor="w")
    value.pack(fill="x", pady=(4, 0))
    sub = tk.Label(box, text="", bg=Theme.PANEL_2, fg=Theme.MUTED, font=("Menlo", 11), anchor="w")
    sub.pack(fill="x", pady=(2, 0))
    return wrap, value, sub
