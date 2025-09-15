#!/usr/bin/env bash
set -euo pipefail

cd /app
export PYTHONPATH=/app

echo "[backend][container] Starting FastAPI (python -m src.main) on ${BACKEND_HOST:-0.0.0.0}:${BACKEND_PORT:-9301}"
exec python -m src.main

