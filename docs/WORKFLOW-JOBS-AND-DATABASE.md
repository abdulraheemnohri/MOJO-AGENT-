# Workflow Jobs, Background Worker and Database Recovery

## Durable workflow jobs

The existing workflow editor remains deterministic and local. Use `POST /api/v1/workflows/{workflow_id}/enqueue` to create a durable job. The job stores a snapshot of the workflow steps, so later edits do not silently change work already queued.

- Queue limit: 500 active jobs.
- Maximum steps per workflow: 50.
- Retry attempts: 1–10 (default 3).
- Retry delay: exponential, capped at 300 seconds.
- Worker batch: 1–10 jobs.
- Job history is stored in SQLite and survives backend restarts.

Job endpoints:
- `GET /api/v1/workflow-jobs?limit=100&status=queued`
- `GET /api/v1/workflow-jobs/{job_id}`
- `POST /api/v1/workflow-jobs/{job_id}/cancel`
- `POST /api/v1/workflow-jobs/{job_id}/retry`
- `POST /api/v1/worker/tick` — explicit one-shot worker cycle
- `GET /api/v1/worker/status`

A cancellation request immediately cancels queued work. A running job checks the cancellation flag between steps; a currently executing individual step is not forcibly interrupted.

## Background worker

The backend starts a lightweight daemon thread. It remains idle unless `worker_enabled=true`. Configure through Settings or `PATCH /api/v1/settings`:

```json
{
  "worker_enabled": true,
  "worker_poll_seconds": 2,
  "worker_batch_size": 3,
  "workflow_max_attempts": 3
}
```

The worker also checks and executes due recurring schedules on each enabled cycle. The worker stops with the backend process. At startup, interrupted jobs are recovered to the queue if attempts remain; exhausted jobs are marked failed. For reliable always-on operation, run the backend under an operating-system service manager (Windows Task Scheduler / NSSM, or systemd on Linux). The worker is not a distributed multi-host queue and should use one active backend process against a local SQLite database.

## Database schema and recovery

MOJO now tracks SQLite schema version using `PRAGMA user_version` and a `schema_migrations` table. Migrations are idempotent and run at API startup. The durable job queue migration is version 2.

- `GET /api/v1/database/status` — schema version, applied migrations, tables and integrity.
- `GET /api/v1/backup/export` — consistent SQLite backup; loopback only.
- `POST /api/v1/backup/inspect` — validate a raw SQLite backup payload; loopback only.
- `POST /api/v1/backup/restore` — restore a verified SQLite backup; loopback only.

Restore constraints:
- Maximum upload size: 128 MiB.
- SQLite quick integrity check must pass.
- Backup must contain core MOJO tables.
- Optional `X-Backup-SHA256` header is checked against the uploaded bytes.
- The current database is backed up to a timestamped `.pre-restore-*.bak` file before replacement.
- WAL/SHM sidecars are checkpointed/cleared before atomic replacement.
- Schema migrations are re-applied after restore.

**Operational recommendation:** stop the backend before restoring a production database. Restore is restricted to loopback requests, but stopping the service avoids concurrent writers and stale in-memory objects. Keep a separate copy of the original backup.

## Security boundaries

- Workflow steps are declarative and limited to built-in `text`, `calculator`, and `text_stats` operations.
- No shell commands, Python source, arbitrary plugin code or remote execution.
- Tool approval requirements are not configurable off.
- API bearer-token authentication is optional but recommended for LAN clients. Initial token setup, rotation and revocation are loopback-restricted. Do not expose the backend port directly to the public internet; configure HTTPS/TLS termination before any trusted remote access.


## Restore validation hardening

Backup inspection and restore now require the complete set of application tables (settings, memory, workflows and job history, analytics, knowledge graph, evolution state, and installed extensions). A SQLite file with only a subset of MOJO tables is rejected before replacing the live database. HTTP backup uploads are consumed incrementally and stopped as soon as the 128 MiB limit is exceeded, including requests without a `Content-Length` header. Keep the backend stopped during a production restore and retain the generated pre-restore safety copy.

## API bearer-token security

Authentication is disabled by default to preserve the existing loopback developer workflow. Enable it from the Security Center while connected to the backend host:

1. Open **Security** in the web dashboard or Android app.
2. Create the initial token from a loopback connection.
3. Save the returned token in the web session or Android app's private preferences.
4. All API routes except health, security status and loopback-only bootstrap require Authorization: Bearer token.
5. Rotate from an authenticated local session when the token needs replacement; the old token stops working immediately. Revoke to disable token enforcement.

The token contains 320 bits of random entropy. Only a salted SHA-256 digest is stored in SQLite and compared in constant time; the raw token is returned only at creation/rotation. The browser stores its token in session storage, not persistent local storage. Android stores its token in app-private preferences. Treat either device as trusted while a token is configured.

This is a single-token local access control layer, not multi-user identity or role-based access control. TLS is not automatically configured. Never expose the raw backend port publicly.

## Windows per-user backend startup

Run from PowerShell in the project directory:

    Set-ExecutionPolicy -Scope Process Bypass
    .\scripts\install_windows_service.ps1
    Start-ScheduledTask -TaskName MOJO-AGENT-Backend

The task starts the Python backend at user logon, bound to 127.0.0.1. It runs as the current user, requires no Docker or administrator privileges, and uses .venv\Scripts\python.exe when available. Remove the task without deleting project data:

    .\scripts\uninstall_windows_service.ps1
