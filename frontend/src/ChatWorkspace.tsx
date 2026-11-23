import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Bot, Plus, Send, Trash2, Paperclip, ShieldCheck, Wrench, RefreshCw, MessageSquare, FileText, Download, Cpu } from 'lucide-react';

type Message = { id:string; role:string; content:string; created_at:number; metadata?:any };
type Conversation = { id:string; title:string; mode:string; model:string; updated_at:number; message_count?:number };
type Attachment = { id:string; filename:string; extension:string; size_bytes:number };

export default function ChatWorkspace({apiBase,apiToken}:{apiBase:string;apiToken:string}) {
 const [sessions,setSessions]=useState<Conversation[]>([]);
 const [active,setActive]=useState('');
 const [messages,setMessages]=useState<Message[]>([]);
 const [models,setModels]=useState<any>({items:[],default_mode:'algorithms'});
 const [tools,setTools]=useState<any>({built_in:[],skills:[],installed_tools:[]});
 const [mode,setMode]=useState('algorithms');
 const [model,setModel]=useState('');
 const [backend,setBackend]=useState('cpu');
 const [draft,setDraft]=useState('');
 const [approved,setApproved]=useState(false);
 const [busy,setBusy]=useState(false);
 const [notice,setNotice]=useState('');
 const [files,setFiles]=useState<Attachment[]>([]);
 const [pendingFiles,setPendingFiles]=useState<File[]>([]);
 const [toolName,setToolName]=useState('calculator');
 const [toolInput,setToolInput]=useState('2+2');
 const [toolApproval,setToolApproval]=useState(false);
 const [skillName,setSkillName]=useState('');
 const [skillOperation,setSkillOperation]=useState('');
 const [showTools,setShowTools]=useState(false);
 const [systemPrompt,setSystemPrompt]=useState('');
 const [maxHistory,setMaxHistory]=useState(12);
 const [settingsOpen,setSettingsOpen]=useState(false);\n const [newModelLabel,setNewModelLabel]=useState('My local model');\n const [newModelId,setNewModelId]=useState('');\n const [newModelBackend,setNewModelBackend]=useState('cpu');
 const bottom=useRef<HTMLDivElement>(null);
 const url=apiBase.replace(/\/$/,'');
 const headers=useMemo(()=>({'Content-Type':'application/json',...(apiToken?{Authorization:'Bearer '+apiToken}:{})}),[apiToken]);
 const call=useCallback(async(path:string,body?:any,method?:string)=>{
  const response=await fetch(url+path,{method:method||(body?'POST':'GET'),headers,...(body!==undefined?{body:JSON.stringify(body)}:{})});
  const data=await response.json().catch(()=>({detail:response.statusText}));
  if(!response.ok)throw new Error(data.detail||response.statusText||'Request failed');
  return data;
 },[url,headers]);
 const refreshSessions=useCallback(async()=>{
  const data=await call('/chat/conversations?limit=100');
  setSessions(data.items||[]);
 },[call]);
 const refreshMessages=useCallback(async(id:string)=>{
  if(!id){setMessages([]);setFiles([]);return}
  const [history,attachments]=await Promise.all([
   call('/chat/conversations/'+id+'/messages?limit=200'),
   call('/chat/conversations/'+id+'/attachments')
  ]);
  setMessages(history.items||[]);setFiles(attachments.items||[]);
 },[call]);
 const refreshCatalog=useCallback(async()=>{
  const [m,t,s]=await Promise.all([call('/chat/models'),call('/chat/tools'),call('/settings')]);
  setModels(m);setTools(t);setMode(m.default_mode||'algorithms');setModel(s.litertlm_model||'');
  setSystemPrompt(s.chat_system_prompt||'');setMaxHistory(s.chat_max_history||12);
 },[call]);
 useEffect(()=>{Promise.all([refreshSessions(),refreshCatalog()]).catch(e=>setNotice(e.message))},[refreshSessions,refreshCatalog]);
 useEffect(()=>{if(active)refreshMessages(active).catch(e=>setNotice(e.message))},[active,refreshMessages]);
 useEffect(()=>{bottom.current?.scrollIntoView({behavior:'smooth',block:'end'})},[messages]);
 const createChat=async()=>{
  setBusy(true);setNotice('');
  try{const item=await call('/chat/conversations',{title:'New chat',mode,model});await refreshSessions();setActive(item.id);setMessages([]);setFiles([])}
  catch(e:any){setNotice(e.message)}finally{setBusy(false)}
 };
 const removeChat=async(id:string)=>{
  if(!confirm('Delete this conversation and its attachments? This cannot be undone.'))return;
  setBusy(true);try{await call('/chat/conversations/'+id,undefined,'DELETE');if(active===id){setActive('');setMessages([]);setFiles([])}await refreshSessions()}catch(e:any){setNotice(e.message)}finally{setBusy(false)}
 };
 const uploadFiles=async(id:string)=>{
  const added:Attachment[]=[];
  for(const file of pendingFiles){
   const response=await fetch(url+'/chat/conversations/'+id+'/attachments?filename='+encodeURIComponent(file.name),{
    method:'POST',headers:{...(apiToken?{Authorization:'Bearer '+apiToken}:{}),'Content-Type':file.type||'application/octet-stream'},body:file
   });
   const data=await response.json().catch(()=>({detail:response.statusText}));
   if(!response.ok)throw new Error(data.detail||'File upload failed');
   added.push(data);
  }
  setPendingFiles([]);return added;
 };
 const send=async()=>{
  if(!draft.trim()&&!pendingFiles.length)return;
  setBusy(true);setNotice('');
  try{
   let id=active;
   if(!id){const created=await call('/chat/conversations',{title:'New chat',mode,model});id=created.id;setActive(id)}
   const added=pendingFiles.length?await uploadFiles(id):[];
   const attachmentIds=added.map(x=>x.id);
   const response=await call('/chat/conversations/'+id+'/send',{
    content:draft,mode,model:model||undefined,backend,approved,attachments:attachmentIds
   });
   setDraft('');setApproved(false);setPendingFiles([]);await Promise.all([refreshMessages(id),refreshSessions()]);
   if(response.model_mode==='algorithms')setNotice('Reply generated by deterministic Algorithms mode (no LLM inference).');
  }catch(e:any){setNotice(e.message)}finally{setBusy(false)}
 };
 const executeTool=async()=>{
  if(!active){setNotice('Create or select a conversation first.');return}
  setBusy(true);setNotice('');
  try{
   const operation=skillName?skillOperation:toolName;
   const args=operation==='calculator'?{expression:toolInput}:{text:toolInput};
   await call('/chat/conversations/'+active+'/tools/execute',{name:operation,arguments:args,approved:toolApproval,skill_name:skillName||undefined});
   setToolApproval(false);await Promise.all([refreshMessages(active),refreshSessions()]);
   setNotice('Approved tool operation completed.');
  }catch(e:any){setNotice(e.message)}finally{setBusy(false)}
 };
 const addModel=async()=>{
  setBusy(true);setNotice('');
  try{await call('/chat/models',{label:newModelLabel,model_id:newModelId,backend:newModelBackend});setNewModelId('');await refreshCatalog();setNotice('Model added to the local catalog. No model files were downloaded.')}
  catch(e:any){setNotice(e.message)}finally{setBusy(false)}
 };
 const selectDefaultModel=async(modelId:string)=>{
  const item=(models.items||[]).find((m:any)=>m.model_id===modelId);
  if(!item?.id||item.id==='algorithms')return;
  setBusy(true);try{await call('/chat/models/'+item.id+'/select',{},'POST');setModel(modelId);await refreshCatalog();setNotice('Default local model selected. Enable LiteRT-LM in Runtime & Models if it is not already enabled.')}
  catch(e:any){setNotice(e.message)}finally{setBusy(false)}
 };
 const removeModel=async(modelId:string)=>{
  const item=(models.items||[]).find((m:any)=>m.model_id===modelId);
  if(!item?.id)return;
  if(!confirm('Remove this model from the catalog? Model files on disk will not be deleted.'))return;
  setBusy(true);try{await call('/chat/models/'+item.id,undefined,'DELETE');await refreshCatalog();if(model===modelId)setModel('');setNotice('Model removed from catalog; model files were left untouched.')}
  catch(e:any){setNotice(e.message)}finally{setBusy(false)}
 };
 const saveChatSettings=async()=>{
  setBusy(true);try{
   await call('/settings',{chat_system_prompt:systemPrompt,chat_max_history:maxHistory},'PATCH');
   setNotice('Chat settings saved.');setSettingsOpen(false);await refreshCatalog();
  }catch(e:any){setNotice(e.message)}finally{setBusy(false)}
 };
 const availableModels=models.items||[];
 const selectedSkill=(tools.skills||[]).find((s:any)=>s.name===skillName);
 const allowedSkillOps=selectedSkill?.allowed_tools||[];
 const canUseModel=mode==='litertlm'&&models.items?.some((m:any)=>m.mode==='litertlm'&&m.available);
 return <div className="chat-workspace">
  <aside className="chat-sidebar">
   <div className="chat-sidebar-head"><div><b>Conversations</b><small>Local persistent history</small></div><button className="primary icon-action" onClick={createChat} disabled={busy} title="New chat"><Plus size={17}/></button></div>
   <div className="chat-session-list">{sessions.map(s=><div className={'chat-session '+(active===s.id?'active':'')} key={s.id}>
    <button className="chat-session-select" onClick={()=>{setActive(s.id);setMode(s.mode);setModel(s.model||'')}}><MessageSquare size={15}/><span><b>{s.title}</b><small>{s.message_count||0} messages · {s.mode}</small></span></button>
    <button className="chat-delete" title="Delete conversation" onClick={()=>removeChat(s.id)} disabled={busy}><Trash2 size={14}/></button>
   </div>)}</div>
  </aside>
  <section className="chat-main">
   <div className="chat-toolbar">
    <div><span className="eyebrow">MOJO CHAT</span><h2>{sessions.find(s=>s.id===active)?.title||'New conversation'}</h2></div>
    <div className="chat-toolbar-actions"><button className="secondary" onClick={()=>setSettingsOpen(v=>!v)}><Cpu size={15}/> Chat settings</button><button className="secondary" onClick={()=>setShowTools(v=>!v)}><Wrench size={15}/> Tools & skills</button><button className="secondary" onClick={()=>{if(active)refreshMessages(active)}} disabled={!active||busy}><RefreshCw size={14}/></button></div>
   </div>
   <div className="chat-modelbar">
    <label>Chat mode<select value={mode} onChange={e=>setMode(e.target.value)}><option value="algorithms">Algorithms (offline, no LLM)</option><option value="litertlm" disabled={!models.items?.some((m:any)=>m.mode==='litertlm')}>Local LiteRT-LM</option></select></label>
    {mode==='litertlm'&&<><label>Model<select value={model} onChange={e=>setModel(e.target.value)}><option value="">Use configured model</option>{availableModels.filter((m:any)=>m.mode==='litertlm').map((m:any)=><option key={m.id} value={m.id}>{m.name}</option>)}</select></label><label>Backend<select value={backend} onChange={e=>setBackend(e.target.value)}><option value="cpu">CPU</option><option value="gpu">GPU</option></select></label></>}
    <span className="chat-safety"><ShieldCheck size={14}/> Tools never auto-run</span>
   </div>
   {settingsOpen&&<div className="chat-settings-panel"><label>System instructions<textarea value={systemPrompt} maxLength={2000} onChange={e=>setSystemPrompt(e.target.value)}/></label><label>History messages<select value={maxHistory} onChange={e=>setMaxHistory(Number(e.target.value))}>{[4,8,12,16,20,24,30].map(n=><option key={n} value={n}>{n}</option>)}</select></label><button className="primary" onClick={saveChatSettings} disabled={busy}>Save chat settings</button><div className="chat-model-manager"><b>Local model catalog</b><small>Add a local .litertlm file path or Hugging Face owner/repository ID. Adding an entry does not download weights.</small><label>Display name<input value={newModelLabel} onChange={e=>setNewModelLabel(e.target.value)} maxLength={100}/></label><label>Model path or repository ID<input value={newModelId} onChange={e=>setNewModelId(e.target.value)} placeholder="C:\\models\\model.litertlm or org/model"/></label><label>Default backend<select value={newModelBackend} onChange={e=>setNewModelBackend(e.target.value)}><option value="cpu">CPU</option><option value="gpu">GPU</option></select></label><button className="secondary" disabled={busy||!newModelLabel.trim()||!newModelId.trim()} onClick={addModel}>Add model</button><div className="chat-model-catalog">{(models.items||[]).filter((m:any)=>m.mode==='litertlm').map((m:any)=><div key={m.model_id} className="chat-model-entry"><span><b>{m.name}</b><small>{m.model_id} · {m.available?'CLI available':'CLI/model unavailable'}</small></span><div><button className="secondary" disabled={busy} onClick={()=>selectDefaultModel(m.model_id)}>Set default</button><button className="chat-delete" disabled={busy} onClick={()=>removeModel(m.model_id)}>×</button></div></div>)}</div></div></div>}
   {notice&&<div className="chat-notice">{notice}</div>}
   <div className="chat-message-list">
    {!messages.length&&<div className="chat-empty"><div className="chat-empty-icon"><Bot size={30}/></div><h3>Start a conversation with MOJO</h3><p>Use Algorithms mode without a model, or enable LiteRT-LM for local model chat. Attach files and run tools only after explicit approval.</p><div className="chat-suggestions">{['Explain how this project works','Create a step-by-step implementation plan','Review this text for errors'].map(s=><button key={s} className="secondary" onClick={()=>setDraft(s)}>{s}</button>)}</div></div>}
    {messages.map(m=><article className={'chat-message '+m.role} key={m.id}><div className="chat-avatar">{m.role==='user'?'You':m.role==='tool'?<Wrench size={15}/>:<Bot size={16}/>}</div><div className="chat-bubble"><div className="chat-message-meta"><b>{m.role==='user'?'You':m.role==='tool'?'Tool result':'MOJO AGENT'}</b><small>{new Date(m.created_at*1000).toLocaleString()}</small></div><div className="chat-message-content">{m.content}</div>{m.metadata?.attachments?.map((a:any)=><div className="chat-attachment-chip" key={a.id}><FileText size={13}/>{a.filename}</div>)}</div></article>)}
    <div ref={bottom}/>
   </div>
   {files.length>0&&<div className="chat-file-strip">{files.map(f=><span key={f.id}><FileText size={13}/>{f.filename} · {(f.size_bytes/1024).toFixed(0)} KB</span>)}</div>}
   {pendingFiles.length>0&&<div className="chat-file-strip pending">{pendingFiles.map((f,i)=><span key={i}><Paperclip size={13}/>{f.name}<button onClick={()=>setPendingFiles(items=>items.filter((_,j)=>j!==i))}>×</button></span>)}</div>}
   <div className="chat-composer">
    <textarea value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}} placeholder="Message MOJO AGENT… (Enter to send, Shift+Enter for a new line)" rows={3}/>
    <div className="chat-composer-bottom"><div className="chat-composer-left">
     <label className="secondary upload chat-upload"><Paperclip size={15}/> Attach files<input type="file" multiple accept=".txt,.md,.json,.csv,.log,.pdf,.docx,.xlsx,.pptx,.png,.jpg,.jpeg,.webp,.mp3,.wav,.m4a,.mp4" onChange={e=>setPendingFiles(Array.from(e.target.files||[]))}/></label>
     {mode==='litertlm'&&<label className="chat-approval"><input type="checkbox" checked={approved} onChange={e=>setApproved(e.target.checked)}/> Approve local model inference for this message</label>}
    </div><button className="primary chat-send" disabled={busy||(!draft.trim()&&!pendingFiles.length)||(mode==='litertlm'&&!approved)|| (mode==='litertlm'&&!canUseModel)} onClick={send}>{busy?'Working…':'Send'} <Send size={15}/></button></div>
    {mode==='litertlm'&&!canUseModel&&<small className="chat-warning">Enable LiteRT-LM and configure a supported model in Runtime & Models first.</small>}
    <small className="chat-footnote">Files up to 10 MiB each. Plain text, Markdown, JSON, CSV and logs can be included as text context. Other file types are stored as attachments only; image/audio/video/document understanding is not enabled by this runtime.</small>
   </div>
  </section>
  {showTools&&<aside className="chat-tools-panel"><div className="chat-sidebar-head"><div><b>Tools & skills</b><small>Explicit approval required</small></div><button className="icon-action secondary" onClick={()=>setShowTools(false)}>×</button></div>
   <label>Built-in tool<select value={toolName} onChange={e=>{setToolName(e.target.value);setSkillName('')}}><option value="calculator">Calculator</option><option value="text_stats">Text statistics</option></select></label>
   <label>{toolName==='calculator'?'Expression':'Text input'}<textarea value={toolInput} onChange={e=>setToolInput(e.target.value)}/></label>
   <div className="chat-approval-card"><ShieldCheck size={16}/><span>Review the exact operation and input before running it.</span></div>
   <label className="chat-approval"><input type="checkbox" checked={toolApproval} onChange={e=>setToolApproval(e.target.checked)}/> I approve this tool operation</label>
   <button className="primary" disabled={busy||!active||!toolApproval||!toolInput.trim()} onClick={executeTool}>Execute approved tool</button>
   <hr/>
   <label>Installed skill<select value={skillName} onChange={e=>{setSkillName(e.target.value);setSkillOperation('')}}><option value="">No skill selected</option>{(tools.skills||[]).map((s:any)=><option key={s.name} value={s.name}>{s.name}</option>)}</select></label>
   {skillName&&<><small>{selectedSkill?.description}</small><label>Skill operation<select value={skillOperation} onChange={e=>setSkillOperation(e.target.value)}><option value="">Choose operation</option>{allowedSkillOps.map((op:string)=><option key={op} value={op}>{op}</option>)}</select></label><label>Input<textarea value={toolInput} onChange={e=>setToolInput(e.target.value)}/></label><button className="primary" disabled={busy||!active||!toolApproval||!skillOperation||!toolInput.trim()} onClick={executeTool}>Run approved skill operation</button></>}
   <p className="chat-footnote">Model text cannot directly invoke tools. Tool calls are separate, visible API requests with per-operation approval.</p>
  </aside>}
 </div>;
}
