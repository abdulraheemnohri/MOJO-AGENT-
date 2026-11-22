import pytest
from mojo_agent.algorithms import bfs,dfs,dijkstra,q_update,tfidf,cosine_similarity,moving_average
def test_search():
 g={'A':['B','C'],'B':['D'],'C':['D'],'D':[]};assert bfs(g,'A','D') in (['A','B','D'],['A','C','D']);assert dfs(g,'A','D') is not None;assert bfs(g,'D','A') is None
def test_dijkstra():
 assert dijkstra({'a':[('b',2)],'b':[('c',3)],'c':[]},'a','c')==(5.0,['a','b','c'])
 with pytest.raises(ValueError):dijkstra({'a':[('b',-1)],'b':[]},'a','b')
def test_learning_text():
 assert q_update(0,1,0,1,0)==1;v=tfidf(['solar power','power grid']);assert cosine_similarity(v[0],v[1])>0;assert moving_average([1,2,3],2)==[1,1.5,2.5]
