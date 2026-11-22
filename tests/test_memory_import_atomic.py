from fastapi.testclient import TestClient
from mojo_agent.api import app
from mojo_agent.memory import MemoryStore

def test_memory_import_is_atomic(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.add("existing record")
    before = store.search("", 200)
    try:
        store.import_many([
            {"content": "valid transactional record", "kind": "episodic", "importance": 0.5},
            {"content": "", "kind": "episodic", "importance": 0.5}
        ])
        assert False, "invalid batch should be rejected"
    except ValueError:
        pass
    assert store.search("", 200) == before

def test_memory_import_validates_batch_before_commit(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    assert store.import_many([
        {"content": "first", "kind": "episodic"},
        {"content": "second", "kind": "semantic", "importance": 0.9}
    ]) == 2
    assert len(store.search("", 200)) == 2

def test_diagnostics_reports_safe_runtime_metadata():
    response = TestClient(app).get("/api/v1/diagnostics")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_enabled"] is False
    assert body["safety"]["shell_execution"] is False
    assert body["database"] == "sqlite"
