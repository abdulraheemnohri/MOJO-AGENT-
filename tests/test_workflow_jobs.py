import json
import sqlite3
import pytest
from mojo_agent.workflows import WorkflowStore
from mojo_agent.tools import ToolRegistry

def test_queue_snapshots_workflow_and_executes(tmp_path):
    store=WorkflowStore(str(tmp_path/"jobs.db"))
    workflow=store.create("queue", [{"type":"text","value":"original"}])
    job=store.enqueue(workflow["id"],max_attempts=2,now=100)
    store.update(workflow["id"],"edited",[{"type":"text","value":"changed"}])
    assert job["status"]=="queued"
    result=store.worker_tick(ToolRegistry(),now=101,limit=2)
    assert result["processed"]==1
    finished=store.get_job(job["id"])
    assert finished["status"]=="completed"
    assert finished["result"][0]["result"]=="original"
    assert finished["attempts"]==1

def test_cancel_queued_and_retry_job(tmp_path):
    store=WorkflowStore(str(tmp_path/"jobs.db"))
    w=store.create("cancel", [{"type":"text","value":"hello"}])
    job=store.enqueue(w["id"],now=100)
    assert store.cancel_job(job["id"])["status"]=="cancelled"
    retried=store.retry_job(job["id"],now=200)
    assert retried["status"]=="queued" and retried["attempts"]==0

def test_worker_recovers_interrupted_job(tmp_path):
    store=WorkflowStore(str(tmp_path/"jobs.db"))
    w=store.create("recover", [{"type":"text","value":"hello"}])
    job=store.enqueue(w["id"],max_attempts=3,now=10)
    claimed=store.claim_job("crashed-worker",now=11)
    assert claimed["id"]==job["id"] and claimed["status"]=="running"
    result=store.recover_interrupted(now=12)
    assert result["recovered"]==1
    restored=store.get_job(job["id"])
    assert restored["status"]=="queued"
    assert restored["error"]=="Recovered after worker interruption"

def test_queue_limits_and_invalid_filters(tmp_path):
    store=WorkflowStore(str(tmp_path/"jobs.db"))
    w=store.create("limits", [{"type":"text","value":"hello"}])
    with pytest.raises(ValueError):store.enqueue(w["id"],max_attempts=11)
    with pytest.raises(ValueError):store.worker_tick(ToolRegistry(),limit=11)
    with pytest.raises(ValueError):store.list_jobs(status="bogus")


def test_worker_tick_also_processes_due_schedules(tmp_path):
    store=WorkflowStore(str(tmp_path/"jobs.db"))
    workflow=store.create("scheduled-worker",[{"type":"text","value":"scheduled"}])
    schedule=store.create_schedule(workflow["id"],60,now=100)
    result=store.worker_tick(ToolRegistry(),now=160,limit=2)
    assert result["scheduled"]["executed"]==1
    assert result["scheduled"]["runs"][0]["status"]=="completed"
    assert store.get_schedule(schedule["id"])["last_status"]=="completed"


def test_template_step_maps_only_prior_step_results(tmp_path):
    store=WorkflowStore(str(tmp_path/"templates.db"))
    workflow=store.create("mapped",[
        {"type":"text","value":"MOJO"},
        {"type":"template","template":"Hello {{project}}!","inputs":{"project":0}},
        {"type":"text_stats","text":"{{project}}"}
    ])
    result=store.run(workflow["id"],ToolRegistry())
    assert result["status"]=="completed"
    assert result["results"][1]["result"]=="Hello MOJO!"
    # Placeholders are literal unless explicitly mapped; no expression evaluation occurs.
    assert result["results"][2]["result"]["words"]==1


def test_template_rejects_forward_and_invalid_references(tmp_path):
    store=WorkflowStore(str(tmp_path/"invalid-templates.db"))
    with pytest.raises(ValueError):
        store.create("forward",[
            {"type":"template","template":"{{later}}","inputs":{"later":1}},
            {"type":"text","value":"not yet"}
        ])
    with pytest.raises(ValueError):
        store.create("bad-name",[
            {"type":"text","value":"safe"},
            {"type":"template","template":"{{x}}","inputs":{"x;DROP":0}}
        ])
    with pytest.raises(ValueError):
        store.create("bad-index",[
            {"type":"text","value":"safe"},
            {"type":"template","template":"{{x}}","inputs":{"x":True}}
        ])


def test_queued_job_executes_template_snapshot(tmp_path):
    store=WorkflowStore(str(tmp_path/"queued-template.db"))
    workflow=store.create("queued template",[
        {"type":"text","value":"snapshot"},
        {"type":"template","template":"value={{item}}","inputs":{"item":0}}
    ])
    job=store.enqueue(workflow["id"],now=10)
    store.update(workflow["id"],"changed",[{"type":"text","value":"edited"}])
    result=store.worker_tick(ToolRegistry(),now=11,limit=1)
    assert result["processed"]==1
    finished=store.get_job(job["id"])
    assert finished["status"]=="completed"
    assert finished["result"][1]["result"]=="value=snapshot"
