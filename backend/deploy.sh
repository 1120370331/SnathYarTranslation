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

USE_VENV=1
if [ ! -d venv ]; then
  echo "[backend][deploy] Creating venv"
  if ! "$PY" -m venv venv 2>/dev/null; then
    echo "[backend][deploy][warn] python -m venv not available. Falling back to --user installs (PEP 668 safe)."
    USE_VENV=0
  fi
fi

if [ "$USE_VENV" = "1" ] && [ -x venv/bin/python ]; then
  VPY="$(pwd)/venv/bin/python"
  echo "[backend][deploy] Upgrading pip and installing project deps (venv)"
  "$VPY" -m pip install -U pip >/dev/null
  "$VPY" -m pip install -e . >/dev/null
  echo "[backend][deploy] Done. You can start with ./entrypoint.sh"
else
  echo "[backend][deploy] Installing to user site-packages (~/.local) with PEP 668 override"
  "$PY" -m ensurepip --upgrade >/dev/null 2>&1 || true
  PIP_BREAK_SYSTEM_PACKAGES=1 "$PY" -m pip install --user -U pip setuptools wheel >/dev/null || \
    "$PY" -m pip install --user -U pip setuptools wheel --break-system-packages >/dev/null || true
  PIP_BREAK_SYSTEM_PACKAGES=1 "$PY" -m pip install --user -e . >/dev/null || \
    "$PY" -m pip install --user -e . --break-system-packages >/dev/null
  echo "[backend][deploy] Done (user mode). entrypoint will use 'python -m uvicorn' automatically."
fi
