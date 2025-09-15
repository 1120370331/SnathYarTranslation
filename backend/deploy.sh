#!/usr/bin/env bash
set -euo pipefail

# Ubuntu (CN) Docker deploy for backend — single, simple path
# - Installs Docker via apt
# - Configures Docker registry mirrors for China
# - Builds image and runs container

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-up}"

IMAGE_NAME="${IMAGE_NAME:-snathyar-backend:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-snathyar-backend}"
HOST_PORT="${HOST_PORT:-9301}"
CONTAINER_PORT=9301
HOST_LOG_DIR="${HOST_LOG_DIR:-/var/log/snathyar-backend}"
CSV_FILE="${CSV_FILE:-$ROOT_DIR/shasiyaer.csv}"
DB_FILE="${DB_FILE:-}"          # optional: host sqlite file path for persistence
DB_URL="${SHATHYAR_DB_URL:-}"   # optional: override DB URL
PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "[backend][deploy] 请使用 root 运行：sudo ./deploy.sh $MODE" >&2
    exit 1
  fi
}

install_docker_ubuntu() {
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi
  echo "[backend][deploy] 安装 Docker（apt）..."
  apt-get update -y
  apt-get install -y ca-certificates curl docker.io docker-compose-plugin
  systemctl enable --now docker || true
}

configure_cn_mirrors() {
  echo "[backend][deploy] 配置国内镜像源（/etc/docker/daemon.json）..."
  mkdir -p /etc/docker
  if [ -f /etc/docker/daemon.json ]; then
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak || true
  fi
  cat > /etc/docker/daemon.json <<JSON
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ]
}
JSON
  systemctl restart docker || true
}

docker_build() {
  echo "[backend][deploy] 构建镜像：$IMAGE_NAME（PIP镜像：$PIP_INDEX_URL）"
  docker build \
    --build-arg PIP_INDEX_URL="$PIP_INDEX_URL" \
    -t "$IMAGE_NAME" "$SCRIPT_DIR"
}

docker_run() {
  echo "[backend][deploy] 运行容器：$CONTAINER_NAME（端口 $HOST_PORT）"
  mkdir -p "$HOST_LOG_DIR"
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

  local run_flags=(
    --name "$CONTAINER_NAME"
    --restart unless-stopped
    -p "$HOST_PORT:$CONTAINER_PORT"
    -v "$HOST_LOG_DIR:/logs"
    -e BACKEND_HOST=0.0.0.0
    -e BACKEND_PORT="$CONTAINER_PORT"
    -e LOG_LEVEL=info
    -e UVICORN_WORKERS=1
    -e RELOAD=false
  )

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

  docker run -d "${run_flags[@]}" "$IMAGE_NAME"
}

docker_stop() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  echo "[backend][deploy] 已停止：$CONTAINER_NAME"
}

docker_logs() {
  docker logs -f "$CONTAINER_NAME"
}

docker_status() {
  docker ps --filter "name=$CONTAINER_NAME" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
}

case "$MODE" in
  up)
    require_root
    install_docker_ubuntu
    configure_cn_mirrors
    docker_build
    docker_run
    ;;
  down)
    require_root
    docker_stop
    ;;
  restart)
    require_root
    docker_stop
    docker_run
    ;;
  logs)
    docker_logs
    ;;
  status)
    docker_status
    ;;
  *)
    echo "用法: $0 [up|down|restart|logs|status]" >&2
    exit 1
    ;;
esac

