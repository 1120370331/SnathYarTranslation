#!/usr/bin/env bash
set -euo pipefail

# Backend docker deploy (single method)
# This script auto-installs Docker if missing, builds the image, and runs the container.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-up}"

IMAGE_NAME="${IMAGE_NAME:-snathyar-backend:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-snathyar-backend}"
HOST_PORT="${HOST_PORT:-9301}"
CONTAINER_PORT=9301
HOST_LOG_DIR="${HOST_LOG_DIR:-$HOME/project/logs}"
CSV_FILE="${CSV_FILE:-$ROOT_DIR/shasiyaer.csv}"
DB_FILE="${DB_FILE:-}"          # optional host path for sqlite persistence
DB_URL="${SHATHYAR_DB_URL:-}"   # optional custom DB URL
DETACH="${DETACH:-1}"

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi
  echo "[backend][deploy] Docker not found. Installing..."
  if ! command -v curl >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
      apt-get update -y && apt-get install -y curl ca-certificates
    elif command -v yum >/dev/null 2>&1; then
      yum install -y curl ca-certificates || true
    elif command -v dnf >/dev/null 2>&1; then
      dnf install -y curl ca-certificates || true
    fi
  fi
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
  else
    echo "[backend][deploy] ERROR: curl unavailable; cannot install Docker automatically." >&2
    exit 1
  fi
  if command -v systemctl >/dev/null 2>&1; then
    systemctl enable --now docker || true
  elif command -v service >/dev/null 2>&1; then
    service docker start || true
  fi
}

ensure_docker() {
  install_docker
  if ! command -v docker >/dev/null 2>&1; then
    echo "[backend][deploy] ERROR: Docker installation failed or is unavailable." >&2
    exit 1
  fi
}

docker_build() {
  echo "[backend][deploy] Building image: $IMAGE_NAME"
  docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
}

docker_run() {
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

  mkdir -p "$HOST_LOG_DIR"
  run_flags+=( -v "$HOST_LOG_DIR:/logs" )

  if [ -f "$CSV_FILE" ]; then
    run_flags+=( -v "$CSV_FILE:/app/shasiyaer.csv:ro" )
  fi

  if [ -n "$DB_FILE" ]; then
    mkdir -p "$(dirname "$DB_FILE")"
    run_flags+=( -e SHATHYAR_DB_URL="${DB_URL:-sqlite:////data/shathyar.db}" )
    run_flags+=( -v "$DB_FILE:/data/shathyar.db" )
  elif [ -n "$DB_URL" ]; then
    run_flags+=( -e SHATHYAR_DB_URL="$DB_URL" )
  fi

  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  echo "[backend][deploy] Starting container: $CONTAINER_NAME -> port $HOST_PORT"
  if [ "$DETACH" = "1" ]; then
    docker run -d "${run_flags[@]}" "$IMAGE_NAME"
  else
    docker run -it --rm "${run_flags[@]}" "$IMAGE_NAME"
  fi
}

docker_stop() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  echo "[backend][deploy] Stopped container: $CONTAINER_NAME"
}

docker_logs() {
  if [ "${1:-}" = "-f" ] || [ "${1:-}" = "--follow" ]; then
    docker logs -f "$CONTAINER_NAME"
  else
    docker logs --tail 200 "$CONTAINER_NAME"
  fi
}

case "$MODE" in
  up)
    ensure_docker
    docker_build
    docker_run
    ;;
  down)
    ensure_docker
    docker_stop
    ;;
  logs)
    ensure_docker
    shift || true
    docker_logs "${1:-}"
    ;;
  restart)
    ensure_docker
    docker_stop
    docker_run
    ;;
  *)
    echo "Usage: $0 [up|down|logs|restart]" >&2
    exit 1
    ;;
esac

