"""Bounded strategy evolution; source code and control policies are immutable."""
import random
from dataclasses import dataclass
@dataclass(frozen=True)
class Strategy:
 learning_rate:float=.1
 exploration:float=.15
 discount:float=.95
 retry_limit:int=2
 def validate(self):
  if not .001<=self.learning_rate<=1:raise ValueError('learning_rate out of range')
  if not 0<=self.exploration<=1 or not 0<=self.discount<=1:raise ValueError('probabilities must be in [0,1]')
  if not 0<=self.retry_limit<=10:raise ValueError('retry_limit out of range')
@dataclass
class Candidate:
 strategy:Strategy
 fitness:float
 generation:int
 tests_passed:bool=False
 approved:bool=False
class EvolutionEngine:
 def __init__(self,population_size=12,seed=7):
  if population_size<2:raise ValueError('population_size must be >= 2')
  self.rng=random.Random(seed);self.population_size=population_size;self.generation=0;self.population=[Strategy() for _ in range(population_size)];self.champion=Strategy();self.candidates=[]
 def evolve(self,evaluator):
  scored=sorted(((float(evaluator(s)),s) for s in self.population),key=lambda x:x[0],reverse=True)
  elite=[s for _,s in scored[:max(1,self.population_size//4)]];new=elite.copy()
  while len(new)<self.population_size:
   a,b=self.rng.choice(elite),self.rng.choice(elite)
   child=Strategy(min(1,max(.001,(a.learning_rate+b.learning_rate)/2+self.rng.uniform(-.03,.03))),min(1,max(0,(a.exploration+b.exploration)/2+self.rng.uniform(-.05,.05))),min(1,max(0,(a.discount+b.discount)/2+self.rng.uniform(-.02,.02))),max(0,min(10,round((a.retry_limit+b.retry_limit)/2+self.rng.choice([-1,0,1])))))
   child.validate();new.append(child)
  self.generation+=1;self.population=new;self.candidates=[Candidate(s,f,self.generation) for f,s in scored]
  return self.candidates
 def validate_candidate(self,candidate,test_runner):
  candidate.tests_passed=bool(test_runner(candidate.strategy));return candidate.tests_passed
 def approve_candidate(self,candidate,approved_by_user):
  if not approved_by_user:raise PermissionError('Explicit user approval required')
  if not candidate.tests_passed:raise ValueError('Candidate must pass tests')
  candidate.approved=True;self.champion=candidate.strategy
