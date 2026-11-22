#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -x .venv/bin/mojo-agent ] || { echo "Run ./scripts/install_backend.sh first"; exit 1; }
exec .venv/bin/mojo-agent "$@"
