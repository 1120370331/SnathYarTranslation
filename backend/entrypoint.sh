#!/usr/bin/env bash
set -euo pipefail

# Backend entrypoint
# - Starts Uvicorn
# - Writes logs to $LOG_DIR/backend.log
# - Tails the log to foreground for easy observation in container

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if present (prefer local backend/.env, then repo root ../.env)
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ] && [ -f "$SCRIPT_DIR/../.env" ]; then
  ENV_FILE="$SCRIPT_DIR/../.env"
fi
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  echo "[backend][entrypoint] Loaded env from $(basename "$ENV_FILE")"
fi

HOST="${BACKEND_HOST:-0.0.0.0}"
PORT="${BACKEND_PORT:-9301}"
WORKERS="${UVICORN_WORKERS:-1}"
LOG_LEVEL="${LOG_LEVEL:-info}"

LOG_DIR="${LOG_DIR:-$HOME/project/logs}"
[ -d "$LOG_DIR" ] || mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/backend.log"
PID_FILE="$LOG_DIR/backend.pid"

PY=python3
if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
  PY="$SCRIPT_DIR/venv/bin/python"
elif ! command -v python3 >/dev/null 2>&1; then
  PY=python
fi

start() {
  echo "[backend][entrypoint] Starting Uvicorn on ${HOST}:${PORT} (workers=${WORKERS})"
  nohup "$PY" -m uvicorn src.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level "$LOG_LEVEL" \
    --proxy-headers \
    >>"$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "[backend][entrypoint] PID=$(cat "$PID_FILE"), log=$LOG_FILE"
}

cleanup() {
  echo "[backend][entrypoint] Stopping..."
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
