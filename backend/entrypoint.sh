#!/usr/bin/env bash
set -euo pipefail

# Backend entrypoint (Python, no uvicorn CLI)
# - Runs the app with the selected Python interpreter
# - Logs to $LOG_DIR/backend.log (tee in foreground mode)
# - Optional BOOTSTRAP_DEPS=1 will create venv + install deps if missing

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
BOOTSTRAP_DEPS="${BOOTSTRAP_DEPS:-0}"

# Ensure Python can import the local 'src' package
export PYTHONPATH="${PYTHONPATH:-$SCRIPT_DIR}"

# Pick an interpreter that already has deps; optionally bootstrap deps if requested
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
      echo "[backend][entrypoint] Warning: venv present but missing deps (fastapi/uvicorn)."
      if [ "$BOOTSTRAP_DEPS" = "1" ]; then
        echo "[backend][entrypoint] Bootstrapping deps into existing venv..."
        bootstrap_runtime "$SCRIPT_DIR/venv/bin/python" || true
        if "$SCRIPT_DIR/venv/bin/python" - <<'PY' >/dev/null 2>&1
import importlib
for m in ("fastapi", "uvicorn"):
    importlib.import_module(m)
PY
        then
          PY="$SCRIPT_DIR/venv/bin/python"
          echo "[backend][entrypoint] Using venv after bootstrap: $PY"
          return
        fi
      fi
      echo "[backend][entrypoint] Falling back to system interpreter."
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
  if [ "$BOOTSTRAP_DEPS" = "1" ]; then
    echo "[backend][entrypoint] Attempting to create venv and install deps (BOOTSTRAP_DEPS=1)..." >&2
    if create_and_install_venv; then
      PY="$SCRIPT_DIR/venv/bin/python"
      echo "[backend][entrypoint] Using venv after bootstrap: $PY"
      return
    else
      echo "[backend][entrypoint] Failed to bootstrap dependencies." >&2
    fi
  fi
  echo "[backend][entrypoint] Install deps at build time: pip install -e . or pip install fastapi 'uvicorn[standard]'" >&2
  exit 1
}

# Create venv and install project deps
create_and_install_venv() {
  echo "[backend][entrypoint] Creating virtual environment under $SCRIPT_DIR/venv" >&2
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$SCRIPT_DIR/venv" || return 1
  elif command -v python >/dev/null 2>&1; then
    python -m venv "$SCRIPT_DIR/venv" || return 1
  else
    echo "[backend][entrypoint] No python interpreter available to create venv." >&2
    return 1
  fi
  VENV_PY="$SCRIPT_DIR/venv/bin/python"
  "$VENV_PY" -m ensurepip --upgrade >/dev/null 2>&1 || true
  "$VENV_PY" -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || return 1
  # Prefer editable install to resolve local package and deps
  echo "[backend][entrypoint] Installing project dependencies into venv..." >&2
  if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    "$VENV_PY" -m pip install -e . || return 1
  else
    # Fallback: explicit deps
    "$VENV_PY" -m pip install fastapi "uvicorn[standard]" || return 1
  fi
  # Verify imports
  "$VENV_PY" - <<'PY'
import importlib
import sys
for m in ("fastapi", "uvicorn"):
    importlib.import_module(m)
print("ok")
PY
}

# Attempt to (re)install into an existing interpreter
bootstrap_runtime() {
  local py="$1"
  echo "[backend][entrypoint] Installing project dependencies into $py ..." >&2
  "$py" -m ensurepip --upgrade >/dev/null 2>&1 || true
  "$py" -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || return 1
  if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    "$py" -m pip install -e . || return 1
  else
    "$py" -m pip install fastapi "uvicorn[standard]" || return 1
  fi
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
            "$PY" -m src.main
      ) 2>&1 | tee -a "$LOG_FILE"
      exit ${PIPESTATUS[0]:-0}
    else
      exec env BACKEND_HOST="$HOST" \
               BACKEND_PORT="$PORT" \
               UVICORN_WORKERS="$WORKERS" \
               LOG_LEVEL="$LOG_LEVEL" \
               RELOAD="$RELOAD" \
               "$PY" -m src.main
    fi
  else
    nohup env BACKEND_HOST="$HOST" \
             BACKEND_PORT="$PORT" \
             UVICORN_WORKERS="$WORKERS" \
             LOG_LEVEL="$LOG_LEVEL" \
             RELOAD="$RELOAD" \
             "$PY" -m src.main \
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
