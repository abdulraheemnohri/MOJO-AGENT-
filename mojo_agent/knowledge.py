"""Inspectable SQLite knowledge graph with safe CRUD operations."""
import json, sqlite3, time, uuid
from pathlib import Path

class KnowledgeGraph:
    def __init__(self, path="data/mojo_agent.sqlite3"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as c:
            c.execute("CREATE TABLE IF NOT EXISTS kg_nodes(id TEXT PRIMARY KEY,label TEXT,kind TEXT,properties TEXT,created REAL)")
            c.execute("CREATE TABLE IF NOT EXISTS kg_edges(id TEXT PRIMARY KEY,source TEXT,target TEXT,relation TEXT,weight REAL)")

    def db(self):
        return sqlite3.connect(self.path, timeout=10)

    def add_node(self, label, kind="concept", properties=None):
        if not isinstance(label, str) or not label.strip() or len(label) > 300:
            raise ValueError("label must be 1–300 characters")
        if not isinstance(kind, str) or not kind.strip() or len(kind) > 80:
            raise ValueError("kind must be 1–80 characters")
        props = properties or {}
        if not isinstance(props, dict):
            raise ValueError("properties must be an object")
        ident = str(uuid.uuid4())
        with self.db() as c:
            c.execute("INSERT INTO kg_nodes VALUES(?,?,?,?,?)",
                      (ident, label.strip(), kind.strip(), json.dumps(props), time.time()))
        return {"id": ident, "label": label.strip(), "kind": kind.strip(), "properties": props}

    def add_edge(self, source, target, relation="related_to", weight=1.0):
        if not isinstance(relation, str) or not relation.strip() or len(relation) > 100:
            raise ValueError("relation must be 1–100 characters")
        if not 0 <= float(weight) <= 100:
            raise ValueError("weight must be between 0 and 100")
        with self.db() as c:
            ids = {r[0] for r in c.execute("SELECT id FROM kg_nodes WHERE id IN (?,?)", (source, target))}
            if source not in ids or target not in ids:
                raise ValueError("both nodes must exist")
            ident = str(uuid.uuid4())
            c.execute("INSERT INTO kg_edges VALUES(?,?,?,?,?)",
                      (ident, source, target, relation.strip(), float(weight)))
        return {"id": ident, "source": source, "target": target, "relation": relation.strip(), "weight": float(weight)}

    def delete_node(self, ident):
        with self.db() as c:
            c.execute("DELETE FROM kg_edges WHERE source=? OR target=?", (ident, ident))
            cur = c.execute("DELETE FROM kg_nodes WHERE id=?", (ident,))
            return cur.rowcount == 1

    def delete_edge(self, ident):
        with self.db() as c:
            cur = c.execute("DELETE FROM kg_edges WHERE id=?", (ident,))
            return cur.rowcount == 1

    def snapshot(self):
        with self.db() as c:
            ns = c.execute("SELECT id,label,kind,properties FROM kg_nodes ORDER BY label").fetchall()
            es = c.execute("SELECT id,source,target,relation,weight FROM kg_edges ORDER BY id").fetchall()
        return {
            "nodes": [{"id": n[0], "label": n[1], "kind": n[2], "properties": json.loads(n[3])} for n in ns],
            "edges": [{"id": e[0], "source": e[1], "target": e[2], "relation": e[3], "weight": e[4]} for e in es]
        }
