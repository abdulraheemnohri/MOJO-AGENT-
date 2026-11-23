# MOJO AGENT Chat Workspace

## What is included

The Chat Workspace is a persistent conversation UI backed by SQLite. It is available in the React dashboard and Android client and reuses the existing local LiteRT-LM runtime, built-in tools and declarative GitHub skills.

### Chat modes and model catalog

- **Algorithms:** works without a language model and returns a deterministic task breakdown. It is not presented as generative AI.
- **LiteRT-LM:** local inference using a local `.litertlm` bundle or a Hugging Face `owner/repository` ID supported by the separate LiteRT CLI wrapper.
- Saved model catalog with label, identifier, backend, add/select/remove controls.
- Model validation rejects invalid identifiers and nonexistent local bundle paths.
- Model registration does not download weights. Download/install the model and CLI separately.
- Cloud provider APIs and API keys are not enabled by this implementation.

### Conversations and history

- Create, list, rename, archive, delete and reopen conversations.
- Persistent messages with user, assistant, tool and system roles.
- Conversation title auto-generated from the first user message.
- Clear message history and fetch bounded message pages.
- Per-conversation mode and model selection.
- Global system instructions and bounded context window (2–30 messages).
- Messages and conversation metadata are stored in the same SQLite database and included in normal database backups.

### Attachments

The API accepts up to 10 MiB per file and allows text, Markdown, JSON, CSV, logs, PDF, DOCX, XLSX, PPTX, common images, audio and MP4 video. Files are stored in SQLite with a sanitized filename and bounded type allowlist.

**Current content-understanding boundary:** only UTF-8 text, Markdown, JSON, CSV and log files are extracted into the model prompt. Other allowed formats are stored and downloadable as attachments, but the current LiteRT-LM adapter does not provide image OCR/vision, audio transcription, video understanding or office/PDF extraction. The UI discloses this limitation; do not interpret file storage as multimodal inference.

### Tools and skills

- Built-in calculator and text statistics tools.
- Installed declarative GitHub extension tools.
- Installed GitHub skills with allowlisted operations.
- Skill planning can add a deterministic plan to the chat without executing operations.
- Tool/skill execution is a separate API call requiring approval for that exact operation.
- Model-generated text cannot trigger a tool call or bypass approval.
- Tool results are appended to the conversation as tool messages.

### Chat settings

- Default mode: Algorithms or LiteRT-LM. LiteRT-LM can only be selected as default after enabling the runtime.
- Global system prompt (up to 2,000 characters).
- Context history count (2–30 messages).
- Model identifier and CPU/GPU backend are selected in the model/runtime settings.
- Existing API bearer authentication middleware protects chat endpoints when authentication is enabled.

## API endpoints

Base path: `/api/v1`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/chat/models` | List built-in and saved local models |
| POST | `/chat/models` | Validate and add a local model entry |
| POST | `/chat/models/{id}/select` | Select the configured LiteRT-LM model |
| DELETE | `/chat/models/{id}` | Remove a model catalog entry (does not delete model files) |
| GET/POST | `/chat/conversations` | List/create conversations |
| GET/PATCH/DELETE | `/chat/conversations/{id}` | Read/update/delete a conversation |
| GET/DELETE | `/chat/conversations/{id}/messages` | Read/clear conversation history and attachments |
| GET | `/chat/conversations/{id}/export` | Export conversation, messages and attachment metadata as JSON |
| POST | `/chat/conversations/{id}/send` | Save user message and generate deterministic or local-model response |
| POST | `/chat/conversations/{id}/attachments?filename=...` | Upload an attachment as a raw request body |
| GET | `/chat/conversations/{id}/attachments` | List conversation attachments |
| GET | `/chat/attachments/{id}` | Download an attachment |
| GET | `/chat/tools` | List built-in tools, installed tools and skills |
| POST | `/chat/conversations/{id}/skills/{name}/plan` | Add a plan-only skill result to chat |
| POST | `/chat/conversations/{id}/tools/execute` | Run an approved built-in, extension or skill operation |

### Send request example

```json
{
  "content": "Summarize the notes",
  "mode": "litertlm",
  "model": "org/model",
  "backend": "cpu",
  "approved": true,
  "attachments": ["attachment-id"]
}
```

The `approved` field must be explicitly true for model inference. Tool execution has a separate `approved` field and is never implied by model approval.

## Android client

The native Compose app includes a Chat tab with conversation creation, history refresh, Algorithms/LiteRT-LM mode selection, per-message inference approval, built-in tool approval and editable chat system instructions/context size. Android file upload, full conversation switching/list UI and advanced model catalog controls remain web-dashboard/API features for now.

## Operational notes

- Schema migration v3 adds chat tables. Existing v2 databases are migrated on backend startup.
- Older backups remain eligible for restore and are migrated after restore; chat tables are not treated as mandatory in legacy backup inspection.
- Attachments are stored in SQLite, so large attachment collections increase backup size.
- The 10 MiB upload limit is per file, not a total database quota. Monitor disk usage and back up before deleting/replacing databases.
- Use API bearer authentication for trusted LAN use. TLS, rate limiting and public-internet hardening remain separate deployment requirements.
- Local inference is synchronous and bounded by the LiteRT-LM timeout. It is not streamed token-by-token in this version.
