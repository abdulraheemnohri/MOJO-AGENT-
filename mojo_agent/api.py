from fastapi import FastAPI,HTTPException,Response,Request
from fastapi.middleware.cors import CORSMiddleware
import socket
from pydantic import BaseModel,Field
from pathlib import Path
from .algorithms import q_update
from .planner import decompose_goal,topological_order
from .evolution import EvolutionEngine
from .evolution_store import EvolutionStore
from .memory import MemoryStore
from .tools import ToolRegistry
from .workflows import WorkflowStore
from .knowledge import KnowledgeGraph
from .analytics import Analytics
from .settings import SettingsStore
from .extensions import GitHubExtensionRegistry, ExtensionError
from .agent_runtime import AgentRuntime
from .litertlm import LiteRTLM, LiteRTLMError
from .database import DatabaseManager
from .chat import ChatStore, MAX_ATTACHMENT_BYTES
import math,uuid,time,platform,os,sqlite3,threading,hashlib,ipaddress,secrets,json
app=FastAPI(title='MOJO AGENT API',version='0.9.0',description='Local algorithmic agent runtime; no LLM required.')
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5173','http://localhost:5173','http://127.0.0.1:4173','http://localhost:4173'],allow_credentials=False,allow_methods=['GET','POST','PATCH','DELETE','OPTIONS'],allow_headers=['Content-Type','Authorization','X-Backup-SHA256'])
memory=MemoryStore();database=DatabaseManager(str(memory.path));database.migrate();chat_store=ChatStore(str(memory.path));evolution=EvolutionEngine();evolution_store=EvolutionStore();evolution.champion=evolution_store.get_champion();evolution.generation=evolution_store.get_generation();tools=ToolRegistry();workflows=WorkflowStore();knowledge=KnowledgeGraph();analytics=Analytics();settings=SettingsStore();extensions=GitHubExtensionRegistry();agent_runtime=AgentRuntime(LiteRTLM(timeout_seconds=settings.get()['litertlm_timeout_seconds']));litertlm=agent_runtime.model_runtime;candidate_registry={};RUNTIME_STARTED_AT=time.time();RUNTIME_LOGS=[];RUNTIME_LOG_LOCK=threading.Lock();RUNTIME_LOG_LIMIT=500
WORKER_STOP=threading.Event()
WORKER_THREAD=None
WORKER_ID="mojo-background-worker"

def _worker_loop():
 while not WORKER_STOP.is_set():
  try:
   prefs=settings.get()
   if prefs.get('worker_enabled'):
    workflows.worker_tick(tools,WORKER_ID,limit=prefs.get('worker_batch_size',3))
   WORKER_STOP.wait(max(1,min(60,int(prefs.get('worker_poll_seconds',2)))))
  except Exception as exc:
   _record_runtime_log('ERROR','Background worker cycle failed: '+str(exc)[:200])
   WORKER_STOP.wait(2)

@app.on_event("startup")
def start_background_worker():
 global WORKER_THREAD
 workflows.recover_interrupted()
 if WORKER_THREAD is None or not WORKER_THREAD.is_alive():
  WORKER_STOP.clear()
  WORKER_THREAD=threading.Thread(target=_worker_loop,name=WORKER_ID,daemon=True)
  WORKER_THREAD.start()

@app.on_event("shutdown")
def stop_background_worker():
 WORKER_STOP.set()
 if WORKER_THREAD and WORKER_THREAD.is_alive():WORKER_THREAD.join(timeout=3)


def _record_runtime_log(level,message,method=None,path=None,status=None,duration_ms=None):
 entry={'time':time.time(),'level':level,'message':message,'method':method,'path':path,'status':status,'duration_ms':duration_ms}
 with RUNTIME_LOG_LOCK:
  RUNTIME_LOGS.append(entry)
  if len(RUNTIME_LOGS)>RUNTIME_LOG_LIMIT: del RUNTIME_LOGS[:-RUNTIME_LOG_LIMIT]
 return entry
class Goal(BaseModel):goal:str=Field(min_length=1,max_length=2000)
class MemoryInput(BaseModel):content:str=Field(min_length=1,max_length=10000);kind:str='episodic';importance:float=Field(default=.5,ge=0,le=1)
class QInput(BaseModel):q:float;reward:float;next_max:float=0;alpha:float=Field(default=.1,ge=0,le=1);gamma:float=Field(default=.95,ge=0,le=1)
class WorkflowInput(BaseModel):name:str=Field(min_length=1,max_length=120);steps:list[dict]=Field(min_length=1,max_length=50)
class ScheduleInput(BaseModel):workflow_id:str;interval_seconds:int=Field(ge=60,le=2592000)
class ScheduleEnabledInput(BaseModel):enabled:bool
class WorkflowEnqueueInput(BaseModel):max_attempts:int|None=Field(default=None,ge=1,le=10)
class WorkerTickInput(BaseModel):limit:int=Field(default=5,ge=1,le=10);worker_id:str=Field(default='manual-worker',min_length=1,max_length=80)
class NodeInput(BaseModel):label:str=Field(min_length=1,max_length=300);kind:str='concept';properties:dict={}
class EdgeInput(BaseModel):source:str;target:str;relation:str='related_to';weight:float=Field(default=1,ge=0,le=100)
class ToolInput(BaseModel):name:str;arguments:dict={};approved:bool=False
class SettingsInput(BaseModel):theme:str|None=None;api_host:str|None=None;api_port:int|None=Field(default=None,ge=1024,le=65535);tool_approval_required:bool|None=None;runtime_mode:str|None=None;litertlm_enabled:bool|None=None;litertlm_backend:str|None=None;litertlm_timeout_seconds:int|None=Field(default=None,ge=10,le=180);litertlm_model:str|None=None;worker_enabled:bool|None=None;worker_poll_seconds:int|None=Field(default=None,ge=1,le=60);worker_batch_size:int|None=Field(default=None,ge=1,le=10);workflow_max_attempts:int|None=Field(default=None,ge=1,le=10);chat_default_mode:str|None=None;chat_system_prompt:str|None=Field(default=None,max_length=2000);chat_max_history:int|None=Field(default=None,ge=2,le=30)
class ApprovalInput(BaseModel):approved:bool
class AgentRunInput(BaseModel):goal:str=Field(min_length=1,max_length=2000);mode:str|None=None;model:str|None=None;backend:str|None=None;approved:bool=False
class GitHubExtensionInput(BaseModel):repository:str=Field(min_length=3,max_length=205);ref:str='main';manifest_path:str='mojo-extension.json'
class GitHubInstallInput(GitHubExtensionInput):expected_sha256:str=Field(min_length=64,max_length=64)
class InstalledToolInput(BaseModel):arguments:dict={};approved:bool=False
class SkillExecutionInput(BaseModel):operation:str=Field(min_length=1,max_length=40);arguments:dict={};approved:bool=False
class ChatConversationInput(BaseModel):title:str=Field(default='New chat',max_length=120);mode:str|None=None;model:str|None=None
class ChatConversationUpdate(BaseModel):title:str|None=Field(default=None,max_length=120);mode:str|None=None;model:str|None=None;system_prompt:str|None=Field(default=None,max_length=2000);archived:bool|None=None
class ChatSendInput(BaseModel):content:str=Field(default='',max_length=20000);mode:str|None=None;model:str|None=None;backend:str|None=None;approved:bool=False;attachments:list[str]=Field(default_factory=list,max_length=10)
class ChatToolInput(BaseModel):name:str=Field(min_length=1,max_length=48);arguments:dict={};approved:bool=False;skill_name:str|None=None;tool_source:str='builtin'
class ChatModelInput(BaseModel):label:str=Field(min_length=1,max_length=100);model_id:str=Field(min_length=1,max_length=512);backend:str='cpu'
from typing import Literal
class LiteRTLMRunInput(BaseModel):
    model: str = Field(min_length=1, max_length=512)
    prompt: str = Field(min_length=1, max_length=6000)
    backend: Literal['cpu', 'gpu'] = 'cpu'
    approved: bool = False

class LiteRTLMBenchmarkInput(BaseModel):
    model: str = Field(min_length=1, max_length=512)
    approved: bool = False

AUTH_EXEMPT_PATHS={'/api/v1/health','/api/v1/security/status','/api/v1/security/token/bootstrap'}

def _request_is_loopback(request):
 try:return ipaddress.ip_address(request.client.host).is_loopback
 except (ValueError,AttributeError):return False

@app.middleware("http")
async def enforce_api_token(request,call_next):
 path=request.url.path
 if request.method!='OPTIONS' and path.startswith('/api/v1/') and path not in AUTH_EXEMPT_PATHS and settings.auth_status()['enabled']:
  header=request.headers.get('authorization','')
  token=header[7:].strip() if header.lower().startswith('bearer ') else ''
  if not settings.verify_api_token(token):
   return Response(content='{"detail":"A valid MOJO API bearer token is required"}',status_code=401,media_type='application/json',headers={'WWW-Authenticate':'Bearer'})
 return await call_next(request)

@app.post('/api/v1/security/token/bootstrap')
def bootstrap_api_token(request:Request):
 if not _request_is_loopback(request):raise HTTPException(403,'Initial API token setup is restricted to loopback clients')
 if settings.auth_status()['enabled']:raise HTTPException(409,'API authentication is already enabled; use an authenticated token rotation')
 token=settings.create_api_token()
 _record_runtime_log('WARNING','Local API token created')
 return {'token':token,'warning':'Copy this token now. It is shown only once; MOJO stores only a salted PBKDF2 hash.'}

@app.post('/api/v1/security/token/rotate')
def rotate_api_token(request:Request):
 if not _request_is_loopback(request):raise HTTPException(403,'API token rotation is restricted to loopback clients')
 token=settings.create_api_token()
 _record_runtime_log('WARNING','Local API token rotated')
 return {'token':token,'warning':'The previous token is invalid. Copy this token now; it is shown only once.'}

@app.delete('/api/v1/security/token')
def revoke_api_token(request:Request):
 if not _request_is_loopback(request):raise HTTPException(403,'API token revocation is restricted to loopback clients')
 result=settings.revoke_api_token()
 _record_runtime_log('WARNING','Local API token revoked')
 return result

@app.middleware("http")
async def collect_safe_analytics(request, call_next):
 started=time.perf_counter()
 response=await call_next(request)
 route=request.scope.get("route")
 route_name=getattr(route,"path",None) or "unmatched"
 if route_name != "/api/v1/analytics":
  status=response.status_code
  level='ERROR' if status>=500 else ('WARNING' if status>=400 else 'INFO')
  _record_runtime_log(level,'HTTP request completed',request.method,route_name,status,round((time.perf_counter()-started)*1000,2))
  try:analytics.record("api_request",{"method":request.method,"route":route_name,"status":response.status_code,"duration_ms":round((time.perf_counter()-started)*1000,2)})
  except Exception:pass
 return response
@app.get('/api/v1/runtime/logs')
def runtime_logs(limit:int=100,level:str|None=None,q:str|None=None):
 if limit<1 or limit>500: raise HTTPException(400,'limit must be between 1 and 500')
 if level and level.upper() not in ('INFO','WARNING','ERROR'): raise HTTPException(400,'level must be INFO, WARNING or ERROR')
 with RUNTIME_LOG_LOCK: items=list(RUNTIME_LOGS)
 if level: items=[item for item in items if item['level']==level.upper()]
 if q:
  needle=q.casefold();items=[item for item in items if needle in item['message'].casefold() or needle in str(item['path']).casefold() or needle in str(item['method']).casefold()]
 items=items[-limit:][::-1]
 return {'items':items,'count':len(items),'capacity':RUNTIME_LOG_LIMIT,'source':'bounded in-memory request events','payloads_recorded':False}
@app.post('/api/v1/runtime/logs/clear')
def clear_runtime_logs():
 with RUNTIME_LOG_LOCK: removed=len(RUNTIME_LOGS);RUNTIME_LOGS.clear()
 return {'cleared':removed}
@app.get('/api/v1/litertlm/status')
def litertlm_status():
 cfg=settings.get()
 return {**litertlm.status(),'enabled':cfg.get('litertlm_enabled',False),'backend':cfg.get('litertlm_backend','cpu'),'configured_timeout_seconds':cfg.get('litertlm_timeout_seconds',120)}
@app.post('/api/v1/litertlm/run')
def litertlm_run(req:LiteRTLMRunInput):
 cfg=settings.get()
 if not cfg.get('litertlm_enabled',False):raise HTTPException(403,'LiteRT-LM is disabled in Settings')
 try:
  result=LiteRTLM(timeout_seconds=cfg.get('litertlm_timeout_seconds',120)).run(req.model,req.prompt,req.backend,req.approved)
  analytics.record('litertlm_run',{'backend':req.backend,'model_source':result['model_source']});return result
 except PermissionError as exc:raise HTTPException(403,str(exc))
 except ValueError as exc:raise HTTPException(400,str(exc))
 except LiteRTLMError as exc:raise HTTPException(503,str(exc))
@app.post('/api/v1/litertlm/benchmark')
def litertlm_benchmark(req:LiteRTLMBenchmarkInput):
 cfg=settings.get()
 if not cfg.get('litertlm_enabled',False):raise HTTPException(403,'LiteRT-LM is disabled in Settings')
 try:
  result=LiteRTLM(timeout_seconds=cfg.get('litertlm_timeout_seconds',120)).benchmark(req.model,req.approved)
  analytics.record('litertlm_benchmark');return result
 except PermissionError as exc:raise HTTPException(403,str(exc))
 except ValueError as exc:raise HTTPException(400,str(exc))
 except LiteRTLMError as exc:raise HTTPException(503,str(exc))

@app.get('/api/v1/chat/models')
def chat_models():
 prefs=settings.get();runtime=agent_runtime.model_runtime.status()
 items=[{'id':'algorithms','name':'MOJO Algorithms','provider':'builtin','mode':'algorithms','available':True,'requires_approval':False}]
 saved=chat_store.list_models()
 configured=prefs.get('litertlm_model','')
 for item in saved:
  try:
   _,is_hf=LiteRTLM.validate_model(item['model_id'])
   available=bool(runtime.get('huggingface_repo_cli_available') if is_hf else runtime.get('local_model_cli_available'))
  except ValueError:available=False
  items.append({**item,'catalog_id':item['id'],'id':item['model_id'],'name':item['label'],'provider':'litertlm','mode':'litertlm','available':available,'requires_approval':True})
 if configured and not any(item.get('model_id')==configured for item in saved):
  try:
   _,is_hf=LiteRTLM.validate_model(configured)
   available=bool(runtime.get('huggingface_repo_cli_available') if is_hf else runtime.get('local_model_cli_available'))
  except ValueError:available=False
  items.append({'id':configured,'model_id':configured,'name':configured,'provider':'litertlm','mode':'litertlm','available':available,'requires_approval':True})
 return {'items':items,'default_mode':prefs.get('chat_default_mode','algorithms'),'configured_model':configured,'runtime_enabled':prefs.get('litertlm_enabled',False),'runtime':runtime,'remote_providers_enabled':False,'note':'Algorithms and local LiteRT-LM are supported. Cloud provider API keys are not used.'}

@app.post('/api/v1/chat/models')
def add_chat_model(req:ChatModelInput):
 try:
  value,is_hf=LiteRTLM.validate_model(req.model_id)
  item=chat_store.add_model(req.label,value,req.backend)
  runtime=agent_runtime.model_runtime.status()
  available=bool(runtime.get('huggingface_repo_cli_available') if is_hf else runtime.get('local_model_cli_available'))
  return {**item,'model_source':'huggingface' if is_hf else 'local','available':available}
 except (ValueError,FileNotFoundError) as exc:raise HTTPException(400,str(exc))

@app.post('/api/v1/chat/models/{catalog_id}/select')
def select_chat_model(catalog_id:str):
 item=chat_store.get_model(catalog_id)
 if not item:raise HTTPException(404,'Chat model not found')
 try:
  LiteRTLM.validate_model(item['model_id'])
  settings.update({'litertlm_model':item['model_id'],'litertlm_backend':item['backend']})
  return {'selected':True,'model':item,'runtime_enabled':settings.get()['litertlm_enabled']}
 except ValueError as exc:raise HTTPException(400,str(exc))

@app.delete('/api/v1/chat/models/{catalog_id}')
def delete_chat_model(catalog_id:str):
 if not chat_store.delete_model(catalog_id):raise HTTPException(404,'Chat model not found')
 return {'deleted':True,'id':catalog_id}

@app.get('/api/v1/chat/tools')
def chat_tools():
 return {'built_in':tools.list_tools(),'installed_tools':extensions.list('tool'),'skills':extensions.list('skill'),'approval_required':True,'automatic_tool_execution':False}

@app.post('/api/v1/chat/conversations')
def create_chat_conversation(req:ChatConversationInput):
 prefs=settings.get();mode=req.mode or prefs.get('chat_default_mode','algorithms')
 if mode not in {'algorithms','litertlm'}:raise HTTPException(400,'mode must be algorithms or litertlm')
 if mode=='litertlm' and not prefs.get('litertlm_enabled'):raise HTTPException(403,'Enable LiteRT-LM in Runtime & Models before creating a model chat')
 try:return chat_store.create(req.title,mode,req.model or prefs.get('litertlm_model',''))
 except ValueError as exc:raise HTTPException(400,str(exc))

@app.get('/api/v1/chat/conversations')
def list_chat_conversations(limit:int=50,include_archived:bool=False):
 return {'items':chat_store.list(limit,include_archived)}

@app.get('/api/v1/chat/conversations/{conversation_id}')
def get_chat_conversation(conversation_id:str):
 item=chat_store.get(conversation_id)
 if not item:raise HTTPException(404,'Conversation not found')
 return {**item,'attachments':chat_store.list_attachments(conversation_id)}

@app.patch('/api/v1/chat/conversations/{conversation_id}')
def update_chat_conversation(conversation_id:str,req:ChatConversationUpdate):
 try:
  item=chat_store.update(conversation_id,**req.model_dump(exclude_unset=True,exclude_none=True))
  if not item:raise HTTPException(404,'Conversation not found')
  return item
 except ValueError as exc:raise HTTPException(400,str(exc))

@app.delete('/api/v1/chat/conversations/{conversation_id}')
def delete_chat_conversation(conversation_id:str):
 if not chat_store.delete(conversation_id):raise HTTPException(404,'Conversation not found')
 return {'deleted':True,'id':conversation_id}

@app.get('/api/v1/chat/conversations/{conversation_id}/messages')
def list_chat_messages(conversation_id:str,limit:int=100,before:float|None=None):
 items=chat_store.messages(conversation_id,limit,before)
 if items is None:raise HTTPException(404,'Conversation not found')
 return {'items':items,'count':len(items)}

@app.delete('/api/v1/chat/conversations/{conversation_id}/messages')
def clear_chat_messages(conversation_id:str):
 count=chat_store.clear_messages(conversation_id)
 if count is None:raise HTTPException(404,'Conversation not found')
 return {'deleted':count}

@app.get('/api/v1/chat/conversations/{conversation_id}/export')
def export_chat_conversation(conversation_id:str):
 conversation=chat_store.get(conversation_id)
 if not conversation:raise HTTPException(404,'Conversation not found')
 payload={'format':'mojo-chat-v1','conversation':conversation,'messages':chat_store.messages(conversation_id,200),'attachments':chat_store.list_attachments(conversation_id)}
 return Response(content=json.dumps(payload,ensure_ascii=False),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="mojo-chat-{conversation_id[:8]}.json"'})

@app.post('/api/v1/chat/conversations/{conversation_id}/attachments')
async def upload_chat_attachment(conversation_id:str,request:Request,filename:str):
 if not chat_store.get(conversation_id):raise HTTPException(404,'Conversation not found')
 chunks=[];total=0
 async for chunk in request.stream():
  total+=len(chunk)
  if total>MAX_ATTACHMENT_BYTES:raise HTTPException(413,'Attachment exceeds 10 MiB')
  chunks.append(chunk)
 try:
  item=chat_store.add_attachment(conversation_id,filename,request.headers.get('content-type','application/octet-stream'),b''.join(chunks))
  analytics.record('chat_attachment_added',{'extension':item['extension'],'size_bytes':item['size_bytes']})
  return item
 except ValueError as exc:raise HTTPException(400,str(exc))

@app.get('/api/v1/chat/conversations/{conversation_id}/attachments')
def list_chat_attachments(conversation_id:str):
 if not chat_store.get(conversation_id):raise HTTPException(404,'Conversation not found')
 return {'items':chat_store.list_attachments(conversation_id)}

@app.get('/api/v1/chat/attachments/{attachment_id}')
def download_chat_attachment(attachment_id:str):
 item=chat_store.attachment_bytes(attachment_id)
 if not item:raise HTTPException(404,'Attachment not found')
 safe_name=Path(item['filename']).name.replace('"','_')
 return Response(content=item['content'],media_type=item['content_type'],headers={'Content-Disposition':f'attachment; filename="{safe_name}"','X-Content-Type-Options':'nosniff'})

@app.post('/api/v1/chat/conversations/{conversation_id}/send')
def send_chat_message(conversation_id:str,req:ChatSendInput):
 conversation=chat_store.get(conversation_id)
 if not conversation:raise HTTPException(404,'Conversation not found')
 prefs=settings.get();mode=req.mode or conversation['mode'] or prefs.get('chat_default_mode','algorithms')
 if mode not in {'algorithms','litertlm'}:raise HTTPException(400,'mode must be algorithms or litertlm')
 if mode=='litertlm' and not prefs.get('litertlm_enabled'):raise HTTPException(403,'LiteRT-LM is disabled in Runtime & Models')
 content=req.content.strip()
 if not content and not req.attachments:raise HTTPException(400,'Enter a message or attach a file')
 if not content:content='Please review the attached file(s).'
 try:attachment_context=chat_store.text_for_attachments(conversation_id,req.attachments)
 except ValueError as exc:raise HTTPException(400,str(exc))
 try:
  chat_store.update(conversation_id,mode=mode,model=req.model or conversation['model'])
  user_message=chat_store.add_message(conversation_id,'user',content,{'attachments':[{'id':a['id'],'filename':a['filename']} for a in attachment_context]})
  history=chat_store.messages(conversation_id,prefs.get('chat_max_history',12)+1) or []
  if mode=='algorithms':
   tasks=decompose_goal(content)
   order=topological_order({task['id']:task['depends_on'] for task in tasks})
   lines=['MOJO AGENT is using deterministic Algorithms mode. No language model was called.','']
   lines.extend([f"{index+1}. {task['title']}" for index,task in enumerate(tasks)])
   lines.extend(['','Execution order: '+', '.join(order) if order else 'Execution order: none','Tools are not run automatically. Open Chat Tools and approve an individual operation when needed.'])
   for attachment in attachment_context:
    lines.append(f"Attachment: {attachment['filename']}. "+("UTF-8 text is available as context." if attachment['extracted_text'] else "This file is stored, but this runtime cannot inspect its contents."))
   answer='\n'.join(lines)
   assistant=chat_store.add_message(conversation_id,'assistant',answer,{'mode':mode,'model':None,'tasks':tasks,'execution':'not automatic'})
  else:
   model=req.model or conversation['model'] or prefs.get('litertlm_model','')
   if not model:raise HTTPException(400,'Select a local .litertlm model or Hugging Face model ID in Runtime & Models')
   if not req.approved:raise HTTPException(403,'Model inference requires checking the per-message approval box')
   system_prompt=conversation.get('system_prompt') or prefs.get('chat_system_prompt','You are MOJO AGENT. Be honest and do not claim to execute tools.')
   transcript=[]
   for message in history:
    if message['role'] in {'user','assistant'}:
     transcript.append(message['role'].upper()+': '+message['content'])
   for attachment in attachment_context:
    if attachment['extracted_text']:transcript.append('ATTACHMENT '+attachment['filename']+': '+attachment['extracted_text'])
   transcript_text='\n'.join(transcript)
   available_context=max(500,5900-len(system_prompt)-40)
   transcript_text=transcript_text[-available_context:]
   prompt=system_prompt[:2000]+'\n\nConversation:\n'+transcript_text+'\nASSISTANT:'
   try:
    result=agent_runtime.model_runtime.run(model,prompt,backend=req.backend or prefs.get('litertlm_backend','cpu'),approved=True)
   except (LiteRTLMError,ValueError,OSError) as exc:raise HTTPException(503,'Local model request failed: '+str(exc)[:300])
   answer=result.get('output','').strip() or '[The local model returned an empty response.]'
   assistant=chat_store.add_message(conversation_id,'assistant',answer,{'mode':mode,'model':model,'backend':req.backend or prefs.get('litertlm_backend','cpu'),'model_source':result.get('model_source')})
  analytics.record('chat_message_sent',{'mode':mode,'has_attachments':bool(req.attachments)})
  return {'user_message':user_message,'assistant_message':assistant,'conversation':chat_store.get(conversation_id),'model_mode':mode}
 except HTTPException:raise
 except (ValueError,KeyError) as exc:raise HTTPException(400,str(exc))

@app.post('/api/v1/chat/conversations/{conversation_id}/skills/{name}/plan')
def plan_chat_skill(conversation_id:str,name:str,req:Goal):
 if not chat_store.get(conversation_id):raise HTTPException(404,'Conversation not found')
 try:
  manifest=extensions.get_manifest('skill',name)
  tasks=decompose_goal(req.goal)
  order=topological_order({task['id']:task['depends_on'] for task in tasks})
  result={'skill':name,'instructions':manifest['instructions'],'allowed_tools':manifest.get('tools',[]),'goal':req.goal,'algorithm_plan':{'tasks':tasks,'execution_order':order},'execution':'plan only; no tools were executed'}
  message=chat_store.add_message(conversation_id,'tool',json.dumps(result,ensure_ascii=False),{'kind':'skill_plan','skill':name,'approval_required_for_execution':True})
  return {'plan':result,'message':message}
 except KeyError:raise HTTPException(404,'Skill not installed')
 except (ValueError,TypeError) as exc:raise HTTPException(400,str(exc))

@app.post('/api/v1/chat/conversations/{conversation_id}/tools/execute')
def execute_chat_tool(conversation_id:str,req:ChatToolInput):
 if not chat_store.get(conversation_id):raise HTTPException(404,'Conversation not found')
 if not req.approved:raise HTTPException(403,'Approve this exact tool operation before execution')
 try:
  if req.tool_source=='skill':
   if not req.skill_name:raise HTTPException(400,'skill_name is required for skill operations')
   result=extensions.execute_skill(req.skill_name,req.name,req.arguments,True)
  elif req.tool_source=='extension':
   result={'status':'completed','result':extensions.execute_tool(req.name,req.arguments,True)}
  elif req.tool_source=='builtin':
   result={'status':'completed','result':tools.execute(req.name,req.arguments,True)}
  else:raise HTTPException(400,'tool_source must be builtin, extension or skill')
  rendered=json.dumps(result,ensure_ascii=False,default=str)
  message=chat_store.add_message(conversation_id,'tool',rendered,{'tool':req.name,'skill':req.skill_name,'approved':True})
  analytics.record('chat_tool_executed',{'tool':req.name,'skill':bool(req.skill_name)})
  return {'result':result,'message':message}
 except PermissionError as exc:raise HTTPException(403,str(exc))
 except KeyError:raise HTTPException(404,'Skill or tool not found')
 except (ValueError,ExtensionError) as exc:raise HTTPException(400,str(exc))

@app.get('/api/v1/health')

def health():return {'status':'ok','name':'MOJO AGENT','version':'0.9.0','llm':'disabled','runtime':'python-reference','platform':'cross-platform'}
@app.get('/api/v1/runtime/status')
def runtime_status():
 db_path=str(memory.path)
 db_bytes=os.path.getsize(db_path) if os.path.exists(db_path) else 0
 with sqlite3.connect(db_path,timeout=5) as conn:
  integrity=conn.execute('PRAGMA quick_check').fetchone()[0]
  table_names={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  counts={}
  for table in ('memories','workflows','workflow_runs','workflow_schedules','workflow_jobs','schema_migrations','analytics_events','knowledge_nodes','knowledge_edges','evolution_candidates','installed_extensions','chat_conversations','chat_messages','chat_attachments','chat_models'):
   if table in table_names: counts[table]=conn.execute('SELECT COUNT(*) FROM "'+table+'"').fetchone()[0]
 schedules=workflows.list_schedules()
 return {'status':'ok' if integrity=='ok' else 'degraded','pid':os.getpid(),'uptime_seconds':round(time.time()-RUNTIME_STARTED_AT,1),'threads':threading.active_count(),'database':{'engine':'sqlite','path':os.path.basename(db_path),'size_bytes':db_bytes,'integrity':integrity,'tables':sorted(table_names),'counts':counts},'scheduler':{'total':len(schedules),'enabled':sum(1 for s in schedules if s['enabled']),'automatic_daemon':bool(settings.get()['worker_enabled'] and WORKER_THREAD and WORKER_THREAD.is_alive()),'execution_mode':'opt-in background worker or manual tick'},'worker':{'enabled':settings.get()['worker_enabled'],'thread_alive':bool(WORKER_THREAD and WORKER_THREAD.is_alive()),'queued':workflows.job_counts()['queued'],'running':workflows.job_counts()['running']},'schema':database.status(),'safety':{'llm_enabled':False,'tool_approval_required':True,'shell_execution':False,'source_self_modification':False}}
@app.get('/api/v1/database/status')
def database_status():return database.status()

def _require_loopback(request:Request):
 try:peer=ipaddress.ip_address(request.client.host if request.client else '')
 except ValueError:raise HTTPException(403,'Database maintenance is available only to loopback clients')
 if not peer.is_loopback:raise HTTPException(403,'Database maintenance is restricted to loopback clients')

async def _read_limited_body(request:Request, max_bytes:int=128*1024*1024):
 declared=request.headers.get('content-length')
 if declared:
  try:size=int(declared)
  except ValueError:raise HTTPException(400,'Invalid Content-Length header')
  if size<0 or size>max_bytes:raise HTTPException(413,'Backup exceeds the 128 MiB restore limit')
 chunks=[];total=0
 async for chunk in request.stream():
  total+=len(chunk)
  if total>max_bytes:raise HTTPException(413,'Backup exceeds the 128 MiB restore limit')
  chunks.append(chunk)
 return b''.join(chunks)

@app.post('/api/v1/backup/inspect')
async def inspect_database_backup(request:Request):
 _require_loopback(request)
 payload=await _read_limited_body(request)
 try:return database.inspect_payload(payload)
 except ValueError as exc:raise HTTPException(400,str(exc))

@app.post('/api/v1/backup/restore')
async def restore_database_backup(request:Request):
 _require_loopback(request)
 payload=await _read_limited_body(request)
 try:
  result=database.restore_payload(payload,request.headers.get('x-backup-sha256'))
  _record_runtime_log('WARNING','Database restored from verified local backup')
  return result
 except ValueError as exc:raise HTTPException(400,str(exc))
 except (OSError,sqlite3.Error) as exc:raise HTTPException(500,'Restore failed safely: '+str(exc)[:200])
@app.get('/api/v1/backup/export')
def export_database_backup(request:Request):
 try:
  peer=ipaddress.ip_address(request.client.host if request.client else '')
 except ValueError:
  raise HTTPException(403,'Database backup is available only to loopback clients')
 if not peer.is_loopback: raise HTTPException(403,'Database backup is restricted to loopback clients; use the local dashboard or USB port forwarding')
 db_path=str(memory.path)
 if not os.path.exists(db_path): raise HTTPException(404,'Database file does not exist yet')
 try:
  with sqlite3.connect(db_path,timeout=10) as source:
   with sqlite3.connect(':memory:') as target:
    source.backup(target)
    integrity=target.execute('PRAGMA integrity_check').fetchone()[0]
    if integrity!='ok': raise HTTPException(500,'Database integrity check failed; backup was not created')
    payload=target.serialize()
 except sqlite3.Error as exc: raise HTTPException(500,'Database backup failed: '+str(exc)[:200])
 digest=hashlib.sha256(payload).hexdigest()
 return Response(content=payload,media_type='application/vnd.sqlite3',headers={'Content-Disposition':'attachment; filename="mojo-agent-backup.sqlite3"','X-Backup-SHA256':digest,'X-Backup-Size':str(len(payload))})
@app.post('/api/v1/settings/validate')
def validate_settings(req:SettingsInput):
 values=req.model_dump(exclude_unset=True)
 unsupported=set(values)-{'theme','tool_approval_required','runtime_mode','litertlm_enabled','litertlm_backend','litertlm_timeout_seconds','litertlm_model','worker_enabled','worker_poll_seconds','worker_batch_size','workflow_max_attempts','chat_default_mode','chat_system_prompt','chat_max_history'}
 if unsupported: raise HTTPException(400,'These settings require a service restart or are not remotely editable: '+', '.join(sorted(unsupported)))
 if values.get('theme') not in (None,'dark','light','system'): raise HTTPException(400,'theme must be dark, light or system')
 if values.get('tool_approval_required') is False: raise HTTPException(400,'Tool approval is mandatory and cannot be disabled')
 if values.get('runtime_mode') not in (None,'algorithms','hybrid','litertlm'):raise HTTPException(400,'runtime_mode must be algorithms, hybrid or litertlm')
 if values.get('litertlm_backend') not in (None,'cpu','gpu'):raise HTTPException(400,'litertlm_backend must be cpu or gpu')
 if values.get('litertlm_enabled') not in (None,True,False):raise HTTPException(400,'litertlm_enabled must be boolean')
 if values.get('litertlm_timeout_seconds') is not None and not 10<=values['litertlm_timeout_seconds']<=180:raise HTTPException(400,'litertlm_timeout_seconds must be 10-180')
 if values.get('runtime_mode') in ('hybrid','litertlm') and not values.get('litertlm_enabled',settings.get()['litertlm_enabled']):raise HTTPException(400,'Hybrid and LiteRT-LM modes require the optional runtime enabled')
 if values.get('tool_approval_required') not in (None,True): raise HTTPException(400,'tool_approval_required must be boolean')
 if values.get('litertlm_enabled') not in (None,True,False): raise HTTPException(400,'litertlm_enabled must be boolean')
 if values.get('litertlm_backend') not in (None,'cpu','gpu'): raise HTTPException(400,'litertlm_backend must be cpu or gpu')
 if values.get('litertlm_timeout_seconds') is not None and (not isinstance(values['litertlm_timeout_seconds'],int) or not 10<=values['litertlm_timeout_seconds']<=180): raise HTTPException(400,'litertlm_timeout_seconds must be between 10 and 180')
  if values.get('chat_default_mode') not in (None,'algorithms','litertlm'):raise HTTPException(400,'chat_default_mode must be algorithms or litertlm')
  if values.get('chat_default_mode')=='litertlm' and not values.get('litertlm_enabled',settings.get()['litertlm_enabled']):raise HTTPException(400,'Enable LiteRT-LM before selecting it as the default chat mode')
  if values.get('chat_system_prompt') is not None and (not isinstance(values['chat_system_prompt'],str) or len(values['chat_system_prompt'])>2000):raise HTTPException(400,'chat_system_prompt must be a string up to 2000 characters')
  if values.get('chat_max_history') is not None and (not isinstance(values['chat_max_history'],int) or not 2<=values['chat_max_history']<=30):raise HTTPException(400,'chat_max_history must be 2-30')
 return {'valid':True,'accepted_fields':sorted(values),'restart_required':False,'protected_invariants':{'tool_approval_required':True,'llm_enabled':False,'source_self_modification':False}}
def _discover_ipv4_addresses():
 addresses=[]
 try:
  for item in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET):
   address=item[4][0]
   if not address.startswith('127.') and not address.startswith('169.254.') and address not in addresses:addresses.append(address)
 except OSError:pass
 # A UDP connect asks the OS which interface it would route through; no packet is sent.
 probe=None
 try:
  probe=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
  probe.connect(("192.0.2.1",80))
  address=probe.getsockname()[0]
  if address and not address.startswith('127.') and not address.startswith('169.254.') and address not in addresses:addresses.insert(0,address)
 except OSError:pass
 finally:
  if probe is not None:probe.close()
 return addresses
@app.get('/api/v1/discovery')
def discovery():
 return {'service':'MOJO AGENT','port':8766,'api_prefix':'/api/v1','addresses':_discover_ipv4_addresses(),'health_path':'/api/v1/health','lan_access_requires_explicit_host_binding':True}
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
def status():return {'generation':evolution.generation,'population_size':evolution.population_size,'champion':evolution.champion.__dict__,'candidates':evolution_store.list_candidates(100),'approval_required':True,'source_mutation':'disabled'}
@app.post('/api/v1/evolution/experiment')
def experiment():
 candidates=evolution.evolve(lambda s:1-abs(s.learning_rate-.2)-abs(s.exploration-.1));evolution_store.set_generation(evolution.generation);analytics.record('evolution_experiment')
 payload=[]
 for c in candidates:
  ident=str(uuid.uuid4());candidate_registry[ident]=c;evolution_store.save_candidate(ident,c)
  payload.append({'id':ident,'fitness':c.fitness,'strategy':c.strategy.__dict__,'tests_passed':c.tests_passed,'approved':c.approved})
 return {'generation':evolution.generation,'candidates':payload,'activation':'manual approval required'}
@app.post('/api/v1/evolution/candidates/{candidate_id}/validate')
def validate_candidate(candidate_id:str):
 c=candidate_registry.get(candidate_id) or evolution_store.get_candidate(candidate_id)
 if not c:raise HTTPException(404,'Candidate not found; run a new experiment')
 candidate_registry[candidate_id]=c
 try:c.tests_passed=evolution.validate_candidate(c,lambda s: (s.validate() is None and all(math.isfinite(v) for v in (s.learning_rate,s.exploration,s.discount))))
 except (ValueError,TypeError):c.tests_passed=False
 evolution_store.save_candidate(candidate_id,c);analytics.record('candidate_validated',{'passed':c.tests_passed})
 return {'id':candidate_id,'tests_passed':c.tests_passed,'activation':'not activated'}
@app.post('/api/v1/evolution/candidates/{candidate_id}/approve')
def approve_candidate(candidate_id:str,req:ApprovalInput):
 c=candidate_registry.get(candidate_id) or evolution_store.get_candidate(candidate_id)
 if not c:raise HTTPException(404,'Candidate not found; run a new experiment')
 candidate_registry[candidate_id]=c
 try:evolution.approve_candidate(c,req.approved);evolution_store.save_candidate(candidate_id,c);evolution_store.set_champion(evolution.champion);analytics.record('candidate_approved');return {'id':candidate_id,'approved':True,'champion':evolution.champion.__dict__}
 except (ValueError,PermissionError) as e:raise HTTPException(400,str(e))
@app.get('/api/v1/tools')
def list_tools():return {'tools':tools.list_tools()}
@app.post('/api/v1/tools/execute')
def execute_tool(req:ToolInput):
 try:return {'result':tools.execute(req.name,req.arguments,approved=req.approved)}
 except PermissionError as e:raise HTTPException(403,str(e))
 except (ValueError,KeyError) as e:raise HTTPException(400,str(e))
@app.get('/api/v1/workflows')
def list_workflows():return {'items':workflows.list(),'history':workflows.history(),'schedules':workflows.list_schedules()}
@app.get('/api/v1/workflow-jobs')
def list_workflow_jobs(limit:int=100,status:str|None=None):
 try:return {'items':workflows.list_jobs(limit,status),'worker':worker_status()}
 except ValueError as exc:raise HTTPException(400,str(exc))
@app.post('/api/v1/workflows/{workflow_id}/enqueue')
def enqueue_workflow(workflow_id:str,req:WorkflowEnqueueInput):
 try:
  item=workflows.enqueue(workflow_id,req.max_attempts or settings.get()['workflow_max_attempts']);analytics.record('workflow_job_enqueued',{'job_id':item['id']})
  return item
 except KeyError as exc:raise HTTPException(404,str(exc))
 except ValueError as exc:raise HTTPException(400,str(exc))
@app.get('/api/v1/workflow-jobs/{job_id}')
def get_workflow_job(job_id:str):
 item=workflows.get_job(job_id)
 if item is None:raise HTTPException(404,'Workflow job not found')
 return item
@app.post('/api/v1/workflow-jobs/{job_id}/cancel')
def cancel_workflow_job(job_id:str):
 item=workflows.cancel_job(job_id)
 if item is None:raise HTTPException(404,'Workflow job not found')
 return item
@app.post('/api/v1/workflow-jobs/{job_id}/retry')
def retry_workflow_job(job_id:str):
 try:
  item=workflows.retry_job(job_id)
  if item is None:raise HTTPException(404,'Workflow job not found')
  return item
 except ValueError as exc:raise HTTPException(409,str(exc))
@app.get('/api/v1/worker/status')
def worker_status():
 prefs=settings.get()
 return {'enabled':prefs['worker_enabled'],'poll_seconds':prefs['worker_poll_seconds'],'batch_size':prefs['worker_batch_size'],
  'thread_alive':bool(WORKER_THREAD and WORKER_THREAD.is_alive()),'processing_active':bool(prefs['worker_enabled'] and WORKER_THREAD and WORKER_THREAD.is_alive()),'worker_id':WORKER_ID,'queue':{
   'queued':workflows.job_counts()['queued'],'running':workflows.job_counts()['running']}}
@app.post('/api/v1/worker/tick')
def worker_tick(req:WorkerTickInput):
 try:return workflows.worker_tick(tools,req.worker_id,limit=req.limit)
 except ValueError as exc:raise HTTPException(400,str(exc))
@app.get('/api/v1/scheduler/schedules')
def list_schedules():return {'items':workflows.list_schedules(),'max_schedules':100,'max_batch':10}
@app.post('/api/v1/scheduler/schedules')
def create_schedule(req:ScheduleInput):
 try:
  item=workflows.create_schedule(req.workflow_id,req.interval_seconds);analytics.record('schedule_created',{'interval_seconds':req.interval_seconds});return item
 except KeyError as exc:raise HTTPException(404,str(exc))
 except ValueError as exc:raise HTTPException(400,str(exc))
@app.patch('/api/v1/scheduler/schedules/{schedule_id}')
def set_schedule(schedule_id:str,req:ScheduleEnabledInput):
 try:
  item=workflows.set_schedule_enabled(schedule_id,req.enabled)
  if item is None:raise HTTPException(404,'Schedule not found')
  return item
 except ValueError as exc:raise HTTPException(400,str(exc))
@app.delete('/api/v1/scheduler/schedules/{schedule_id}')
def delete_schedule(schedule_id:str):
 if not workflows.delete_schedule(schedule_id):raise HTTPException(404,'Schedule not found')
 return {'deleted':True,'id':schedule_id}
@app.post('/api/v1/scheduler/tick')
def scheduler_tick():
 try:
  result=workflows.run_due(tools,limit=10);analytics.record('scheduler_tick',{'executed':result['executed']});return result
 except ValueError as exc:raise HTTPException(400,str(exc))
@app.get('/api/v1/workflows/{workflow_id}/history')
def workflow_history(workflow_id:str,limit:int=50):
 if not workflows.get(workflow_id):raise HTTPException(404,'Workflow not found')
 return {'items':workflows.history(limit,workflow_id)}
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
def analytics_summary(limit:int=20,event:str|None=None):
 try:return analytics.summary(limit,event)
 except ValueError as e:raise HTTPException(400,str(e))
@app.get('/api/v1/diagnostics')
def diagnostics():
 graph_snapshot=knowledge.snapshot()
 return {'status':'ok','python':platform.python_version(),'platform':platform.platform(),'runtime':'python-reference','runtime_mode':settings.get()['runtime_mode'],'llm_enabled':False,'litertlm':agent_runtime.model_runtime.status(),'database':'sqlite','modules':{'memory_records':len(memory.search('',200)),'workflows':len(workflows.list()),'knowledge_nodes':len(graph_snapshot['nodes']),'knowledge_edges':len(graph_snapshot['edges']),'evolution_candidates':len(evolution_store.list_candidates(500)),'installed_extensions':len(extensions.list()),'chat_conversations':len(chat_store.list(100))},'limits':{'memory_search':200,'workflow_steps':50,'analytics_retention':analytics.retention},'safety':{'tool_approval_required':True,'shell_execution':False,'source_self_modification':False,'github_extension_code_execution':False}}
@app.get('/api/v1/security/status')
def security_status():return {'mode':'local-first','tool_allowlist':tools.list_tools(),'approval_required':settings.get()['tool_approval_required'],'api_auth':settings.auth_status(),'shell_execution':False,'source_self_modification':False,'remote_access':'LAN access requires token authentication; use HTTPS termination before exposing beyond trusted networks'}
@app.get('/api/v1/settings')
def get_settings():return settings.get()
@app.patch('/api/v1/settings')
def patch_settings(req:SettingsInput):
 try:return settings.update({k:v for k,v in req.model_dump().items() if v is not None})
 except ValueError as e:raise HTTPException(400,str(e))
class MemoryUpdate(BaseModel):
 content:str|None=Field(default=None,max_length=10000);kind:str|None=None;importance:float|None=Field(default=None,ge=0,le=1)
@app.patch('/api/v1/memory/{memory_id}')
def update_memory(memory_id:int,req:MemoryUpdate):
 try:
  item=memory.update(memory_id,**req.model_dump(exclude_unset=True))
  if item is None:raise HTTPException(404,'Memory not found')
  analytics.record('memory_updated');return item
 except ValueError as e:raise HTTPException(400,str(e))
@app.delete('/api/v1/memory/{memory_id}')
def delete_memory(memory_id:int):
 if not memory.delete(memory_id):raise HTTPException(404,'Memory not found')
 analytics.record('memory_deleted');return {'deleted':True,'id':memory_id}
@app.get('/api/v1/memory/export')
def export_memory():return {'format':'mojo-memory-v1','items':memory.export_all()}
@app.delete('/api/v1/knowledge/nodes/{node_id}')
def delete_knowledge_node(node_id:str):
 if not knowledge.delete_node(node_id):raise HTTPException(404,'Node not found')
 analytics.record('knowledge_node_deleted');return {'deleted':True,'id':node_id}
@app.delete('/api/v1/knowledge/edges/{edge_id}')
def delete_knowledge_edge(edge_id:str):
 if not knowledge.delete_edge(edge_id):raise HTTPException(404,'Edge not found')
 analytics.record('knowledge_edge_deleted');return {'deleted':True,'id':edge_id}
class WorkflowUpdate(BaseModel):
 name:str=Field(min_length=1,max_length=120);steps:list[dict]=Field(min_length=1,max_length=50)
@app.patch('/api/v1/workflows/{workflow_id}')
def update_workflow(workflow_id:str,req:WorkflowUpdate):
 try:
  if not workflows.update(workflow_id,req.name,req.steps):raise HTTPException(404,'Workflow not found')
  analytics.record('workflow_updated');return workflows.get(workflow_id)
 except ValueError as e:raise HTTPException(400,str(e))
@app.delete('/api/v1/workflows/{workflow_id}')
def delete_workflow(workflow_id:str):
 if not workflows.delete(workflow_id):raise HTTPException(404,'Workflow not found')
 return {'deleted':True,'id':workflow_id}
class MemoryImport(BaseModel):
 format:str='mojo-memory-v1';items:list[dict]=Field(min_length=0,max_length=5000)
@app.post('/api/v1/memory/import')
def import_memory(req:MemoryImport):
 if req.format!='mojo-memory-v1':raise HTTPException(400,'Unsupported memory export format')
 try:added=memory.import_many(req.items)
 except (ValueError,TypeError) as exc:raise HTTPException(400,str(exc))
 analytics.record('memory_imported',{'count':added});return {'imported':added}


@app.get('/api/v1/agent/runtime')
def agent_runtime_status():
 result=agent_runtime.status();prefs=settings.get()
 result.update({'active_mode':prefs['runtime_mode'],'configured_mode':prefs['runtime_mode'],'litertlm_enabled':prefs['litertlm_enabled'],'configured_model':prefs['litertlm_model'],'configured_backend':prefs['litertlm_backend']})
 return result

@app.post('/api/v1/agent/run')
def run_agent(req:AgentRunInput):
 prefs=settings.get();mode=req.mode or prefs['runtime_mode']
 if mode in {'hybrid','litertlm'} and not prefs['litertlm_enabled']:raise HTTPException(400,'Optional LiteRT-LM runtime is disabled in settings')
 model=req.model if req.model is not None else prefs['litertlm_model'];backend=req.backend if req.backend is not None else prefs['litertlm_backend']
 try:
  agent_runtime.model_runtime.timeout_seconds=prefs['litertlm_timeout_seconds']
  result=agent_runtime.run(req.goal,mode,model,backend,req.approved);analytics.record('agent_run',{'mode':mode});return result
 except PermissionError as exc:raise HTTPException(403,str(exc))
 except (ValueError,RuntimeError) as exc:raise HTTPException(400,str(exc))

@app.get('/api/v1/litertlm/status')
def litertlm_status():
 status=agent_runtime.model_runtime.status();prefs=settings.get();status.update({'enabled':prefs['litertlm_enabled'],'configured_model':prefs['litertlm_model'],'configured_backend':prefs['litertlm_backend']});return status

@app.post('/api/v1/litertlm/run')
def litertlm_run(req:AgentRunInput):
 prefs=settings.get()
 if not prefs['litertlm_enabled']:raise HTTPException(400,'LiteRT-LM is disabled in settings')
 if not req.model and not prefs['litertlm_model']:raise HTTPException(400,'Configure a local model or Hugging Face model id first')
 try:
  agent_runtime.model_runtime.timeout_seconds=prefs['litertlm_timeout_seconds']
  return agent_runtime.model_runtime.run(req.model or prefs['litertlm_model'],req.goal,backend=req.backend or prefs['litertlm_backend'],approved=req.approved)
 except PermissionError as exc:raise HTTPException(403,str(exc))
 except (ValueError,LiteRTLMError) as exc:raise HTTPException(400,str(exc))

@app.get('/api/v1/extensions')
def list_extensions(kind:str|None=None):
 if kind not in (None,'skill','tool'):raise HTTPException(400,'kind must be skill or tool')
 return {'items':extensions.list(kind),'code_execution':False,'source':'GitHub declarative manifests'}

@app.post('/api/v1/extensions/github/preview')
def preview_github_extension(req:GitHubExtensionInput):
 try:return extensions.preview(req.repository,req.ref,req.manifest_path)
 except ExtensionError as exc:raise HTTPException(400,str(exc))

@app.post('/api/v1/extensions/github/install')
def install_github_extension(req:GitHubInstallInput):
 try:
  item=extensions.install(req.repository,req.ref,req.manifest_path,req.expected_sha256);analytics.record('github_extension_installed',{'kind':item['kind'],'name':item['name']});return item
 except ExtensionError as exc:raise HTTPException(400,str(exc))

@app.delete('/api/v1/extensions/{extension_id}')
def uninstall_extension(extension_id:str):
 if not extensions.uninstall(extension_id):raise HTTPException(404,'Installed extension not found')
 analytics.record('github_extension_removed');return {'removed':True,'id':extension_id}

@app.post('/api/v1/tools/installed/{name}/execute')
def execute_installed_tool(name:str,req:InstalledToolInput):
 try:return {'result':extensions.execute_tool(name,req.arguments,req.approved)}
 except PermissionError as exc:raise HTTPException(403,str(exc))
 except KeyError as exc:raise HTTPException(404,str(exc))
 except ExtensionError as exc:raise HTTPException(400,str(exc))

@app.post('/api/v1/skills/{name}/run')
def run_installed_skill(name:str,req:Goal):
 try:manifest=extensions.get_manifest('skill',name)
 except KeyError:raise HTTPException(404,'Skill not installed')
 tasks=decompose_goal(req.goal);order=topological_order({task['id']:task['depends_on'] for task in tasks})
 return {'skill':name,'instructions':manifest['instructions'],'allowed_tools':manifest.get('tools',[]),'goal':req.goal,'algorithm_plan':{'tasks':tasks,'execution_order':order},'execution':'instructions and plan only; tools are not auto-executed'}

@app.post('/api/v1/skills/{name}/execute')
def execute_skill_tool(name:str,req:SkillExecutionInput):
 try:
  result=extensions.execute_skill(name,req.operation,req.arguments,req.approved)
  analytics.record('skill_tool_executed',{'skill':name,'operation':req.operation,'status':result['status']})
  return result
 except PermissionError as exc:raise HTTPException(403,str(exc))
 except KeyError:raise HTTPException(404,'Skill not installed')
 except ExtensionError as exc:raise HTTPException(400,str(exc))

@app.get('/api/v1/skills/{name}/history')
def get_skill_history(name:str,limit:int=50):
 try:return {'items':extensions.skill_history(name,limit)}
 except KeyError:raise HTTPException(404,'Skill not installed')


@app.post('/api/v1/litertlm/benchmark')
def litertlm_benchmark(req:AgentRunInput):
 prefs=settings.get()
 if not prefs['litertlm_enabled']:raise HTTPException(400,'LiteRT-LM is disabled in settings')
 model=req.model or prefs['litertlm_model']
 if not model:raise HTTPException(400,'Configure a local model or Hugging Face model id first')
 try:
  agent_runtime.model_runtime.timeout_seconds=prefs['litertlm_timeout_seconds']
  return agent_runtime.model_runtime.benchmark(model,approved=req.approved)
 except PermissionError as exc:raise HTTPException(403,str(exc))
 except (ValueError,LiteRTLMError) as exc:raise HTTPException(400,str(exc))
