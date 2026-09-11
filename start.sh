#!/usr/bin/env bash
# ============================================================
#  Algorithm Discovery Lab — One-Click Launcher
#  Run:  chmod +x start.sh && ./start.sh
# ============================================================

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
PORT="${ADL_PORT:-8000}"

# Colors
R='\033[0;31m' G='\033[0;32m' C='\033[0;36m' Y='\033[1;33m' B='\033[1m' D='\033[0m'

clear
echo -e "${C}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║        ALGORITHM DISCOVERY LAB                  ║"
echo "  ║   Search → Verify → Benchmark → Discover        ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${D}"

# ── Step 1: Python check ──────────────────────────────────
echo -e "${B}[1/4]${D} Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo -e "${R}Python3 not found. Install: sudo apt install python3 python3-venv${D}"
    exit 1
fi
PY=$(python3 --version 2>&1)
echo -e "      ${G}Found: $PY${D}"

# ── Step 2: Create venv if missing ────────────────────────
echo -e "${B}[2/4]${D} Setting up virtual environment..."
if [ ! -d "$VENV" ]; then
    echo "      Creating venv..."
    python3 -m venv "$VENV"
    source "$VENV/bin/activate"
    echo "      Installing dependencies (first run)..."
    pip install -q -e "$DIR/." httpx >/dev/null 2>&1
else
    source "$VENV/bin/activate"
fi
echo -e "      ${G}Ready${D}"

# ── Step 3: Kill old server if running ────────────────────
if lsof -ti :"$PORT" &>/dev/null; then
    echo -e "${Y}      Stopping old server on port $PORT...${D}"
    kill $(lsof -ti :"$PORT") 2>/dev/null || true
    sleep 1
fi

# ── Step 4: Start web server ──────────────────────────────
echo -e "${B}[3/4]${D} Starting server on port ${PORT}..."
echo -e "${B}[4/4]${D} ${G}Server running!${D}"
echo ""

cd "$DIR"
python3 -c "
import sys, os, threading, time, webbrowser

sys.path.insert(0, 'web/backend')

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app import app as api_app

FRONTEND = os.path.join('$DIR', 'web', 'frontend')

@api_app.get('/')
async def serve_index():
    return FileResponse(os.path.join(FRONTEND, 'index.html'))

@api_app.get('/{full_path:path}')
async def serve_static(full_path: str):
    file_path = os.path.join(FRONTEND, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND, 'index.html'))

def open_browser():
    time.sleep(2)
    webbrowser.open('http://localhost:$PORT')

threading.Thread(target=open_browser, daemon=True).start()

print('  ╔══════════════════════════════════════════════════╗')
print(f'  ║  Dashboard:   http://localhost:$PORT              ║')
print(f'  ║  API Docs:    http://localhost:$PORT/docs         ║')
print(f'  ║  CLI:         source .venv/bin/activate && adl   ║')
print('  ║                                                  ║')
print('  ║  Press Ctrl+C to stop                            ║')
print('  ╚══════════════════════════════════════════════════╝')
print()

uvicorn.run(api_app, host='0.0.0.0', port=$PORT, log_level='warning')
"
