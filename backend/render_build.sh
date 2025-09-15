#!/usr/bin/env bash
set -euo pipefail

# Render build script for backend service
# Usage (Render Build Command):
#   bash backend/render_build.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Backend build: installing Python dependencies"
python -m pip install --upgrade pip setuptools wheel

if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt
fi

# Install project in editable mode to expose entry points (optional)
python -m pip install -e .

echo "✅ Backend build completed"

