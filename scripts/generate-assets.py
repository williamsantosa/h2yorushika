#!/usr/bin/env python3
"""Generate Rockbox BMP assets for h2yorushika (24-bit, PIL — matches official theme packs)."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".rockbox" / "wps" / "h2yorushika"
LOGO_SRC = ROOT / "assets" / "yorushika-logo.png"

# Elma's Diary palette: deep oxblood leather, warm brown edge, dusty-mauve
# sheen, crimson cracks bleeding through, gold embossed accents.
BG = (0x22, 0x10, 0x13)        # deep oxblood (top-right, darkest)
BG_LIGHT = (0x47, 0x28, 0x22)  # warm leather brown (lower-left)
MAUVE = (0x86, 0x60, 0x68)     # worn, moonlit sheen on the leather
CRIMSON = (0x9E, 0x2A, 0x1C)   # red cracks showing through near the seam
AMBER = (0x8B, 0x6F, 0x47)
AMBER_LIGHT = (0xA8, 0x90, 0x70)
BRIGHT = (0xC8, 0x9B, 0x5A)
TRACK = (0x32, 0x1A, 0x1E)
TRACK_EDGE = (0x4E, 0x2C, 0x2C)
DIM_AMBER = (0x4A, 0x3E, 0x30)


def clamp(v: int) -> int:
    return max(0, min(255, v))


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def lerp_rgb(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def _hash01(ix: int, iy: int, seed: int = 0) -> float:
    n = (ix * 374761393 + iy * 668265263 + seed * 1274126177) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n = (n ^ (n >> 16)) & 0xFFFFFFFF
    return n / 0xFFFFFFFF


def _smoothstep(t: float) -> float:
    t = clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def _value_noise(x: float, y: float, scale: float, seed: int = 0) -> float:
    gx, gy = x / scale, y / scale
    ix, iy = math.floor(gx), math.floor(gy)
    fx, fy = gx - ix, gy - iy
    ux, uy = _smoothstep(fx), _smoothstep(fy)
    v00 = _hash01(ix, iy, seed)
    v10 = _hash01(ix + 1, iy, seed)
    v01 = _hash01(ix, iy + 1, seed)
    v11 = _hash01(ix + 1, iy + 1, seed)
    a = v00 + (v10 - v00) * ux
    b = v01 + (v11 - v01) * ux
    return a + (b - a) * uy


def _fbm(x: float, y: float, seed: int = 0) -> float:
    """Layered value noise for the weathered leather grain."""
    return (
        _value_noise(x, y, 64, seed) * 0.55
        + _value_noise(x, y, 26, seed + 7) * 0.30
        + _value_noise(x, y, 10, seed + 19) * 0.15
    )


def backdrop_color(x: int, y: int, width: int = 320, height: int = 240, grain: bool = True) -> tuple[int, int, int]:
    # Diagonal base: deep oxblood top-right -> warm leather brown lower-left.
    diag = ((width - 1 - x) / max(width - 1, 1) + y / max(height - 1, 1)) * 0.5
    col = lerp_rgb(BG, BG_LIGHT, _smoothstep(diag) * 0.85)

    # Dusty-mauve sheen: worn, moonlit patch biased to the center-right band.
    n = _fbm(x, y)
    sheen = _smoothstep((n - 0.48) * 2.4)
    band_x = math.exp(-((x - width * 0.62) ** 2) / (2 * (width * 0.30) ** 2))
    band_y = math.exp(-((y - height * 0.42) ** 2) / (2 * (height * 0.45) ** 2))
    col = lerp_rgb(col, MAUVE, sheen * band_x * band_y * 0.42)

    # Crimson cracks: sparse, bright, clustered toward the lower seam.
    crack = _value_noise(x, y, 5, 101)
    if grain and crack > 0.9 and y > height * 0.4:
        depth = (y - height * 0.4) / (height * 0.6)
        col = lerp_rgb(col, CRIMSON, ((crack - 0.9) / 0.1) * 0.55 * depth)

    # Vignette: pull the corners into shadow.
    cx, cy = width * 0.5, height * 0.42
    max_dist = (width**2 + height**2) ** 0.5
    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    vignette = min(dist / (max_dist * 0.62), 1.0) * 0.24

    # Fine leather grain: non-directional speckle from the hash.
    g = int((_hash01(x, y, 53) - 0.5) * 7) if grain else 0
    return (
        clamp(int(col[0] * (1.0 - vignette)) + g),
        clamp(int(col[1] * (1.0 - vignette)) + g),
        clamp(int(col[2] * (1.0 - vignette)) + g),
    )


def bg_at(x: int, y: int) -> tuple[int, int, int]:
    """Flat backdrop color at a point, so overlay tiles blend in."""
    return backdrop_color(x, y, grain=False)


def make_backdrop(width: int = 320, height: int = 240) -> Image.Image:
    img = Image.new("RGB", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            px[x, y] = backdrop_color(x, y, width, height)
    return img


def make_pb(width: int = 304, height: int = 15) -> Image.Image:
    img = Image.new("RGB", (width, height), TRACK)
    px = img.load()
    for x in range(width):
        t = x / max(width - 1, 1)
        color = lerp_rgb(AMBER, AMBER_LIGHT, t * 0.6)
        for y in range(1, height - 1):
            px[x, y] = color
    for x in range(width):
        px[x, 0] = TRACK_EDGE
        px[x, height - 1] = TRACK_EDGE
    for y in range(height):
        px[0, y] = TRACK_EDGE
        px[width - 1, y] = TRACK_EDGE
    return img


def eye_gray(target_w: int) -> Image.Image:
    """Load the Yorushika logo, autocrop, scale to target width, return grayscale (dark = ink)."""
    src = Image.open(LOGO_SRC).convert("L")
    bbox = ImageOps.invert(src).getbbox()
    if bbox:
        src = src.crop(bbox)
    w0, h0 = src.size
    target_h = max(1, round(target_w * h0 / w0))
    return src.resize((target_w, target_h), Image.LANCZOS)


def paint_eye(img: Image.Image, ox: int, oy: int, gray: Image.Image, fg: tuple[int, int, int], thresh: int = 150) -> None:
    gp = gray.load()
    px = img.load()
    w, h = gray.size
    for y in range(h):
        for x in range(w):
            if gp[x, y] < thresh:
                px[ox + x, oy + y] = fg


def make_logo(width: int = 30) -> Image.Image:
    gray = eye_gray(width)
    w, h = gray.size
    img = Image.new("RGB", (w, h), bg_at(288 + w // 2, 12 + h // 2))
    paint_eye(img, 0, 0, gray, AMBER_LIGHT)
    return img


def make_frame(size: int = 104) -> Image.Image:
    """Framed box drawn behind the album art. Album art covers the interior when present;
    when absent, the dim eye placeholder shows."""
    img = Image.new("RGB", (size, size), TRACK)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, size - 1, size - 1], outline=AMBER, width=2)
    gray = eye_gray(round(size * 0.6))
    w, h = gray.size
    paint_eye(img, (size - w) // 2, (size - h) // 2, gray, AMBER)
    return img


def make_vubar(w: int = 12, h: int = 128) -> Image.Image:
    """Solid bright-amber block. One segment of the side peak meters, shown when lit."""
    return Image.new("RGB", (w, h), BRIGHT)


def make_knob(w: int = 7, h: int = 15) -> Image.Image:
    """Traveling marker for the progress bar: a small bright-amber bar."""
    img = Image.new("RGB", (w, h), BRIGHT)
    px = img.load()
    for x in range(w):
        px[x, 0] = AMBER
        px[x, h - 1] = AMBER
    return img


def make_divider(w: int = 320, h: int = 2) -> Image.Image:
    """Bright-amber rule under the top bar, faded at both ends."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    fade = 56
    for x in range(w):
        if x < fade:
            t = x / fade
        elif x > w - 1 - fade:
            t = (w - 1 - x) / fade
        else:
            t = 1.0
        col = lerp_rgb(bg_at(x, 14), BRIGHT, t)
        for y in range(h):
            px[x, y] = col
    return img


def make_battery(w: int = 22, h: int = 11) -> Image.Image:
    """Three-frame strip: low (1 bar), mid (2 bars), full (3 bars)."""
    bg = bg_at(262, 7)
    img = Image.new("RGB", (w, h * 3), bg)
    d = ImageDraw.Draw(img)
    c = BRIGHT

    def cell(oy: int, segs: int) -> None:
        d.rectangle([1, oy + 2, 16, oy + 8], outline=c, width=1)
        d.rectangle([17, oy + 4, 18, oy + 6], fill=c)
        for i in range(segs):
            x0 = 3 + i * 5
            d.rectangle([x0, oy + 4, x0 + 2, oy + 6], fill=c)

    cell(0, 1)
    cell(h, 2)
    cell(h * 2, 3)
    return img


def make_shuffle(w: int = 14, h: int = 11) -> Image.Image:
    bg = bg_at(96, 7)
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    c = AMBER_LIGHT
    d.line([(1, 2), (12, 8)], fill=c, width=1)
    d.line([(1, 8), (12, 2)], fill=c, width=1)
    d.polygon([(12, 0), (13, 3), (10, 3)], fill=c)
    d.polygon([(12, 10), (13, 7), (10, 7)], fill=c)
    return img


def make_repeat(w: int = 14, h: int = 11) -> Image.Image:
    """Two-frame strip: repeat-all, repeat-one."""
    bg = bg_at(112, 7)
    img = Image.new("RGB", (w, h * 2), bg)
    d = ImageDraw.Draw(img)
    c = AMBER_LIGHT

    def loop(oy: int) -> None:
        d.line([(2, oy + 2), (10, oy + 2)], fill=c)
        d.line([(10, oy + 2), (10, oy + 7)], fill=c)
        d.line([(3, oy + 8), (10, oy + 8)], fill=c)
        d.line([(3, oy + 3), (3, oy + 8)], fill=c)
        d.polygon([(2, oy + 2), (5, oy + 0), (5, oy + 4)], fill=c)

    loop(0)
    loop(h)
    d.line([(7, h + 4), (7, h + 9)], fill=c)
    return img


def make_playmode(fw: int = 16, fh: int = 16) -> Image.Image:
    """Vertical 5-frame strip for %mp: stop, play, pause, ff, rew."""
    bg = bg_at(8 + fw // 2, 177 + fh // 2)
    img = Image.new("RGB", (fw, fh * 5), bg)
    d = ImageDraw.Draw(img)
    c = AMBER_LIGHT

    def oy(i: int) -> int:
        return i * fh

    # stop
    d.rectangle([4, oy(0) + 4, 11, oy(0) + 11], fill=c)
    # play
    d.polygon([(5, oy(1) + 3), (5, oy(1) + 12), (12, oy(1) + 7)], fill=c)
    # pause
    d.rectangle([4, oy(2) + 3, 6, oy(2) + 12], fill=c)
    d.rectangle([9, oy(2) + 3, 11, oy(2) + 12], fill=c)
    # fast forward
    d.polygon([(3, oy(3) + 4), (3, oy(3) + 11), (7, oy(3) + 7)], fill=c)
    d.polygon([(8, oy(3) + 4), (8, oy(3) + 11), (12, oy(3) + 7)], fill=c)
    # rewind
    d.polygon([(8, oy(4) + 4), (8, oy(4) + 11), (4, oy(4) + 7)], fill=c)
    d.polygon([(13, oy(4) + 4), (13, oy(4) + 11), (9, oy(4) + 7)], fill=c)
    return img


def make_pb_back(width: int = 304, height: int = 15) -> Image.Image:
    """Empty progress groove: dark fill, no amber. The amber pb.bmp fills over it."""
    img = Image.new("RGB", (width, height), TRACK)
    px = img.load()
    for x in range(width):
        px[x, 0] = TRACK_EDGE
        px[x, height - 1] = TRACK_EDGE
    for y in range(height):
        px[0, y] = TRACK_EDGE
        px[width - 1, y] = TRACK_EDGE
    return img


def save_bmp(path: Path, img: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "BMP")


def main() -> None:
    if not LOGO_SRC.exists():
        raise SystemExit(f"Missing logo source: {LOGO_SRC}")
    save_bmp(OUT / "backdrop.bmp", make_backdrop())
    save_bmp(OUT / "pb.bmp", make_pb())
    save_bmp(OUT / "pb_back.bmp", make_pb_back())
    save_bmp(OUT / "logo.bmp", make_logo())
    save_bmp(OUT / "frame.bmp", make_frame(132))
    save_bmp(OUT / "playmode.bmp", make_playmode())
    save_bmp(OUT / "shuffle.bmp", make_shuffle())
    save_bmp(OUT / "repeat.bmp", make_repeat())
    save_bmp(OUT / "vubar.bmp", make_vubar())
    save_bmp(OUT / "divider.bmp", make_divider())
    save_bmp(OUT / "battery.bmp", make_battery())
    save_bmp(OUT / "knob.bmp", make_knob())
    print(f"Wrote 24-bit BMP assets to {OUT}")


if __name__ == "__main__":
    main()
