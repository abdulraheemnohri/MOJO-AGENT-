import pytest
from fastapi.testclient import TestClient
from mojo_agent.api import app
from mojo_agent.tools import calculator
from mojo_agent.security import PermissionDenied
client=TestClient(app)
def test_health_plan():
 assert client.get('/api/v1/health').json()['llm']=='disabled';r=client.post('/api/v1/plan',json={'goal':'inspect; test'});assert r.status_code==200 and len(r.json()['tasks'])==2
def test_calculator_gate():
 with pytest.raises(PermissionDenied):calculator('2+3')
 assert calculator('2+3',approved=True)==5
