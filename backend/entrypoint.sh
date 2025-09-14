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

# Ensure runtime has uvicorn available
ensure_runtime() {
  # Prefer project venv
  if [ ! -x "$SCRIPT_DIR/venv/bin/python" ]; then
    # Try to create venv (may fail if python3-venv is missing)
    command -v python3 >/dev/null 2>&1 || true
    python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    python3 -m venv "$SCRIPT_DIR/venv" >/dev/null 2>&1 || true
  fi

  if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
    # Install deps into venv if uvicorn missing
    if ! "$SCRIPT_DIR/venv/bin/python" -c 'import uvicorn' >/dev/null 2>&1; then
      echo "[backend][entrypoint] Installing deps into venv"
      "$SCRIPT_DIR/venv/bin/python" -m pip install -U pip >/dev/null 2>&1 || true
      "$SCRIPT_DIR/venv/bin/python" -m pip install -e . >/dev/null 2>&1 || true
    fi
    PY="$SCRIPT_DIR/venv/bin/python"
    return
  fi

  # Fallback: break PEP 668 for system/user install as last resort
  if ! python3 -c 'import uvicorn' >/dev/null 2>&1; then
    echo "[backend][entrypoint] Fallback installing deps to system/user site (PEP 668 override)"
    PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m pip install -U pip setuptools wheel >/dev/null 2>&1 || true
    PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m pip install -e . >/dev/null 2>&1 || true
  fi
  PY=python3
}

PY=python3
ensure_runtime

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
