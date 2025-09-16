#!/usr/bin/env bash
set -euo pipefail

# Frontend entrypoint for prebuilt Vite React app
# - Serves ./dist via server/index.js
# - Writes logs to $LOG_DIR/frontend.log and tails them

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"

PORT="${PORT:-${FRONTEND_PORT:-1573}}"
HOST="${HOST:-${FRONTEND_HOST:-0.0.0.0}}"

LOG_DIR="${LOG_DIR:-$HOME/project/logs}"
[ -d "$LOG_DIR" ] || mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/frontend.log"
PID_FILE="$LOG_DIR/frontend.pid"

DIST_DIR="$APP_DIR/dist"
if [ ! -d "$DIST_DIR" ]; then
  echo "[frontend][entrypoint][error] dist/ not found. Build first: npm ci && npm run build" >&2
  exit 1
fi

start() {
  echo "[frontend][entrypoint] Starting static server on ${HOST}:${PORT}"
  PORT="$PORT" HOST="$HOST" nohup node "$APP_DIR/server/index.js" >>"$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "[frontend][entrypoint] PID=$(cat "$PID_FILE"), log=$LOG_FILE"
}

cleanup() {
  echo "[frontend][entrypoint] Stopping..."
  if [ -f "$PID_FILE" ]; then
    kill "$(cat "$PID_FILE")" 2>/dev/null || true
    rm -f "$PID_FILE"
  fi
  exit 0
}

trap cleanup INT TERM

start
tail -n +1 -F "$LOG_FILE" &
TAIL_PID=$!
wait "$TAIL_PID"
