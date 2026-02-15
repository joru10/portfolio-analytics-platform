#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d backend/.venv ]]; then
  python3 -m venv backend/.venv
fi

source backend/.venv/bin/activate
pip install --upgrade pip
pip install -e backend[dev]

echo "Bootstrap complete. Run: make run"
