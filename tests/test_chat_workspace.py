from types import SimpleNamespace
from fastapi.testclient import TestClient
from mojo_agent import api
from mojo_agent.chat import ChatStore
from mojo_agent.settings import SettingsStore

def _client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "chat_store", ChatStore(str(tmp_path / "chat.sqlite3")))
    monkeypatch.setattr(api, "settings", SettingsStore(str(tmp_path / "settings.sqlite3")))
    return TestClient(api.app, client=("127.0.0.1", 51001))

def test_conversation_persistence_and_algorithm_chat(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    created = client.post("/api/v1/chat/conversations", json={"title": "New chat"})
    assert created.status_code == 200
    conversation_id = created.json()["id"]
    sent = client.post(f"/api/v1/chat/conversations/{conversation_id}/send",
                       json={"content": "Plan; implement; test the application"})
    assert sent.status_code == 200
    assert sent.json()["model_mode"] == "algorithms"
    assert "deterministic Algorithms mode" in sent.json()["assistant_message"]["content"]
    history = client.get(f"/api/v1/chat/conversations/{conversation_id}/messages")
    assert history.status_code == 200
    assert [m["role"] for m in history.json()["items"]] == ["user", "assistant"]
    assert client.get("/api/v1/chat/conversations").json()["items"][0]["message_count"] == 2
    assert client.delete(f"/api/v1/chat/conversations/{conversation_id}").json()["deleted"] is True

def test_litertlm_chat_requires_explicit_approval_and_uses_selected_model(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    api.settings.update({"litertlm_enabled": True, "litertlm_model": "local/model.litertlm"})
    class FakeRuntime:
        def run(self, model, prompt, backend="cpu", approved=False):
            assert approved is True
            assert model == "local/model.litertlm"
            assert "USER: Explain the result" in prompt
            return {"output": "Model answer", "model_source": "local"}
    monkeypatch.setattr(api, "agent_runtime", SimpleNamespace(model_runtime=FakeRuntime()))
    conversation = client.post("/api/v1/chat/conversations", json={"mode": "litertlm"}).json()
    denied = client.post(f"/api/v1/chat/conversations/{conversation['id']}/send",
                         json={"content": "Explain the result", "mode": "litertlm"})
    assert denied.status_code == 403
    allowed = client.post(f"/api/v1/chat/conversations/{conversation['id']}/send",
                          json={"content": "Explain the result", "mode": "litertlm", "approved": True})
    assert allowed.status_code == 200
    assert allowed.json()["assistant_message"]["content"] == "Model answer"

def test_chat_tools_are_separate_and_require_approval(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    conversation = client.post("/api/v1/chat/conversations", json={}).json()
    path = f"/api/v1/chat/conversations/{conversation['id']}/tools/execute"
    denied = client.post(path, json={"name": "calculator", "arguments": {"expression": "2+2"}})
    assert denied.status_code == 403
    allowed = client.post(path, json={"name": "calculator", "arguments": {"expression": "2+2"}, "approved": True})
    assert allowed.status_code == 200
    assert allowed.json()["result"]["result"] == 4
    assert allowed.json()["message"]["role"] == "tool"

def test_chat_attachment_size_type_and_text_extraction(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    conversation = client.post("/api/v1/chat/conversations", json={}).json()
    path = f"/api/v1/chat/conversations/{conversation['id']}/attachments"
    uploaded = client.post(path + "?filename=notes.txt", content=b"local notes", headers={"content-type": "text/plain"})
    assert uploaded.status_code == 200
    attachment_id = uploaded.json()["id"]
    sent = client.post(f"/api/v1/chat/conversations/{conversation['id']}/send",
                       json={"content": "Summarize this", "attachments": [attachment_id]})
    assert sent.status_code == 200
    assert "UTF-8 text is available as context" in sent.json()["assistant_message"]["content"]
    bad = client.post(path + "?filename=payload.exe", content=b"no", headers={"content-type": "application/octet-stream"})
    assert bad.status_code == 400

def test_chat_settings_validation():
    client = TestClient(api.app, client=("127.0.0.1", 51002))
    assert client.post("/api/v1/settings/validate", json={"chat_default_mode": "litertlm", "litertlm_enabled": True}).status_code == 200
    assert client.post("/api/v1/settings/validate", json={"chat_default_mode": "cloud"}).status_code == 400
    assert client.post("/api/v1/settings/validate", json={"chat_max_history": 99}).status_code == 422

def test_local_model_catalog_validation_and_selection(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    class FakeRuntime:
        def status(self):
            return {"available": True, "huggingface_repo_cli_available": True, "local_model_cli_available": True}
    monkeypatch.setattr(api, "agent_runtime", SimpleNamespace(model_runtime=FakeRuntime()))
    added = client.post("/api/v1/chat/models", json={"label": "Tiny model", "model_id": "acme/tiny-model", "backend": "cpu"})
    assert added.status_code == 200
    catalog = client.get("/api/v1/chat/models").json()
    assert any(item.get("model_id") == "acme/tiny-model" for item in catalog["items"])
    selected = client.post("/api/v1/chat/models/" + added.json()["id"] + "/select", json={})
    assert selected.status_code == 200
    assert api.settings.get()["litertlm_model"] == "acme/tiny-model"
    assert client.delete("/api/v1/chat/models/" + added.json()["id"]).json()["deleted"] is True

def test_chat_skill_plan_is_recorded_without_executing_tools(tmp_path, monkeypatch):
    from mojo_agent.extensions import GitHubExtensionRegistry
    original = api.extensions
    registry = GitHubExtensionRegistry(str(tmp_path / "skills.sqlite3"))
    manifest = {"schema":"mojo.extension.v1","kind":"skill","name":"chat-skill","version":"1.0",
                "description":"Plan tasks","instructions":"Break down the requested task.","tools":["text_stats"]}
    monkeypatch.setattr("mojo_agent.extensions._fetch_manifest", lambda *args: (manifest, "a"*64))
    monkeypatch.setattr(api, "extensions", registry)
    client = _client(tmp_path, monkeypatch)
    try:
        registry.install("acme/chat-skill", "main", "skill.json", expected_sha256="a"*64)
        conversation = client.post("/api/v1/chat/conversations", json={}).json()
        response = client.post(f"/api/v1/chat/conversations/{conversation['id']}/skills/chat-skill/plan",
                               json={"goal":"Inspect the code; write tests"})
        assert response.status_code == 200
        assert response.json()["plan"]["execution"].startswith("plan only")
        assert response.json()["message"]["role"] == "tool"
    finally:
        monkeypatch.setattr(api, "extensions", original)

def test_chat_export_and_clear_remove_messages_and_attachments(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    conversation = client.post("/api/v1/chat/conversations", json={}).json()
    conversation_id = conversation["id"]
    client.post(f"/api/v1/chat/conversations/{conversation_id}/send", json={"content":"Keep this locally"})
    upload = client.post(f"/api/v1/chat/conversations/{conversation_id}/attachments?filename=keep.txt",
                         content=b"attachment", headers={"content-type":"text/plain"})
    assert upload.status_code == 200
    exported = client.get(f"/api/v1/chat/conversations/{conversation_id}/export")
    assert exported.status_code == 200
    assert exported.json()["format"] == "mojo-chat-v1"
    assert len(exported.json()["messages"]) == 2
    cleared = client.delete(f"/api/v1/chat/conversations/{conversation_id}/messages")
    assert cleared.status_code == 200
    assert client.get(f"/api/v1/chat/conversations/{conversation_id}/messages").json()["items"] == []
    assert client.get(f"/api/v1/chat/conversations/{conversation_id}/attachments").json()["items"] == []
