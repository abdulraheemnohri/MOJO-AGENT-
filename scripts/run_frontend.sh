#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
[ -d node_modules ] || { echo "Run ../scripts/install_frontend.sh first"; exit 1; }
exec npm run dev
