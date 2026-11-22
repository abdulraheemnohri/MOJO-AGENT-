"""Inspectable SQLite knowledge graph."""
import sqlite3,uuid,time,json
from pathlib import Path
class KnowledgeGraph:
 def __init__(self,path="data/mojo_agent.sqlite3"):
  self.path=path;Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:
   c.execute("CREATE TABLE IF NOT EXISTS kg_nodes(id TEXT PRIMARY KEY,label TEXT,kind TEXT,properties TEXT,created REAL)")
   c.execute("CREATE TABLE IF NOT EXISTS kg_edges(id TEXT PRIMARY KEY,source TEXT,target TEXT,relation TEXT,weight REAL)")
 def db(self):return sqlite3.connect(self.path)
 def add_node(self,label,kind="concept",properties=None):
  if not label.strip() or len(label)>300:raise ValueError("label must be 1–300 characters")
  props=properties or {}
  if not isinstance(props,dict):raise ValueError("properties must be an object")
  ident=str(uuid.uuid4())
  with self.db() as c:c.execute("INSERT INTO kg_nodes VALUES(?,?,?,?,?)",(ident,label.strip(),kind,json.dumps(props),time.time()))
  return {"id":ident,"label":label.strip(),"kind":kind,"properties":props}
 def add_edge(self,source,target,relation="related_to",weight=1.0):
  with self.db() as c:
   ids={r[0] for r in c.execute("SELECT id FROM kg_nodes WHERE id IN (?,?)",(source,target))}
   if source not in ids or target not in ids:raise ValueError("both nodes must exist")
   ident=str(uuid.uuid4());c.execute("INSERT INTO kg_edges VALUES(?,?,?,?,?)",(ident,source,target,relation,float(weight)))
  return {"id":ident,"source":source,"target":target,"relation":relation,"weight":weight}
 def snapshot(self):
  with self.db() as c:
   ns=c.execute("SELECT id,label,kind,properties FROM kg_nodes ORDER BY label").fetchall();es=c.execute("SELECT id,source,target,relation,weight FROM kg_edges").fetchall()
  return {"nodes":[{"id":n[0],"label":n[1],"kind":n[2],"properties":json.loads(n[3])} for n in ns],"edges":[{"id":e[0],"source":e[1],"target":e[2],"relation":e[3],"weight":e[4]} for e in es]}
