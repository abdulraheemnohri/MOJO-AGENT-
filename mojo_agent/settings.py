"""Persistent, validated local runtime preferences."""
import json,sqlite3
from pathlib import Path
DEFAULTS={'runtime':'python-reference','llm_enabled':False,'api_host':'127.0.0.1','api_port':8766,'memory':'sqlite','evolution_auto_activate':False,'tool_approval_required':True,'theme':'dark'}
class SettingsStore:
 def __init__(self,path='data/mojo_agent.sqlite3'):
  self.path=path;Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:c.execute('CREATE TABLE IF NOT EXISTS app_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
 def db(self):return sqlite3.connect(self.path)
 def get(self):
  with self.db() as c:rows=c.execute('SELECT key,value FROM app_settings').fetchall()
  out=DEFAULTS.copy()
  for k,v in rows:
   try:out[k]=json.loads(v)
   except json.JSONDecodeError:continue
  return out
 def update(self,values):
  allowed={'theme','tool_approval_required'}
  if set(values)-allowed:raise ValueError('Unsupported or restart-only setting')
  if 'theme' in values and values['theme'] not in {'dark','light','system'}:raise ValueError('theme must be dark, light or system')
  if values.get('tool_approval_required') is False:raise ValueError('Tool approval is mandatory and cannot be disabled')
  if 'tool_approval_required' in values and not isinstance(values['tool_approval_required'],bool):raise ValueError('tool_approval_required must be boolean')
  with self.db() as c:
   for k,v in values.items():c.execute('INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,json.dumps(v)))
  return self.get()
