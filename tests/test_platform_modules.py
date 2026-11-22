from mojo_agent.algorithms import dijkstra,tfidf
from mojo_agent.knowledge import KnowledgeGraph
from mojo_agent.workflows import WorkflowStore
from mojo_agent.tools import ToolRegistry
def test_dijkstra_unorderable_tie_nodes():
 a=object();b=object();c=object();cost,path=dijkstra({a:[(b,1),(c,1)]},a,b)
 assert cost==1 and path[0] is a and path[-1] is b
def test_tfidf_tokenizes_words():
 result=tfidf(["hello world","hello mojo"])
 assert "hello" in result[0] and "world" in result[0]
def test_knowledge_graph(tmp_path):
 g=KnowledgeGraph(str(tmp_path/"kg.db"));a=g.add_node("Alpha");b=g.add_node("Beta");g.add_edge(a["id"],b["id"],"connects")
 snap=g.snapshot();assert len(snap["nodes"])==2 and len(snap["edges"])==1
def test_workflow_runner(tmp_path):
 store=WorkflowStore(str(tmp_path/"wf.db"));w=store.create("demo",[{"type":"text","value":"hello"}]);result=store.run(w["id"],ToolRegistry())
 assert result["status"]=="completed" and result["results"][0]["result"]=="hello"
