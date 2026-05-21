#!/usr/bin/env pwsh
# CarbonScan AI - Setup Script (Windows PowerShell)
#
# Usage:
#   ./scripts/setup.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> CarbonScan AI Setup" -ForegroundColor Green
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Cyan

$node = node --version 2>$null
if (-not $node) { Write-Error "❌ Node.js not installed. Install from https://nodejs.org/" }
Write-Host "✅ Node.js: $node"

$pnpm = pnpm --version 2>$null
if (-not $pnpm) {
    Write-Host "Installing pnpm..." -ForegroundColor Yellow
    npm install -g pnpm
}
Write-Host "✅ pnpm: $(pnpm --version)"

$python = python --version 2>$null
if (-not $python) { Write-Error "❌ Python not installed. Install Python 3.11+" }
Write-Host "✅ Python: $python"

$flutter = flutter --version 2>$null
if (-not $flutter) {
    Write-Warning "⚠️ Flutter not installed. Skipping mobile setup."
    Write-Warning "    Install from https://docs.flutter.dev/get-started/install"
}

Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Cyan

# JS dependencies (monorepo root)
Write-Host ""
Write-Host "📦 Installing Node packages..." -ForegroundColor Yellow
pnpm install

# Python: API
Write-Host ""
Write-Host "🐍 Setting up API (Python)..." -ForegroundColor Yellow
Set-Location services/api
if (-not (Test-Path .venv)) {
    python -m venv .venv
}
& .venv/Scripts/Activate.ps1
pip install --upgrade pip
pip install -e ".[dev]"
deactivate
Set-Location ../..

# Python: ML
Write-Host ""
Write-Host "🧠 Setting up ML (Python)..." -ForegroundColor Yellow
Set-Location services/ml
if (-not (Test-Path .venv)) {
    python -m venv .venv
}
& .venv/Scripts/Activate.ps1
pip install --upgrade pip
pip install -e ".[dev,cpu]"
deactivate
Set-Location ../..

# Flutter (if available)
if ($flutter) {
    Write-Host ""
    Write-Host "📱 Setting up Mobile (Flutter)..." -ForegroundColor Yellow
    Set-Location apps/mobile
    flutter pub get
    Set-Location ../..
}

# Env files
Write-Host ""
Write-Host "📝 Setting up .env files..." -ForegroundColor Yellow

if (Test-Path services/api/.env.example) {
    if (-not (Test-Path services/api/.env)) {
        Copy-Item services/api/.env.example services/api/.env
        Write-Host "  Created services/api/.env (please fill in secrets)"
    }
}

if (Test-Path apps/web/.env.example) {
    if (-not (Test-Path apps/web/.env.local)) {
        Copy-Item apps/web/.env.example apps/web/.env.local
        Write-Host "  Created apps/web/.env.local (please fill in secrets)"
    }
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Fill in .env files (ask User for secrets)"
Write-Host "  2. Run 'pnpm dev' to start Web + API"
Write-Host "  3. Open http://localhost:3000"
Write-Host "  4. Read docs/ONBOARDING.md (30 min)"
Write-Host ""
