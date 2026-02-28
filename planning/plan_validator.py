from __future__ import annotations

from copy import deepcopy

from core.exceptions import PlanValidationError, PolicyViolationError
from core.types import Plan, PlanStep, ValidatedPlan
from execution.tool_registry import ToolRegistry

from .policy import PolicyEngine


def validate_plan(plan: Plan, registry: ToolRegistry, policy: PolicyEngine) -> ValidatedPlan:
    validated_steps: list[PlanStep] = []
    warnings: list[str] = []
    for step in plan.steps:
        if not registry.has_tool(step.tool_name):
            raise PlanValidationError(f"Unknown tool in plan: {step.tool_name}", {"step_id": step.step_id})
        try:
            policy.validate_step(step)
        except PolicyViolationError as exc:
            raise PlanValidationError(str(exc), {"step_id": step.step_id, **getattr(exc, "diagnostics", {})}) from exc
        try:
            validated_args = registry.validate_args(step.tool_name, step.tool_args)
        except Exception as exc:
            raise PlanValidationError(
                f"Invalid tool args for {step.tool_name}: {exc}",
                {"step_id": step.step_id, "tool_name": step.tool_name},
            ) from exc
        step_copy = deepcopy(step)
        step_copy.tool_args = validated_args.model_dump()
        validated_steps.append(step_copy)
    return ValidatedPlan(
        plan=Plan(
            steps=validated_steps,
            max_steps=plan.max_steps,
            max_retries_per_step=plan.max_retries_per_step,
            budget_guard=plan.budget_guard,
            planner_notes=plan.planner_notes,
        ),
        warnings=warnings,
    )

