# Theme guide

How **h2yorushika** is built. Use this to update this theme or start another one.

Target: **320×240**, **16-bit color**, HiFi Walker H2 (`erosqnative`).

---

## The five files Rockbox needs

A theme is not one file. Rockbox loads a bundle.

| File | Role |
|------|------|
| `themes/*.cfg` | Points to WPS, SBS, font, colors, icon paths |
| `wps/*.wps` | **W**hile **P**laying **S**creen — music UI |
| `wps/*.sbs` | **S**tatus **B**ar **S**kin — status bar, menus, file browser, settings (see below) |
| `wps/<name>/*.bmp` | Images the skins reference |
| `fonts/*.fnt` | UI font (needs CJK for Japanese titles) |

Optional but used here:

| File | Role |
|------|------|
| `icons/*-icons.bmp` | Menu icons (`__list_icons__` in skin) |
| `icons/*-viewers.bmp` | File-browser icons |

The `.cfg` is the entry point. Everything else is linked from it.

---

## Screen layout (this theme)

```
y=0   ┌──────────────────────────────────────┐
      │  Status bar (sbs) — 32px tall      │  logo, clock, controls, title, battery
y=32  ├──────────────────────────────────────┤
      │                                      │
      │  Content (menus or WPS body)         │  208px tall
      │                                      │
y=240 └──────────────────────────────────────┘
```

**SBS** owns the top band on every screen. **WPS** owns the large area below it only while music is playing. Menus use that same lower area, but **SBS** draws them — not WPS.

Coordinates are pixels. `(0,0)` is top-left. Width is always 320 on this device.

Negative X means “from the right edge.” `%V(-21,8,21,12)` places a 21px-wide box with its left edge at `320 - 21 = 299`.

---

## WPS vs SBS — who draws the menus?

The name **SBS** suggests a thin bar at the top. That is only half true.

| Screen | Top bar (y=0–31) | Main area (y=32–240) |
|--------|------------------|----------------------|
| Music (WPS) | SBS | WPS |
| Root menu | SBS | SBS |
| File browser | SBS | SBS |
| Settings, playlists, database | SBS | SBS |

**WPS never draws the root menu or file tree.** Edit `.wps` for the music screen only.

**SBS draws the status bar and all list UIs.** Root menu tiles, folder listings, settings rows, playlist tracks — all use the `%Vi` / `%Lb` / `%Vl` blocks at the bottom of `h2yorushika.sbs`.

Your `.cfg` sets `statusbar: custom`. That flag tells Rockbox to load the `.sbs` file for the whole non-WPS chrome, not just the top strip.

### Firmware vs theme

Rockbox **firmware** owns structure. The theme cannot change it.

- Which items appear in the root menu (Files, Database, Settings, …)
- How folder navigation works (enter folder, go up, open a file)
- What happens when you select an item

The **theme** owns appearance.

- Tile grid vs plain list
- Row height, colors, selection highlight
- Icons per row (`%LI`), labels (`%LT`)
- Status bar layout above the list

```
Firmware  →  what menus exist, what files are in a folder
.sbs      →  how those lists look (tiles, rows, icons, colors)
.cfg      →  font, default colors, icon BMP paths
icons/*.bmp → glyphs for %xd(I,%LI,2)
```

In `h2yorushika.sbs`, the split is explicit:

- `%?if(%Lt,=,Rockbox)` → root menu uses `%Lb(tile,160,52,tile)` (2×4 tiles)
- Everything else → `%Lb(row,320,18)` (18px rows)

The file browser uses the **row** layout. Same `%Vl(row,…)` block as Settings and album track lists.

---

## Skin language (beginner tags)

Skins are text files full of **tags**. Tags start with `%`.

### Load images

```
%xl(B,battery.bmp,0,0,3)
```

Preload `battery.bmp` as label `B`. The `3` means three frames stacked vertically in one BMP (low / mid / full battery).

```
%xd(Bb)
```

Draw frame `b` of image `B` (a=first, b=second, c=third).

### Place a box of content

```
%V(176,7,52,14,1)
%Vf(F0E8DC)
%s%ac%?it<%it|%fn>
```

- `%V(x,y,w,h,font)` — viewport (a rectangle)
- `%Vf(RRGGBB)` — text color
- `%al` / `%ac` / `%ar` — align left, center, right
- `%s` — scroll long text
- `%it` — track title; `%fn` — filename fallback

### Conditionals

```
%?if(%mp,>,1)<%s%ac%?it<%it|%fn>|>
```

If play mode is greater than 1 (not stopped), show the title. Otherwise show nothing.

`%mp`: 1=stop, 2=play, 3=pause.

### Lists (menus)

```
%Lb(tile,160,52,tile)
%Vl(tile,4,36,152,14,1)
%ac%LT
```

- `%Lb` — draw list in cells of 160×52
- `%Vl` — viewport **inside each cell** (label `tile`)
- `%LT` — this row's text
- `%LI` — this row's icon index
- `%LN` — row number (1-based)
- `%Lc` — true if this row is selected

Root menu uses tiles. Submenus use `%Lb(row,320,18)` and a single `%Vl(row,…)` block.

---

## How this theme splits work

### `h2yorushika.cfg`

Sets paths, default colors, peak meter range (`peak meter min: 18` for log-style meters), `statusbar: custom`, `playlist viewer icons: on`.

Foreground `F0E8DC` is off-white. Background `221013` is oxblood.

### `h2yorushika.sbs`

Two jobs in one file: status bar (lines 1–62) and menu chrome (lines 64–86).

**Status bar:** logo, clock, play/shuffle/repeat, now-playing title, volume, battery, divider.

**Menu chrome:** `%Vi` sets the list area. `%Lb` + `%Vl` paint each cell or row. See [WPS vs SBS](#wps-vs-sbs--who-draws-the-menus) above.

Highlights:

- Logo + ヨルシカ wordmark (gold `C89B5A`)
- Center slot: now-playing title when `%mp > 1`, else blank
- Root **Rockbox** menu only: 2×4 tiles with label under icon
- All other menus: 18px list rows

Root tiles are gated with `%?if(%Lt,=,Rockbox)`. English menu title only. If you use another UI language, tiles may fall back to a plain list until you adjust that string.

### `h2yorushika.wps`

Album art left, metadata right, peak meters above art, progress bar with `pb_back.bmp` + `knob.bmp` slider. No amber fill inside the bar — only the knob moves.

Peak meters use `%pL` / `%pR` over `volbar.bmp` / `vubar.bmp`. Tuning lives in the `.cfg` (`peak meter min` / `max`).

---

## Icons

Menu icons come from `icons/h2yorushika-icons.bmp` — a vertical strip of 16×16 cells, one per Rockbox icon index (32 slots).

In the skin:

```
%xl(I,__list_icons__,0,0)
%xd(I,%LI,2)
```

**Important:** Rockbox subtracts 2 from `%LI` when drawing list icons. Pass `,2` as offset so the correct cell shows. Without it, Database, Settings, and others map to the wrong glyph.

Custom icons are drawn in `scripts/generate-assets.py` (`MENU_ICON_OVERRIDES`). The script recolors Tango defaults, then overwrites key slots (playlist, language, database, settings, etc.).

### Playlist row icons

When `%LN` equals `%pp` and audio is playing, the row shows the play-in-circle icon (slot 25). Queued tracks use slot 12. Other rows use `%LI` or nothing.

Requires `playlist viewer icons: on` in the cfg.

---

## BMP assets (`generate-assets.py`)

Run after palette or layout changes:

```powershell
python scripts/generate-assets.py
```

The script:

1. Renders `backdrop.bmp` (procedural leather texture)
2. Parses `h2yorushika.sbs` and `h2yorushika.wps` for `%V` positions
3. Cuts status-icon backgrounds from the backdrop at those positions so opaque icons blend
4. Draws icons (battery, shuffle, play mode, tile highlight, etc.)
5. Builds menu icon strips from `assets/yorushika-logo.png` + Tango base

**Battery fix:** negative `%V` X must be resolved to screen coordinates before cropping. `x = 320 + (-21) = 299`. A bad crop produced a black rectangle.

Colors live at the top of `generate-assets.py` (`BG`, `BRIGHT`, `AMBER`, …). Change them there, then regenerate.

---

## Workflow: edit → test → ship

```
edit .wps / .sbs / .cfg
        ↓
python scripts/generate-assets.py   (if BMPs or icons changed)
        ↓
.\scripts\sync-to-sim.ps1
        ↓
rockboxui.exe --debugwps
        ↓
copy .rockbox/ to player
```

`sync-to-sim.ps1` copies theme files into `simdisk/.rockbox/` and patches `config.cfg` (font, wps, sbs, iconset, peak meter).

---

## Start a new theme from this one

1. Copy the `.rockbox/` tree. Rename `h2yorushika` everywhere (cfg, wps, sbs, folder).
2. Update `themes/<name>.cfg` paths to match.
3. Change palette constants in `generate-assets.py`. Regenerate assets.
4. Edit layouts in `.wps` and `.sbs`. Keep the 320×240 grid in mind.
5. Swap `assets/yorushika-logo.png` or remove logo viewports in sbs.
6. Test in the sim before copying to hardware.

You do not need to compile Rockbox. Skins are data files.

---

## Debug when something breaks

| Symptom | Likely cause |
|---------|----------------|
| Skin fails to load | Syntax error. Run `rockboxui.exe --debugwps`. Check the line it names. |
| Wrong menu icon | Missing `%LI,2` offset, or wrong slot in `MENU_ICON_OVERRIDES` |
| Black box behind battery | Negative `%V` X not resolved when building BMP |
| Root menu is a list, not tiles | `%Lt` is not `Rockbox` (translated UI language) |
| No now-playing marker in playlist | `playlist viewer icons` off, or `%LN` ≠ `%pp` in that view |
| Japanese titles show boxes | Font missing. Install `13-Sazanami-Mincho.fnt`. |

---

## Further reading

- [CustomWPS tag list](https://www.rockbox.org/wiki/CustomWPS) — full tag reference
- [d00k.net theming](https://d00k.net/wiki/rockbox_theming/introduction/) — gentle tutorial series
- `_iretro/.rockbox/wps/iRetro.sbs` in this repo — reference theme with tile menu pattern

Rockbox source snippets under the repo root (`_skin_parser.c`, `_icon.h`, `_root_menu.c`) are local copies for icon index lookup. They are not shipped to the player.
