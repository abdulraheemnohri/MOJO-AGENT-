#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
command -v npm >/dev/null 2>&1 || { echo "Node.js 20+ and npm are required"; exit 1; }
npm install
npm run build
echo "Frontend installed and production build verified."
