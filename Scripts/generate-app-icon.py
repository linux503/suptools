#!/usr/bin/env python3
"""Generate a macOS-style SupTools Dock icon (squircle + soft depth).

Concept: precision open-end wrench on a soft plate — “超级工具箱”.
Palette: ink slate → deep emerald, with a restrained gold status accent.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageChops


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
    """Deep ink → emerald, formal product-utility look."""
    c0 = (6, 14, 22)
    c1 = (8, 58, 62)
    c2 = (18, 148, 128)
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = 0.28 * (x / (size - 1)) + 0.72 * (y / (size - 1))
            t = max(0.0, min(1.0, t))
            if t < 0.42:
                c = lerp(c0, c1, t / 0.42)
            else:
                c = lerp(c1, c2, (t - 0.42) / 0.58)
            sheen = max(0.0, 1.0 - math.hypot(x / size - 0.30, y / size - 0.18) / 0.70)
            sheen = (sheen ** 2.0) * 34
            glow = max(0.0, 1.0 - math.hypot(x / size - 0.76, y / size - 0.84) / 0.46)
            glow = (glow ** 2.2) * 36
            px[x, y] = (
                min(255, int(c[0] + sheen * 0.50 + glow * 0.30)),
                min(255, int(c[1] + sheen * 0.70 + glow * 0.90)),
                min(255, int(c[2] + sheen * 0.55 + glow * 0.55)),
            )
    return img


def draw_wrench_upright(size: int) -> Image.Image:
    """Draw a clean open-end wrench pointing up (mask-based), then caller rotates it."""
    mask = Image.new("L", (size, size), 0)
    m = ImageDraw.Draw(mask)

    cx = size * 0.50
    head_cy = size * 0.355
    head_outer = size * 0.138
    head_inner = size * 0.072
    jaw_w = size * 0.062

    # Head ring
    m.ellipse(
        [cx - head_outer, head_cy - head_outer, cx + head_outer, head_cy + head_outer],
        fill=255,
    )
    m.ellipse(
        [cx - head_inner, head_cy - head_inner, cx + head_inner, head_cy + head_inner],
        fill=0,
    )
    # Open-end cut (top sector + center slot)
    m.pieslice(
        [cx - head_outer - 4, head_cy - head_outer - 4, cx + head_outer + 4, head_cy + head_outer + 4],
        start=245,
        end=295,
        fill=0,
    )
    m.rectangle(
        [cx - jaw_w / 2, head_cy - head_outer - 6, cx + jaw_w / 2, head_cy - head_inner * 0.35],
        fill=0,
    )

    # Neck + handle body
    neck_w = size * 0.082
    neck_top = head_cy + head_outer * 0.42
    handle_bot = size * 0.735
    m.rounded_rectangle(
        [cx - neck_w / 2, neck_top, cx + neck_w / 2, handle_bot],
        radius=neck_w * 0.42,
        fill=255,
    )
    # Slightly wider lower grip
    hw = size * 0.098
    m.rounded_rectangle(
        [cx - hw / 2, size * 0.58, cx + hw / 2, handle_bot + size * 0.018],
        radius=hw * 0.42,
        fill=255,
    )

    # Colorize silhouette
    ink = Image.new("RGBA", (size, size), (8, 38, 44, 255))
    ink.putalpha(mask)

    # Gold status chip on handle
    accent = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    a = ImageDraw.Draw(accent, "RGBA")
    gold = (232, 178, 72, 255)
    gold_hi = (255, 214, 128, 255)
    sy0 = size * 0.585
    sy1 = sy0 + size * 0.040
    a.rounded_rectangle(
        [cx - size * 0.030, sy0, cx + size * 0.030, sy1],
        radius=size * 0.012,
        fill=gold,
    )
    a.rounded_rectangle(
        [cx - size * 0.018, sy0 + size * 0.009, cx + size * 0.018, sy1 - size * 0.009],
        radius=size * 0.006,
        fill=gold_hi,
    )
    # Only keep gold where wrench body exists
    ra, ga, ba, aa = accent.split()
    aa = ImageChops.multiply(aa, mask)
    accent = Image.merge("RGBA", (ra, ga, ba, aa))

    return Image.alpha_composite(ink, accent)


def draw_mark(size: int) -> Image.Image:
    """White plate + rotated wrench."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")

    white = (248, 252, 250, 255)
    plate = (234, 245, 241, 255)

    cx = size * 0.50
    cy = size * 0.505

    # Soft ground shadow
    d.ellipse(
        [cx - size * 0.30, cy + size * 0.18, cx + size * 0.30, cy + size * 0.30],
        fill=(0, 18, 26, 58),
    )

    # Elevated plate
    r = size * 0.272
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=white)
    rin = r * 0.78
    d.ellipse([cx - rin, cy - rin, cx + rin, cy + rin], fill=plate)

    wrench = draw_wrench_upright(size)
    wrench = wrench.rotate(38, resample=Image.Resampling.BICUBIC, center=(cx, cy))
    layer = Image.alpha_composite(layer, wrench)
    return layer


def add_inner_shadow(base: Image.Image, mask: Image.Image) -> Image.Image:
    size = base.size[0]
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    for i in range(170):
        a = int(72 * (i / 170) ** 1.15)
        y = size - 170 + i
        d.rectangle([0, y, size, y + 1], fill=(2, 14, 20, a))

    for i in range(140):
        a = int(52 * (1 - i / 140) ** 1.35)
        d.rectangle([0, i, size, i + 1], fill=(255, 255, 255, a))

    specular = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(specular)
    sd.ellipse(
        [size * 0.08, size * 0.00, size * 0.90, size * 0.42],
        fill=(255, 255, 255, 38),
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
                rim_px[x, y] = 105
    rim = rim.filter(ImageFilter.GaussianBlur(4))
    white = Image.new("RGBA", base.size, (255, 255, 255, 0))
    white.putalpha(rim)
    overlay = Image.alpha_composite(overlay, white)

    return Image.alpha_composite(base.convert("RGBA"), overlay)


def build() -> Image.Image:
    size = SIZE
    mask = squircle_mask(size, n=4.8, margin=size * 0.068)

    fill = paint_gradient(size).convert("RGBA")
    glyph_layer = draw_mark(size)

    g_alpha = glyph_layer.split()[-1]
    shadow_colored = Image.new("RGBA", (size, size), (0, 22, 28, 0))
    shadow_colored.putalpha(g_alpha.point(lambda a: int(a * 0.26)))
    shadow_colored = shadow_colored.filter(ImageFilter.GaussianBlur(radius=16))
    shadow_canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_canvas.paste(shadow_colored, (0, int(size * 0.016)), shadow_colored)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(fill, (0, 0))
    canvas = Image.alpha_composite(canvas, shadow_canvas)
    canvas = Image.alpha_composite(canvas, glyph_layer)
    canvas = add_inner_shadow(canvas, mask)

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
