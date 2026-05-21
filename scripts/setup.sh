#!/usr/bin/env bash
# CarbonScan AI - Setup Script (macOS / Linux)
#
# Usage:
#   ./scripts/setup.sh

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}==> CarbonScan AI Setup${NC}"
echo ""

# Check prerequisites
echo -e "${CYAN}Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not installed. Install from https://nodejs.org/${NC}"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}Installing pnpm...${NC}"
    npm install -g pnpm
fi
echo "✅ pnpm: $(pnpm --version)"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python not installed. Install Python 3.11+${NC}"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

if ! command -v flutter &> /dev/null; then
    echo -e "${YELLOW}⚠️ Flutter not installed. Skipping mobile setup.${NC}"
    HAS_FLUTTER=0
else
    HAS_FLUTTER=1
    echo "✅ Flutter: $(flutter --version | head -1)"
fi

echo ""
echo -e "${CYAN}Installing dependencies...${NC}"

# JS dependencies (monorepo root)
echo ""
echo -e "${YELLOW}📦 Installing Node packages...${NC}"
pnpm install

# Python: API
echo ""
echo -e "${YELLOW}🐍 Setting up API (Python)...${NC}"
pushd services/api > /dev/null
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
deactivate
popd > /dev/null

# Python: ML
echo ""
echo -e "${YELLOW}🧠 Setting up ML (Python)...${NC}"
pushd services/ml > /dev/null
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,cpu]"
deactivate
popd > /dev/null

# Flutter
if [ $HAS_FLUTTER -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}📱 Setting up Mobile (Flutter)...${NC}"
    pushd apps/mobile > /dev/null
    flutter pub get
    popd > /dev/null
fi

# Env files
echo ""
echo -e "${YELLOW}📝 Setting up .env files...${NC}"

if [ -f services/api/.env.example ] && [ ! -f services/api/.env ]; then
    cp services/api/.env.example services/api/.env
    echo "  Created services/api/.env (please fill in secrets)"
fi

if [ -f apps/web/.env.example ] && [ ! -f apps/web/.env.local ]; then
    cp apps/web/.env.example apps/web/.env.local
    echo "  Created apps/web/.env.local (please fill in secrets)"
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "  1. Fill in .env files (ask User for secrets)"
echo "  2. Run 'pnpm dev' to start Web + API"
echo "  3. Open http://localhost:3000"
echo "  4. Read docs/ONBOARDING.md (30 min)"
echo ""
