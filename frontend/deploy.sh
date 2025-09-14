#!/usr/bin/env bash
set -euo pipefail

# Frontend deploy script (install deps and build)
# - Installs npm deps via npm ci
# - Builds Vite app to ./dist

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if present (to use VITE_* variables at build time)
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/../.env}"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  echo "[frontend][deploy] Loaded env from $ENV_FILE"
fi

echo "[frontend][deploy] Installing dependencies (npm ci)"
npm ci

echo "[frontend][deploy] Building app (VITE_API_BASE_URL=${VITE_API_BASE_URL:-/api/v1})"
npm run build

echo "[frontend][deploy] Done. You can start with ./entrypoint.sh"

