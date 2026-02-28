from __future__ import annotations

from core.types import PerceptionResult, Plan


class PlanCritic:
    def review(self, perception: PerceptionResult, plan: Plan) -> list[str]:
        issues: list[str] = []
        if not plan.steps:
            issues.append("Plan has no steps")
        if len(plan.steps) > plan.max_steps:
            issues.append("Plan exceeds max_steps")
        if perception.task_type.value == "summarization" and all(s.tool_name != "summarize" for s in plan.steps):
            issues.append("Missing summarize step for summarization task")
        return issues

