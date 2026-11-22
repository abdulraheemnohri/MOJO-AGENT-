import sys
from mojo_agent import cli

def test_legacy_backend_flags_still_work(monkeypatch):
    called={}
    monkeypatch.setattr(sys,"argv",["mojo-agent","--host","127.0.0.1","--port","8766"])
    monkeypatch.setattr(cli.uvicorn,"run",lambda *a,**kw:called.update(kw))
    assert cli.main()==0
    assert called["host"]=="127.0.0.1" and called["port"]==8766

def test_serve_subcommand_uses_environment_defaults(monkeypatch):
    called={}
    monkeypatch.setattr(sys,"argv",["mojo-agent","serve"])
    monkeypatch.setattr(cli.uvicorn,"run",lambda *a,**kw:called.update(kw))
    assert cli.main()==0
    assert called["host"]=="127.0.0.1" and called["port"]==8766

def test_litertlm_status_command(monkeypatch,capsys):
    monkeypatch.setattr(sys,"argv",["mojo-agent","litertlm","status"])
    monkeypatch.setattr("mojo_agent.litertlm.shutil.which",lambda _:None)
    assert cli.main()==0
    assert "available" in capsys.readouterr().out
