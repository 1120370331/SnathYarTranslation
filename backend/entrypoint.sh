#!/usr/bin/env bash
set -euo pipefail

# Backend docker launcher (host-side only)
# Single method: build and run Docker container

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="${IMAGE_NAME:-snathyar-backend:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-snathyar-backend}"
HOST_PORT="${BACKEND_PORT:-9301}"
CONTAINER_PORT=9301
BACKEND_HOST_ENV="${BACKEND_HOST:-0.0.0.0}"
LOG_DIR_HOST="${LOG_DIR:-$HOME/project/logs}"
CSV_FILE="${CSV_FILE:-$ROOT_DIR/shasiyaer.csv}"
DB_FILE="${DB_FILE:-}"
DB_URL="${SHATHYAR_DB_URL:-}"
DETACH="${DETACH:-1}"

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi
  echo "[backend][entrypoint] Docker not found. Installing..."

  # 1) Try OS package managers first
  if command -v apt-get >/dev/null 2>&1; then
    echo "[backend][entrypoint] Installing via apt-get (docker.io)"
    DEBIAN_FRONTEND=noninteractive apt-get update -y || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io || true
  elif command -v yum >/dev/null 2>&1; then
    echo "[backend][entrypoint] Installing via yum"
    if command -v amazon-linux-extras >/dev/null 2>&1; then
      amazon-linux-extras install -y docker || true
    else
      yum install -y docker || yum install -y docker-engine || true
    fi
  elif command -v dnf >/dev/null 2>&1; then
    echo "[backend][entrypoint] Installing via dnf"
    dnf install -y docker || true
  elif command -v zypper >/dev/null 2>&1; then
    echo "[backend][entrypoint] Installing via zypper"
    zypper -n in docker || true
  fi

  # 2) Fallback to official (or CN mirror) install script if still missing
  if ! command -v docker >/dev/null 2>&1; then
    if ! command -v curl >/dev/null 2>&1; then
      if command -v apt-get >/dev/null 2>&1; then
        apt-get update -y && apt-get install -y curl ca-certificates || true
      elif command -v yum >/dev/null 2>&1; then
        yum install -y curl ca-certificates || true
      elif command -v dnf >/dev/null 2>&1; then
        dnf install -y curl ca-certificates || true
      fi
    fi
    if command -v curl >/dev/null 2>&1; then
      if [ "${DOCKER_INSTALL_MIRROR:-}" = "cn" ]; then
        echo "[backend][entrypoint] Using CN mirror script (DaoCloud)"
        curl -fsSL https://get.daocloud.io/docker | sh || true
      else
        curl -fsSL https://get.docker.com | sh || true
      fi
    fi
  fi

  # 3) Start Docker service if present
  if command -v systemctl >/dev/null 2>&1; then
    systemctl enable --now docker || true
  elif command -v service >/dev/null 2>&1; then
    service docker start || true
  fi
}

ensure_docker() {
  install_docker
  if ! command -v docker >/dev/null 2>&1; then
    echo "[backend][entrypoint] ERROR: Docker installation failed or is unavailable." >&2
    exit 1
  fi
}

docker_build() {
  echo "[backend][entrypoint] Building image: $IMAGE_NAME"
  docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
}

docker_run() {
  local run_flags=(
    --name "$CONTAINER_NAME"
    --restart unless-stopped
    -p "$HOST_PORT:$CONTAINER_PORT"
    -e BACKEND_HOST="$BACKEND_HOST_ENV"
    -e BACKEND_PORT="$CONTAINER_PORT"
    -e UVICORN_WORKERS=1
    -e LOG_LEVEL=info
    -e RELOAD=false
  )
  mkdir -p "$LOG_DIR_HOST"
  run_flags+=( -v "$LOG_DIR_HOST:/logs" )
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
  echo "[backend][entrypoint] Starting container: $CONTAINER_NAME (host:$HOST_PORT -> container:$CONTAINER_PORT)"
  if [ "$DETACH" = "1" ]; then
    docker run -d "${run_flags[@]}" "$IMAGE_NAME"
  else
    docker run -it --rm "${run_flags[@]}" "$IMAGE_NAME"
  fi
}

ensure_docker
docker_build
docker_run

echo "[backend][entrypoint] Ready. Logs: docker logs -f $CONTAINER_NAME"
