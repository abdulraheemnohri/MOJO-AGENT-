# MOJO AGENT — roadmap after core implementation

This roadmap describes work that is still outstanding. Features already merged into `main` are not listed as future work.

## Implemented foundation

- Algorithm-first Python/FastAPI runtime and deterministic planner.
- SQLite memory, knowledge graph, analytics, settings and bounded evolution.
- Approval-gated built-in tools and declarative workflows.
- Visual workflow composition, templates and prior-step conditions.
- Durable single-host SQLite job queue, retry/recovery/cancellation and opt-in worker.
- Schema migrations, backup inspection and loopback-only restore.
- Optional bearer-token API authentication.
- Optional approval-gated LiteRT-LM runtime.
- Declarative JSON-only GitHub extensions and approval-gated skill operations.
- React/Vite dashboard and Kotlin/Compose Android backend client.
- Windows, POSIX and Termux setup scripts.

## P0 — release integrity and safety

1. Fix all failing CI jobs and require Python, frontend, installer and Android workflows to pass on the same final commit.
2. Add CI coverage for LiteRT-LM API schemas, workflow conditions, queue recovery, backup/restore and authentication edge cases.
3. Add dependency vulnerability scanning and a dependency update policy.
4. Add API rate limiting and configurable request/body limits beyond the backup endpoint.
5. Document a secure private-LAN deployment profile; do not permit public internet exposure without TLS, authentication and operational hardening.
6. Test backup/restore and interrupted-job recovery against disposable databases on Windows and Linux.

## P1 — client quality and maintainability

1. Split React `App.tsx` into feature routes/components and add component tests.
2. Split the Android single-activity UI into feature modules/screens.
3. Add native Android file selection and structured list/detail experiences.
4. Add loading, empty, error, retry and offline states to all client pages.
5. Add accessibility semantics, keyboard navigation verification and screen-reader checks.
6. Add UI automation for Android and browser workflows.

## P2 — operations and packaging

1. Add a native Windows installer only if a signed installer and update/uninstall lifecycle can be maintained.
2. Add signed release APK/AAB builds and reproducible release metadata.
3. Add structured log export, log rotation and configurable retention without storing secrets or request bodies.
4. Add queue idempotency keys and clearer operator controls for stuck jobs; preserve the current single-host SQLite boundary unless a real distributed backend is designed.
5. Add scheduled database backup with retention and restore drills.

## P3 — optional model/runtime maturity

1. Verify real LiteRT-LM inference on supported Windows/Linux host configurations and publish a tested model/runtime matrix.
2. Measure CPU/GPU memory, latency and thermal behavior before recommending models.
3. Keep model output advisory and keep tool execution behind explicit operator approval.
4. Add model download integrity checks, disk-space preflight and model lifecycle controls.
5. Keep Algorithms mode fully usable with no model installed.

## Explicit non-goals for this release

- No unrestricted self-modifying source code or self-updating control core.
- No arbitrary shell/script/binary extensions.
- No automatic tool execution from LLM output.
- No public cloud dependency or required paid API.
- No claim of distributed job execution, production remote security or native iOS support.

## Release gate

A release is complete only when all CI workflows pass on the same commit, Windows install/run smoke tests pass, Android APK installs and connects on a physical device, backup/restore is exercised on a disposable database, and optional inference is verified on the advertised host/model combination.