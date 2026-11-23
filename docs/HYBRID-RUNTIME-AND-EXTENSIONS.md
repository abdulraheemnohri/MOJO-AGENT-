# Hybrid Agent Runtime and GitHub Extensions

## Operating modes

| Mode | Behavior | Network/model required |
|---|---|---|
| `algorithms` | Deterministic planner and algorithms only | No |
| `hybrid` | Deterministic plan first; optional LiteRT-LM provides advisory review | Optional local model or Hugging Face download |
| `litertlm` | Deterministic plan plus local-model output | Yes, configured LiteRT-LM runtime |

Algorithms is the default and remains fully functional without installing a model. Hybrid model output is advisory; it cannot execute tools, alter permissions or replace deterministic task ordering. All tool execution remains explicit and approval-gated.

## Configure through the dashboard

Open **Runtime & Models**:
1. Select Algorithms, Hybrid or LiteRT-LM.
2. Enable the optional runtime in the backend settings.
3. Enter a local `.litertlm` model path or Hugging Face `owner/repository`.
4. Choose CPU or GPU and timeout in the settings/API.
5. Save configuration.
6. Explicitly approve each model inference request.

Backend settings:
- `runtime_mode`: algorithms / hybrid / litertlm
- `litertlm_enabled`: false by default
- `litertlm_model`: local model path or Hugging Face repository ID
- `litertlm_backend`: cpu / gpu
- `litertlm_timeout_seconds`: 10–180

## Install LiteRT-LM

Windows PowerShell:
```powershell
.\scripts\install_litertlm.ps1
```

Linux/macOS/Termux:
```bash
chmod +x scripts/install_litertlm.sh
./scripts/install_litertlm.sh
```

These scripts install the native `litert-lm` runner into the existing MOJO virtual environment for local `.litertlm` bundles. They do not download a model. Model downloads can be large and need network access/storage. A local `.litertlm` file runs without network once downloaded. The Android APK does not bundle the CLI or model; inference runs on the machine hosting the Python backend.

### Hugging Face repository IDs

For a Hugging Face `owner/repository` ID, MOJO uses the official LiteRT CLI wrapper (`litert lm`) because it resolves repository IDs and handles cached conversion. Install the wrapper separately in a Python 3.13 environment as documented by Google:

```powershell
py -3.13 -m pip install --upgrade litert-cli-nightly
```

Set `MOJO_LITERT_CLI_BIN` to the full path of the `litert` executable if it is not on the backend process PATH. Local bundle inference continues to use `litert-lm` and does not require the wrapper. If the wrapper is not installed, MOJO returns a clear setup error instead of invoking the native CLI with incomplete Hugging Face arguments.

## API

- `GET /api/v1/agent/runtime`
- `POST /api/v1/agent/run` — goal, optional mode/model/backend and explicit approval
- `GET /api/v1/litertlm/status`
- `POST /api/v1/litertlm/run`
- `PATCH /api/v1/settings` — validated runtime preferences

## GitHub skill and tool installation

Open **Extensions Hub** and enter:
- repository: `owner/repository`
- ref: branch, tag or preferably immutable commit SHA
- manifest path: `mojo-extension.json` or a custom JSON path

Preview the manifest and inspect its repository, version, description and SHA-256 before installing.

### Skill manifest

```json
{
  "schema": "mojo.extension.v1",
  "kind": "skill",
  "name": "project-review",
  "version": "1.0.0",
  "description": "Review a software project",
  "instructions": "Review the supplied project context. Identify risks and propose tests.",
  "tools": ["text_stats"]
}
```

### Tool manifest

```json
{
  "schema": "mojo.extension.v1",
  "kind": "tool",
  "name": "uppercase-text",
  "version": "1.0.0",
  "description": "Convert input text to uppercase",
  "operation": "uppercase",
  "input_schema": {"text": "string"}
}
```

Only these built-in declarative operations are currently supported:
- `text_stats`
- `uppercase`
- `lowercase`
- `word_count`
- `calculator`

A GitHub skill is stored as instructions and a list of allowed built-in tools. A skill run returns instructions and a deterministic task plan; it does not autonomously invoke tools. Installed tools still require explicit approval for every execution.

### Security restrictions

- Only public GitHub raw JSON manifests are fetched.
- Manifest size is limited to 128 KiB.
- Repository, ref and path inputs are validated.
- Python source, shell scripts, executables, binaries and GitHub Actions are never installed or run.
- Arbitrary code hooks and dynamic imports are not supported.
- Tool operations are hard-coded in MOJO AGENT and are approval-gated.
- Prefer pinning an immutable commit SHA rather than a moving branch.
- Review manifest content and repository ownership before installation.

This is a controlled declarative extension system, not a general-purpose plugin runtime.


## Skill execution engine

An installed skill may invoke only the built-in operations declared in its JSON manifest. The Android and web clients submit one operation at a time; the backend validates the skill allowlist and requires an explicit approval flag for every execution. No skill can run arbitrary repository code, shell commands, Python modules or network actions.

New endpoints:
- `POST /api/v1/skills/{name}/execute` — operation, arguments and explicit approval
- `GET /api/v1/skills/{name}/history` — bounded execution history (maximum 100 records)

Execution history records the operation, status, timestamp and input shape/length metadata rather than storing raw input text. The immediate execution response contains the operation result. An operation outside the skill's allowlist is rejected.
