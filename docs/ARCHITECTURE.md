# Architecture

Trust boundary: the Control Core is the policy enforcement point. Evolution can propose bounded strategy parameters only; it cannot modify permissions, security policies, tool allowlists, binaries or source code.

Data flow: command -> deterministic parser/planner -> policy validation -> allowlisted tool -> result evaluation -> experience store -> candidate optimizer -> isolated validation -> explicit approval -> active strategy.

Linux runs Mojo where supported plus Python API, SQLite and React. Windows development uses WSL2 for Mojo. Android uses Kotlin integration and a compatible service/runtime, not a claim of native Mojo support.

Current implementation includes a Python reference runtime and a Mojo BFS starter. Advanced modules/platform shells remain roadmap items until code and tests land.
