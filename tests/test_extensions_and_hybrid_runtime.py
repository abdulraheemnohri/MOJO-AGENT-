import json
import pytest
from mojo_agent.extensions import GitHubExtensionRegistry, ExtensionError
from mojo_agent.agent_runtime import AgentRuntime
from mojo_agent.settings import SettingsStore

def test_skill_and_tool_manifests_are_declarative_only(tmp_path, monkeypatch):
    registry=GitHubExtensionRegistry(str(tmp_path/'extensions.db'))
    skill={"schema":"mojo.extension.v1","kind":"skill","name":"project-review","version":"1.0.0","description":"Review project structure","instructions":"Review the supplied project facts and report risks.","tools":["text_stats"]}
    tool={"schema":"mojo.extension.v1","kind":"tool","name":"uppercase-text","version":"1.0.0","description":"Uppercase text","operation":"uppercase"}
    def fake(repo,ref,path):
        data=skill if path.endswith("skill.json") else tool
        return data,"a"*64
    monkeypatch.setattr("mojo_agent.extensions._fetch_manifest",fake)
    assert registry.install("acme/demo","main","skill.json")["kind"]=="skill"
    assert registry.install("acme/demo","main","tool.json")["kind"]=="tool"
    assert len(registry.list())==2
    with pytest.raises(PermissionError): registry.execute_tool("uppercase-text",{"text":"hello"})
    assert registry.execute_tool("uppercase-text",{"text":"hello"},approved=True)=="HELLO"
    assert registry.uninstall("tool:uppercase-text")
    assert len(registry.list())==1

def test_unsupported_extension_code_is_rejected(tmp_path,monkeypatch):
    registry=GitHubExtensionRegistry(str(tmp_path/'extensions.db'))
    manifest={"schema":"mojo.extension.v1","kind":"tool","name":"evil-tool","description":"not allowed","operation":"run_shell"}
    monkeypatch.setattr("mojo_agent.extensions._fetch_manifest",lambda *args:(manifest,"b"*64))
    with pytest.raises(ExtensionError):registry.preview("acme/demo")

def test_settings_keep_algorithms_default_and_require_runtime_enable(tmp_path):
    store=SettingsStore(str(tmp_path/'settings.db'))
    assert store.get()["runtime_mode"]=="algorithms"
    with pytest.raises(ValueError):store.update({"runtime_mode":"hybrid"})
    result=store.update({"litertlm_enabled":True,"runtime_mode":"hybrid","litertlm_backend":"cpu"})
    assert result["runtime_mode"]=="hybrid"
    with pytest.raises(ValueError):store.update({"tool_approval_required":False})

class FakeModelRuntime:
    def __init__(self): self.called=False
    def status(self): return {"available":True}
    def run(self,model,prompt,backend="cpu",approved=False):
        self.called=True
        return {"output":"advisory suggestion","model":model,"backend":backend}

def test_hybrid_keeps_deterministic_plan_and_requires_approval():
    fake=FakeModelRuntime();runtime=AgentRuntime(fake)
    result=runtime.run("inspect; test",mode="algorithms")
    assert len(result["algorithm_result"]["tasks"])==2 and fake.called is False
    with pytest.raises(PermissionError):runtime.run("inspect",mode="hybrid",model="org/model")
    result=runtime.run("inspect",mode="hybrid",model="org/model",approved=True)
    assert result["model_result"]["output"]=="advisory suggestion"
    assert "advisory" in result["hybrid_policy"]
