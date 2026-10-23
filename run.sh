#!/usr/bin/env bash
# ScamShield AI — Local Dev Server Launcher (macOS / Linux)
set -e

echo "========================================================"
echo "  ScamShield AI — Scam & Phishing Detection System"
echo "  KLE BCA Coding Club — Problem AI · 03"
echo "========================================================"
echo ""

if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
fi

echo "Starting Uvicorn web server on http://127.0.0.1:8000 ..."
echo "  - Web Dashboard:  http://127.0.0.1:8000"
echo "  - API Swagger UI: http://127.0.0.1:8000/docs"
echo ""

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
