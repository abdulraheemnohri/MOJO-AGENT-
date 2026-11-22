# MOJO AGENT — Complete Installation Guide

This guide covers the supported deployment shapes for Windows 10/11, Linux, macOS, Android/Termux, Android Studio and browser-only clients.

## 1. What runs where

| Component | Windows | Linux | macOS | Android |
|---|---|---|---|---|
| Python API/backend | Yes | Yes | Yes | Yes, through Termux |
| React dashboard | Yes | Yes | Yes | Yes, in a mobile browser or Termux |
| Native Kotlin app | No | Build with Android SDK | Build with Android SDK | Install APK |
| SQLite data | Local disk | Local disk | Local disk | Termux app storage |

The backend is the source of truth and stores data in `data/mojo_agent.sqlite3`. The dashboard and native Android app are clients. No LLM, API key, Docker, cloud account or paid service is required. Python 3.10+ and Node.js 20+ are recommended.

## 2. Get the source

Clone the implementation branch:

```bash
git clone --branch implementation/full-platform https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
```

If Git is unavailable, open the repository on GitHub and use **Code → Download ZIP**, extract it, then open a terminal in the extracted `MOJO-AGENT-` folder.

## 3. Windows 10/11 — full installation

### Install prerequisites

Open PowerShell. If you have winget:

```powershell
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Git.Git -e
```

Close and reopen PowerShell, then verify:

```powershell
py --version
node --version
npm --version
git --version
```

Python must be 3.10 or newer; Node.js must be 20 or newer.

### Clone and install both components

```powershell
git clone --branch implementation/full-platform https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_all.ps1
```

### Start the backend and dashboard

Open **two PowerShell windows** in the project folder.

Terminal 1:

```powershell
.\scripts\run_backend.ps1
```

Terminal 2:

```powershell
.\scripts\run_frontend.ps1
```

Open the dashboard at http://127.0.0.1:5173. Backend health: http://127.0.0.1:8766/api/v1/health. Interactive API documentation: http://127.0.0.1:8766/docs.

### Install only one component

```powershell
.\scripts\install_backend.ps1
.\scripts\install_frontend.ps1
```

Run separately with ` .\scripts\run_backend.ps1 ` or ` .\scripts\run_frontend.ps1 `.

## 4. Ubuntu / Debian / Linux Mint

Install system dependencies:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nodejs npm
```

Check versions:

```bash
python3 --version
node --version
npm --version
```

Install and run:

```bash
git clone --branch implementation/full-platform https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_all.sh
```

Use two terminals from the project folder:

```bash
./scripts/run_backend.sh
```

```bash
./scripts/run_frontend.sh
```

If your distribution's Node.js package is older than 20, install a current Node.js LTS release from the official Node.js distribution instructions before running `install_frontend.sh`.

## 5. Fedora

```bash
sudo dnf install -y git python3 python3-pip nodejs npm
python3 --version
node --version
git clone --branch implementation/full-platform https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_all.sh
```

Start in separate terminals:

```bash
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

## 6. Arch Linux / Manjaro

```bash
sudo pacman -Syu --needed git python python-pip nodejs npm
git clone --branch implementation/full-platform https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_all.sh
```

Start in separate terminals with `./scripts/run_backend.sh` and `./scripts/run_frontend.sh`.

## 7. macOS (Intel and Apple Silicon)

Install prerequisites using Homebrew. If Homebrew is not installed, install it using the instructions at https://brew.sh.

```bash
brew update
brew install git python@3.12 node
python3 --version
node --version
npm --version
```

Clone and install:

```bash
git clone --branch implementation/full-platform https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_all.sh
```

Run backend and frontend in separate Terminal windows:

```bash
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

## 8. Android phone — native app (recommended client setup)

The Android APK is a client; it does not contain the Python backend. Run the backend on a PC, Mac, Linux machine or Android/Termux, then connect the APK to it.

### Download the verified debug APK

1. Open the [Android APK workflow run](https://github.com/abdulraheemnohri/MOJO-AGENT-/actions/runs/45006397618).
2. Sign in to GitHub if prompted.
3. In **Artifacts**, download `mojo-agent-debug-apk`.
4. Extract the ZIP; it contains `app-debug.apk`.
5. On Android, allow installation for the browser/file manager when Android prompts, then tap the APK and install.

This is a debug/test build, not a Play Store release. The artifact expires after the retention period shown by GitHub Actions; build a fresh APK from source if it expires.

### Connect Android to a computer on the same Wi-Fi

On the computer, start the backend with LAN binding:

Windows PowerShell:
```powershell
.\scripts\run_backend.ps1 --host 0.0.0.0 --port 8766
```

Linux/macOS:
```bash
./scripts/run_backend.sh --host 0.0.0.0 --port 8766
```

Allow inbound TCP port 8766 on the computer's **Private** network firewall profile only. Keep the phone and computer on the same trusted Wi-Fi. Open MOJO AGENT on Android, tap **Find backend on Wi-Fi**, then select the discovered computer. If discovery fails, enter the computer's LAN IP manually, for example `http://192.168.1.20:8766/api/v1`.

### USB connection (no Wi-Fi discovery)

Install Android Platform Tools on the computer, enable USB debugging, connect the phone and approve the debugging prompt:

```bash
adb devices
adb reverse tcp:8766 tcp:8766
```

In the app set the backend URL to:

```
http://127.0.0.1:8766/api/v1
```

Windows PowerShell uses the same `adb` commands.

### Android emulator

Use this API base URL inside the emulator:

```
http://10.0.2.2:8766/api/v1
```

The backend must be running on the host computer.

## 9. Android phone — run the backend locally with Termux

This runs the Python API on the phone itself. Install Termux from a trusted official distribution source such as the F-Droid project or the Termux GitHub releases; avoid outdated Play Store builds.

Open Termux:

```bash
pkg update && pkg upgrade -y
pkg install -y git python nodejs-lts
```

Clone and install backend + dashboard:

```bash
git clone --branch implementation/full-platform https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_termux.sh
```

Start the backend:

```bash
./scripts/run_termux_backend.sh
```

Open another Termux session, go to the same folder and start the dashboard:

```bash
cd MOJO-AGENT-
./scripts/run_termux_frontend.sh
```

Open http://127.0.0.1:5173 in the phone browser. Backend health is http://127.0.0.1:8766/api/v1/health. To use the native APK on the same phone, set its API base to `http://127.0.0.1:8766/api/v1`.

Termux may stop background processes when Android reclaims memory or applies battery restrictions. Keep Termux open while testing. This is a development setup, not a persistent Android service.

## 10. Build the Android APK from source

Requirements: Android Studio with JDK 17, Android SDK Platform 35, Android Build Tools 35.0.0 and Gradle 8.9.

1. Open Android Studio.
2. Select **Open**, then choose the repository's `android/` directory.
3. Let Gradle sync and install missing SDK components.
4. Select **Build → Build Bundle(s) / APK(s) → Build APK(s)**.
5. The debug APK is created at `android/app/build/outputs/apk/debug/app-debug.apk`.

Command line (after installing JDK 17, Android SDK 35 and Gradle 8.9):

```bash
gradle --no-daemon -p android :app:assembleDebug
```

Install to a connected device:

```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

Windows PowerShell path:

```powershell
gradle --no-daemon -p android :app:assembleDebug
adb install -r .\android\app\build\outputs\apk\debug\app-debug.apk
```

## 11. Verify installation and run tests

Backend health:

```bash
curl http://127.0.0.1:8766/api/v1/health
```

Windows PowerShell equivalent:

```powershell
Invoke-RestMethod http://127.0.0.1:8766/api/v1/health
```

Run backend tests:

```bash
# Linux/macOS/Termux
.venv/bin/python -m pytest -q

# Windows PowerShell
.venv\Scripts\python.exe -m pytest -q
```

Build the dashboard:

```bash
cd frontend
npm run build
```

## 12. Data, backups and updates

The SQLite database is stored in `data/mojo_agent.sqlite3`. Stop the backend before copying the database for a consistent simple backup. Back up the whole `data/` directory to a safe location. Do not commit private databases or memory exports to a public repository.

Update the source:

```bash
git pull --ff-only origin implementation/full-platform
```

Then rerun the installer for your OS to refresh Python and Node dependencies. Existing SQLite data is retained; keep a backup before updating.

## 13. Network and security notes

- Backend defaults to `127.0.0.1` (loopback only). Do not bind to `0.0.0.0` unless you explicitly need LAN access.
- LAN mode currently has no remote authentication or TLS. Use it only on a trusted private network; never port-forward 8766 or expose it to the public internet.
- Keep firewall rules limited to a private LAN and remove them when finished testing.
- The runtime has no shell-execution tool and does not modify protected source code. Evolution optimizes bounded strategy parameters and requires validation and explicit approval.
- Do not use sensitive or production data in this development build.

## 14. Troubleshooting

**`python` / `python3` not found:** install Python 3.10+ and reopen the terminal.

**`npm` not found or old Node:** install Node.js 20+ and reopen the terminal.

**Port 8766 already in use:** stop the other process or launch with a different port; note that Android subnet discovery currently probes the default port 8766.

**Dashboard cannot reach API:** verify the backend health URL, then check that the dashboard's API base is `http://127.0.0.1:8766/api/v1`. For a phone, use the computer LAN IP or USB reverse instructions.

**Android discovery returns no servers:** verify both devices share the same Wi-Fi subnet, the backend was started with `--host 0.0.0.0`, and the computer's private firewall permits TCP 8766. Guest Wi-Fi/client isolation can block discovery.

**Termux install fails:** update Termux packages and use a current Termux distribution; ensure the installed Node package provides both `node` and `npm`.

**APK installation blocked:** allow the source app to install unknown apps, or use `adb install -r` from a computer with USB debugging enabled.

## 15. Platform support boundaries

The supported reference backend is Python. The React dashboard is a browser app. The native Android app is a Kotlin client. Windows, Linux and macOS use the same Python and Node installers; Android can run the backend through Termux. There is no native iOS app, no native Windows executable installer, and no production-hardened remote server configuration in this release. Mojo compiler integration remains experimental and is not required.
