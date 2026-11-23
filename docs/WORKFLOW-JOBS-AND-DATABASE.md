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

The worker stops with the backend process. At startup, interrupted jobs are recovered to the queue if attempts remain; exhausted jobs are marked failed. For reliable always-on operation, run the backend under an operating-system service manager (Windows Task Scheduler / NSSM, or systemd on Linux). The worker is not a distributed multi-host queue and should use one active backend process against a local SQLite database.

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
- Job queue endpoints are local API capabilities; remote authentication/TLS is still a separate deployment requirement. Do not expose the backend port directly to the public internet.
