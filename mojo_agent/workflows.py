"""Safe local workflow registry and bounded deterministic runner."""
import json,sqlite3,time,uuid
from pathlib import Path
ALLOWED_STEP_TYPES={"text","calculator","text_stats"}
MAX_TEXT=10000
class WorkflowStore:
 def __init__(self,path="data/mojo_agent.sqlite3"):
  self.path=path;Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:
   c.execute("CREATE TABLE IF NOT EXISTS workflows(id TEXT PRIMARY KEY,name TEXT,steps TEXT,created REAL,updated REAL)")
   c.execute("CREATE TABLE IF NOT EXISTS workflow_runs(id TEXT PRIMARY KEY,workflow_id TEXT,status TEXT,results TEXT,started REAL,finished REAL)")
   c.execute("CREATE TABLE IF NOT EXISTS workflow_schedules(id TEXT PRIMARY KEY,workflow_id TEXT NOT NULL,interval_seconds INTEGER NOT NULL,next_run REAL NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,created REAL NOT NULL,last_run REAL,last_status TEXT)")
 def db(self):return sqlite3.connect(self.path,timeout=10)
 def _validate(self,name,steps):
  if not isinstance(name,str) or not name.strip() or len(name)>120:raise ValueError("workflow name must contain 1–120 characters")
  if not isinstance(steps,list) or not 1<=len(steps)<=50:raise ValueError("workflow needs 1–50 steps")
  for s in steps:
   if not isinstance(s,dict) or s.get("type") not in ALLOWED_STEP_TYPES:raise ValueError("unsupported workflow step")
   key={"text":"value","calculator":"expression","text_stats":"text"}[s["type"]];v=s.get(key,"")
   if not isinstance(v,str) or len(v)> (200 if key=="expression" else MAX_TEXT):raise ValueError("workflow step input is invalid or too long")
   if key=="expression" and not v:raise ValueError("calculator expression cannot be empty")
 def _row(self,r):return {"id":r[0],"name":r[1],"steps":json.loads(r[2]),"created":r[3],"updated":r[4]}
 def create(self,name,steps):
  self._validate(name,steps);ident,now=str(uuid.uuid4()),time.time()
  with self.db() as c:c.execute("INSERT INTO workflows VALUES(?,?,?,?,?)",(ident,name.strip(),json.dumps(steps),now,now))
  return self.get(ident)
 def get(self,ident):
  with self.db() as c:r=c.execute("SELECT id,name,steps,created,updated FROM workflows WHERE id=?",(ident,)).fetchone()
  return self._row(r) if r else None
 def list(self):
  with self.db() as c:rows=c.execute("SELECT id,name,steps,created,updated FROM workflows ORDER BY updated DESC").fetchall()
  return [self._row(r) for r in rows]
 def update(self,ident,name,steps):
  self._validate(name,steps)
  with self.db() as c:return c.execute("UPDATE workflows SET name=?,steps=?,updated=? WHERE id=?",(name.strip(),json.dumps(steps),time.time(),ident)).rowcount==1
 def delete(self,ident):
  with self.db() as c:
   c.execute("DELETE FROM workflow_runs WHERE workflow_id=?",(ident,))
   c.execute("DELETE FROM workflow_schedules WHERE workflow_id=?",(ident,))
   return c.execute("DELETE FROM workflows WHERE id=?",(ident,)).rowcount==1
 def run(self,ident,tools):
  w=self.get(ident)
  if not w:raise KeyError("workflow not found")
  rid,started,results,status=str(uuid.uuid4()),time.time(),[],"completed"
  try:
   for i,s in enumerate(w["steps"]):
    kind=s["type"]
    if kind=="text":result=s.get("value","")
    elif kind=="calculator":result=tools.execute(kind,{"expression":s["expression"]},approved=True)
    else:result=tools.execute(kind,{"text":s.get("text","")},approved=True)
    results.append({"step":i,"type":kind,"result":result})
  except Exception as exc:status="failed";results.append({"step":len(results),"error":str(exc)[:500]})
  with self.db() as c:c.execute("INSERT INTO workflow_runs VALUES(?,?,?,?,?,?)",(rid,ident,status,json.dumps(results),started,time.time()))
  return {"id":rid,"workflow_id":ident,"status":status,"results":results}

 def create_schedule(self,workflow_id,interval_seconds,now=None):
  if not isinstance(interval_seconds,int) or isinstance(interval_seconds,bool) or not 60<=interval_seconds<=2592000:
   raise ValueError("schedule interval must be between 60 seconds and 30 days")
  if not self.get(workflow_id):raise KeyError("workflow not found")
  ident=str(uuid.uuid4());stamp=time.time() if now is None else float(now)
  with self.db() as c:
   count=c.execute("SELECT COUNT(*) FROM workflow_schedules").fetchone()[0]
   if count>=100:raise ValueError("maximum of 100 schedules reached")
   c.execute("INSERT INTO workflow_schedules(id,workflow_id,interval_seconds,next_run,enabled,created) VALUES(?,?,?,?,1,?)",(ident,workflow_id,interval_seconds,stamp+interval_seconds,stamp))
  return self.get_schedule(ident)
 def get_schedule(self,ident):
  with self.db() as c:r=c.execute("SELECT id,workflow_id,interval_seconds,next_run,enabled,created,last_run,last_status FROM workflow_schedules WHERE id=?",(ident,)).fetchone()
  return self._schedule_row(r) if r else None
 def _schedule_row(self,r):
  return {"id":r[0],"workflow_id":r[1],"interval_seconds":r[2],"next_run":r[3],"enabled":bool(r[4]),"created":r[5],"last_run":r[6],"last_status":r[7]}
 def list_schedules(self):
  with self.db() as c:rows=c.execute("SELECT id,workflow_id,interval_seconds,next_run,enabled,created,last_run,last_status FROM workflow_schedules ORDER BY next_run").fetchall()
  return [self._schedule_row(r) for r in rows]
 def delete_schedule(self,ident):
  with self.db() as c:return c.execute("DELETE FROM workflow_schedules WHERE id=?",(ident,)).rowcount==1
 def set_schedule_enabled(self,ident,enabled,now=None):
  if not isinstance(enabled,bool):raise ValueError("enabled must be boolean")
  stamp=time.time() if now is None else float(now)
  with self.db() as c:
   row=c.execute("SELECT interval_seconds FROM workflow_schedules WHERE id=?",(ident,)).fetchone()
   if not row:return None
   next_run=stamp+row[0] if enabled else 0
   c.execute("UPDATE workflow_schedules SET enabled=?,next_run=? WHERE id=?",(int(enabled),next_run,ident))
  return self.get_schedule(ident)
 def run_due(self,tools,now=None,limit=10):
  if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=10:raise ValueError("scheduler batch limit must be 1..10")
  stamp=time.time() if now is None else float(now)
  db=self.db()
  try:
   db.execute("BEGIN IMMEDIATE")
   rows=db.execute("SELECT id,workflow_id,interval_seconds FROM workflow_schedules WHERE enabled=1 AND next_run<=? ORDER BY next_run LIMIT ?",(stamp,limit)).fetchall()
   for sid,wid,interval in rows:
    db.execute("UPDATE workflow_schedules SET next_run=?,last_run=? WHERE id=?",(stamp+interval,stamp,sid))
   db.commit()
  except Exception:
   db.rollback();raise
  finally:db.close()
  results=[]
  for sid,wid,interval in rows:
   try:
    result=self.run(wid,tools);status=result["status"]
   except Exception as exc:
    result={"workflow_id":wid,"status":"failed","error":str(exc)[:300]};status="failed"
   with self.db() as c:c.execute("UPDATE workflow_schedules SET last_status=? WHERE id=?",(status,sid))
   results.append({"schedule_id":sid,**result})
  return {"checked_at":stamp,"executed":len(results),"runs":results,"batch_limit":limit}

 def history(self,limit=50,workflow_id=None):
  limit=max(1,min(int(limit),200))
  with self.db() as c:
   if workflow_id:rows=c.execute("SELECT id,workflow_id,status,results,started,finished FROM workflow_runs WHERE workflow_id=? ORDER BY started DESC LIMIT ?",(workflow_id,limit)).fetchall()
   else:rows=c.execute("SELECT id,workflow_id,status,results,started,finished FROM workflow_runs ORDER BY started DESC LIMIT ?",(limit,)).fetchall()
  return [{"id":r[0],"workflow_id":r[1],"status":r[2],"results":json.loads(r[3]),"started":r[4],"finished":r[5]} for r in rows]
