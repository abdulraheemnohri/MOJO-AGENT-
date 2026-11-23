import pytest
from mojo_agent.litertlm import LiteRTLM,LiteRTLMError

def test_status_optional(monkeypatch):
    monkeypatch.setattr("mojo_agent.litertlm.shutil.which",lambda _:None)
    assert LiteRTLM().status()["available"] is False

def test_requires_approval():
    with pytest.raises(PermissionError): LiteRTLM().run("org/model","hello")

def test_model_validation(tmp_path):
    assert LiteRTLM.validate_model("org/model")[1] is True
    with pytest.raises(ValueError): LiteRTLM.validate_model("../evil")
    with pytest.raises(ValueError): LiteRTLM.validate_model("missing.gguf")
    model=tmp_path/"model.litertlm";model.write_bytes(b"x")
    assert LiteRTLM.validate_model(str(model))[1] is False

def test_run_is_shell_free_and_timeout_bounded(monkeypatch,tmp_path):
    model=tmp_path/"model.litertlm";model.write_bytes(b"x")
    monkeypatch.setattr("mojo_agent.litertlm.shutil.which",lambda _: "/usr/bin/litert-lm")
    seen={}
    class Result: returncode=0;stdout="answer";stderr=""
    def fake(command,**kwargs): seen.update(kwargs);seen["command"]=command;return Result()
    monkeypatch.setattr("mojo_agent.litertlm.subprocess.run",fake)
    result=LiteRTLM(timeout_seconds=999).run(str(model),"hello",approved=True)
    assert result["output"]=="answer" and seen["shell"] is False and seen["timeout"]==180
    assert "--prompt=hello" in seen["command"]

def test_rejects_invalid_prompt_and_backend():
    with pytest.raises(ValueError): LiteRTLM().run("org/model"," ",approved=True)
    with pytest.raises(ValueError): LiteRTLM().run("org/model","hello",backend="remote",approved=True)

def test_cli_missing(monkeypatch):
    monkeypatch.setattr("mojo_agent.litertlm.shutil.which",lambda _:None)
    with pytest.raises(LiteRTLMError): LiteRTLM().run("org/model","hello",approved=True)


def test_hugging_face_repo_id_uses_supported_native_cli_flag(monkeypatch):
    monkeypatch.setattr("mojo_agent.litertlm.shutil.which",lambda _: "/usr/bin/litert-lm")
    seen={}
    class Result: returncode=0;stdout="answer";stderr=""
    def fake(command,**kwargs): seen["command"]=command;return Result()
    monkeypatch.setattr("mojo_agent.litertlm.subprocess.run",fake)
    result=LiteRTLM().run("Qwen/Qwen3-0.6B","hello",approved=True)
    assert result["model_source"]=="huggingface"
    assert "--from-huggingface-repo=Qwen/Qwen3-0.6B" in seen["command"]
    assert not any(item == "Qwen/Qwen3-0.6B" for item in seen["command"])
    assert not any(item.endswith(".litertlm") for item in seen["command"])

def test_hugging_face_benchmark_uses_supported_native_cli_flag(monkeypatch):
    monkeypatch.setattr("mojo_agent.litertlm.shutil.which",lambda _: "/usr/bin/litert-lm")
    seen={}
    class Result: returncode=0;stdout="benchmark";stderr=""
    def fake(command,**kwargs): seen["command"]=command;return Result()
    monkeypatch.setattr("mojo_agent.litertlm.subprocess.run",fake)
    result=LiteRTLM().benchmark("org/model",approved=True)
    assert result["model_source"]=="huggingface"
    assert seen["command"]==["litert-lm","benchmark","--from-huggingface-repo=org/model"]
