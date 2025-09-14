#!/usr/bin/env bash
set -euo pipefail

# Devbox backend startup script
# - Reads ../../.env (or ./.env) and exports variables
# - Creates venv, installs dependencies
# - Starts uvicorn with configured host/port

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR/backend"

ENV_FILE="${ROOT_DIR}/.env"
[[ -f ./.env ]] && ENV_FILE="./.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  echo "[env] Loaded $(basename "$ENV_FILE")"
else
  echo "[env] No .env found; proceeding with defaults"
fi

PYTHON_BIN="python3"
command -v python3 >/dev/null 2>&1 || PYTHON_BIN="python"

if [[ ! -d venv ]]; then
  echo "[setup] Creating Python virtual environment"
  "$PYTHON_BIN" -m venv venv
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

echo "[setup] Installing backend dependencies"
pip install --upgrade pip >/dev/null
pip install -e . >/dev/null

HOST="${BACKEND_HOST:-0.0.0.0}"
PORT="${BACKEND_PORT:-8000}"

echo "[start] Starting backend on ${HOST}:${PORT}"
exec python -m uvicorn src.main:app --host "$HOST" --port "$PORT"

