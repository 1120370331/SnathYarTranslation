#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

ENV_FILE="${ROOT_DIR}/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  echo "[env] Loaded .env"
else
  echo "[warn] No .env at repo root; using defaults/environment"
fi

# Allow FE_* overrides; fall back to global DEVBOX_* and REMOTE_DIR/DEPLOY_BRANCH
FE_HOST="${FE_DEVBOX_SSH_HOST:-${DEVBOX_SSH_HOST:-}}"
FE_PORT="${FE_DEVBOX_SSH_PORT:-${DEVBOX_SSH_PORT:-}}"
FE_USER="${FE_DEVBOX_SSH_USER:-${DEVBOX_SSH_USER:-}}"
FE_KEY="${FE_DEVBOX_SSH_KEY_PATH:-${DEVBOX_SSH_KEY_PATH:-}}"
FE_DIR="${FE_REMOTE_DIR:-${REMOTE_DIR:-}}"
FE_BRANCH="${FE_DEPLOY_BRANCH:-${DEPLOY_BRANCH:-devbox-deploy}}"

REQ=( FE_HOST FE_PORT FE_USER FE_KEY FE_DIR FE_BRANCH REMOTE_REPO_SSH )
for k in "${REQ[@]}"; do
  if [[ -z "${!k:-}" ]]; then
    echo "[error] Missing required var: $k in .env" >&2
    exit 1
  fi
done

SSH_OPTS=( -i "$FE_KEY" -p "$FE_PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null )
REMOTE="${FE_USER}@${FE_HOST}"

ssh "${SSH_OPTS[@]}" "$REMOTE" bash -lc "'
set -e
mkdir -p "$FE_DIR"
if [[ ! -d "$FE_DIR/.git" ]]; then
  echo "[remote] Cloning repo into $FE_DIR"
  git clone "$REMOTE_REPO_SSH" "$FE_DIR"
fi
cd "$FE_DIR"
git fetch --all --prune
git checkout "$FE_BRANCH" || git checkout -b "$FE_BRANCH"
git pull --ff-only || true
mkdir -p logs
chmod +x frontend/devbox-start.sh || true
'
"

if [[ -f "$ENV_FILE" ]]; then
  echo "[scp] Uploading .env to frontend container"
  scp -P "$FE_PORT" -i "$FE_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    "$ENV_FILE" "$REMOTE:$FE_DIR/.env"
fi

ssh "${SSH_OPTS[@]}" "$REMOTE" bash -lc "'
set -e
cd "$FE_DIR"
if pgrep -f "vite" >/dev/null 2>&1; then
  echo "[remote] Frontend already running; attempting to stop"
  pkill -f vite || true
  sleep 1
fi
nohup bash frontend/devbox-start.sh > logs/frontend.out 2>&1 & echo $! > logs/frontend.pid
echo "[remote] Frontend started (PID $(cat logs/frontend.pid))"
'
"

echo "[done] Frontend deployed to $REMOTE:$FE_DIR"
