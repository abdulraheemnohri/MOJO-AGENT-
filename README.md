# MOJO AGENT

Self-evolving, algorithm-first autonomous agent. No LLM required.

## Quick start
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux: source .venv/bin/activate
pip install -e ".[dev]"
mojo-agent
```
API: http://127.0.0.1:8766/docs

Run tests: `pytest`
Dashboard: `cd frontend && npm install && npm run dev`

Mojo compiler support is platform-dependent. The Mojo core is intended for supported Linux environments; use WSL2 on Windows. Android uses a Kotlin integration layer and compatible service/runtime, not an unsupported native Mojo build.

## Architecture
`mojo_core/` Mojo primitives; `mojo_agent/` functional Python reference runtime/API; `frontend/` responsive dashboard; `android/` integration plan; `tests/` automated tests; `docs/` architecture and security.

Runtime analytics events are persisted in SQLite, queryable by event name, and retained with a bounded rolling limit.\n\nEvolution modifies bounded strategy parameters only. It cannot rewrite protected control code. Candidate activation requires tests and explicit approval.

Apache-2.0. See LICENSE.
