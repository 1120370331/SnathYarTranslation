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
  if command -v apt-get >/dev/null 2>&1; then
    echo "[backend][deploy] Installing via apt-get (docker.io)"
    DEBIAN_FRONTEND=noninteractive apt-get update -y || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io || true
  elif command -v yum >/dev/null 2>&1; then
    echo "[backend][deploy] Installing via yum"
    if command -v amazon-linux-extras >/dev/null 2>&1; then
      amazon-linux-extras install -y docker || true
    else
      yum install -y docker || yum install -y docker-engine || true
    fi
  elif command -v dnf >/dev/null 2>&1; then
    echo "[backend][deploy] Installing via dnf"
    dnf install -y docker || true
  elif command -v zypper >/dev/null 2>&1; then
    echo "[backend][deploy] Installing via zypper"
    zypper -n in docker || true
  fi
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
        echo "[backend][deploy] Using CN mirror script (DaoCloud)"
        curl -fsSL https://get.daocloud.io/docker | sh || true
      else
        curl -fsSL https://get.docker.com | sh || true
      fi
    fi
  fi
  if command -v systemctl >/dev/null 2>&1; then
    systemctl enable --now docker || true
  elif command -v service >/dev/null 2>&1; then
    service docker start || true
  fi
}

# Configure Docker registry mirrors for China if requested
configure_docker_mirrors() {
  local enable_cn="${CN_MIRROR:-}"
  if [ -z "$enable_cn" ] && [ "${DOCKER_INSTALL_MIRROR:-}" = "cn" ]; then
    enable_cn=1
  fi
  if [ -z "$enable_cn" ]; then
    return 0
  fi

  local mirrors_csv
  mirrors_csv="${DOCKER_REGISTRY_MIRRORS:-https://docker.mirrors.ustc.edu.cn,https://hub-mirror.c.163.com,https://mirror.ccs.tencentyun.com,https://registry.docker-cn.com}"
  # Convert CSV to JSON array entries
  IFS=',' read -r -a arr <<< "$mirrors_csv"
  local json_list=""
  for m in "${arr[@]}"; do
    m_trimmed="${m//\ /}"
    if [ -n "$m_trimmed" ]; then
      if [ -n "$json_list" ]; then json_list+=" , "; fi
      json_list+="\"$m_trimmed\""
    fi
  done

  echo "[backend][deploy] Configuring Docker registry mirrors: [$mirrors_csv]"
  mkdir -p /etc/docker
  if [ -f /etc/docker/daemon.json ]; then
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak || true
  fi
  cat > /etc/docker/daemon.json <<JSON
{
  "registry-mirrors": [ $json_list ]
}
JSON

  if command -v systemctl >/dev/null 2>&1; then
    systemctl restart docker || true
  elif command -v service >/dev/null 2>&1; then
    service docker restart || true
  fi
}

ensure_docker() {
  install_docker
  if ! command -v docker >/dev/null 2>&1; then
    echo "[backend][deploy] ERROR: Docker installation failed or is unavailable." >&2
    exit 1
  fi
  configure_docker_mirrors || true
  ensure_docker_daemon || true
}

# Ensure docker daemon is running in environments without systemd
ensure_docker_daemon() {
  if docker info >/dev/null 2>&1; then
    return 0
  fi
  echo "[backend][deploy] Docker daemon not running. Attempting to start..."
  if command -v systemctl >/dev/null 2>&1; then
    systemctl start docker || true
  elif command -v service >/dev/null 2>&1; then
    service docker start || true
  fi
  # If still not running, try launching dockerd directly (no systemd)
  if ! docker info >/dev/null 2>&1; then
    echo "[backend][deploy] Launching dockerd (no systemd). Using storage-driver=vfs as fallback."
    nohup dockerd --host=unix:///var/run/docker.sock --storage-driver=vfs >>/var/log/dockerd.log 2>&1 &
  fi
  # Wait for daemon to be ready
  for i in $(seq 1 20); do
    if docker info >/dev/null 2>&1; then
      echo "[backend][deploy] Docker daemon is up."
      return 0
    fi
    sleep 1
  done
  echo "[backend][deploy] WARN: Could not confirm docker daemon is running. 'docker build' may fail." >&2
  return 1
}

docker_build() {
  echo "[backend][deploy] Building image: $IMAGE_NAME"
  local build_args=()
  if [ -n "${PIP_INDEX_URL:-}" ]; then
    build_args+=( --build-arg PIP_INDEX_URL="$PIP_INDEX_URL" )
  elif [ -n "${CN_MIRROR:-}" ] || [ "${DOCKER_INSTALL_MIRROR:-}" = "cn" ]; then
    build_args+=( --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple )
  fi
  if [ -n "${PIP_EXTRA_INDEX_URL:-}" ]; then
    build_args+=( --build-arg PIP_EXTRA_INDEX_URL="$PIP_EXTRA_INDEX_URL" )
  fi
  docker build "${build_args[@]}" -t "$IMAGE_NAME" "$SCRIPT_DIR"
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

