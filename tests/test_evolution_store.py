from mojo_agent.evolution import Candidate,Strategy
from mojo_agent.evolution_store import EvolutionStore

def test_candidates_champion_and_generation_persist(tmp_path):
 p=str(tmp_path/"state.sqlite3");s=EvolutionStore(p)
 c=Candidate(Strategy(learning_rate=.25,exploration=.2),.91,3,True,True)
 s.save_candidate("c1",c);s.set_champion(c.strategy);s.set_generation(7)
 s=EvolutionStore(p);r=s.get_candidate("c1")
 assert r and r.tests_passed and r.approved and r.fitness==.91
 assert s.get_champion().learning_rate==.25
 assert s.get_generation()==7
 assert s.list_candidates()[0]["id"]=="c1"

def test_generation_defaults_to_zero(tmp_path):
 assert EvolutionStore(str(tmp_path/"new.sqlite3")).get_generation()==0
