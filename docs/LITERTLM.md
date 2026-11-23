# Optional LiteRT-LM CLI

MOJO AGENT remains algorithm-first and works without a model. LiteRT-LM is an optional local inference runtime, not a replacement for the planner, workflows, memory, or safety policy.

## Install

The upstream CLI requires Python 3.10+. Activate the MOJO AGENT virtual environment.

Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade litert-lm
litert-lm --help
```

Linux/macOS/Termux:
```bash
source .venv/bin/activate
python -m pip install --upgrade litert-lm
litert-lm --help
```

Google also documents `uvx litert-lm` and `uv tool install litert-lm`. See [official installation](https://developers.google.cn/edge/litert-lm/cli/installation).

## Commands

```bash
mojo-agent litertlm status
mojo-agent litertlm run --model ./models/model.litertlm --prompt "Explain this task" --backend cpu --approved
mojo-agent litertlm run --model litert-community/gemma-4-E2B-it-litert-lm --prompt "Hello" --backend gpu --approved
mojo-agent litertlm benchmark --model ./models/model.litertlm --approved
```

Inference and benchmark require explicit `--approved`. Local model files must end in `.litertlm`; Hugging Face IDs use `owner/repository`. Hugging Face mode may download model files and requires network access and storage. Local model files can run offline once present.

## Settings and API

- `GET /api/v1/litertlm/status`
- `POST /api/v1/litertlm/run` with `model`, `prompt`, `backend`, and `approved: true`
- `POST /api/v1/litertlm/benchmark` with `model` and `approved: true`
- Settings: `litertlm_enabled` (default false), `litertlm_backend` (cpu/gpu), `litertlm_timeout_seconds` (10–180).

The adapter accepts no arbitrary CLI arguments and never invokes a shell. Prompts are limited to 6,000 characters and output to 12,000 characters. CPU is the default; GPU support depends on drivers, model and device.

## Gemma 4 E2B quick start

```bash
litert-lm run --from-huggingface-repo=litert-community/gemma-4-E2B-it-litert-lm gemma-4-E2B-it.litertlm --prompt="What is the capital of France?"
```

See [CLI usage](https://developers.google.cn/edge/litert-lm/cli/usage) and [LiteRT-LM overview](https://developers.google.cn/edge/litert-lm/overview). Check device RAM/storage requirements before downloading, especially on 6 GB Android devices.

## Boundaries

The CLI integration runs on the backend host only. It does not bundle LiteRT-LM or a model into the Android APK. Native Android embedding is a separate future integration. Do not expose this development API to untrusted networks; remote authentication and TLS are not configured.
