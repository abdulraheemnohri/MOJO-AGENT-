# MOJO AGENT implementation status

## Implemented
- Cross-platform Python reference API, React dashboard and Android Compose client.
- SQLite persistence for memory, workflows, knowledge graph, analytics, settings and evolution candidates/champion.
- Atomic memory batch import and JSON export.
- Goal planner, deterministic algorithms, bounded strategy evolution and manual candidate validation/approval.
- Allowlisted tools with mandatory approval; shell execution disabled.
- Workflow CRUD, synchronous execution and execution history.
- Knowledge graph node/edge CRUD and search.
- Safe diagnostics and privacy-limited API request telemetry.
- Dashboard workflow editing/history, memory search, graph relationship management, analytics and theme controls.
- Android screens for runtime, planning, memory, workflows, evolution, knowledge, tools, analytics, security, diagnostics and settings.

## Deliberate limitations
- No LLM integration by design.
- Main-branch baseline remains synchronous; durable queue and opt-in worker are implemented on the feature branch, but not merged into main.
- Android still uses a single Compose activity and a raw JSON response panel; native file pickers, full workflow editor and structured list rendering are incomplete.
- Native Mojo compiler compatibility and Windows installer packaging require separate toolchain validation.
- API defaults to loopback; physical-device access should use a trusted local connection such as ADB reverse.


## Additional feature branch implementation (pending CI/merge)
- Algorithms, Hybrid and LiteRT-LM agent modes; Algorithms remains the default and needs no model.
- Optional LiteRT-LM CLI adapter with CPU/GPU selection, bounded timeout, local `.litertlm` or Hugging Face model ID, inference approval and benchmark endpoint.
- Persistent runtime mode/model/backend settings with validation.
- GitHub extension registry for declarative skill/tool JSON manifests, preview hash verification, install/list/uninstall and skill plan endpoint.
- Frontend Runtime & Models and Extensions Hub pages; installed GitHub tools/skills are surfaced in the capability registry.
- Android Runtime & Models and Extensions Hub screens with model configuration and GitHub manifest preview/install.
- Example manifests and optional Windows/POSIX LiteRT-LM CLI installer scripts.

### Limitations of this feature branch
- LiteRT-LM executes on the backend host, not inside the Android APK; Android is a remote local-network client.
- Hugging Face model loading may download large artifacts and requires network/storage. A local `.litertlm` file is needed for offline inference.
- GPU availability depends on the host runtime, drivers and model. CPU is the portable baseline.
- GitHub extension manifests are public JSON only. No arbitrary code execution, dynamic imports, shell hooks or binary extensions.
- Skills currently return their instructions and deterministic task plan; tools are not auto-executed by a skill.
- All features in this section are pending the branch CI run and review; do not treat them as merged into main until PR merge.


### Skill execution engine (pending branch CI/review)
- Installed skills can execute only manifest-allowlisted built-in operations, one operation per request.
- Explicit approval is required for every execution; the backend rejects operations outside the skill allowlist.
- SQLite stores bounded skill execution history with status and input shape/length metadata; raw input text is not persisted.
- Web and Android clients expose skill operation execution and history.
- LiteRT-LM passes Hugging Face repository IDs directly to the CLI rather than guessing a model artifact filename.


### Durable workflow engine and database recovery (feature branch; CI pending)
- Added a persistent SQLite job queue with workflow-step snapshots, bounded queue capacity, attempt counters, exponential retry delay and per-job status/result history.
- Added cancellation for queued jobs and cooperative cancellation checks between running workflow steps.
- Added worker claim locking, bounded worker batches, interrupted-job recovery on backend startup and an opt-in background daemon.
- Added worker settings: enabled flag, polling interval, batch size and default retry attempts.
- Added job queue/status/cancel/retry/manual worker APIs and dashboard + Android workflow controls.
- Added SQLite schema version tracking and idempotent migration metadata.
- Added loopback-only backup inspection and restore with integrity checks, optional SHA-256 verification, size cap, pre-restore safety backup and WAL handling.
- Added database status and restore controls to the web settings page and schema diagnostics to Android.
- Distributed queue coordination, forced interruption of a currently executing step and production multi-process database operation remain out of scope. TLS termination is still a deployment responsibility; do not expose the backend directly to the public internet.


### Local API security and Windows startup (feature branch)
- Added opt-in bearer-token authentication for all API routes except health, security-status and loopback-only initial token bootstrap.
- Generates 40-byte random URL-safe tokens, stores only salted SHA-256 digests, uses constant-time digest comparison, and supports authenticated token rotation and revocation.
- Initial token creation, rotation and revocation are loopback-restricted. CORS allows Authorization headers and preflight requests.
- Web Security Center supports initial setup, token rotation, revocation and session-only token storage. Android accepts a bearer token, stores it in app-private preferences and supports loopback initial setup.
- Added a per-user Windows Task Scheduler installer and uninstall script; it starts the backend at logon on 127.0.0.1 without Docker or administrator privileges.
- The dashboard retains its responsive dark/light theme, compact/comfortable density, keyboard navigation, mobile drawer and reduced-motion support; new security cards follow the existing adaptive design system.
- TLS certificates, public internet exposure, multi-user RBAC and distributed worker coordination are not enabled by this change.


### Visual workflow builder and adaptive interface
- Replaced the single-text workflow form with a multi-step visual composer supporting text output, text statistics, calculator and safe template/data-mapping steps.
- Supports up to 50 ordered steps, add/remove, move up/down, editing existing workflows, and starter/analysis templates.
- Adds conditional execution against earlier step results with equals, not_equals, contains and truthy operators. False conditions are recorded as skipped; the same validation and behavior apply to direct and queued runs. The visual editor exposes prior-step selection and expected-value controls.
- Template mappings and conditions can reference only earlier steps. No arbitrary expression evaluator, shell command, script, dynamic import or user-supplied code is executed.
- Added responsive step cards and mobile stacking styles consistent with MOJO's design system.


### Conditional workflow execution (feature branch; CI pending)
- Added optional per-step conditions referencing an earlier step index.
- Supported operators: equals, not_equals, contains and truthy. Non-truthy comparisons use bounded text values.
- False conditions create explicit skipped step results and do not invoke the step operation.
- The same deterministic evaluator is used by direct workflow runs and durable queue jobs.
- Frontend step cards provide condition enable/disable, source-step selection, operator selection and expected text.
- Automated tests cover false/true conditions, validation rejection and immutable queued workflow snapshots.
