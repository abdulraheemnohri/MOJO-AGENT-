import sqlite3
from pathlib import Path
class MemoryStore:
 def __init__(self,path='data/mojo_agent.sqlite3'):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with sqlite3.connect(self.path) as db:db.execute('CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,content TEXT NOT NULL,importance REAL NOT NULL DEFAULT .5,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
 def add(self,content,kind='episodic',importance=.5):
  if not content.strip():raise ValueError('Memory cannot be empty')
  if kind not in {'working','short_term','long_term','episodic','semantic','experience'}:raise ValueError('Unsupported memory kind')
  with sqlite3.connect(self.path) as db:
   cur=db.execute('INSERT INTO memories(kind,content,importance) VALUES(?,?,?)',(kind,content,max(0,min(1,importance))))
   return cur.lastrowid
 def search(self,query='',limit=20):
  if not 1<=limit<=200:raise ValueError('limit must be 1..200')
  with sqlite3.connect(self.path) as db:
   rows=db.execute('SELECT id,kind,content,importance,created_at FROM memories WHERE content LIKE ? ORDER BY importance DESC LIMIT ?',(f'%{query}%',limit)).fetchall()
  return [dict(zip(('id','kind','content','importance','created_at'),r)) for r in rows]
