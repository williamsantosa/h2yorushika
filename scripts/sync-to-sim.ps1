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
    @{ Src = "wps\h2yorushika.sbs"; Dst = "wps\h2yorushika.sbs" }
)

foreach ($item in $items) {
    $from = Join-Path $source $item.Src
    $toDir = Join-Path $target (Split-Path $item.Dst -Parent)
    New-Item -ItemType Directory -Force -Path $toDir | Out-Null
    Copy-Item -Path $from -Destination (Join-Path $target $item.Dst) -Force
    Write-Host "Copied $($item.Src)"
}

$imagesSrc = Join-Path $source "wps\h2yorushika\images"
$imagesDst = Join-Path $target "wps\h2yorushika"
if (Test-Path $imagesSrc) {
    New-Item -ItemType Directory -Force -Path $imagesDst | Out-Null
    Get-ChildItem $imagesSrc -File | Where-Object { -not $_.Name.StartsWith(".") } | ForEach-Object {
        Copy-Item $_.FullName -Destination $imagesDst -Force
        Write-Host "Copied image $($_.Name)"
    }
}

Write-Host ""
Write-Host "Synced to $target"
Write-Host "Restart rockboxui.exe, then Settings -> Theme Settings -> Browse Theme Files -> h2yorushika"
