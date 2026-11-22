#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/install_backend.sh"
"$ROOT/scripts/install_frontend.sh"
