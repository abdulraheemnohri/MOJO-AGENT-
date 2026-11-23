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
- Persistent Chat Workspace with conversation history, local model catalog, system prompts and bounded context
- Algorithms chat without an LLM and optional approval-gated LiteRT-LM model chat
- Chat attachments (10 MiB per file) with UTF-8 text extraction for text/Markdown/JSON/CSV/log files
- Chat-connected built-in tools, installed extension tools and skills; separate approval before every execution
- Bounded evolutionary strategy optimization with validation and explicit approval
- SQLite memory CRUD, search, import and export
- Knowledge graph nodes, edges and search
- Allowlisted tools with mandatory approval
- Visual declarative workflows with templates, prior-step conditions and bounded execution
- Durable SQLite workflow queue, immutable job snapshots, retries, cancellation, recovery and opt-in worker
- Persistent scheduler definitions, manual tick and worker status
- SQLite migrations, backup export/inspection and loopback-only verified restore
- Optional bearer-token API authentication, rotation and revocation
- Optional Algorithms / Hybrid / LiteRT-LM runtime with explicit inference approval
- Declarative JSON-only GitHub extensions and approval-gated allowlisted skill operations
- Persistent analytics, diagnostics, runtime status and bounded metadata-only logs
- Responsive React dashboard and adaptive Android backend client with queue/runtime/security controls

## Project documentation

- [Chat Workspace guide](docs/CHAT-WORKSPACE.md) — chat models, conversations, attachments, tools, skills, API and limitations
- [Complete project guide](docs/PROJECT-GUIDE.md) — architecture, modules, API, platform setup, settings, safety and known gaps
- [Installation guide](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation status](docs/IMPLEMENTATION-STATUS.md)
- [Security](docs/SECURITY.md)
- [Roadmap](docs/ROADMAP.md)

## Configuration and safety

- Python 3.10+ and Node.js 20+ recommended.
- No Docker, API key, LLM or paid service required for the main baseline.
- Backend binds to loopback by default. Bearer-token authentication is optional; TLS, rate limiting and multi-user RBAC are not included. Do not expose the backend directly to the public internet.
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

See [implementation status](docs/IMPLEMENTATION-STATUS.md) for the current CI result and release blockers. CI success is not a substitute for physical-device testing.

## Optional LiteRT-LM CLI

Install the native runner with `python -m pip install --upgrade litert-lm` inside the MOJO AGENT virtual environment. Local `.litertlm` bundles use this CLI. Hugging Face repository IDs require the separate LiteRT CLI wrapper (`litert lm`), installed with Python 3.13 and `litert-cli-nightly`. Check availability using `mojo-agent litertlm status`. See [Hybrid Runtime and Extensions](docs/HYBRID-RUNTIME-AND-EXTENSIONS.md). Runtime remains disabled by default.

## Platform boundaries

Python is the supported reference backend. React/Vite is the browser dashboard. Kotlin/Jetpack Compose is the Android client. Android can also host the backend via Termux. There is no native iOS client, Windows executable installer, or production-hardened remote server in this release. Mojo compiler integration remains experimental.


## Optional hybrid runtime and GitHub extensions

The default agent mode is deterministic **Algorithms**. Optional **Hybrid** and **LiteRT-LM** modes use the local LiteRT-LM CLI on the backend host; model inference requires explicit approval. See [Hybrid Runtime and Extensions](docs/HYBRID-RUNTIME-AND-EXTENSIONS.md).

The dashboard and Android client include Runtime & Models and Extensions Hub screens. GitHub skills and tools install from public JSON manifests only. Arbitrary Python, shell scripts and binaries are never executed. Install scripts for the optional CLI:
- Windows: `scripts/install_litertlm.ps1`
- Linux/macOS/Termux: `scripts/install_litertlm.sh`

Example declarative packages are in `examples/extensions/`. Pin a commit SHA and review the manifest hash before installation.
