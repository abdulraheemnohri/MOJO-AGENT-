from collections import defaultdict,deque
def topological_order(deps:dict[str,list[str]]):
 nodes=set(deps)
 for values in deps.values():nodes.update(values)
 degree={n:0 for n in nodes};children=defaultdict(list)
 for task,parents in deps.items():
  for parent in parents:degree[task]+=1;children[parent].append(task)
 q=deque(sorted(n for n,d in degree.items() if d==0));out=[]
 while q:
  n=q.popleft();out.append(n)
  for child in children[n]:
   degree[child]-=1
   if degree[child]==0:q.append(child)
 if len(out)!=len(nodes):raise ValueError('Task dependency cycle detected')
 return out
def decompose_goal(goal:str):
 if not goal.strip():raise ValueError('Goal cannot be empty')
 parts=[p.strip(' .') for p in goal.replace(' then ',';').split(';') if p.strip(' .')]
 return [{'id':f'task-{i}','title':p,'depends_on':[f'task-{i-1}'] if i>1 else []} for i,p in enumerate(parts,1)]
