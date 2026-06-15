#!/usr/bin/env python3
"""Generate Rockbox BMP assets for h2yorushika (24-bit, PIL — matches official theme packs)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".rockbox" / "wps" / "h2yorushika"
LOGO_SRC = ROOT / "assets" / "yorushika-logo.png"

BG = (0x1C, 0x18, 0x14)
BG_LIGHT = (0x28, 0x22, 0x1C)
AMBER = (0x8B, 0x6F, 0x47)
AMBER_LIGHT = (0xA8, 0x90, 0x70)
TRACK = (0x2A, 0x24, 0x1E)
TRACK_EDGE = (0x3D, 0x35, 0x2C)
DIM_AMBER = (0x4A, 0x3E, 0x30)


def clamp(v: int) -> int:
    return max(0, min(255, v))


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def lerp_rgb(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def backdrop_color(x: int, y: int, width: int = 320, height: int = 240, grain: bool = True) -> tuple[int, int, int]:
    cx, cy = width * 0.55, height * 0.35
    max_dist = (width**2 + height**2) ** 0.5
    t = y / max(height - 1, 1)
    base = lerp_rgb(BG, BG_LIGHT, t * 0.35)
    dx, dy = x - cx, y - cy
    dist = (dx * dx + dy * dy) ** 0.5
    vignette = min(dist / (max_dist * 0.65), 1.0) * 0.22
    g = (((x * 17 + y * 31) & 7) - 3) if grain else 0
    return (
        clamp(int(base[0] * (1.0 - vignette)) + g),
        clamp(int(base[1] * (1.0 - vignette)) + g),
        clamp(int(base[2] * (1.0 - vignette)) + g),
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


def make_knob(w: int = 5, h: int = 15) -> Image.Image:
    """Slider playhead for the progress bar: a solid amber bar (no transparency)."""
    img = Image.new("RGB", (w, h), AMBER_LIGHT)
    px = img.load()
    for x in range(w):
        px[x, 0] = AMBER
        px[x, h - 1] = AMBER
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
    save_bmp(OUT / "frame.bmp", make_frame())
    save_bmp(OUT / "playmode.bmp", make_playmode())
    save_bmp(OUT / "knob.bmp", make_knob())
    save_bmp(OUT / "shuffle.bmp", make_shuffle())
    save_bmp(OUT / "repeat.bmp", make_repeat())
    print(f"Wrote 24-bit BMP assets to {OUT}")


if __name__ == "__main__":
    main()
