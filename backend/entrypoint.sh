#!/usr/bin/env bash
set -euo pipefail

# Minimal production entrypoint for FastAPI (Uvicorn)
# Expects dependencies already installed in the image/runtime.

HOST="${BACKEND_HOST:-0.0.0.0}"
PORT="${BACKEND_PORT:-9301}"
WORKERS="${UVICORN_WORKERS:-1}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Prefer python -m uvicorn to avoid PATH issues
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

exec "$PY" -m uvicorn src.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WORKERS" \
  --log-level "$LOG_LEVEL" \
  --proxy-headers
