import pytest
from fastapi.testclient import TestClient
from mojo_agent.api import app
from mojo_agent.tools import calculator
from mojo_agent.security import PermissionDenied
client=TestClient(app,client=("127.0.0.1",50000))
def test_health_plan():
 assert client.get('/api/v1/health').json()['llm']=='disabled';r=client.post('/api/v1/plan',json={'goal':'inspect; test'});assert r.status_code==200 and len(r.json()['tasks'])==2
def test_calculator_gate():
 with pytest.raises(PermissionDenied):calculator('2+3')
 assert calculator('2+3',approved=True)==5


def test_runtime_status_and_database_backup():
 status=client.get('/api/v1/runtime/status')
 assert status.status_code==200
 assert status.json()['database']['integrity']=='ok'
 backup=client.get('/api/v1/backup/export')
 assert backup.status_code==200
 assert backup.content[:16]==b'SQLite format 3'+bytes([0])
 assert int(backup.headers['X-Backup-Size'])==len(backup.content)

def test_settings_validation_does_not_mutate():
 before=client.get('/api/v1/settings').json()
 good=client.post('/api/v1/settings/validate',json={'theme':'light'})
 assert good.status_code==200 and good.json()['valid'] is True
 assert client.get('/api/v1/settings').json()==before
 assert client.post('/api/v1/settings/validate',json={'tool_approval_required':False}).status_code==400
 assert client.post('/api/v1/settings/validate',json={'api_port':9999}).status_code==400


def test_database_backup_rejects_remote_clients():
 remote=TestClient(app,client=("192.168.1.50",50000))
 assert remote.get('/api/v1/backup/export').status_code==403


def test_runtime_logs_are_bounded_safe_and_filterable():
 client.get('/api/v1/health')
 result=client.get('/api/v1/runtime/logs?limit=20')
 assert result.status_code==200
 body=result.json()
 assert body['count']>=1 and body['payloads_recorded'] is False
 assert body['items'][0]['path']=='/api/v1/runtime/logs'
 assert client.get('/api/v1/runtime/logs?limit=501').status_code==400
 assert client.get('/api/v1/runtime/logs?level=TRACE').status_code==400
 cleared=client.post('/api/v1/runtime/logs/clear')
 assert cleared.status_code==200 and cleared.json()['cleared']>=1
