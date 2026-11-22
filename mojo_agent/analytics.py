"""Persistent, bounded and inspectable runtime analytics."""
import json
import sqlite3
import time
from pathlib import Path

class Analytics:
    def __init__(self, path="data/mojo_agent.sqlite3", retention=5000):
        self.path = path
        self.retention = max(100, min(int(retention), 50000))
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS analytics_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                detail TEXT NOT NULL,
                created REAL NOT NULL
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_event_time ON analytics_events(event, created DESC)")

    def db(self):
        return sqlite3.connect(self.path, timeout=10)

    def record(self, event, detail=None):
        if not isinstance(event, str) or not event.strip() or len(event) > 100:
            raise ValueError("event must contain 1–100 characters")
        try:
            payload = json.dumps(detail or {}, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("event detail must be JSON-serializable") from exc
        if len(payload) > 10000:
            raise ValueError("event detail exceeds 10000 characters")
        now = time.time()
        with self.db() as conn:
            conn.execute("INSERT INTO analytics_events(event,detail,created) VALUES(?,?,?)",
                         (event.strip(), payload, now))
            conn.execute("""DELETE FROM analytics_events WHERE id NOT IN
                         (SELECT id FROM analytics_events ORDER BY id DESC LIMIT ?)""",
                         (self.retention,))
        return {"event": event.strip(), "time": now}

    def summary(self, limit=20, event=None):
        limit = max(1, min(int(limit), 200))
        if event is not None and (not isinstance(event, str) or not event.strip() or len(event) > 100):
            raise ValueError("event filter must contain 1–100 characters")
        with self.db() as conn:
            if event:
                rows = conn.execute("SELECT event,detail,created FROM analytics_events WHERE event=? ORDER BY id DESC LIMIT ?",
                                    (event.strip(), limit)).fetchall()
                total = conn.execute("SELECT COUNT(*) FROM analytics_events WHERE event=?", (event.strip(),)).fetchone()[0]
                grouped = conn.execute("SELECT event,COUNT(*) FROM analytics_events WHERE event=? GROUP BY event",
                                        (event.strip(),)).fetchall()
            else:
                rows = conn.execute("SELECT event,detail,created FROM analytics_events ORDER BY id DESC LIMIT ?",
                                    (limit,)).fetchall()
                total = conn.execute("SELECT COUNT(*) FROM analytics_events").fetchone()[0]
                grouped = conn.execute("SELECT event,COUNT(*) FROM analytics_events GROUP BY event ORDER BY COUNT(*) DESC").fetchall()
        return {
            "events_total": total,
            "counts": {name: count for name, count in grouped},
            "recent": [{"event": row[0], "detail": json.loads(row[1]), "time": row[2]} for row in rows],
            "retention_limit": self.retention
        }
