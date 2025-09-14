#!/usr/bin/env bash
set -euo pipefail

# Devbox remote deploy helper
# - SSH into remote and clone/update repo
# - Push local .env to remote
# - Start backend and frontend using their devbox-start.sh scripts (nohup)

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

REQUIRED=( DEVBOX_SSH_HOST DEVBOX_SSH_PORT DEVBOX_SSH_USER DEVBOX_SSH_KEY_PATH REMOTE_REPO_SSH REMOTE_DIR DEPLOY_BRANCH )
for k in "${REQUIRED[@]}"; do
  if [[ -z "${!k:-}" ]]; then
    echo "[error] Missing required var: $k in .env" >&2
    exit 1
  fi
done

SSH_OPTS=(
  -i "$DEVBOX_SSH_KEY_PATH"
  -p "$DEVBOX_SSH_PORT"
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
)

REMOTE="${DEVBOX_SSH_USER}@${DEVBOX_SSH_HOST}"

echo "[ssh] Connecting to $REMOTE"

# Ensure remote base dir exists and repo is present
ssh "${SSH_OPTS[@]}" "$REMOTE" bash -lc "'
set -e
mkdir -p "$REMOTE_DIR"
if [[ ! -d "$REMOTE_DIR/.git" ]]; then
  echo "[remote] Cloning repo into $REMOTE_DIR"
  if git ls-remote "$REMOTE_REPO_SSH" >/dev/null 2>&1; then
    git clone "$REMOTE_REPO_SSH" "$REMOTE_DIR"
  elif [[ -n "$REMOTE_REPO_HTTPS" ]] && git ls-remote "$REMOTE_REPO_HTTPS" >/dev/null 2>&1; then
    git clone "$REMOTE_REPO_HTTPS" "$REMOTE_DIR"
  else
    echo "[error] Cannot access repo via SSH or HTTPS" >&2
    exit 1
  fi
fi
cd "$REMOTE_DIR"
git fetch --all --prune
git checkout "$DEPLOY_BRANCH" || git checkout -b "$DEPLOY_BRANCH"
git pull --ff-only || true
mkdir -p logs
chmod +x backend/devbox-start.sh frontend/devbox-start.sh || true
# Normalize line endings in case scripts were edited on Windows
if command -v dos2unix >/dev/null 2>&1; then
  dos2unix backend/devbox-start.sh frontend/devbox-start.sh 2>/dev/null || true
else
  sed -i 's/\r$//' backend/devbox-start.sh 2>/dev/null || true
  sed -i 's/\r$//' frontend/devbox-start.sh 2>/dev/null || true
fi
'"

# Sync local .env to remote (contains secrets, kept out of Git)
if [[ -f "$ENV_FILE" ]]; then
  echo "[scp] Uploading .env to remote"
  scp -P "$DEVBOX_SSH_PORT" -i "$DEVBOX_SSH_KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    "$ENV_FILE" "$REMOTE:$REMOTE_DIR/.env"
fi

# Start backend and frontend with nohup
ssh "${SSH_OPTS[@]}" "$REMOTE" bash -lc "'
set -e
cd "$REMOTE_DIR"

# Backend
if pgrep -f "uvicorn .*src.main:app" >/dev/null 2>&1; then
  echo "[remote] Backend already running; attempting to stop"
  pkill -f "uvicorn .*src.main:app" || true
  sleep 1
fi
nohup bash backend/devbox-start.sh > logs/backend.out 2>&1 & echo $! > logs/backend.pid
echo "[remote] Backend started (PID $(cat logs/backend.pid))"

# Frontend
if pgrep -f "vite" >/dev/null 2>&1; then
  echo "[remote] Frontend already running; attempting to stop"
  pkill -f vite || true
  sleep 1
fi
nohup bash frontend/devbox-start.sh > logs/frontend.out 2>&1 & echo $! > logs/frontend.pid
echo "[remote] Frontend started (PID $(cat logs/frontend.pid))"
'
"

echo "[done] Remote deploy triggered. Tail logs with:"
echo "       ssh ${DEVBOX_SSH_USER}@${DEVBOX_SSH_HOST} -p ${DEVBOX_SSH_PORT} -i ${DEVBOX_SSH_KEY_PATH} 'tail -f ${REMOTE_DIR}/logs/*.out'"
