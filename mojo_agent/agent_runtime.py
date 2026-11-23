"""Algorithm-first and optional local-model hybrid orchestration."""
from __future__ import annotations
from .planner import decompose_goal, topological_order
from .litertlm import LiteRTLM, LiteRTLMError

class AgentRuntime:
    MODES = {"algorithms", "hybrid", "litertlm"}
    def __init__(self, model_runtime=None):
        self.model_runtime = model_runtime or LiteRTLM()

    def status(self):
        model = self.model_runtime.status()
        return {"modes": sorted(self.MODES), "default_mode":"algorithms",
                "active_mode":"algorithms", "llm_required":False,
                "model_runtime":model,
                "hybrid_policy":"deterministic planner remains authoritative; model output is advisory",
                "tools_auto_execute":False}

    def run(self, goal, mode="algorithms", model="", backend="cpu", approved=False):
        if mode not in self.MODES: raise ValueError("mode must be algorithms, hybrid or litertlm")
        tasks = decompose_goal(goal)
        order = topological_order({task["id"]:task["depends_on"] for task in tasks})
        result = {"goal":goal,"mode":mode,"algorithm_result":{"tasks":tasks,"execution_order":order},
                  "tool_execution":"not automatic","policy":"deterministic plan is authoritative"}
        if mode == "algorithms":
            result["model_result"] = None
            return result
        if not model: raise ValueError("select a local .litertlm model or Hugging Face model id")
        if not approved: raise PermissionError("Local model inference requires explicit operator approval")
        prompt = ("You are an advisory planning assistant. Do not execute tools or claim actions were performed. "
                  "Review this goal and deterministic task plan. Suggest risks and improvements only.\n"
                  f"Goal: {goal}\nPlan: {tasks}")
        try:
            model_result = self.model_runtime.run(model,prompt,backend=backend,approved=True)
        except (LiteRTLMError, ValueError, OSError) as exc:
            raise RuntimeError(str(exc)) from exc
        result["model_result"] = model_result
        result["hybrid_policy"] = "model suggestions are advisory; deterministic plan and tool approval remain authoritative"
        return result
