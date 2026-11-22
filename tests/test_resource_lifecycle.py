import pytest
from mojo_agent.memory import MemoryStore
from mojo_agent.knowledge import KnowledgeGraph
from mojo_agent.workflows import WorkflowStore

def test_memory_update_delete_and_export(tmp_path):
    store = MemoryStore(str(tmp_path / "memory.db"))
    ident = store.add("first note", importance=.4)
    updated = store.update(ident, content="edited note", importance=.9)
    assert updated["content"] == "edited note"
    assert store.export_all()[0]["id"] == ident
    assert store.delete(ident) is True
    assert store.delete(ident) is False

def test_memory_rejects_invalid_values(tmp_path):
    store = MemoryStore(str(tmp_path / "memory.db"))
    with pytest.raises(ValueError):
        store.add("x", kind="unknown")
    with pytest.raises(ValueError):
        store.add("x" * 10001)

def test_knowledge_delete_node_cascades_edges(tmp_path):
    graph = KnowledgeGraph(str(tmp_path / "graph.db"))
    a = graph.add_node("A")
    b = graph.add_node("B")
    edge = graph.add_edge(a["id"], b["id"])
    assert graph.delete_node(a["id"])
    snapshot = graph.snapshot()
    assert len(snapshot["nodes"]) == 1
    assert snapshot["edges"] == []
    assert not graph.delete_edge(edge["id"])

def test_workflow_update_delete_and_history(tmp_path):
    store = WorkflowStore(str(tmp_path / "workflow.db"))
    workflow = store.create("demo", [{"type": "text", "value": "hello"}])
    assert store.update(workflow["id"], "renamed", [{"type": "text", "value": "world"}])
    assert store.get(workflow["id"])["name"] == "renamed"
    assert not store.update("missing", "name", [{"type": "text"}])
    assert store.delete(workflow["id"])
    assert store.get(workflow["id"]) is None
