#!/usr/bin/env bash
set -euo pipefail

# Backend entrypoint (Python, no uvicorn CLI)
# - Runs the app with the selected Python interpreter
# - Logs to $LOG_DIR/backend.log (tee in foreground mode)

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
RELOAD="${RELOAD:-false}"
LOG_DIR="${LOG_DIR:-$HOME/project/logs}"
[ -d "$LOG_DIR" ] || mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/backend.log"
PID_FILE="$LOG_DIR/backend.pid"
FOREGROUND="${FOREGROUND:-1}"

# Pick an interpreter that already has deps; do not install at runtime
ensure_runtime() {
  if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
    if "$SCRIPT_DIR/venv/bin/python" - <<'PY' >/dev/null 2>&1
import importlib
for m in ("fastapi", "uvicorn"):
    importlib.import_module(m)
PY
    then
      PY="$SCRIPT_DIR/venv/bin/python"
      echo "[backend][entrypoint] Using venv interpreter: $PY"
      return
    else
      echo "[backend][entrypoint] Warning: venv present but missing deps (fastapi/uvicorn); falling back."
    fi
  fi

  if command -v python3 >/dev/null 2>&1 && \
     python3 - <<'PY' >/dev/null 2>&1
import importlib
for m in ("fastapi", "uvicorn"):
    importlib.import_module(m)
PY
  then
    PY=python3
    echo "[backend][entrypoint] Using system interpreter: $PY"
    return
  fi

  if command -v python >/dev/null 2>&1 && \
     python - <<'PY' >/dev/null 2>&1
import importlib
for m in ("fastapi", "uvicorn"):
    importlib.import_module(m)
PY
  then
    PY=python
    echo "[backend][entrypoint] Using interpreter: $PY"
    return
  fi

  echo "[backend][entrypoint] ERROR: Python environment lacks required packages: fastapi and/or uvicorn." >&2
  echo "[backend][entrypoint] Install deps at build time: pip install -e .[dev] or pip install fastapi 'uvicorn[standard]'" >&2
  exit 1
}

PY=python3
ensure_runtime

start() {
  echo "[backend][entrypoint] Starting FastAPI via python on ${HOST}:${PORT} (workers=${WORKERS}, reload=${RELOAD}, fg=${FOREGROUND})"
  if [ "$FOREGROUND" = "1" ]; then
    if command -v tee >/dev/null 2>&1; then
      echo "[backend][entrypoint] Foreground with tee -> $LOG_FILE"
      (
        env BACKEND_HOST="$HOST" \
            BACKEND_PORT="$PORT" \
            UVICORN_WORKERS="$WORKERS" \
            LOG_LEVEL="$LOG_LEVEL" \
            RELOAD="$RELOAD" \
            "$PY" "$SCRIPT_DIR/src/main.py"
      ) 2>&1 | tee -a "$LOG_FILE"
      exit ${PIPESTATUS[0]:-0}
    else
      exec env BACKEND_HOST="$HOST" \
               BACKEND_PORT="$PORT" \
               UVICORN_WORKERS="$WORKERS" \
               LOG_LEVEL="$LOG_LEVEL" \
               RELOAD="$RELOAD" \
               "$PY" "$SCRIPT_DIR/src/main.py"
    fi
  else
    nohup env BACKEND_HOST="$HOST" \
             BACKEND_PORT="$PORT" \
             UVICORN_WORKERS="$WORKERS" \
             LOG_LEVEL="$LOG_LEVEL" \
             RELOAD="$RELOAD" \
             "$PY" "$SCRIPT_DIR/src/main.py" \
             >>"$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "[backend][entrypoint] PID=$(cat "$PID_FILE"), log=$LOG_FILE"
  fi
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

if [ "$FOREGROUND" != "1" ]; then
  tail -n +1 -F "$LOG_FILE" &
  TAIL_PID=$!
  wait "$TAIL_PID"
fi
