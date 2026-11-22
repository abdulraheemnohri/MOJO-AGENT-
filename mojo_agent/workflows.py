"""Safe local workflow registry and deterministic runner."""
import json, sqlite3, time, uuid
from pathlib import Path

ALLOWED_STEP_TYPES = {"text", "calculator", "text_stats"}

class WorkflowStore:
    def __init__(self, path="data/mojo_agent.sqlite3"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as c:
            c.execute("CREATE TABLE IF NOT EXISTS workflows(id TEXT PRIMARY KEY,name TEXT,steps TEXT,created REAL,updated REAL)")
            c.execute("CREATE TABLE IF NOT EXISTS workflow_runs(id TEXT PRIMARY KEY,workflow_id TEXT,status TEXT,results TEXT,started REAL,finished REAL)")

    def db(self):
        return sqlite3.connect(self.path, timeout=10)

    def _validate(self, name, steps):
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ValueError("workflow name must contain 1–120 characters")
        if not isinstance(steps, list) or not 1 <= len(steps) <= 50:
            raise ValueError("workflow needs 1–50 steps")
        if any(not isinstance(s, dict) or s.get("type") not in ALLOWED_STEP_TYPES for s in steps):
            raise ValueError("unsupported workflow step")

    def _row(self, r):
        return {"id": r[0], "name": r[1], "steps": json.loads(r[2]), "created": r[3], "updated": r[4]}

    def create(self, name, steps):
        self._validate(name, steps)
        ident, now = str(uuid.uuid4()), time.time()
        with self.db() as c:
            c.execute("INSERT INTO workflows VALUES(?,?,?,?,?)", (ident, name.strip(), json.dumps(steps), now, now))
        return self.get(ident)

    def get(self, ident):
        with self.db() as c:
            r = c.execute("SELECT id,name,steps,created,updated FROM workflows WHERE id=?", (ident,)).fetchone()
        return self._row(r) if r else None

    def list(self):
        with self.db() as c:
            rows = c.execute("SELECT id,name,steps,created,updated FROM workflows ORDER BY updated DESC").fetchall()
        return [self._row(r) for r in rows]

    def update(self, ident, name, steps):
        self._validate(name, steps)
        with self.db() as c:
            cur = c.execute("UPDATE workflows SET name=?,steps=?,updated=? WHERE id=?",
                            (name.strip(), json.dumps(steps), time.time(), ident))
            return cur.rowcount == 1

    def delete(self, ident):
        with self.db() as c:
            c.execute("DELETE FROM workflow_runs WHERE workflow_id=?", (ident,))
            cur = c.execute("DELETE FROM workflows WHERE id=?", (ident,))
            return cur.rowcount == 1

    def run(self, ident, tools):
        w = self.get(ident)
        if not w:
            raise KeyError("workflow not found")
        rid, started, results, status = str(uuid.uuid4()), time.time(), [], "completed"
        try:
            for i, step in enumerate(w["steps"]):
                kind = step["type"]
                if kind == "text":
                    result = str(step.get("value", ""))
                elif kind == "calculator":
                    result = tools.execute(kind, {"expression": step.get("expression", "")}, approved=True)
                else:
                    result = tools.execute(kind, {"text": step.get("text", "")}, approved=True)
                results.append({"step": i, "type": kind, "result": result})
        except Exception as exc:
            status = "failed"
            results.append({"error": str(exc)})
        with self.db() as c:
            c.execute("INSERT INTO workflow_runs VALUES(?,?,?,?,?,?)",
                      (rid, ident, status, json.dumps(results), started, time.time()))
        return {"id": rid, "workflow_id": ident, "status": status, "results": results}

    def history(self, limit=50):
        with self.db() as c:
            rows = c.execute("SELECT id,workflow_id,status,results,started,finished FROM workflow_runs ORDER BY started DESC LIMIT ?",
                             (max(1, min(limit, 200)),)).fetchall()
        return [{"id": r[0], "workflow_id": r[1], "status": r[2], "results": json.loads(r[3]),
                 "started": r[4], "finished": r[5]} for r in rows]
