#!/bin/bash

# ============================================================
# StegoTool Launcher
# Linux / macOS
# ============================================================

set -u

# ------------------------------------------------------------
# Colors
# ------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ------------------------------------------------------------
# Project directory
# ------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_FILE="$ROOT_DIR/stegotool.pyw"

echo "========================================"
echo "              STEGOTOOL"
echo "========================================"
echo
echo "[INFO] Checking Python..."
echo

# ------------------------------------------------------------
# Check Python
# ------------------------------------------------------------

if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo -e "${RED}[ERROR]${NC} Python was not found."
    echo
    echo "Please install Python 3 and try again."
    echo
    read -r -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python found: $PYTHON"
echo

# ------------------------------------------------------------
# Check application
# ------------------------------------------------------------

if [ ! -f "$APP_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} StegoTool application not found."
    echo
    echo "Expected:"
    echo "$APP_FILE"
    echo
    read -r -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}[OK]${NC} StegoTool application found."
echo
echo "[INFO] Starting StegoTool..."
echo

# ------------------------------------------------------------
# Launch application
# ------------------------------------------------------------

cd "$ROOT_DIR" || exit 1

nohup "$PYTHON" "$APP_FILE" >/dev/null 2>&1 &
PID=$!

sleep 1

if kill -0 "$PID" 2>/dev/null; then
    echo -e "${GREEN}[OK]${NC} StegoTool started."
    echo "PID: $PID"
else
    echo -e "${RED}[ERROR]${NC} Failed to start StegoTool."
    exit 1
fi

echo

exit 0