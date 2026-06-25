# Sync elmas-diary theme files to a Rockbox UI simulator simdisk.
# Usage: .\scripts\sync-to-sim.ps1
#        .\scripts\sync-to-sim.ps1 -SimPath D:\RockboxSim

param(
    [string]$SimPath = "C:\RockboxSim"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot ".rockbox"
$target = Join-Path $SimPath "simdisk\.rockbox"

if (-not (Test-Path $source)) {
    Write-Error "Theme source not found: $source"
}

if (-not (Test-Path (Join-Path $SimPath "rockboxui.exe"))) {
    Write-Error "Simulator not found at $SimPath (expected rockboxui.exe). Download from README."
}

New-Item -ItemType Directory -Force -Path $target | Out-Null

$items = @(
    @{ Src = "themes\elmas-diary.cfg"; Dst = "themes\elmas-diary.cfg" },
    @{ Src = "wps\elmas-diary.wps"; Dst = "wps\elmas-diary.wps" },
    @{ Src = "wps\elmas-diary.sbs"; Dst = "wps\elmas-diary.sbs" },
    @{ Src = "fonts\13-Sazanami-Mincho.fnt"; Dst = "fonts\13-Sazanami-Mincho.fnt" },
    @{ Src = "icons\elmas-diary-icons.bmp"; Dst = "icons\elmas-diary-icons.bmp" },
    @{ Src = "icons\elmas-diary-viewers.bmp"; Dst = "icons\elmas-diary-viewers.bmp" }
)

$imageNames = @("backdrop.bmp", "pb.bmp", "pb_back.bmp", "logo.bmp", "frame.bmp", "frame_top.bmp", "frame_bottom.bmp", "frame_left.bmp", "frame_right.bmp", "playmode.bmp", "shuffle.bmp", "repeat.bmp", "volbar.bmp", "vubar.bmp", "divider.bmp", "battery.bmp", "knob.bmp", "tile_sel.bmp", "scroll_track.bmp", "scroll_thumb.bmp")

foreach ($item in $items) {
    $from = Join-Path $source $item.Src
    $toDir = Join-Path $target (Split-Path $item.Dst -Parent)
    New-Item -ItemType Directory -Force -Path $toDir | Out-Null
    Copy-Item -Path $from -Destination (Join-Path $target $item.Dst) -Force
    Write-Host "Copied $($item.Src)"
}

$imagesSrc = Join-Path $source "wps\elmas-diary"
$imagesDst = Join-Path $target "wps\elmas-diary"
New-Item -ItemType Directory -Force -Path $imagesDst | Out-Null
foreach ($name in $imageNames) {
    $from = Join-Path $imagesSrc $name
    if (-not (Test-Path $from)) {
        Write-Error "Missing $name - run: python scripts/generate-assets.py"
    }
    Copy-Item -Path $from -Destination (Join-Path $imagesDst $name) -Force
    Write-Host "Copied image $name"
}

Write-Host ""
Write-Host "Synced to $target"

# Remove legacy theme files left from the h2yorushika rename (sync only copies; it does not prune).
$legacy = @(
    "themes\h2yorushika.cfg",
    "wps\h2yorushika.wps",
    "wps\h2yorushika.sbs",
    "icons\h2yorushika-icons.bmp",
    "icons\h2yorushika-viewers.bmp"
)
foreach ($rel in $legacy) {
    $path = Join-Path $target $rel
    if (Test-Path $path) {
        Remove-Item -Path $path -Force
        Write-Host "Removed legacy $rel"
    }
}
$legacyDir = Join-Path $target "wps\h2yorushika"
if (Test-Path $legacyDir) {
    Remove-Item -Path $legacyDir -Recurse -Force
    Write-Host "Removed legacy wps\h2yorushika\"
}

$configPath = Join-Path $target "config.cfg"
if (Test-Path $configPath) {
    $lines = Get-Content $configPath
    $updated = $lines | ForEach-Object {
        if ($_ -match '^(font|wps|sbs|statusbar|iconset|viewers iconset|peak meter dbfs|peak meter min|peak meter max|playlist viewer icons|scrollbar|scrollbar width): ') {
            switch -Regex ($_) {
                '^font: '              { 'font: /.rockbox/fonts/13-Sazanami-Mincho.fnt' }
                '^wps: '               { 'wps: /.rockbox/wps/elmas-diary.wps' }
                '^sbs: '               { 'sbs: /.rockbox/wps/elmas-diary.sbs' }
                '^statusbar: '         { 'statusbar: custom' }
                '^iconset: '           { 'iconset: /.rockbox/icons/elmas-diary-icons.bmp' }
                '^viewers iconset: '   { 'viewers iconset: /.rockbox/icons/elmas-diary-viewers.bmp' }
                '^peak meter dbfs: '   { 'peak meter dbfs: on' }
                '^peak meter min: '    { 'peak meter min: 18' }
                '^peak meter max: '    { 'peak meter max: 0' }
                '^playlist viewer icons: ' { 'playlist viewer icons: on' }
                '^scrollbar: '         { 'scrollbar: off' }
                default                { $_ }
            }
        } else { $_ }
    }
    $hasIconset = $updated | Where-Object { $_ -match '^iconset: ' }
    $hasViewers = $updated | Where-Object { $_ -match '^viewers iconset: ' }
    if (-not $hasIconset) {
        $updated += 'iconset: /.rockbox/icons/elmas-diary-icons.bmp'
    }
    if (-not $hasViewers) {
        $updated += 'viewers iconset: /.rockbox/icons/elmas-diary-viewers.bmp'
    }
    $hasPeakDbfs = $updated | Where-Object { $_ -match '^peak meter dbfs: ' }
    $hasPeakMin = $updated | Where-Object { $_ -match '^peak meter min: ' }
    $hasPeakMax = $updated | Where-Object { $_ -match '^peak meter max: ' }
    $hasPlaylistIcons = $updated | Where-Object { $_ -match '^playlist viewer icons: ' }
    if (-not $hasPeakDbfs) { $updated += 'peak meter dbfs: on' }
    if (-not $hasPeakMin) { $updated += 'peak meter min: 18' }
    if (-not $hasPeakMax) { $updated += 'peak meter max: 0' }
    if (-not $hasPlaylistIcons) { $updated += 'playlist viewer icons: on' }
    $hasScrollbar = $updated | Where-Object { $_ -match '^scrollbar: ' }
    $hasScrollbarWidth = $updated | Where-Object { $_ -match '^scrollbar width: ' }
    if (-not $hasScrollbar) { $updated += 'scrollbar: off' }
    Set-Content -Path $configPath -Value $updated -Encoding UTF8
    Write-Host "Updated config.cfg (font, wps, sbs, iconset, peak meter)"
}

Write-Host "Restart rockboxui.exe, then Settings -> Theme Settings -> Browse Theme Files -> elmas-diary"
