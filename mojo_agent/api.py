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
app=FastAPI(title='MOJO AGENT API',version='0.2.0',description='Local algorithmic agent runtime; no LLM required.')
memory=MemoryStore();evolution=EvolutionEngine();tools=ToolRegistry();workflows=WorkflowStore();knowledge=KnowledgeGraph();analytics=Analytics()
class Goal(BaseModel):goal:str=Field(min_length=1,max_length=2000)
class MemoryInput(BaseModel):content:str=Field(min_length=1,max_length=10000);kind:str='episodic';importance:float=Field(default=.5,ge=0,le=1)
class QInput(BaseModel):q:float;reward:float;next_max:float=0;alpha:float=Field(default=.1,ge=0,le=1);gamma:float=Field(default=.95,ge=0,le=1)
class WorkflowInput(BaseModel):name:str=Field(min_length=1,max_length=120);steps:list[dict]=Field(min_length=1,max_length=50)
class NodeInput(BaseModel):label:str=Field(min_length=1,max_length=300);kind:str='concept';properties:dict={}
class EdgeInput(BaseModel):source:str;target:str;relation:str='related_to';weight:float=Field(default=1,ge=0,le=100)
class ToolInput(BaseModel):name:str;arguments:dict={};approved:bool=False
@app.get('/api/v1/health')
def health():return {'status':'ok','name':'MOJO AGENT','version':'0.2.0','llm':'disabled','runtime':'python-reference','platform':'cross-platform'}
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
 return {'generation':evolution.generation,'candidates':[{'fitness':c.fitness,'strategy':c.strategy.__dict__} for c in candidates],'activation':'manual approval required'}
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
def security_status():return {'mode':'local-only','tool_allowlist':tools.list_tools(),'approval_required':True,'shell_execution':False,'source_self_modification':False,'remote_access':'not configured'}
@app.get('/api/v1/settings')
def get_settings():return {'runtime':'python-reference','llm_enabled':False,'api_host':'127.0.0.1','api_port':8766,'memory':'sqlite','evolution_auto_activate':False,'tool_approval_required':True,'theme':'dark'}
