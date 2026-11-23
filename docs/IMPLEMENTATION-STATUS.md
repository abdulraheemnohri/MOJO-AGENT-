# MOJO AGENT — implementation status

Last reconciled against `main` commit `31d78ae309883fbb5c2a50cdc9eff8bb3e8f3d9d` on 2026-11-23. PR #9 is merged. This feature branch contains the new Chat Workspace implementation and is not yet merged.

## Implemented on main

- Python/FastAPI reference backend with versioned JSON API and SQLite persistence.
- Deterministic goal decomposition, dependency ordering and algorithm utilities.
- Bounded evolutionary strategy proposals with validation and explicit approval; the protected control core is not self-modified.
- Memory CRUD, search, JSON import/export and knowledge-graph nodes, edges and search.
- Allowlisted deterministic tools with mandatory approval; no arbitrary shell, Python evaluation or dynamic extension code.
- Declarative workflow builder with ordered steps, templates, prior-step mappings and conditional execution.
- Durable SQLite workflow queue with immutable snapshots, bounded retries, backoff, cooperative cancellation, history, startup recovery and opt-in worker.
- Persistent schedules, worker tick and worker status. Queue and worker are single-host SQLite features.
- SQLite migrations, database status, backup export/inspection and loopback-only restore with integrity checks, optional SHA-256 verification, request-size cap and safety backup.
- Optional API bearer-token authentication with high-entropy tokens, salted hashes, constant-time verification, rotation and revocation. Authentication is opt-in; TLS and multi-user RBAC are not included.
- Optional Algorithms / Hybrid / LiteRT-LM runtime modes. Algorithms remains the default and does not require a model. Local inference is approval-gated and advisory.
- Optional LiteRT-LM CLI adapter for local `.litertlm` bundles and separate LiteRT CLI wrapper for Hugging Face repository IDs.
- Public JSON-only GitHub extension manifests with preview/hash verification, install/list/uninstall, skill instructions and approval-gated allowlisted operations. No extension source code, shell scripts or binaries are executed.
- React/Vite dashboard with responsive navigation, workflow composition, runtime/model and extension pages, security controls, diagnostics, analytics and settings.
- Kotlin/Jetpack Compose Android client with adaptive navigation, backend discovery/configuration, runtime/extensions, workflow queue controls and bearer-token support.
- Windows, POSIX and Termux setup/run scripts. Windows startup helper creates a per-user Task Scheduler task, not a native Windows service or packaged EXE installer.

## New Chat Workspace implementation — feature branch

Branch: `feature/universal-chat-workspace`

- Persistent SQLite chat conversations, messages and attachment blobs.
- Schema migration v3; older database backups remain eligible for inspection and are migrated after restore.
- Algorithms chat mode with deterministic responses and no model dependency.
- Optional local LiteRT-LM chat mode with per-message explicit inference approval.
- Saved local model catalog with validation, select/default and remove controls. Adding a catalog entry does not download model weights.
- Conversation CRUD, bounded history, title generation, system prompt and context-window settings.
- Attachment upload/download (10 MiB per file) for text, Markdown, JSON, CSV, logs, PDF, Office files, images, audio and MP4.
- UTF-8 extraction into model context only for text, Markdown, JSON, CSV and log files. Other file types are stored but not interpreted by this runtime.
- Chat-connected built-in tools, installed extension tools and installed skills. Skill plans can be recorded without execution.
- Each tool/skill execution requires separate explicit approval; model output cannot invoke tools automatically.
- Responsive React Chat Workspace and basic Android Compose Chat tab.
- New tests cover conversation persistence, Algorithms mode, model approval, tool approval, attachment handling, model catalog and plan-only skills.

## Chat Workspace limitations

- No cloud model provider integration or provider API keys in this increment; supported model execution is local LiteRT-LM only.
- No model weight downloader; model artifacts and CLI must be installed separately.
- PDF/Office extraction, OCR, vision, audio transcription and video understanding are not implemented. Non-text attachments are stored/downloadable only.
- Android currently has a basic chat screen; full conversation switcher, native file upload and model catalog controls are web/API features.
- Local inference is synchronous, not token-streamed. Real inference depends on CLI/model/driver compatibility and needs host testing.

## Validation status

The last successful baseline PR #9 CI run [45125919085](https://github.com/abdulraheemnohri/MOJO-AGENT-/actions/runs/45125919085) reported Python **92 passed**, frontend build passed and installer validation passed on implementation commit `c63b14807758d503881ff8c8807bc9bd2ad97a42`. PR #9 is merged into main.

The Chat Workspace branch has not yet received CI validation. Do not treat its Python, frontend or Android changes as tested until a fresh CI run passes on this branch/PR. Physical Android-device testing, Windows smoke tests, database restore drills and real LiteRT-LM inference remain separate release checks.

## Remaining release checks

1. Run Python tests, frontend production build, installer validation and Android APK workflow on the same feature PR head.
2. Install and exercise the Android Chat tab on a physical device.
3. Run Windows 10/11 install and backend/frontend smoke tests.
4. Exercise chat attachment size/type limits and database backup/restore with a disposable database.
5. Test local LiteRT-LM chat with a supported model and host; keep Algorithms mode as the safe default.
6. Add multimodal extraction only with verified model/runtime support and explicit size/privacy controls.
7. Create a tagged release only after CI and platform smoke tests pass.

## Local verification commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm install
npm run build
cd ..
gradle --no-daemon -p android :app:assembleDebug
```

Features are release-verified only when the matching code and CI evidence are available.
