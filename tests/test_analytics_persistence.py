import pytest
from mojo_agent.analytics import Analytics

def test_analytics_persists_and_filters_events(tmp_path):
    path = str(tmp_path / "events.sqlite3")
    store = Analytics(path)
    store.record("plan_created", {"tasks": 3})
    store.record("memory_added")
    restored = Analytics(path)
    all_events = restored.summary(limit=10)
    assert all_events["events_total"] == 2
    assert all_events["counts"] == {"plan_created": 1, "memory_added": 1}
    filtered = restored.summary(limit=5, event="plan_created")
    assert filtered["events_total"] == 1
    assert filtered["recent"][0]["detail"] == {"tasks": 3}

def test_analytics_validates_and_bounds_inputs(tmp_path):
    store = Analytics(str(tmp_path / "events.sqlite3"), retention=100)
    with pytest.raises(ValueError):
        store.record("")
    with pytest.raises(ValueError):
        store.record("bad", {"number": float("nan")})
    for i in range(105):
        store.record("tick", {"n": i})
    assert store.summary(limit=200)["events_total"] == 100

def test_analytics_rejects_invalid_query(tmp_path):
    store = Analytics(str(tmp_path / "events.sqlite3"))
    with pytest.raises(ValueError):
        store.summary(event="x" * 101)
