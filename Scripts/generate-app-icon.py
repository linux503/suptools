#!/usr/bin/env python3
"""Generate a macOS-style SupTools Dock icon (squircle + soft depth).

Concept: solid tool case with a golden status strip — “超级工具箱”.
Palette: ink slate → deep emerald (distinct from the old indigo/cyan pulse mark).
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
DOCS_ICON = ROOT / "docs" / "assets" / "icon.png"
DOCS_ICON_256 = ROOT / "docs" / "assets" / "icon-256.png"
SIZE = 1024


def squircle_mask(size: int, n: float = 4.85, margin: float = 0.0) -> Image.Image:
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
    """Ink slate → deep emerald, with a soft top-left sheen."""
    c0 = (8, 18, 28)
    c1 = (12, 72, 78)
    c2 = (34, 168, 142)
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = 0.32 * (x / (size - 1)) + 0.68 * (y / (size - 1))
            t = max(0.0, min(1.0, t))
            if t < 0.48:
                c = lerp(c0, c1, t / 0.48)
            else:
                c = lerp(c1, c2, (t - 0.48) / 0.52)
            sheen = max(0.0, 1.0 - math.hypot(x / size - 0.28, y / size - 0.20) / 0.72)
            sheen = (sheen ** 1.9) * 28
            glow = max(0.0, 1.0 - math.hypot(x / size - 0.78, y / size - 0.82) / 0.48)
            glow = (glow ** 2.1) * 30
            px[x, y] = (
                min(255, int(c[0] + sheen * 0.55 + glow * 0.35)),
                min(255, int(c[1] + sheen * 0.75 + glow * 0.85)),
                min(255, int(c[2] + sheen * 0.55 + glow * 0.55)),
            )
    return img


def draw_mark(draw: ImageDraw.ImageDraw, size: int) -> None:
    """Filled tool case + lid + gold status strip (reads clearly at Dock size)."""
    white = (248, 252, 250, 255)
    soft = (232, 244, 240, 255)
    gold = (255, 196, 92, 255)
    gold_soft = (255, 214, 140, 255)

    cx = size * 0.50
    body_w = size * 0.46
    body_h = size * 0.34
    left = cx - body_w / 2
    top = size * 0.40
    right = left + body_w
    bottom = top + body_h
    radius = size * 0.072

    # Soft ground shadow under the case
    shadow = [
        left + size * 0.02,
        bottom - size * 0.01,
        right - size * 0.02,
        bottom + size * 0.06,
    ]
    draw.ellipse(shadow, fill=(0, 20, 30, 55))

    # Case body (solid)
    draw.rounded_rectangle([left, top, right, bottom], radius=radius, fill=white)

    # Inner well (slightly inset, softer fill)
    inset = size * 0.028
    draw.rounded_rectangle(
        [left + inset, top + body_h * 0.34, right - inset, bottom - inset],
        radius=radius * 0.7,
        fill=soft,
    )

    # Lid (angled open panel)
    lid_h = size * 0.11
    lid = [
        (left + body_w * 0.08, top + size * 0.01),
        (cx, top - lid_h),
        (right - body_w * 0.08, top + size * 0.01),
        (right - body_w * 0.12, top + body_h * 0.22),
        (left + body_w * 0.12, top + body_h * 0.22),
    ]
    draw.polygon(lid, fill=white)

    # Handle notch on lid
    hx, hy = cx, top - lid_h * 0.42
    hw, hh = size * 0.055, size * 0.018
    draw.rounded_rectangle([hx - hw, hy - hh, hx + hw, hy + hh], radius=hh, fill=soft)

    # Golden status strip (monitoring accent)
    strip_y0 = top + body_h * 0.52
    strip_y1 = strip_y0 + size * 0.048
    strip_x0 = left + body_w * 0.18
    strip_x1 = left + body_w * 0.72
    draw.rounded_rectangle(
        [strip_x0, strip_y0, strip_x1, strip_y1],
        radius=size * 0.024,
        fill=gold,
    )
    # Short secondary meter
    draw.rounded_rectangle(
        [strip_x1 + size * 0.03, strip_y0, right - body_w * 0.18, strip_y1],
        radius=size * 0.024,
        fill=gold_soft,
    )

    # Three tool slots / rivets
    slot_y = top + body_h * 0.72
    for i, t in enumerate((0.22, 0.50, 0.78)):
        sx = left + body_w * t
        r = size * 0.018
        draw.ellipse([sx - r, slot_y - r, sx + r, slot_y + r], fill=(180, 210, 200, 255))


def add_inner_shadow(base: Image.Image, mask: Image.Image) -> Image.Image:
    size = base.size[0]
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    for i in range(170):
        a = int(70 * (i / 170) ** 1.15)
        y = size - 170 + i
        d.rectangle([0, y, size, y + 1], fill=(2, 16, 22, a))

    for i in range(140):
        a = int(48 * (1 - i / 140) ** 1.35)
        d.rectangle([0, i, size, i + 1], fill=(255, 255, 255, a))

    specular = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(specular)
    sd.ellipse(
        [size * 0.08, size * 0.00, size * 0.90, size * 0.42],
        fill=(255, 255, 255, 36),
    )
    specular = specular.filter(ImageFilter.GaussianBlur(radius=30))
    overlay = Image.alpha_composite(overlay, specular)

    rim = Image.new("L", base.size, 0)
    eroded = mask.filter(ImageFilter.MinFilter(7))
    rim_px = rim.load()
    m = mask.load()
    e = eroded.load()
    for y in range(size):
        for x in range(size):
            if m[x, y] > 200 and e[x, y] < 160 and y < size * 0.55:
                rim_px[x, y] = 100
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
    draw = ImageDraw.Draw(glyph_layer, "RGBA")
    draw_mark(draw, size)

    g_alpha = glyph_layer.split()[-1]
    shadow_colored = Image.new("RGBA", (size, size), (0, 24, 30, 0))
    shadow_colored.putalpha(g_alpha.point(lambda a: int(a * 0.28)))
    shadow_colored = shadow_colored.filter(ImageFilter.GaussianBlur(radius=18))
    shadow_canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_canvas.paste(shadow_colored, (0, int(size * 0.018)), shadow_colored)

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
    (ROOT / "docs" / "assets").mkdir(parents=True, exist_ok=True)

    icon.save(OUT, "PNG")
    icon.save(ASSETS, "PNG")
    icon.save(OUT_LEGACY, "PNG")
    icon.save(ASSETS_LEGACY, "PNG")
    icon.save(OUT_SYSPULSE, "PNG")

    preview = icon.resize((256, 256), Image.Resampling.LANCZOS)
    preview.save(ROOT / "assets" / "SupToolsIcon-preview-256.png", "PNG")
    preview.save(DOCS_ICON_256, "PNG")

    web = icon.resize((512, 512), Image.Resampling.LANCZOS)
    web.save(DOCS_ICON, "PNG")

    print(f"✓ Wrote {OUT}")
    print(f"✓ Wrote {ASSETS}")
    print(f"✓ Wrote {DOCS_ICON_256}")


if __name__ == "__main__":
    main()
