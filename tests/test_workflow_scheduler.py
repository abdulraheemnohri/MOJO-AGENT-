import pytest
from mojo_agent.workflows import WorkflowStore
from mojo_agent.tools import ToolRegistry

def test_schedule_is_persistent_and_due_run_is_bounded(tmp_path):
    path = str(tmp_path / "workflow.sqlite3")
    store = WorkflowStore(path)
    workflow = store.create("scheduled", [{"type": "text", "value": "hello"}])
    schedule = store.create_schedule(workflow["id"], 60, now=1000)
    assert schedule["next_run"] == 1060
    assert store.run_due(ToolRegistry(), now=1059)["executed"] == 0
    result = store.run_due(ToolRegistry(), now=1060)
    assert result["executed"] == 1
    assert result["runs"][0]["status"] == "completed"
    restored = WorkflowStore(path)
    assert restored.get_schedule(schedule["id"])["last_status"] == "completed"
    assert restored.get_schedule(schedule["id"])["next_run"] == 1120

def test_schedule_validation_and_pause(tmp_path):
    store = WorkflowStore(str(tmp_path / "workflow.sqlite3"))
    workflow = store.create("scheduled", [{"type": "text", "value": "hello"}])
    with pytest.raises(ValueError):
        store.create_schedule(workflow["id"], 30)
    schedule = store.create_schedule(workflow["id"], 60, now=100)
    paused = store.set_schedule_enabled(schedule["id"], False, now=200)
    assert paused["enabled"] is False
    assert store.run_due(ToolRegistry(), now=100000)["executed"] == 0

def test_schedule_limit_and_missing_workflow(tmp_path):
    store = WorkflowStore(str(tmp_path / "workflow.sqlite3"))
    with pytest.raises(KeyError):
        store.create_schedule("missing", 60)
    with pytest.raises(ValueError):
        store.run_due(ToolRegistry(), limit=11)
