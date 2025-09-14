#!/usr/bin/env bash
set -euo pipefail

# Backend deployment helper
# Modes:
#   venv            - Install deps into local venv (legacy/local dev)
#   docker-build    - Build backend image
#   docker-run      - Run backend container
#   docker-stop     - Stop and remove container
#   docker-restart  - Restart container
#   docker-logs     - Tail container logs
#   compose-up      - docker compose up -d (uses repo root compose)
#   compose-down    - docker compose down

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-}"

# Defaults for Docker
IMAGE_NAME="${IMAGE_NAME:-snathyar-backend:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-snathyar-backend}"
HOST_PORT="${HOST_PORT:-9301}"
CONTAINER_PORT=9301
HOST_LOG_DIR="${HOST_LOG_DIR:-$HOME/project/logs}"
DETACH="${DETACH:-1}"
CSV_FILE="${CSV_FILE:-$ROOT_DIR/shasiyaer.csv}"
DB_FILE="${DB_FILE:-}"                 # optional: host path to persist DB
DB_URL="${SHATHYAR_DB_URL:-}"          # optional: explicitly set DB URL

ensure_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[backend][deploy] ERROR: docker not found on PATH" >&2
    exit 1
  fi
}

docker_build() {
  ensure_docker
  echo "[backend][deploy] Building image: $IMAGE_NAME"
  docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
}

docker_run() {
  ensure_docker
  local run_flags=(
    --name "$CONTAINER_NAME"
    --restart unless-stopped
    -p "$HOST_PORT:$CONTAINER_PORT"
    -e BACKEND_HOST=0.0.0.0
    -e BACKEND_PORT="$CONTAINER_PORT"
    -e UVICORN_WORKERS=1
    -e LOG_LEVEL=info
    -e RELOAD=false
  )

  # Logs volume
  mkdir -p "$HOST_LOG_DIR"
  run_flags+=( -v "$HOST_LOG_DIR:/logs" )

  # Optional CSV mount if exists
  if [ -f "$CSV_FILE" ]; then
    run_flags+=( -v "$CSV_FILE:/app/shasiyaer.csv:ro" )
  fi

  # Optional DB persistence
  if [ -n "$DB_FILE" ]; then
    mkdir -p "$(dirname "$DB_FILE")"
    run_flags+=( -e SHATHYAR_DB_URL="${DB_URL:-sqlite:////data/shathyar.db}" )
    run_flags+=( -v "$DB_FILE:/data/shathyar.db" )
  elif [ -n "$DB_URL" ]; then
    run_flags+=( -e SHATHYAR_DB_URL="$DB_URL" )
  fi

  # Remove existing container
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

  echo "[backend][deploy] Starting container: $CONTAINER_NAME -> port $HOST_PORT"
  if [ "$DETACH" = "1" ]; then
    docker run -d "${run_flags[@]}" "$IMAGE_NAME"
  else
    docker run -it --rm "${run_flags[@]}" "$IMAGE_NAME"
  fi
}

docker_stop() {
  ensure_docker
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  echo "[backend][deploy] Stopped container: $CONTAINER_NAME"
}

docker_restart() {
  ensure_docker
  docker_stop
  docker_run
}

docker_logs() {
  ensure_docker
  if [ "${1:-}" = "-f" ] || [ "${1:-}" = "--follow" ]; then
    docker logs -f "$CONTAINER_NAME"
  else
    docker logs --tail 200 "$CONTAINER_NAME"
  fi
}

compose_up() {
  ensure_docker
  local compose_file="$ROOT_DIR/docker-compose.yml"
  if [ ! -f "$compose_file" ]; then
    echo "[backend][deploy] ERROR: $compose_file not found" >&2
    exit 1
  fi
  echo "[backend][deploy] docker compose up -d (backend)"
  (cd "$ROOT_DIR" && docker compose up -d --build backend)
}

compose_down() {
  ensure_docker
  local compose_file="$ROOT_DIR/docker-compose.yml"
  if [ ! -f "$compose_file" ]; then
    echo "[backend][deploy] ERROR: $compose_file not found" >&2
    exit 1
  fi
  echo "[backend][deploy] docker compose down"
  (cd "$ROOT_DIR" && docker compose down)
}

venv_install() {
  local PY=python3
  command -v python3 >/dev/null 2>&1 || PY=python
  echo "[backend][deploy] Using Python: $PY"

  local USE_VENV=1
  if [ ! -d venv ]; then
    echo "[backend][deploy] Creating venv"
    if ! "$PY" -m venv venv 2>/dev/null; then
      echo "[backend][deploy][warn] python -m venv not available. Falling back to --user installs (PEP 668 safe)."
      USE_VENV=0
    fi
  fi

  if [ "$USE_VENV" = "1" ] && [ -x venv/bin/python ]; then
    local VPY="$(pwd)/venv/bin/python"
    echo "[backend][deploy] Upgrading pip and installing project deps (venv)"
    "$VPY" -m pip install -U pip
    "$VPY" -m pip install -e .
    echo "[backend][deploy] Done. You can start with ./entrypoint.sh"
  else
    echo "[backend][deploy] Installing to user site-packages (~/.local) with PEP 668 override"
    "$PY" -m ensurepip --upgrade >/dev/null 2>&1 || true
    PIP_BREAK_SYSTEM_PACKAGES=1 "$PY" -m pip install --user -U pip setuptools wheel || \
      "$PY" -m pip install --user -U pip setuptools wheel --break-system-packages || true
    PIP_BREAK_SYSTEM_PACKAGES=1 "$PY" -m pip install --user -e . || \
      "$PY" -m pip install --user -e . --break-system-packages
    echo "[backend][deploy] Done (user mode)."
  fi
}

usage() {
  cat <<USAGE
Usage: $0 <mode>

Modes:
  venv             Install deps into local venv (for local dev)
  docker-build     Build backend image (IMAGE_NAME=$IMAGE_NAME)
  docker-run       Run container (CONTAINER_NAME=$CONTAINER_NAME, HOST_PORT=$HOST_PORT)
  docker-stop      Stop and remove container
  docker-restart   Restart container
  docker-logs      Show logs (add -f to follow)
  compose-up       docker compose up -d --build backend
  compose-down     docker compose down

Important env vars:
  IMAGE_NAME, CONTAINER_NAME, HOST_PORT, HOST_LOG_DIR, DETACH
  DB_FILE (host path to persist sqlite), SHATHYAR_DB_URL (custom DB URL)
  CSV_FILE (host path to shasiyaer.csv)
USAGE
}

case "$MODE" in
  venv)           venv_install ;;
  docker-build)   docker_build ;;
  docker-run)     docker_run ;;
  docker-stop)    docker_stop ;;
  docker-restart) docker_restart ;;
  docker-logs)    shift || true; docker_logs "${1:-}" ;;
  compose-up)     compose_up ;;
  compose-down)   compose_down ;;
  "")            usage; exit 1 ;;
  *)              echo "[backend][deploy] Unknown mode: $MODE" >&2; usage; exit 1 ;;
esac
