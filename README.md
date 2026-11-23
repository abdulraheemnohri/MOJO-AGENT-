# MOJO AGENT

Algorithm-first, local-first autonomous agent runtime. **No LLM is required or loaded.** Python is the supported cross-platform reference backend; React/Vite and Android are companion clients.

## Quick install

### Windows 10/11 (PowerShell)
```powershell
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_all.ps1
```
Start in two terminals: ` .\scripts\run_backend.ps1 ` and ` .\scripts\run_frontend.ps1 `.

### Linux / macOS
```bash
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_all.sh
```
Start in two terminals: `./scripts/run_backend.sh` and `./scripts/run_frontend.sh`.

### Android / Termux
Install Termux from a current trusted distribution, then:
```bash
pkg update && pkg upgrade -y
pkg install -y git python nodejs-lts
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_termux.sh
```
Run `./scripts/run_termux_backend.sh` and in another Termux session `./scripts/run_termux_frontend.sh`. Open http://127.0.0.1:5173 on the phone.

## Service URLs

- Dashboard: http://127.0.0.1:5173
- Backend health: http://127.0.0.1:8766/api/v1/health
- API docs: http://127.0.0.1:8766/docs

## Android native app

The APK is a client, not a bundled server. Install the current debug artifact from the [Android APK workflow](https://github.com/abdulraheemnohri/MOJO-AGENT-/actions/workflows/android-apk.yml). On the same Wi-Fi, run the PC backend with `--host 0.0.0.0 --port 8766`, allow TCP 8766 on the private firewall and tap **Find backend on Wi-Fi** in the app. For USB use `adb reverse tcp:8766 tcp:8766` and `http://127.0.0.1:8766/api/v1`. Emulator URL: `http://10.0.2.2:8766/api/v1`.

## Complete installation instructions

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for Windows, Ubuntu/Debian, Fedora, Arch/Manjaro, macOS, Termux, Android APK installation/build, firewall setup, testing, backup and troubleshooting.

## Configuration and safety

- Python 3.10+ and Node.js 20+ recommended. No Docker, API key, LLM or paid service required.
- Backend defaults to loopback-only. LAN mode is opt-in and has no remote authentication/TLS; never expose port 8766 to the public internet.
- Tools are allowlisted and approval-gated. Shell execution and protected-source self-modification are disabled.
- Evolution changes bounded strategy parameters; candidate validation and explicit approval are required.
- SQLite data is stored in `data/mojo_agent.sqlite3`; back up the `data/` directory.

## Testing

```bash
.venv/bin/python -m pytest -q
cd frontend && npm run build
gradle --no-daemon -p android :app:assembleDebug
```
Windows backend test: `.venv\Scripts\python.exe -m pytest -q`.

## Optional LiteRT-LM CLI

Install with `python -m pip install --upgrade litert-lm` inside the MOJO AGENT virtual environment. Check availability using `mojo-agent litertlm status`. See [docs/LITERTLM.md](docs/LITERTLM.md) for model execution, benchmarking and API configuration. It remains disabled by default.

## Platform boundaries

Python is the supported reference backend. React/Vite is the browser dashboard. Kotlin/Jetpack Compose is the Android client. Android can also host the backend via Termux. There is no native iOS client, Windows executable installer, or production-hardened remote server in this release. Mojo compiler integration remains experimental.


## Optional hybrid runtime and GitHub extensions

The default agent mode is deterministic **Algorithms**. Optional **Hybrid** and **LiteRT-LM** modes use the local LiteRT-LM CLI on the backend host; model inference requires explicit approval. See [Hybrid Runtime and Extensions](docs/HYBRID-RUNTIME-AND-EXTENSIONS.md).

The dashboard and Android client include Runtime & Models and Extensions Hub screens. GitHub skills and tools install from public JSON manifests only. Arbitrary Python, shell scripts and binaries are never executed. Install scripts for the optional CLI:
- Windows: `scripts/install_litertlm.ps1`
- Linux/macOS/Termux: `scripts/install_litertlm.sh`

Example declarative packages are in `examples/extensions/`. Pin a commit SHA and review the manifest hash before installation.
