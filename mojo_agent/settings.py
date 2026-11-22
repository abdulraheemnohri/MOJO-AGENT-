"""Persistent, validated local runtime preferences."""
import json,sqlite3
from pathlib import Path
DEFAULTS={'runtime':'python-reference','llm_enabled':False,'api_host':'127.0.0.1','api_port':8766,'memory':'sqlite','evolution_auto_activate':False,'tool_approval_required':True,'theme':'dark','runtime_mode':'algorithms','litertlm_enabled':False,'litertlm_backend':'cpu','litertlm_timeout_seconds':120,'litertlm_model':''}
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
  allowed={'theme','tool_approval_required','runtime_mode','litertlm_enabled','litertlm_backend','litertlm_timeout_seconds','litertlm_model'}
  if set(values)-allowed:raise ValueError('Unsupported or restart-only setting')
  if 'theme' in values and values['theme'] not in {'dark','light','system'}:raise ValueError('theme must be dark, light or system')
  if values.get('tool_approval_required') is False:raise ValueError('Tool approval is mandatory and cannot be disabled')
  if 'tool_approval_required' in values and not isinstance(values['tool_approval_required'],bool):raise ValueError('tool_approval_required must be boolean')
  if 'runtime_mode' in values and values['runtime_mode'] not in {'algorithms','hybrid','litertlm'}:raise ValueError('runtime_mode must be algorithms, hybrid or litertlm')
  if 'litertlm_enabled' in values and not isinstance(values['litertlm_enabled'],bool):raise ValueError('litertlm_enabled must be boolean')
  if 'litertlm_backend' in values and values['litertlm_backend'] not in {'cpu','gpu'}:raise ValueError('litertlm_backend must be cpu or gpu')
  if 'litertlm_timeout_seconds' in values and (not isinstance(values['litertlm_timeout_seconds'],int) or not 10<=values['litertlm_timeout_seconds']<=180):raise ValueError('litertlm_timeout_seconds must be 10-180')
  if 'litertlm_model' in values and (not isinstance(values['litertlm_model'],str) or len(values['litertlm_model'])>512):raise ValueError('litertlm_model must be a string up to 512 characters')
  if values.get('runtime_mode') in {'hybrid','litertlm'} and not (values.get('litertlm_enabled') or self.get().get('litertlm_enabled')):raise ValueError('Enable LiteRT-LM before selecting hybrid or litertlm mode')
  with self.db() as c:
   for k,v in values.items():c.execute('INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,json.dumps(v)))
  return self.get()
