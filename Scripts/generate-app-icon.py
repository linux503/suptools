#!/usr/bin/env python3
"""Generate a macOS-style SupTools Dock icon (squircle + soft depth).

Concept: open toolbox + live pulse — “超级工具箱” that also monitors the Mac.
Palette: deep indigo → electric cyan.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Resources" / "SupToolsIcon.png"
OUT_LEGACY = ROOT / "Resources" / "SystemMonitIcon.png"
OUT_SYSPULSE = ROOT / "Resources" / "SysPulseIcon.png"
ASSETS = ROOT / "assets" / "SupToolsIcon.png"
ASSETS_LEGACY = ROOT / "assets" / "SystemMonitIcon.png"
SIZE = 1024


def squircle_mask(size: int, n: float = 5.0, margin: float = 0.0) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    px = mask.load()
    c = (size - 1) / 2.0
    radius = c - margin
    for y in range(size):
        for x in range(size):
            nx = (x - c) / radius
            ny = (y - c) / radius
            if abs(nx) ** n + abs(ny) ** n <= 1.0:
                px[x, y] = 255
    return mask.filter(ImageFilter.GaussianBlur(radius=1.2))


def lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def paint_gradient(size: int) -> Image.Image:
    """Deep indigo → electric cyan diagonal with restrained sheen."""
    c0 = (12, 18, 58)
    c1 = (10, 92, 158)
    c2 = (16, 188, 178)
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (0.38 * (x / (size - 1)) + 0.62 * (y / (size - 1)))
            t = max(0.0, min(1.0, t))
            if t < 0.42:
                c = lerp(c0, c1, t / 0.42)
            else:
                c = lerp(c1, c2, (t - 0.42) / 0.58)
            sheen = max(0.0, 1.0 - math.hypot(x / size - 0.30, y / size - 0.18) / 0.78)
            sheen = (sheen ** 1.85) * 26
            warm = max(0.0, 1.0 - math.hypot(x / size - 0.80, y / size - 0.78) / 0.50)
            warm = (warm ** 2.2) * 22
            px[x, y] = (
                min(255, int(c[0] + sheen * 0.45 + warm * 1.0)),
                min(255, int(c[1] + sheen * 0.85 + warm * 0.30)),
                min(255, int(c[2] + sheen * 0.75)),
            )
    return img


def _thick_polyline(
    draw: ImageDraw.ImageDraw,
    pts: list[tuple[float, float]],
    fill: tuple,
    width: int,
) -> None:
    draw.line(pts, fill=fill, width=width, joint="curve")
    r = max(1, width // 2)
    for x, y in pts:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def draw_mark(draw: ImageDraw.ImageDraw, size: int) -> None:
    """White open toolbox + pulse waveform (tools + monitoring)."""
    white = (255, 255, 255, 255)
    soft = (255, 255, 255, 230)

    cx, cy = size * 0.50, size * 0.54
    stroke = max(40, int(size * 0.062))
    thin = max(28, int(size * 0.044))

    bw, bh = size * 0.48, size * 0.36
    left, top = cx - bw / 2, cy - bh * 0.22
    right, bottom = left + bw, top + bh
    radius = size * 0.06
    draw.rounded_rectangle(
        [left, top, right, bottom],
        radius=radius,
        outline=white,
        width=stroke,
    )

    lid_y = top + bh * 0.30
    inset = stroke * 0.55
    draw.line([(left + inset, lid_y), (right - inset, lid_y)], fill=soft, width=max(16, thin // 2))

    hx, hy = cx, top + bh * 0.15
    hw, hh = size * 0.07, size * 0.028
    draw.rounded_rectangle(
        [hx - hw, hy - hh, hx + hw, hy + hh],
        radius=hh,
        fill=white,
    )

    lid_pts = [
        (left + bw * 0.10, top + stroke * 0.05),
        (cx, top - size * 0.088),
        (right - bw * 0.10, top + stroke * 0.05),
    ]
    _thick_polyline(draw, lid_pts, soft, max(24, int(thin * 0.85)))

    py = top + bh * 0.64
    x0 = left + bw * 0.16
    x1 = right - bw * 0.16
    amp = bh * 0.24
    pulse = [
        (x0, py),
        (x0 + (x1 - x0) * 0.20, py),
        (x0 + (x1 - x0) * 0.30, py - amp * 0.12),
        (x0 + (x1 - x0) * 0.38, py + amp * 0.92),
        (x0 + (x1 - x0) * 0.48, py - amp * 1.08),
        (x0 + (x1 - x0) * 0.58, py + amp * 0.22),
        (x0 + (x1 - x0) * 0.70, py),
        (x1, py),
    ]
    _thick_polyline(draw, pulse, white, thin)

    peak = pulse[4]
    br = size * 0.024
    draw.ellipse([peak[0] - br, peak[1] - br, peak[0] + br, peak[1] + br], fill=white)


def add_inner_shadow(base: Image.Image, mask: Image.Image) -> Image.Image:
    size = base.size[0]
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    for i in range(160):
        a = int(64 * (i / 160) ** 1.2)
        y = size - 160 + i
        d.rectangle([0, y, size, y + 1], fill=(4, 12, 40, a))

    for i in range(130):
        a = int(56 * (1 - i / 130) ** 1.4)
        d.rectangle([0, i, size, i + 1], fill=(255, 255, 255, a))

    specular = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(specular)
    sd.ellipse(
        [size * 0.10, size * 0.02, size * 0.88, size * 0.40],
        fill=(255, 255, 255, 34),
    )
    specular = specular.filter(ImageFilter.GaussianBlur(radius=28))
    overlay = Image.alpha_composite(overlay, specular)

    rim = Image.new("L", base.size, 0)
    eroded = mask.filter(ImageFilter.MinFilter(7))
    rim_px = rim.load()
    m = mask.load()
    e = eroded.load()
    for y in range(size):
        for x in range(size):
            if m[x, y] > 200 and e[x, y] < 160 and y < size * 0.55:
                rim_px[x, y] = 110
    rim = rim.filter(ImageFilter.GaussianBlur(4))
    white = Image.new("RGBA", base.size, (255, 255, 255, 0))
    white.putalpha(rim)
    overlay = Image.alpha_composite(overlay, white)

    return Image.alpha_composite(base.convert("RGBA"), overlay)


def build() -> Image.Image:
    size = SIZE
    mask = squircle_mask(size, n=4.8, margin=size * 0.068)

    fill = paint_gradient(size).convert("RGBA")
    glyph_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glyph_layer)
    draw_mark(draw, size)

    g_alpha = glyph_layer.split()[-1]
    shadow_colored = Image.new("RGBA", (size, size), (0, 20, 50, 0))
    shadow_colored.putalpha(g_alpha.point(lambda a: int(a * 0.32)))
    shadow_colored = shadow_colored.filter(ImageFilter.GaussianBlur(radius=16))
    shadow_canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_canvas.paste(shadow_colored, (0, int(size * 0.016)), shadow_colored)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(fill, (0, 0))
    canvas = Image.alpha_composite(canvas, shadow_canvas)
    canvas = Image.alpha_composite(canvas, glyph_layer)
    canvas = add_inner_shadow(canvas, mask)

    from PIL import ImageChops

    r, g, b, a = canvas.split()
    a = ImageChops.multiply(a, mask)
    return Image.merge("RGBA", (r, g, b, a))


def main() -> None:
    icon = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)
    icon.save(OUT, "PNG")
    icon.save(ASSETS, "PNG")
    icon.save(OUT_LEGACY, "PNG")
    icon.save(ASSETS_LEGACY, "PNG")
    icon.save(OUT_SYSPULSE, "PNG")
    preview = icon.resize((256, 256), Image.Resampling.LANCZOS)
    preview.save(ROOT / "assets" / "SupToolsIcon-preview-256.png", "PNG")
    print(f"✓ Wrote {OUT}")
    print(f"✓ Wrote {ASSETS}")


if __name__ == "__main__":
    main()
