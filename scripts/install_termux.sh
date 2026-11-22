#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v pkg >/dev/null 2>&1 || [ -z "${PREFIX:-}" ]; then
  echo "This installer is for Termux on Android only."
  exit 1
fi

pkg update
pkg install -y git python nodejs-lts
command -v python >/dev/null 2>&1 || { echo "Termux Python installation failed"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is missing; install a Termux Node.js package that provides npm"; exit 1; }

export PYTHON=python
./scripts/install_backend.sh
./scripts/install_frontend.sh

echo
echo "MOJO AGENT is installed in: $ROOT"
echo "Backend: ./scripts/run_termux_backend.sh"
echo "Dashboard: ./scripts/run_termux_frontend.sh"
