import sqlite3
import pytest
from mojo_agent.database import DatabaseManager

def create_valid_db(path):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE app_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        conn.execute("CREATE TABLE workflows(id TEXT PRIMARY KEY,name TEXT,steps TEXT,created REAL,updated REAL)")
        for table in sorted(DatabaseManager.REQUIRED_TABLES - {"app_settings", "workflows", "workflow_jobs"}):
            conn.execute(f"CREATE TABLE {table}(id TEXT PRIMARY KEY)")
        conn.execute("""CREATE TABLE workflow_jobs(
            id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, workflow_name TEXT NOT NULL, steps TEXT NOT NULL,
            status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3,
            available_at REAL NOT NULL, created REAL NOT NULL, started REAL, finished REAL,
            result TEXT NOT NULL DEFAULT '[]', error TEXT NOT NULL DEFAULT '',
            cancel_requested INTEGER NOT NULL DEFAULT 0, worker_id TEXT NOT NULL DEFAULT '')""")

def test_migrations_are_idempotent(tmp_path):
    manager=DatabaseManager(str(tmp_path/"mojo.db"))
    first=manager.migrate()
    second=manager.migrate()
    assert first["version"]==2 and first["applied"]==[1,2]
    assert second["version"]==2 and second["applied"]==[]
    assert manager.status()["up_to_date"] is True

def test_backup_inspection_rejects_invalid_and_accepts_valid(tmp_path):
    path=tmp_path/"backup.sqlite3"
    create_valid_db(path)
    payload=path.read_bytes()
    info=DatabaseManager.inspect_payload(payload)
    assert info["valid"] and info["size_bytes"]==len(payload)
    with pytest.raises(ValueError):DatabaseManager.inspect_payload(b"not sqlite")

def test_restore_keeps_safety_copy_and_checks_checksum(tmp_path):
    target=tmp_path/"live.db"
    create_valid_db(target)
    manager=DatabaseManager(str(target))
    manager.migrate()
    source=tmp_path/"source.db"
    create_valid_db(source)
    with sqlite3.connect(source) as conn:
        conn.execute("INSERT INTO app_settings VALUES('theme','\"light\"')")
    payload=source.read_bytes()
    import hashlib
    with pytest.raises(ValueError):manager.restore_payload(payload,"0"*64)
    result=manager.restore_payload(payload,hashlib.sha256(payload).hexdigest())
    assert result["restored"] is True
    assert result["safety_backup"]
    assert manager.status()["version"]==2


def test_backup_inspection_rejects_incomplete_application_schema(tmp_path):
    path=tmp_path/"partial.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE app_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        conn.execute("CREATE TABLE workflows(id TEXT PRIMARY KEY)")
    with pytest.raises(ValueError, match="missing required MOJO AGENT tables"):
        DatabaseManager.inspect_payload(path.read_bytes())
