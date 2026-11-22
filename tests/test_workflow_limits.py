import pytest
from mojo_agent.workflows import WorkflowStore
from mojo_agent.tools import ToolRegistry
def test_rejects_oversized_and_unknown_steps(tmp_path):
 s=WorkflowStore(str(tmp_path/"w.sqlite3"))
 with pytest.raises(ValueError):s.create("bad",[{"type":"text","value":"x"*10001}])
 with pytest.raises(ValueError):s.create("bad",[{"type":"shell","command":"whoami"}])
def test_failed_run_is_recorded(tmp_path):
 s=WorkflowStore(str(tmp_path/"w.sqlite3"));w=s.create("bad",[{"type":"calculator","expression":"1/0"}])
 r=s.run(w["id"],ToolRegistry())
 assert r["status"]=="failed" and s.history(workflow_id=w["id"])[0]["status"]=="failed"
