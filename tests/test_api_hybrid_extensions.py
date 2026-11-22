from fastapi.testclient import TestClient
from mojo_agent import api
from mojo_agent.extensions import GitHubExtensionRegistry

client=TestClient(api.app,client=("127.0.0.1",50000))

def test_agent_algorithms_mode_needs_no_model():
    response=client.post("/api/v1/agent/run",json={"goal":"inspect; test","mode":"algorithms"})
    assert response.status_code==200
    assert len(response.json()["algorithm_result"]["tasks"])==2
    assert response.json()["model_result"] is None

def test_runtime_settings_validation():
    assert client.post("/api/v1/settings/validate",json={"runtime_mode":"algorithms"}).status_code==200
    assert client.post("/api/v1/settings/validate",json={"runtime_mode":"unknown"}).status_code==400
    assert client.post("/api/v1/settings/validate",json={"litertlm_backend":"remote"}).status_code==400
    assert client.post("/api/v1/settings/validate",json={"litertlm_timeout_seconds":999}).status_code==422

def test_hybrid_mode_disabled_by_default():
    response=client.post("/api/v1/agent/run",json={"goal":"test","mode":"hybrid","model":"org/model","approved":True})
    assert response.status_code==400
    assert client.get("/api/v1/litertlm/status").json()["enabled"] is False

def test_github_extension_install_preview_and_skill_run(monkeypatch,tmp_path):
    original=api.extensions
    registry=GitHubExtensionRegistry(str(tmp_path/"extensions.db"))
    skill={"schema":"mojo.extension.v1","kind":"skill","name":"test-skill","version":"1.0","description":"Test skill","instructions":"Review and explain the task.","tools":["text_stats"]}
    monkeypatch.setattr("mojo_agent.extensions._fetch_manifest",lambda *args:(skill,"c"*64))
    try:
        api.extensions=registry
        preview=client.post("/api/v1/extensions/github/preview",json={"repository":"sample/repo","ref":"main","manifest_path":"skill.json"})
        assert preview.status_code==200 and preview.json()["code_execution"] is False if "code_execution" in preview.json() else preview.status_code==200
        installed=client.post("/api/v1/extensions/github/install",json={"repository":"sample/repo","ref":"main","manifest_path":"skill.json"})
        assert installed.status_code==200 and installed.json()["kind"]=="skill"
        run=client.post("/api/v1/skills/test-skill/run",json={"goal":"inspect"})
        assert run.status_code==200 and run.json()["allowed_tools"]==["text_stats"]
        assert client.get("/api/v1/extensions?kind=skill").json()["items"][0]["name"]=="test-skill"
    finally:
        api.extensions=original
