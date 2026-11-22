from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from .algorithms import q_update
from .planner import decompose_goal,topological_order
from .evolution import EvolutionEngine
from .memory import MemoryStore
from .tools import ToolRegistry
from .workflows import WorkflowStore
from .knowledge import KnowledgeGraph
from .analytics import Analytics
from .settings import SettingsStore
import math,uuid
app=FastAPI(title='MOJO AGENT API',version='0.4.0',description='Local algorithmic agent runtime; no LLM required.')
memory=MemoryStore();evolution=EvolutionEngine();tools=ToolRegistry();workflows=WorkflowStore();knowledge=KnowledgeGraph();analytics=Analytics();settings=SettingsStore();candidate_registry={}
class Goal(BaseModel):goal:str=Field(min_length=1,max_length=2000)
class MemoryInput(BaseModel):content:str=Field(min_length=1,max_length=10000);kind:str='episodic';importance:float=Field(default=.5,ge=0,le=1)
class QInput(BaseModel):q:float;reward:float;next_max:float=0;alpha:float=Field(default=.1,ge=0,le=1);gamma:float=Field(default=.95,ge=0,le=1)
class WorkflowInput(BaseModel):name:str=Field(min_length=1,max_length=120);steps:list[dict]=Field(min_length=1,max_length=50)
class NodeInput(BaseModel):label:str=Field(min_length=1,max_length=300);kind:str='concept';properties:dict={}
class EdgeInput(BaseModel):source:str;target:str;relation:str='related_to';weight:float=Field(default=1,ge=0,le=100)
class ToolInput(BaseModel):name:str;arguments:dict={};approved:bool=False
class SettingsInput(BaseModel):theme:str|None=None;api_host:str|None=None;api_port:int|None=Field(default=None,ge=1024,le=65535);tool_approval_required:bool|None=None
class ApprovalInput(BaseModel):approved:bool
@app.get('/api/v1/health')
def health():return {'status':'ok','name':'MOJO AGENT','version':'0.4.0','llm':'disabled','runtime':'python-reference','platform':'cross-platform'}
@app.post('/api/v1/plan')
def plan(req:Goal):
 try:
  tasks=decompose_goal(req.goal);order=topological_order({t['id']:t['depends_on'] for t in tasks});analytics.record('plan_created');return {'goal':req.goal,'tasks':tasks,'execution_order':order}
 except ValueError as e:raise HTTPException(400,str(e))
@app.post('/api/v1/algorithms/q-update')
def qlearn(req:QInput):return {'updated_q':q_update(req.q,req.reward,req.next_max,req.alpha,req.gamma)}
@app.post('/api/v1/memory')
def add_memory(req:MemoryInput):
 try:
  ident=memory.add(req.content,req.kind,req.importance);analytics.record('memory_added');return {'id':ident}
 except ValueError as e:raise HTTPException(400,str(e))
@app.get('/api/v1/memory')
def search_memory(q:str='',limit:int=20):
 try:return {'items':memory.search(q,limit)}
 except ValueError as e:raise HTTPException(400,str(e))
@app.get('/api/v1/evolution/status')
def status():return {'generation':evolution.generation,'population_size':evolution.population_size,'champion':evolution.champion.__dict__,'approval_required':True,'source_mutation':'disabled'}
@app.post('/api/v1/evolution/experiment')
def experiment():
 candidates=evolution.evolve(lambda s:1-abs(s.learning_rate-.2)-abs(s.exploration-.1));analytics.record('evolution_experiment')
 payload=[]
 for c in candidates:
  ident=str(uuid.uuid4());candidate_registry[ident]=c
  payload.append({'id':ident,'fitness':c.fitness,'strategy':c.strategy.__dict__,'tests_passed':c.tests_passed,'approved':c.approved})
 return {'generation':evolution.generation,'candidates':payload,'activation':'manual approval required'}
@app.post('/api/v1/evolution/candidates/{candidate_id}/validate')
def validate_candidate(candidate_id:str):
 c=candidate_registry.get(candidate_id)
 if not c:raise HTTPException(404,'Candidate not found; run a new experiment')
 try:c.tests_passed=evolution.validate_candidate(c,lambda s: (s.validate() is None and all(math.isfinite(v) for v in (s.learning_rate,s.exploration,s.discount))))
 except (ValueError,TypeError):c.tests_passed=False
 analytics.record('candidate_validated',{'passed':c.tests_passed})
 return {'id':candidate_id,'tests_passed':c.tests_passed,'activation':'not activated'}
@app.post('/api/v1/evolution/candidates/{candidate_id}/approve')
def approve_candidate(candidate_id:str,req:ApprovalInput):
 c=candidate_registry.get(candidate_id)
 if not c:raise HTTPException(404,'Candidate not found; run a new experiment')
 try:evolution.approve_candidate(c,req.approved);analytics.record('candidate_approved');return {'id':candidate_id,'approved':True,'champion':evolution.champion.__dict__}
 except (ValueError,PermissionError) as e:raise HTTPException(400,str(e))
@app.get('/api/v1/tools')
def list_tools():return {'tools':tools.list_tools()}
@app.post('/api/v1/tools/execute')
def execute_tool(req:ToolInput):
 try:return {'result':tools.execute(req.name,req.arguments,approved=req.approved)}
 except PermissionError as e:raise HTTPException(403,str(e))
 except (ValueError,KeyError) as e:raise HTTPException(400,str(e))
@app.get('/api/v1/workflows')
def list_workflows():return {'items':workflows.list(),'history':workflows.history()}
@app.post('/api/v1/workflows')
def create_workflow(req:WorkflowInput):
 try:
  w=workflows.create(req.name,req.steps);analytics.record('workflow_created');return w
 except ValueError as e:raise HTTPException(400,str(e))
@app.post('/api/v1/workflows/{workflow_id}/run')
def run_workflow(workflow_id:str):
 try:
  result=workflows.run(workflow_id,tools);analytics.record('workflow_run',{'status':result['status']});return result
 except KeyError as e:raise HTTPException(404,str(e))
@app.get('/api/v1/knowledge')
def graph():return knowledge.snapshot()
@app.get('/api/v1/knowledge/search')
def search_graph(q:str):
 snap=knowledge.snapshot();q=q.casefold()
 return {'nodes':[n for n in snap['nodes'] if q in n['label'].casefold() or q in n['kind'].casefold()]}
@app.post('/api/v1/knowledge/nodes')
def add_node(req:NodeInput):
 try:return knowledge.add_node(req.label,req.kind,req.properties)
 except ValueError as e:raise HTTPException(400,str(e))
@app.post('/api/v1/knowledge/edges')
def add_edge(req:EdgeInput):
 try:return knowledge.add_edge(req.source,req.target,req.relation,req.weight)
 except ValueError as e:raise HTTPException(400,str(e))
@app.get('/api/v1/analytics')
def analytics_summary():return analytics.summary()
@app.get('/api/v1/security/status')
def security_status():return {'mode':'local-only','tool_allowlist':tools.list_tools(),'approval_required':settings.get()['tool_approval_required'],'shell_execution':False,'source_self_modification':False,'remote_access':'not configured'}
@app.get('/api/v1/settings')
def get_settings():return settings.get()
@app.patch('/api/v1/settings')
def patch_settings(req:SettingsInput):
 try:return settings.update({k:v for k,v in req.model_dump().items() if v is not None})
 except ValueError as e:raise HTTPException(400,str(e))

# Resource lifecycle endpoints: explicit IDs, bounded payloads, and cascade-safe deletion.
class MemoryUpdate(BaseModel):
    content: str | None = Field(default=None, max_length=10000)
    kind: str | None = None
    importance: float | None = Field(default=None, ge=0, le=1)

@app.patch('/api/v1/memory/{memory_id}')
def update_memory(memory_id: int, req: MemoryUpdate):
    try:
        item = memory.update(memory_id, **req.model_dump(exclude_unset=True))
        if item is None:
            raise HTTPException(404, 'Memory not found')
        analytics.record('memory_updated')
        return item
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete('/api/v1/memory/{memory_id}')
def delete_memory(memory_id: int):
    if not memory.delete(memory_id):
        raise HTTPException(404, 'Memory not found')
    analytics.record('memory_deleted')
    return {'deleted': True, 'id': memory_id}

@app.get('/api/v1/memory/export')
def export_memory():
    return {'format': 'mojo-memory-v1', 'items': memory.export_all()}

@app.delete('/api/v1/knowledge/nodes/{node_id}')
def delete_knowledge_node(node_id: str):
    if not knowledge.delete_node(node_id):
        raise HTTPException(404, 'Node not found')
    analytics.record('knowledge_node_deleted')
    return {'deleted': True, 'id': node_id}

@app.delete('/api/v1/knowledge/edges/{edge_id}')
def delete_knowledge_edge(edge_id: str):
    if not knowledge.delete_edge(edge_id):
        raise HTTPException(404, 'Edge not found')
    analytics.record('knowledge_edge_deleted')
    return {'deleted': True, 'id': edge_id}

class WorkflowUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    steps: list[dict] = Field(min_length=1, max_length=50)

@app.patch('/api/v1/workflows/{workflow_id}')
def update_workflow(workflow_id: str, req: WorkflowUpdate):
    try:
        if not workflows.update(workflow_id, req.name, req.steps):
            raise HTTPException(404, 'Workflow not found')
        analytics.record('workflow_updated')
        return workflows.get(workflow_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.delete('/api/v1/workflows/{workflow_id}')
def delete_workflow(workflow_id: str):
    if not workflows.delete(workflow_id):
        raise HTTPException(404, 'Workflow not found')
    analytics.record('workflow_deleted')
    return {'deleted': True, 'id': workflow_id}

class MemoryImport(BaseModel):
    format: str = 'mojo-memory-v1'
    items: list[dict] = Field(min_length=0, max_length=5000)

@app.post('/api/v1/memory/import')
def import_memory(req: MemoryImport):
    if req.format != 'mojo-memory-v1':
        raise HTTPException(400, 'Unsupported memory export format')
    added = 0
    try:
        for item in req.items:
            if not isinstance(item, dict):
                raise ValueError('Each memory item must be an object')
            memory.add(item.get('content'), item.get('kind', 'episodic'), item.get('importance', .5))
            added += 1
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, f'Import stopped after {added} records: {exc}')
    analytics.record('memory_imported', {'count': added})
    return {'imported': added}

@app.get('/api/v1/memory/export')
def export_memory():
    return {'format': 'mojo-memory-v1', 'items': memory.export_all()}
