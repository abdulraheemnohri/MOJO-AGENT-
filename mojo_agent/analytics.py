"""Transparent in-process runtime metrics."""
import time
class Analytics:
 def __init__(self):self.events=[]
 def record(self,event,detail=None):
  self.events.append({"event":event,"detail":detail or {},"time":time.time()});self.events=self.events[-1000:]
 def summary(self):
  counts={}
  for e in self.events:counts[e["event"]]=counts.get(e["event"],0)+1
  return {"events_total":len(self.events),"counts":counts,"recent":list(reversed(self.events[-20:]))}
