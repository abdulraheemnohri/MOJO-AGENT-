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
   c.execute("""CREATE TABLE IF NOT EXISTS workflow_jobs(
    id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, workflow_name TEXT NOT NULL, steps TEXT NOT NULL,
    status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3,
    available_at REAL NOT NULL, created REAL NOT NULL, started REAL, finished REAL,
    result TEXT NOT NULL DEFAULT '[]', error TEXT NOT NULL DEFAULT '',
    cancel_requested INTEGER NOT NULL DEFAULT 0, worker_id TEXT NOT NULL DEFAULT '')""")
   c.execute("CREATE INDEX IF NOT EXISTS idx_workflow_jobs_queue ON workflow_jobs(status,available_at,created)")
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


 # Durable queue: enqueue snapshots the workflow so later edits do not mutate queued work.
 def enqueue(self,workflow_id,max_attempts=3,now=None):
  if not isinstance(max_attempts,int) or isinstance(max_attempts,bool) or not 1<=max_attempts<=10:
   raise ValueError("max_attempts must be between 1 and 10")
  workflow=self.get(workflow_id)
  if not workflow: raise KeyError("workflow not found")
  stamp=time.time() if now is None else float(now);ident=str(uuid.uuid4())
  with self.db() as c:
   queued=c.execute("SELECT COUNT(*) FROM workflow_jobs WHERE status IN ('queued','running')").fetchone()[0]
   if queued>=500: raise ValueError("workflow queue is full (500 active jobs maximum)")
   c.execute("""INSERT INTO workflow_jobs(id,workflow_id,workflow_name,steps,status,attempts,max_attempts,available_at,created)
    VALUES(?,?,?,?, 'queued',0,?,?,?)""",(ident,workflow_id,workflow["name"],json.dumps(workflow["steps"]),max_attempts,stamp,stamp))
  return self.get_job(ident)

 def _job_row(self,row):
  return {"id":row[0],"workflow_id":row[1],"workflow_name":row[2],"steps":json.loads(row[3]),
   "status":row[4],"attempts":row[5],"max_attempts":row[6],"available_at":row[7],
   "created":row[8],"started":row[9],"finished":row[10],"result":json.loads(row[11]),
   "error":row[12],"cancel_requested":bool(row[13]),"worker_id":row[14]}
 def get_job(self,job_id):
  with self.db() as c: row=c.execute("""SELECT id,workflow_id,workflow_name,steps,status,attempts,max_attempts,
   available_at,created,started,finished,result,error,cancel_requested,worker_id FROM workflow_jobs WHERE id=?""",(job_id,)).fetchone()
  return self._job_row(row) if row else None
 def list_jobs(self,limit=100,status=None):
  limit=max(1,min(int(limit),200))
  with self.db() as c:
   query="""SELECT id,workflow_id,workflow_name,steps,status,attempts,max_attempts,available_at,created,started,finished,result,error,cancel_requested,worker_id FROM workflow_jobs"""
   args=[]
   if status:
    if status not in {"queued","running","completed","failed","cancelled"}: raise ValueError("invalid job status")
    query+=" WHERE status=?";args.append(status)
   query+=" ORDER BY created DESC LIMIT ?";args.append(limit)
   rows=c.execute(query,args).fetchall()
  return [self._job_row(row) for row in rows]
 def job_counts(self):
  with self.db() as c:rows=c.execute("SELECT status,COUNT(*) FROM workflow_jobs GROUP BY status").fetchall()
  counts={status:0 for status in ("queued","running","completed","failed","cancelled")}
  counts.update({status:count for status,count in rows})
  return counts
 def cancel_job(self,job_id):
  with self.db() as c:
   row=c.execute("SELECT status FROM workflow_jobs WHERE id=?",(job_id,)).fetchone()
   if not row:return None
   if row[0]=="queued":
    c.execute("UPDATE workflow_jobs SET status='cancelled',finished=?,error='Cancelled before execution' WHERE id=?",(time.time(),job_id))
   elif row[0]=="running":
    c.execute("UPDATE workflow_jobs SET cancel_requested=1 WHERE id=?",(job_id,))
  return self.get_job(job_id)
 def retry_job(self,job_id,now=None):
  stamp=time.time() if now is None else float(now)
  with self.db() as c:
   row=c.execute("SELECT status,attempts,max_attempts FROM workflow_jobs WHERE id=?",(job_id,)).fetchone()
   if not row:return None
   if row[0] not in {"failed","cancelled"}:raise ValueError("only failed or cancelled jobs can be retried")
   c.execute("""UPDATE workflow_jobs SET status='queued',attempts=0,available_at=?,started=NULL,finished=NULL,
    result='[]',error='',cancel_requested=0,worker_id='' WHERE id=?""",(stamp,job_id))
  return self.get_job(job_id)
 def recover_interrupted(self,now=None):
  stamp=time.time() if now is None else float(now)
  with self.db() as c:
   rows=c.execute("SELECT id,attempts,max_attempts FROM workflow_jobs WHERE status='running'").fetchall()
   for ident,attempts,maximum in rows:
    if attempts<maximum:
     c.execute("""UPDATE workflow_jobs SET status='queued',available_at=?,started=NULL,worker_id='',
      error='Recovered after worker interruption' WHERE id=?""",(stamp,ident))
    else:
     c.execute("""UPDATE workflow_jobs SET status='failed',finished=?,worker_id='',
      error='Worker interrupted; retry limit reached' WHERE id=?""",(stamp,ident))
  return {"recovered":len(rows),"jobs":[self.get_job(row[0]) for row in rows]}
 def _execute_steps(self,steps,tools,job_id=None):
  results=[]
  for index,step in enumerate(steps):
   if job_id:
    job=self.get_job(job_id)
    if not job or job["cancel_requested"]: raise InterruptedError("Job cancellation requested")
   kind=step["type"]
   if kind=="text":result=step.get("value","")
   elif kind=="calculator":result=tools.execute(kind,{"expression":step["expression"]},approved=True)
   else:result=tools.execute(kind,{"text":step.get("text","")},approved=True)
   results.append({"step":index,"type":kind,"result":result})
  return results
 def claim_job(self,worker_id="local-worker",now=None):
  stamp=time.time() if now is None else float(now)
  with self.db() as c:
   c.execute("BEGIN IMMEDIATE")
   row=c.execute("""SELECT id FROM workflow_jobs WHERE status='queued' AND available_at<=?
    ORDER BY created LIMIT 1""",(stamp,)).fetchone()
   if not row:c.commit();return None
   ident=row[0]
   changed=c.execute("""UPDATE workflow_jobs SET status='running',attempts=attempts+1,started=?,
    worker_id=?,cancel_requested=0 WHERE id=? AND status='queued'""",(stamp,worker_id,ident)).rowcount
   c.commit()
   if not changed:return None
  return self.get_job(ident)
 def execute_job(self,job_id,tools,now=None):
  job=self.get_job(job_id)
  if not job:raise KeyError("job not found")
  if job["status"]!="running":raise ValueError("job must be claimed before execution")
  stamp=time.time() if now is None else float(now)
  try:
   results=self._execute_steps(job["steps"],tools,job_id)
   current=self.get_job(job_id)
   if current and current["cancel_requested"]:status="cancelled";error="Cancelled during execution"
   else:status="completed";error=""
  except InterruptedError as exc:
   results=[];status="cancelled";error=str(exc)
  except Exception as exc:
   results=[];error=str(exc)[:500]
   status="queued" if job["attempts"]<job["max_attempts"] else "failed"
  with self.db() as c:
   if status=="queued":
    delay=min(300,2**max(0,job["attempts"]-1))
    c.execute("""UPDATE workflow_jobs SET status='queued',available_at=?,result=?,error=?,worker_id='',
     started=NULL,cancel_requested=0 WHERE id=?""",(stamp+delay,json.dumps(results),error,job_id))
   else:
    c.execute("""UPDATE workflow_jobs SET status=?,finished=?,result=?,error=?,worker_id='',
     cancel_requested=0 WHERE id=?""",(status,stamp,json.dumps(results),error,job_id))
  return self.get_job(job_id)
 def worker_tick(self,tools,worker_id="local-worker",now=None,limit=5):
  if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=10:
   raise ValueError("worker batch limit must be 1..10")
  stamp=time.time() if now is None else float(now);processed=[]
  for _ in range(limit):
   job=self.claim_job(worker_id,stamp)
   if not job:break
   processed.append(self.execute_job(job["id"],tools,stamp))
  scheduled=self.run_due(tools,now=stamp,limit=min(10,limit))
  return {"worker_id":worker_id,"processed":len(processed),"jobs":processed,"scheduled":scheduled,"checked_at":stamp}
