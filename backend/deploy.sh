#!/usr/bin/env bash
set -euo pipefail

# Backend deploy script (install runtime deps inside container)
# - Creates venv under ./venv
# - Installs project in editable mode (includes FastAPI/Uvicorn deps)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

echo "[backend][deploy] Using Python: $PY"

if [ ! -d venv ]; then
  echo "[backend][deploy] Creating venv"
  "$PY" -m venv venv
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

echo "[backend][deploy] Upgrading pip and installing project deps"
pip install -U pip >/dev/null
pip install -e . >/dev/null

echo "[backend][deploy] Done. You can start with ./entrypoint.sh"

