"""Persistent, validated local runtime preferences."""
import json,sqlite3,secrets,hashlib,hmac
from pathlib import Path
DEFAULTS={'runtime':'python-reference','llm_enabled':False,'api_host':'127.0.0.1','api_port':8766,'memory':'sqlite','evolution_auto_activate':False,'tool_approval_required':True,'theme':'dark','runtime_mode':'algorithms','litertlm_enabled':False,'litertlm_backend':'cpu','litertlm_timeout_seconds':120,'litertlm_model':'','worker_enabled':False,'worker_poll_seconds':2,'worker_batch_size':3,'workflow_max_attempts':3,'api_auth_enabled':False}
class SettingsStore:
 def __init__(self,path='data/mojo_agent.sqlite3'):
  self.path=path;Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:c.execute('CREATE TABLE IF NOT EXISTS app_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
 def db(self):return sqlite3.connect(self.path)
 def _get_raw(self):
  with self.db() as c:rows=c.execute('SELECT key,value FROM app_settings').fetchall()
  out=DEFAULTS.copy()
  for k,v in rows:
   try:out[k]=json.loads(v)
   except json.JSONDecodeError:continue
  return out
 def get(self):
  out=self._get_raw()
  out.pop('api_auth_hash',None);out.pop('api_auth_salt',None)
  return out
 def update(self,values):
  allowed={'theme','tool_approval_required','runtime_mode','litertlm_enabled','litertlm_backend','litertlm_timeout_seconds','litertlm_model','worker_enabled','worker_poll_seconds','worker_batch_size','workflow_max_attempts'}
  if set(values)-allowed:raise ValueError('Unsupported or restart-only setting')
  if 'theme' in values and values['theme'] not in {'dark','light','system'}:raise ValueError('theme must be dark, light or system')
  if values.get('tool_approval_required') is False:raise ValueError('Tool approval is mandatory and cannot be disabled')
  if 'tool_approval_required' in values and not isinstance(values['tool_approval_required'],bool):raise ValueError('tool_approval_required must be boolean')
  if 'runtime_mode' in values and values['runtime_mode'] not in {'algorithms','hybrid','litertlm'}:raise ValueError('runtime_mode must be algorithms, hybrid or litertlm')
  if 'litertlm_enabled' in values and not isinstance(values['litertlm_enabled'],bool):raise ValueError('litertlm_enabled must be boolean')
  if 'litertlm_backend' in values and values['litertlm_backend'] not in {'cpu','gpu'}:raise ValueError('litertlm_backend must be cpu or gpu')
  if 'litertlm_timeout_seconds' in values and (not isinstance(values['litertlm_timeout_seconds'],int) or not 10<=values['litertlm_timeout_seconds']<=180):raise ValueError('litertlm_timeout_seconds must be 10-180')
  if 'litertlm_model' in values and (not isinstance(values['litertlm_model'],str) or len(values['litertlm_model'])>512):raise ValueError('litertlm_model must be a string up to 512 characters')
  if 'worker_enabled' in values and not isinstance(values['worker_enabled'],bool):raise ValueError('worker_enabled must be boolean')
  if 'worker_poll_seconds' in values and (not isinstance(values['worker_poll_seconds'],int) or not 1<=values['worker_poll_seconds']<=60):raise ValueError('worker_poll_seconds must be 1-60')
  if 'worker_batch_size' in values and (not isinstance(values['worker_batch_size'],int) or not 1<=values['worker_batch_size']<=10):raise ValueError('worker_batch_size must be 1-10')
  if 'workflow_max_attempts' in values and (not isinstance(values['workflow_max_attempts'],int) or not 1<=values['workflow_max_attempts']<=10):raise ValueError('workflow_max_attempts must be 1-10')
  current=self.get();effective_mode=values.get('runtime_mode',current['runtime_mode']);effective_enabled=values.get('litertlm_enabled',current['litertlm_enabled'])
  if effective_mode in {'hybrid','litertlm'} and not effective_enabled:raise ValueError('Enable LiteRT-LM before selecting hybrid or litertlm mode')
  with self.db() as c:
   for k,v in values.items():c.execute('INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,json.dumps(v)))
  return self.get()

 def auth_status(self):
  current=self._get_raw()
  return {'enabled':bool(current.get('api_auth_enabled',False)),'configured':bool(current.get('api_auth_hash') and current.get('api_auth_salt')),'algorithm':'PBKDF2-HMAC-SHA256'}

 def create_api_token(self):
  token=secrets.token_urlsafe(40)
  salt=secrets.token_bytes(16)
  digest=hashlib.pbkdf2_hmac('sha256',token.encode(),salt,310000)
  with self.db() as c:
   c.executemany('INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',[
    ('api_auth_salt',json.dumps(salt.hex())),('api_auth_hash',json.dumps(digest.hex())),('api_auth_enabled','true')])
  return token

 def revoke_api_token(self):
  with self.db() as c:
   c.execute("DELETE FROM app_settings WHERE key IN ('api_auth_salt','api_auth_hash')")
   c.execute("INSERT INTO app_settings(key,value) VALUES('api_auth_enabled','false') ON CONFLICT(key) DO UPDATE SET value='false'")
  return {'enabled':False,'configured':False}

 def verify_api_token(self,token):
  if not token:return False
  current=self._get_raw()
  if not current.get('api_auth_enabled'):return True
  salt=current.get('api_auth_salt');expected=current.get('api_auth_hash')
  if not salt or not expected:return False
  try:actual=hashlib.pbkdf2_hmac('sha256',token.encode(),bytes.fromhex(salt),310000).hex()
  except (ValueError,TypeError):return False
  return hmac.compare_digest(actual,expected)
