#!/usr/bin/env bash
# ScamShield AI — Automated Test Suite Runner (macOS / Linux)
set -e

echo "========================================================"
echo "  ScamShield AI — Test Suite Verification"
echo "  KLE BCA Coding Club — Problem AI · 03"
echo "========================================================"
echo ""

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "Running full automated test suite (83 tests)..."
pytest -v
