# MOJO AGENT

Algorithm-first, local-first autonomous agent runtime. **No LLM is required or loaded in the main baseline.** Python/FastAPI is the supported reference backend; React/Vite and Kotlin/Jetpack Compose are companion clients.

## Quick start — Windows 10/11

```powershell
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_all.ps1
```

Open two PowerShell terminals:

```powershell
.\scripts\run_backend.ps1
.\scripts\run_frontend.ps1
```

Dashboard: http://127.0.0.1:5173  
API health: http://127.0.0.1:8766/api/v1/health  
Interactive API docs: http://127.0.0.1:8766/docs

## Other platforms

### Linux / macOS

```bash
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_all.sh
```

Run `./scripts/run_backend.sh` and `./scripts/run_frontend.sh` in separate terminals.

### Android / Termux backend

```bash
pkg update && pkg upgrade -y
pkg install -y git python nodejs-lts
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_termux.sh
```

Start `./scripts/run_termux_backend.sh`; in a second Termux session start `./scripts/run_termux_frontend.sh`. Open http://127.0.0.1:5173 on the phone.

## Android native app

The APK is a client, not a bundled Python server. Download the `mojo-agent-debug-apk` artifact from the [Android APK workflow](https://github.com/abdulraheemnohri/MOJO-AGENT-/actions/workflows/android-apk.yml).

- Android emulator backend URL: `http://10.0.2.2:8766/api/v1`
- USB: run `adb reverse tcp:8766 tcp:8766` and use `http://127.0.0.1:8766/api/v1`
- Same trusted Wi-Fi: run the backend on a private LAN interface, permit TCP 8766 in the private firewall, then use backend discovery in the app.

## Capabilities

- Deterministic goal planning and algorithm utilities
- Bounded evolutionary strategy optimization with validation and explicit approval
- SQLite memory CRUD, search, import and export
- Knowledge graph nodes, edges and search
- Allowlisted tools with mandatory approval
- Workflow CRUD, bounded synchronous execution and run history
- Scheduler definitions with manual scheduler tick
- Persistent analytics, diagnostics, runtime status and bounded metadata-only logs
- Settings and responsive dashboard preferences
- Adaptive Android client with local backend discovery

## Project documentation

- [Complete project guide](docs/PROJECT-GUIDE.md) — architecture, modules, API, platform setup, settings, safety and known gaps
- [Installation guide](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation status](docs/IMPLEMENTATION-STATUS.md)
- [Security](docs/SECURITY.md)
- [Roadmap](docs/ROADMAP.md)

## Configuration and safety

- Python 3.10+ and Node.js 20+ recommended.
- No Docker, API key, LLM or paid service required for the main baseline.
- Backend binds to loopback by default. LAN mode has no remote authentication/TLS; do not expose it to the public internet.
- Tool approval is mandatory. Shell execution and protected-source self-modification are disabled.
- Evolution can propose bounded strategy parameters only; candidate validation and explicit approval are required.
- SQLite database: `data/mojo_agent.sqlite3`. Back up the `data/` directory while the backend is stopped.

## Tests and builds

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
gradle --no-daemon -p android :app:assembleDebug
```

The frontend/backend CI and Android debug APK CI passed for main commit `3c41501a0a0109b924af74f1bbe888c29b0abf56`. CI success is not a substitute for physical-device testing.

## Platform boundaries

Python is the supported reference runtime. React/Vite is the web dashboard. Kotlin/Compose is the Android client. Android can host the backend separately through Termux. There is no native iOS client, no Windows executable installer, and no production-hardened remote server. Mojo compiler integration remains experimental. Optional LiteRT-LM work is isolated on open PR #4 and is not part of this main-branch baseline.
