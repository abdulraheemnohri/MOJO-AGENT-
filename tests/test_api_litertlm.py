from fastapi.testclient import TestClient
from mojo_agent import api
from mojo_agent.settings import SettingsStore

client=TestClient(api.app,client=("127.0.0.1",50000))

def test_litertlm_status_disabled_by_default():
    response=client.get("/api/v1/litertlm/status")
    assert response.status_code==200
    assert response.json()["enabled"] is False

def test_litertlm_execution_requires_enable_setting():
    response=client.post("/api/v1/litertlm/run",json={
        "model":"litert-community/gemma-4-E2B-it-litert-lm",
        "prompt":"Hello","approved":True
    })
    assert response.status_code==403

def test_litertlm_settings_validation():
    good=client.post("/api/v1/settings/validate",json={
        "litertlm_enabled":True,"litertlm_backend":"gpu","litertlm_timeout_seconds":90
    })
    assert good.status_code==200 and good.json()["valid"] is True
    assert client.post("/api/v1/settings/validate",json={"litertlm_backend":"remote"}).status_code==400
    assert client.post("/api/v1/settings/validate",json={"litertlm_timeout_seconds":999}).status_code==422

def test_litertlm_settings_persist(tmp_path):
    original=api.settings
    try:
        api.settings=SettingsStore(str(tmp_path/"settings.sqlite3"))
        saved=api.settings.update({"litertlm_enabled":True,"litertlm_backend":"gpu"})
        assert saved["litertlm_enabled"] is True
        assert saved["litertlm_backend"]=="gpu"
    finally:
        api.settings=original
