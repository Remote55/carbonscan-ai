# Run Flutter app in dev mode with dart-defines from a .env file (Windows)
#
# Usage:
#   .\scripts\run-dev.ps1
#   .\scripts\run-dev.ps1 -DeviceId emulator-5554

param(
    [string]$DeviceId = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ScriptDir)

if (-not (Test-Path .env)) {
    Write-Host "ERROR: apps\mobile\.env not found. Copy .env.example to .env first." -ForegroundColor Red
    exit 1
}

# Build --dart-define args from .env (skipping comments + blank lines)
$Defines = @()
Get-Content .env | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#")) {
        $Defines += "--dart-define=$line"
    }
}

Write-Host "Running with defines:" -ForegroundColor Cyan
$Defines | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }

$args = $Defines
if ($DeviceId) {
    $args += "-d", $DeviceId
}

flutter run @args
