#!/usr/bin/env bash
set -euo pipefail

# Minimal production entrypoint for prebuilt Vite React app
# Serves ./dist via a lightweight Node static server (no external deps)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"

PORT="${PORT:-${FRONTEND_PORT:-1573}}"
HOST="${HOST:-${FRONTEND_HOST:-0.0.0.0}}"

DIST_DIR="$APP_DIR/dist"
if [ ! -d "$DIST_DIR" ]; then
  echo "[error] dist/ not found. Build the app first (npm ci && npm run build)." >&2
  exit 1
fi

exec node "$APP_DIR/server/index.js"

