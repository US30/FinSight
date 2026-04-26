#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  FinSight AI Financial Dashboard"
echo "  ================================"
echo ""

# ── Backend ────────────────────────────────────────────────────────────────────
echo "[1/3] Setting up Python backend..."
cd "$ROOT/backend"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

# Copy .env if needed
if [ ! -f ".env" ] && [ -f "$ROOT/.env" ]; then
  cp "$ROOT/.env" .env
fi

echo "[2/3] Starting FastAPI backend on :8000 ..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# ── Frontend ───────────────────────────────────────────────────────────────────
echo "[3/3] Setting up React frontend..."
cd "$ROOT/frontend"

if [ ! -d "node_modules" ]; then
  echo "      Installing npm dependencies (first run)..."
  npm install
fi

echo "      Starting Vite dev server on :5173 ..."
npm run dev &
FRONTEND_PID=$!

# ── Ready ──────────────────────────────────────────────────────────────────────
echo ""
echo "  ✓ Backend  → http://localhost:8000"
echo "  ✓ Frontend → http://localhost:5173"
echo ""
echo "  Open http://localhost:5173 in your browser."
echo "  Press Ctrl+C to stop."
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
