# MOJO AGENT — Complete Project Guide

## 1. Product definition

MOJO AGENT is a local-first, algorithm-first agent runtime. Python/FastAPI is the supported reference backend, React/Vite is the browser dashboard, and Kotlin/Jetpack Compose is the Android client. The default mode is deterministic Algorithms: no LLM, API key, Docker, paid service or cloud account is required.

Optional local model inference is isolated behind the LiteRT-LM adapter and explicit operator approval. The deterministic plan remains authoritative; model output is advisory and does not execute tools.

## 2. Architecture and trust boundaries

```text
React/Vite dashboard ─────┐
                          ├── HTTP / JSON ── FastAPI control API
Android Compose client ───┘                       │
                                                  ├── deterministic planner / algorithms
                                                  ├── allowlisted tools + approval gate
                                                  ├── workflow definitions + SQLite job queue
                                                  ├── opt-in worker + recurring schedules
                                                  ├── bounded evolutionary candidates
                                                  ├── memory / knowledge graph / analytics
                                                  ├── optional LiteRT-LM advisory runtime
                                                  ├── JSON-only extension registry
                                                  └── SQLite migrations / backup / restore
```

The control core is the policy boundary. Evolution may propose bounded strategy parameters; it must not rewrite source code, binaries, permissions, tool allowlists or security policy. Tool execution requires explicit approval. Arbitrary shell execution, arbitrary Python evaluation, dynamic extension imports and remote code execution are not supported.

## 3. Implemented backend areas

| Area | Current responsibility |
|---|---|
| Planning and algorithms | Deterministic goal decomposition, dependency ordering and utility algorithms |
| Evolution | Bounded strategy candidates, validation and explicit approval |
| Memory and knowledge | SQLite memory CRUD/search/import/export and knowledge graph nodes/edges |
| Tools | Built-in allowlisted deterministic operations with approval checks |
| Workflows | Up to 50 ordered steps; text, calculator, text statistics and safe template mappings |
| Conditions | equals, not_equals, contains and truthy checks against earlier workflow steps |
| Durable jobs | Immutable step snapshots, queue capacity bound, retries/backoff, cancellation, recovery and history |
| Worker and schedules | Opt-in backend worker, bounded polling/batches, manual worker tick and recurring schedule definitions |
| Database | Schema version/migrations, status, backup export/inspection and loopback-only verified restore |
| Security | Optional bearer token auth, hashed token storage, rotation/revocation and security status |
| Optional models | Algorithms/Hybrid/LiteRT-LM modes, approval-gated local inference and benchmark endpoints |
| Chat Workspace | Persistent SQLite conversations/messages, local model catalog, attachments, bounded context and chat-to-tool/skill operations with explicit approval |
| Extensions | Public JSON manifests, preview/hash verification, install/list/uninstall and allowlisted skill operations |
| Operations | Runtime status, diagnostics, bounded metadata-only logs, analytics and validated settings |

The SQLite queue is for one backend host. It is not a distributed queue. A running job checks cancellation between steps; an active operation is not forcibly interrupted by the queue.

## 4. API surface

Base URL: `http://127.0.0.1:8766/api/v1`

The interactive OpenAPI page is available at `http://127.0.0.1:8766/docs` while the backend is running.

- Runtime: health, runtime status, diagnostics and bounded runtime logs.
- Planning: goal plan, deterministic agent run and algorithm utilities.
- Memory: CRUD, search, import and export.
- Evolution: experiment, candidate validation and approval.
- Tools: list and approval-gated execution.
- Workflows: CRUD, direct run, history, schedules and manual scheduler tick.
- Durable jobs: enqueue, list/get, cancel, retry, worker tick and worker status.
- Database: migration/status, backup export, backup inspect and restore.
- Security: status, loopback bootstrap, token rotation and revocation.
- LiteRT-LM: status, run and benchmark.
- Extensions and skills: GitHub manifest preview/install, list/uninstall, skill plan, allowlisted skill execution and execution history.
- Analytics and settings: persistent analytics, settings validation/read/update and diagnostics.

Consult FastAPI OpenAPI for exact request/response schemas; do not rely on this guide as a substitute for the running API schema.

## 5. Frontend dashboard

The React/Vite dashboard includes overview, agent/planner, intelligence/evolution, memory, tools/skills, workflow composition, knowledge graph, analytics, security, diagnostics, runtime logs, backend control and settings. It includes responsive desktop/mobile navigation, theme and density preferences, reduced-motion support, workflow queue controls, runtime/model controls, extension management and database maintenance controls.

Some feature logic remains concentrated in `frontend/src/App.tsx`. The dashboard is functional but still needs component-level decomposition and broader automated UI coverage.

## 6. Android application

- Native Kotlin + Jetpack Compose client.
- Adaptive phone navigation and backend configuration/discovery.
- Workflow queue controls, worker settings, runtime/model and extension screens, security token support and backend status.
- Android emulator backend URL: `http://10.0.2.2:8766/api/v1`.
- USB: run `adb reverse tcp:8766 tcp:8766`, then use `http://127.0.0.1:8766/api/v1`.
- Same trusted Wi-Fi: configure the backend on a trusted private LAN interface and use backend discovery.
- The APK is a client only; it does not bundle the Python server, model weights or LiteRT-LM CLI. A backend can be hosted separately through Termux.

Known Android limitation: UI logic remains centered in a large Compose activity. Native file selection, structured list/detail experiences for every resource and comprehensive UI/accessibility tests remain outstanding.

## 7. Security and data safety

- Backend defaults to loopback.
- Bearer-token authentication is opt-in. The token is high entropy; only a salted digest is stored. Rotation invalidates the previous token.
- Initial token bootstrap, rotation, revocation and database restore are loopback-restricted.
- Database restore validates integrity, enforces a 128 MiB streaming request cap, supports optional SHA-256 verification and creates a safety backup.
- The worker is opt-in. Queue snapshots prevent later workflow edits from changing already-enqueued work.
- Runtime telemetry records request metadata, not request bodies.
- TLS termination, public internet hardening, rate limiting and multi-user RBAC are not included. Do not expose the backend directly to the public internet.
- Back up the SQLite database while the backend is stopped when using manual file copies. Prefer the API backup export for a consistent SQLite snapshot.

## 8. Install and run

### Windows 10/11 PowerShell

```powershell
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_all.ps1
```

Start two PowerShell terminals:

```powershell
.\scripts\run_backend.ps1
.\scripts\run_frontend.ps1
```

Dashboard: http://127.0.0.1:5173  
API docs: http://127.0.0.1:8766/docs

Optional Windows startup helper: `scripts/install_windows_service.ps1` creates a per-user Task Scheduler task. It is not a native Windows service or an EXE/MSI installer.

### Linux / macOS

```bash
git clone https://github.com/abdulraheemnohri/MOJO-AGENT-.git
cd MOJO-AGENT-
chmod +x scripts/*.sh
./scripts/install_all.sh
./scripts/run_backend.sh
# In another terminal:
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

Open a second Termux session and run `./scripts/run_termux_frontend.sh`, then visit http://127.0.0.1:5173.

### Android APK

Use the [Android APK workflow](https://github.com/abdulraheemnohri/MOJO-AGENT-/actions/workflows/android-apk.yml) and download the artifact from a successful run. A debug APK is not a signed production release.

## 9. Optional LiteRT-LM runtime

The default Algorithms mode does not load a model. To use local model inference, enable the runtime in Settings and install the native `litert-lm` CLI in the backend Python environment. Local `.litertlm` bundles use that CLI. Hugging Face repository IDs use the separate LiteRT CLI wrapper and may require Python 3.13 plus `litert-cli-nightly`; see `docs/HYBRID-RUNTIME-AND-EXTENSIONS.md`.

Model downloads can be large. Local offline inference requires the model artifacts to already be present. CPU is the portable baseline; GPU support depends on host drivers, runtime and model compatibility. Actual inference must be tested on the target machine.

## 10. Validation and release state

Run locally:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm install
npm run build
cd ..
gradle --no-daemon -p android :app:assembleDebug
```

The last inspected main commit, `094bd0e53dbc9e51bffa1decf79cd48ce5192454`, had a failed Python CI job because two LiteRT-LM API request schemas were missing. Frontend and installer jobs passed. The missing schema definitions and regression tests are being added on a follow-up branch. Do not call this state release-verified until all CI workflows pass on the final merge commit.

CI success is not a substitute for physical-device testing, Windows smoke testing, backup/restore testing or a real local model inference check.

## 11. Known gaps

1. No native iOS client.
2. No native Windows EXE/MSI installer.
3. No production-ready public remote server: TLS, rate limiting, multi-user RBAC and public exposure hardening remain out of scope.
4. No distributed queue or multi-host worker coordination.
5. Frontend and Android component decomposition and broad UI automation remain incomplete.
6. Native Android file picking and structured detail views for every resource remain incomplete.
7. Real LiteRT-LM inference depends on model/runtime/driver compatibility and needs host-specific verification.
8. Mojo compiler integration remains experimental; Python is the supported reference backend.

## 12. Licensing and support

The package metadata declares Apache-2.0. Voluntary donations can support development without locking core functionality behind a subscription. Keep changes tested, preserve the control-core boundary and document platform-specific requirements.


## 13. Chat Workspace

See [Chat Workspace guide](CHAT-WORKSPACE.md) for the complete API and feature contract. The dashboard and Android client include chat screens. Conversations, messages, model catalog entries and attachment blobs persist in SQLite. Algorithms mode requires no model; LiteRT-LM mode requires the runtime enabled and explicit approval for each inference. Built-in tools, installed extension tools and skills are exposed separately and require per-operation approval. Skill planning is non-executing.

Attachments are limited to 10 MiB each. UTF-8 text, Markdown, JSON, CSV and log files can be extracted into prompt context. PDF, Office, image, audio and video files can be stored/downloaded, but multimodal/OCR/transcription/extraction is not implemented by the current LiteRT-LM adapter. No cloud model provider or provider API key support is enabled. Model catalog entries do not trigger model downloads.
