#!/usr/bin/env bash
set -euo pipefail

# Devbox frontend startup script
# - Reads ../.env (or ./.env) and exports variables
# - Installs npm dependencies
# - Starts Vite dev server binding to configured host/port

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR/frontend"

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

if ! command -v node >/dev/null 2>&1; then
  echo "[error] Node.js not found (require v18+)." >&2
  exit 1
fi

if [[ ! -d node_modules ]]; then
  echo "[setup] Installing Node dependencies"
  npm install --silent
fi

HOST="${FRONTEND_HOST:-0.0.0.0}"
PORT="${FRONTEND_PORT:-5173}"

EXTRA_OPTS=( )
if [[ -n "${VITE_BACKEND_PROXY_TARGET:-}" ]]; then
  echo "[info] Proxy target: ${VITE_BACKEND_PROXY_TARGET}"
fi

echo "[start] Starting Vite on ${HOST}:${PORT}"
exec npm run dev -- --host "$HOST" --port "$PORT"

