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
- Workflow runner is synchronous; no background scheduler or distributed queue.
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
