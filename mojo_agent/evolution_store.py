"""SQLite persistence for evolution experiments, generation, and approved champion."""
import json, sqlite3
from pathlib import Path
from .evolution import Candidate, Strategy

class EvolutionStore:
 def __init__(self,path="data/mojo_agent.sqlite3"):
  self.path=path;Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:
   c.execute("CREATE TABLE IF NOT EXISTS evolution_candidates(id TEXT PRIMARY KEY,strategy TEXT NOT NULL,fitness REAL NOT NULL,generation INTEGER NOT NULL,tests_passed INTEGER NOT NULL,approved INTEGER NOT NULL,created REAL DEFAULT (strftime('%s','now')))")
   c.execute("CREATE TABLE IF NOT EXISTS evolution_state(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
 def db(self):return sqlite3.connect(self.path,timeout=10)
 def save_candidate(self,ident,candidate):
  with self.db() as c:c.execute("""INSERT INTO evolution_candidates(id,strategy,fitness,generation,tests_passed,approved) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET strategy=excluded.strategy,fitness=excluded.fitness,generation=excluded.generation,tests_passed=excluded.tests_passed,approved=excluded.approved""",(ident,json.dumps(candidate.strategy.__dict__,sort_keys=True),float(candidate.fitness),int(candidate.generation),int(candidate.tests_passed),int(candidate.approved)))
 def get_candidate(self,ident):
  with self.db() as c:r=c.execute("SELECT strategy,fitness,generation,tests_passed,approved FROM evolution_candidates WHERE id=?",(ident,)).fetchone()
  return Candidate(Strategy(**json.loads(r[0])),r[1],r[2],bool(r[3]),bool(r[4])) if r else None
 def list_candidates(self,limit=100):
  with self.db() as c:rows=c.execute("SELECT id,strategy,fitness,generation,tests_passed,approved FROM evolution_candidates ORDER BY generation DESC,fitness DESC LIMIT ?",(max(1,min(int(limit),500)),)).fetchall()
  return [{"id":r[0],"strategy":json.loads(r[1]),"fitness":r[2],"generation":r[3],"tests_passed":bool(r[4]),"approved":bool(r[5])} for r in rows]
 def set_champion(self,strategy):
  with self.db() as c:c.execute("INSERT INTO evolution_state(key,value) VALUES('champion',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(json.dumps(strategy.__dict__,sort_keys=True),))
 def get_champion(self):
  with self.db() as c:r=c.execute("SELECT value FROM evolution_state WHERE key='champion'").fetchone()
  return Strategy(**json.loads(r[0])) if r else Strategy()
 def set_generation(self,generation):
  with self.db() as c:c.execute("INSERT INTO evolution_state(key,value) VALUES('generation',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(str(max(0,int(generation))),))
 def get_generation(self):
  with self.db() as c:r=c.execute("SELECT value FROM evolution_state WHERE key='generation'").fetchone()
  return max(0,int(r[0])) if r else 0
