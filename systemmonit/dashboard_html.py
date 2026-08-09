"""Embedded HTML dashboard — native macOS / iOS flat style."""

from __future__ import annotations

import base64
import io
from pathlib import Path


def _brand_logo_data_uri() -> str:
    """Load app icon as a compact data URI for the sidebar brand."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "SupToolsIcon.png",  # packaged: …/Resources/SupToolsIcon.png
        here.parents[1] / "Resources" / "SupToolsIcon.png",  # source tree
        here.parents[1] / "assets" / "SupToolsIcon.png",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            from PIL import Image

            img = Image.open(path).convert("RGBA").resize((128, 128), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        except Exception:
            try:
                return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
            except Exception:
                continue
    # Inline teal gauge fallback if icon file missing
    return (
        "data:image/svg+xml,"
        "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 128 128'%3E"
        "%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='0' y2='1'%3E"
        "%3Cstop stop-color='%2324d2ba'/%3E%3Cstop offset='1' stop-color='%230c588e'/%3E"
        "%3C/linearGradient%3E%3C/defs%3E"
        "%3Crect width='128' height='128' rx='28' fill='url(%23g)'/%3E"
        "%3Cpath d='M28 70a36 36 0 0 1 72 0' fill='none' stroke='white' stroke-width='8' "
        "stroke-linecap='round'/%3E"
        "%3Ccircle cx='64' cy='70' r='6' fill='white'/%3E"
        "%3Cpath d='M64 70 L92 46' stroke='white' stroke-width='6' stroke-linecap='round'/%3E"
        "%3Cpath d='M52 78 L70 88 L54 98 L72 110' fill='none' stroke='white' stroke-width='8' "
        "stroke-linecap='round' stroke-linejoin='round'/%3E"
        "%3C/svg%3E"
    )


_BRAND_LOGO_SRC = _brand_logo_data_uri()

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>SupTools</title>
<style>
  :root, [data-theme="dark"] {
    --bg: transparent;
    --surface-rgb: 12, 12, 14;
    --surface2-rgb: 22, 22, 24;
    --wash-rgb: 0, 0, 0;
    --sidebar-rgb: 0, 0, 0;
    --toolbar-rgb: 0, 0, 0;
    --btn-rgb: 255, 255, 255;
    --ring-rgb: 0, 0, 0;
    --glass-a: 0.62;
    --glass-a2: 0.55;
    --wash-a: 0.72;
    --sidebar-a: 0.55;
    --toolbar-a: 0.48;
    --btn-a: 0.08;
    --ring-a: 0.78;
    --bg-wash: rgba(var(--wash-rgb), var(--wash-a));
    --grouped: rgba(var(--surface-rgb), var(--glass-a));
    --grouped2: rgba(var(--surface2-rgb), var(--glass-a2));
    --fill: rgba(255,255,255,0.08);
    --sep: rgba(255,255,255,0.08);
    --glass-edge: rgba(255,255,255,0.10);
    --text: #f2f2f2;
    --text2: #8e8e93;
    --accent: #64d2ff;
    --tint: #0a84ff;
    --cpu: #ffd60a;
    --mem: #64d2ff;
    --disk: #30d158;
    --down: #30d158;
    --up: #ff453a;
    --warn: #ffd60a;
    --danger: #ff453a;
    --sidebar: rgba(var(--sidebar-rgb), var(--sidebar-a));
    --select: rgba(255,255,255,0.08);
    --track: rgba(255,255,255,0.10);
    --toolbar: rgba(var(--toolbar-rgb), var(--toolbar-a));
    --btn-bg: rgba(var(--btn-rgb), var(--btn-a));
    --btn-primary: #0a84ff;
    --btn-primary-text: #fff;
    --ring-hole: rgba(var(--ring-rgb), var(--ring-a));
    --nav-active: #0a84ff;
    --shadow: 0 14px 40px rgba(0,0,0,0.55);
    --glass-blur: blur(32px) saturate(160%);
  }
  [data-theme="light"] {
    --bg: transparent;
    --surface-rgb: 255, 255, 255;
    --surface2-rgb: 255, 255, 255;
    --wash-rgb: 242, 244, 248;
    --sidebar-rgb: 255, 255, 255;
    --toolbar-rgb: 255, 255, 255;
    --btn-rgb: 255, 255, 255;
    --ring-rgb: 255, 255, 255;
    --glass-a: 0.58;
    --glass-a2: 0.40;
    --wash-a: 0.42;
    --sidebar-a: 0.36;
    --toolbar-a: 0.48;
    --btn-a: 0.62;
    --ring-a: 0.78;
    --bg-wash: rgba(var(--wash-rgb), var(--wash-a));
    --grouped: rgba(var(--surface-rgb), var(--glass-a));
    --grouped2: rgba(var(--surface2-rgb), var(--glass-a2));
    --fill: rgba(0,0,0,0.05);
    --sep: rgba(60,60,67,0.10);
    --glass-edge: rgba(255,255,255,0.72);
    --text: #1c1c1e;
    --text2: #6c6c70;
    --accent: #007aff;
    --tint: #007aff;
    --cpu: #ff9500;
    --mem: #007aff;
    --disk: #34c759;
    --down: #34c759;
    --up: #ff3b30;
    --warn: #ff9500;
    --danger: #ff3b30;
    --sidebar: rgba(var(--sidebar-rgb), var(--sidebar-a));
    --select: rgba(255,255,255,0.55);
    --track: rgba(0,0,0,0.06);
    --toolbar: rgba(var(--toolbar-rgb), var(--toolbar-a));
    --btn-bg: rgba(var(--btn-rgb), var(--btn-a));
    --btn-primary: #007aff;
    --btn-primary-text: #fff;
    --ring-hole: rgba(var(--ring-rgb), var(--ring-a));
    --nav-active: #007aff;
    --shadow: 0 12px 32px rgba(30,40,70,0.10);
    --glass-blur: blur(28px) saturate(180%);
  }
  /* Glass transparency presets */
  body[data-glass="opaque"] {
    --glass-a: 0.94;
    --glass-a2: 0.88;
    --wash-a: 0.96;
    --sidebar-a: 0.94;
    --toolbar-a: 0.92;
    --btn-a: 0.88;
    --ring-a: 0.96;
    --glass-blur: blur(8px) saturate(120%);
    --shadow: 0 10px 28px rgba(0,0,0,0.18);
  }
  body[data-theme="light"][data-glass="opaque"] {
    --glass-a: 0.96;
    --glass-a2: 0.92;
    --wash-a: 0.98;
    --sidebar-a: 0.96;
    --toolbar-a: 0.94;
    --btn-a: 0.96;
    --ring-a: 0.98;
    --glass-edge: rgba(0,0,0,0.08);
  }
  body[data-glass="medium"] {
    /* defaults from theme */
  }
  body[data-glass="clear"] {
    --glass-a: 0.28;
    --glass-a2: 0.20;
    --wash-a: 0.18;
    --sidebar-a: 0.22;
    --toolbar-a: 0.24;
    --btn-a: 0.22;
    --ring-a: 0.42;
    --glass-blur: blur(42px) saturate(190%);
    --shadow: 0 16px 44px rgba(0,0,0,0.16);
  }
  body[data-theme="light"][data-glass="clear"] {
    --glass-a: 0.30;
    --glass-a2: 0.20;
    --wash-a: 0.16;
    --sidebar-a: 0.22;
    --toolbar-a: 0.26;
    --btn-a: 0.36;
    --ring-a: 0.45;
    --glass-edge: rgba(255,255,255,0.55);
  }
  body[data-theme="dark"][data-glass="clear"] {
    --glass-a: 0.30;
    --glass-a2: 0.22;
    --wash-a: 0.28;
    --sidebar-a: 0.26;
    --toolbar-a: 0.24;
    --btn-a: 0.12;
    --ring-a: 0.50;
  }
  * { box-sizing: border-box; }
  [hidden] { display: none !important; }
  html, body {
    margin: 0; height: 100%;
    background: transparent;
    color: var(--text);
    font: 13px/1.45 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }
  #app {
    display: grid;
    grid-template-columns: 220px 1fr;
    height: 100%;
    background:
      radial-gradient(120% 80% at 0% 0%, color-mix(in srgb, var(--tint) 12%, transparent), transparent 50%),
      radial-gradient(90% 70% at 100% 10%, color-mix(in srgb, var(--mem) 10%, transparent), transparent 45%),
      var(--bg-wash);
  }
  body[data-theme="dark"] #app {
    background:
      radial-gradient(90% 60% at 12% 0%, rgba(10,132,255,0.10), transparent 55%),
      radial-gradient(70% 50% at 100% 8%, rgba(100,210,255,0.06), transparent 50%),
      linear-gradient(180deg, rgba(0,0,0,0.88), rgba(0,0,0,0.94));
  }
  body[data-theme="dark"] .card,
  body[data-theme="dark"] .info-pill,
  body[data-theme="dark"] .settings-group,
  body[data-theme="dark"] .shot-action,
  body[data-theme="dark"] .shot-opts,
  body[data-theme="dark"] .shot-preview,
  body[data-theme="dark"] .tile {
    background: var(--grouped);
    border-color: rgba(255,255,255,0.09);
    box-shadow: var(--shadow), inset 0 0.5px 0 rgba(255,255,255,0.06);
  }
  body[data-theme="dark"] aside,
  body[data-theme="dark"] .toolbar,
  body[data-theme="dark"] .statusbar {
    background: var(--sidebar);
    border-color: rgba(255,255,255,0.08);
  }
  body[data-theme="dark"] .toolbar,
  body[data-theme="dark"] .statusbar {
    background: var(--toolbar);
  }
  body[data-theme="dark"] .nav button:hover {
    background: rgba(255,255,255,0.06);
  }
  body[data-theme="dark"] .nav button.active {
    background: rgba(10,132,255,0.92);
  }
  aside {
    background: var(--sidebar);
    border-right: 0.5px solid var(--glass-edge);
    padding: 52px 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    -webkit-app-region: drag;
    app-region: drag;
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 8px 18px;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.35px;
    color: var(--text);
    -webkit-app-region: drag;
    app-region: drag;
    cursor: default;
    min-width: 0;
  }
  .brand-logo {
    width: 36px;
    height: 36px;
    border-radius: 9px;
    flex: 0 0 auto;
    display: block;
    object-fit: cover;
    box-shadow:
      0 6px 16px rgba(0, 40, 60, 0.18),
      inset 0 0 0 0.5px rgba(255,255,255,0.35);
  }
  .brand-text { min-width: 0; line-height: 1.15; }
  .brand-text .name { display: block; }
  .brand small {
    display: block;
    margin-top: 3px;
    font-size: 11px;
    font-weight: 500;
    color: var(--text2);
    letter-spacing: 0;
  }
  .nav { display: flex; flex-direction: column; gap: 1px; flex: 1; min-height: 0; overflow: auto; -webkit-app-region: no-drag; app-region: no-drag; }
  .nav-label {
    margin: 12px 10px 6px;
    font: 650 10px/1 -apple-system, sans-serif;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: var(--text2);
    opacity: 0.85;
    -webkit-app-region: no-drag;
    app-region: no-drag;
    user-select: none;
  }
  .nav-label:first-child { margin-top: 2px; }
  .nav-sep {
    height: 1px; margin: 8px 10px;
    background: var(--sep);
    border: 0;
    -webkit-app-region: no-drag;
    app-region: no-drag;
  }
  .nav button {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    border: 0;
    border-radius: 10px;
    background: transparent;
    color: var(--text);
    padding: 9px 10px;
    font: 600 13px/1 -apple-system, sans-serif;
    cursor: pointer;
    text-align: left;
    -webkit-app-region: no-drag;
    app-region: no-drag;
    transition: background .14s ease, color .14s ease, transform .12s ease;
  }
  .nav button:active { transform: scale(0.98); }
  .nav button:hover { background: color-mix(in srgb, var(--fill) 70%, transparent); }
  .nav button.active {
    background: var(--nav-active);
    color: #fff;
  }
  .nav button.active .ico { background: rgba(255,255,255,0.22); color: #fff; }
  .ico {
    width: 28px; height: 28px; border-radius: 7px;
    display: grid; place-items: center;
    background: var(--fill);
    color: var(--text);
    flex: 0 0 auto;
  }
  .ico svg { width: 16px; height: 16px; display: block; }
  .host {
    margin-top: auto;
    padding: 14px 10px 4px;
    border-top: 0.5px solid var(--sep);
    font-size: 12px;
    -webkit-app-region: drag;
    app-region: drag;
  }
  .host #host-name { font-weight: 600; }
  .host span {
    display: block;
    margin-top: 4px;
    color: var(--text2);
    white-space: pre-line;
    font-weight: 400;
  }
  main {
    display: flex; flex-direction: column; min-width: 0; min-height: 0;
    background: transparent;
  }
  .toolbar {
    height: 52px;
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 20px 0 18px;
    background: var(--toolbar);
    border-bottom: 0.5px solid var(--glass-edge);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    -webkit-app-region: drag;
    app-region: drag;
    cursor: default;
    position: relative;
    z-index: 300;
    overflow: visible;
  }
  .toolbar h1 {
    margin: 0;
    flex: 1;
    min-width: 0;
    font-size: 17px;
    font-weight: 650;
    letter-spacing: -0.3px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    -webkit-app-region: drag;
    app-region: drag;
  }
  .toolbar .controls {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text2);
    font-size: 12px;
    flex: 0 0 auto;
    -webkit-app-region: no-drag;
    app-region: no-drag;
    position: relative;
    z-index: 310;
  }
  .toolbar button, .toolbar select {
    appearance: none;
    border: 0;
    border-radius: 8px;
    background: var(--btn-bg);
    color: var(--text);
    padding: 6px 11px;
    font: 600 12px/1 -apple-system, sans-serif;
    cursor: pointer;
    box-shadow: inset 0 0 0 0.5px var(--sep);
    -webkit-app-region: no-drag;
    app-region: no-drag;
  }
  .theme-btn {
    width: 32px; height: 32px; padding: 0 !important; border-radius: 10px !important;
    display: grid; place-items: center;
    background: var(--btn-bg);
    box-shadow: inset 0 0 0 0.5px var(--glass-edge);
    transition: transform .12s ease, background .14s ease;
    position: relative;
  }
  .theme-btn:hover { background: color-mix(in srgb, var(--tint) 10%, var(--btn-bg)); }
  .theme-btn:active { transform: scale(0.96); }
  .theme-btn svg { width: 15px; height: 15px; display: none; color: var(--text); }
  body[data-theme-pref="light"] .theme-btn .ico-sun { display: block; }
  body[data-theme-pref="dark"] .theme-btn .ico-moon { display: block; }
  body[data-theme-pref="system"] .theme-btn .ico-auto { display: block; }
  /* fallback if pref attr missing */
  body:not([data-theme-pref])[data-theme="light"] .theme-btn .ico-sun { display: block; }
  body:not([data-theme-pref])[data-theme="dark"] .theme-btn .ico-moon { display: block; }
  .hero {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    padding: 16px 18px 8px;
    position: relative;
    z-index: 1;
    flex: 0 0 auto;
  }
  .theme-cards {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; min-width: 280px;
  }
  .glass-cards {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; min-width: 280px;
  }
  .theme-card, .glass-card {
    border: 0.5px solid var(--glass-edge); border-radius: 14px; padding: 10px 8px 12px;
    background: var(--grouped2); cursor: pointer; text-align: center;
    transition: transform .12s ease, box-shadow .14s ease, border-color .14s ease;
    color: var(--text); font: 650 12px/1 -apple-system, sans-serif;
  }
  .theme-card:hover, .glass-card:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
  .theme-card.on, .glass-card.on {
    border-color: color-mix(in srgb, var(--tint) 55%, var(--glass-edge));
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--tint) 22%, transparent);
  }
  .theme-card .preview, .glass-card .preview {
    height: 36px; border-radius: 10px; margin-bottom: 8px;
    box-shadow: inset 0 0 0 0.5px var(--sep);
  }
  .theme-card .preview.light { background: linear-gradient(145deg, #fff, #e8eef8); }
  .theme-card .preview.dark { background: linear-gradient(145deg, #1a1a1c, #000); }
  .theme-card .preview.system {
    background: linear-gradient(90deg, #f2f2f7 50%, #1c1c1e 50%);
  }
  .glass-card .preview.opaque {
    background: linear-gradient(145deg, #fff, #d7dee9);
  }
  .glass-card .preview.medium {
    background:
      linear-gradient(145deg, rgba(255,255,255,0.8), rgba(210,220,235,0.4)),
      repeating-linear-gradient(45deg, #9aa7bd 0 3px, transparent 3px 8px);
  }
  .glass-card .preview.clear {
    background:
      linear-gradient(145deg, rgba(255,255,255,0.35), rgba(190,205,230,0.15)),
      repeating-linear-gradient(-45deg, #7f8ea8 0 2px, transparent 2px 6px);
  }
  body[data-theme="dark"] .glass-card .preview.opaque {
    background: linear-gradient(145deg, #2c2c30, #050505);
  }
  body[data-theme="dark"] .glass-card .preview.medium {
    background:
      linear-gradient(145deg, rgba(40,40,44,0.85), rgba(8,8,10,0.4)),
      repeating-linear-gradient(45deg, #555 0 3px, transparent 3px 8px);
  }
  body[data-theme="dark"] .glass-card .preview.clear {
    background:
      linear-gradient(145deg, rgba(40,40,44,0.4), rgba(0,0,0,0.12)),
      repeating-linear-gradient(-45deg, #666 0 2px, transparent 2px 6px);
  }
  .tile {
    background: var(--grouped);
    border-radius: 14px;
    padding: 14px 14px 12px;
    box-shadow: var(--shadow);
    border: 0.5px solid var(--glass-edge);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
  }
  .tile .k {
    display: flex; align-items: center; gap: 6px;
    color: var(--text2); font-size: 12px; font-weight: 600; margin-bottom: 8px;
  }
  .tile .dot {
    width: 8px; height: 8px; border-radius: 50%; background: var(--c, var(--accent));
  }
  .tile .v {
    font-size: 28px; font-weight: 700; letter-spacing: -0.8px;
    color: var(--text); font-variant-numeric: tabular-nums;
  }
  .tile .s {
    margin-top: 6px; color: var(--text2);
    font: 500 11px/1.3 ui-monospace, Menlo, monospace;
  }
  .content { flex: 1; min-height: 0; overflow: auto; padding: 8px 18px 18px; position: relative; z-index: 1; }
  .page { display: none; }
  .page.active { display: block; animation: fade .18s ease; }
  @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
  @media (prefers-reduced-motion: reduce) {
    .page.active, .nav button, .btn-primary, .btn-ghost, .btn-danger, .btn-mini,
    .clean-progress .bar > i, .clean-progress.indeterminate .bar > i { animation: none !important; transition: none !important; }
  }
  .head { margin: 4px 0 14px; }
  .head h2 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.6px; }
  .head p { margin: 6px 0 0; color: var(--text2); font-size: 13px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: stretch; }
  .grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
  .grid.cols-4 { grid-template-columns: repeat(4, 1fr); }
  .card {
    background: var(--grouped);
    border-radius: 16px;
    padding: 14px 16px;
    border: 0.5px solid var(--glass-edge);
    box-shadow: var(--shadow);
    min-height: 0;
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    display: flex;
    flex-direction: column;
  }
  .card.h-metric { min-height: 168px; }
  .card.h-chart { min-height: 188px; }
  .card.h-table { min-height: 220px; }
  .card h3 {
    margin: 0 0 12px;
    color: var(--text2);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.2px;
    text-transform: uppercase;
    display: flex; align-items: center; gap: 8px;
  }
  .card h3 i {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--c, var(--accent)); display: inline-block;
  }
  .card .card-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }
  .metric-row { display: flex; gap: 16px; align-items: center; }
  .metric-row .grow { flex: 1; min-width: 0; }
  .ring {
    --p: 0; width: 104px; height: 104px; border-radius: 50%;
    background: conic-gradient(var(--c) calc(var(--p) * 1%), var(--track) 0);
    display: grid; place-items: center; flex: 0 0 auto;
  }
  .ring > div {
    width: 78px; height: 78px; border-radius: 50%;
    background: var(--ring-hole);
    display: grid; place-items: center; text-align: center;
  }
  .ring b {
    font-size: 20px; font-weight: 700; letter-spacing: -0.5px;
    font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;
  }
  .ring small { color: var(--text2); font-size: 10px; font-weight: 600; }
  .detail {
    font: 500 12px/1.7 ui-monospace, Menlo, monospace;
    color: var(--text); white-space: pre-line;
  }
  .kv-list { display: flex; flex-direction: column; gap: 0; }
  .kv-row {
    display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: baseline;
    padding: 8px 0; border-bottom: 0.5px solid color-mix(in srgb, var(--sep) 80%, transparent);
    font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;
  }
  .kv-row:last-child { border-bottom: 0; }
  .kv-row .k { color: var(--text2); font: 600 12px/1.2 -apple-system, sans-serif; }
  .kv-row .v {
    color: var(--text); font: 650 13px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
    text-align: right; letter-spacing: -0.2px;
  }
  .kv-row .v.accent { color: var(--tint); }
  .kv-row .v.warn { color: var(--warn); }
  .kv-row .v.good { color: var(--disk); }
  .kpi-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px;
  }
  .kpi {
    background: var(--grouped); border-radius: 16px; padding: 14px 16px;
    border: 0.5px solid var(--glass-edge); box-shadow: var(--shadow);
    backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
    min-height: 108px; display: flex; flex-direction: column; justify-content: space-between;
  }
  .kpi .label {
    display: flex; align-items: center; gap: 8px;
    color: var(--text2); font: 700 11px/1 -apple-system, sans-serif;
    letter-spacing: 0.2px; text-transform: uppercase;
  }
  .kpi .label i {
    width: 8px; height: 8px; border-radius: 50%; background: var(--c, var(--accent));
  }
  .kpi .value {
    margin-top: 10px; font: 700 28px/1.05 -apple-system, sans-serif;
    letter-spacing: -0.8px; font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;
    color: var(--text);
  }
  .kpi .value.sm { font-size: 22px; letter-spacing: -0.5px; }
  .kpi .sub {
    margin-top: 8px; color: var(--text2);
    font: 500 11px/1.35 ui-monospace, Menlo, monospace;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .rate-row {
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 8px;
  }
  .rate-box {
    padding: 10px 12px; border-radius: 12px; background: var(--grouped2);
    border: 0.5px solid color-mix(in srgb, var(--sep) 70%, transparent);
  }
  .rate-box .rk { color: var(--text2); font: 650 10px/1 -apple-system, sans-serif; letter-spacing: 0.3px; text-transform: uppercase; }
  .rate-box .rv {
    margin-top: 6px; font: 700 18px/1 ui-monospace, Menlo, monospace;
    font-variant-numeric: tabular-nums; letter-spacing: -0.3px;
  }
  .bar {
    height: 8px; border-radius: 99px; background: var(--track); overflow: hidden; margin: 8px 0;
  }
  .bar > span {
    display: block; height: 100%; width: 0%;
    background: var(--c, var(--accent)); border-radius: 99px;
    transition: width .28s ease;
  }
  .stack {
    display: flex; height: 10px; border-radius: 99px; overflow: hidden;
    background: var(--track); margin: 8px 0;
  }
  .stack i { display: block; height: 100%; }
  .muted { color: var(--text2); font-size: 12px; }
  .big {
    font-size: 28px; font-weight: 700; letter-spacing: -0.7px;
    font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;
  }
  .down { color: var(--down); }
  .up { color: var(--up); }
  .section-gap { margin-top: 4px; margin-bottom: 10px; color: var(--text2); font: 700 11px/1 -apple-system, sans-serif; letter-spacing: 0.3px; text-transform: uppercase; }
  .info-grid {
    display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px;
  }
  @media (max-width: 1180px) {
    .info-grid { grid-template-columns: repeat(3, 1fr); }
    .kpi-grid, .grid.cols-4 { grid-template-columns: repeat(2, 1fr); }
    .grid.cols-3 { grid-template-columns: 1fr 1fr; }
  }
  table {
    width: 100%; border-collapse: collapse;
    font: 500 12px/1.4 ui-monospace, Menlo, monospace;
  }
  th, td {
    text-align: left; padding: 9px 6px;
    border-bottom: 0.5px solid var(--sep);
  }
  th {
    color: var(--text2); font-weight: 650;
    font-family: -apple-system, sans-serif; font-size: 11px;
  }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  .statusbar {
    height: 32px; flex: 0 0 auto; display: flex; align-items: center; padding: 0 16px;
    background: var(--toolbar); border-top: 0.5px solid var(--glass-edge);
    color: var(--text2); font: 500 11px/1 ui-monospace, Menlo, monospace;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    position: relative; z-index: 2;
  }
  .spark { width: 100%; height: 52px; display: block; margin-top: 8px; }
  .cores { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  @media (max-width: 1180px) { .cores { grid-template-columns: repeat(3, 1fr); } }
  .core {
    background: var(--grouped2); border-radius: 12px; padding: 10px 12px;
    border: 0.5px solid var(--glass-edge);
    backdrop-filter: blur(12px) saturate(160%);
    -webkit-backdrop-filter: blur(12px) saturate(160%);
  }
  .core .top { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
  .core .t { color: var(--text2); font-size: 11px; font-weight: 600; }
  .core .n {
    text-align: right; font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;
    font: 700 14px/1 ui-monospace, Menlo, monospace; letter-spacing: -0.2px;
  }
  .vols-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  @media (max-width: 980px) { .vols-grid { grid-template-columns: 1fr; } }
  .vol-card {
    margin: 0; padding: 12px 14px; border-bottom: 0;
    background: var(--grouped2); border-radius: 14px;
    border: 0.5px solid color-mix(in srgb, var(--sep) 70%, transparent);
  }
  .search { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
  .search input {
    background: var(--grouped); border: 0.5px solid var(--sep); color: var(--text);
    border-radius: 10px; padding: 9px 12px; min-width: 240px; font: inherit;
  }
  .full { grid-column: 1 / -1; }
  .clean-hero {
    display: grid; grid-template-columns: 1fr auto; gap: 16px; align-items: end;
    padding: 20px 20px; border-radius: 18px; margin-bottom: 12px;
    background:
      radial-gradient(120% 80% at 0% 0%, color-mix(in srgb, var(--tint) 18%, transparent), transparent 55%),
      var(--grouped);
    border: 0.5px solid var(--glass-edge);
    box-shadow: var(--shadow);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
  }
  .clean-hero .bytes {
    font-size: 36px; font-weight: 700; letter-spacing: -1.2px; color: var(--tint);
    font-variant-numeric: tabular-nums;
  }
  .clean-hero .hint { color: var(--text2); margin-top: 4px; font-size: 12px; max-width: 420px; }
  .clean-hero .meta {
    display: flex; gap: 14px; margin-top: 12px; flex-wrap: wrap;
    color: var(--text2); font-size: 12px;
  }
  .clean-hero .meta b { color: var(--text); font-weight: 650; }
  .clean-stack {
    display: flex; height: 8px; border-radius: 999px; overflow: hidden; margin-top: 14px;
    background: var(--grouped2); box-shadow: inset 0 0 0 0.5px var(--sep);
  }
  .clean-stack i { display:block; height:100%; min-width: 0; }
  .clean-insights {
    display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 12px 0 4px;
  }
  .clean-insight {
    border-radius: 12px; padding: 10px 12px;
    background: color-mix(in srgb, var(--grouped2) 80%, transparent);
    border: 0.5px solid var(--sep);
  }
  .clean-insight .l { font-size: 11px; color: var(--text2); font-weight: 650; }
  .clean-insight .v { margin-top: 4px; font: 750 15px/1.1 -apple-system, sans-serif; letter-spacing: -0.3px; }
  .clean-insight .d { margin-top: 3px; font-size: 11px; color: var(--text2); }
  .clean-insight.good .v { color: #248a3d; }
  .clean-insight.warn .v { color: #c93400; }
  body[data-theme="dark"] .clean-insight.good .v { color: #30d158; }
  body[data-theme="dark"] .clean-insight.warn .v { color: #ff9f0a; }
  .clean-cat-filters {
    display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 10px;
  }
  .clean-chip {
    border: 0.5px solid var(--sep); border-radius: 999px; padding: 5px 10px; cursor: pointer;
    background: var(--grouped2); color: var(--text2); font: 650 11px/1 -apple-system, sans-serif;
  }
  .clean-chip.active { background: color-mix(in srgb, var(--tint) 14%, transparent); color: var(--tint); border-color: color-mix(in srgb, var(--tint) 35%, var(--sep)); }
  @media (max-width: 980px) {
    .clean-insights { grid-template-columns: repeat(2, 1fr); }
  }
  .un-hero {
    display: flex; justify-content: space-between; gap: 18px; align-items: flex-start;
    margin-bottom: 14px; flex-wrap: wrap;
  }
  .un-hero .bytes {
    font: 750 34px/1.05 -apple-system, sans-serif; letter-spacing: -0.8px; margin-top: 4px;
  }
  .un-hero .hint { margin-top: 8px; color: var(--text2); font-size: 13px; max-width: 520px; line-height: 1.45; }
  .un-hero .meta {
    display: flex; gap: 14px; margin-top: 12px; flex-wrap: wrap;
    color: var(--text2); font-size: 12px;
  }
  .un-hero .meta b { color: var(--text); font-weight: 650; }
  .un-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
  .un-layout {
    display: grid; grid-template-columns: minmax(280px, 1.05fr) minmax(320px, 1.2fr); gap: 12px;
  }
  @media (max-width: 980px) {
    .un-layout { grid-template-columns: 1fr; }
  }
  .un-pane {
    border-radius: 16px; background: var(--grouped); border: 0.5px solid var(--sep);
    box-shadow: var(--shadow); overflow: hidden; min-height: 420px;
    display: flex; flex-direction: column;
  }
  .un-pane-head {
    padding: 12px 14px; border-bottom: 0.5px solid var(--sep);
    display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
  }
  .un-pane-head .title { font: 650 13px/1 -apple-system, sans-serif; margin-right: auto; }
  .un-search {
    border: 0.5px solid var(--sep); border-radius: 10px; padding: 8px 10px;
    background: var(--grouped2); color: var(--text); font-size: 12px; min-width: 140px; flex: 1;
  }
  .un-select {
    border: 0.5px solid var(--sep); border-radius: 10px; padding: 7px 8px;
    background: var(--grouped2); color: var(--text); font-size: 12px;
  }
  .un-apps, .un-leftovers { overflow: auto; flex: 1; max-height: min(58vh, 620px); padding: 6px; }
  .un-app {
    display: grid; grid-template-columns: 40px 1fr auto; gap: 10px; align-items: center;
    padding: 10px 10px; border-radius: 12px; cursor: pointer;
  }
  .un-app:hover { background: color-mix(in srgb, var(--tint) 8%, transparent); }
  .un-app.active { background: color-mix(in srgb, var(--tint) 14%, transparent); }
  .un-app.protected { opacity: 0.55; }
  .un-app .ico {
    width: 40px; height: 40px; border-radius: 10px; overflow: hidden;
    background: var(--grouped2); display: grid; place-items: center;
    font: 750 14px/1 -apple-system, sans-serif; color: var(--tint);
  }
  .un-app .ico img { width: 100%; height: 100%; object-fit: cover; }
  .un-app .name { font: 650 13px/1.2 -apple-system, sans-serif; }
  .un-app .sub { margin-top: 3px; color: var(--text2); font-size: 11px; }
  .un-app .size { font: 650 12px/1 ui-monospace, Menlo, monospace; color: var(--text2); }
  .un-detail-empty {
    padding: 48px 24px; text-align: center; color: var(--text2); font-size: 13px; line-height: 1.5;
  }
  .un-detail-empty .big { font: 700 16px/1.3 -apple-system, sans-serif; color: var(--text); margin-bottom: 8px; }
  .un-detail-head {
    display: flex; gap: 12px; align-items: center; padding: 14px 14px 10px;
  }
  .un-detail-head .ico {
    width: 52px; height: 52px; border-radius: 14px; overflow: hidden;
    background: var(--grouped2); display: grid; place-items: center;
    font: 750 18px/1 -apple-system, sans-serif; color: var(--tint); flex: 0 0 auto;
  }
  .un-detail-head .ico img { width: 100%; height: 100%; object-fit: cover; }
  .un-detail-head .name { font: 700 16px/1.2 -apple-system, sans-serif; }
  .un-detail-head .sub { margin-top: 4px; color: var(--text2); font-size: 12px; }
  .un-row {
    display: grid; grid-template-columns: 18px 1fr auto; gap: 10px; align-items: start;
    padding: 10px 10px; border-radius: 10px;
  }
  .un-row:hover { background: color-mix(in srgb, var(--tint) 6%, transparent); }
  .un-row .name { font: 650 12.5px/1.25 -apple-system, sans-serif; }
  .un-row .path { margin-top: 2px; color: var(--text2); font-size: 11px; word-break: break-all; }
  .un-row .size { font: 650 12px/1 ui-monospace, Menlo, monospace; color: var(--text2); padding-top: 2px; }
  .un-foot {
    border-top: 0.5px solid var(--sep); padding: 12px 14px;
    display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
  }
  .un-foot .sum { margin-right: auto; color: var(--text2); font-size: 12px; }
  .un-foot .sum b { color: var(--text); }
  .un-progress {
    display: none; margin-bottom: 12px; padding: 12px 14px; border-radius: 14px;
    background: var(--grouped); border: 0.5px solid var(--sep);
  }
  .un-progress.show { display: block; }
  .un-progress.indeterminate .bar i { width: 35% !important; animation: cleanPulse 1.1s ease-in-out infinite; }
  .un-progress .row { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
  .un-progress .label { font: 650 12px/1 -apple-system, sans-serif; }
  .un-progress .pct { color: var(--text2); font-size: 12px; }
  .un-progress .bar { height: 6px; border-radius: 999px; background: var(--grouped2); margin-top: 8px; overflow: hidden; }
  .un-progress .bar i { display: block; height: 100%; width: 0; background: var(--tint); border-radius: inherit; transition: width .2s ease; }
  .un-progress .current { margin-top: 8px; color: var(--text2); font-size: 11px; word-break: break-all; }
  .un-success {
    display: none; margin-bottom: 12px; padding: 12px 14px; border-radius: 14px;
    background: color-mix(in srgb, #30d158 12%, var(--grouped)); border: 0.5px solid color-mix(in srgb, #30d158 30%, var(--sep));
  }
  .un-success.show { display: block; }
  .un-success .t { font: 700 14px/1.2 -apple-system, sans-serif; }
  .un-success .s { margin-top: 4px; color: var(--text2); font-size: 12px; }
  .su-hero {
    display: flex; justify-content: space-between; gap: 18px; align-items: flex-start;
    margin-bottom: 14px; flex-wrap: wrap;
  }
  .su-hero .bytes {
    font: 750 34px/1.05 -apple-system, sans-serif; letter-spacing: -0.8px; margin-top: 4px;
  }
  .su-hero .hint { margin-top: 8px; color: var(--text2); font-size: 13px; max-width: 560px; line-height: 1.45; }
  .su-hero .meta {
    display: flex; gap: 14px; margin-top: 12px; flex-wrap: wrap;
    color: var(--text2); font-size: 12px;
  }
  .su-hero .meta b { color: var(--text); font-weight: 650; }
  .su-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
  .su-toolbar {
    display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 10px;
  }
  .su-search {
    border: 0.5px solid var(--sep); border-radius: 10px; padding: 8px 10px;
    background: var(--grouped2); color: var(--text); font-size: 12px; min-width: 180px; flex: 1;
  }
  .su-select {
    border: 0.5px solid var(--sep); border-radius: 10px; padding: 7px 8px;
    background: var(--grouped2); color: var(--text); font-size: 12px;
  }
  .su-list {
    border-radius: 16px; background: var(--grouped); border: 0.5px solid var(--sep);
    box-shadow: var(--shadow); overflow: hidden;
  }
  .su-row {
    display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: center;
    padding: 12px 14px; border-top: 0.5px solid var(--sep);
  }
  .su-row:first-child { border-top: 0; }
  .su-row:hover { background: color-mix(in srgb, var(--tint) 6%, transparent); }
  .su-row.protected { opacity: 0.55; }
  .su-row .name { font: 650 13px/1.25 -apple-system, sans-serif; }
  .su-row .sub { margin-top: 3px; color: var(--text2); font-size: 11px; word-break: break-all; }
  .su-row .tags { margin-top: 6px; display: flex; gap: 6px; flex-wrap: wrap; }
  .su-row .right { display: flex; gap: 8px; align-items: center; }
  .su-empty { padding: 48px 24px; text-align: center; color: var(--text2); font-size: 13px; line-height: 1.5; }
  .su-empty .big { font: 700 16px/1.3 -apple-system, sans-serif; color: var(--text); margin-bottom: 8px; }
  .su-progress {
    display: none; margin-bottom: 12px; padding: 12px 14px; border-radius: 14px;
    background: var(--grouped); border: 0.5px solid var(--sep);
  }
  .su-progress.show { display: block; }
  .su-progress.indeterminate .bar i { width: 35% !important; animation: cleanPulse 1.1s ease-in-out infinite; }
  .su-progress .row { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
  .su-progress .label { font: 650 12px/1 -apple-system, sans-serif; }
  .su-progress .pct { color: var(--text2); font-size: 12px; }
  .su-progress .bar { height: 6px; border-radius: 999px; background: var(--grouped2); margin-top: 8px; overflow: hidden; }
  .su-progress .bar i { display: block; height: 100%; width: 0; background: var(--tint); border-radius: inherit; transition: width .2s ease; }
  .su-progress .current { margin-top: 8px; color: var(--text2); font-size: 11px; word-break: break-all; }
  .su-toast {
    display: none; margin-bottom: 12px; padding: 12px 14px; border-radius: 14px;
    background: color-mix(in srgb, #30d158 12%, var(--grouped));
    border: 0.5px solid color-mix(in srgb, #30d158 30%, var(--sep));
  }
  .su-toast.show { display: block; }
  .su-toast.warn {
    background: color-mix(in srgb, #ff9f0a 14%, var(--grouped));
    border-color: color-mix(in srgb, #ff9f0a 30%, var(--sep));
  }
  .su-toast .t { font: 700 14px/1.2 -apple-system, sans-serif; }
  .su-toast .s { margin-top: 4px; color: var(--text2); font-size: 12px; }
  .su-switch {
    appearance: none; width: 42px; height: 26px; border-radius: 999px; border: 0;
    background: color-mix(in srgb, var(--text2) 35%, transparent); position: relative; cursor: pointer;
    transition: background .16s ease;
  }
  .su-switch::after {
    content: ""; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%;
    background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.2); transition: transform .16s ease;
  }
  .su-switch.on { background: var(--tint); }
  .su-switch.on::after { transform: translateX(16px); }
  .su-switch:disabled { opacity: 0.4; cursor: not-allowed; }
  .perm-page-hero {
    display: flex; gap: 18px; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;
    margin-bottom: 14px; padding: 16px 18px; border-radius: 16px;
    background: var(--grouped); border: 0.5px solid var(--sep); box-shadow: var(--shadow);
  }
  .perm-page-hero .bytes { font: 800 28px/1.1 -apple-system, sans-serif; letter-spacing: -0.03em; margin: 6px 0; }
  .perm-page-hero .hint { color: var(--text2); font-size: 12.5px; line-height: 1.45; max-width: 520px; }
  .perm-page-hero .meta { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 10px; color: var(--text2); font-size: 12px; }
  .perm-page-hero .meta b { color: var(--text); font-weight: 700; }
  .perm-all-ok {
    display: none; margin-bottom: 12px; padding: 12px 14px; border-radius: 14px;
    background: color-mix(in srgb, #30d158 14%, var(--grouped));
    border: 0.5px solid color-mix(in srgb, #30d158 32%, var(--sep));
  }
  .perm-all-ok.show { display: block; }
  .perm-all-ok .t { font: 700 14px/1.25 -apple-system, sans-serif; color: var(--text); }
  .perm-all-ok .s { margin-top: 4px; color: var(--text2); font-size: 12px; }
  .perm-toast {
    display: none; margin-bottom: 12px; padding: 12px 14px; border-radius: 14px;
    background: color-mix(in srgb, #30d158 12%, var(--grouped));
    border: 0.5px solid color-mix(in srgb, #30d158 30%, var(--sep));
  }
  .perm-toast.show { display: block; }
  .perm-toast.warn {
    background: color-mix(in srgb, #ff9f0a 14%, var(--grouped));
    border-color: color-mix(in srgb, #ff9f0a 30%, var(--sep));
  }
  .perm-toast .t { font: 700 14px/1.2 -apple-system, sans-serif; }
  .perm-toast .s { margin-top: 4px; color: var(--text2); font-size: 12px; }
  .perm-list {
    border-radius: 16px; background: var(--grouped); border: 0.5px solid var(--sep);
    box-shadow: var(--shadow); overflow: hidden;
  }
  .perm-row {
    display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: center;
    padding: 14px 16px; border-top: 0.5px solid var(--sep);
  }
  .perm-row:first-child { border-top: 0; }
  .perm-row .name { font: 650 13.5px/1.3 -apple-system, sans-serif; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .perm-row .sub { margin-top: 3px; color: var(--text2); font-size: 12px; line-height: 1.4; }
  .perm-row .tools { margin-top: 6px; color: var(--text2); font-size: 11px; }
  .perm-row .right { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
  .perm-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 9px; border-radius: 999px; font: 700 11px/1 -apple-system, sans-serif;
    background: color-mix(in srgb, var(--text2) 14%, transparent); color: var(--text2);
  }
  .perm-badge.ok {
    background: color-mix(in srgb, #30d158 18%, transparent); color: #1b8f46;
  }
  body[data-theme="dark"] .perm-badge.ok { color: #30d158; }
  .perm-badge.bad {
    background: color-mix(in srgb, #ff9f0a 18%, transparent); color: #c77700;
  }
  body[data-theme="dark"] .perm-badge.bad { color: #ff9f0a; }
  .perm-badge .dot {
    width: 7px; height: 7px; border-radius: 50%; background: currentColor;
  }
  body[data-page="perms"] .hero { display:none; }
  .clean-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
  .btn-primary {
    border: 0; border-radius: 12px; padding: 11px 18px; cursor: pointer;
    font: 650 13px/1 -apple-system, sans-serif;
    color: var(--btn-primary-text); background: var(--btn-primary);
    transition: opacity .14s ease, transform .12s ease, filter .14s ease;
  }
  .btn-primary:hover { filter: brightness(1.06); }
  .btn-primary:active { transform: scale(0.97); }
  .btn-primary:disabled { opacity: 0.45; cursor: not-allowed; filter: none; transform: none; }
  .btn-ghost {
    border: 0; border-radius: 12px; padding: 11px 16px; cursor: pointer;
    background: var(--btn-bg); color: var(--tint);
    font: 650 13px/1 -apple-system, sans-serif;
    box-shadow: inset 0 0 0 0.5px var(--sep);
    transition: background .14s ease, transform .12s ease;
  }
  .btn-ghost:hover { background: color-mix(in srgb, var(--tint) 10%, var(--btn-bg)); }
  .btn-ghost:active { transform: scale(0.97); }
  .btn-ghost:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
  .btn-danger {
    border: 0; border-radius: 12px; padding: 11px 18px; cursor: pointer;
    font: 650 13px/1 -apple-system, sans-serif;
    color: #fff; background: var(--danger);
    transition: filter .14s ease, transform .12s ease;
  }
  .btn-danger:hover { filter: brightness(1.06); }
  .btn-danger:active { transform: scale(0.97); }
  .btn-mini {
    border: 0; border-radius: 8px; padding: 6px 10px; cursor: pointer;
    background: transparent; color: var(--tint);
    font: 650 12px/1 -apple-system, sans-serif;
    transition: background .14s ease, transform .12s ease, color .14s ease;
  }
  .btn-mini:hover { background: color-mix(in srgb, var(--tint) 10%, transparent); }
  .btn-mini:active { transform: scale(0.96); }
  .btn-mini.dim { color: var(--text2); }
  .btn-mini.danger { color: var(--danger); }
  .btn-mini.danger:hover { background: color-mix(in srgb, var(--danger) 12%, transparent); }
  .clean-progress {
    display: none; margin-bottom: 12px; padding: 14px 16px; border-radius: 14px;
    background: var(--grouped); border: 0.5px solid var(--sep);
  }
  .clean-progress.show { display: block; }
  .clean-progress .row {
    display: flex; justify-content: space-between; gap: 12px; align-items: center;
    margin-bottom: 8px;
  }
  .clean-progress .label { font-weight: 650; font-size: 13px; }
  .clean-progress .pct {
    font: 650 12px ui-monospace, Menlo, monospace; color: var(--tint);
    font-variant-numeric: tabular-nums;
  }
  .clean-progress .bar {
    height: 8px; border-radius: 999px; background: var(--grouped2); overflow: hidden;
    box-shadow: inset 0 0 0 0.5px var(--sep);
  }
  .clean-progress .bar > i {
    display: block; height: 100%; width: 0%; border-radius: inherit;
    background: linear-gradient(90deg, color-mix(in srgb, var(--tint) 70%, #34c759), var(--tint));
    transition: width .18s ease;
  }
  .clean-progress.indeterminate .bar > i {
    width: 36% !important;
    animation: clean-indeterminate 1.1s ease-in-out infinite;
  }
  @keyframes clean-indeterminate {
    0% { transform: translateX(-120%); }
    100% { transform: translateX(320%); }
  }
  .clean-progress .current {
    margin-top: 8px; color: var(--text2); font-size: 11px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-family: ui-monospace, Menlo, monospace;
  }
  .clean-progress .stats {
    margin-top: 8px; display: flex; gap: 14px; flex-wrap: wrap; align-items: center;
    color: var(--text2); font-size: 11px;
  }
  .clean-toolbar {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    margin-bottom: 10px; flex-wrap: wrap;
  }
  .clean-toolbar .left, .clean-toolbar .right { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
  .clean-search {
    background: var(--grouped); border: 0.5px solid var(--sep); color: var(--text);
    border-radius: 10px; padding: 7px 10px; min-width: 160px; font: inherit;
  }
  .clean-select {
    background: var(--grouped); border: 0.5px solid var(--sep); color: var(--text);
    border-radius: 10px; padding: 7px 10px; font: inherit;
  }
  .clean-toggle {
    display: inline-flex; align-items: center; gap: 6px; color: var(--text2); font-size: 12px;
    user-select: none; cursor: pointer;
  }
  .clean-cats { display: flex; flex-direction: column; gap: 8px; }
  .clean-cat {
    border-radius: 12px; background: var(--grouped2); overflow: hidden;
    box-shadow: inset 0 0 0 0.5px var(--sep);
  }
  .clean-cat-head {
    display: grid; grid-template-columns: 28px 28px 22px 1fr auto; gap: 8px; align-items: center;
    padding: 12px 12px; cursor: pointer; user-select: none;
  }
  .clean-cat-head:hover { background: color-mix(in srgb, var(--tint) 6%, transparent); }
  .clean-cat-ico {
    width: 28px; height: 28px; border-radius: 8px; display: grid; place-items: center;
    background: color-mix(in srgb, var(--tint) 14%, transparent); color: var(--tint);
  }
  .clean-cat-ico svg { width: 15px; height: 15px; }
  .clean-cat-head .chev {
    width: 18px; height: 18px; color: var(--text2);
    transition: transform .15s ease; display: grid; place-items: center;
  }
  .clean-cat.open .chev { transform: rotate(90deg); }
  .clean-cat-head .title { font-weight: 650; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .clean-cat-head .sub { color: var(--text2); font-size: 11px; margin-top: 2px; }
  .clean-cat-head .size {
    font: 650 13px ui-monospace, Menlo, monospace; color: var(--tint);
    font-variant-numeric: tabular-nums; text-align: right;
  }
  .clean-items { display: none; border-top: 0.5px solid var(--sep); max-height: 320px; overflow: auto; }
  .clean-cat.open .clean-items { display: block; }
  .clean-row {
    display: grid; grid-template-columns: 28px 1fr auto auto; gap: 8px; align-items: start;
    padding: 10px 12px 10px 40px; border-top: 0.5px solid color-mix(in srgb, var(--sep) 70%, transparent);
  }
  .clean-row:hover { background: color-mix(in srgb, var(--tint) 5%, transparent); }
  .clean-row .name { font-weight: 600; font-size: 12.5px; word-break: break-all; }
  .clean-row .path { color: var(--text2); font-size: 10.5px; margin-top: 2px;
    font-family: ui-monospace, Menlo, monospace; word-break: break-all; }
  .clean-row .meta { color: var(--text2); font-size: 10.5px; margin-top: 3px; }
  .clean-row .size {
    font: 650 12px ui-monospace, Menlo, monospace; color: var(--text);
    font-variant-numeric: tabular-nums; padding-top: 2px; min-width: 64px; text-align: right;
  }
  .clean-row .reveal {
    border: 0; background: transparent; color: var(--tint); cursor: pointer;
    font: 650 11px/1 -apple-system, sans-serif; padding: 4px 6px; border-radius: 6px;
    opacity: 0.75;
  }
  .clean-row:hover .reveal { opacity: 1; background: color-mix(in srgb, var(--tint) 10%, transparent); }
  .clean-empty {
    padding: 36px 20px; text-align: center; color: var(--text2); font-size: 13px;
  }
  .clean-empty .big { font-size: 15px; font-weight: 650; color: var(--text); margin-bottom: 6px; }
  .clean-empty .art {
    width: 56px; height: 56px; margin: 0 auto 14px; border-radius: 16px;
    display: grid; place-items: center; color: var(--tint);
    background: color-mix(in srgb, var(--tint) 12%, transparent);
  }
  .clean-history {
    margin-top: 12px; padding: 12px; border-radius: 12px; background: var(--grouped2);
  }
  .clean-history h4 { margin: 0 0 8px; font-size: 12px; color: var(--text2); font-weight: 650; }
  .clean-history .h-row {
    display: flex; justify-content: space-between; gap: 10px; padding: 5px 0;
    border-top: 0.5px solid color-mix(in srgb, var(--sep) 60%, transparent); font-size: 12px;
  }
  .clean-history .h-row:first-of-type { border-top: 0; }
  .clean-success {
    display: none; margin-bottom: 12px; padding: 16px 18px; border-radius: 14px;
    background: color-mix(in srgb, var(--disk) 12%, var(--grouped));
    border: 0.5px solid color-mix(in srgb, var(--disk) 35%, var(--sep));
  }
  .clean-success.show { display: block; animation: clean-pop .35s ease; }
  @keyframes clean-pop {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: none; }
  }
  .clean-success .t { font-weight: 700; font-size: 15px; color: var(--disk); }
  .clean-success .s { color: var(--text2); margin-top: 4px; font-size: 12px; }
  .modal-backdrop {
    display: none; position: fixed; inset: 0; z-index: 50;
    background: rgba(0,0,0,0.45); align-items: center; justify-content: center;
  }
  .modal-backdrop.show { display: flex; }
  #perm-modal { z-index: 12000; }
  .modal {
    width: min(420px, 92vw); background: var(--grouped); border-radius: 16px;
    border: 0.5px solid var(--sep); padding: 20px; box-shadow: 0 18px 48px rgba(0,0,0,0.35);
  }
  .modal h3 { margin: 0 0 8px; font-size: 16px; }
  .modal p { margin: 0 0 14px; color: var(--text2); font-size: 13px; line-height: 1.5; }
  .modal .warn-box {
    background: color-mix(in srgb, var(--warn) 12%, transparent);
    color: var(--warn); border-radius: 10px; padding: 10px 12px; font-size: 12px; margin-bottom: 14px;
  }
  .modal .actions { display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap; }
  .modal .steps {
    margin: 0 0 14px; padding: 0 0 0 18px; color: var(--text); font-size: 13px; line-height: 1.55;
  }
  .modal .steps li { margin: 0 0 6px; }
  .modal .perm-ico {
    width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
    background: color-mix(in srgb, var(--tint) 14%, transparent); color: var(--tint); margin-bottom: 12px;
  }
  .modal .perm-ico svg { width: 22px; height: 22px; }
  .perm-banner {
    display: none; margin: 10px 0 0; padding: 10px 12px; border-radius: 12px; gap: 10px; align-items: center;
    background: color-mix(in srgb, var(--warn) 12%, var(--grouped));
    border: 0.5px solid color-mix(in srgb, var(--warn) 30%, var(--sep));
    color: var(--text); font-size: 12px; line-height: 1.4;
  }
  .perm-banner.show { display: flex; }
  .perm-banner .txt { flex: 1; min-width: 0; }
  .perm-banner b { display:block; margin-bottom: 2px; font-size: 12.5px; }
  .perm-link {
    border: 0; background: transparent; color: var(--tint); font: 650 12px/1.4 -apple-system, sans-serif;
    cursor: pointer; padding: 0; text-decoration: underline; text-underline-offset: 2px;
  }
  .badge {
    display: inline-block; font-size: 10px; padding: 2px 7px; border-radius: 6px;
    background: color-mix(in srgb, var(--tint) 14%, transparent); color: var(--tint); margin-left: 0;
    font-weight: 650;
  }
  .badge.warn {
    background: color-mix(in srgb, var(--warn) 16%, transparent); color: var(--warn);
  }
  input[type=checkbox].clean-cb {
    width: 16px; height: 16px; accent-color: var(--tint); cursor: pointer; margin: 0;
  }

  .alerts { display:none; gap:8px; margin-bottom:12px; flex-wrap:wrap; }
  .alerts.show { display:flex; }
  .alert {
    padding: 8px 12px; border-radius: 10px; font-size: 12px; font-weight: 650;
    background: color-mix(in srgb, var(--warn) 14%, var(--grouped));
    color: var(--warn); border: 0.5px solid color-mix(in srgb, var(--warn) 30%, var(--sep));
  }
  .alert.danger {
    background: color-mix(in srgb, var(--danger) 14%, var(--grouped));
    color: var(--danger); border-color: color-mix(in srgb, var(--danger) 30%, var(--sep));
  }
  .info-pill {
    background: var(--grouped); border: 0.5px solid var(--glass-edge); border-radius: 14px; padding: 11px 12px;
    box-shadow: var(--shadow);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    min-height: 68px;
  }
  .info-pill .k {
    color: var(--text2); font-size: 10px; font-weight: 700;
    letter-spacing: 0.2px; text-transform: uppercase;
  }
  .info-pill .v {
    font-size: 14px; font-weight: 700; margin-top: 6px; letter-spacing: -0.2px;
    font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .proc-actions { display:flex; gap:4px; justify-content:flex-end; white-space:nowrap; }
  .proc-actions button {
    border:0; border-radius:7px; padding:4px 7px; cursor:pointer; font:650 11px/1 -apple-system,sans-serif;
    background: var(--btn-bg); color: var(--tint); box-shadow: inset 0 0 0 0.5px var(--sep);
  }
  .proc-actions button.danger { color: var(--danger); }
  .card-head {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    margin-bottom: 10px;
  }
  .card-head h3 { margin: 0; }
  .card-head .proc-stop-btn[disabled] { opacity: 0.4; cursor: default; }
  .proc-toolbar {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;
  }
  .proc-toolbar .sel-count { color: var(--text2); font-size: 12px; margin-right: 4px; }
  .proc-toolbar button.danger { color: var(--danger); }
  table td.chk, table th.chk { width: 28px; text-align: center; }
  table input.proc-cb { width: 14px; height: 14px; accent-color: var(--tint); cursor: pointer; }
  tr.proc-selected { background: color-mix(in srgb, var(--tint) 10%, transparent); }
  .vol-meta { display:flex; justify-content:space-between; align-items:baseline; gap:10px; margin-bottom:8px; }
  .vol-meta .vt { font-weight: 650; font-size: 13px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .vol-meta .vp {
    font: 700 14px/1 ui-monospace, Menlo, monospace;
    font-variant-numeric: tabular-nums; letter-spacing: -0.2px; flex: 0 0 auto;
  }
  .hero.hide-on-clean { }
  body[data-page="clean"] .hero { display:none; }
  body[data-page="uninstall"] .hero { display:none; }
  body[data-page="startup"] .hero { display:none; }
  body[data-page="settings"] .hero { display:none; }
  body[data-page="shot"] .hero { display:none; }
  body[data-page="rec"] .hero { display:none; }
  .rec-live {
    display: none; margin-bottom: 14px; padding: 14px 16px; border-radius: 16px;
    background: linear-gradient(135deg, color-mix(in srgb, #ff3b30 18%, var(--grouped)), var(--grouped));
    border: 0.5px solid color-mix(in srgb, #ff3b30 35%, var(--sep));
    box-shadow: var(--shadow);
  }
  .rec-live.on { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .rec-live .left { display: flex; align-items: center; gap: 12px; min-width: 0; }
  .rec-live .dot {
    width: 10px; height: 10px; border-radius: 50%; background: #ff3b30;
    box-shadow: 0 0 0 0 rgba(255,59,48,0.55);
    animation: recPulse 1.2s ease-out infinite;
    flex: 0 0 auto;
  }
  @keyframes recPulse {
    0% { box-shadow: 0 0 0 0 rgba(255,59,48,0.5); }
    70% { box-shadow: 0 0 0 10px rgba(255,59,48,0); }
    100% { box-shadow: 0 0 0 0 rgba(255,59,48,0); }
  }
  .rec-live .timer {
    font: 800 22px/1 ui-monospace, Menlo, monospace; letter-spacing: -0.4px;
    font-variant-numeric: tabular-nums;
  }
  .rec-live .msg { color: var(--text2); font-size: 12px; margin-top: 4px; }
  .rec-live .btn-stop {
    border: 0; border-radius: 12px; padding: 10px 16px; cursor: pointer;
    background: #ff3b30; color: #fff; font: 700 13px/1 -apple-system, sans-serif;
  }
  .rec-live .btn-stop:hover { filter: brightness(1.06); }
  .rec-countdown {
    display: none; position: fixed; inset: 0; z-index: 9500;
    background: rgba(0,0,0,0.55); align-items: center; justify-content: center;
    flex-direction: column; gap: 10px; color: #fff;
  }
  .rec-countdown.on { display: flex; }
  .rec-countdown .n {
    font: 800 96px/1 ui-rounded, -apple-system, sans-serif; letter-spacing: -4px;
    animation: themePop .2s ease;
  }
  .rec-countdown .t { font-size: 14px; opacity: 0.7; }
  .rec-editor {
    display: none; position: fixed; inset: 0; z-index: 9000;
    background: rgba(8, 10, 14, 0.72);
    backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
    flex-direction: column;
  }
  .rec-editor.open { display: flex; animation: themePop .16s ease; }
  .rec-ed-stage {
    flex: 1 1 auto; min-height: 0; display: flex; align-items: center; justify-content: center;
    padding: 8px 18px 12px; overflow: hidden;
  }
  .rec-ed-card {
    width: min(880px, 100%); background: rgba(28,28,30,0.92); border-radius: 18px;
    overflow: hidden; box-shadow: 0 18px 50px rgba(0,0,0,0.45);
  }
  .rec-ed-poster {
    aspect-ratio: 16/10; background: #111 center/cover no-repeat;
    display: flex; align-items: center; justify-content: center; position: relative;
  }
  .rec-ed-poster .play {
    width: 64px; height: 64px; border-radius: 50%; border: 0; cursor: pointer;
    background: rgba(255,255,255,0.92); color: #111;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  }
  .rec-ed-poster .play svg { width: 26px; height: 26px; margin-left: 3px; }
  .rec-ed-info { padding: 16px 18px; color: #fff; }
  .rec-ed-info .name { font: 700 16px/1.2 -apple-system, sans-serif; }
  .rec-ed-info .meta { margin-top: 6px; color: rgba(255,255,255,0.55); font-size: 12px; }
  body[data-page="conn"] .hero { display:none; }
  .conn-stage {
    position: relative; overflow: hidden;
    border-radius: 22px; padding: 28px 28px 24px;
    margin-bottom: 16px;
    background:
      radial-gradient(120% 90% at 12% -10%, color-mix(in srgb, #0a84ff 28%, transparent), transparent 55%),
      radial-gradient(90% 70% at 88% 110%, color-mix(in srgb, #30d158 18%, transparent), transparent 50%),
      linear-gradient(165deg, color-mix(in srgb, var(--grouped) 92%, #0a84ff), var(--grouped));
    border: 0.5px solid var(--glass-edge);
    box-shadow: var(--shadow);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
  }
  .conn-stage::after {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background-image:
      linear-gradient(color-mix(in srgb, var(--sep) 55%, transparent) 1px, transparent 1px),
      linear-gradient(90deg, color-mix(in srgb, var(--sep) 55%, transparent) 1px, transparent 1px);
    background-size: 28px 28px; opacity: 0.18; mask-image: radial-gradient(circle at 40% 30%, #000 20%, transparent 70%);
  }
  .conn-stage-inner {
    position: relative; z-index: 1;
    display: grid; grid-template-columns: auto 1fr auto; gap: 28px; align-items: center;
  }
  .conn-ring {
    --p: 0; --ring: #0a84ff;
    width: 148px; height: 148px; position: relative;
  }
  .conn-ring svg { width: 100%; height: 100%; transform: rotate(-90deg); }
  .conn-ring .track { fill: none; stroke: color-mix(in srgb, var(--sep) 80%, transparent); stroke-width: 10; }
  .conn-ring .bar {
    fill: none; stroke: var(--ring); stroke-width: 10; stroke-linecap: round;
    stroke-dasharray: 339.292; stroke-dashoffset: calc(339.292 * (1 - var(--p) / 100));
    transition: stroke-dashoffset .55s cubic-bezier(.2,.8,.2,1), stroke .3s ease;
    filter: drop-shadow(0 0 10px color-mix(in srgb, var(--ring) 45%, transparent));
  }
  .conn-ring.busy .bar { animation: connPulse 1.4s ease-in-out infinite; }
  @keyframes connPulse { 0%,100%{ opacity:1 } 50%{ opacity:.55 } }
  .conn-ring .center {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; text-align: center; pointer-events: none;
  }
  .conn-ring .score {
    font: 800 42px/1 ui-rounded, -apple-system, sans-serif;
    letter-spacing: -1.5px; font-variant-numeric: tabular-nums;
  }
  .conn-ring .score-unit { font-size: 12px; font-weight: 650; color: var(--text2); margin-top: 4px; letter-spacing: 0.4px; }
  .conn-copy .eyebrow {
    font-size: 11px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase;
    color: var(--tint); margin-bottom: 6px;
  }
  .conn-copy h2 { margin: 0; font-size: 28px; font-weight: 750; letter-spacing: -0.7px; }
  .conn-copy .sub { margin: 8px 0 0; color: var(--text2); font-size: 13px; line-height: 1.45; max-width: 340px; }
  .conn-copy .status-line {
    margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    min-height: 28px;
  }
  .conn-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 650;
    background: color-mix(in srgb, var(--tint) 12%, transparent); color: var(--tint);
  }
  .conn-pill.ok { background: color-mix(in srgb, #30d158 16%, transparent); color: #248a3d; }
  .conn-pill.warn { background: color-mix(in srgb, #ffd60a 18%, transparent); color: #9a6700; }
  .conn-pill.fail { background: color-mix(in srgb, #ff453a 16%, transparent); color: #d70015; }
  .conn-pill.muted { background: color-mix(in srgb, var(--text2) 12%, transparent); color: var(--text2); }
  body[data-theme="dark"] .conn-pill.ok { color: #30d158; }
  body[data-theme="dark"] .conn-pill.warn { color: #ffd60a; }
  body[data-theme="dark"] .conn-pill.fail { color: #ff6961; }
  .conn-cta { display: flex; flex-direction: column; gap: 10px; align-items: stretch; min-width: 148px; }
  .conn-cta .btn-primary, .conn-cta .btn-ghost {
    padding: 12px 18px; border-radius: 14px; font-size: 14px; font-weight: 700;
  }
  .conn-progress {
    display: none; margin-top: 18px; position: relative; z-index: 1;
  }
  .conn-progress.on { display: block; }
  .conn-progress .row { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:8px; }
  .conn-progress .label { font-size: 13px; font-weight: 650; }
  .conn-progress .pct { font: 700 13px/1 ui-monospace, Menlo, monospace; color: var(--tint); }
  .conn-progress .bar {
    height: 6px; border-radius: 99px; overflow: hidden;
    background: color-mix(in srgb, var(--sep) 70%, transparent);
  }
  .conn-progress .bar > i {
    display:block; height:100%; width:0%; border-radius: inherit;
    background: linear-gradient(90deg, #0a84ff, #64d2ff);
    transition: width .35s ease;
  }
  .conn-kpis {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px;
  }
  .conn-kpi {
    border-radius: 16px; padding: 14px 14px 12px;
    background: var(--grouped); border: 0.5px solid var(--glass-edge);
    box-shadow: var(--shadow);
  }
  .conn-kpi .k { font-size: 11px; font-weight: 700; color: var(--text2); letter-spacing: 0.3px; }
  .conn-kpi .v {
    margin-top: 8px; font: 750 22px/1 ui-rounded, -apple-system, sans-serif;
    letter-spacing: -0.6px; font-variant-numeric: tabular-nums;
  }
  .conn-kpi .s { margin-top: 6px; font-size: 11px; color: var(--text2); }
  .conn-groups { display: flex; flex-direction: column; gap: 12px; }
  .conn-group {
    border-radius: 18px; padding: 16px 16px 8px;
    background: var(--grouped); border: 0.5px solid var(--glass-edge);
    box-shadow: var(--shadow);
  }
  .conn-group-head {
    display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
    margin-bottom: 10px; padding: 0 2px;
  }
  .conn-group-head .t { font-size: 15px; font-weight: 700; letter-spacing: -0.2px; }
  .conn-group-head .d { margin-top: 2px; font-size: 12px; color: var(--text2); }
  .conn-group-head .badge {
    flex: 0 0 auto; font: 700 12px/1 -apple-system, sans-serif;
    padding: 6px 10px; border-radius: 999px;
    background: color-mix(in srgb, var(--tint) 12%, transparent); color: var(--tint);
  }
  .conn-row {
    display: grid; grid-template-columns: 1fr auto auto; gap: 12px; align-items: center;
    padding: 11px 8px; border-top: 0.5px solid color-mix(in srgb, var(--sep) 70%, transparent);
  }
  .conn-row:first-of-type { border-top: 0; }
  .conn-row .name { font-weight: 650; font-size: 13px; }
  .conn-row .detail { margin-top: 3px; font-size: 11px; color: var(--text2); max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .conn-lat {
    font: 700 13px/1 ui-monospace, Menlo, monospace;
    font-variant-numeric: tabular-nums; min-width: 72px; text-align: right;
  }
  .conn-grade {
    min-width: 52px; text-align: center; font-size: 11px; font-weight: 750;
    padding: 5px 8px; border-radius: 8px;
  }
  .conn-grade.excellent { background: color-mix(in srgb, #30d158 18%, transparent); color: #248a3d; }
  .conn-grade.good { background: color-mix(in srgb, #64d2ff 20%, transparent); color: #0071a4; }
  .conn-grade.fair { background: color-mix(in srgb, #ffd60a 22%, transparent); color: #9a6700; }
  .conn-grade.slow, .conn-grade.poor { background: color-mix(in srgb, #ff9f0a 20%, transparent); color: #c93400; }
  .conn-grade.fail { background: color-mix(in srgb, #ff453a 18%, transparent); color: #d70015; }
  body[data-theme="dark"] .conn-grade.excellent { color: #30d158; }
  body[data-theme="dark"] .conn-grade.good { color: #64d2ff; }
  body[data-theme="dark"] .conn-grade.fair { color: #ffd60a; }
  body[data-theme="dark"] .conn-grade.slow, body[data-theme="dark"] .conn-grade.poor { color: #ff9f0a; }
  body[data-theme="dark"] .conn-grade.fail { color: #ff6961; }
  .conn-empty {
    text-align: center; padding: 36px 20px; color: var(--text2); font-size: 13px; line-height: 1.55;
  }
  .conn-empty b { display:block; color: var(--text); font-size: 16px; margin-bottom: 6px; }
  @media (max-width: 920px) {
    .conn-stage-inner { grid-template-columns: 1fr; justify-items: center; text-align: center; }
    .conn-copy .sub { max-width: none; }
    .conn-copy .status-line { justify-content: center; }
    .conn-cta { width: 100%; max-width: 280px; }
    .conn-kpis { grid-template-columns: repeat(2, 1fr); }
  }
  .shot-hero {
    display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 14px; margin-bottom: 14px;
  }
  .shot-actions {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px;
  }
  .shot-action {
    border: 0.5px solid var(--glass-edge); border-radius: 16px; padding: 16px 14px;
    background: var(--grouped); cursor: pointer; text-align: left; color: var(--text);
    box-shadow: var(--shadow); backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    transition: transform .12s ease, background .14s ease;
  }
  .shot-action:hover { transform: translateY(-1px); background: color-mix(in srgb, var(--tint) 8%, var(--grouped)); }
  .shot-action:active { transform: scale(0.98); }
  .shot-action:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
  .shot-action .ico-lg {
    width: 36px; height: 36px; border-radius: 11px; display: grid; place-items: center;
    background: color-mix(in srgb, var(--tint) 14%, transparent); color: var(--tint); margin-bottom: 10px;
  }
  .shot-action .ico-lg svg { width: 18px; height: 18px; }
  .shot-action .t { font: 700 14px/1.2 -apple-system, sans-serif; }
  .shot-action .d { margin-top: 5px; color: var(--text2); font: 500 11px/1.35 -apple-system, sans-serif; }
  .shot-opts {
    display: flex; flex-wrap: wrap; gap: 14px 18px; align-items: center;
    padding: 12px 14px; border-radius: 14px; margin-bottom: 14px;
    background: var(--grouped); border: 0.5px solid var(--glass-edge);
    backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  }
  .shot-opts label {
    display: inline-flex; align-items: center; gap: 7px; color: var(--text2);
    font: 600 12px/1 -apple-system, sans-serif; cursor: pointer; user-select: none;
  }
  .shot-opts select {
    appearance: none; border: 0; border-radius: 8px; padding: 6px 10px;
    background: var(--btn-bg); color: var(--text); font: 600 12px/1 -apple-system, sans-serif;
    box-shadow: inset 0 0 0 0.5px var(--sep);
  }
  .shot-preview {
    min-height: 220px; border-radius: 16px; overflow: hidden;
    background: var(--grouped); border: 0.5px solid var(--glass-edge);
    box-shadow: var(--shadow); display: grid; place-items: center;
    backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  }
  .shot-preview img {
    max-width: 100%; max-height: 320px; display: block; object-fit: contain;
  }
  .shot-preview .empty {
    text-align: center; color: var(--text2); padding: 28px 16px; font-size: 13px;
  }
  .shot-preview .empty b { display:block; color: var(--text); font-size: 15px; margin-bottom: 6px; }
  .shot-meta {
    margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
  }
  .shot-list { display: flex; flex-direction: column; gap: 8px; }
  .shot-row {
    display: grid; grid-template-columns: 1fr auto; gap: 10px; align-items: center;
    padding: 10px 12px; border-radius: 12px; background: var(--grouped2);
    border: 0.5px solid var(--glass-edge);
  }
  .shot-row .name { font-weight: 650; font-size: 12.5px; word-break: break-all; }
  .shot-row .sub { color: var(--text2); font-size: 11px; margin-top: 3px; }
  .shot-row .acts { display: flex; gap: 4px; }
  .shot-toast {
    display: none; position: fixed; left: 50%; bottom: 28px; transform: translateX(-50%);
    z-index: 120; padding: 10px 16px; border-radius: 12px;
    background: rgba(28,28,30,0.92); color: #fff; font: 650 13px/1 -apple-system, sans-serif;
    box-shadow: 0 12px 32px rgba(0,0,0,0.28);
  }
  .shot-toast.show { display: block; animation: themePop .16s ease; }
  .shot-toast.bad { background: rgba(255,59,48,0.92); }
  .shot-busy-banner {
    display: none; margin-bottom: 12px; padding: 10px 14px; border-radius: 12px;
    background: color-mix(in srgb, var(--tint) 12%, var(--grouped));
    color: var(--tint); font: 650 12px/1.3 -apple-system, sans-serif;
    border: 0.5px solid color-mix(in srgb, var(--tint) 28%, var(--sep));
  }
  .shot-busy-banner.show { display: block; }
  .shot-hotkeys {
    display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px;
    margin: 12px 0 4px;
  }
  @media (max-width: 980px) { .shot-hotkeys { grid-template-columns: 1fr; } }
  .shot-editor {
    display: none; position: fixed; inset: 0; z-index: 9000;
    background: rgba(8, 10, 14, 0.72);
    backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
    flex-direction: column;
  }
  .shot-editor.open { display: flex; animation: themePop .16s ease; }
  .shot-ed-top {
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 12px 16px 10px; flex: 0 0 auto;
  }
  .shot-ed-top .title {
    color: #fff; font: 700 15px/1.2 -apple-system, sans-serif; letter-spacing: -0.2px;
  }
  .shot-ed-top .hint { color: rgba(255,255,255,0.55); font-size: 12px; margin-top: 3px; }
  .shot-ed-tools {
    display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
    padding: 0 16px 10px; flex: 0 0 auto;
  }
  .shot-ed-tool, .shot-ed-chip {
    border: 0; border-radius: 10px; padding: 8px 10px; cursor: pointer;
    background: rgba(255,255,255,0.1); color: #fff; font: 650 12px/1 -apple-system, sans-serif;
    display: inline-flex; align-items: center; gap: 6px;
  }
  .shot-ed-tool:hover, .shot-ed-chip:hover { background: rgba(255,255,255,0.16); }
  .shot-ed-tool.active { background: #0a84ff; }
  .shot-ed-tool svg { width: 14px; height: 14px; }
  .shot-ed-sep { width: 1px; height: 22px; background: rgba(255,255,255,0.18); margin: 0 4px; }
  .shot-ed-colors { display: inline-flex; gap: 5px; align-items: center; }
  .shot-ed-color {
    width: 18px; height: 18px; border-radius: 50%; border: 2px solid transparent;
    cursor: pointer; padding: 0;
  }
  .shot-ed-color.active { border-color: #fff; box-shadow: 0 0 0 2px rgba(10,132,255,0.9); }
  .shot-ed-size {
    appearance: none; -webkit-appearance: none; width: 90px; height: 4px;
    border-radius: 99px; background: rgba(255,255,255,0.25); outline: none;
  }
  .shot-ed-stage {
    flex: 1 1 auto; min-height: 0; display: flex; align-items: center; justify-content: center;
    padding: 8px 18px 12px; overflow: hidden;
  }
  .shot-ed-canvas-wrap {
    position: relative; max-width: 100%; max-height: 100%;
    box-shadow: 0 18px 50px rgba(0,0,0,0.45); border-radius: 8px; overflow: hidden;
    background: #111; touch-action: none;
  }
  .shot-ed-canvas-wrap canvas {
    display: block; max-width: 100%; max-height: calc(100vh - 190px);
    cursor: crosshair;
  }
  .shot-ed-bottom {
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 10px 16px 16px; flex: 0 0 auto;
  }
  .shot-ed-bottom .left { color: rgba(255,255,255,0.55); font-size: 12px; }
  .shot-ed-bottom .right { display: flex; gap: 8px; }
  .shot-ed-bottom .btn-ghost {
    background: rgba(255,255,255,0.1); color: #fff; border: 0;
  }
  .shot-ed-bottom .btn-primary { min-width: 108px; }
  .shot-ed-text-input {
    position: absolute; z-index: 2; min-width: 80px; max-width: 60%;
    border: 1.5px dashed #0a84ff; border-radius: 6px; padding: 4px 8px;
    background: rgba(255,255,255,0.92); color: #111;
    font: 700 18px/1.3 -apple-system, sans-serif; outline: none;
  }
  .hk-card {
    background: var(--grouped); border: 0.5px solid var(--glass-edge); border-radius: 14px;
    padding: 12px 14px; box-shadow: var(--shadow);
    backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  }
  .hk-card .hk-title { font: 650 12px/1.2 -apple-system, sans-serif; color: var(--text2); }
  .hk-card .hk-row { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
  .hk-btn {
    flex: 1; min-width: 0; appearance: none; border: 0.5px solid var(--glass-edge);
    border-radius: 10px; padding: 9px 10px; cursor: pointer; text-align: center;
    background: var(--grouped2); color: var(--text);
    font: 700 13px/1 ui-monospace, Menlo, monospace; letter-spacing: 0.2px;
    transition: background .14s ease, border-color .14s ease, transform .12s ease;
  }
  .hk-btn:hover { background: color-mix(in srgb, var(--tint) 10%, var(--grouped2)); }
  .hk-btn.recording {
    border-color: var(--tint); color: var(--tint);
    animation: hkPulse 1s ease infinite;
  }
  @keyframes hkPulse {
    0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--tint) 35%, transparent); }
    50% { box-shadow: 0 0 0 4px color-mix(in srgb, var(--tint) 18%, transparent); }
  }
  .hk-hint { margin-top: 8px; color: var(--text2); font-size: 11px; line-height: 1.45; }
  .hk-hint.warn { color: var(--warn); }
  #ov-quick .kpi { min-height: 108px; }

  /* Settings center */
  .settings-page { max-width: 720px; }
  .settings-group {
    background: var(--grouped);
    border-radius: 14px;
    margin: 0 0 18px;
    overflow: hidden;
    box-shadow: var(--shadow);
    border: 0.5px solid var(--glass-edge);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
  }
  .settings-group h3 {
    margin: 0;
    padding: 14px 16px 6px;
    font-size: 12px;
    font-weight: 650;
    color: var(--text2);
    letter-spacing: 0.2px;
    text-transform: none;
  }
  .settings-group .hint {
    padding: 0 16px 12px;
    font-size: 12px;
    color: var(--text2);
    line-height: 1.4;
  }
  .settings-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 12px 16px;
    border-top: 0.5px solid var(--sep);
    min-height: 48px;
  }
  .settings-row:first-of-type { border-top: 0; }
  .settings-row .label { font-weight: 560; color: var(--text); }
  .settings-row .desc { display:block; margin-top: 2px; font-size: 12px; font-weight: 400; color: var(--text2); }
  .settings-row select, .settings-row .seg {
    border: 0; border-radius: 8px; background: var(--select); color: var(--text);
    font: 560 12px/1.2 -apple-system, sans-serif; padding: 7px 10px; outline: none;
  }
  .settings-row .seg { display:inline-flex; padding: 3px; gap: 2px; }
  .pressure-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 3px 8px; border-radius: 999px; font: 650 11px/1 -apple-system, sans-serif;
    background: color-mix(in srgb, var(--disk) 16%, transparent); color: var(--disk);
  }
  .pressure-pill.warn {
    background: color-mix(in srgb, var(--warn) 18%, transparent); color: var(--warn);
  }
  .pressure-pill.critical {
    background: color-mix(in srgb, var(--danger) 18%, transparent); color: var(--danger);
  }
  .settings-row input[type="number"] {
    width: 72px; font: 560 12px/1.2 -apple-system, sans-serif; padding: 7px 10px; outline: none;
    border-radius: 10px; border: 0.5px solid var(--sep); background: var(--grouped); color: var(--text);
  }
  .settings-row .seg button {
    border: 0; border-radius: 6px; padding: 6px 12px; cursor: pointer;
    background: transparent; color: var(--text2); font: 650 12px/1 -apple-system,sans-serif;
  }
  .settings-row .seg button.on { background: var(--grouped2); color: var(--text); box-shadow: inset 0 0 0 0.5px var(--sep); }
  .switch {
    position: relative; width: 42px; height: 26px; flex-shrink: 0;
  }
  .switch input { opacity: 0; width: 0; height: 0; position: absolute; }
  .switch span {
    position: absolute; inset: 0; border-radius: 99px; background: var(--fill);
    transition: background .18s ease; cursor: pointer;
  }
  .switch span::after {
    content: ''; position: absolute; top: 2px; left: 2px; width: 22px; height: 22px;
    border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25);
    transition: transform .18s ease;
  }
  .switch input:checked + span { background: var(--tint); }
  .switch input:checked + span::after { transform: translateX(16px); }
  .settings-actions { display:flex; gap: 10px; flex-wrap: wrap; margin: 4px 0 24px; }
  .settings-actions button {
    border: 0; border-radius: 10px; padding: 10px 14px; cursor: pointer;
    font: 650 13px/1 -apple-system,sans-serif;
    background: var(--btn-bg); color: var(--tint); box-shadow: inset 0 0 0 0.5px var(--sep);
  }
  .settings-actions button.danger { color: var(--danger); }
  .settings-about {
    padding: 14px 16px 18px; color: var(--text2); font-size: 12px; line-height: 1.55;
  }
  .settings-about b { color: var(--text); font-weight: 650; }
  .settings-path {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 11px; word-break: break-all; color: var(--text2);
  }
</style>
</head>
<body data-theme="light" data-glass="medium">
<div id="app">
  <aside>
    <div class="brand">
      <img class="brand-logo" src="__BRAND_LOGO_SRC__" width="36" height="36" alt="SupTools" draggable="false" />
      <div class="brand-text"><span class="name">SupTools</span><small>超级工具箱</small></div>
    </div>
    <div class="nav" id="nav">
      <button data-page="overview" class="active"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg></span>总览</button>
      <button data-page="clean"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/></svg></span>清理</button>
      <button data-page="uninstall"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3h6l1 2h4v2H4V5h4l1-2z"/><path d="M6 9l1 11a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-11"/><path d="M10 12v6M14 12v6"/></svg></span>卸载</button>
      <button data-page="startup"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v10"/><path d="M8 9l4 4 4-4"/><path d="M5 19h14"/><path d="M7 15h10"/></svg></span>启动项</button>
      <button data-page="shot"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 8h3l2-2h6l2 2h3v11H4V8z"/><circle cx="12" cy="13" r="3.5"/></svg></span>截图</button>
      <button data-page="rec"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg></span>录屏</button>
      <button data-page="perms"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l2.2 2.2L17 4l-.4 2.8L19 9l-2.4.8L17 12.5 14.2 11 12 13.2 9.8 11 7 12.5l.4-2.7L5 9l2.4-.2L7 6l2.8 1.2L12 3z"/><path d="M5 19h14"/><path d="M8 15h8"/></svg></span>权限</button>
      <div class="nav-sep"></div>
      <button data-page="settings"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9c.2.6.7 1 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg></span>设置</button>
    </div>
    <div class="host"><div id="host-name">…</div><span id="meta"></span></div>
  </aside>
  <main>
    <div class="toolbar">
      <h1 id="title">总览</h1>
      <div class="controls">
        <button type="button" class="theme-btn" id="themeBtn" title="切换外观：浅色 / 深色 / 自动">
          <svg class="ico-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg class="ico-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 14.5A8.5 8.5 0 1 1 9.5 3 7 7 0 0 0 21 14.5z"/></svg>
          <svg class="ico-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 3v18"/><path d="M12 3a9 9 0 0 1 0 18"/></svg>
        </button>
        <span>刷新</span>
        <select id="interval">
          <option value="500">0.5s</option>
          <option value="1000" selected>1s</option>
          <option value="2000">2s</option>
        </select>
        <button id="pauseBtn">暂停</button>
      </div>
    </div>
    <div class="hero" id="hero"></div>
    <div class="content">
      <section class="page active" id="page-overview">
        <div class="head"><h2 id="ov-header">加载中…</h2><p id="ov-sub">正在连接本机采集器…</p></div>
        <div class="alerts" id="ov-alerts"></div>
        <div id="ov-stubs" style="position:absolute;width:0;height:0;overflow:hidden;opacity:0;pointer-events:none" aria-hidden="true">
          <span id="ov-chip"></span><span id="ov-cores"></span><span id="ov-load"></span><span id="ov-uptime"></span>
          <span class="pressure-pill" id="ov-pressure"></span><span id="ov-battery"></span><span id="ov-batt-pill"></span>
          <span id="ov-cpu-pct"></span><div id="ov-cpu-ring"></div><div id="ov-cpu-kv"></div><canvas id="ov-cpu-spark"></canvas>
          <span id="ov-mem-pct"></span><span id="ov-mem-used"></span><div id="ov-mem-ring"></div><div id="ov-mem-kv"></div>
          <div id="ov-mem-stack"></div><div id="ov-mem-legend"></div><canvas id="ov-mem-spark"></canvas>
          <span id="ov-net-down"></span><span id="ov-net-up"></span><span id="ov-net-iface"></span><canvas id="ov-net-spark"></canvas>
          <span id="ov-disk-name"></span><span id="ov-disk-pct-label"></span><span id="ov-disk-bar"></span>
          <span id="ov-disk-text"></span><span id="ov-disk-read"></span><span id="ov-disk-write"></span>
        </div>
        <div class="kpi-grid" id="ov-quick">
          <div class="kpi" style="--c:var(--cpu)"><div class="label"><i></i>CPU</div><div class="value" id="q-cpu">—</div><div class="sub" id="q-cpu-s"></div></div>
          <div class="kpi" style="--c:var(--mem)"><div class="label"><i></i>内存</div><div class="value" id="q-mem">—</div><div class="sub" id="q-mem-s"></div></div>
          <div class="kpi" style="--c:var(--down)"><div class="label"><i></i>下行</div><div class="value sm down" id="q-down">—</div><div class="sub" id="q-up"></div></div>
          <div class="kpi" style="--c:var(--disk)"><div class="label"><i></i>磁盘</div><div class="value" id="q-disk">—</div><div class="sub" id="q-disk-s"></div></div>
        </div>
        <div class="section-gap">进程</div>
        <div class="grid">
          <div class="card h-table">
            <div class="card-head">
              <h3><i style="background:var(--cpu)"></i>CPU 最高</h3>
              <button type="button" class="btn-mini danger proc-stop-btn" id="ov-cpu-stop" disabled>一键停止</button>
            </div>
            <table><thead><tr><th class="chk"></th><th class="num">PID</th><th>进程</th><th class="num">CPU</th><th class="num">内存</th><th></th></tr></thead>
            <tbody id="ov-procs"></tbody></table>
          </div>
          <div class="card h-table">
            <div class="card-head">
              <h3><i style="background:var(--mem)"></i>内存最高</h3>
              <button type="button" class="btn-mini danger proc-stop-btn" id="ov-mem-stop" disabled>一键停止</button>
            </div>
            <table><thead><tr><th class="chk"></th><th class="num">PID</th><th>进程</th><th class="num">内存</th><th class="num">CPU</th><th></th></tr></thead>
            <tbody id="ov-mem-procs"></tbody></table>
          </div>
        </div>
      </section>

      <section class="page" id="page-cpu">
        <div class="section-gap">处理器</div>
        <div class="grid cols-3">
          <div class="card h-metric" style="--c:var(--cpu)">
            <h3><i></i>总占用</h3>
            <div class="card-body" style="align-items:center;justify-content:center">
              <div class="ring" id="cpu-ring" style="--c:var(--cpu)"><div><b id="cpu-pct">—</b><small>全部核心</small></div></div>
            </div>
          </div>
          <div class="card h-metric">
            <h3><i style="background:var(--warn)"></i>组成</h3>
            <div class="card-body kv-list" id="cpu-compose-kv"></div>
          </div>
          <div class="card h-chart">
            <h3><i style="background:var(--cpu)"></i>近 60 秒趋势</h3>
            <div class="card-body"><canvas class="spark" id="cpu-spark" style="height:140px;flex:1"></canvas></div>
          </div>
          <div class="card full">
            <h3><i style="background:var(--cpu)"></i>每核心占用</h3>
            <div class="cores" id="cpu-cores"></div>
          </div>
          <div class="card full h-table">
            <div class="card-head">
              <h3><i style="background:var(--cpu)"></i>CPU 占用最高进程</h3>
              <button type="button" class="btn-mini danger proc-stop-btn" id="cpu-top-stop" disabled>一键停止</button>
            </div>
            <table><thead><tr><th class="chk"></th><th class="num">PID</th><th>进程</th><th>用户</th><th class="num">CPU</th><th class="num">内存</th><th></th></tr></thead>
            <tbody id="cpu-top-procs"></tbody></table>
          </div>
        </div>
      </section>

      <section class="page" id="page-memory">
        <div class="section-gap">内存</div>
        <div class="grid cols-3">
          <div class="card h-metric" style="--c:var(--mem)">
            <h3><i></i>压力</h3>
            <div class="card-body" style="align-items:center;justify-content:center">
              <div class="ring" id="mem-ring" style="--c:var(--mem)"><div><b id="mem-pct">—</b><small id="mem-pressure-label">压力</small></div></div>
            </div>
          </div>
          <div class="card h-metric">
            <h3><i style="background:var(--mem)"></i>容量明细</h3>
            <div class="card-body kv-list" id="mem-compose-kv"></div>
          </div>
          <div class="card h-chart">
            <h3><i style="background:var(--mem)"></i>近 60 秒趋势</h3>
            <div class="card-body"><canvas class="spark" id="mem-spark" style="height:140px;flex:1"></canvas></div>
          </div>
          <div class="card full">
            <h3><i style="background:var(--mem)"></i>细分构成</h3>
            <div class="stack" id="mem-stack" style="height:16px"></div>
            <div class="muted" id="mem-breakdown" style="font-family:ui-monospace,Menlo,monospace;margin-top:8px"></div>
          </div>
          <div class="card full h-table">
            <div class="card-head">
              <h3><i style="background:var(--mem)"></i>内存占用最高进程</h3>
              <button type="button" class="btn-mini danger proc-stop-btn" id="mem-top-stop" disabled>一键停止</button>
            </div>
            <table><thead><tr><th class="chk"></th><th class="num">PID</th><th>进程</th><th>用户</th><th class="num">内存</th><th class="num">CPU</th><th></th></tr></thead>
            <tbody id="mem-top-procs"></tbody></table>
          </div>
        </div>
      </section>

      <section class="page" id="page-disk">
        <div class="section-gap">存储</div>
        <div class="grid cols-3">
          <div class="card h-metric" style="--c:var(--disk)">
            <h3><i></i>主磁盘容量</h3>
            <div class="card-body" style="align-items:center;justify-content:center">
              <div class="ring" id="disk-ring" style="--c:var(--disk)"><div><b id="disk-pct">—</b><small id="disk-ring-label">占用</small></div></div>
              <div class="muted" id="disk-cap-text" style="text-align:center;margin-top:10px;font-variant-numeric:tabular-nums"></div>
            </div>
          </div>
          <div class="card h-metric" style="--c:var(--disk)">
            <h3><i></i>读取速度</h3>
            <div class="card-body" style="justify-content:center">
              <div class="big" id="disk-read" style="color:var(--disk)">—</div>
              <div class="muted" style="margin-top:8px">当前读吞吐</div>
            </div>
          </div>
          <div class="card h-metric" style="--c:var(--warn)">
            <h3><i></i>写入速度</h3>
            <div class="card-body" style="justify-content:center">
              <div class="big" id="disk-write" style="color:var(--warn)">—</div>
              <div class="muted" style="margin-top:8px">当前写吞吐</div>
            </div>
          </div>
          <div class="card full h-chart">
            <h3><i style="background:var(--disk)"></i>磁盘吞吐趋势</h3>
            <div class="rate-row" style="margin-bottom:4px">
              <div class="muted">读</div><div class="muted" style="text-align:right">写</div>
            </div>
            <canvas class="spark" id="disk-read-spark"></canvas>
            <canvas class="spark" id="disk-write-spark" style="margin-top:10px"></canvas>
          </div>
          <div class="card full"><h3><i style="background:var(--disk)"></i>存储卷</h3><div class="vols-grid" id="disk-vols"></div></div>
        </div>
      </section>

      <section class="page" id="page-network">
        <div class="grid">
          <div class="card" style="--c:var(--down)">
            <h3><i></i>下载</h3><div class="big down" id="net-down">—</div>
            <canvas class="spark" id="net-down-spark" style="height:84px"></canvas>
          </div>
          <div class="card" style="--c:var(--up)">
            <h3><i></i>上传</h3><div class="big up" id="net-up">—</div>
            <canvas class="spark" id="net-up-spark" style="height:84px"></canvas>
          </div>
          <div class="card full"><h3><i style="background:var(--down)"></i>网卡详情</h3>
            <div class="muted" id="net-summary" style="margin-bottom:8px"></div>
            <table><thead><tr><th>接口</th><th>状态</th><th>IP</th><th class="num">速率</th><th class="num">下行</th><th class="num">上行</th><th class="num">累计↓</th><th class="num">累计↑</th><th class="num">包↓/↑</th></tr></thead>
            <tbody id="net-ifaces"></tbody></table>
          </div>
        </div>
      </section>

      <section class="page" id="page-conn">
        <div class="conn-stage" id="conn-stage">
          <div class="conn-stage-inner">
            <div class="conn-ring" id="conn-ring" style="--p:0;--ring:#0a84ff">
              <svg viewBox="0 0 120 120" aria-hidden="true">
                <circle class="track" cx="60" cy="60" r="54"></circle>
                <circle class="bar" cx="60" cy="60" r="54"></circle>
              </svg>
              <div class="center">
                <div class="score" id="conn-score">—</div>
                <div class="score-unit" id="conn-score-unit">连通指数</div>
              </div>
            </div>
            <div class="conn-copy">
              <div class="eyebrow">Network Check</div>
              <h2 id="conn-title">网络连通性</h2>
              <p class="sub" id="conn-sub">检测 DNS、节点握手与主流站点访问延迟，一键判断当前网络是否畅通。</p>
              <div class="status-line" id="conn-status">
                <span class="conn-pill muted">尚未检测</span>
              </div>
            </div>
            <div class="conn-cta">
              <button type="button" class="btn-primary" id="conn-start">开始检测</button>
              <button type="button" class="btn-ghost" id="conn-cancel" style="display:none">取消</button>
            </div>
          </div>
          <div class="conn-progress" id="conn-progress">
            <div class="row">
              <div class="label" id="conn-prog-label">准备检测…</div>
              <div class="pct" id="conn-prog-pct">0%</div>
            </div>
            <div class="bar"><i id="conn-prog-bar"></i></div>
          </div>
        </div>
        <div class="conn-kpis" id="conn-kpis" style="display:none">
          <div class="conn-kpi"><div class="k">成功率</div><div class="v" id="conn-kpi-rate">—</div><div class="s" id="conn-kpi-rate-s">通过项</div></div>
          <div class="conn-kpi"><div class="k">平均延迟</div><div class="v" id="conn-kpi-avg">—</div><div class="s">毫秒</div></div>
          <div class="conn-kpi"><div class="k">评级</div><div class="v" id="conn-kpi-label">—</div><div class="s" id="conn-kpi-time">—</div></div>
          <div class="conn-kpi"><div class="k">耗时</div><div class="v" id="conn-kpi-elapsed">—</div><div class="s">整轮检测</div></div>
        </div>
        <div class="conn-groups" id="conn-groups">
          <div class="conn-empty" id="conn-empty">
            <b>一键诊断你的网络</b>
            将对阿里 / 腾讯 DNS、Apple / 微软 / Cloudflare 节点，以及百度、腾讯、GitHub 等站点进行连通测试。
          </div>
        </div>
      </section>

      <section class="page" id="page-processes">
        <div class="search">
          <input id="proc-q" placeholder="搜索进程名 / PID / 用户" />
          <label><input type="radio" name="psort" value="cpu" checked /> 按 CPU</label>
          <label><input type="radio" name="psort" value="mem" /> 按内存</label>
          <span class="muted" id="proc-count" style="margin-left:8px"></span>
        </div>
        <div class="proc-toolbar">
          <span class="sel-count" id="proc-sel-count">已选 0</span>
          <button type="button" class="btn-mini" id="proc-sel-all">全选当前</button>
          <button type="button" class="btn-mini" id="proc-sel-none">取消选择</button>
          <button type="button" class="btn-mini danger proc-stop-btn" id="proc-stop-selected" disabled>一键停止</button>
          <button type="button" class="btn-mini danger proc-stop-btn" id="proc-force-selected" disabled style="display:none">强制结束所选</button>
        </div>
        <div class="card">
          <table>
            <thead><tr><th class="chk"><input type="checkbox" id="proc-master-cb" title="全选当前列表" /></th><th class="num">PID</th><th>进程</th><th>用户</th><th class="num">CPU</th><th class="num">内存</th><th class="num">线程</th><th>运行</th><th>状态</th><th></th></tr></thead>
            <tbody id="proc-rows"></tbody>
          </table>
        </div>
      </section>

      <section class="page" id="page-clean">
        <div class="clean-hero">
          <div>
            <div class="muted">可清理空间</div>
            <div class="bytes" id="clean-total">—</div>
            <div class="hint">智能扫描缓存、浏览器、开发工具、Docker、大文件与废纸篓。若扫描不全，请到「工具 → 权限」开启完全磁盘访问。</div>
            <div class="meta">
              <span>安全可清 <b id="clean-safe">0 B</b></span>
              <span>已选 <b id="clean-selected">0 B</b></span>
              <span>项目 <b id="clean-count">0</b></span>
              <span>已勾选 <b id="clean-sel-count">0</b></span>
            </div>
            <div class="clean-insights" id="clean-insights"></div>
            <div class="clean-stack" id="clean-stack" title="分类占比"></div>
          </div>
          <div class="clean-actions">
            <button class="btn-ghost" id="clean-scan">开始扫描</button>
            <button class="btn-ghost" id="clean-recommend" type="button" disabled>智能勾选</button>
            <button class="btn-ghost" id="clean-empty-trash" type="button" disabled>清空废纸篓</button>
            <button class="btn-primary" id="clean-smart" disabled>清理所选</button>
          </div>
        </div>
        <div class="clean-success" id="clean-success">
          <div class="t" id="clean-success-t">清理完成</div>
          <div class="s" id="clean-success-s"></div>
        </div>
        <div class="clean-progress" id="clean-progress">
          <div class="row">
            <div class="label" id="clean-prog-label">准备扫描…</div>
            <div style="display:flex;gap:10px;align-items:center">
              <div class="pct" id="clean-prog-pct">0%</div>
              <button class="btn-mini dim" id="clean-cancel" type="button">取消</button>
            </div>
          </div>
          <div class="bar"><i id="clean-prog-bar"></i></div>
          <div class="current" id="clean-prog-current">—</div>
          <div class="stats">
            <span id="clean-prog-found">已发现 0 项</span>
            <span id="clean-prog-bytes">0 B</span>
          </div>
        </div>
        <div class="card">
          <div class="clean-toolbar">
            <div class="left">
              <input class="clean-search" id="clean-q" placeholder="搜索名称或路径…" />
              <select class="clean-select" id="clean-sort">
                <option value="size">按大小</option>
                <option value="name">按名称</option>
                <option value="risk">谨慎优先</option>
              </select>
              <select class="clean-select" id="clean-minsize">
                <option value="0">全部大小</option>
                <option value="1048576">≥ 1 MB</option>
                <option value="10485760">≥ 10 MB</option>
                <option value="104857600">≥ 100 MB</option>
              </select>
              <select class="clean-select" id="clean-risk">
                <option value="all">全部风险</option>
                <option value="safe">仅安全</option>
                <option value="caution">仅谨慎</option>
              </select>
            </div>
            <div class="right">
              <button class="btn-mini" id="clean-sel-safe" type="button">仅安全项</button>
              <button class="btn-mini" id="clean-sel-all" type="button">全选</button>
              <button class="btn-mini" id="clean-sel-none" type="button">取消全选</button>
              <button class="btn-mini" id="clean-expand" type="button">展开全部</button>
              <label class="clean-toggle"><input type="checkbox" id="clean-trash-mode" checked /> 移至废纸篓</label>
            </div>
          </div>
          <div class="clean-cat-filters" id="clean-cat-filters"></div>
          <div class="clean-cats" id="clean-list">
            <div class="clean-empty" id="clean-welcome">
              <div class="art"><svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/></svg></div>
              <div class="big">专业系统清理</div>
              覆盖缓存、Safari / 浏览器、Xcode / Docker、大文件发现与废纸篓。<br/>点击「开始扫描」查看可清理空间，再用「智能勾选」一键选中安全项。
            </div>
          </div>
          <div class="clean-history" id="clean-history" style="display:none">
            <h4>最近清理</h4>
            <div id="clean-history-rows"></div>
          </div>
        </div>
      </section>

      <section class="page" id="page-uninstall">
        <div class="un-hero">
          <div>
            <div class="muted">已安装应用</div>
            <div class="bytes" id="un-total">—</div>
            <div class="hint">扫描 Applications 中的应用，并查找偏好设置、缓存、容器等关联残留。若残留扫不全，请到「工具 → 权限」开启完全磁盘访问。</div>
            <div class="meta">
              <span>应用 <b id="un-count">0</b></span>
              <span>可卸载 <b id="un-removable">0</b></span>
              <span>已选释放 <b id="un-selected">0 B</b></span>
            </div>
          </div>
          <div class="un-actions">
            <button class="btn-ghost" id="un-scan" type="button">扫描应用</button>
            <button class="btn-ghost" id="un-cancel" type="button" style="visibility:hidden">取消</button>
          </div>
        </div>
        <div class="un-success" id="un-success">
          <div class="t" id="un-success-t">卸载完成</div>
          <div class="s" id="un-success-s"></div>
        </div>
        <div class="un-progress" id="un-progress">
          <div class="row">
            <div class="label" id="un-prog-label">准备扫描…</div>
            <div class="pct" id="un-prog-pct">0%</div>
          </div>
          <div class="bar"><i id="un-prog-bar"></i></div>
          <div class="current" id="un-prog-current">—</div>
        </div>
        <div class="un-layout">
          <div class="un-pane">
            <div class="un-pane-head">
              <div class="title">应用列表</div>
              <input class="un-search" id="un-q" placeholder="搜索应用…" />
              <select class="un-select" id="un-sort">
                <option value="size">按大小</option>
                <option value="name">按名称</option>
                <option value="recent">最近使用</option>
              </select>
              <select class="un-select" id="un-filter">
                <option value="all">全部</option>
                <option value="removable">可卸载</option>
                <option value="user">用户目录</option>
              </select>
            </div>
            <div class="un-apps" id="un-apps">
              <div class="un-detail-empty">
                <div class="big">扫描已安装应用</div>
                点击「扫描应用」开始，选择应用后可查看并勾选关联文件。
              </div>
            </div>
          </div>
          <div class="un-pane">
            <div class="un-pane-head">
              <div class="title">关联文件</div>
              <button class="btn-mini" id="un-sel-safe" type="button">仅安全项</button>
              <button class="btn-mini" id="un-sel-all" type="button">全选</button>
              <button class="btn-mini" id="un-sel-none" type="button">取消全选</button>
            </div>
            <div class="un-leftovers" id="un-leftovers">
              <div class="un-detail-empty" id="un-detail-empty">
                <div class="big">选择左侧应用</div>
                将自动扫描偏好设置、缓存、Application Support、容器等残留。
              </div>
            </div>
            <div class="un-foot">
              <div class="sum">预计释放 <b id="un-free">0 B</b> · <span id="un-item-count">0</span> 项</div>
              <label class="clean-toggle"><input type="checkbox" id="un-trash-mode" checked /> 移至废纸篓</label>
              <button class="btn-primary" id="un-run" type="button" disabled>卸载所选</button>
            </div>
          </div>
        </div>
      </section>

      <section class="page" id="page-startup">
        <div class="su-hero">
          <div>
            <div class="muted">启动项 / 开机服务</div>
            <div class="bytes" id="su-total">—</div>
            <div class="hint">管理登录时自动启动的应用与 LaunchAgent。关闭后下次登录不再自动运行；系统级项目可能需要管理员权限。完整权限请到「工具 → 权限」查看。</div>
            <div class="meta">
              <span>启用中 <b id="su-enabled">0</b></span>
              <span>已禁用 <b id="su-disabled">0</b></span>
              <span>登录项 <b id="su-login">0</b></span>
              <span>服务 <b id="su-agents">0</b></span>
            </div>
          </div>
          <div class="su-actions">
            <button class="btn-ghost" id="su-settings" type="button">系统登录项</button>
            <button class="btn-ghost" id="su-scan" type="button">扫描启动项</button>
          </div>
        </div>
        <div class="su-toast" id="su-toast">
          <div class="t" id="su-toast-t">操作完成</div>
          <div class="s" id="su-toast-s"></div>
        </div>
        <div class="su-progress" id="su-progress">
          <div class="row">
            <div class="label" id="su-prog-label">准备扫描…</div>
            <div class="pct" id="su-prog-pct">0%</div>
          </div>
          <div class="bar"><i id="su-prog-bar"></i></div>
          <div class="current" id="su-prog-current">—</div>
        </div>
        <div class="su-toolbar">
          <input class="su-search" id="su-q" placeholder="搜索名称、标签或路径…" />
          <select class="su-select" id="su-filter">
            <option value="all">全部</option>
            <option value="enabled">仅启用</option>
            <option value="disabled">仅禁用</option>
            <option value="login">登录项</option>
            <option value="agent">LaunchAgent</option>
            <option value="user">用户级</option>
          </select>
        </div>
        <div class="su-list" id="su-list">
          <div class="su-empty">
            <div class="big">扫描开机启动项</div>
            点击「扫描启动项」查看可关闭的登录应用与后台服务。
          </div>
        </div>
      </section>

      <section class="page" id="page-perms">
        <div class="perm-page-hero">
          <div>
            <div class="muted">权限引导</div>
            <div class="bytes" id="perm-summary-count">—</div>
            <div class="hint">工具功能依赖系统隐私权限。开启后返回本页会自动检测；每一项成功开启都会提示「已开启」。</div>
            <div class="meta">
              <span>推荐已开 <b id="perm-required-ok">0</b>/<b id="perm-required-total">0</b></span>
              <span>全部已开 <b id="perm-granted">0</b>/<b id="perm-total">0</b></span>
            </div>
          </div>
          <div class="su-actions">
            <button class="btn-ghost" id="perm-refresh" type="button">重新检测</button>
          </div>
        </div>
        <div class="perm-all-ok" id="perm-all-ok">
          <div class="t">推荐权限已全部开启</div>
          <div class="s">截图、录屏快捷键与启动项相关权限已就绪。可选权限可按需开启以获得更完整清理/卸载扫描。</div>
        </div>
        <div class="perm-toast" id="perm-toast">
          <div class="t" id="perm-toast-t">已开启</div>
          <div class="s" id="perm-toast-s"></div>
        </div>
        <div class="perm-list" id="perm-list">
          <div class="su-empty"><div class="big">正在检测权限…</div>请稍候</div>
        </div>
      </section>

      <section class="page" id="page-shot">
        <div class="head">
          <h2>截图工具</h2>
          <p>框选、窗口或全屏截图后进入标记编辑：画笔、箭头、矩形、文字、马赛克，再保存或复制。</p>
        </div>
        <div class="shot-busy-banner" id="shot-busy">正在截图… 选择区域后松开鼠标；按 Esc 取消。</div>
        <div class="shot-actions">
          <button type="button" class="shot-action" data-mode="selection" id="shot-sel">
            <div class="ico-lg"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/><rect x="8" y="8" width="8" height="8" rx="1"/></svg></div>
            <div class="t">框选截图</div>
            <div class="d">拖拽选择区域；空格切换窗口模式</div>
            <div class="d" style="margin-top:8px;font:700 12px/1 ui-monospace,Menlo,monospace;color:var(--tint)" id="shot-hk-sel-label">⌃⌘4</div>
          </button>
          <button type="button" class="shot-action" data-mode="window" id="shot-win">
            <div class="ico-lg"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18"/></svg></div>
            <div class="t">窗口截图</div>
            <div class="d">交互选取窗口（可按空格）</div>
            <div class="d" style="margin-top:8px;font:700 12px/1 ui-monospace,Menlo,monospace;color:var(--tint)" id="shot-hk-win-label">⌃⌘5</div>
          </button>
          <button type="button" class="shot-action" data-mode="full" id="shot-full">
            <div class="ico-lg"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M8 20h8"/></svg></div>
            <div class="t">全屏截图</div>
            <div class="d">捕获主显示器整屏画面</div>
            <div class="d" style="margin-top:8px;font:700 12px/1 ui-monospace,Menlo,monospace;color:var(--tint)" id="shot-hk-full-label">⌃⌘3</div>
          </button>
        </div>
        <div class="shot-hotkeys" id="shot-hotkeys">
          <div class="hk-card">
            <div class="hk-title">框选快捷键</div>
            <div class="hk-row">
              <button type="button" class="hk-btn" data-hk="hotkey_shot_selection" id="hk-btn-selection">⌃⌘4</button>
              <button type="button" class="btn-mini" data-hk-clear="hotkey_shot_selection">清除</button>
            </div>
          </div>
          <div class="hk-card">
            <div class="hk-title">窗口快捷键</div>
            <div class="hk-row">
              <button type="button" class="hk-btn" data-hk="hotkey_shot_window" id="hk-btn-window">⌃⌘5</button>
              <button type="button" class="btn-mini" data-hk-clear="hotkey_shot_window">清除</button>
            </div>
          </div>
          <div class="hk-card">
            <div class="hk-title">全屏快捷键</div>
            <div class="hk-row">
              <button type="button" class="hk-btn" data-hk="hotkey_shot_full" id="hk-btn-full">⌃⌘3</button>
              <button type="button" class="btn-mini" data-hk-clear="hotkey_shot_full">清除</button>
            </div>
          </div>
        </div>
        <div class="hk-hint" id="shot-hk-hint">点击上方按键位可录制新快捷键；Esc 取消，Delete 清除。默认 ⌃⌘3 / 4 / 5，避免与系统 ⌘⇧ 截图冲突。</div>
        <div class="shot-opts">
          <label><input type="checkbox" id="shot-hide" checked /> 截图前隐藏本窗口</label>
          <label><input type="checkbox" id="shot-clip" /> 保存时同时复制到剪贴板</label>
          <label><input type="checkbox" id="shot-cursor" /> 包含鼠标指针（全屏）</label>
          <label>延迟
            <select id="shot-delay">
              <option value="0">无</option>
              <option value="0.5" selected>0.5 秒</option>
              <option value="1">1 秒</option>
              <option value="2">2 秒</option>
              <option value="3">3 秒</option>
            </select>
          </label>
          <button type="button" class="btn-mini" id="shot-folder">打开保存文件夹</button>
        </div>
        <div class="shot-hero">
          <div class="card" style="min-height:auto">
            <h3><i style="background:var(--tint)"></i>最近预览</h3>
            <div class="shot-preview" id="shot-preview">
              <div class="empty"><b>还没有截图</b>点击上方按钮开始</div>
            </div>
            <div class="shot-meta" id="shot-meta"></div>
          </div>
          <div class="card" style="min-height:auto">
            <div class="card-head">
              <h3><i style="background:var(--disk)"></i>最近文件</h3>
              <button type="button" class="btn-mini" id="shot-refresh">刷新</button>
            </div>
            <div class="muted" id="shot-folder-path" style="margin-bottom:8px;font-family:ui-monospace,Menlo,monospace;font-size:11px">—</div>
            <div class="shot-list" id="shot-list"></div>
          </div>
        </div>
        <div class="perm-banner" id="shot-perm-banner">
          <div class="txt"><b>需要屏幕录制权限</b>截图前请允许 SupTools 访问屏幕。</div>
          <button type="button" class="btn-mini" data-perm="screen">权限引导</button>
        </div>
        <div class="muted" style="margin-top:8px;line-height:1.5">
          无法截图？<button type="button" class="perm-link" data-perm="screen">打开权限引导</button>
        </div>
      </section>

      <section class="page" id="page-rec">
        <div class="head">
          <h2>屏幕录制</h2>
          <p>区域或全屏录制，可选麦克风 / 系统音频与点击高亮；结束后预览再保存到「影片 / SupTools」。</p>
        </div>
        <div class="rec-live" id="rec-live">
          <div class="left">
            <div class="dot"></div>
            <div>
              <div class="timer" id="rec-timer">0:00</div>
              <div class="msg" id="rec-live-msg">正在录制…</div>
            </div>
          </div>
          <button type="button" class="btn-stop" id="rec-stop">停止录制</button>
        </div>
        <div class="shot-actions">
          <button type="button" class="shot-action" data-rec-mode="selection" id="rec-sel">
            <div class="ico-lg"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3" fill="currentColor"/><path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/></svg></div>
            <div class="t">区域录屏</div>
            <div class="d">拖拽选择要录制的屏幕区域</div>
            <div class="d" style="margin-top:8px;font:700 12px/1 ui-monospace,Menlo,monospace;color:var(--tint)" id="rec-hk-sel-label">⌃⌘6</div>
          </button>
          <button type="button" class="shot-action" data-rec-mode="full" id="rec-full">
            <div class="ico-lg"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><circle cx="12" cy="12" r="3.5"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/></svg></div>
            <div class="t">全屏录屏</div>
            <div class="d">录制主显示器整屏画面</div>
            <div class="d" style="margin-top:8px;font:700 12px/1 ui-monospace,Menlo,monospace;color:var(--tint)" id="rec-hk-full-label">⌃⌘7</div>
          </button>
          <button type="button" class="shot-action" id="rec-stop-card" disabled>
            <div class="ico-lg"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="7" y="7" width="10" height="10" rx="1.5" fill="currentColor"/></svg></div>
            <div class="t">停止录制</div>
            <div class="d">结束当前录制并进入预览</div>
            <div class="d" style="margin-top:8px;font:700 12px/1 ui-monospace,Menlo,monospace;color:var(--tint)" id="rec-hk-stop-label">⌃⌘8</div>
          </button>
        </div>
        <div class="shot-hotkeys">
          <div class="hk-card">
            <div class="hk-title">区域录屏快捷键</div>
            <div class="hk-row">
              <button type="button" class="hk-btn" data-hk="hotkey_rec_selection" id="hk-btn-rec-sel">⌃⌘6</button>
              <button type="button" class="btn-mini" data-hk-clear="hotkey_rec_selection">清除</button>
            </div>
          </div>
          <div class="hk-card">
            <div class="hk-title">全屏录屏快捷键</div>
            <div class="hk-row">
              <button type="button" class="hk-btn" data-hk="hotkey_rec_full" id="hk-btn-rec-full">⌃⌘7</button>
              <button type="button" class="btn-mini" data-hk-clear="hotkey_rec_full">清除</button>
            </div>
          </div>
          <div class="hk-card">
            <div class="hk-title">停止录屏快捷键</div>
            <div class="hk-row">
              <button type="button" class="hk-btn" data-hk="hotkey_rec_stop" id="hk-btn-rec-stop">⌃⌘8</button>
              <button type="button" class="btn-mini" data-hk-clear="hotkey_rec_stop">清除</button>
            </div>
          </div>
        </div>
        <div class="hk-hint" id="rec-hk-hint">默认 ⌃⌘6 / 7 / 8。菜单栏也可随时停止录制。</div>
        <div class="shot-opts">
          <label><input type="checkbox" id="rec-hide" checked /> 录制前隐藏本窗口</label>
          <label><input type="checkbox" id="rec-mic" /> 麦克风</label>
          <label><input type="checkbox" id="rec-sysaudio" /> 系统音频</label>
          <label><input type="checkbox" id="rec-clicks" checked /> 显示鼠标点击</label>
          <label><input type="checkbox" id="rec-open-after" /> 保存后打开</label>
          <label>倒计时
            <select id="rec-countdown-sel">
              <option value="0">无</option>
              <option value="3" selected>3 秒</option>
              <option value="5">5 秒</option>
            </select>
          </label>
          <label>最长
            <select id="rec-max">
              <option value="0" selected>不限</option>
              <option value="30">30 秒</option>
              <option value="60">1 分钟</option>
              <option value="180">3 分钟</option>
              <option value="600">10 分钟</option>
            </select>
          </label>
          <button type="button" class="btn-mini" id="rec-folder">打开保存文件夹</button>
        </div>
        <div class="shot-hero">
          <div class="card" style="min-height:auto">
            <h3><i style="background:#ff3b30"></i>最近预览</h3>
            <div class="shot-preview" id="rec-preview">
              <div class="empty"><b>还没有录屏</b>选择区域或全屏开始录制</div>
            </div>
            <div class="shot-meta" id="rec-meta"></div>
          </div>
          <div class="card" style="min-height:auto">
            <div class="card-head">
              <h3><i style="background:var(--disk)"></i>最近文件</h3>
              <button type="button" class="btn-mini" id="rec-refresh">刷新</button>
            </div>
            <div class="muted" id="rec-folder-path" style="margin-bottom:8px;font-family:ui-monospace,Menlo,monospace;font-size:11px">—</div>
            <div class="shot-list" id="rec-list"></div>
          </div>
        </div>
        <div class="perm-banner" id="rec-perm-banner">
          <div class="txt"><b>需要屏幕录制权限</b>录屏前请允许 SupTools；麦克风另需麦克风权限。</div>
          <button type="button" class="btn-mini" data-perm="screen">权限引导</button>
        </div>
        <div class="muted" style="margin-top:8px;line-height:1.5">
          无法录屏？<button type="button" class="perm-link" data-perm="screen">打开权限引导</button>
          · 麦克风无声？<button type="button" class="perm-link" data-perm="microphone">麦克风权限</button>
          · 文件保存为 .mov
        </div>
      </section>

      <section class="page" id="page-settings">
        <div class="settings-page">
          <div class="head"><h2>设置中心</h2><p>外观、任务栏、清理与安全选项，即时生效并自动保存。</p></div>

          <div class="settings-group">
            <h3>外观</h3>
            <div class="settings-row" style="align-items:flex-start">
              <div><div class="label">主题</div><span class="desc">选择浅色、深色或跟随系统</span></div>
              <div class="theme-cards" id="set-theme">
                <button type="button" class="theme-card" data-v="light"><div class="preview light"></div>浅色</button>
                <button type="button" class="theme-card" data-v="dark"><div class="preview dark"></div>深色</button>
                <button type="button" class="theme-card" data-v="system"><div class="preview system"></div>自动</button>
              </div>
            </div>
            <div class="settings-row" style="align-items:flex-start">
              <div><div class="label">透明度</div><span class="desc">窗口毛玻璃透明程度</span></div>
              <div class="glass-cards" id="set-glass">
                <button type="button" class="glass-card" data-v="opaque"><div class="preview opaque"></div>实心</button>
                <button type="button" class="glass-card" data-v="medium"><div class="preview medium"></div>毛玻璃</button>
                <button type="button" class="glass-card" data-v="clear"><div class="preview clear"></div>高透</button>
              </div>
            </div>
            <div class="settings-row">
              <div><div class="label">刷新间隔</div><span class="desc">指标采集频率（越快越耗电）</span></div>
              <select id="set-refresh">
                <option value="500">0.5 秒</option>
                <option value="1000">1 秒</option>
                <option value="2000">2 秒</option>
                <option value="3000">3 秒</option>
                <option value="5000">5 秒</option>
              </select>
            </div>
            <div class="settings-row">
              <div><div class="label">总览告警条</div><span class="desc">指标偏高时在总览显示提示</span></div>
              <label class="switch"><input type="checkbox" id="set-alerts" /><span></span></label>
            </div>
            <div class="settings-row">
              <div><div class="label">系统通知</div><span class="desc">达到阈值时推送到通知中心（同类 App 标配）</span></div>
              <label class="switch"><input type="checkbox" id="set-notify" /><span></span></label>
            </div>
            <div class="settings-row">
              <div><div class="label">CPU 告警阈值</div><span class="desc">占用 ≥ 此值时告警（%）</span></div>
              <input type="number" id="set-alert-cpu" min="50" max="100" step="1" />
            </div>
            <div class="settings-row">
              <div><div class="label">内存告警阈值</div><span class="desc">占用 ≥ 此值时告警（%）</span></div>
              <input type="number" id="set-alert-mem" min="50" max="100" step="1" />
            </div>
            <div class="settings-row">
              <div><div class="label">磁盘告警阈值</div><span class="desc">占用 ≥ 此值时告警（%）</span></div>
              <input type="number" id="set-alert-disk" min="50" max="100" step="1" />
            </div>
            <div class="settings-row">
              <div><div class="label">电池告警阈值</div><span class="desc">未充电且电量 ≤ 此值时告警（%）</span></div>
              <input type="number" id="set-alert-battery" min="5" max="50" step="1" />
            </div>
          </div>

          <div class="settings-group">
            <h3>超级右键 · Finder</h3>
            <div class="settings-row">
              <div>
                <div class="label">新建文本文档</div>
                <span class="desc">在 Finder 右键菜单加入「新建文本文档 / 在此新建文本文档」</span>
              </div>
              <label class="switch"><input type="checkbox" id="set-finder-newtxt" /><span></span></label>
            </div>
            <div class="settings-row">
              <div><div class="label">创建后打开</div><span class="desc">用默认文本编辑器打开新建的 .txt</span></div>
              <label class="switch"><input type="checkbox" id="set-finder-newtxt-open" /><span></span></label>
            </div>
            <div class="settings-row">
              <div><div class="label">立即新建</div><span class="desc">在当前 Finder 窗口文件夹创建</span></div>
              <button type="button" class="btn-mini" id="set-finder-newtxt-now">新建一个</button>
            </div>
            <div class="hint" id="set-finder-newtxt-hint">启用后出现在：Finder 右键 → 快速操作 / 服务。若看不到，到「系统设置 → 键盘 → 键盘快捷键 → 服务」勾选 SupTools 相关项。</div>
          </div>

          <div class="settings-group">
            <h3>截图快捷键</h3>
            <div class="settings-row">
              <div><div class="label">框选截图</div><span class="desc">全局快捷键（后台也可用）</span></div>
              <div style="display:flex;gap:8px;align-items:center">
                <button type="button" class="hk-btn" style="min-width:120px" data-hk="hotkey_shot_selection" id="set-hk-selection">⌃⌘4</button>
                <button type="button" class="btn-mini" data-hk-clear="hotkey_shot_selection">清除</button>
              </div>
            </div>
            <div class="settings-row">
              <div><div class="label">窗口截图</div><span class="desc">点击后按下新组合键即可绑定</span></div>
              <div style="display:flex;gap:8px;align-items:center">
                <button type="button" class="hk-btn" style="min-width:120px" data-hk="hotkey_shot_window" id="set-hk-window">⌃⌘5</button>
                <button type="button" class="btn-mini" data-hk-clear="hotkey_shot_window">清除</button>
              </div>
            </div>
            <div class="settings-row">
              <div><div class="label">全屏截图</div><span class="desc">Esc 取消录制 · Delete 清除</span></div>
              <div style="display:flex;gap:8px;align-items:center">
                <button type="button" class="hk-btn" style="min-width:120px" data-hk="hotkey_shot_full" id="set-hk-full">⌃⌘3</button>
                <button type="button" class="btn-mini" data-hk-clear="hotkey_shot_full">清除</button>
              </div>
            </div>
            <div class="hint" id="set-hk-hint">若后台快捷键无效，请到「工具 → 权限」开启辅助功能与屏幕录制。</div>
            <div style="margin-top:10px">
              <button type="button" class="btn-mini" data-page-jump="perms">打开权限引导</button>
              <button type="button" class="btn-mini" data-perm="accessibility" style="margin-left:6px">辅助功能</button>
              <button type="button" class="btn-mini" data-perm="screen" style="margin-left:6px">屏幕录制</button>
            </div>
          </div>

          <div class="settings-group">
            <h3>菜单栏</h3>
            <div class="settings-row">
              <div><div class="label">显示模式</div><span class="desc">状态栏标题内容</span></div>
              <select id="set-menubar-mode">
                <option value="net">网络吞吐</option>
                <option value="net_m">网络（固定 M）</option>
                <option value="cpu_net">CPU · 网络</option>
                <option value="cpu">仅 CPU%</option>
                <option value="memory">仅内存%</option>
                <option value="compact">CPU · 内存</option>
                <option value="disk">磁盘可用</option>
                <option value="battery">电池</option>
                <option value="spark">CPU 波形</option>
              </select>
            </div>
            <div class="settings-row">
              <div><div class="label">显示状态图标</div><span class="desc">在网速文字旁显示小图标</span></div>
              <label class="switch"><input type="checkbox" id="set-menubar-icon" /><span></span></label>
            </div>
            <div class="settings-row">
              <div><div class="label">启动时隐藏面板</div><span class="desc">仅保留菜单栏，需要时再打开窗口</span></div>
              <label class="switch"><input type="checkbox" id="set-start-hidden" /><span></span></label>
            </div>
            <div class="settings-row">
              <div><div class="label">登录时启动</div><span class="desc">通过 LaunchAgent 在登录后自动打开</span></div>
              <label class="switch"><input type="checkbox" id="set-login" /><span></span></label>
            </div>
          </div>

          <div class="settings-group">
            <h3>清理</h3>
            <div class="settings-row">
              <div><div class="label">默认移至废纸篓</div><span class="desc">清理时优先可恢复删除</span></div>
              <label class="switch"><input type="checkbox" id="set-clean-trash" /><span></span></label>
            </div>
            <div class="settings-row">
              <div><div class="label">清理前确认</div><span class="desc">执行清理前弹出确认对话框</span></div>
              <label class="switch"><input type="checkbox" id="set-clean-confirm" /><span></span></label>
            </div>
          </div>

          <div class="settings-group">
            <h3>安全</h3>
            <p class="hint">进程操作可能影响正在运行的软件，请谨慎开启。</p>
            <div class="settings-row">
              <div><div class="label">结束进程前确认</div><span class="desc">「结束 / 强退」前弹出系统确认</span></div>
              <label class="switch"><input type="checkbox" id="set-proc-confirm" /><span></span></label>
            </div>
            <div class="settings-row">
              <div><div class="label">允许强制结束</div><span class="desc">关闭后隐藏「强退」并拒绝强制 kill</span></div>
              <label class="switch"><input type="checkbox" id="set-force-kill" /><span></span></label>
            </div>
          </div>

          <div class="settings-group">
            <h3>关于</h3>
            <div class="settings-about">
              <div><b>SupTools</b> <span id="set-version">—</span></div>
              <div style="margin-top:8px">本机系统监控 · 菜单栏网速 · 垃圾清理</div>
              <div style="margin-top:10px">应用路径</div>
              <div class="settings-path" id="set-app-path">—</div>
              <div style="margin-top:8px">配置文件</div>
              <div class="settings-path" id="set-config-path">—</div>
            </div>
          </div>

          <div class="settings-actions">
            <button type="button" id="set-reveal-config">在 Finder 显示配置</button>
            <button type="button" class="danger" id="set-reset">恢复默认设置</button>
          </div>
        </div>
      </section>
    </div>
    <div class="statusbar" id="status">正在采集…</div>
  </main>
</div>
<div class="rec-countdown" id="rec-countdown" aria-hidden="true">
  <div class="n" id="rec-countdown-n">3</div>
  <div class="t">即将开始录制</div>
</div>
<div class="rec-editor" id="rec-editor" aria-hidden="true">
  <div class="shot-ed-top">
    <div>
      <div class="title">录制预览</div>
      <div class="hint">确认无误后保存到「影片 / SupTools」· Esc 丢弃</div>
    </div>
  </div>
  <div class="rec-ed-stage">
    <div class="rec-ed-card">
      <div class="rec-ed-poster" id="rec-ed-poster">
        <button type="button" class="play" id="rec-ed-play" title="用 QuickTime 播放">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        </button>
      </div>
      <div class="rec-ed-info">
        <div class="name" id="rec-ed-name">Recording</div>
        <div class="meta" id="rec-ed-meta">—</div>
      </div>
    </div>
  </div>
  <div class="shot-ed-bottom">
    <div class="left" id="rec-ed-hint">未保存草稿</div>
    <div class="right">
      <button type="button" class="btn-ghost" id="rec-ed-cancel">丢弃</button>
      <button type="button" class="btn-ghost" id="rec-ed-reveal">显示</button>
      <button type="button" class="btn-primary" id="rec-ed-save">保存</button>
    </div>
  </div>
</div>
<div class="shot-editor" id="shot-editor" aria-hidden="true">
  <div class="shot-ed-top">
    <div>
      <div class="title">标记截图</div>
      <div class="hint">画完后可保存到「图片 / SupTools」，或先复制到剪贴板 · Esc 取消</div>
    </div>
  </div>
  <div class="shot-ed-tools" id="shot-ed-tools">
    <button type="button" class="shot-ed-tool active" data-tool="pen" title="画笔">画笔</button>
    <button type="button" class="shot-ed-tool" data-tool="highlight" title="荧光笔">高亮</button>
    <button type="button" class="shot-ed-tool" data-tool="rect" title="矩形">矩形</button>
    <button type="button" class="shot-ed-tool" data-tool="ellipse" title="椭圆">椭圆</button>
    <button type="button" class="shot-ed-tool" data-tool="arrow" title="箭头">箭头</button>
    <button type="button" class="shot-ed-tool" data-tool="text" title="文字">文字</button>
    <button type="button" class="shot-ed-tool" data-tool="mosaic" title="马赛克">马赛克</button>
    <span class="shot-ed-sep"></span>
    <span class="shot-ed-colors" id="shot-ed-colors">
      <button type="button" class="shot-ed-color active" data-color="#ff3b30" style="background:#ff3b30" title="红"></button>
      <button type="button" class="shot-ed-color" data-color="#ff9f0a" style="background:#ff9f0a" title="橙"></button>
      <button type="button" class="shot-ed-color" data-color="#ffd60a" style="background:#ffd60a" title="黄"></button>
      <button type="button" class="shot-ed-color" data-color="#30d158" style="background:#30d158" title="绿"></button>
      <button type="button" class="shot-ed-color" data-color="#0a84ff" style="background:#0a84ff" title="蓝"></button>
      <button type="button" class="shot-ed-color" data-color="#ffffff" style="background:#fff" title="白"></button>
      <button type="button" class="shot-ed-color" data-color="#1c1c1e" style="background:#1c1c1e" title="黑"></button>
    </span>
    <span class="shot-ed-sep"></span>
    <input type="range" class="shot-ed-size" id="shot-ed-size" min="2" max="28" value="4" title="粗细" />
    <span class="shot-ed-sep"></span>
    <button type="button" class="shot-ed-chip" id="shot-ed-undo" title="撤销">撤销</button>
    <button type="button" class="shot-ed-chip" id="shot-ed-redo" title="重做">重做</button>
    <button type="button" class="shot-ed-chip" id="shot-ed-clear" title="清空标记">清空</button>
  </div>
  <div class="shot-ed-stage">
    <div class="shot-ed-canvas-wrap" id="shot-ed-wrap">
      <canvas id="shot-ed-canvas"></canvas>
    </div>
  </div>
  <div class="shot-ed-bottom">
    <div class="left" id="shot-ed-meta">未命名草稿</div>
    <div class="right">
      <button type="button" class="btn-ghost" id="shot-ed-cancel">取消</button>
      <button type="button" class="btn-ghost" id="shot-ed-copy">复制</button>
      <button type="button" class="btn-primary" id="shot-ed-save">保存</button>
    </div>
  </div>
</div>
<div class="shot-toast" id="shot-toast"></div>
<div class="modal-backdrop" id="clean-modal">
  <div class="modal">
    <h3 id="clean-modal-title">确认清理</h3>
    <p id="clean-modal-body">将删除已勾选的项目。</p>
    <div class="warn-box" id="clean-modal-warn" style="display:none"></div>
    <div class="actions">
      <button class="btn-ghost" id="clean-modal-cancel" type="button">取消</button>
      <button class="btn-danger" id="clean-modal-ok" type="button">确认清理</button>
    </div>
  </div>
</div>
<div class="modal-backdrop" id="un-modal">
  <div class="modal">
    <h3 id="un-modal-title">确认卸载</h3>
    <p id="un-modal-body">将卸载所选应用及相关文件。</p>
    <div class="warn-box" id="un-modal-warn" style="display:none"></div>
    <div class="actions">
      <button class="btn-ghost" id="un-modal-cancel" type="button">取消</button>
      <button class="btn-danger" id="un-modal-ok" type="button">确认卸载</button>
    </div>
  </div>
</div>
<div class="modal-backdrop" id="perm-modal">
  <div class="modal">
    <div class="perm-ico" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M8 20h8"/><path d="M12 11v3M12 8h.01"/></svg>
    </div>
    <h3 id="perm-modal-title">需要权限</h3>
    <p id="perm-modal-sub">请在系统设置中允许 SupTools。</p>
    <ol class="steps" id="perm-modal-steps"></ol>
    <div class="actions">
      <button class="btn-ghost" id="perm-modal-close" type="button">我知道了</button>
      <button class="btn-primary" id="perm-modal-open" type="button">打开系统设置</button>
    </div>
  </div>
</div>
<script>
const TITLES = {overview:'总览',cpu:'CPU',memory:'内存',disk:'硬盘',network:'网络',conn:'连通性',processes:'进程',clean:'清理',uninstall:'卸载',startup:'启动项',perms:'权限',shot:'截图',rec:'录屏',settings:'设置'};
let state = null;
let paused = false;
let page = 'overview';
let cleanItems = [];
let cleanCategories = [];
let cleanBusy = false;
let cleanExpanded = {};
let cleanHistory = [];
let cleanMoveToTrash = true;
let cleanConfirm = true;
let cleanPendingIds = null;
let cleanRecommendIds = [];
let cleanCatFilter = 'all';
let cleanInsights = [];
let unApps = [];
let unBusy = false;
let unSelectedPath = '';
let unItems = [];
let unAppDetail = null;
let unPendingItems = null;
let unMoveToTrash = true;
let suItems = [];
let suBusy = false;
let suMeta = {};
let connBusy = false;
let connData = null;
let appSettings = {
  theme: 'light',
  glass: 'medium',
  menubar_mode: 'net',
  refresh_ms: 1000,
  clean_move_to_trash: true,
  clean_confirm: true,
  start_hidden: false,
  launch_at_login: false,
  show_alerts: true,
  notify_alerts: true,
  alert_cpu: 85,
  alert_mem: 85,
  alert_disk: 90,
  alert_battery: 15,
  confirm_proc_kill: true,
  allow_force_kill: true,
  menubar_show_icon: true,
  screenshot_hide_self: true,
  screenshot_clipboard: false,
  screenshot_cursor: false,
  screenshot_delay: 0.5,
  hotkey_shot_selection: 'ctrl+cmd+4',
  hotkey_shot_window: 'ctrl+cmd+5',
  hotkey_shot_full: 'ctrl+cmd+3',
  recording_hide_self: true,
  recording_mic: false,
  recording_system_audio: false,
  recording_clicks: true,
  recording_countdown: 3,
  recording_max_seconds: 0,
  recording_open_after: false,
  hotkey_rec_selection: 'ctrl+cmd+6',
  hotkey_rec_full: 'ctrl+cmd+7',
  hotkey_rec_stop: 'ctrl+cmd+8',
  finder_new_txt: false,
  finder_new_txt_open: true,
  version: '—'
};
let settingsApplying = false;
const CLEAN_COLORS = ['#0a84ff','#30d158','#ffd60a','#64d2ff','#bf5af2','#ff9f0a','#ff453a','#ac8e68'];
const CAT_ICONS = {
  cache:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7z"/><path d="M8 7V5a4 4 0 0 1 8 0v2"/></svg>',
  browser:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
  app:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/></svg>',
  log:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 4h10v16H7z"/><path d="M10 8h4M10 12h4M10 16h3"/></svg>',
  tmp:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v10"/><path d="M8 9l4 4 4-4"/><path d="M5 19h14"/></svg>',
  dev:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 9l-4 3 4 3M16 9l4 3-4 3M13 6l-2 12"/></svg>',
  archive:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="5" rx="1"/><path d="M6 9v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V9"/><path d="M10 13h4"/></svg>',
  code:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 8l-4 4 4 4M16 8l4 4-4 4"/></svg>',
  node:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/></svg>',
  brew:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 8h10l-1 11H7L6 8z"/><path d="M9 8V5M13 8V5M16 10h2a2 2 0 0 1 0 4h-2"/></svg>',
  phone:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="8" y="2" width="8" height="20" rx="2"/><path d="M11 18h2"/></svg>',
  trash:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/></svg>',
  folder:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7h6l2 2h10v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/></svg>',
  mail:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 7 9-7"/></svg>',
  docker:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="10" width="4" height="4"/><rect x="8" y="10" width="4" height="4"/><rect x="13" y="10" width="4" height="4"/><rect x="8" y="5" width="4" height="4"/><path d="M3 16h14a4 4 0 0 0 4-4"/></svg>',
  large:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 20h16M7 20V10l5-6 5 6v10"/><path d="M10 14h4"/></svg>'
};

function post(msg){
  try { window.webkit.messageHandlers.suptools.postMessage(msg); } catch(_){}
}
/** Native WKWebView ignores CSS app-region; ask AppKit to start a window drag. */
function requestWindowDrag(){
  post({type:'window_drag'});
}
document.addEventListener('mousedown', (e) => {
  if (e.button !== 0) return;
  if (e.metaKey || e.ctrlKey || e.altKey || e.shiftKey) return;
  const t = e.target;
  if (!t || !t.closest) return;
  if (t.closest('button, a, input, select, textarea, label, option, .controls, .nav, .modal, .modal-backdrop, .clean-modal, .seg, .theme-btn, table, canvas, .proc-actions, .shot-editor, .rec-editor, .perm-link')) return;
  if (t.closest('aside, .toolbar, .brand, .host')) requestWindowDrag();
}, true);
function $(id){ return document.getElementById(id); }
function pct(v,d=1){ return Number(v||0).toFixed(d) + '%'; }
function esc(s){
  return String(s==null?'':s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function setRing(el, p){ if(el) el.style.setProperty('--p', Math.max(0, Math.min(100, p))); }
function cssVar(name){
  return getComputedStyle(document.body).getPropertyValue(name).trim() || '#888';
}
function renderKv(el, rows){
  if (!el) return;
  el.innerHTML = (rows || []).map(r => {
    const cls = r.cls ? (' ' + r.cls) : '';
    return '<div class="kv-row"><span class="k">'+esc(r.k)+'</span><span class="v'+cls+'">'+esc(r.v)+'</span></div>';
  }).join('');
}

function spark(canvas, values, color, dual) {
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 300, h = canvas.clientHeight || 52;
  const key = w + 'x' + h + '@' + dpr;
  if (canvas.__sparkKey !== key) {
    canvas.__sparkKey = key;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
  }
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,w,h);
  const draw = (arr, col) => {
    if (!arr || arr.length < 2) return;
    const max = Math.max(...arr, 0.001);
    ctx.beginPath();
    arr.forEach((v,i) => {
      const x = i * (w-2) / (arr.length-1);
      const y = h - 3 - (v/max)*(h-8);
      if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.stroke();
  };
  if (dual) { draw(values[0], color[0]); draw(values[1], color[1]); }
  else draw(values, color);
}

function stack(el, parts) {
  if (!el) return;
  el.innerHTML = '';
  const sum = parts.reduce((a,b)=>a+Math.max(0,b[0]),0) || 1;
  parts.forEach(([f,c]) => {
    const i = document.createElement('i');
    i.style.width = (Math.max(0,f)/sum*100)+'%';
    i.style.background = c;
    el.appendChild(i);
  });
}

document.getElementById('nav').addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-page]'); if (!btn) return;
  page = btn.dataset.page;
  document.body.setAttribute('data-page', page);
  document.querySelectorAll('.nav button').forEach(b => b.classList.toggle('active', b===btn));
  document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === 'page-'+page));
  $('title').textContent = TITLES[page] || page;
  if (page === 'clean') {
    post({type:'clean_history'});
    if (!cleanItems.length && !cleanBusy) showCleanWelcome();
    else renderCleanList();
  }
  if (page === 'uninstall') {
    if (!unApps.length && !unBusy) post({type:'uninstall_list'});
    else { renderUnApps(); renderUnLeftovers(); }
  }
  if (page === 'startup') {
    if (!suItems.length && !suBusy) post({type:'startup_list'});
    else renderStartupList();
  }
  if (page === 'perms') {
    post({type:'permissions_status'});
  }
  if (page === 'settings') {
    post({type:'settings_get'});
  }
  if (page === 'shot') {
    post({type:'screenshot_list'});
    syncShotPrefsUI();
  }
  if (page === 'rec') {
    post({type:'recording_list'});
    syncRecPrefsUI();
  }
  if (state) render(state);
  post({type:'page', page});
});

$('pauseBtn').onclick = () => {
  paused = !paused;
  $('pauseBtn').textContent = paused ? '继续' : '暂停';
  post({type:'pause', paused});
};
$('interval').onchange = (e) => {
  post({type:'settings_set', values: {refresh_ms: Number(e.target.value)}});
};

function resolveTheme(theme){
  if (theme === 'system') {
    try {
      return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    } catch (_) { return 'dark'; }
  }
  return (theme === 'light') ? 'light' : 'dark';
}
function normalizeGlass(glass){
  return (glass === 'opaque' || glass === 'clear') ? glass : 'medium';
}
function syncGlassUI(){
  const g = normalizeGlass(appSettings.glass || 'medium');
  document.querySelectorAll('#set-glass .glass-card, #set-glass button').forEach(b => {
    b.classList.toggle('on', b.dataset.v === g);
  });
}
function applyGlass(glass, opts){
  const skipRender = opts && opts.skipRender;
  appSettings.glass = normalizeGlass(glass || appSettings.glass || 'medium');
  document.body.setAttribute('data-glass', appSettings.glass);
  syncGlassUI();
  if (!skipRender && state) render(state);
}
function themeLabel(theme){
  return ({light:'浅色', dark:'深色', system:'自动'}[theme] || '浅色');
}
function syncThemeBtn(){
  const btn = $('themeBtn');
  if (!btn) return;
  const pref = appSettings.theme || 'light';
  btn.title = '外观：' + themeLabel(pref) + '（点击切换）';
  btn.setAttribute('aria-label', btn.title);
}
function applyTheme(theme, opts){
  const skipRender = opts && opts.skipRender;
  appSettings.theme = theme || appSettings.theme || 'light';
  const t = resolveTheme(appSettings.theme);
  document.body.setAttribute('data-theme', t);
  document.body.setAttribute('data-theme-pref', appSettings.theme);
  applyGlass(appSettings.glass || 'medium', {skipRender: true});
  document.querySelectorAll('#set-theme .theme-card, #set-theme button').forEach(b => {
    b.classList.toggle('on', b.dataset.v === (appSettings.theme || 'light'));
  });
  syncThemeBtn();
  if (!skipRender && state) render(state);
}
window.__setTheme = function(payload){
  const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
  if (data && data.glass) appSettings.glass = normalizeGlass(data.glass);
  applyTheme((data && data.theme) || appSettings.theme || 'light', {skipRender: true});
};
window.__setInterval = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    if (data && data.ms) {
      const v = String(data.ms);
      const sel = $('interval');
      if (sel && [...sel.options].some(o => o.value === v)) sel.value = v;
      const sref = $('set-refresh');
      if (sref) {
        if (![...sref.options].some(o => o.value === v)) {
          const opt = document.createElement('option');
          opt.value = v; opt.textContent = (Number(v)/1000) + ' 秒';
          sref.appendChild(opt);
        }
        sref.value = v;
      }
    }
    if (data && typeof data.paused === 'boolean') {
      paused = !!data.paused;
      const btn = $('pauseBtn');
      if (btn) btn.textContent = paused ? '继续' : '暂停';
    }
  } catch (e) {}
};
window.__navigate = function(payload){
  const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
  const target = (data && data.page) || 'overview';
  const btn = document.querySelector('.nav button[data-page="'+target+'"]');
  if (btn) btn.click();
};
function setThemeChoice(theme){
  const next = (theme === 'dark' || theme === 'system') ? theme : 'light';
  applyTheme(next, {skipRender: true});
  post({type:'settings_set', values: {theme: next}});
}
function cycleTheme(){
  const order = ['light', 'dark', 'system'];
  const cur = appSettings.theme || 'light';
  const idx = Math.max(0, order.indexOf(cur));
  setThemeChoice(order[(idx + 1) % order.length]);
}
function setGlassChoice(glass){
  const next = normalizeGlass(glass);
  applyGlass(next, {skipRender: true});
  post({type:'settings_set', values: {glass: next}});
}
if ($('themeBtn')) $('themeBtn').onclick = (e) => {
  e.stopPropagation();
  cycleTheme();
};
try {
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
    if (appSettings.theme === 'system') applyTheme('system', {skipRender: true});
  });
} catch (_) {}
function saveSettings(patch){
  if (settingsApplying) return;
  post({type:'settings_set', values: patch || {}});
}
function bindSettingsUI(){
  const themeSeg = $('set-theme');
  if (themeSeg) themeSeg.onclick = (e) => {
    const btn = e.target.closest('button'); if (!btn) return;
    setThemeChoice(btn.dataset.v);
  };
  const glassSeg = $('set-glass');
  if (glassSeg) glassSeg.onclick = (e) => {
    const btn = e.target.closest('button'); if (!btn) return;
    setGlassChoice(btn.dataset.v);
  };
  const refresh = $('set-refresh');
  if (refresh) refresh.onchange = () => {
    const ms = Number(refresh.value);
    const sel = $('interval');
    if (sel && [...sel.options].some(o => o.value === String(ms))) sel.value = String(ms);
    saveSettings({refresh_ms: ms});
  };
  const mode = $('set-menubar-mode');
  if (mode) mode.onchange = () => saveSettings({menubar_mode: mode.value});
  const map = [
    ['set-alerts', 'show_alerts'],
    ['set-notify', 'notify_alerts'],
    ['set-menubar-icon', 'menubar_show_icon'],
    ['set-start-hidden', 'start_hidden'],
    ['set-login', 'launch_at_login'],
    ['set-clean-trash', 'clean_move_to_trash'],
    ['set-clean-confirm', 'clean_confirm'],
    ['set-proc-confirm', 'confirm_proc_kill'],
    ['set-force-kill', 'allow_force_kill'],
    ['set-finder-newtxt', 'finder_new_txt'],
    ['set-finder-newtxt-open', 'finder_new_txt_open'],
  ];
  map.forEach(([id, key]) => {
    const el = $(id);
    if (!el) return;
    el.onchange = () => {
      const val = !!el.checked;
      if (key === 'clean_move_to_trash') {
        cleanMoveToTrash = val;
        const t = $('clean-trash-mode'); if (t) t.checked = val;
      }
      if (key === 'clean_confirm') cleanConfirm = val;
      if (key === 'finder_new_txt') {
        post({type:'finder_new_txt_install', enabled: val});
        return;
      }
      saveSettings({[key]: val});
      if (key === 'allow_force_kill' && state) renderProcesses(state);
    };
  });
  const newTxtNow = $('set-finder-newtxt-now');
  if (newTxtNow) newTxtNow.onclick = () => post({type:'finder_new_txt'});
  [['set-alert-cpu','alert_cpu'],['set-alert-mem','alert_mem'],['set-alert-disk','alert_disk'],['set-alert-battery','alert_battery']].forEach(([id, key]) => {
    const el = $(id);
    if (!el) return;
    el.onchange = () => {
      const n = Number(el.value);
      if (!Number.isFinite(n)) return;
      saveSettings({[key]: n});
    };
  });
  const resetBtn = $('set-reset');
  if (resetBtn) resetBtn.onclick = () => {
    if (!confirm('恢复全部设置为默认值？\n登录启动项也会关闭。')) return;
    post({type:'settings_reset'});
  };
  const revealBtn = $('set-reveal-config');
  if (revealBtn) revealBtn.onclick = () => {
    const p = appSettings.config_path || '';
    if (p) post({type:'clean_reveal', path: p});
  };
}
bindSettingsUI();
window.__setSettings = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    if (!data) return;
    settingsApplying = true;
    appSettings = Object.assign({}, appSettings, data);
    applyTheme(appSettings.theme || 'light', {skipRender: true, keepMenu: true});
    applyGlass(appSettings.glass || 'medium', {skipRender: true});
    cleanMoveToTrash = !!appSettings.clean_move_to_trash;
    cleanConfirm = appSettings.clean_confirm !== false;
    const set = (id, checked) => { const el = $(id); if (el) el.checked = !!checked; };
    set('set-alerts', appSettings.show_alerts !== false);
    set('set-notify', appSettings.notify_alerts !== false);
    set('set-menubar-icon', appSettings.menubar_show_icon !== false);
    set('set-start-hidden', !!appSettings.start_hidden);
    set('set-login', !!appSettings.launch_at_login);
    set('set-finder-newtxt', !!appSettings.finder_new_txt);
    set('set-finder-newtxt-open', appSettings.finder_new_txt_open !== false);
    const fHint = $('set-finder-newtxt-hint');
    if (fHint) {
      fHint.textContent = appSettings.finder_new_txt_hint
        || '启用后出现在：Finder 右键 → 快速操作 / 服务。若看不到，到「系统设置 → 键盘 → 键盘快捷键 → 服务」勾选相关项。';
    }
    set('set-clean-trash', !!appSettings.clean_move_to_trash);
    set('set-clean-confirm', appSettings.clean_confirm !== false);
    set('set-proc-confirm', appSettings.confirm_proc_kill !== false);
    set('set-force-kill', appSettings.allow_force_kill !== false);
    const setNum = (id, v) => { const el = $(id); if (el && v != null) el.value = String(v); };
    setNum('set-alert-cpu', appSettings.alert_cpu);
    setNum('set-alert-mem', appSettings.alert_mem);
    setNum('set-alert-disk', appSettings.alert_disk);
    setNum('set-alert-battery', appSettings.alert_battery);
    syncShotPrefsUI();
    syncRecPrefsUI();
    const mode = $('set-menubar-mode');
    if (mode && appSettings.menubar_mode) mode.value = appSettings.menubar_mode;
    const refresh = $('set-refresh');
    if (refresh && appSettings.refresh_ms) {
      const v = String(appSettings.refresh_ms);
      if (![...refresh.options].some(o => o.value === v)) {
        const opt = document.createElement('option');
        opt.value = v; opt.textContent = (Number(v)/1000) + ' 秒';
        refresh.appendChild(opt);
      }
      refresh.value = v;
      const sel = $('interval');
      if (sel && [...sel.options].some(o => o.value === v)) sel.value = v;
    }
    if ($('set-version')) $('set-version').textContent = 'v' + (appSettings.version || '');
    if ($('set-app-path')) $('set-app-path').textContent = appSettings.app_path || '—';
    if ($('set-config-path')) $('set-config-path').textContent = appSettings.config_path || '—';
    const trash = $('clean-trash-mode');
    if (trash) trash.checked = !!appSettings.clean_move_to_trash;
    if (state) renderProcesses(state);
  } catch (e) {}
  settingsApplying = false;
};
$('proc-q').oninput = () => { if (state) renderProcesses(state); };
document.querySelectorAll('input[name=psort]').forEach(r => r.onchange = () => { if (state) renderProcesses(state); });

let selectedPids = {};
let lastShownProcPids = [];

function selectedPidList() {
  return Object.keys(selectedPids).map(Number).filter(n => n > 1);
}
function setPidSelected(pid, on) {
  pid = Number(pid);
  if (!pid || pid <= 1) return;
  if (on) selectedPids[pid] = true;
  else delete selectedPids[pid];
}
function clearSelectedPids(pids) {
  (pids || selectedPidList()).forEach(pid => delete selectedPids[pid]);
  updateProcStopUI();
}
function updateProcStopUI() {
  const n = selectedPidList().length;
  const count = $('proc-sel-count');
  if (count) count.textContent = '已选 ' + n;
  document.querySelectorAll('.proc-stop-btn').forEach(btn => {
    btn.disabled = n === 0;
  });
  const forceBtn = $('proc-force-selected');
  if (forceBtn) {
    forceBtn.style.display = (appSettings.allow_force_kill === false) ? 'none' : '';
    forceBtn.disabled = n === 0;
  }
  const master = $('proc-master-cb');
  if (master && lastShownProcPids.length) {
    const sel = lastShownProcPids.filter(pid => selectedPids[pid]).length;
    master.checked = sel > 0 && sel === lastShownProcPids.length;
    master.indeterminate = sel > 0 && sel < lastShownProcPids.length;
  } else if (master) {
    master.checked = false;
    master.indeterminate = false;
  }
}
function stopSelectedProcesses(force) {
  const pids = selectedPidList();
  if (!pids.length) return;
  if (force && appSettings.allow_force_kill === false) {
    $('status').textContent = '已在设置中禁用强制结束';
    return;
  }
  const action = force ? 'kill' : 'terminate';
  const label = force ? '强制结束' : '结束';
  if (appSettings.confirm_proc_kill !== false) {
    const msg = label + '已选的 ' + pids.length + ' 个进程？' + (force ? '\n可能导致未保存数据丢失。' : '');
    if (!confirm(msg)) return;
  }
  post({type:'proc_batch', pids, action});
  $('status').textContent = '正在' + label + ' ' + pids.length + ' 个进程…';
}
function procRowStopBtn(pid) {
  return '<div class="proc-actions"><button type="button" class="danger" data-act="terminate" data-pid="'+pid+'" title="结束进程">停止</button></div>';
}
function procChk(pid) {
  const on = !!selectedPids[pid];
  return '<td class="chk"><input type="checkbox" class="proc-cb" data-pid="'+pid+'"'+(on?' checked':'')+' /></td>';
}

document.addEventListener('change', (e) => {
  const cb = e.target.closest('input.proc-cb');
  if (cb) {
    setPidSelected(cb.dataset.pid, cb.checked);
    const tr = cb.closest('tr');
    if (tr) tr.classList.toggle('proc-selected', cb.checked);
    updateProcStopUI();
    return;
  }
  if (e.target && e.target.id === 'proc-master-cb') {
    const on = !!e.target.checked;
    lastShownProcPids.forEach(pid => setPidSelected(pid, on));
    if (state) renderProcesses(state);
    else updateProcStopUI();
  }
});
document.addEventListener('click', (e) => {
  const stopBtn = e.target.closest('.proc-stop-btn');
  if (stopBtn && !stopBtn.disabled) {
    e.preventDefault();
    stopSelectedProcesses(stopBtn.id === 'proc-force-selected');
    return;
  }
  const btn = e.target.closest('.proc-actions button');
  if (!btn) return;
  const pid = Number(btn.dataset.pid||0);
  const act = btn.dataset.act || '';
  if (!pid || !act) return;
  if (act === 'kill' && appSettings.allow_force_kill === false) {
    $('status').textContent = '已在设置中禁用强制结束';
    return;
  }
  if (appSettings.confirm_proc_kill !== false) {
    if (act === 'terminate' && !confirm('结束进程 PID ' + pid + '？')) return;
    if (act === 'kill' && !confirm('强制结束进程 PID ' + pid + '？\n可能导致未保存数据丢失。')) return;
  }
  post({type:'proc_action', pid, action: act});
});
if ($('proc-sel-all')) $('proc-sel-all').onclick = () => {
  lastShownProcPids.forEach(pid => setPidSelected(pid, true));
  if (state) renderProcesses(state);
};
if ($('proc-sel-none')) $('proc-sel-none').onclick = () => {
  clearSelectedPids();
  if (state) renderProcesses(state);
};
window.__setProcResult = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    if (!data.ok) {
      $('status').textContent = '进程操作失败: ' + (data.error || 'unknown');
      return;
    }
    const map = {terminate:'已发送结束', kill:'已强制结束', reveal:'已在 Finder 显示'};
    $('status').textContent = (map[data.action] || '已完成') + ' · ' + (data.name||'') + ' (PID ' + data.pid + ')';
    if (data.action === 'terminate' || data.action === 'kill') {
      delete selectedPids[data.pid];
      updateProcStopUI();
    }
  } catch (e) {}
};
window.__setProcBatchResult = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    const ok = data.ok_count || 0;
    const fail = data.fail_count || 0;
    const action = data.action === 'kill' ? '强制结束' : '结束';
    $('status').textContent = action + '完成 · 成功 ' + ok + (fail ? (' · 失败 ' + fail) : '');
    (data.ok_pids || []).forEach(pid => delete selectedPids[pid]);
    updateProcStopUI();
    if (state) {
      if (page === 'processes') renderProcesses(state);
    }
  } catch (e) {}
};

function renderHero(s) {
  const hero = $('hero');
  if (!hero) return;
  const tiles = [
    {k:'CPU', v:pct(s.cpu_percent,0), s:`用户 ${pct(s.cpu_user,0)} · 系统 ${pct(s.cpu_system,0)}`, c:'var(--cpu)'},
    {k:'内存', v:pct(s.mem_percent,0), s:`${esc(s.mem_used)} / ${esc(s.mem_total)}`, c:'var(--mem)'},
    {k:'网络', v:'↓ '+esc(s.net_down_m), s:'↑ '+esc(s.net_up_m), c:'var(--down)'},
    {k:'磁盘', v:pct(s.disk_percent,0), s:`${esc(s.disk_used)} / ${esc(s.disk_total)}`, c:'var(--disk)'},
  ];
  hero.innerHTML = tiles.map(t => `
    <div class="tile" style="--c:${t.c}">
      <div class="k"><span class="dot"></span>${t.k}</div>
      <div class="v">${t.v}</div>
      <div class="s">${t.s}</div>
    </div>`).join('');
}

function renderProcesses(s) {
  const q = ($('proc-q').value || '').trim().toLowerCase();
  const sort = (document.querySelector('input[name=psort]:checked') || {}).value || 'cpu';
  let items = (s.processes || []).slice();
  if (q) items = items.filter(p =>
    String(p.name).toLowerCase().includes(q) ||
    String(p.pid).includes(q) ||
    String(p.user||'').toLowerCase().includes(q) ||
    String(p.cmd||'').toLowerCase().includes(q)
  );
  items.sort((a,b) => sort==='mem' ? b.memory_bytes-a.memory_bytes : b.cpu-a.cpu);
  const shown = items.slice(0,50);
  lastShownProcPids = shown.map(p => p.pid);
  const count = $('proc-count');
  if (count) count.textContent = '显示 ' + shown.length + ' / ' + (s.processes||[]).length;
  $('proc-rows').innerHTML = shown.map(p => `
    <tr class="${selectedPids[p.pid]?'proc-selected':''}">
      ${procChk(p.pid)}
      <td class="num">${p.pid}</td>
      <td title="${esc(p.cmd||p.name)}">${esc(p.name)}</td>
      <td>${esc(p.user||'—')}</td>
      <td class="num">${pct(p.cpu)}</td>
      <td class="num">${esc(p.memory)}</td>
      <td class="num">${p.threads}</td>
      <td>${esc(p.runtime||'—')}</td>
      <td>${esc(p.status)}</td>
      <td><div class="proc-actions">
        <button type="button" data-act="terminate" data-pid="${p.pid}" title="结束进程">结束</button>
        ${appSettings.allow_force_kill === false ? '' : '<button type="button" class="danger" data-act="kill" data-pid="'+p.pid+'" title="强制结束">强退</button>'}
        <button type="button" data-act="reveal" data-pid="${p.pid}" title="在 Finder 显示">显示</button>
      </div></td>
    </tr>`).join('') ||
    '<tr><td colspan="10" class="muted">暂无匹配进程</td></tr>';
  updateProcStopUI();
}

function renderProcMini(el, items, memFirst) {
  if (!el) return;
  const rows = (items||[]).slice(0,8);
  if (!rows.length) {
    el.innerHTML = '<tr><td colspan="6" class="muted">暂无进程数据</td></tr>';
    updateProcStopUI();
    return;
  }
  if (memFirst) {
    el.innerHTML = rows.map(p => `
      <tr class="${selectedPids[p.pid]?'proc-selected':''}">
        ${procChk(p.pid)}
        <td class="num">${p.pid}</td><td title="${esc(p.name)}">${esc(p.name)}</td>
        <td class="num">${esc(p.memory)}</td><td class="num">${pct(p.cpu)}</td>
        <td>${procRowStopBtn(p.pid)}</td>
      </tr>`).join('');
  } else {
    el.innerHTML = rows.map(p => `
      <tr class="${selectedPids[p.pid]?'proc-selected':''}">
        ${procChk(p.pid)}
        <td class="num">${p.pid}</td><td title="${esc(p.name)}">${esc(p.name)}</td>
        <td class="num">${pct(p.cpu)}</td><td class="num">${esc(p.memory)}</td>
        <td>${procRowStopBtn(p.pid)}</td>
      </tr>`).join('');
  }
  updateProcStopUI();
}

function renderAlerts(s) {
  const box = $('ov-alerts');
  if (!box) return;
  if (appSettings.show_alerts === false) { box.classList.remove('show'); box.innerHTML=''; return; }
  const alerts = s.alerts || [];
  if (!alerts.length) { box.classList.remove('show'); box.innerHTML=''; return; }
  box.classList.add('show');
  box.innerHTML = alerts.map(a => `<div class="alert ${a.level==='danger'?'danger':''}">${esc(a.text)}</div>`).join('');
}

function render(s) {
  state = s;
  const p = page || 'overview';
  const hn = $('host-name'); if (hn) hn.textContent = s.hostname || '本机';
  const meta = $('meta'); if (meta) meta.textContent = (s.chip || '') + '\n' + (s.platform || '');
  const st = $('status'); if (st) st.textContent = s.status_line || '';
  if (p !== 'clean' && p !== 'uninstall' && p !== 'startup' && p !== 'perms' && p !== 'settings' && p !== 'shot' && p !== 'rec' && p !== 'conn') {
    renderHero(s);
  }

  if (p === 'overview') {
    const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };
    set('ov-header', s.hostname || '本机');
    set('ov-sub', s.subtitle || '');
    renderAlerts(s);
    set('ov-chip', s.chip || '—');
    set('ov-cores', s.cores_label || '—');
    set('ov-load', (s.load||[]).join(' / ') || '—');
    set('ov-uptime', s.uptime || '—');
    const press = $('ov-pressure');
    if (press) {
      const lv = s.mem_pressure || 'normal';
      press.textContent = s.mem_pressure_cn || ({normal:'正常',warn:'警告',critical:'严重'}[lv] || '正常');
      press.className = 'pressure-pill' + (lv === 'warn' || lv === 'critical' ? ' ' + lv : '');
    }
    const battPill = $('ov-batt-pill');
    set('ov-battery', s.battery_text || '—');
    if (battPill) battPill.style.display = (s.has_battery === false && (s.battery_text||'').indexOf('外接')>=0) ? '' : '';
    set('q-cpu', pct(s.cpu_percent, 0));
    set('q-cpu-s', `用户 ${pct(s.cpu_user,0)} · 系统 ${pct(s.cpu_system,0)}`);
    set('q-mem', pct(s.mem_percent, 0));
    set('q-mem-s', `${s.mem_used || ''} / ${s.mem_total || ''}`);
    set('q-down', s.net_down || '—');
    set('q-up', '上行 ' + (s.net_up || '—'));
    set('q-disk', pct(s.disk_percent, 0));
    set('q-disk-s', s.disk_text || '');

    setRing($('ov-cpu-ring'), s.cpu_percent);
    set('ov-cpu-pct', pct(s.cpu_percent,0));
    renderKv($('ov-cpu-kv'), [
      {k:'用户', v: pct(s.cpu_user,1)},
      {k:'系统', v: pct(s.cpu_system,1)},
      {k:'空闲', v: pct(s.cpu_idle,1), cls:'good'},
      {k:'负载', v: (s.load||[]).join(' / ') || '—'},
    ]);
    spark($('ov-cpu-spark'), s.cpu_history || [], cssVar('--cpu'));

    setRing($('ov-mem-ring'), s.mem_percent);
    set('ov-mem-pct', pct(s.mem_percent,0));
    set('ov-mem-used', s.mem_used || '');
    renderKv($('ov-mem-kv'), [
      {k:'已用', v: s.mem_used || '—'},
      {k:'可用', v: s.mem_available || '—', cls:'good'},
      {k:'总计', v: s.mem_total || '—'},
      {k:'压力', v: s.mem_pressure_cn || '—'},
    ]);
    stack($('ov-mem-stack'), s.mem_segments || []);
    set('ov-mem-legend', s.mem_legend || '');
    spark($('ov-mem-spark'), s.mem_history || [], cssVar('--mem'));

    set('ov-net-down', s.net_down || '—');
    set('ov-net-up', s.net_up || '—');
    set('ov-net-iface', s.net_iface || '');
    spark($('ov-net-spark'), [s.net_down_history||[], s.net_up_history||[]], [cssVar('--down'), cssVar('--up')], true);

    set('ov-disk-name', s.disk_label || '主磁盘');
    set('ov-disk-pct-label', pct(s.disk_percent, 1));
    const diskBar = $('ov-disk-bar');
    if (diskBar) diskBar.style.width = Math.min(100, s.disk_percent||0) + '%';
    set('ov-disk-text', s.disk_text || '—');
    set('ov-disk-read', s.disk_read || '—');
    set('ov-disk-write', s.disk_write || '—');
    renderProcMini($('ov-procs'), s.processes||[], false);
    renderProcMini($('ov-mem-procs'), s.top_mem||[], true);
  }

  if (p === 'cpu') {
    setRing($('cpu-ring'), s.cpu_percent);
    $('cpu-pct').textContent = pct(s.cpu_percent);
    renderKv($('cpu-compose-kv'), [
      {k:'用户态', v: pct(s.cpu_user,1)},
      {k:'系统态', v: pct(s.cpu_system,1)},
      {k:'空闲', v: pct(s.cpu_idle,1), cls:'good'},
      {k:'核心', v: s.cores_label || '—'},
      {k:'负载', v: (s.load||[]).join('  ') || '—'},
      {k:'启动于', v: s.boot_time || '—'},
    ]);
    spark($('cpu-spark'), s.cpu_history||[], cssVar('--cpu'));
    $('cpu-cores').innerHTML = (s.cpu_per_core||[]).map((v,i) => `
      <div class="core">
        <div class="top"><span class="t">核心 ${i}</span><span class="n">${pct(v,0)}</span></div>
        <div class="bar" style="--c:var(--cpu)"><span style="width:${Math.min(100,v)}%"></span></div>
      </div>`).join('');
    if ($('cpu-top-procs')) {
      const rows = (s.processes||[]).slice(0,12);
      $('cpu-top-procs').innerHTML = rows.map(pr => `
        <tr class="${selectedPids[pr.pid]?'proc-selected':''}">
          ${procChk(pr.pid)}
          <td class="num">${pr.pid}</td><td title="${esc(pr.name)}">${esc(pr.name)}</td><td>${esc(pr.user||'—')}</td>
          <td class="num">${pct(pr.cpu)}</td><td class="num">${esc(pr.memory)}</td>
          <td>${procRowStopBtn(pr.pid)}</td>
        </tr>`).join('')
        || '<tr><td colspan="7" class="muted">暂无进程数据</td></tr>';
    }
    updateProcStopUI();
  }

  if (p === 'memory') {
    setRing($('mem-ring'), s.mem_pressure_score != null ? s.mem_pressure_score : s.mem_percent);
    $('mem-pct').textContent = pct(s.mem_percent);
    if ($('mem-pressure-label')) $('mem-pressure-label').textContent = s.mem_pressure_cn || '压力';
    renderKv($('mem-compose-kv'), [
      {k:'物理内存', v: s.mem_total || '—'},
      {k:'已用', v: (s.mem_used || '—') + '  (' + pct(s.mem_percent,1) + ')'},
      {k:'可用', v: s.mem_available || '—', cls:'good'},
      {k:'压力', v: (s.mem_pressure_cn || '—') + (s.mem_pressure_score!=null ? ('  ' + Number(s.mem_pressure_score).toFixed(0)) : '')},
      {k:'交换', v: (s.swap_used || '—') + ' / ' + (s.swap_total || '—')},
    ]);
    spark($('mem-spark'), s.mem_history||[], cssVar('--mem'));
    stack($('mem-stack'), s.mem_segments || []);
    $('mem-breakdown').textContent = s.mem_breakdown || '';
    if ($('mem-top-procs')) {
      const rows = (s.top_mem||[]).slice(0,12);
      $('mem-top-procs').innerHTML = rows.map(pr => `
        <tr class="${selectedPids[pr.pid]?'proc-selected':''}">
          ${procChk(pr.pid)}
          <td class="num">${pr.pid}</td><td title="${esc(pr.name)}">${esc(pr.name)}</td><td>${esc(pr.user||'—')}</td>
          <td class="num">${esc(pr.memory)}</td><td class="num">${pct(pr.cpu)}</td>
          <td>${procRowStopBtn(pr.pid)}</td>
        </tr>`).join('')
        || '<tr><td colspan="7" class="muted">暂无进程数据</td></tr>';
    }
    updateProcStopUI();
  }

  if (p === 'disk') {
    setRing($('disk-ring'), s.disk_percent);
    if ($('disk-pct')) $('disk-pct').textContent = pct(s.disk_percent,0);
    if ($('disk-ring-label')) $('disk-ring-label').textContent = s.disk_label || '占用';
    if ($('disk-cap-text')) $('disk-cap-text').textContent = (s.disk_used||'—') + ' / ' + (s.disk_total||'—') + ' · 可用 ' + (s.disk_free||'—');
    $('disk-read').textContent = s.disk_read || '—';
    $('disk-write').textContent = s.disk_write || '—';
    spark($('disk-read-spark'), s.disk_read_history||[], cssVar('--disk'));
    spark($('disk-write-spark'), s.disk_write_history||[], cssVar('--warn'));
    $('disk-vols').innerHTML = (s.volumes||[]).map(v => `
      <div class="vol-card">
        <div class="vol-meta">
          <div class="vt" title="${esc(v.title)}">${esc(v.title)}</div>
          <div class="vp" style="color:${v.warn?'var(--danger)':'var(--tint)'}">${pct(v.percent,1)}</div>
        </div>
        <div class="bar" style="--c:${esc(v.color)}"><span style="width:${Math.min(100,v.percent||0)}%"></span></div>
        <div class="muted" style="font-family:ui-monospace,Menlo,monospace;margin-top:8px;font-variant-numeric:tabular-nums">${esc(v.detail)}</div>
      </div>`).join('') || '<div class="muted">暂无卷信息</div>';
  }

  if (p === 'network') {
    $('net-down').textContent = s.net_down || '—';
    $('net-up').textContent = s.net_up || '—';
    spark($('net-down-spark'), s.net_down_history||[], cssVar('--down'));
    spark($('net-up-spark'), s.net_up_history||[], cssVar('--up'));
    if ($('net-summary')) $('net-summary').textContent = s.net_iface || '';
    $('net-ifaces').innerHTML = (s.ifaces||[]).map(i => `
      <tr>
        <td>${esc(i.name)}</td>
        <td>${i.isup?'在线':'离线'}</td>
        <td>${esc(i.ip)}</td>
        <td class="num">${esc(i.speed_text||'—')}</td>
        <td class="num">${esc(i.down)}</td>
        <td class="num">${esc(i.up)}</td>
        <td class="num">${esc(i.recv)}</td>
        <td class="num">${esc(i.sent)}</td>
        <td class="num">${esc((i.packets_recv||0)+' / '+(i.packets_sent||0))}</td>
      </tr>`).join('') ||
      '<tr><td colspan="9" class="muted">暂无活跃网卡</td></tr>';
  }

  if (p === 'processes') renderProcesses(s);
}

window.__setMetrics = function(payload) {
  try { render(typeof payload === 'string' ? JSON.parse(payload) : payload); }
  catch (e) { $('status').textContent = '界面更新失败: ' + e; }
};

window.__setCleanProgress = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    const panel = $('clean-progress');
    if (panel) {
      panel.classList.add('show');
      panel.classList.toggle('indeterminate', (Number(data.percent)||0) < 2 && (data.phase==='scan'||data.phase==='clean'));
    }
    $('clean-success').classList.remove('show');
    const phase = data.phase || 'scan';
    const pctN = Math.max(0, Math.min(100, Number(data.percent) || 0));
    let label = '正在扫描…';
    if (phase === 'clean') label = '正在清理…';
    else if (phase === 'scan_done') label = '扫描完成';
    else if (phase === 'scan_cancelled') label = '扫描已取消';
    else if (phase === 'clean_done') label = '清理完成';
    else if (phase === 'clean_cancelled') label = '清理已取消';
    else if (data.category) label = '扫描「' + data.category + '」';
    $('clean-prog-label').textContent = label;
    $('clean-prog-pct').textContent = Math.round(pctN) + '%';
    $('clean-prog-bar').style.width = pctN + '%';
    $('clean-prog-current').textContent = data.current || '—';
    const found = data.found_items != null ? data.found_items : (data.cleaned_items != null ? data.cleaned_items : 0);
    const bytes = data.scanned_bytes != null ? data.scanned_bytes : (data.freed_bytes != null ? data.freed_bytes : 0);
    if (phase === 'clean' || phase === 'clean_done' || phase === 'clean_cancelled') {
      const idx = data.index || found;
      const tot = data.total || 0;
      $('clean-prog-found').textContent = tot ? ('进度 ' + idx + ' / ' + tot) : ('已处理 ' + found + ' 项');
      $('clean-prog-bytes').textContent = '已释放 ' + formatBytes(bytes);
    } else {
      $('clean-prog-found').textContent = '已发现 ' + found + ' 项';
      $('clean-prog-bytes').textContent = formatBytes(bytes);
    }
    cleanBusy = phase === 'scan' || phase === 'clean';
    setCleanBusyUI(cleanBusy);
  } catch (e) {}
};

window.__setCleanPrefs = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    cleanMoveToTrash = !!data.move_to_trash;
    if (typeof data.clean_confirm === 'boolean') cleanConfirm = data.clean_confirm;
    const box = $('clean-trash-mode');
    if (box) box.checked = cleanMoveToTrash;
    cleanHistory = data.history || [];
    renderCleanHistory();
  } catch (e) {}
};

window.__setCleanScan = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    cleanItems = data.items || [];
    cleanCategories = data.categories || [];
    cleanRecommendIds = data.recommend_ids || [];
    cleanInsights = data.insights || [];
    if (!Object.keys(cleanExpanded).length && cleanCategories.length) {
      cleanExpanded[cleanCategories[0].key] = true;
    }
    $('clean-total').textContent = data.total_text || formatBytes(data.total_bytes || 0);
    $('clean-safe').textContent = data.safe_text || formatBytes(data.safe_bytes || 0);
    renderCleanInsights();
    renderCleanCatFilters();
    renderCleanStack();
    renderCleanList();
    updateCleanSelectionSummary();
    const rec = $('clean-recommend');
    if (rec) rec.disabled = !cleanRecommendIds.length;
    const et = $('clean-empty-trash');
    if (et) et.disabled = !(Number(data.trash_bytes || 0) > 0);
    const panel = $('clean-progress');
    if (panel) {
      panel.classList.remove('indeterminate');
      if (!cleanBusy) {
        const cancelled = !!data.cancelled;
        $('clean-prog-label').textContent = cancelled ? '扫描已取消' : '扫描完成';
        $('clean-prog-pct').textContent = '100%';
        $('clean-prog-bar').style.width = '100%';
        $('clean-prog-current').textContent = data.error
          ? ('失败: ' + data.error)
          : ('共 ' + (data.item_count || cleanItems.length) + ' 项 · 用时 ' + (data.elapsed || '—') + 's');
        $('clean-prog-found').textContent = '已发现 ' + (data.item_count || cleanItems.length) + ' 项';
        $('clean-prog-bytes').textContent = data.total_text || '0 B';
        if (!data.error) setTimeout(function(){ if (!cleanBusy) panel.classList.remove('show'); }, 1800);
      }
    }
    cleanBusy = false;
    setCleanBusyUI(false);
    $('clean-scan').textContent = '重新扫描';
  } catch (e) {
    cleanBusy = false;
    setCleanBusyUI(false);
  }
};

window.__setCleanResult = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    const panel = $('clean-progress');
    if (panel) {
      panel.classList.add('show');
      panel.classList.remove('indeterminate');
      $('clean-prog-label').textContent = data.cancelled ? '清理已取消' : (data.will_rescan ? '清理完成 · 刷新中' : '清理完成');
      $('clean-prog-pct').textContent = '100%';
      $('clean-prog-bar').style.width = '100%';
      $('clean-prog-current').textContent = (data.action_label || (data.moved_to_trash ? '已移至废纸篓' : '已释放')) + ' · ' + (data.freed_text || '0 B');
      $('clean-prog-found').textContent = '已处理 ' + (data.removed_items || 0) + ' 项';
      $('clean-prog-bytes').textContent = data.freed_text || '0 B';
    }
    const ok = $('clean-success');
    ok.classList.add('show');
    $('clean-success-t').textContent = data.cancelled ? '已取消 · 部分完成' : (data.emptied_trash ? '废纸篓已清空' : '清理完成');
    const mode = data.action_label || (data.moved_to_trash ? '已移至废纸篓（清空后才真正释放磁盘）' : '已永久删除并释放空间');
    $('clean-success-s').textContent = (data.freed_text || '0 B') + ' · ' + (data.removed_items || 0) + ' 项 · ' + mode
      + ((data.errors && data.errors.length) ? (' · ' + data.errors.length + ' 个错误') : '');
    if (data.errors && data.errors.length) {
      $('status').textContent = '清理错误: ' + data.errors[0];
    } else if ((data.removed_items || 0) === 0 && (data.requested || 0) > 0) {
      $('status').textContent = '未能删除所选项目（可能被占用或权限不足）';
    } else if ((data.requested || 0) === 0 && (data.errors && data.errors.length)) {
      $('status').textContent = data.errors[0];
    }
    if (data.will_rescan && !data.cancelled) {
      cleanBusy = true;
      setCleanBusyUI(true);
      if ($('clean-prog-label')) $('clean-prog-label').textContent = '正在刷新扫描结果…';
    } else {
      cleanBusy = false;
      setCleanBusyUI(false);
    }
  } catch (e) {
    cleanBusy = false;
    setCleanBusyUI(false);
  }
};

function formatBytes(n){
  const u=['B','KB','MB','GB','TB']; let v=Math.max(0, Number(n)||0);
  for (const x of u){ if (v<1024 || x==='TB') return (x==='B'?Math.round(v):v.toFixed(1))+' '+x; v/=1024; }
  return n+' B';
}

function showCleanWelcome(){
  $('clean-list').innerHTML = `
    <div class="clean-empty">
      <div class="art"><svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/></svg></div>
      <div class="big">专业系统清理</div>
      覆盖缓存、浏览器、开发工具、聊天应用、安装包、大文件与废纸篓。<br/>扫描后可用「智能勾选」一键选中安全项。
    </div>`;
  $('clean-total').textContent = '—';
  $('clean-safe').textContent = '0 B';
  $('clean-stack').innerHTML = '';
  const insights = $('clean-insights');
  if (insights) insights.innerHTML = '';
  const chips = $('clean-cat-filters');
  if (chips) chips.innerHTML = '';
  updateCleanSelectionSummary();
}

function renderCleanHistory(){
  const box = $('clean-history');
  const rows = $('clean-history-rows');
  if (!cleanHistory.length) { box.style.display = 'none'; return; }
  box.style.display = 'block';
  rows.innerHTML = cleanHistory.map(h => {
    const d = new Date((h.ts||0)*1000);
    const when = isNaN(d.getTime()) ? '—' : (d.getMonth()+1) + '/' + d.getDate() + ' ' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0');
    return `<div class="h-row"><span>${esc(when)} · ${esc(h.removed_items||0)} 项${h.moved_to_trash?' · 废纸篓':''}</span><b>${esc(h.freed_text||'0 B')}</b></div>`;
  }).join('');
}

function renderCleanStack(){
  const el = $('clean-stack');
  if (!cleanCategories.length) { el.innerHTML = ''; return; }
  const total = cleanCategories.reduce((a,c)=>a+(c.bytes||0),0) || 1;
  el.innerHTML = cleanCategories.slice(0,8).map((c,i) =>
    `<i style="width:${Math.max(2,(c.bytes||0)/total*100)}%;background:${CLEAN_COLORS[i%CLEAN_COLORS.length]}" title="${esc(c.title)} ${esc(c.size_text||'')}"></i>`
  ).join('');
}

function setCleanBusyUI(busy) {
  const scan = $('clean-scan');
  const smart = $('clean-smart');
  if (scan) {
    scan.disabled = !!busy;
    if (!busy) scan.textContent = cleanItems.length ? '重新扫描' : '开始扫描';
    else if (scan.textContent.indexOf('扫描') >= 0) scan.textContent = '扫描中…';
  }
  if (smart) {
    if (busy) { smart.disabled = true; smart.textContent = '处理中…'; }
    else {
      smart.textContent = '清理所选';
      updateCleanSelectionSummary();
    }
  }
  ['clean-recommend','clean-empty-trash'].forEach(id => {
    const el = $(id);
    if (!el) return;
    if (busy) el.disabled = true;
    else if (id === 'clean-recommend') el.disabled = !cleanRecommendIds.length;
    else el.disabled = !cleanItems.some(it => it.category === 'trash');
  });
  const cancel = $('clean-cancel');
  if (cancel) cancel.style.visibility = busy ? 'visible' : 'hidden';
}

function renderCleanInsights(){
  const el = $('clean-insights');
  if (!el) return;
  if (!cleanInsights.length) { el.innerHTML = ''; return; }
  el.innerHTML = cleanInsights.map(it =>
    `<div class="clean-insight ${esc(it.tone||'')}">`+
      `<div class="l">${esc(it.label||'')}</div>`+
      `<div class="v">${esc(it.value||'—')}</div>`+
      `<div class="d">${esc(it.detail||'')}</div>`+
    `</div>`
  ).join('');
}

function renderCleanCatFilters(){
  const el = $('clean-cat-filters');
  if (!el) return;
  if (!cleanCategories.length) { el.innerHTML = ''; return; }
  const chips = [{key:'all', title:'全部', count: cleanItems.length}].concat(cleanCategories);
  el.innerHTML = chips.map(c =>
    `<button type="button" class="clean-chip ${cleanCatFilter===c.key?'active':''}" data-clean-cat="${esc(c.key)}">${esc(c.title)}${c.count!=null?' · '+c.count:''}</button>`
  ).join('');
}

function getSelectedCleanItems() {
  const boxes = [...document.querySelectorAll('#clean-list input.item-cb:checked')];
  const byId = {};
  cleanItems.forEach(it => { byId[String(it.id)] = it; });
  const out = [];
  const seen = {};
  const pushIt = (it) => {
    if (!it || !it.path || seen[it.path]) return;
    seen[it.path] = true;
    out.push(it);
  };
  if (boxes.length) {
    boxes.forEach(el => {
      const id = String(el.dataset.id || '');
      const cached = byId[id];
      if (cached) pushIt(cached);
      else pushIt({
        id: id,
        path: el.dataset.path || '',
        name: id.split(':').slice(1).join(':') || id,
        category: el.dataset.cat || '',
        risk: el.dataset.risk || 'safe',
        bytes: Number(el.dataset.bytes || 0),
        mode: 'all',
      });
    });
  } else {
    cleanItems.filter(it => it.selected).forEach(pushIt);
  }
  return out;
}

function filteredCleanItems() {
  const q = (($('clean-q') && $('clean-q').value) || '').trim().toLowerCase();
  const minSize = Number(($('clean-minsize') && $('clean-minsize').value) || 0);
  const risk = ($('clean-risk') && $('clean-risk').value) || 'all';
  let items = cleanItems.slice();
  if (cleanCatFilter && cleanCatFilter !== 'all') {
    items = items.filter(it => it.category === cleanCatFilter);
  }
  if (risk === 'safe') items = items.filter(it => it.risk !== 'caution');
  if (risk === 'caution') items = items.filter(it => it.risk === 'caution');
  if (minSize > 0) items = items.filter(it => (it.bytes||0) >= minSize);
  if (q) items = items.filter(it =>
    String(it.name||'').toLowerCase().includes(q) ||
    String(it.path||'').toLowerCase().includes(q) ||
    String(it.path_display||'').toLowerCase().includes(q) ||
    String(it.category_title||'').toLowerCase().includes(q)
  );
  const sort = ($('clean-sort') && $('clean-sort').value) || 'size';
  if (sort === 'name') items.sort((a,b)=>String(a.name).localeCompare(String(b.name),'zh'));
  else if (sort === 'risk') items.sort((a,b)=> (a.risk==='caution'?0:1)-(b.risk==='caution'?0:1) || (b.bytes||0)-(a.bytes||0));
  else items.sort((a,b)=>(b.bytes||0)-(a.bytes||0));
  return items;
}

function updateCleanSelectionSummary() {
  const checked = [...document.querySelectorAll('#clean-list input.item-cb:checked')];
  let bytes = 0;
  checked.forEach(el => { bytes += Number(el.dataset.bytes || 0); });
  $('clean-selected').textContent = formatBytes(bytes);
  $('clean-count').textContent = String(cleanItems.length);
  $('clean-sel-count').textContent = String(checked.length);
  const smart = $('clean-smart');
  if (smart && !cleanBusy) smart.disabled = checked.length === 0;
  document.querySelectorAll('#clean-list .cat-cb').forEach(cb => {
    const key = cb.dataset.key;
    const items = [...document.querySelectorAll('#clean-list input.item-cb[data-cat="'+key+'"]')];
    if (!items.length) { cb.checked = false; cb.indeterminate = false; return; }
    const n = items.filter(i => i.checked).length;
    cb.checked = n === items.length;
    cb.indeterminate = n > 0 && n < items.length;
  });
}

function renderCleanList() {
  const root = $('clean-list');
  const items = filteredCleanItems();
  if (!cleanItems.length) { showCleanWelcome(); return; }
  if (!items.length) {
    root.innerHTML = '<div class="clean-empty"><div class="big">没有匹配结果</div>试试调整搜索或大小筛选</div>';
    updateCleanSelectionSummary();
    return;
  }
  const byCat = {};
  items.forEach(it => {
    const k = it.category || 'other';
    if (!byCat[k]) byCat[k] = [];
    byCat[k].push(it);
  });
  const cats = (cleanCategories && cleanCategories.length)
    ? cleanCategories.filter(c => byCat[c.key] && byCat[c.key].length)
    : Object.keys(byCat).map(k => ({
        key: k,
        title: (byCat[k][0] && byCat[k][0].category_title) || k,
        risk: (byCat[k][0] && byCat[k][0].risk) || 'safe',
        icon: 'folder',
        bytes: byCat[k].reduce((a,b)=>a+(b.bytes||0),0),
        size_text: null,
        count: byCat[k].length,
      }));

  root.innerHTML = cats.map(cat => {
    const group = byCat[cat.key] || [];
    const open = !!cleanExpanded[cat.key];
    const riskBadge = cat.risk === 'caution' ? '<span class="badge warn">谨慎</span>' : '<span class="badge">安全</span>';
    const sizeText = cat.size_text || formatBytes(group.reduce((a,b)=>a+(b.bytes||0),0));
    const allSelected = group.every(i => i.selected);
    const ico = CAT_ICONS[cat.icon] || CAT_ICONS.folder;
    const rows = group.map(it => `
      <div class="clean-row">
        <input class="clean-cb item-cb" type="checkbox" data-id="${esc(it.id)}" data-cat="${esc(it.category)}" data-bytes="${it.bytes||0}" data-risk="${esc(it.risk||'safe')}" data-path="${esc(it.path||'')}" ${it.selected ? 'checked' : ''} />
        <div>
          <div class="name">${esc(it.name)}${it.risk==='caution'?' <span class="badge warn">谨慎</span>':''}</div>
          <div class="path">${esc(it.path_display || it.path || '')}</div>
          <div class="meta">${it.files != null ? (esc(it.files) + ' 个文件') : ''}</div>
        </div>
        <div class="size">${esc(it.size_text || formatBytes(it.bytes||0))}</div>
        <button class="reveal" type="button" data-path="${esc(it.path||'')}" title="在 Finder 中显示">显示</button>
      </div>`).join('');
    return `
      <div class="clean-cat ${open ? 'open' : ''}" data-key="${esc(cat.key)}">
        <div class="clean-cat-head">
          <input class="clean-cb cat-cb" type="checkbox" data-key="${esc(cat.key)}" ${allSelected ? 'checked' : ''} onclick="event.stopPropagation()" />
          <div class="clean-cat-ico">${ico}</div>
          <span class="chev"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 6l6 6-6 6"/></svg></span>
          <div>
            <div class="title">${esc(cat.title)} ${riskBadge}</div>
            <div class="sub">${group.length} 项 · ${esc(cat.detail || '')}</div>
          </div>
          <div class="size">${esc(sizeText)}</div>
        </div>
        <div class="clean-items">${rows}</div>
      </div>`;
  }).join('');

  root.querySelectorAll('.clean-cat-head').forEach(head => {
    head.addEventListener('click', (e) => {
      if (e.target.closest('input')) return;
      const cat = head.closest('.clean-cat');
      const key = cat.dataset.key;
      cleanExpanded[key] = !cat.classList.contains('open');
      cat.classList.toggle('open');
    });
  });
  root.querySelectorAll('.cat-cb').forEach(cb => {
    cb.addEventListener('change', () => {
      const key = cb.dataset.key;
      root.querySelectorAll('input.item-cb[data-cat="'+key+'"]').forEach(el => { el.checked = cb.checked; });
      cleanItems.forEach(it => { if (it.category === key) it.selected = cb.checked; });
      updateCleanSelectionSummary();
    });
  });
  root.querySelectorAll('.item-cb').forEach(cb => {
    cb.addEventListener('change', () => {
      const id = cb.dataset.id;
      const it = cleanItems.find(x => x.id === id);
      if (it) it.selected = cb.checked;
      updateCleanSelectionSummary();
    });
  });
  root.querySelectorAll('.reveal').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      post({type:'clean_reveal', path: btn.dataset.path || ''});
    });
  });
  updateCleanSelectionSummary();
}

function scanClean(){
  if (cleanBusy) return;
  cleanBusy = true;
  setCleanBusyUI(true);
  $('clean-success').classList.remove('show');
  const panel = $('clean-progress');
  if (panel) {
    panel.classList.add('show');
    panel.classList.add('indeterminate');
    $('clean-prog-label').textContent = '正在扫描…';
    $('clean-prog-pct').textContent = '0%';
    $('clean-prog-bar').style.width = '8%';
    $('clean-prog-current').textContent = '准备中…';
    $('clean-prog-found').textContent = '已发现 0 项';
    $('clean-prog-bytes').textContent = '0 B';
  }
  $('clean-list').innerHTML = '<div class="clean-empty"><div class="big">正在扫描磁盘</div>正在分析缓存、日志与开发者残留…</div>';
  post({type:'clean_scan'});
}

function openCleanModal(items) {
  cleanPendingIds = items;
  const selected = items || [];
  const bytes = selected.reduce((a,b)=>a+(b.bytes||0),0);
  const caution = selected.filter(it => it.risk === 'caution');
  const mode = ($('clean-trash-mode') && $('clean-trash-mode').checked)
    ? '移至废纸篓（可恢复；清空废纸篓后才真正释放磁盘）'
    : '永久删除（不可恢复）';
  $('clean-modal-title').textContent = '确认清理';
  $('clean-modal-body').textContent = '将处理 ' + selected.length + ' 项，约 ' + formatBytes(bytes) + '。\n方式：' + mode;
  const warn = $('clean-modal-warn');
  if (caution.length) {
    warn.style.display = 'block';
    warn.textContent = '包含 ' + caution.length + ' 个谨慎项（如废纸篓 / Archives / iOS 备份），请确认后再继续。';
  } else {
    warn.style.display = 'none';
  }
  $('clean-modal').classList.add('show');
}

function requestClean(items) {
  if (!items || !items.length) return;
  if (cleanConfirm === false) runCleanWithItems(items);
  else openCleanModal(items);
}

function runCleanWithItems(items) {
  if (cleanBusy || !items || !items.length) return;
  cleanBusy = true;
  setCleanBusyUI(true);
  $('clean-success').classList.remove('show');
  const move = !!( $('clean-trash-mode') && $('clean-trash-mode').checked );
  cleanMoveToTrash = move;
  post({type:'clean_pref', move_to_trash: move});
  const panel = $('clean-progress');
  if (panel) {
    panel.classList.add('show');
    panel.classList.remove('indeterminate');
    $('clean-prog-label').textContent = '正在清理…';
    $('clean-prog-pct').textContent = '0%';
    $('clean-prog-bar').style.width = '0%';
    $('clean-prog-current').textContent = '准备删除…';
    $('clean-prog-found').textContent = '进度 0 / ' + items.length;
    $('clean-prog-bytes').textContent = '已释放 0 B';
  }
  const payloadItems = items.map(it => ({
    id: it.id,
    path: it.path,
    name: it.name,
    category: it.category,
    category_title: it.category_title,
    mode: it.mode || 'all',
    cutoff_days: it.cutoff_days || 7,
    risk: it.risk || 'safe',
    bytes: it.bytes || 0,
  }));
  post({
    type:'clean_run',
    item_ids: payloadItems.map(it => it.id),
    paths: payloadItems.map(it => it.path),
    items: payloadItems,
    move_to_trash: move,
  });
}

$('clean-scan').onclick = scanClean;
$('clean-cancel').onclick = () => { post({type:'clean_cancel'}); };
$('clean-smart').onclick = () => {
  let items = getSelectedCleanItems();
  if (!items.length) {
    document.querySelectorAll('#clean-list input.item-cb').forEach(el => {
      el.checked = el.dataset.risk !== 'caution';
    });
    cleanItems.forEach(it => { it.selected = it.risk !== 'caution'; });
    updateCleanSelectionSummary();
    items = getSelectedCleanItems();
  }
  if (!items.length) {
    $('status').textContent = '请先勾选要清理的项目';
    return;
  }
  requestClean(items);
};
$('clean-modal-cancel').onclick = () => { $('clean-modal').classList.remove('show'); cleanPendingIds = null; };
$('clean-modal-ok').onclick = () => {
  $('clean-modal').classList.remove('show');
  const items = cleanPendingIds || [];
  cleanPendingIds = null;
  runCleanWithItems(items);
};
$('clean-modal').addEventListener('click', (e) => {
  if (e.target === $('clean-modal')) { $('clean-modal').classList.remove('show'); cleanPendingIds = null; }
});
$('clean-sel-all').onclick = () => {
  document.querySelectorAll('#clean-list input.item-cb').forEach(el => { el.checked = true; });
  const visible = new Set([...document.querySelectorAll('#clean-list input.item-cb')].map(el => el.dataset.id));
  cleanItems.forEach(it => { if (visible.has(it.id)) it.selected = true; });
  updateCleanSelectionSummary();
};
$('clean-sel-safe').onclick = () => {
  document.querySelectorAll('#clean-list input.item-cb').forEach(el => {
    el.checked = el.dataset.risk !== 'caution';
  });
  const visible = new Set([...document.querySelectorAll('#clean-list input.item-cb')].map(el => el.dataset.id));
  cleanItems.forEach(it => {
    if (visible.has(it.id)) it.selected = it.risk !== 'caution';
  });
  updateCleanSelectionSummary();
};
$('clean-sel-none').onclick = () => {
  document.querySelectorAll('#clean-list input.item-cb').forEach(el => { el.checked = false; });
  const visible = new Set([...document.querySelectorAll('#clean-list input.item-cb')].map(el => el.dataset.id));
  cleanItems.forEach(it => { if (visible.has(it.id)) it.selected = false; });
  updateCleanSelectionSummary();
};
$('clean-expand').onclick = () => {
  const cats = document.querySelectorAll('#clean-list .clean-cat');
  const allOpen = [...cats].every(c => c.classList.contains('open'));
  cats.forEach(c => {
    cleanExpanded[c.dataset.key] = !allOpen;
    c.classList.toggle('open', !allOpen);
  });
  $('clean-expand').textContent = allOpen ? '展开全部' : '收起全部';
};
['clean-q','clean-sort','clean-minsize','clean-risk'].forEach(id => {
  const el = $(id);
  if (!el) return;
  el.addEventListener(id==='clean-q'?'input':'change', () => renderCleanList());
});
const cleanCatFiltersEl = $('clean-cat-filters');
if (cleanCatFiltersEl) {
  cleanCatFiltersEl.addEventListener('click', (e) => {
    const btn = e.target && e.target.closest ? e.target.closest('[data-clean-cat]') : null;
    if (!btn) return;
    cleanCatFilter = btn.getAttribute('data-clean-cat') || 'all';
    renderCleanCatFilters();
    renderCleanList();
  });
}
const cleanRecommendBtn = $('clean-recommend');
if (cleanRecommendBtn) {
  cleanRecommendBtn.onclick = () => {
    if (!cleanRecommendIds.length) return;
    const want = new Set(cleanRecommendIds.map(String));
    cleanItems.forEach(it => { it.selected = want.has(String(it.id)); });
    document.querySelectorAll('#clean-list input.item-cb').forEach(el => {
      el.checked = want.has(String(el.dataset.id || ''));
    });
    // Expand categories that have recommended items
    cleanCategories.forEach(c => {
      if (cleanItems.some(it => it.category === c.key && want.has(String(it.id)))) {
        cleanExpanded[c.key] = true;
      }
    });
    renderCleanList();
    updateCleanSelectionSummary();
  };
}
const cleanEmptyTrashBtn = $('clean-empty-trash');
if (cleanEmptyTrashBtn) {
  cleanEmptyTrashBtn.onclick = () => {
    if (cleanBusy) return;
    const trashBytes = cleanItems.filter(it => it.category === 'trash').reduce((a, it) => a + (it.bytes || 0), 0);
    const msg = trashBytes
      ? ('将永久清空废纸篓（约 ' + formatBytes(trashBytes) + '），此操作不可恢复。确定继续？')
      : '将永久清空废纸篓，此操作不可恢复。确定继续？';
    if (!window.confirm(msg)) return;
    cleanBusy = true;
    setCleanBusyUI(true);
    const panel = $('clean-progress');
    if (panel) {
      panel.classList.add('show');
      panel.classList.add('indeterminate');
      $('clean-prog-label').textContent = '正在清空废纸篓…';
      $('clean-prog-pct').textContent = '…';
      $('clean-prog-bar').style.width = '30%';
      $('clean-prog-current').textContent = '永久删除废纸篓内容';
    }
    post({type:'clean_empty_trash'});
  };
}
$('clean-trash-mode').onchange = () => {
  cleanMoveToTrash = !!$('clean-trash-mode').checked;
  post({type:'clean_pref', move_to_trash: cleanMoveToTrash});
};

/* —— Software Uninstaller —— */
function setUnBusyUI(busy) {
  const scan = $('un-scan');
  const run = $('un-run');
  const cancel = $('un-cancel');
  if (scan) {
    scan.disabled = !!busy;
    if (!busy) scan.textContent = unApps.length ? '重新扫描' : '扫描应用';
    else scan.textContent = '扫描中…';
  }
  if (run && !busy) updateUnSelectionSummary();
  else if (run) run.disabled = true;
  if (cancel) cancel.style.visibility = busy ? 'visible' : 'hidden';
}

function filteredUnApps() {
  const q = (($('un-q') && $('un-q').value) || '').trim().toLowerCase();
  const filter = ($('un-filter') && $('un-filter').value) || 'all';
  let items = unApps.slice();
  if (filter === 'removable') items = items.filter(a => !a.protected);
  if (filter === 'user') items = items.filter(a => String(a.path||'').indexOf('/Users/') === 0);
  if (q) items = items.filter(a =>
    String(a.name||'').toLowerCase().includes(q) ||
    String(a.bundle_id||'').toLowerCase().includes(q) ||
    String(a.path||'').toLowerCase().includes(q)
  );
  const sort = ($('un-sort') && $('un-sort').value) || 'size';
  if (sort === 'name') items.sort((a,b)=>String(a.name).localeCompare(String(b.name),'zh'));
  else if (sort === 'recent') items.sort((a,b)=>(Number(b.last_used)||0)-(Number(a.last_used)||0));
  else items.sort((a,b)=>(b.bytes||0)-(a.bytes||0));
  return items;
}

function unLetter(name) {
  const s = String(name||'?').trim();
  return (s[0] || '?').toUpperCase();
}

function renderUnApps() {
  const root = $('un-apps');
  if (!root) return;
  const items = filteredUnApps();
  if (!unApps.length) {
    root.innerHTML = '<div class="un-detail-empty"><div class="big">扫描已安装应用</div>点击「扫描应用」开始。</div>';
    return;
  }
  if (!items.length) {
    root.innerHTML = '<div class="un-detail-empty"><div class="big">没有匹配结果</div>试试调整搜索或筛选。</div>';
    return;
  }
  root.innerHTML = items.map(a => {
    const active = unSelectedPath && a.path === unSelectedPath;
    const ico = a.icon
      ? `<img src="${esc(a.icon)}" alt="" />`
      : esc(unLetter(a.name));
    const ver = a.version ? (' · v' + a.version) : '';
    const used = a.last_used_text ? (' · ' + a.last_used_text) : '';
    const badge = a.protected ? ' · 受保护' : (a.apple ? ' · Apple' : '');
    return `<div class="un-app ${active?'active':''} ${a.protected?'protected':''}" data-path="${esc(a.path)}" data-bundle="${esc(a.bundle_id||'')}" data-name="${esc(a.name||'')}" data-protected="${a.protected?1:0}">
      <div class="ico">${ico}</div>
      <div>
        <div class="name">${esc(a.name)}</div>
        <div class="sub">${esc(a.location||'')}${esc(ver)}${esc(used)}${esc(badge)}</div>
      </div>
      <div class="size">${esc(a.size_text||formatBytes(a.bytes||0))}</div>
    </div>`;
  }).join('');
}

function renderUnLeftovers() {
  const root = $('un-leftovers');
  if (!root) return;
  if (!unSelectedPath) {
    root.innerHTML = '<div class="un-detail-empty"><div class="big">选择左侧应用</div>将自动扫描偏好设置、缓存、Application Support、容器等残留。</div>';
    updateUnSelectionSummary();
    return;
  }
  if (!unItems.length && unBusy) {
    root.innerHTML = '<div class="un-detail-empty"><div class="big">正在扫描关联文件…</div></div>';
    return;
  }
  if (!unItems.length) {
    root.innerHTML = '<div class="un-detail-empty"><div class="big">未找到关联文件</div>仍可卸载主程序。</div>';
    updateUnSelectionSummary();
    return;
  }
  const app = unAppDetail || {};
  const ico = app.icon
    ? `<img src="${esc(app.icon)}" alt="" />`
    : esc(unLetter(app.name || 'App'));
  const head = `<div class="un-detail-head">
    <div class="ico">${ico}</div>
    <div>
      <div class="name">${esc(app.name || '应用')}</div>
      <div class="sub">${esc(app.bundle_id || '')} · ${esc(app.size_text || '')} · 关联 ${unItems.filter(i=>i.kind!=='app').length} 项</div>
    </div>
  </div>`;
  const rows = unItems.map(it => `
    <div class="un-row">
      <input type="checkbox" class="un-cb" data-id="${esc(it.id)}" data-path="${esc(it.path||'')}" data-bytes="${it.bytes||0}" data-risk="${esc(it.risk||'safe')}" data-kind="${esc(it.kind||'')}" data-name="${esc(it.name||'')}" data-cat="${esc(it.category_title||'')}" ${it.selected?'checked':''} ${it.required?'disabled':''} />
      <div>
        <div class="name">${esc(it.name)}${it.risk==='caution'?' <span class="badge warn">谨慎</span>':''}${it.required?' <span class="badge">主程序</span>':''}</div>
        <div class="path">${esc(it.path_display || it.path || '')}${it.hint?' · '+esc(it.hint):''}</div>
      </div>
      <div class="size">${esc(it.size_text || formatBytes(it.bytes||0))}</div>
    </div>`).join('');
  root.innerHTML = head + rows;
  updateUnSelectionSummary();
}

function updateUnSelectionSummary() {
  const boxes = [...document.querySelectorAll('#un-leftovers input.un-cb:checked')];
  let bytes = 0;
  boxes.forEach(el => { bytes += Number(el.dataset.bytes || 0); });
  if ($('un-free')) $('un-free').textContent = formatBytes(bytes);
  if ($('un-selected')) $('un-selected').textContent = formatBytes(bytes);
  if ($('un-item-count')) $('un-item-count').textContent = String(boxes.length);
  const run = $('un-run');
  if (run && !unBusy) {
    const protectedSel = unAppDetail && unAppDetail.protected;
    run.disabled = !boxes.length || !!protectedSel;
  }
}

function getSelectedUnItems() {
  const boxes = [...document.querySelectorAll('#un-leftovers input.un-cb:checked')];
  const byId = {};
  unItems.forEach(it => { byId[String(it.id)] = it; });
  const out = [];
  boxes.forEach(el => {
    const id = String(el.dataset.id || '');
    const cached = byId[id];
    if (cached) out.push(cached);
    else out.push({
      id,
      path: el.dataset.path || '',
      name: el.dataset.name || '',
      kind: el.dataset.kind || 'leftover',
      category_title: el.dataset.cat || '',
      bytes: Number(el.dataset.bytes || 0),
    });
  });
  return out;
}

function selectUnApp(path, bundleId, name, protectedFlag) {
  if (unBusy) return;
  unSelectedPath = path;
  unItems = [];
  unAppDetail = { name, path, bundle_id: bundleId, protected: !!protectedFlag };
  renderUnApps();
  renderUnLeftovers();
  if (protectedFlag) {
    $('status').textContent = '该应用受保护，无法卸载';
    return;
  }
  unBusy = true;
  setUnBusyUI(true);
  const panel = $('un-progress');
  if (panel) {
    panel.classList.add('show');
    panel.classList.add('indeterminate');
    $('un-prog-label').textContent = '正在扫描关联文件…';
    $('un-prog-pct').textContent = '…';
    $('un-prog-bar').style.width = '28%';
    $('un-prog-current').textContent = name || path;
  }
  post({type:'uninstall_leftovers', path, bundle_id: bundleId, name});
}

window.__setUninstallProgress = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    unBusy = true;
    setUnBusyUI(true);
    const panel = $('un-progress');
    if (!panel) return;
    panel.classList.add('show');
    const pct = Math.max(0, Math.min(100, Number(data.percent) || 0));
    if (pct > 0) panel.classList.remove('indeterminate');
    else panel.classList.add('indeterminate');
    $('un-prog-label').textContent = data.category || data.phase || '处理中…';
    $('un-prog-pct').textContent = pct ? (pct + '%') : '…';
    $('un-prog-bar').style.width = (pct || 28) + '%';
    $('un-prog-current').textContent = data.current || '—';
  } catch (e) {}
};

window.__setUninstallApps = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    unApps = data.apps || [];
    $('un-total').textContent = data.total_text || formatBytes(data.total_bytes || 0);
    $('un-count').textContent = String(data.app_count || unApps.length);
    $('un-removable').textContent = String(data.removable_count != null ? data.removable_count : unApps.filter(a=>!a.protected).length);
    // Clear selection if app vanished
    if (unSelectedPath && !unApps.some(a => a.path === unSelectedPath)) {
      unSelectedPath = '';
      unItems = [];
      unAppDetail = null;
    }
    renderUnApps();
    renderUnLeftovers();
    const panel = $('un-progress');
    if (panel && !data.will_refresh) {
      panel.classList.remove('indeterminate');
      $('un-prog-label').textContent = data.cancelled ? '已取消' : (data.error || '扫描完成');
      $('un-prog-pct').textContent = '100%';
      $('un-prog-bar').style.width = '100%';
      $('un-prog-current').textContent = '共 ' + (data.app_count || unApps.length) + ' 个应用 · 用时 ' + (data.elapsed || '—') + 's';
      setTimeout(function(){ if (!unBusy) panel.classList.remove('show'); }, 1600);
    }
    unBusy = false;
    setUnBusyUI(false);
  } catch (e) {
    unBusy = false;
    setUnBusyUI(false);
  }
};

window.__setUninstallLeftovers = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    unItems = data.items || [];
    unAppDetail = data.app || unAppDetail;
    if (unAppDetail && unAppDetail.path) unSelectedPath = unAppDetail.path;
    renderUnApps();
    renderUnLeftovers();
    const panel = $('un-progress');
    if (panel) {
      panel.classList.remove('indeterminate');
      $('un-prog-label').textContent = data.error || (data.cancelled ? '已取消' : '关联文件扫描完成');
      $('un-prog-pct').textContent = '100%';
      $('un-prog-bar').style.width = '100%';
      $('un-prog-current').textContent = '关联 ' + (data.leftover_count || 0) + ' 项 · ' + (data.leftover_text || '0 B');
      setTimeout(function(){ if (!unBusy) panel.classList.remove('show'); }, 1400);
    }
    unBusy = false;
    setUnBusyUI(false);
  } catch (e) {
    unBusy = false;
    setUnBusyUI(false);
  }
};

window.__setUninstallResult = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    const panel = $('un-progress');
    if (panel) {
      panel.classList.add('show');
      panel.classList.remove('indeterminate');
      $('un-prog-label').textContent = data.cancelled ? '已取消' : (data.will_refresh ? '卸载完成 · 刷新中' : '卸载完成');
      $('un-prog-pct').textContent = '100%';
      $('un-prog-bar').style.width = '100%';
      $('un-prog-current').textContent = (data.action_label || '') + ' · ' + (data.freed_text || '0 B');
    }
    const ok = $('un-success');
    if (ok) {
      ok.classList.add('show');
      $('un-success-t').textContent = data.cancelled ? '已取消 · 部分完成' : '卸载完成';
      $('un-success-s').textContent = (data.freed_text || '0 B') + ' · ' + (data.removed_items || 0) + ' 项 · ' + (data.action_label || '')
        + ((data.errors && data.errors.length) ? (' · ' + data.errors.length + ' 个错误') : '');
    }
    if (data.errors && data.errors.length) $('status').textContent = '卸载错误: ' + data.errors[0];
    unSelectedPath = '';
    unItems = [];
    unAppDetail = null;
    if (data.will_refresh && !data.cancelled) {
      unBusy = true;
      setUnBusyUI(true);
    } else {
      unBusy = false;
      setUnBusyUI(false);
      renderUnApps();
      renderUnLeftovers();
    }
  } catch (e) {
    unBusy = false;
    setUnBusyUI(false);
  }
};

if ($('un-scan')) $('un-scan').onclick = () => {
  if (unBusy) return;
  unBusy = true;
  setUnBusyUI(true);
  const panel = $('un-progress');
  if (panel) {
    panel.classList.add('show');
    panel.classList.add('indeterminate');
    $('un-prog-label').textContent = '正在扫描应用…';
    $('un-prog-pct').textContent = '…';
    $('un-prog-bar').style.width = '25%';
    $('un-prog-current').textContent = 'Applications';
  }
  const ok = $('un-success');
  if (ok) ok.classList.remove('show');
  post({type:'uninstall_scan'});
};
if ($('un-cancel')) $('un-cancel').onclick = () => post({type:'uninstall_cancel'});
if ($('un-apps')) $('un-apps').addEventListener('click', (e) => {
  const row = e.target && e.target.closest ? e.target.closest('.un-app') : null;
  if (!row) return;
  selectUnApp(
    row.getAttribute('data-path') || '',
    row.getAttribute('data-bundle') || '',
    row.getAttribute('data-name') || '',
    row.getAttribute('data-protected') === '1'
  );
});
if ($('un-leftovers')) $('un-leftovers').addEventListener('change', (e) => {
  if (!(e.target && e.target.classList && e.target.classList.contains('un-cb'))) return;
  const id = String(e.target.dataset.id || '');
  unItems.forEach(it => { if (String(it.id) === id && !it.required) it.selected = !!e.target.checked; });
  updateUnSelectionSummary();
});
['un-q','un-sort','un-filter'].forEach(id => {
  const el = $(id);
  if (!el) return;
  el.addEventListener(id==='un-q'?'input':'change', () => renderUnApps());
});
if ($('un-sel-all')) $('un-sel-all').onclick = () => {
  document.querySelectorAll('#un-leftovers input.un-cb').forEach(el => { if (!el.disabled) el.checked = true; });
  unItems.forEach(it => { if (!it.required) it.selected = true; else it.selected = true; });
  updateUnSelectionSummary();
};
if ($('un-sel-safe')) $('un-sel-safe').onclick = () => {
  document.querySelectorAll('#un-leftovers input.un-cb').forEach(el => {
    if (el.disabled) { el.checked = true; return; }
    el.checked = el.dataset.risk !== 'caution';
  });
  unItems.forEach(it => {
    if (it.required) it.selected = true;
    else it.selected = it.risk !== 'caution';
  });
  updateUnSelectionSummary();
};
if ($('un-sel-none')) $('un-sel-none').onclick = () => {
  document.querySelectorAll('#un-leftovers input.un-cb').forEach(el => {
    if (el.disabled) { el.checked = true; return; }
    el.checked = false;
  });
  unItems.forEach(it => { it.selected = !!it.required; });
  updateUnSelectionSummary();
};
if ($('un-trash-mode')) $('un-trash-mode').onchange = () => {
  unMoveToTrash = !!$('un-trash-mode').checked;
};
if ($('un-run')) $('un-run').onclick = () => {
  const items = getSelectedUnItems();
  if (!items.length || unBusy) return;
  if (unAppDetail && unAppDetail.protected) {
    $('status').textContent = '该应用受保护，无法卸载';
    return;
  }
  const bytes = items.reduce((a, it) => a + (it.bytes || 0), 0);
  const caution = items.filter(it => it.risk === 'caution' && it.kind !== 'app').length;
  unPendingItems = items;
  $('un-modal-title').textContent = '确认卸载';
  $('un-modal-body').textContent = '将处理 ' + items.length + ' 项，约 ' + formatBytes(bytes) + '。\n方式：' + (unMoveToTrash ? '移至废纸篓（可恢复）' : '永久删除');
  const warn = $('un-modal-warn');
  if (caution) {
    warn.style.display = 'block';
    warn.textContent = '包含 ' + caution + ' 个谨慎关联项，请确认后再卸载。';
  } else {
    warn.style.display = 'none';
    warn.textContent = '';
  }
  $('un-modal').classList.add('show');
};
if ($('un-modal-cancel')) $('un-modal-cancel').onclick = () => {
  $('un-modal').classList.remove('show');
  unPendingItems = null;
};
if ($('un-modal-ok')) $('un-modal-ok').onclick = () => {
  $('un-modal').classList.remove('show');
  const items = unPendingItems || [];
  unPendingItems = null;
  if (!items.length) return;
  unBusy = true;
  setUnBusyUI(true);
  const panel = $('un-progress');
  if (panel) {
    panel.classList.add('show');
    panel.classList.add('indeterminate');
    $('un-prog-label').textContent = '正在卸载…';
    $('un-prog-pct').textContent = '…';
    $('un-prog-bar').style.width = '30%';
    $('un-prog-current').textContent = items[0].name || items[0].path || '';
  }
  const ok = $('un-success');
  if (ok) ok.classList.remove('show');
  post({
    type: 'uninstall_run',
    move_to_trash: unMoveToTrash,
    items: items.map(it => ({
      path: it.path,
      name: it.name,
      kind: it.kind,
      category_title: it.category_title,
      bytes: it.bytes || 0,
    })),
  });
};
if ($('un-modal')) $('un-modal').addEventListener('click', (e) => {
  if (e.target === $('un-modal')) { $('un-modal').classList.remove('show'); unPendingItems = null; }
});

/* —— Startup manager —— */
function setSuBusyUI(busy) {
  const scan = $('su-scan');
  if (scan) {
    scan.disabled = !!busy;
    scan.textContent = busy ? '扫描中…' : (suItems.length ? '重新扫描' : '扫描启动项');
  }
  const settings = $('su-settings');
  if (settings) settings.disabled = !!busy;
}

function filteredSuItems() {
  const q = (($('su-q') && $('su-q').value) || '').trim().toLowerCase();
  const filter = ($('su-filter') && $('su-filter').value) || 'all';
  let items = suItems.slice();
  if (filter === 'enabled') items = items.filter(it => !it.disabled && !it.protected);
  if (filter === 'disabled') items = items.filter(it => !!it.disabled);
  if (filter === 'login') items = items.filter(it => it.kind === 'login_item');
  if (filter === 'agent') items = items.filter(it => it.kind === 'launch_agent');
  if (filter === 'user') items = items.filter(it => it.scope === 'user');
  if (q) items = items.filter(it =>
    String(it.name||'').toLowerCase().includes(q) ||
    String(it.label||'').toLowerCase().includes(q) ||
    String(it.path||'').toLowerCase().includes(q) ||
    String(it.program||'').toLowerCase().includes(q)
  );
  return items;
}

function renderStartupList() {
  const root = $('su-list');
  if (!root) return;
  const items = filteredSuItems();
  if (!suItems.length) {
    root.innerHTML = '<div class="su-empty"><div class="big">扫描开机启动项</div>点击「扫描启动项」开始。</div>';
    return;
  }
  if (!items.length) {
    root.innerHTML = '<div class="su-empty"><div class="big">没有匹配结果</div>试试调整搜索或筛选。</div>';
    return;
  }
  root.innerHTML = items.map(it => {
    const on = !it.disabled && !it.protected && it.enabled !== false;
    const kind = it.kind === 'login_item' ? '登录项' : 'LaunchAgent';
    const scope = it.scope === 'system' ? '系统' : '用户';
    const risk = it.risk === 'caution' ? '<span class="badge warn">谨慎</span>' : '';
    const prot = it.protected ? '<span class="badge">受保护</span>' : '';
    const path = it.path_display || it.program_display || it.label || '';
    return `<div class="su-row ${it.protected?'protected':''}" data-id="${esc(it.id)}">
      <div>
        <div class="name">${esc(it.name||it.label||'—')} ${risk}${prot}</div>
        <div class="sub">${esc(path)}</div>
        <div class="tags">
          <span class="badge">${esc(kind)}</span>
          <span class="badge">${esc(scope)}</span>
          <span class="badge">${esc(it.detail||'')}</span>
        </div>
      </div>
      <div class="right">
        <button class="btn-mini" type="button" data-su-reveal="${esc(it.path||'')}" ${!(it.path)?'disabled':''}>显示</button>
        <button class="su-switch ${on?'on':''}" type="button" role="switch" aria-checked="${on?'true':'false'}" data-su-toggle="${esc(it.id)}" ${it.protected||suBusy?'disabled':''} title="${on?'点击关闭':'点击开启'}"></button>
      </div>
    </div>`;
  }).join('');
}

function showSuToast(ok, title, msg) {
  const el = $('su-toast');
  if (!el) return;
  el.classList.add('show');
  el.classList.toggle('warn', !ok);
  $('su-toast-t').textContent = title || (ok ? '操作完成' : '操作失败');
  $('su-toast-s').textContent = msg || '';
  setTimeout(function(){ el.classList.remove('show'); }, 3200);
}

window.__setStartupProgress = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    suBusy = true;
    setSuBusyUI(true);
    const panel = $('su-progress');
    if (!panel) return;
    panel.classList.add('show');
    const pct = Math.max(0, Math.min(100, Number(data.percent) || 0));
    if (pct > 0) panel.classList.remove('indeterminate');
    else panel.classList.add('indeterminate');
    $('su-prog-label').textContent = data.phase === 'set' ? '正在应用更改…' : '正在扫描…';
    $('su-prog-pct').textContent = pct ? (pct + '%') : '…';
    $('su-prog-bar').style.width = (pct || 28) + '%';
    $('su-prog-current').textContent = data.current || '—';
  } catch (e) {}
};

window.__setStartupList = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    suItems = data.items || [];
    suMeta = data;
    $('su-total').textContent = String(data.item_count != null ? data.item_count : suItems.length);
    $('su-enabled').textContent = String(data.enabled_count != null ? data.enabled_count : 0);
    $('su-disabled').textContent = String(data.disabled_count != null ? data.disabled_count : 0);
    $('su-login').textContent = String(data.login_count != null ? data.login_count : 0);
    $('su-agents').textContent = String(data.agent_count != null ? data.agent_count : 0);
    renderStartupList();
    const panel = $('su-progress');
    if (panel) {
      panel.classList.remove('indeterminate');
      $('su-prog-label').textContent = data.error || (data.cancelled ? '已取消' : '扫描完成');
      $('su-prog-pct').textContent = '100%';
      $('su-prog-bar').style.width = '100%';
      $('su-prog-current').textContent = (data.settings_hint || ('共 ' + suItems.length + ' 项 · 用时 ' + (data.elapsed || '—') + 's'));
      setTimeout(function(){ if (!suBusy) panel.classList.remove('show'); }, 1400);
    }
    suBusy = false;
    setSuBusyUI(false);
  } catch (e) {
    suBusy = false;
    setSuBusyUI(false);
  }
};

window.__setStartupResult = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    if (data.open_settings) {
      showSuToast(false, '请前往系统设置', data.error || data.message || '');
    } else if (data.ok) {
      showSuToast(true, data.name ? ('已更新「' + data.name + '」') : '操作完成', data.message || '');
    } else {
      showSuToast(false, '操作失败', data.error || data.message || '');
    }
    // Always clear busy here; success path also refreshes the list separately.
    suBusy = false;
    setSuBusyUI(false);
    if (!data.ok) renderStartupList();
  } catch (e) {
    suBusy = false;
    setSuBusyUI(false);
  }
};

if ($('su-scan')) $('su-scan').onclick = () => {
  if (suBusy) return;
  suBusy = true;
  setSuBusyUI(true);
  const panel = $('su-progress');
  if (panel) {
    panel.classList.add('show');
    panel.classList.add('indeterminate');
    $('su-prog-label').textContent = '正在扫描启动项…';
    $('su-prog-pct').textContent = '…';
    $('su-prog-bar').style.width = '25%';
    $('su-prog-current').textContent = 'LaunchAgents / 登录项';
  }
  const toast = $('su-toast');
  if (toast) toast.classList.remove('show');
  post({type:'startup_scan'});
};
if ($('su-settings')) $('su-settings').onclick = () => post({type:'startup_open_settings'});
['su-q','su-filter'].forEach(id => {
  const el = $(id);
  if (!el) return;
  el.addEventListener(id==='su-q'?'input':'change', () => renderStartupList());
});
if ($('su-list')) $('su-list').addEventListener('click', (e) => {
  const reveal = e.target && e.target.closest ? e.target.closest('[data-su-reveal]') : null;
  if (reveal) {
    const path = reveal.getAttribute('data-su-reveal') || '';
    if (path) post({type:'startup_reveal', path});
    return;
  }
  const tog = e.target && e.target.closest ? e.target.closest('[data-su-toggle]') : null;
  if (!tog || tog.disabled || suBusy) return;
  const id = tog.getAttribute('data-su-toggle') || '';
  const item = suItems.find(it => String(it.id) === String(id));
  if (!item || item.protected) return;
  const currentlyOn = !item.disabled && item.enabled !== false;
  const nextEnabled = !currentlyOn;
  const action = nextEnabled ? '启用' : '关闭';
  // Confirm only for destructive / system cases; user agents toggle instantly.
  const needConfirm = (item.kind === 'login_item' && !nextEnabled)
    || item.scope === 'system'
    || item.risk === 'caution';
  if (needConfirm) {
    const tip = item.kind === 'login_item' && !nextEnabled
      ? ('将「' + (item.name||'') + '」从登录项移除？')
      : ('确定' + action + '「' + (item.name||item.label||'') + '」？\n系统级项目关闭后可能影响相关功能。');
    if (!window.confirm(tip)) return;
  }
  // Optimistic UI so the switch responds immediately.
  item.disabled = !nextEnabled;
  item.enabled = nextEnabled;
  tog.classList.toggle('on', nextEnabled);
  tog.setAttribute('aria-checked', nextEnabled ? 'true' : 'false');
  tog.title = nextEnabled ? '点击关闭' : '点击开启';
  suBusy = true;
  setSuBusyUI(true);
  const panel = $('su-progress');
  if (panel) {
    panel.classList.add('show');
    panel.classList.add('indeterminate');
    $('su-prog-label').textContent = '正在' + action + '…';
    $('su-prog-pct').textContent = '…';
    $('su-prog-bar').style.width = '30%';
    $('su-prog-current').textContent = item.name || item.label || '';
  }
  post({type:'startup_set', enabled: nextEnabled, item: {
    id: item.id,
    kind: item.kind,
    label: item.label,
    name: item.name,
    path: item.path,
    scope: item.scope,
    protected: item.protected,
  }});
});

let shotBusy = false;
let shotLastPath = '';
let shotToastTimer = null;
let shotEditor = {
  open: false,
  draft: '',
  alsoCopy: false,
  tool: 'pen',
  color: '#ff3b30',
  size: 4,
  strokes: [],
  redo: [],
  drawing: false,
  current: null,
  img: null,
  scale: 1,
  dpr: 1,
  textEl: null
};

function formatHotkeyLabel(spec){
  if (!spec) return '未设置';
  const parts = String(spec).toLowerCase().split('+').filter(Boolean);
  if (!parts.length) return '未设置';
  const key = parts[parts.length-1];
  const mods = parts.slice(0,-1);
  const map = {ctrl:'⌃', alt:'⌥', shift:'⇧', cmd:'⌘'};
  const special = {space:'空格', return:'↩', enter:'↩', escape:'⎋', esc:'⎋', tab:'⇥', delete:'⌫', backspace:'⌫'};
  const k = special[key] || (key.length===1 ? key.toUpperCase() : key);
  return mods.map(m => map[m]||m).join('') + k;
}
function syncHotkeyUI(){
  const map = {
    hotkey_shot_selection: ['hk-btn-selection','set-hk-selection','shot-hk-sel-label'],
    hotkey_shot_window: ['hk-btn-window','set-hk-window','shot-hk-win-label'],
    hotkey_shot_full: ['hk-btn-full','set-hk-full','shot-hk-full-label'],
    hotkey_rec_selection: ['hk-btn-rec-sel','rec-hk-sel-label'],
    hotkey_rec_full: ['hk-btn-rec-full','rec-hk-full-label'],
    hotkey_rec_stop: ['hk-btn-rec-stop','rec-hk-stop-label'],
  };
  Object.keys(map).forEach(id => {
    const spec = appSettings[id] || '';
    const label = appSettings[id + '_label'] || formatHotkeyLabel(spec);
    map[id].forEach(elId => {
      const el = $(elId);
      if (!el) return;
      if (el.classList.contains('recording')) return;
      el.textContent = label;
    });
  });
  const hint = $('shot-hk-hint');
  const setHint = $('set-hk-hint');
  const globalOk = appSettings.global_ok !== false;
  const tip = globalOk
    ? '点击按键位可录制新快捷键；Esc 取消，Delete 清除。默认 ⌃⌘3 / 4 / 5，避免与系统 ⌘⇧ 截图冲突。'
    : '当前仅前台快捷键可用。若要后台触发，请授予「辅助功能」权限。';
  if (hint) {
    hint.textContent = tip;
    hint.classList.toggle('warn', !globalOk);
  }
  if (setHint) setHint.textContent = tip;
  const axBannerNeed = !globalOk;
  document.querySelectorAll('[data-perm-hint="accessibility"]').forEach(el => {
    el.style.display = axBannerNeed ? '' : 'none';
  });
  const screenOk = appSettings.screen_ok !== false;
  ['shot-perm-banner','rec-perm-banner'].forEach(id => {
    const el = $(id);
    if (el) el.classList.toggle('show', !screenOk);
  });
}
function syncShotPrefsUI(){
  const hide = $('shot-hide'); if (hide) hide.checked = appSettings.screenshot_hide_self !== false;
  const clip = $('shot-clip'); if (clip) clip.checked = !!appSettings.screenshot_clipboard;
  const cur = $('shot-cursor'); if (cur) cur.checked = !!appSettings.screenshot_cursor;
  const delay = $('shot-delay');
  if (delay && appSettings.screenshot_delay != null) {
    const v = String(appSettings.screenshot_delay);
    if (![...delay.options].some(o => o.value === v)) {
      const opt = document.createElement('option');
      opt.value = v; opt.textContent = v + ' 秒';
      delay.appendChild(opt);
    }
    delay.value = v;
  }
  syncHotkeyUI();
}

function syncRecPrefsUI(){
  const hide = $('rec-hide'); if (hide) hide.checked = appSettings.recording_hide_self !== false;
  const mic = $('rec-mic'); if (mic) mic.checked = !!appSettings.recording_mic;
  const sys = $('rec-sysaudio'); if (sys) sys.checked = !!appSettings.recording_system_audio;
  const clicks = $('rec-clicks'); if (clicks) clicks.checked = appSettings.recording_clicks !== false;
  const openAfter = $('rec-open-after'); if (openAfter) openAfter.checked = !!appSettings.recording_open_after;
  const cd = $('rec-countdown-sel');
  if (cd && appSettings.recording_countdown != null) cd.value = String(appSettings.recording_countdown);
  const mx = $('rec-max');
  if (mx && appSettings.recording_max_seconds != null) mx.value = String(appSettings.recording_max_seconds);
  syncHotkeyUI();
}

function shotOpts(){
  return {
    hide_self: !!($('shot-hide') && $('shot-hide').checked),
    clipboard: !!($('shot-clip') && $('shot-clip').checked),
    cursor: !!($('shot-cursor') && $('shot-cursor').checked),
    delay: Number(($('shot-delay') && $('shot-delay').value) || 0.5),
  };
}

function connToneColor(tone){
  return ({
    excellent: '#30d158',
    good: '#0a84ff',
    fair: '#ffd60a',
    poor: '#ff9f0a',
    fail: '#ff453a'
  })[tone] || '#0a84ff';
}
function setConnBusy(busy){
  connBusy = !!busy;
  const start = $('conn-start');
  const cancel = $('conn-cancel');
  const ring = $('conn-ring');
  if (start) {
    start.disabled = connBusy;
    start.textContent = connBusy ? '检测中…' : (connData && connData.phase === 'done' ? '重新检测' : '开始检测');
  }
  if (cancel) cancel.style.display = connBusy ? '' : 'none';
  if (ring) ring.classList.toggle('busy', connBusy);
  const prog = $('conn-progress');
  if (prog) prog.classList.toggle('on', connBusy);
}
function renderConnStatus(data){
  const el = $('conn-status');
  if (!el) return;
  if (!data) {
    el.innerHTML = '<span class="conn-pill muted">尚未检测</span>';
    return;
  }
  const pills = [];
  if (data.busy || data.phase === 'progress' || data.phase === 'start') {
    pills.push('<span class="conn-pill">检测进行中</span>');
    if (data.current) pills.push('<span class="conn-pill muted">'+esc(data.current)+'</span>');
  } else if (data.phase === 'cancelled') {
    pills.push('<span class="conn-pill warn">已取消</span>');
  } else {
    const tone = data.tone || 'good';
    const cls = tone === 'fail' || tone === 'poor' ? 'fail' : (tone === 'fair' ? 'warn' : 'ok');
    pills.push('<span class="conn-pill '+cls+'">'+esc(data.label || '完成')+'</span>');
    if (data.ok_count != null) pills.push('<span class="conn-pill muted">'+esc(data.ok_count)+'/'+esc(data.total)+' 通过</span>');
    if (data.avg_ms != null) pills.push('<span class="conn-pill muted">均延 '+esc(data.avg_ms)+' ms</span>');
  }
  el.innerHTML = pills.join('');
}
function renderConnRing(data){
  const ring = $('conn-ring');
  const scoreEl = $('conn-score');
  const unit = $('conn-score-unit');
  if (!ring || !scoreEl) return;
  let p = 0;
  let tone = 'good';
  if (data && data.busy && data.percent != null) {
    p = Math.max(0, Math.min(100, Number(data.percent) || 0));
    scoreEl.textContent = String(Math.round(p));
    if (unit) unit.textContent = '进度 %';
  } else if (data && data.score != null && data.phase === 'done') {
    p = Math.max(0, Math.min(100, Number(data.score) || 0));
    tone = data.tone || 'good';
    scoreEl.textContent = String(Math.round(p));
    if (unit) unit.textContent = esc(data.label || '连通指数');
  } else if (data && data.score != null) {
    p = Math.max(0, Math.min(100, Number(data.score) || 0));
    tone = data.tone || 'good';
    scoreEl.textContent = String(Math.round(p));
    if (unit) unit.textContent = '连通指数';
  } else {
    scoreEl.textContent = '—';
    if (unit) unit.textContent = '连通指数';
  }
  ring.style.setProperty('--p', String(p));
  ring.style.setProperty('--ring', connToneColor(tone));
}
function renderConnKpis(data){
  const box = $('conn-kpis');
  if (!box) return;
  if (!data || data.phase !== 'done') {
    if (!(data && data.ok_count != null && !data.busy)) {
      // keep visible during live progress after first result
    }
  }
  const show = !!(data && (data.ok_count != null || data.score != null));
  box.style.display = show ? '' : 'none';
  if (!show) return;
  const rate = data.success_rate != null ? data.success_rate : (data.total ? Math.round(100 * (data.ok_count||0) / data.total) : null);
  $('conn-kpi-rate').textContent = rate != null ? (String(rate) + '%') : '—';
  $('conn-kpi-rate-s').textContent = (data.ok_count != null && data.total != null) ? (data.ok_count + ' / ' + data.total + ' 通过') : '通过项';
  $('conn-kpi-avg').textContent = data.avg_ms != null ? String(data.avg_ms) : '—';
  $('conn-kpi-label').textContent = data.label || '—';
  $('conn-kpi-time').textContent = data.checked_at || '—';
  const elapsed = data.elapsed_ms;
  $('conn-kpi-elapsed').textContent = elapsed != null ? ((elapsed >= 1000) ? ((elapsed/1000).toFixed(1) + 's') : (elapsed + 'ms')) : '—';
}
function renderConnGroups(data){
  const root = $('conn-groups');
  if (!root) return;
  const groups = (data && data.groups) || [];
  const results = (data && data.results) || [];
  if (!groups.length && !results.length) {
    root.innerHTML = '<div class="conn-empty" id="conn-empty"><b>一键诊断你的网络</b>将对阿里 / 腾讯 DNS、Apple / 微软 / Cloudflare 节点，以及百度、腾讯、GitHub 等站点进行连通测试。</div>';
    return;
  }
  const useGroups = groups.length ? groups : [{
    title: '检测结果',
    desc: '',
    ok_count: results.filter(r => r.ok).length,
    total: results.length,
    items: results
  }];
  root.innerHTML = useGroups.map(g => {
    const items = g.items || [];
    const rows = items.map(it => {
      const ms = it.ms != null ? (Number(it.ms).toFixed(0) + ' ms') : '—';
      const grade = it.grade || 'fail';
      const detail = it.detail || '';
      return '<div class="conn-row">'
        + '<div><div class="name">'+esc(it.name||'')+'</div><div class="detail">'+esc(detail)+'</div></div>'
        + '<div class="conn-lat">'+esc(ms)+'</div>'
        + '<div class="conn-grade '+esc(grade)+'">'+esc(it.grade_cn || grade)+'</div>'
        + '</div>';
    }).join('');
    return '<div class="conn-group">'
      + '<div class="conn-group-head"><div><div class="t">'+esc(g.title||'')+'</div><div class="d">'+esc(g.desc||'')+'</div></div>'
      + '<div class="badge">'+(g.ok_count!=null?esc(g.ok_count)+'/'+esc(g.total):'')+'</div></div>'
      + rows + '</div>';
  }).join('');
}
function applyConnectivity(data){
  connData = data || connData;
  const d = data || {};
  const busy = !!(d.busy || d.phase === 'start' || d.phase === 'progress');
  setConnBusy(busy);
  if ($('conn-prog-label')) $('conn-prog-label').textContent = d.message || (busy ? '检测中…' : '准备检测…');
  const pct = Math.max(0, Math.min(100, Number(d.percent) || 0));
  if ($('conn-prog-pct')) $('conn-prog-pct').textContent = Math.round(pct) + '%';
  if ($('conn-prog-bar')) $('conn-prog-bar').style.width = pct + '%';
  if ($('conn-title')) {
    if (d.phase === 'done') $('conn-title').textContent = '网络' + (d.label || '检测完成');
    else if (busy) $('conn-title').textContent = '正在检测…';
    else $('conn-title').textContent = '网络连通性';
  }
  if ($('conn-sub') && d.phase === 'done' && d.message) {
    $('conn-sub').textContent = '本轮覆盖 DNS、节点握手与网站访问。可随时重新检测以对比波动。';
  }
  renderConnRing(d);
  renderConnStatus(d);
  renderConnKpis(d);
  if (d.groups || d.results) renderConnGroups(d);
}
window.__setConnectivityProgress = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    applyConnectivity(Object.assign({}, connData || {}, data || {}, {busy: true}));
  } catch (e) {}
};
window.__setConnectivityResult = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    applyConnectivity(Object.assign({}, data || {}, {busy: false}));
  } catch (e) {}
};

function shotEdCanvas(){ return $('shot-ed-canvas'); }
function shotEdCtx(){
  const c = shotEdCanvas();
  return c ? c.getContext('2d') : null;
}
function shotEdPtr(e){
  const c = shotEdCanvas();
  if (!c) return {x:0,y:0};
  const r = c.getBoundingClientRect();
  const x = (e.clientX - r.left) * (c.width / Math.max(1, r.width));
  const y = (e.clientY - r.top) * (c.height / Math.max(1, r.height));
  return {x, y};
}
function shotEdDrawArrow(ctx, x1, y1, x2, y2, color, width){
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx*dx + dy*dy) || 1;
  const ux = dx / len, uy = dy / len;
  const head = Math.max(10, width * 3.2);
  ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = width;
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - ux*head - uy*head*0.55, y2 - uy*head + ux*head*0.55);
  ctx.lineTo(x2 - ux*head + uy*head*0.55, y2 - uy*head - ux*head*0.55);
  ctx.closePath(); ctx.fill();
}
function shotEdApplyMosaic(ctx, x1, y1, x2, y2, block){
  const c = shotEdCanvas();
  if (!c) return;
  const left = Math.max(0, Math.floor(Math.min(x1, x2)));
  const top = Math.max(0, Math.floor(Math.min(y1, y2)));
  const right = Math.min(c.width, Math.ceil(Math.max(x1, x2)));
  const bottom = Math.min(c.height, Math.ceil(Math.max(y1, y2)));
  const w = right - left, h = bottom - top;
  if (w < 2 || h < 2) return;
  const b = Math.max(4, block|0);
  try {
    const img = ctx.getImageData(left, top, w, h);
    const d = img.data;
    for (let y = 0; y < h; y += b) {
      for (let x = 0; x < w; x += b) {
        const i = ((y * w) + x) * 4;
        const r = d[i], g = d[i+1], bl = d[i+2], a = d[i+3];
        for (let yy = y; yy < Math.min(y+b, h); yy++) {
          for (let xx = x; xx < Math.min(x+b, w); xx++) {
            const j = ((yy * w) + xx) * 4;
            d[j]=r; d[j+1]=g; d[j+2]=bl; d[j+3]=a;
          }
        }
      }
    }
    ctx.putImageData(img, left, top);
  } catch (_) {}
}
function shotEdPaintStroke(ctx, s, live){
  if (!s) return;
  const color = s.color || '#ff3b30';
  const width = s.size || 4;
  if (s.tool === 'pen' || s.tool === 'highlight') {
    const pts = s.points || [];
    if (pts.length < 1) return;
    ctx.save();
    if (s.tool === 'highlight') {
      ctx.globalAlpha = 0.35;
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(12, width * 3);
    } else {
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
    }
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
    ctx.stroke();
    ctx.restore();
  } else if (s.tool === 'rect') {
    ctx.strokeStyle = color; ctx.lineWidth = width;
    ctx.strokeRect(s.x1, s.y1, s.x2 - s.x1, s.y2 - s.y1);
  } else if (s.tool === 'ellipse') {
    const cx = (s.x1 + s.x2) / 2, cy = (s.y1 + s.y2) / 2;
    const rx = Math.abs(s.x2 - s.x1) / 2, ry = Math.abs(s.y2 - s.y1) / 2;
    ctx.strokeStyle = color; ctx.lineWidth = width;
    ctx.beginPath(); ctx.ellipse(cx, cy, Math.max(1,rx), Math.max(1,ry), 0, 0, Math.PI*2); ctx.stroke();
  } else if (s.tool === 'arrow') {
    shotEdDrawArrow(ctx, s.x1, s.y1, s.x2, s.y2, color, width);
  } else if (s.tool === 'text' && s.text) {
    ctx.fillStyle = color;
    ctx.font = '700 ' + Math.max(14, width * 4) + 'px -apple-system, sans-serif';
    ctx.textBaseline = 'top';
    ctx.fillText(s.text, s.x1, s.y1);
  } else if (s.tool === 'mosaic' && !live) {
    shotEdApplyMosaic(ctx, s.x1, s.y1, s.x2, s.y2, Math.max(6, width * 2));
  } else if (s.tool === 'mosaic' && live) {
    ctx.save();
    ctx.strokeStyle = 'rgba(255,255,255,0.7)';
    ctx.setLineDash([6,4]);
    ctx.lineWidth = 1;
    ctx.strokeRect(s.x1, s.y1, s.x2 - s.x1, s.y2 - s.y1);
    ctx.restore();
  }
}
function shotEdRedraw(){
  const ctx = shotEdCtx();
  const c = shotEdCanvas();
  const img = shotEditor.img;
  if (!ctx || !c || !img) return;
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.drawImage(img, 0, 0, c.width, c.height);
  shotEditor.strokes.forEach(s => shotEdPaintStroke(ctx, s, false));
  if (shotEditor.current) shotEdPaintStroke(ctx, shotEditor.current, true);
}
function shotEdCommitText(){
  const el = shotEditor.textEl;
  if (!el) return;
  const text = (el.value || '').trim();
  const x = Number(el.dataset.x || 0);
  const y = Number(el.dataset.y || 0);
  el.remove();
  shotEditor.textEl = null;
  if (!text) return;
  shotEditor.strokes.push({
    tool: 'text', text, x1: x, y1: y,
    color: shotEditor.color, size: shotEditor.size
  });
  shotEditor.redo = [];
  shotEdRedraw();
}
function shotEdExportDataUrl(){
  const src = shotEdCanvas();
  if (!src) return '';
  // Flatten on a clean canvas at natural pixel size
  const out = document.createElement('canvas');
  out.width = src.width; out.height = src.height;
  const ctx = out.getContext('2d');
  if (!ctx) return '';
  if (shotEditor.img) ctx.drawImage(shotEditor.img, 0, 0, out.width, out.height);
  shotEditor.strokes.forEach(s => shotEdPaintStroke(ctx, s, false));
  try { return out.toDataURL('image/png'); } catch (_) { return ''; }
}
function closeScreenshotEditor(){
  shotEdCommitText();
  const ed = $('shot-editor');
  if (ed) {
    ed.classList.remove('open');
    ed.setAttribute('aria-hidden', 'true');
  }
  shotEditor.open = false;
  shotEditor.draft = '';
  shotEditor.strokes = [];
  shotEditor.redo = [];
  shotEditor.current = null;
  shotEditor.img = null;
  if (shotEditor.textEl) {
    try { shotEditor.textEl.remove(); } catch(_){}
    shotEditor.textEl = null;
  }
}
function openScreenshotEditor(payload){
  const data = payload || {};
  const ed = $('shot-editor');
  const canvas = shotEdCanvas();
  if (!ed || !canvas || !data.preview) return;
  shotEdCommitText();
  shotEditor.open = true;
  shotEditor.draft = data.draft || '';
  shotEditor.alsoCopy = !!data.also_copy;
  shotEditor.strokes = [];
  shotEditor.redo = [];
  shotEditor.current = null;
  shotEditor.tool = 'pen';
  document.querySelectorAll('.shot-ed-tool').forEach(b => {
    b.classList.toggle('active', b.dataset.tool === 'pen');
  });
  const meta = $('shot-ed-meta');
  if (meta) {
    const f = data.file || {};
    meta.textContent = (f.size_text ? f.size_text + ' · ' : '') + '标记后保存到图片 / SupTools';
  }
  const img = new Image();
  img.onload = function(){
    const maxW = Math.max(320, window.innerWidth - 48);
    const maxH = Math.max(240, window.innerHeight - 190);
    let w = img.naturalWidth || img.width;
    let h = img.naturalHeight || img.height;
    const scale = Math.min(1, maxW / w, maxH / h);
    // Keep full resolution for export quality
    canvas.width = w;
    canvas.height = h;
    canvas.style.width = Math.round(w * scale) + 'px';
    canvas.style.height = Math.round(h * scale) + 'px';
    shotEditor.img = img;
    shotEditor.scale = scale;
    shotEdRedraw();
  };
  img.src = data.preview;
  ed.classList.add('open');
  ed.setAttribute('aria-hidden', 'false');
  try { window.__navigate({page:'shot'}); } catch(_){}
}
window.__openScreenshotEditor = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    openScreenshotEditor(data || {});
  } catch (e) {}
};
window.__closeScreenshotEditor = function(){
  closeScreenshotEditor();
};

function setShotBusy(busy, message){
  shotBusy = !!busy;
  const banner = $('shot-busy');
  if (banner) {
    banner.classList.toggle('show', shotBusy);
    if (message) banner.textContent = message;
  }
  document.querySelectorAll('.shot-action').forEach(b => { b.disabled = shotBusy; });
}

function showShotToast(ok, message){
  const el = $('shot-toast');
  if (!el || !message) return;
  el.textContent = message;
  el.classList.toggle('bad', !ok);
  el.classList.add('show');
  if (shotToastTimer) clearTimeout(shotToastTimer);
  shotToastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

function renderShotPreview(data){
  const box = $('shot-preview');
  const meta = $('shot-meta');
  if (!box) return;
  if (data && data.preview) {
    box.innerHTML = '<img alt="preview" src="'+data.preview+'" />';
  } else if (data && data.path) {
    box.innerHTML = '<div class="empty"><b>截图已保存</b>'+esc(data.path)+'</div>';
  } else {
    box.innerHTML = '<div class="empty"><b>还没有截图</b>点击上方按钮开始</div>';
  }
  if (meta) {
    if (data && data.file) {
      const f = data.file;
      meta.innerHTML =
        '<button type="button" class="btn-mini" data-shot-act="open" data-path="'+esc(f.path)+'">打开</button>'+
        '<button type="button" class="btn-mini" data-shot-act="reveal" data-path="'+esc(f.path)+'">显示</button>'+
        '<button type="button" class="btn-mini" data-shot-act="copy" data-path="'+esc(f.path)+'">复制</button>'+
        '<span class="muted">'+esc(f.size_text||'')+' · '+esc(f.mtime_text||'')+'</span>';
    } else {
      meta.innerHTML = '';
    }
  }
}

function renderShotList(payload){
  const list = $('shot-list');
  const folder = $('shot-folder-path');
  if (folder) folder.textContent = (payload && payload.folder) || '—';
  if (!list) return;
  const items = (payload && payload.items) || [];
  if (!items.length) {
    list.innerHTML = '<div class="muted" style="padding:12px 4px">暂无历史截图</div>';
    return;
  }
  list.innerHTML = items.map(it => `
    <div class="shot-row">
      <div>
        <div class="name">${esc(it.name)}</div>
        <div class="sub">${esc(it.mtime_text||'')} · ${esc(it.size_text||'')}</div>
      </div>
      <div class="acts">
        <button type="button" class="btn-mini" data-shot-act="open" data-path="${esc(it.path)}">打开</button>
        <button type="button" class="btn-mini" data-shot-act="reveal" data-path="${esc(it.path)}">显示</button>
        <button type="button" class="btn-mini" data-shot-act="copy" data-path="${esc(it.path)}">复制</button>
        <button type="button" class="btn-mini danger" data-shot-act="delete" data-path="${esc(it.path)}">删除</button>
      </div>
    </div>`).join('');
}

function startShot(mode){
  if (shotBusy) return;
  const opts = shotOpts();
  setShotBusy(true, mode === 'full' ? '正在全屏截图…' : '请选择截图区域（Esc 取消）…');
  post({
    type: 'screenshot_capture',
    mode: mode,
    hide_self: opts.hide_self,
    clipboard: opts.clipboard,
    cursor: opts.cursor,
    delay: opts.delay,
  });
}

document.querySelectorAll('.shot-action').forEach(btn => {
  btn.onclick = () => startShot(btn.dataset.mode || 'selection');
});

(function setupShotEditor(){
  const canvas = shotEdCanvas();
  if (!canvas) return;
  document.querySelectorAll('.shot-ed-tool').forEach(btn => {
    btn.onclick = () => {
      shotEdCommitText();
      shotEditor.tool = btn.dataset.tool || 'pen';
      document.querySelectorAll('.shot-ed-tool').forEach(b => b.classList.toggle('active', b === btn));
    };
  });
  document.querySelectorAll('.shot-ed-color').forEach(btn => {
    btn.onclick = () => {
      shotEditor.color = btn.dataset.color || '#ff3b30';
      document.querySelectorAll('.shot-ed-color').forEach(b => b.classList.toggle('active', b === btn));
    };
  });
  const size = $('shot-ed-size');
  if (size) size.oninput = () => { shotEditor.size = Number(size.value) || 4; };
  if ($('shot-ed-undo')) $('shot-ed-undo').onclick = () => {
    shotEdCommitText();
    if (!shotEditor.strokes.length) return;
    shotEditor.redo.push(shotEditor.strokes.pop());
    shotEdRedraw();
  };
  if ($('shot-ed-redo')) $('shot-ed-redo').onclick = () => {
    if (!shotEditor.redo.length) return;
    shotEditor.strokes.push(shotEditor.redo.pop());
    shotEdRedraw();
  };
  if ($('shot-ed-clear')) $('shot-ed-clear').onclick = () => {
    shotEdCommitText();
    if (!shotEditor.strokes.length) return;
    shotEditor.redo = shotEditor.redo.concat(shotEditor.strokes.slice().reverse());
    shotEditor.strokes = [];
    shotEdRedraw();
  };
  if ($('shot-ed-cancel')) $('shot-ed-cancel').onclick = () => {
    const draft = shotEditor.draft;
    closeScreenshotEditor();
    post({type:'screenshot_annotate_cancel', draft});
  };
  if ($('shot-ed-copy')) $('shot-ed-copy').onclick = () => {
    shotEdCommitText();
    const data_url = shotEdExportDataUrl();
    if (!data_url) { showShotToast(false, '导出失败'); return; }
    post({type:'screenshot_annotate_copy', data_url, draft: shotEditor.draft});
  };
  if ($('shot-ed-save')) $('shot-ed-save').onclick = () => {
    shotEdCommitText();
    const data_url = shotEdExportDataUrl();
    if (!data_url) { showShotToast(false, '导出失败'); return; }
    post({
      type:'screenshot_annotate_save',
      data_url,
      draft: shotEditor.draft,
      copy: !!shotEditor.alsoCopy || !!($('shot-clip') && $('shot-clip').checked)
    });
  };

  function onDown(e){
    if (!shotEditor.open || !shotEditor.img) return;
    if (e.button != null && e.button !== 0) return;
    e.preventDefault();
    const p = shotEdPtr(e);
    shotEdCommitText();
    if (shotEditor.tool === 'text') {
      const wrap = $('shot-ed-wrap');
      if (!wrap) return;
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'shot-ed-text-input';
      input.placeholder = '输入文字，Enter 确认';
      input.dataset.x = String(p.x);
      input.dataset.y = String(p.y);
      const r = canvas.getBoundingClientRect();
      const wr = wrap.getBoundingClientRect();
      input.style.left = (r.left - wr.left + (p.x / canvas.width) * r.width) + 'px';
      input.style.top = (r.top - wr.top + (p.y / canvas.height) * r.height) + 'px';
      input.style.color = shotEditor.color;
      wrap.appendChild(input);
      shotEditor.textEl = input;
      input.focus();
      input.onkeydown = (ev) => {
        if (ev.key === 'Enter') { ev.preventDefault(); shotEdCommitText(); }
        if (ev.key === 'Escape') {
          ev.preventDefault();
          input.remove();
          shotEditor.textEl = null;
        }
      };
      input.onblur = () => shotEdCommitText();
      return;
    }
    shotEditor.drawing = true;
    shotEditor.redo = [];
    if (shotEditor.tool === 'pen' || shotEditor.tool === 'highlight') {
      shotEditor.current = {
        tool: shotEditor.tool,
        color: shotEditor.color,
        size: shotEditor.size,
        points: [p]
      };
    } else {
      shotEditor.current = {
        tool: shotEditor.tool,
        color: shotEditor.color,
        size: shotEditor.size,
        x1: p.x, y1: p.y, x2: p.x, y2: p.y
      };
    }
    shotEdRedraw();
  }
  function onMove(e){
    if (!shotEditor.drawing || !shotEditor.current) return;
    e.preventDefault();
    const p = shotEdPtr(e);
    if (shotEditor.current.points) shotEditor.current.points.push(p);
    else { shotEditor.current.x2 = p.x; shotEditor.current.y2 = p.y; }
    shotEdRedraw();
  }
  function onUp(e){
    if (!shotEditor.drawing || !shotEditor.current) return;
    e.preventDefault();
    const cur = shotEditor.current;
    shotEditor.drawing = false;
    shotEditor.current = null;
    if (cur.points && cur.points.length < 2) return;
    if (!cur.points && Math.hypot((cur.x2-cur.x1),(cur.y2-cur.y1)) < 3 && cur.tool !== 'mosaic') return;
    shotEditor.strokes.push(cur);
    shotEdRedraw();
  }
  canvas.addEventListener('mousedown', onDown);
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
  canvas.addEventListener('touchstart', (e) => {
    if (!e.touches || !e.touches[0]) return;
    onDown(e.touches[0]);
  }, {passive:false});
  window.addEventListener('touchmove', (e) => {
    if (!shotEditor.drawing || !e.touches || !e.touches[0]) return;
    onMove(e.touches[0]);
  }, {passive:false});
  window.addEventListener('touchend', (e) => onUp(e.changedTouches && e.changedTouches[0] || e));

  document.addEventListener('keydown', (e) => {
    if (!shotEditor.open) return;
    if (e.key === 'Escape') {
      if (shotEditor.textEl) {
        shotEditor.textEl.remove();
        shotEditor.textEl = null;
        return;
      }
      e.preventDefault();
      const draft = shotEditor.draft;
      closeScreenshotEditor();
      post({type:'screenshot_annotate_cancel', draft});
      return;
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      if (e.shiftKey) {
        if (shotEditor.redo.length) {
          shotEditor.strokes.push(shotEditor.redo.pop());
          shotEdRedraw();
        }
      } else if (shotEditor.strokes.length) {
        shotEditor.redo.push(shotEditor.strokes.pop());
        shotEdRedraw();
      }
      return;
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      if ($('shot-ed-save')) $('shot-ed-save').click();
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'c' && !shotEditor.textEl) {
      // avoid stealing OS copy when selecting text input
      if (document.activeElement && document.activeElement.tagName === 'INPUT') return;
      e.preventDefault();
      if ($('shot-ed-copy')) $('shot-ed-copy').click();
    }
  });
})();

let recBusy = false;
let recDraft = '';
let recTimer = null;
let recStartedAt = 0;
let recCountdownTimer = null;
let recLastPath = '';

function fmtRecTime(sec){
  sec = Math.max(0, Math.floor(sec || 0));
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  const h = Math.floor(m / 60);
  if (h) return h + ':' + String(m % 60).padStart(2,'0') + ':' + String(s).padStart(2,'0');
  return m + ':' + String(s).padStart(2,'0');
}
function recOpts(){
  return {
    hide_self: !!($('rec-hide') && $('rec-hide').checked),
    mic: !!($('rec-mic') && $('rec-mic').checked),
    system_audio: !!($('rec-sysaudio') && $('rec-sysaudio').checked),
    clicks: !!($('rec-clicks') && $('rec-clicks').checked),
    open_after: !!($('rec-open-after') && $('rec-open-after').checked),
    countdown: Number(($('rec-countdown-sel') && $('rec-countdown-sel').value) || 0),
    max_seconds: Number(($('rec-max') && $('rec-max').value) || 0),
  };
}
function setRecBusyUI(busy, message){
  recBusy = !!busy;
  const live = $('rec-live');
  if (live) live.classList.toggle('on', recBusy);
  if ($('rec-live-msg') && message) $('rec-live-msg').textContent = message;
  document.querySelectorAll('[data-rec-mode]').forEach(b => { b.disabled = recBusy; });
  const stopCard = $('rec-stop-card');
  if (stopCard) stopCard.disabled = !recBusy;
  if ($('rec-stop')) $('rec-stop').disabled = !recBusy;
}
function startRecTimer(startedAt){
  recStartedAt = startedAt || Date.now() / 1000;
  if (recTimer) clearInterval(recTimer);
  const tick = () => {
    const el = $('rec-timer');
    if (el) el.textContent = fmtRecTime((Date.now()/1000) - recStartedAt);
  };
  tick();
  recTimer = setInterval(tick, 250);
}
function stopRecTimer(){
  if (recTimer) clearInterval(recTimer);
  recTimer = null;
}
function hideRecCountdown(){
  if (recCountdownTimer) { clearInterval(recCountdownTimer); recCountdownTimer = null; }
  const box = $('rec-countdown');
  if (box) { box.classList.remove('on'); box.setAttribute('aria-hidden','true'); }
}
function showRecCountdown(seconds, onDone){
  hideRecCountdown();
  let n = Math.max(0, Math.floor(seconds || 0));
  if (n <= 0) { onDone(); return; }
  const box = $('rec-countdown');
  const num = $('rec-countdown-n');
  if (!box || !num) { onDone(); return; }
  box.classList.add('on');
  box.setAttribute('aria-hidden','false');
  num.textContent = String(n);
  recCountdownTimer = setInterval(() => {
    n -= 1;
    if (n <= 0) {
      hideRecCountdown();
      onDone();
      return;
    }
    num.textContent = String(n);
  }, 1000);
}
function startRecording(mode){
  if (recBusy || shotBusy) return;
  const opts = recOpts();
  saveSettings({
    recording_hide_self: opts.hide_self,
    recording_mic: opts.mic,
    recording_system_audio: opts.system_audio,
    recording_clicks: opts.clicks,
    recording_open_after: opts.open_after,
    recording_countdown: opts.countdown,
    recording_max_seconds: opts.max_seconds,
  });
  const go = () => {
    setRecBusyUI(true, mode === 'full' ? '即将全屏录制…' : '请选择录制区域…');
    if ($('rec-timer')) $('rec-timer').textContent = '0:00';
    post({
      type: 'recording_start',
      mode: mode,
      hide_self: opts.hide_self,
      mic: opts.mic,
      system_audio: opts.system_audio,
      clicks: opts.clicks,
      countdown: opts.countdown,
      max_seconds: opts.max_seconds,
    });
  };
  if (mode === 'full' && opts.countdown > 0) showRecCountdown(opts.countdown, go);
  else go();
}
function renderRecPreview(data){
  const box = $('rec-preview');
  const meta = $('rec-meta');
  if (!box) return;
  if (data && data.poster) {
    box.innerHTML = '<img alt="preview" src="'+data.poster+'" />';
  } else if (data && data.path) {
    box.innerHTML = '<div class="empty"><b>录屏已保存</b>'+esc(data.path)+'</div>';
  } else {
    box.innerHTML = '<div class="empty"><b>还没有录屏</b>选择区域或全屏开始录制</div>';
  }
  if (meta) {
    if (data && data.file) {
      const f = data.file;
      meta.innerHTML =
        '<button type="button" class="btn-mini" data-rec-act="open" data-path="'+esc(f.path)+'">播放</button>'+
        '<button type="button" class="btn-mini" data-rec-act="reveal" data-path="'+esc(f.path)+'">显示</button>'+
        '<button type="button" class="btn-mini" data-rec-act="copy" data-path="'+esc(f.path)+'">复制</button>'+
        '<span class="muted">'+esc(f.duration_text||'')+' · '+esc(f.size_text||'')+'</span>';
    } else meta.innerHTML = '';
  }
}
function renderRecList(payload){
  const list = $('rec-list');
  const folder = $('rec-folder-path');
  if (folder) folder.textContent = (payload && payload.folder) || '—';
  if (!list) return;
  const items = (payload && payload.items) || [];
  if (!items.length) {
    list.innerHTML = '<div class="muted" style="padding:12px 4px">暂无历史录屏</div>';
    return;
  }
  list.innerHTML = items.map(it => `
    <div class="shot-row">
      <div>
        <div class="name">${esc(it.name)}</div>
        <div class="sub">${esc(it.duration_text||'—')} · ${esc(it.size_text||'')} · ${esc(it.mtime_text||'')}</div>
      </div>
      <div class="acts">
        <button type="button" class="btn-mini" data-rec-act="open" data-path="${esc(it.path)}">播放</button>
        <button type="button" class="btn-mini" data-rec-act="reveal" data-path="${esc(it.path)}">显示</button>
        <button type="button" class="btn-mini" data-rec-act="copy" data-path="${esc(it.path)}">复制</button>
        <button type="button" class="btn-mini danger" data-rec-act="delete" data-path="${esc(it.path)}">删除</button>
      </div>
    </div>`).join('');
}
function openRecordingEditor(payload){
  const data = payload || {};
  const ed = $('rec-editor');
  if (!ed) return;
  recDraft = data.draft || '';
  const poster = $('rec-ed-poster');
  if (poster) {
    if (data.poster) poster.style.backgroundImage = 'url("'+data.poster+'")';
    else poster.style.backgroundImage = '';
  }
  const f = data.file || {};
  if ($('rec-ed-name')) $('rec-ed-name').textContent = f.name || 'Recording.mov';
  const bits = [];
  if (f.duration_text) bits.push(f.duration_text);
  if (f.width && f.height) bits.push(f.width + '×' + f.height);
  if (f.size_text) bits.push(f.size_text);
  if ($('rec-ed-meta')) $('rec-ed-meta').textContent = bits.join(' · ') || '—';
  if ($('rec-ed-hint')) $('rec-ed-hint').textContent = '草稿 · 保存到影片 / SupTools';
  ed.classList.add('open');
  ed.setAttribute('aria-hidden','false');
  try { window.__navigate({page:'rec'}); } catch(_){}
}
function closeRecordingEditor(){
  const ed = $('rec-editor');
  if (ed) { ed.classList.remove('open'); ed.setAttribute('aria-hidden','true'); }
  recDraft = '';
}
window.__setRecordingState = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    const busy = !!(data && data.busy);
    setRecBusyUI(busy, (data && data.message) || '');
    if (busy && data.phase === 'recording') startRecTimer(data.started_at);
    else if (busy && data.phase === 'selecting') {
      stopRecTimer();
      if ($('rec-timer')) $('rec-timer').textContent = '…';
    } else if (!busy) stopRecTimer();
  } catch (e) {}
};
window.__setRecordingList = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    renderRecList(data || {});
  } catch (e) {}
};
window.__setRecordingResult = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    if (data && data.path) recLastPath = data.path;
    renderRecPreview(data || {});
  } catch (e) {}
};
window.__setRecordingToast = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    showShotToast(!!(data && data.ok), (data && data.message) || '');
  } catch (e) {}
};
window.__openRecordingEditor = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    openRecordingEditor(data || {});
  } catch (e) {}
};
window.__closeRecordingEditor = function(){ closeRecordingEditor(); };

document.querySelectorAll('[data-rec-mode]').forEach(btn => {
  btn.onclick = () => startRecording(btn.dataset.recMode || 'selection');
});
if ($('rec-stop')) $('rec-stop').onclick = () => post({type:'recording_stop'});
if ($('rec-stop-card')) $('rec-stop-card').onclick = () => {
  if (!recBusy) return;
  post({type:'recording_stop'});
};
if ($('rec-folder')) $('rec-folder').onclick = () => post({type:'recording_folder'});
if ($('rec-refresh')) $('rec-refresh').onclick = () => post({type:'recording_list'});
['rec-hide','rec-mic','rec-sysaudio','rec-clicks','rec-open-after','rec-countdown-sel','rec-max'].forEach(id => {
  const el = $(id);
  if (!el) return;
  el.onchange = () => {
    const opts = recOpts();
    saveSettings({
      recording_hide_self: opts.hide_self,
      recording_mic: opts.mic,
      recording_system_audio: opts.system_audio,
      recording_clicks: opts.clicks,
      recording_open_after: opts.open_after,
      recording_countdown: opts.countdown,
      recording_max_seconds: opts.max_seconds,
    });
  };
});
if ($('rec-ed-cancel')) $('rec-ed-cancel').onclick = () => {
  const draft = recDraft;
  closeRecordingEditor();
  post({type:'recording_cancel', draft});
};
if ($('rec-ed-save')) $('rec-ed-save').onclick = () => {
  post({
    type:'recording_save',
    draft: recDraft,
    open_after: !!($('rec-open-after') && $('rec-open-after').checked),
  });
};
if ($('rec-ed-reveal')) $('rec-ed-reveal').onclick = () => {
  if (recDraft) post({type:'recording_reveal', path: recDraft});
};
if ($('rec-ed-play')) $('rec-ed-play').onclick = () => {
  if (recDraft) post({type:'recording_open', path: recDraft});
};
document.addEventListener('keydown', (e) => {
  const ed = $('rec-editor');
  if (!ed || !ed.classList.contains('open')) return;
  if (e.key === 'Escape') {
    e.preventDefault();
    const draft = recDraft;
    closeRecordingEditor();
    post({type:'recording_cancel', draft});
  }
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
    e.preventDefault();
    if ($('rec-ed-save')) $('rec-ed-save').click();
  }
});

if ($('conn-start')) $('conn-start').onclick = () => {
  if (connBusy) return;
  post({type:'connectivity_run'});
};
if ($('conn-cancel')) $('conn-cancel').onclick = () => {
  post({type:'connectivity_cancel'});
};
['shot-hide','shot-clip','shot-cursor','shot-delay'].forEach(id => {
  const el = $(id);
  if (!el) return;
  el.onchange = () => {
    const opts = shotOpts();
    saveSettings({
      screenshot_hide_self: opts.hide_self,
      screenshot_clipboard: opts.clipboard,
      screenshot_cursor: opts.cursor,
      screenshot_delay: opts.delay,
    });
  };
});
if ($('shot-folder')) $('shot-folder').onclick = () => post({type:'screenshot_folder'});
if ($('shot-refresh')) $('shot-refresh').onclick = () => post({type:'screenshot_list'});
document.addEventListener('click', (e) => {
  const clearBtn = e.target.closest('[data-hk-clear]');
  if (clearBtn) {
    e.preventDefault();
    e.stopPropagation();
    post({type:'hotkey_clear', id: clearBtn.dataset.hkClear});
    return;
  }
  const hkBtn = e.target.closest('[data-hk]');
  if (hkBtn) {
    e.preventDefault();
    e.stopPropagation();
    const id = hkBtn.dataset.hk;
    document.querySelectorAll('.hk-btn').forEach(b => {
      b.classList.remove('recording');
      const key = b.dataset.hk;
      if (key) b.textContent = appSettings[key + '_label'] || formatHotkeyLabel(appSettings[key] || '');
    });
    hkBtn.classList.add('recording');
    hkBtn.textContent = '按下快捷键…';
    post({type:'hotkey_record', id});
    return;
  }
  const btn = e.target.closest('[data-shot-act]');
  if (btn) {
    const act = btn.dataset.shotAct;
    const path = btn.dataset.path || '';
    if (act === 'open') post({type:'screenshot_open', path});
    else if (act === 'reveal') post({type:'screenshot_reveal', path});
    else if (act === 'copy') post({type:'screenshot_copy', path});
    else if (act === 'delete') {
      if (!confirm('删除这张截图？')) return;
      post({type:'screenshot_delete', path});
      if (path && path === shotLastPath) renderShotPreview(null);
    }
    return;
  }
  const rbtn = e.target.closest('[data-rec-act]');
  if (!rbtn) return;
  const ract = rbtn.dataset.recAct;
  const rpath = rbtn.dataset.path || '';
  if (ract === 'open') post({type:'recording_open', path: rpath});
  else if (ract === 'reveal') post({type:'recording_reveal', path: rpath});
  else if (ract === 'copy') post({type:'recording_copy', path: rpath});
  else if (ract === 'delete') {
    if (!confirm('删除这段录屏？')) return;
    post({type:'recording_delete', path: rpath});
    if (rpath && rpath === recLastPath) renderRecPreview(null);
  }
});

let permGuideKind = 'screen';
let permStatus = { items: [] };
let permPrevGranted = {};
let permToastTimer = null;

function showPermToast(ok, title, msg) {
  const el = $('perm-toast');
  if (!el) return;
  el.classList.add('show');
  el.classList.toggle('warn', !ok);
  if ($('perm-toast-t')) $('perm-toast-t').textContent = title || (ok ? '已开启' : '提示');
  if ($('perm-toast-s')) $('perm-toast-s').textContent = msg || '';
  if (permToastTimer) clearTimeout(permToastTimer);
  permToastTimer = setTimeout(function(){ el.classList.remove('show'); }, 3600);
}

function renderPermissions(payload, opts) {
  opts = opts || {};
  const data = payload || {};
  const items = Array.isArray(data.items) ? data.items : [];
  permStatus = data;
  if ($('perm-summary-count')) $('perm-summary-count').textContent = data.summary || (items.length ? (data.granted_count + '/' + items.length) : '—');
  if ($('perm-required-ok')) $('perm-required-ok').textContent = String(data.required_granted != null ? data.required_granted : 0);
  if ($('perm-required-total')) $('perm-required-total').textContent = String(data.required_count != null ? data.required_count : 0);
  if ($('perm-granted')) $('perm-granted').textContent = String(data.granted_count != null ? data.granted_count : 0);
  if ($('perm-total')) $('perm-total').textContent = String(data.item_count != null ? data.item_count : items.length);
  const allOk = $('perm-all-ok');
  if (allOk) allOk.classList.toggle('show', !!data.all_required_ok);

  // Announce newly granted permissions
  const newly = [];
  items.forEach(it => {
    const id = String(it.id || '');
    const now = it.granted === true;
    const prev = permPrevGranted[id];
    if (opts.announce && prev === false && now) newly.push(it);
    if (it.granted === true || it.granted === false) permPrevGranted[id] = now;
    else if (permPrevGranted[id] == null) permPrevGranted[id] = now;
  });
  if (newly.length === 1) {
    showPermToast(true, '已开启「' + (newly[0].title || '') + '」', newly[0].used_by || '权限已生效');
  } else if (newly.length > 1) {
    showPermToast(true, '已开启 ' + newly.length + ' 项权限', newly.map(i => i.title).join('、'));
  }

  const root = $('perm-list');
  if (!root) return;
  if (!items.length) {
    root.innerHTML = '<div class="su-empty"><div class="big">暂无权限项</div>点击「重新检测」刷新。</div>';
    return;
  }
  root.innerHTML = items.map(it => {
    const ok = it.granted === true;
    const unknown = it.granted == null;
    const badgeClass = ok ? 'ok' : (unknown ? '' : 'bad');
    const badgeText = ok ? '已开启' : (unknown ? (it.status_text || '前往确认') : '未开启');
    const req = it.required ? '<span class="badge">推荐</span>' : '<span class="badge">可选</span>';
    const reqBtn = it.can_request && !ok
      ? `<button class="btn-mini" type="button" data-perm-request="${esc(it.id)}">请求授权</button>`
      : '';
    const openBtn = `<button class="btn-ghost" type="button" data-perm-open="${esc(it.open_kind || it.id)}" style="padding:8px 12px;border-radius:10px;font-size:12px">${ok ? '查看设置' : '去开启'}</button>`;
    return `<div class="perm-row" data-id="${esc(it.id)}">
      <div>
        <div class="name">${esc(it.title || '')} ${req}
          <span class="perm-badge ${badgeClass}"><span class="dot"></span>${esc(badgeText)}</span>
        </div>
        <div class="sub">${esc(it.desc || '')}</div>
        <div class="tools">用于：${esc(it.used_by || '')}</div>
      </div>
      <div class="right">${reqBtn}${openBtn}</div>
    </div>`;
  }).join('');
}

window.__setPermissionsStatus = function(payload) {
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    renderPermissions(data || {}, { announce: true });
  } catch (e) {}
};

if ($('perm-refresh')) $('perm-refresh').onclick = () => {
  if ($('perm-refresh')) {
    $('perm-refresh').disabled = true;
    $('perm-refresh').textContent = '检测中…';
    setTimeout(function(){
      if ($('perm-refresh')) {
        $('perm-refresh').disabled = false;
        $('perm-refresh').textContent = '重新检测';
      }
    }, 1200);
  }
  post({type:'permissions_status'});
};
if ($('perm-list')) $('perm-list').addEventListener('click', (e) => {
  const openBtn = e.target.closest('[data-perm-open]');
  if (openBtn) {
    const kind = openBtn.getAttribute('data-perm-open') || 'screen';
    post({type:'open_privacy_settings', kind});
    // Re-check shortly after user returns
    setTimeout(function(){ post({type:'permissions_status'}); }, 2500);
    return;
  }
  const reqBtn = e.target.closest('[data-perm-request]');
  if (reqBtn) {
    const kind = reqBtn.getAttribute('data-perm-request') || 'screen';
    post({type:'permission_request', kind});
  }
});
document.addEventListener('click', (e) => {
  const jump = e.target.closest('[data-page-jump]');
  if (!jump) return;
  const target = jump.getAttribute('data-page-jump');
  const navBtn = document.querySelector('.nav button[data-page="'+target+'"]');
  if (navBtn) navBtn.click();
});

function showPermissionGuide(payload){
  const data = payload || {};
  permGuideKind = data.kind || 'screen';
  const title = $('perm-modal-title');
  const sub = $('perm-modal-sub');
  const steps = $('perm-modal-steps');
  const openBtn = $('perm-modal-open');
  if (title) title.textContent = data.title || '需要权限';
  if (sub) sub.textContent = data.subtitle || '请在系统设置中允许 SupTools。';
  if (steps) {
    const list = Array.isArray(data.steps) ? data.steps : [];
    steps.innerHTML = list.map(s => '<li>'+esc(s)+'</li>').join('');
  }
  if (openBtn) openBtn.textContent = data.button || '打开系统设置';
  const modal = $('perm-modal');
  if (modal) modal.classList.add('show');
}
function hidePermissionGuide(){
  const modal = $('perm-modal');
  if (modal) modal.classList.remove('show');
}
window.__showPermissionGuide = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    showPermissionGuide(data || {});
  } catch (e) {}
};
window.__setPermissionGuideResult = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    if (data && data.message) {
      if (document.body.getAttribute('data-page') === 'perms') showPermToast(!!data.ok, data.ok ? '已打开系统设置' : '无法打开设置', data.message);
      else showShotToast(!!data.ok, data.message);
    }
    if (data && data.status) renderPermissions(data.status, { announce: true });
  } catch (e) {}
};
if ($('perm-modal-close')) $('perm-modal-close').onclick = () => hidePermissionGuide();
if ($('perm-modal-open')) $('perm-modal-open').onclick = () => {
  post({type:'open_privacy_settings', kind: permGuideKind || 'screen'});
};
if ($('perm-modal')) $('perm-modal').addEventListener('click', (e) => {
  if (e.target === $('perm-modal')) hidePermissionGuide();
});
document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-perm]');
  if (!btn) return;
  e.preventDefault();
  const kind = btn.dataset.perm || 'screen';
  post({type:'permission_guide', kind});
});

window.__setHotkeyRecord = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    if (!data) return;
    if (data.id && data.spec != null) {
      appSettings[data.id] = data.spec || '';
      appSettings[data.id + '_label'] = data.label || formatHotkeyLabel(data.spec || '');
    }
    if (!data.recording) {
      document.querySelectorAll('.hk-btn').forEach(b => b.classList.remove('recording'));
      syncHotkeyUI();
    } else if (data.id) {
      document.querySelectorAll('.hk-btn[data-hk="'+data.id+'"]').forEach(b => {
        b.classList.add('recording');
        b.textContent = '按下快捷键…';
      });
    }
  } catch (e) {}
};

window.__setScreenshotList = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    renderShotList(data || {});
  } catch (e) {}
};
window.__setScreenshotProgress = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    setShotBusy(!!(data && data.busy), (data && data.message) || '');
  } catch (e) {}
};
window.__setScreenshotResult = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    setShotBusy(false, '');
    if (data && data.ok) {
      shotLastPath = data.path || '';
      renderShotPreview(data);
    } else if (data && data.error) {
      showShotToast(false, data.error);
    }
  } catch (e) {}
};
window.__setScreenshotToast = function(payload){
  try {
    const data = typeof payload === 'string' ? JSON.parse(payload) : payload;
    showShotToast(!!(data && data.ok), (data && data.message) || '');
  } catch (e) {}
};

(function boot(){
  const pending = window.__pending || [];
  window.__pending = [];
  pending.forEach(function(item){
    const fn = window[item[0]];
    if (typeof fn === 'function') fn(item[1]);
  });
  post({type:'ui_ready'});
  $('status').textContent = '已连接，等待首包数据…';
})();
</script>
</body>
</html>
""".replace("__BRAND_LOGO_SRC__", _BRAND_LOGO_SRC)
