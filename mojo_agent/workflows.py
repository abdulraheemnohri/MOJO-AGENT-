"""Safe local workflow registry and deterministic runner."""
import json,sqlite3,time,uuid
from pathlib import Path
class WorkflowStore:
 def __init__(self,path="data/mojo_agent.sqlite3"):
  self.path=path;Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:
   c.execute("CREATE TABLE IF NOT EXISTS workflows(id TEXT PRIMARY KEY,name TEXT,steps TEXT,created REAL,updated REAL)")
   c.execute("CREATE TABLE IF NOT EXISTS workflow_runs(id TEXT PRIMARY KEY,workflow_id TEXT,status TEXT,results TEXT,started REAL,finished REAL)")
 def db(self):return sqlite3.connect(self.path)
 def create(self,name,steps):
  if not name.strip():raise ValueError("workflow name required")
  if not isinstance(steps,list) or not 1<=len(steps)<=50:raise ValueError("workflow needs 1–50 steps")
  if any(not isinstance(s,dict) or s.get("type") not in {"text","calculator","text_stats"} for s in steps):raise ValueError("unsupported workflow step")
  ident=str(uuid.uuid4());now=time.time()
  with self.db() as c:c.execute("INSERT INTO workflows VALUES(?,?,?,?,?)",(ident,name.strip(),json.dumps(steps),now,now))
  return self.get(ident)
 def row(self,r):return {"id":r[0],"name":r[1],"steps":json.loads(r[2]),"created":r[3],"updated":r[4]}
 def get(self,ident):
  with self.db() as c:r=c.execute("SELECT id,name,steps,created,updated FROM workflows WHERE id=?",(ident,)).fetchone()
  return self.row(r) if r else None
 def list(self):
  with self.db() as c:rows=c.execute("SELECT id,name,steps,created,updated FROM workflows ORDER BY updated DESC").fetchall()
  return [self.row(r) for r in rows]
 def run(self,ident,tools):
  w=self.get(ident)
  if not w:raise KeyError("workflow not found")
  rid=str(uuid.uuid4());started=time.time();results=[];status="completed"
  try:
   for i,s in enumerate(w["steps"]):
    t=s["type"];v=str(s.get("value","")) if t=="text" else tools.execute(t,{"expression":s.get("expression","")} if t=="calculator" else {"text":s.get("text","")},approved=True)
    results.append({"step":i,"type":t,"result":v})
  except Exception as e:status="failed";results.append({"error":str(e)})
  with self.db() as c:c.execute("INSERT INTO workflow_runs VALUES(?,?,?,?,?,?)",(rid,ident,status,json.dumps(results),started,time.time()))
  return {"id":rid,"workflow_id":ident,"status":status,"results":results}
 def history(self,limit=50):
  with self.db() as c:rows=c.execute("SELECT id,workflow_id,status,results,started,finished FROM workflow_runs ORDER BY started DESC LIMIT ?",(max(1,min(limit,200)),)).fetchall()
  return [{"id":r[0],"workflow_id":r[1],"status":r[2],"results":json.loads(r[3]),"started":r[4],"finished":r[5]} for r in rows]
