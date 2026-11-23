from fastapi.testclient import TestClient
from mojo_agent import api
from mojo_agent.settings import SettingsStore

def test_api_token_is_hashed_and_rotation_revokes_old_token(monkeypatch,tmp_path):
    store=SettingsStore(str(tmp_path/"auth.sqlite3"))
    monkeypatch.setattr(api,"settings",store)
    client=TestClient(api.app,client=("127.0.0.1",50001))

    bootstrap=client.post("/api/v1/security/token/bootstrap")
    assert bootstrap.status_code==200
    token=bootstrap.json()["token"]
    assert token and len(token)>40
    public_settings=client.get("/api/v1/settings")
    assert public_settings.status_code==401
    assert "api_auth_hash" not in store.get()
    assert "api_auth_salt" not in store.get()

    authorized=client.get("/api/v1/settings",headers={"Authorization":"Bearer "+token})
    assert authorized.status_code==200
    assert authorized.json()["api_auth_enabled"] is True

    rotated=client.post("/api/v1/security/token/rotate",headers={"Authorization":"Bearer "+token})
    assert rotated.status_code==200
    new_token=rotated.json()["token"]
    assert client.get("/api/v1/settings",headers={"Authorization":"Bearer "+token}).status_code==401
    assert client.get("/api/v1/settings",headers={"Authorization":"Bearer "+new_token}).status_code==200

    revoked=client.delete("/api/v1/security/token",headers={"Authorization":"Bearer "+new_token})
    assert revoked.status_code==200
    assert store.auth_status()["enabled"] is False
    assert client.get("/api/v1/settings").status_code==200

def test_api_token_bootstrap_rejects_non_loopback(monkeypatch,tmp_path):
    store=SettingsStore(str(tmp_path/"auth-remote.sqlite3"))
    monkeypatch.setattr(api,"settings",store)
    client=TestClient(api.app,client=("192.0.2.10",50002))
    assert client.post("/api/v1/security/token/bootstrap").status_code==403

def test_auth_status_never_exposes_secret_material(tmp_path):
    store=SettingsStore(str(tmp_path/"auth-status.sqlite3"))
    token=store.create_api_token()
    status=store.auth_status()
    assert status=={"enabled":True,"configured":True,"algorithm":"PBKDF2-HMAC-SHA256"}
    assert token not in str(status)
    assert store.verify_api_token(token)
    assert not store.verify_api_token("incorrect")
