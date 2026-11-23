"""SQLite schema versioning, integrity checks and safe local restore helpers."""
import hashlib
import os
import sqlite3
import tempfile
import time
import uuid
from pathlib import Path

class DatabaseManager:
    CURRENT_VERSION = 3
    REQUIRED_TABLES = {
        "app_settings", "memories", "workflows", "workflow_runs", "workflow_schedules",
        "workflow_jobs", "analytics_events", "kg_nodes", "kg_edges",
        "evolution_candidates", "evolution_state", "installed_extensions", "skill_executions",\n        
    }
    def __init__(self, path="data/mojo_agent.sqlite3"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.path, timeout=15)

    def migrate(self):
        applied = []
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at REAL NOT NULL)")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version < 1:
                conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES(1,'baseline',?)", (time.time(),))
                conn.execute("PRAGMA user_version=1")
                applied.append(1)
                version = 1
            if version < 2:
                conn.execute("""CREATE TABLE IF NOT EXISTS workflow_jobs(
                    id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, workflow_name TEXT NOT NULL, steps TEXT NOT NULL,
                    status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3,
                    available_at REAL NOT NULL, created REAL NOT NULL, started REAL, finished REAL,
                    result TEXT NOT NULL DEFAULT '[]', error TEXT NOT NULL DEFAULT '',
                    cancel_requested INTEGER NOT NULL DEFAULT 0, worker_id TEXT NOT NULL DEFAULT '')""")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_jobs_queue ON workflow_jobs(status,available_at,created)")
                conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES(2,'durable_workflow_jobs',?)", (time.time(),))
                conn.execute("PRAGMA user_version=2")
                applied.append(2)
                version = 2
            if version < 3:
                conn.execute("""CREATE TABLE IF NOT EXISTS chat_conversations(
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, mode TEXT NOT NULL DEFAULT 'algorithms',
                    model TEXT NOT NULL DEFAULT '', system_prompt TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL, updated_at REAL NOT NULL, archived INTEGER NOT NULL DEFAULT 0)""")
                conn.execute("""CREATE TABLE IF NOT EXISTS chat_messages(
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL, content TEXT NOT NULL, metadata TEXT NOT NULL DEFAULT '{}', created_at REAL NOT NULL)""")
                conn.execute("""CREATE TABLE IF NOT EXISTS chat_attachments(
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
                    message_id TEXT, filename TEXT NOT NULL, extension TEXT NOT NULL, content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL, content BLOB NOT NULL, created_at REAL NOT NULL)""")
                conn.execute("""CREATE TABLE IF NOT EXISTS chat_models(
                    id TEXT PRIMARY KEY, label TEXT NOT NULL, model_id TEXT NOT NULL UNIQUE,
                    backend TEXT NOT NULL DEFAULT 'cpu', added_at REAL NOT NULL)""")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id,created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_conversations_updated ON chat_conversations(updated_at DESC)")
                conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES(3,'persistent_chat_workspace',?)", (time.time(),))
                conn.execute("PRAGMA user_version=3")
                applied.append(3)
        return {"version": self.status()["version"], "applied": applied}

    def status(self):
        with self.connect() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
            tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            migrations = []
            if "schema_migrations" in tables:
                migrations = [{"version": r[0], "name": r[1], "applied_at": r[2]} for r in conn.execute("SELECT version,name,applied_at FROM schema_migrations ORDER BY version")]
        return {"version": version, "current_version": self.CURRENT_VERSION, "up_to_date": version == self.CURRENT_VERSION, "integrity": integrity, "tables": tables, "migrations": migrations}

    @staticmethod
    def inspect_payload(payload, max_bytes=128 * 1024 * 1024):
        if not isinstance(payload, (bytes, bytearray)) or not payload:
            raise ValueError("backup payload is empty")
        if len(payload) > max_bytes:
            raise ValueError("backup exceeds the 128 MiB restore limit")
        digest = hashlib.sha256(payload).hexdigest()
        fd, path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        try:
            Path(path).write_bytes(payload)
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10) as conn:
                integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
                if integrity != "ok":
                    raise ValueError("backup integrity check failed")
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                missing = DatabaseManager.REQUIRED_TABLES - tables
                if missing:
                    names = ", ".join(sorted(missing))
                    raise ValueError("backup is missing required MOJO AGENT tables: " + names)
                version = conn.execute("PRAGMA user_version").fetchone()[0]
            return {"valid": True, "sha256": digest, "size_bytes": len(payload), "schema_version": version, "tables": sorted(tables)}
        except sqlite3.DatabaseError as exc:
            raise ValueError("backup is not a valid SQLite database") from exc
        finally:
            try: os.unlink(path)
            except OSError: pass

    def restore_payload(self, payload, expected_sha256=None):
        info = self.inspect_payload(payload)
        digest = hashlib.sha256(payload).hexdigest()
        if expected_sha256 and digest.lower() != expected_sha256.lower():
            raise ValueError("backup SHA-256 does not match the supplied checksum")
        parent = str(Path(self.path).parent)
        fd, temp_path = tempfile.mkstemp(prefix="mojo-restore-", suffix=".sqlite3", dir=parent)
        os.close(fd)
        backup_path = self.path + ".pre-restore-" + str(int(time.time())) + "-" + uuid.uuid4().hex[:8] + ".bak"
        replaced = False
        try:
            Path(temp_path).write_bytes(payload)
            if os.path.exists(self.path):
                with sqlite3.connect(self.path, timeout=15) as source:
                    try: source.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    except sqlite3.DatabaseError: pass
                    with sqlite3.connect(backup_path) as target:
                        source.backup(target)
            for suffix in ("-wal", "-shm"):
                sidecar = self.path + suffix
                if os.path.exists(sidecar): os.unlink(sidecar)
            os.replace(temp_path, self.path)
            replaced = True
            migration = self.migrate()
            return {**info, "restored": True, "safety_backup": os.path.basename(backup_path) if os.path.exists(backup_path) else None, "migration": migration}
        except Exception:
            if replaced and os.path.exists(backup_path):
                os.replace(backup_path, self.path)
            raise
        finally:
            try:
                if os.path.exists(temp_path): os.unlink(temp_path)
            except OSError: pass
