#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || { echo "Run scripts/install_backend.sh first." >&2; exit 1; }
"$PY" -m pip install --upgrade litert-lm
"$PY" -m mojo_agent.cli litertlm status
