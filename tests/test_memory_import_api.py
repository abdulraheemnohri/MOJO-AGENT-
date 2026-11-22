from fastapi.testclient import TestClient
from mojo_agent.api import app
client=TestClient(app)
def test_memory_export_import_roundtrip():
    client.post('/api/v1/memory',json={'content':'export-import-probe','kind':'episodic','importance':.4})
    exported=client.get('/api/v1/memory/export').json()
    assert exported['format']=='mojo-memory-v1'
    assert any(x['content']=='export-import-probe' for x in exported['items'])
    result=client.post('/api/v1/memory/import',json={'format':'mojo-memory-v1','items':[{'content':'import-probe','kind':'semantic','importance':.8}]})
    assert result.status_code==200 and result.json()['imported']==1
def test_memory_import_rejects_unknown_format():
    assert client.post('/api/v1/memory/import',json={'format':'unknown','items':[]}).status_code==400
