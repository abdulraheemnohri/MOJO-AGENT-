# MOJO AGENT — Complete Project Guide

## 1. Product definition

MOJO AGENT is a local-first, algorithm-first agent runtime. The reference backend is Python/FastAPI with SQLite persistence. React/Vite is the browser dashboard; Kotlin/Jetpack Compose is the Android client. The default configuration has no LLM, API key, Docker, paid service, or cloud dependency.

The original project profile is retained:
- Architecture: evolutionary, with a protected control core
- Platforms: Windows, Linux, macOS, Android/Termux and browser
- Learning: bounded evolutionary optimization, not unrestricted self-training
- LLM: none by default

## 2. Architecture and trust boundaries

```text
React/Vite dashboard ─────┐
                          ├── HTTP / JSON ── FastAPI control API
Android Compose client ───┘                       │
                                                  ├── deterministic planner / algorithms
                                                  ├── allowlisted tool registry
                                                  ├── workflow engine and manual scheduler tick
                                                  ├── bounded evolution + candidate validation
                                                  ├── memory / knowledge graph / analytics
                                                  ├── settings / diagnostics / security status
                                                  └── SQLite database
```

The control core is the policy enforcement boundary. Evolution may propose bounded strategy parameters; it must not rewrite source code, binaries, permissions, tool allowlists, or security policy. Candidate validation and explicit approval are required before activation. Shell execution is disabled. The API does not expose arbitrary Python evaluation.

## 3. Implemented backend modules

| Module | Responsibility |
|---|---|
| `algorithms.py` | Deterministic graph/search and utility algorithms, similarity and Q-value update helpers |
| `planner.py` | Goal decomposition and dependency ordering |
| `evolution.py` | Bounded strategy candidate generation and evaluation |
| `evolution_store.py` | Persisted champion, generation and candidates |
| `memory.py` | SQLite memory CRUD, search and JSON import/export |
| `knowledge.py` | Knowledge graph node/edge CRUD and search |
| `workflows.py` | Workflow definitions, bounded step execution, schedules and run history |
| `tools.py` | Allowlisted deterministic tools with approval checks |
| `analytics.py` | Persistent, bounded event analytics |
| `settings.py` | Validated persistent preferences; protected safety defaults |
| `security.py` | Security policy/status helpers |
| `api.py` | FastAPI routes, request telemetry, diagnostics and runtime status |
| `cli.py` | `mojo-agent` command entry point |
| `litertlm.py` | Optional integration on the separate LiteRT-LM feature branch / PR #4; not part of the verified main-branch baseline |

## 4. API surface on main

Base URL: `http://127.0.0.1:8766/api/v1`

- Runtime: `GET /health`, `GET /runtime/status`, `GET /runtime/logs`, `POST /runtime/logs/clear`, `GET /backup/export`
- Discovery and planning: `GET /discovery`, `POST /plan`, `POST /algorithms/q-update`
- Memory: `GET|POST /memory`, `PATCH|DELETE /memory/{memory_id}`, `GET /memory/export`, `POST /memory/import`
- Evolution: `GET /evolution/status`, `POST /evolution/experiment`, candidate validate and approve routes
- Tools: `GET /tools`, `POST /tools/execute`
- Workflows: list/create/update/delete, run, and history routes
- Scheduler: list/create/update/delete schedules and explicit `POST /scheduler/tick`
- Knowledge graph: list/search, create nodes/edges, delete nodes/edges
- Operations: analytics, diagnostics, security status, settings read/update/validation

The scheduler is manually ticked; it is not a continuously running background service. Workflow execution is synchronous and bounded.

## 5. Frontend dashboard

The Vite/React dashboard provides navigation for Overview, Agent Studio, Tasks & Planner, Intelligence Lab, Evolution Lab, Memory Center, Tools & Skills, Workflows, Knowledge Graph, Analytics, Security, Diagnostics, Runtime Logs, Backend Control and Settings.

The current responsive stylesheet provides desktop sidebar navigation, mobile drawer behavior, responsive grids/cards/forms, light/dark theme styling, compact density, reduced-motion support and breakpoints for phone/tablet/desktop. Some page logic remains concentrated in `App.tsx`; this is functional but should be refactored into feature-level components as the next maintainability milestone.

Local browser preferences include API base URL, theme-related UI state, density, hints, auto-refresh interval and reduced motion. Browser-local preferences are separate from backend SQLite settings.

## 6. Android application

- Native Kotlin + Jetpack Compose client; min SDK 26, target SDK 35, Java 17.
- Uses OkHttp to call the configured FastAPI backend.
- Adaptive navigation includes compact phone navigation and a wider navigation layout.
- Backend discovery scans the current local Wi-Fi subnet for the MOJO health endpoint.
- The APK is a client only; the Python backend is not bundled into the APK.
- USB workflow: `adb reverse tcp:8766 tcp:8766`, then use `http://127.0.0.1:8766/api/v1`.
- Android emulator workflow: `http://10.0.2.2:8766/api/v1`.
- Same-LAN workflow requires starting the backend on a trusted LAN interface and permitting TCP 8766 on the private firewall.

Known Android limitation: the current client is still centered in one large Compose activity and includes a raw JSON response view. Native file selection, structured list/detail experiences for every resource, full workflow editing and broader accessibility/UI test coverage remain future work.

## 7. Settings and safety

Backend settings currently persist supported preferences such as theme. Tool approval is mandatory and cannot be disabled. Runtime host/port are restart-time configuration, not live settings. The default backend binding is loopback. LAN mode has no remote authentication or TLS and must not be exposed to the public internet.

Do not put secrets, passwords, OTPs, provider API keys or private data in runtime logs. Request telemetry records route/method/status/timing metadata, not request bodies.

## 8. Install and run

### Windows 10/11 PowerShell

```powershell
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_all.ps1
```

Start two PowerShell windows:

```powershell
.\scripts\run_backend.ps1
.\scripts\run_frontend.ps1
```

Dashboard: http://127.0.0.1:5173  
API docs: http://127.0.0.1:8766/docs

### Linux / macOS

```bash
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_all.sh
./scripts/run_backend.sh
# In a second terminal:
./scripts/run_frontend.sh
```

### Android / Termux backend

```bash
pkg update && pkg upgrade -y
pkg install -y git python nodejs-lts
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_termux.sh
./scripts/run_termux_backend.sh
```

Open a second Termux session and run `./scripts/run_termux_frontend.sh`. Then visit http://127.0.0.1:5173 on the phone.

### Android APK

Download the `mojo-agent-debug-apk` artifact from the successful [Android APK workflow](https://github.com/abdulraheemnohri/MOJO-AGENT-/actions/workflows/android-apk.yml). Enable installation for the app used to open the APK. For development builds:

```bash
gradle --no-daemon -p android :app:assembleDebug
```

## 9. Validation commands

```powershell
# Windows backend
.\.venv\Scripts\python.exe -m pytest -q

# Frontend
cd frontend
npm run build

# Android
gradle --no-daemon -p android :app:assembleDebug
```

The frontend/backend workflow and Android APK workflow were successful for main commit `3c41501a0a0109b924af74f1bbe888c29b0abf56`. This is CI evidence, not a claim of physical-device testing on every Android model or OS.

## 10. Known gaps — do not mistake roadmap for shipped functionality

1. No native iOS client.
2. No bundled Python backend in Android APK; Termux is a separate backend deployment.
3. No production remote-authentication/TLS layer; LAN mode is trusted-network development use only.
4. No persistent background worker/daemon for scheduled workflows; scheduler tick is manual.
5. Workflow execution is synchronous, not a distributed queue.
6. Android native file picker, complete structured resource screens, full workflow editor and UI tests need implementation.
7. React dashboard page logic should be split into reusable feature components and tested with component-level tests.
8. Database restore and a safe migration/rollback manager are not implemented; export/backup is available.
9. Mojo compiler integration is experimental; Python is the supported reference backend.
10. LiteRT-LM integration is optional and currently isolated on open PR #4; it is not a dependency of the no-LLM main baseline.

## 11. Development priorities

P0: authentication/TLS before any remote/LAN exposure; API request size/rate limits; automated dependency/security scans; backup restore/migration tests.  
P1: split Android Compose screens and React feature components; add UI tests, accessibility semantics, loading/error/empty states and robust API retry handling.  
P2: background scheduler with persisted leases and crash recovery; workflow cancellation and idempotency; database migration framework.  
P3: optional local model adapters only behind explicit opt-in, bounded resource budgets and the existing protected control core.

## 12. Licensing and contributions

The package metadata declares Apache-2.0. Keep new modules tested, preserve the control-core boundary, and document platform-specific requirements. Donations can be added as a voluntary support option without locking core functionality behind a subscription.
