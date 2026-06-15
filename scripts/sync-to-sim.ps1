# Sync h2yorushika theme files to a Rockbox UI simulator simdisk.
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
    @{ Src = "themes\h2yorushika.cfg"; Dst = "themes\h2yorushika.cfg" },
    @{ Src = "wps\h2yorushika.wps"; Dst = "wps\h2yorushika.wps" },
    @{ Src = "wps\h2yorushika.sbs"; Dst = "wps\h2yorushika.sbs" },
    @{ Src = "fonts\13-Sazanami-Mincho.fnt"; Dst = "fonts\13-Sazanami-Mincho.fnt" },
    @{ Src = "icons\h2yorushika-icons.bmp"; Dst = "icons\h2yorushika-icons.bmp" },
    @{ Src = "icons\h2yorushika-viewers.bmp"; Dst = "icons\h2yorushika-viewers.bmp" }
)

$imageNames = @("backdrop.bmp", "pb_back.bmp", "logo.bmp", "frame.bmp", "playmode.bmp", "shuffle.bmp", "repeat.bmp", "volbar.bmp", "vubar.bmp", "divider.bmp", "battery.bmp", "knob.bmp")

foreach ($item in $items) {
    $from = Join-Path $source $item.Src
    $toDir = Join-Path $target (Split-Path $item.Dst -Parent)
    New-Item -ItemType Directory -Force -Path $toDir | Out-Null
    Copy-Item -Path $from -Destination (Join-Path $target $item.Dst) -Force
    Write-Host "Copied $($item.Src)"
}

$imagesSrc = Join-Path $source "wps\h2yorushika"
$imagesDst = Join-Path $target "wps\h2yorushika"
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

$configPath = Join-Path $target "config.cfg"
if (Test-Path $configPath) {
    $lines = Get-Content $configPath
    $updated = $lines | ForEach-Object {
        if ($_ -match '^(font|wps|sbs|statusbar|iconset|viewers iconset): ') {
            switch -Regex ($_) {
                '^font: '              { 'font: /.rockbox/fonts/13-Sazanami-Mincho.fnt' }
                '^wps: '               { 'wps: /.rockbox/wps/h2yorushika.wps' }
                '^sbs: '               { 'sbs: /.rockbox/wps/h2yorushika.sbs' }
                '^statusbar: '         { 'statusbar: custom' }
                '^iconset: '           { 'iconset: /.rockbox/icons/h2yorushika-icons.bmp' }
                '^viewers iconset: '   { 'viewers iconset: /.rockbox/icons/h2yorushika-viewers.bmp' }
                default                { $_ }
            }
        } else { $_ }
    }
    $hasIconset = $updated | Where-Object { $_ -match '^iconset: ' }
    $hasViewers = $updated | Where-Object { $_ -match '^viewers iconset: ' }
    if (-not $hasIconset) {
        $updated += 'iconset: /.rockbox/icons/h2yorushika-icons.bmp'
    }
    if (-not $hasViewers) {
        $updated += 'viewers iconset: /.rockbox/icons/h2yorushika-viewers.bmp'
    }
    Set-Content -Path $configPath -Value $updated -Encoding UTF8
    Write-Host "Updated config.cfg (font, wps, sbs, iconset)"
}

Write-Host "Restart rockboxui.exe, then Settings -> Theme Settings -> Browse Theme Files -> h2yorushika"
