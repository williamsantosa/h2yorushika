# h2yorushika

A Rockbox theme for the **HiFi Walker H2** (320×240, 16-bit color, `erosqnative`).

## Repository layout

Theme files mirror the on-device `.rockbox` layout:

```
.rockbox/
├── themes/h2yorushika.cfg    # theme config (colors, font, paths)
├── wps/h2yorushika.wps       # music player screen
├── wps/h2yorushika.sbs       # menu status bar
└── wps/h2yorushika/          # BMP assets (backdrop, progress bar)
```

## Install on the H2

1. Connect the player via USB.
2. Copy the contents of `.rockbox/` into the player's `/.rockbox/` folder (merge, don't replace the whole tree).
3. Ensure `11-Sazanami-Mincho.fnt` is in `/.rockbox/fonts/` ([Rockbox font pack](https://www.rockbox.org/daily.shtml)) for Japanese track titles.
4. On the device: **Settings → Theme Settings → Browse Theme Files → h2yorushika**.

## Simulator on Windows 11

Use a pre-built **erosqnative** simulator to test without copying to the player each time.

### Should RockboxSim live in this repo?

**No.** Keep `C:\RockboxSim` (or similar) outside this repository.

- The simulator is ~70+ MB of binaries and bundled Rockbox runtime files.
- `simdisk/` contains generated state (resume config, default themes, plugins) that changes every run.
- It is a separate third-party download, not part of the theme source.

This repo holds **only the theme**. Point the simulator at it with the sync script below.

### One-time simulator setup

1. Download the latest Windows build from [rockbox-sim-builds releases](https://github.com/adriankeenan/rockbox-sim-builds/releases/latest):
   - **`rockboxui-win32-aigo-eros-q-k-native-247-....zip`**
2. Extract to `C:\RockboxSim` (or any path you prefer).
3. Run `make install` equivalent once by starting `rockboxui.exe` — it populates `simdisk/.rockbox/` with defaults.
4. The font `11-Sazanami-Mincho.fnt` is included in most sim installs under `simdisk/.rockbox/fonts/`.
5. Optionally add test MP3s under `C:\RockboxSim\simdisk\` to preview the WPS while playing.

### Sync theme changes to the simulator

After editing files in this repo:

```powershell
cd C:\git\h2yorushika
.\scripts\sync-to-sim.ps1
```

Custom simulator path:

```powershell
.\scripts\sync-to-sim.ps1 -SimPath D:\RockboxSim
```

Then run `rockboxui.exe` from the simulator folder. For WPS errors:

```powershell
.\rockboxui.exe --debugwps
```

### Simulator controls

| Key | Action |
|-----|--------|
| Numpad 8 / Up | Up |
| Numpad 2 / Down | Down |
| Numpad 4 / Left | Previous |
| Numpad 6 / Right | Next |
| Numpad 5 / Enter | Select |
| Numpad 0 / Esc | Back |

## Development workflow

1. Edit `.rockbox/wps/h2yorushika.wps` (layout/tags) and `.rockbox/themes/h2yorushika.cfg` (colors, font).
2. Regenerate BMP assets after palette changes: `python scripts/generate-assets.py`
3. Run `.\scripts\sync-to-sim.ps1` and test in the simulator.
4. Copy `.rockbox/` to the H2 when ready.

## References

- [Rockbox theme tag reference (CustomWPS)](https://www.rockbox.org/wiki/CustomWPS)
- [HiFi Walker H2 / Eros Q wiki](https://www.rockbox.org/wiki/AIGOErosQK)
- [d00k.net theming guide](https://d00k.net/wiki/rockbox_theming/introduction/)
