from fastapi.testclient import TestClient
from mojo_agent import api
from mojo_agent.workflows import WorkflowStore
from mojo_agent.tools import ToolRegistry
from mojo_agent.settings import SettingsStore

def test_durable_workflow_job_api_and_manual_worker(tmp_path, monkeypatch):
    original_workflows=api.workflows
    original_tools=api.tools
    store=WorkflowStore(str(tmp_path/"api-jobs.db"))
    monkeypatch.setattr(api,"workflows",store)
    monkeypatch.setattr(api,"tools",ToolRegistry())
    client=TestClient(api.app,client=("127.0.0.1",50001))
    try:
        workflow=client.post("/api/v1/workflows",json={"name":"API queue","steps":[{"type":"text","value":"queued"}]})
        assert workflow.status_code==200
        job=client.post(f"/api/v1/workflows/{workflow.json()['id']}/enqueue",json={"max_attempts":2})
        assert job.status_code==200 and job.json()["status"]=="queued"
        listed=client.get("/api/v1/workflow-jobs?limit=10")
        assert listed.status_code==200 and listed.json()["items"][0]["id"]==job.json()["id"]
        tick=client.post("/api/v1/worker/tick",json={"limit":2,"worker_id":"test-worker"})
        assert tick.status_code==200 and tick.json()["processed"]==1
        detail=client.get("/api/v1/workflow-jobs/"+job.json()["id"])
        assert detail.json()["status"]=="completed"
    finally:
        monkeypatch.setattr(api,"workflows",original_workflows)
        monkeypatch.setattr(api,"tools",original_tools)

def test_worker_settings_validation():
    client=TestClient(api.app,client=("127.0.0.1",50002))
    assert client.post("/api/v1/settings/validate",json={"worker_enabled":True,"worker_poll_seconds":2,"worker_batch_size":3}).status_code==200
    assert client.post("/api/v1/settings/validate",json={"worker_poll_seconds":0}).status_code==422
    assert client.post("/api/v1/settings/validate",json={"worker_batch_size":99}).status_code==422


def test_enqueue_uses_configured_retry_default(tmp_path, monkeypatch):
    original_workflows=api.workflows
    original_settings=api.settings
    monkeypatch.setattr(api,"workflows",WorkflowStore(str(tmp_path/"queue.db")))
    monkeypatch.setattr(api,"settings",SettingsStore(str(tmp_path/"settings.db")))
    api.settings.update({"workflow_max_attempts":5})
    client=TestClient(api.app,client=("127.0.0.1",50003))
    try:
        workflow=client.post("/api/v1/workflows",json={"name":"defaults","steps":[{"type":"text","value":"x"}]}).json()
        job=client.post(f"/api/v1/workflows/{workflow['id']}/enqueue",json={})
        assert job.status_code==200 and job.json()["max_attempts"]==5
    finally:
        monkeypatch.setattr(api,"workflows",original_workflows)
        monkeypatch.setattr(api,"settings",original_settings)
