#!/usr/bin/env bash
set -euo pipefail

# Render start script for the backend FastAPI service
# - Uses $PORT provided by Render (defaults to 8000 locally)
# - Loads env vars from repo root .env and backend/.env if present
# - Serves FastAPI via uvicorn

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Export env from .env files if they exist
set +u
if [ -f "../.env" ]; then
  # shellcheck disable=SC2046
  set -a; . ../.env; set +a
fi
if [ -f ".env" ]; then
  # shellcheck disable=SC2046
  set -a; . ./.env; set +a
fi
set -u

PORT="${PORT:-8000}"
HOST="${BACKEND_HOST:-0.0.0.0}"

echo "🔮 Starting Shathyar Translator (FastAPI)"
echo "📍 Listening on http://${HOST}:${PORT}"

exec python -m uvicorn src.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips "*"

