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

# Allow BE_* overrides; fall back to global DEVBOX_* and REMOTE_DIR/DEPLOY_BRANCH
BE_HOST="${BE_DEVBOX_SSH_HOST:-${DEVBOX_SSH_HOST:-}}"
BE_PORT="${BE_DEVBOX_SSH_PORT:-${DEVBOX_SSH_PORT:-}}"
BE_USER="${BE_DEVBOX_SSH_USER:-${DEVBOX_SSH_USER:-}}"
BE_KEY="${BE_DEVBOX_SSH_KEY_PATH:-${DEVBOX_SSH_KEY_PATH:-}}"
BE_DIR="${BE_REMOTE_DIR:-${REMOTE_DIR:-}}"
BE_BRANCH="${BE_DEPLOY_BRANCH:-${DEPLOY_BRANCH:-devbox-deploy}}"

REQ=( BE_HOST BE_PORT BE_USER BE_KEY BE_DIR BE_BRANCH REMOTE_REPO_SSH )
for k in "${REQ[@]}"; do
  if [[ -z "${!k:-}" ]]; then
    echo "[error] Missing required var: $k in .env" >&2
    exit 1
  fi
done

SSH_OPTS=( -i "$BE_KEY" -p "$BE_PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null )
REMOTE="${BE_USER}@${BE_HOST}"

ssh "${SSH_OPTS[@]}" "$REMOTE" bash -lc "'
set -e
mkdir -p "$BE_DIR"
if [[ ! -d "$BE_DIR/.git" ]]; then
  echo "[remote] Cloning repo into $BE_DIR"
  git clone "$REMOTE_REPO_SSH" "$BE_DIR"
fi
cd "$BE_DIR"
git fetch --all --prune
git checkout "$BE_BRANCH" || git checkout -b "$BE_BRANCH"
git pull --ff-only || true
mkdir -p logs
chmod +x backend/devbox-start.sh || true
'
"

if [[ -f "$ENV_FILE" ]]; then
  echo "[scp] Uploading .env to backend container"
  scp -P "$BE_PORT" -i "$BE_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    "$ENV_FILE" "$REMOTE:$BE_DIR/.env"
fi

ssh "${SSH_OPTS[@]}" "$REMOTE" bash -lc "'
set -e
cd "$BE_DIR"
if pgrep -f "uvicorn .*src.main:app" >/dev/null 2>&1; then
  echo "[remote] Backend already running; attempting to stop"
  pkill -f "uvicorn .*src.main:app" || true
  sleep 1
fi
nohup bash backend/devbox-start.sh > logs/backend.out 2>&1 & echo $! > logs/backend.pid
echo "[remote] Backend started (PID $(cat logs/backend.pid))"
'
"

echo "[done] Backend deployed to $REMOTE:$BE_DIR"

