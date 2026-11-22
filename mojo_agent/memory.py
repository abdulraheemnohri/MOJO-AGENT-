"""Persistent, bounded SQLite memory store."""
import sqlite3
from pathlib import Path

KINDS = {"working", "short_term", "long_term", "episodic", "semantic", "experience"}

class MemoryStore:
    def __init__(self, path="data/mojo_agent.sqlite3"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS memories(
                id INTEGER PRIMARY KEY, kind TEXT NOT NULL, content TEXT NOT NULL,
                importance REAL NOT NULL DEFAULT .5,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            columns = {row[1] for row in db.execute("PRAGMA table_info(memories)")}
            if "updated_at" not in columns:
                db.execute("ALTER TABLE memories ADD COLUMN updated_at TEXT")

    def _db(self):
        return sqlite3.connect(self.path, timeout=10)

    def add(self, content, kind="episodic", importance=.5):
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Memory cannot be empty")
        if len(content) > 10000:
            raise ValueError("Memory cannot exceed 10000 characters")
        if kind not in KINDS:
            raise ValueError("Unsupported memory kind")
        if not 0 <= float(importance) <= 1:
            raise ValueError("importance must be between 0 and 1")
        with self._db() as db:
            cur = db.execute(
                "INSERT INTO memories(kind,content,importance) VALUES(?,?,?)",
                (kind, content.strip(), float(importance)))
            return cur.lastrowid

    def search(self, query="", limit=20):
        if not 1 <= limit <= 200:
            raise ValueError("limit must be 1..200")
        with self._db() as db:
            rows = db.execute(
                """SELECT id,kind,content,importance,created_at,updated_at
                   FROM memories WHERE content LIKE ? ORDER BY importance DESC,id DESC LIMIT ?""",
                (f"%{query}%", limit)).fetchall()
        keys = ("id", "kind", "content", "importance", "created_at", "updated_at")
        return [dict(zip(keys, row)) for row in rows]

    def update(self, memory_id, content=None, kind=None, importance=None):
        current = next((m for m in self.search("", 200) if m["id"] == memory_id), None)
        if current is None:
            return None
        content = current["content"] if content is None else content
        kind = current["kind"] if kind is None else kind
        importance = current["importance"] if importance is None else importance
        if not isinstance(content, str) or not content.strip() or len(content) > 10000:
            raise ValueError("content must contain 1..10000 characters")
        if kind not in KINDS:
            raise ValueError("Unsupported memory kind")
        if not 0 <= float(importance) <= 1:
            raise ValueError("importance must be between 0 and 1")
        with self._db() as db:
            db.execute("""UPDATE memories SET content=?,kind=?,importance=?,
                updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (content.strip(), kind, float(importance), memory_id))
        return next(m for m in self.search("", 200) if m["id"] == memory_id)

    def delete(self, memory_id):
        with self._db() as db:
            cur = db.execute("DELETE FROM memories WHERE id=?", (memory_id,))
            return cur.rowcount == 1

    def export_all(self):
        return self.search("", 200)
