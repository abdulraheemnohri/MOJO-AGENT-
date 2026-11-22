#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || { echo "Python 3.10+ is required"; exit 1; }
"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' || { echo "Python 3.10+ is required"; exit 1; }
if [ ! -d .venv ]; then "$PYTHON" -m venv .venv; fi
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
echo "Backend installed. Run ./scripts/run_backend.sh"
