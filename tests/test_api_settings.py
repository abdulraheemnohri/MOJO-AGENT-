from fastapi.testclient import TestClient
from mojo_agent.api import app
from mojo_agent.settings import SettingsStore
client=TestClient(app)
def test_settings_are_persistent_and_loopback_only(tmp_path):
 s=SettingsStore(str(tmp_path/'s.db'));assert s.update({'theme':'light'})['theme']=='light'
 try:s.update({'api_host':'0.0.0.0'})
 except ValueError:pass
 else:assert False
def test_settings_api_patch():
 r=client.patch('/api/v1/settings',json={'theme':'system'});assert r.status_code==200 and r.json()['theme']=='system'
def test_tool_requires_approval():
 r=client.post('/api/v1/tools/execute',json={'name':'calculator','arguments':{'expression':'2+2'}});assert r.status_code==403
 r=client.post('/api/v1/tools/execute',json={'name':'calculator','arguments':{'expression':'2+2'},'approved':True});assert r.status_code==200 and r.json()['result']==4
def test_plan_rejects_blank_goal():
 assert client.post('/api/v1/plan',json={'goal':'  '}).status_code==400
