# MOJO AGENT

Algorithm-first, local-first autonomous agent runtime. **No LLM is required or loaded.** Python is the supported cross-platform reference backend; React/Vite and Android are companion clients.

## Quick install

### Windows 10/11 (PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_all.ps1
# Terminal 1
.\scripts\run_backend.ps1
# Terminal 2
.\scripts\run_frontend.ps1
```

### Linux / macOS
```bash
chmod +x scripts/*.sh
./scripts/install_all.sh
# Terminal 1
./scripts/run_backend.sh
# Terminal 2
./scripts/run_frontend.sh
```

Backend API: http://127.0.0.1:8766/api/v1/health
API docs: http://127.0.0.1:8766/docs
Dashboard: http://127.0.0.1:5173

## Install separately

- Backend: `scripts/install_backend.sh` or `scripts/install_backend.ps1`
- Frontend: `scripts/install_frontend.sh` or `scripts/install_frontend.ps1`
- Run backend: `scripts/run_backend.sh` / `scripts/run_backend.ps1`
- Run frontend: `scripts/run_frontend.sh` / `scripts/run_frontend.ps1`

Python 3.10+ and Node.js 20+ are recommended. Backend dependencies are isolated in `.venv`; frontend packages are installed in `frontend/node_modules`. No Docker, cloud account, API key or paid service is required.

## Android

Open `android/` in Android Studio (JDK 17, Android SDK 35) and build a debug APK, or run the **Android Debug APK** GitHub Actions workflow. Install `android/app/build/outputs/apk/debug/app-debug.apk`.

- Emulator: `http://10.0.2.2:8766/api/v1`.
- USB: `adb reverse tcp:8766 tcp:8766`, then use `http://127.0.0.1:8766/api/v1`.
- Same Wi-Fi: run backend on PC with `mojo-agent --host 0.0.0.0`, allow TCP 8766 on the private-network firewall, then tap **Find backend on Wi-Fi**. Android scans the connected Wi-Fi subnet (maximum 1022 host probes) for the MOJO health endpoint on port 8766 and lets you select a result.

**LAN security:** default backend binding is loopback-only. LAN binding is opt-in and should only be used on a trusted private network. Never expose port 8766 directly to the public internet: the API has no remote authentication layer. Android cleartext HTTP is enabled for local development; add TLS/authentication before any untrusted deployment.

## Configuration

- CLI: `mojo-agent --host 127.0.0.1 --port 8766`; environment: `MOJO_AGENT_HOST`, `MOJO_AGENT_PORT`.
- Frontend: set `VITE_API_BASE=http://127.0.0.1:8766/api/v1`; Settings can save an override in browser-local storage.
- CORS is restricted to local Vite development/preview origins.
- Workflow scheduler is pull-driven; call `POST /api/v1/scheduler/tick` from an OS scheduler or manually.
- Tools are allowlisted and approval-gated. Shell execution and protected-source self-modification are disabled.
- Evolution changes bounded strategy parameters only; candidate validation and explicit approval are required.

## Testing

```bash
# Backend
.venv/bin/python -m pytest -q
# Windows: .venv\Scripts\python.exe -m pytest -q
# Frontend
cd frontend && npm run build
# Android (Gradle 8.9, JDK 17, SDK 35)
gradle --no-daemon -p android :app:assembleDebug
```

## Supported installation targets

| Platform | Backend | Frontend | Native client |
|---|---|---|---|
| Windows 10/11 | Python venv + PowerShell | Node/Vite | Browser; Android client over LAN |
| Linux | Python venv + shell | Node/Vite | Browser; Android client over LAN |
| macOS | Python venv + shell | Node/Vite | Browser; Android client over LAN |
| Android | Connects to an installed/running backend | Browser dashboard | Kotlin/Jetpack Compose app |

Mojo compiler integration is experimental and platform-dependent; Python remains the tested reference runtime. The Android app is a client and does not bundle the Python server.

See `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, and `docs/ROADMAP.md`.
