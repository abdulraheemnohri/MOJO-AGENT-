from fastapi.testclient import TestClient
from mojo_agent import api
from mojo_agent.evolution import Candidate, Strategy, EvolutionEngine

def test_approved_candidate_can_be_restored_from_store(monkeypatch,tmp_path):
 store=api.EvolutionStore(str(tmp_path/"evolution.sqlite3"))
 candidate=Candidate(Strategy(learning_rate=.3),.9,1,True,False)
 store.save_candidate("persisted-candidate",candidate)
 monkeypatch.setattr(api,"evolution_store",store)
 monkeypatch.setattr(api,"evolution",EvolutionEngine())
 client=TestClient(api.app)
 response=client.post("/api/v1/evolution/candidates/persisted-candidate/approve",json={"approved":True})
 assert response.status_code==200
 assert response.json()["approved"] is True
 assert store.get_candidate("persisted-candidate").approved is True
 assert store.get_champion().learning_rate==.3

def test_generation_is_restored_from_store(tmp_path):
 store=api.EvolutionStore(str(tmp_path/"generation.sqlite3"))
 store.set_generation(12)
 assert store.get_generation()==12
