#!/usr/bin/env python3
"""Generate Rockbox BMP assets for h2yorushika (24-bit, PIL — matches official theme packs)."""

from __future__ import annotations

import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".rockbox" / "wps" / "h2yorushika"
ICON_OUT = ROOT / ".rockbox" / "icons"
SBS_PATH = ROOT / ".rockbox" / "wps" / "h2yorushika.sbs"
WPS_PATH = ROOT / ".rockbox" / "wps" / "h2yorushika.wps"
LOGO_SRC = ROOT / "assets" / "yorushika-logo.png"
TANGO_REF = ROOT / "assets" / "tango_ref.bmp"
TANGO_VIEWERS_REF = ROOT / "assets" / "tango_viewers_ref.bmp"

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


ICON_SIZE = 16
ICON_COUNT = 32  # Icon_Last_Themeable in Rockbox
INK = BRIGHT
INK_DIM = AMBER_LIGHT
INK_FAINT = AMBER
INK_SHADOW = (0x6B, 0x52, 0x35)


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


# Rendered backdrop, set in main() before any icon tile is built.
BACKDROP: Image.Image | None = None


def bg_tile(dx: int, dy: int, w: int, h: int, frames: int = 1) -> Image.Image:
    """Icon background cut straight from the backdrop at the spot it is drawn.

    Rockbox draws these tiles opaque, so matching the leather pixel-for-pixel
    is what makes them blend. Multi-frame strips repeat the same crop because
    every frame is drawn at the one viewport position.
    """
    if BACKDROP is None:
        raise RuntimeError("BACKDROP not rendered yet")
    crop = BACKDROP.crop((dx, dy, dx + w, dy + h)).convert("RGB")
    if frames == 1:
        return crop.copy()
    img = Image.new("RGB", (w, h * frames))
    for i in range(frames):
        img.paste(crop, (0, i * h))
    return img


# Where each icon BMP is drawn on screen, parsed from the skin files so the
# crops follow the layout instead of hardcoded coordinates that drift.
POS: dict[str, tuple[int, int]] = {}


def icon_positions() -> dict[str, tuple[int, int]]:
    """Map icon filename -> (x, y) draw position from the .sbs / .wps skins.

    Tracks the current %V(x,y,...) viewport and records the position of the
    first %xd(label) that draws a label defined by %xl(label,file,...).
    """
    v_re = re.compile(r"%V\(\s*(-?\d+),\s*(-?\d+)")
    xl_re = re.compile(r"%xl\(\s*([A-Za-z]),\s*([^,)]+)")
    xd_re = re.compile(r"%xd\(\s*([A-Za-z])")
    label_file: dict[str, str] = {}
    pos: dict[str, tuple[int, int]] = {}
    for path in (SBS_PATH, WPS_PATH):
        if not path.exists():
            continue
        vp = (0, 0)
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            for m in xl_re.finditer(line):
                label_file[m.group(1)] = m.group(2).strip()
            mv = v_re.search(line)
            if mv:
                vp = (int(mv.group(1)), int(mv.group(2)))
            for m in xd_re.finditer(line):
                fname = label_file.get(m.group(1))
                if fname and fname not in pos:
                    pos[fname] = vp
    return pos


def tile_at(fname: str, w: int, h: int, frames: int = 1, default: tuple[int, int] = (0, 0)) -> Image.Image:
    """Background tile for an icon, cut from the backdrop at the icon's parsed
    draw position so it blends regardless of where the skin places it."""
    dx, dy = POS.get(fname, default)
    return bg_tile(dx, dy, w, h, frames)


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
    img = tile_at("logo.bmp", w, h, default=(4, 0))
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
        dy = POS.get("divider.bmp", (0, 16))[1]
        base = BACKDROP.getpixel((x, dy)) if BACKDROP is not None else bg_at(x, dy)
        col = lerp_rgb(base, BRIGHT, t)
        for y in range(h):
            px[x, y] = col
    return img


def make_battery(w: int = 21, h: int = 11) -> Image.Image:
    """Three-frame strip: low (1 bar), mid (2 bars), full (3 bars)."""
    img = tile_at("battery.bmp", w, h, frames=3, default=(254, 4))
    d = ImageDraw.Draw(img)
    c = BRIGHT

    # Inner casing is x=2..14; keep 1px inset on both sides (x=2 and x=14).
    CHARGE_X = (3, 7, 11)

    def cell(oy: int, segs: int) -> None:
        d.rectangle([1, oy + 2, 15, oy + 8], outline=c, width=1)
        d.rectangle([16, oy + 4, 17, oy + 6], fill=c)
        for i in range(segs):
            x0 = CHARGE_X[i]
            d.rectangle([x0, oy + 4, x0 + 2, oy + 6], fill=c)

    cell(0, 1)
    cell(h, 2)
    cell(h * 2, 3)
    return img


def make_shuffle(w: int = 14, h: int = 11) -> Image.Image:
    """Two-frame strip: dim (off), bright (on)."""
    img = tile_at("shuffle.bmp", w, h, frames=2, default=(144, 8))
    d = ImageDraw.Draw(img)

    def draw_shuffle(oy: int, c: tuple[int, int, int]) -> None:
        d.line([(1, oy + 2), (12, oy + 8)], fill=c, width=1)
        d.line([(1, oy + 8), (12, oy + 2)], fill=c, width=1)
        d.polygon([(12, oy + 0), (13, oy + 3), (10, oy + 3)], fill=c)
        d.polygon([(12, oy + 10), (13, oy + 7), (10, oy + 7)], fill=c)

    draw_shuffle(0, DIM_AMBER)
    draw_shuffle(h, AMBER_LIGHT)
    return img


def make_repeat(w: int = 14, h: int = 11) -> Image.Image:
    """Three-frame strip: dim (off), repeat-all, repeat-one."""
    img = tile_at("repeat.bmp", w, h, frames=3, default=(160, 8))
    d = ImageDraw.Draw(img)

    def loop(oy: int, c: tuple[int, int, int]) -> None:
        d.line([(2, oy + 2), (10, oy + 2)], fill=c)
        d.line([(10, oy + 2), (10, oy + 7)], fill=c)
        d.line([(3, oy + 8), (10, oy + 8)], fill=c)
        d.line([(3, oy + 3), (3, oy + 8)], fill=c)
        d.polygon([(2, oy + 2), (5, oy + 0), (5, oy + 4)], fill=c)

    loop(0, DIM_AMBER)
    loop(h, AMBER_LIGHT)
    loop(h * 2, AMBER_LIGHT)
    d.line([(7, h * 2 + 4), (7, h * 2 + 9)], fill=AMBER_LIGHT)
    return img


def make_playmode(fw: int = 16, fh: int = 16) -> Image.Image:
    """Vertical 5-frame strip for %mp: stop, play, pause, ff, rew."""
    img = tile_at("playmode.bmp", fw, fh, frames=5, default=(82, 2))
    d = ImageDraw.Draw(img)
    c = AMBER_LIGHT

    def oy(i: int) -> int:
        return i * fh

    # Glyphs centered in 16px frame (center y=7) for status bar viewport y=7.
    # stop
    d.rectangle([4, oy(0) + 3, 11, oy(0) + 10], fill=c)
    # play
    d.polygon([(5, oy(1) + 3), (5, oy(1) + 11), (12, oy(1) + 7)], fill=c)
    # pause
    d.rectangle([4, oy(2) + 3, 6, oy(2) + 10], fill=c)
    d.rectangle([9, oy(2) + 3, 11, oy(2) + 10], fill=c)
    # fast forward
    d.polygon([(3, oy(3) + 3), (3, oy(3) + 10), (7, oy(3) + 6)], fill=c)
    d.polygon([(8, oy(3) + 3), (8, oy(3) + 10), (12, oy(3) + 6)], fill=c)
    # rewind
    d.polygon([(8, oy(4) + 3), (8, oy(4) + 10), (4, oy(4) + 6)], fill=c)
    d.polygon([(13, oy(4) + 3), (13, oy(4) + 10), (9, oy(4) + 6)], fill=c)
    return img


def _icon_tile(draw_fn) -> Image.Image:
    tile = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(tile))
    return tile


def _draw_menu_files(d: ImageDraw.ImageDraw) -> None:
    d.polygon([(2, 6), (6, 6), (7, 4), (11, 4), (12, 6), (13, 6)], fill=INK_DIM)
    d.rectangle([2, 6, 13, 13], outline=INK)


def _draw_menu_playlist(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([4, 2, 12, 13], outline=INK)
    for y in (5, 8, 11):
        d.line([(6, y), (11, y)], fill=INK_DIM)
    d.ellipse([9, 10, 11, 12], fill=INK)
    d.line([(10, 7), (10, 10)], fill=INK)


def _draw_menu_plugin(d: ImageDraw.ImageDraw) -> None:
    c = INK
    d.line([(8, 2), (8, 13)], fill=c)
    d.line([(2, 7), (13, 7)], fill=c)
    d.line([(4, 4), (12, 11)], fill=INK_DIM)
    d.line([(12, 4), (4, 11)], fill=INK_DIM)
    d.rectangle([7, 6, 8, 8], fill=c)


def _draw_menu_theme(d: ImageDraw.ImageDraw) -> None:
    """Theme Settings — screen + palette swatches (Icon_Wps, slot 4)."""
    d.rectangle([2, 3, 9, 10], outline=INK)
    d.line([(4, 6), (7, 6)], fill=INK_DIM)
    d.line([(4, 8), (7, 8)], fill=INK_FAINT)
    d.ellipse([10, 4, 12, 6], fill=INK)
    d.ellipse([11, 7, 13, 9], fill=INK_DIM)
    d.ellipse([9, 9, 11, 11], fill=INK_FAINT)


def _draw_menu_shortcuts(d: ImageDraw.ImageDraw) -> None:
    """Shortcuts — keyboard grid + lightning bolt (Icon_Bookmark, slot 10)."""
    d.rectangle([2, 7, 13, 13], outline=INK)
    d.line([(5, 7), (5, 13)], fill=INK_DIM)
    d.line([(9, 7), (9, 13)], fill=INK_DIM)
    d.line([(2, 10), (13, 10)], fill=INK_DIM)
    d.polygon([(4, 2), (7, 6), (6, 6), (8, 10), (5, 7), (6, 7)], fill=INK)


def _draw_menu_setting(d: ImageDraw.ImageDraw) -> None:
    """Per-item settings — clock face (Icon_Menu_setting, slot 17; shared fallback)."""
    d.ellipse([3, 3, 12, 12], outline=INK)
    d.ellipse([6, 6, 9, 9], fill=INK_FAINT)
    d.line([(7, 7), (7, 5)], fill=INK)
    d.line([(7, 7), (10, 8)], fill=INK)


def _draw_menu_settings(d: ImageDraw.ImageDraw) -> None:
    """Settings root — cog + submenu arrow (Icon_Submenu_Entered, slot 20)."""
    d.ellipse([2, 4, 9, 11], outline=INK)
    d.ellipse([4, 6, 7, 9], fill=INK_FAINT)
    for i in range(6):
        a = i * math.pi / 3
        x0 = 5.5 + 5 * math.cos(a)
        y0 = 7.5 + 5 * math.sin(a)
        x1 = 5.5 + 3 * math.cos(a)
        y1 = 7.5 + 3 * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill=INK, width=1)
    d.polygon([(10, 6), (10, 9), (13, 7)], fill=INK)


def _draw_menu_general_settings(d: ImageDraw.ImageDraw) -> None:
    """General Settings — three sliders (Icon_General_settings_menu, slot 23)."""
    for y, knob in ((4, 9), (7, 6), (10, 11)):
        d.line([(2, y), (13, y)], fill=INK_DIM)
        d.rectangle([knob - 1, y - 1, knob + 1, y + 1], fill=INK)


def _draw_menu_system(d: ImageDraw.ImageDraw) -> None:
    d.ellipse([4, 4, 11, 11], outline=INK)
    d.ellipse([6, 6, 9, 9], fill=INK_FAINT)
    for i in range(8):
        a = i * math.pi / 4
        x0 = 7.5 + 5 * math.cos(a)
        y0 = 7.5 + 5 * math.sin(a)
        x1 = 7.5 + 3 * math.cos(a)
        y1 = 7.5 + 3 * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill=INK, width=1)


def _draw_menu_now_playing(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([3, 3, 12, 11], outline=INK)
    d.polygon([(6, 5), (6, 10), (11, 7)], fill=INK)
    d.line([(5, 12), (10, 12)], fill=INK_DIM)


# Icon indices from apps/gui/icon.h (0-based after Icon_NOICON=-1).
# Menu assignments from apps/root_menu.c, apps/menus/main_menu.c, theme_menu.c.
MENU_ICON_OVERRIDES: dict[int, object] = {
    2: _draw_menu_playlist,           # Playlists
    4: _draw_menu_theme,              # Theme Settings (Icon_Wps)
    9: _draw_menu_plugin,             # Plugins
    10: _draw_menu_shortcuts,         # Shortcuts (Icon_Bookmark)
    17: _draw_menu_setting,           # Time & Date + MT_SETTING fallback
    20: _draw_menu_settings,          # Settings root (Icon_Submenu_Entered)
    23: _draw_menu_general_settings,  # General Settings
    24: _draw_menu_system,            # System
    25: _draw_menu_now_playing,       # Now Playing
    29: _draw_menu_files,             # Files
}


def _rockbox_tile() -> Image.Image:
    tile = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    gray = eye_gray(13)
    w, h = gray.size
    paint_eye(tile, (ICON_SIZE - w) // 2, (ICON_SIZE - h) // 2, gray, INK)
    return tile


def _apply_menu_icon_overrides(strip: Image.Image) -> Image.Image:
    for idx, draw_fn in MENU_ICON_OVERRIDES.items():
        strip.paste(_icon_tile(draw_fn), (0, idx * ICON_SIZE))
    strip.paste(_rockbox_tile(), (0, (ICON_COUNT - 1) * ICON_SIZE))
    return strip


def _ensure_tango_asset(path: Path, url: str) -> None:
    if path.exists():
        return
    import urllib.request

    path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, path)


def recolor_icon_strip(src: Image.Image) -> Image.Image:
    """Map Tango glyphs to the Elma amber palette while keeping their shading."""
    src = src.convert("RGBA")
    out = Image.new("RGBA", src.size)
    spx, opx = src.load(), out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = spx[x, y]
            if a < 20:
                opx[x, y] = (0, 0, 0, 0)
                continue
            lum = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0
            if lum > 0.72:
                col = INK
            elif lum > 0.48:
                col = INK_DIM
            elif lum > 0.28:
                col = INK_FAINT
            else:
                col = INK_SHADOW
            opx[x, y] = (*col, a)
    return out


def make_iconset() -> Image.Image:
    _ensure_tango_asset(
        TANGO_REF,
        "https://git.rockbox.org/cgit/rockbox.git/plain/icons/tango_icons.16x16.bmp",
    )
    strip = recolor_icon_strip(Image.open(TANGO_REF))
    return _apply_menu_icon_overrides(strip)


def make_viewers_iconset() -> Image.Image:
    _ensure_tango_asset(
        TANGO_VIEWERS_REF,
        "https://git.rockbox.org/cgit/rockbox.git/plain/icons/tango_icons_viewers.16x16.bmp",
    )
    return recolor_icon_strip(Image.open(TANGO_VIEWERS_REF))


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


def _bgra_pixel_rows(img: Image.Image) -> bytes:
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    rows = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b, a = px[x, y]
            rows.extend((b, g, r, a))
    return bytes(rows)


def save_bmp32_rgba(path: Path, img: Image.Image, template: Path) -> None:
    """Write a Rockbox-compatible 32-bit BMP using the official icon header layout."""
    import struct

    img = img.convert("RGBA")
    w, h = img.size
    with open(template, "rb") as f:
        header = bytearray(f.read(122))

    row_bytes = w * 4
    pixel_data_size = row_bytes * h
    file_size = 122 + pixel_data_size
    struct.pack_into("<I", header, 2, file_size)
    struct.pack_into("<i", header, 18, w)
    struct.pack_into("<i", header, 22, h)
    struct.pack_into("<I", header, 34, pixel_data_size)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(header)
        f.write(_bgra_pixel_rows(img))


def save_icon_bmp(path: Path, img: Image.Image) -> None:
    template = TANGO_VIEWERS_REF if img.height <= 176 else TANGO_REF
    _ensure_tango_asset(
        template,
        "https://git.rockbox.org/cgit/rockbox.git/plain/icons/"
        + ("tango_icons_viewers.16x16.bmp" if img.height <= 176 else "tango_icons.16x16.bmp"),
    )
    save_bmp32_rgba(path, img, template)


def main() -> None:
    global BACKDROP, POS
    if not LOGO_SRC.exists():
        raise SystemExit(f"Missing logo source: {LOGO_SRC}")
    POS = icon_positions()
    print(f"Icon positions from skins: {POS}")
    BACKDROP = make_backdrop()
    save_bmp(OUT / "backdrop.bmp", BACKDROP)
    save_bmp(OUT / "pb.bmp", make_pb())
    save_bmp(OUT / "pb_back.bmp", make_pb_back())
    save_bmp(OUT / "logo.bmp", make_logo())
    save_bmp(OUT / "frame.bmp", make_frame(140))
    save_bmp(OUT / "playmode.bmp", make_playmode())
    save_bmp(OUT / "shuffle.bmp", make_shuffle())
    save_bmp(OUT / "repeat.bmp", make_repeat())
    save_bmp(OUT / "vubar.bmp", make_vubar())
    save_bmp(OUT / "divider.bmp", make_divider())
    save_bmp(OUT / "battery.bmp", make_battery())
    save_bmp(OUT / "knob.bmp", make_knob())
    save_icon_bmp(ICON_OUT / "h2yorushika-icons.bmp", make_iconset())
    save_icon_bmp(ICON_OUT / "h2yorushika-viewers.bmp", make_viewers_iconset())
    print(f"Wrote 24-bit BMP assets to {OUT}")
    print(f"Wrote menu iconsets to {ICON_OUT}")


if __name__ == "__main__":
    main()
