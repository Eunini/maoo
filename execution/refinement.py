from __future__ import annotations

from typing import Any

from core.types import FailureSignal, PerceptionResult, PlanStep, RefinementActionType, RefinementDecision, ToolCatalogEntry


class RefinementEngine:
    def decide(
        self,
        step: PlanStep,
        failure_signal: FailureSignal,
        attempt: int,
        max_retries_per_step: int,
        perception: PerceptionResult,
        tool_catalog: list[ToolCatalogEntry],
        planner: Any = None,
        remaining_steps: list[PlanStep] | None = None,
        scratchpad: dict[str, Any] | None = None,
    ) -> RefinementDecision:
        remaining_steps = remaining_steps or []
        scratchpad = scratchpad or {}

        if failure_signal.failure_type.value == "non_progress":
            return RefinementDecision(action=RefinementActionType.ABORT, reason="Non-progress threshold exceeded")

        prefers_replan = "replan" in step.fallback_strategy or "alternate" in step.fallback_strategy
        if (
            planner is not None
            and failure_signal.failure_type.value in {"schema_error", "bad_response"}
            and prefers_replan
        ):
            replan_scratchpad = dict(scratchpad)
            replan_scratchpad["failure_context"] = {
                "failure_type": failure_signal.failure_type.value,
                "step_id": step.step_id,
                "tool_name": step.tool_name,
            }
            replanned_steps = planner.replan_remaining(perception, remaining_steps, tool_catalog, scratchpad=replan_scratchpad)
            if replanned_steps:
                return RefinementDecision(
                    action=RefinementActionType.REPLAN_REMAINING,
                    replanned_steps=replanned_steps,
                    reason=f"Replanned remaining steps after {failure_signal.failure_type.value}",
                )

        if failure_signal.retryable and attempt < max_retries_per_step:
            patched_args: dict[str, Any] = {}
            if failure_signal.failure_type.value == "timeout" and step.tool_name in {"http_get", "http_post"}:
                current = float(step.tool_args.get("timeout_s", 2.0))
                patched_args["timeout_s"] = min(current * 2, 10.0)
            elif failure_signal.failure_type.value == "schema_error" and step.tool_name == "http_get":
                if not prefers_replan:
                    patched_args["allow_malformed"] = True
                    patched_args["expect_json"] = False
            if patched_args:
                return RefinementDecision(
                    action=RefinementActionType.PATCH_AND_RETRY,
                    patched_args=patched_args,
                    reason=f"Retrying with patched args due to {failure_signal.failure_type.value}",
                )
            return RefinementDecision(
                action=RefinementActionType.PATCH_AND_RETRY,
                patched_args={},
                reason=f"Retrying same args due to retryable {failure_signal.failure_type.value}",
            )

        can_replan = (
            planner is not None
            and failure_signal.failure_type.value in {"schema_error", "bad_response", "tool_error", "timeout"}
            and (prefers_replan or failure_signal.failure_type.value == "schema_error")
        )
        if can_replan:
            replan_scratchpad = dict(scratchpad)
            replan_scratchpad["failure_context"] = {
                "failure_type": failure_signal.failure_type.value,
                "step_id": step.step_id,
                "tool_name": step.tool_name,
            }
            replanned_steps = planner.replan_remaining(perception, remaining_steps, tool_catalog, scratchpad=replan_scratchpad)
            if replanned_steps:
                return RefinementDecision(
                    action=RefinementActionType.REPLAN_REMAINING,
                    replanned_steps=replanned_steps,
                    reason=f"Replanned remaining steps after {failure_signal.failure_type.value}",
                )

        if "skip" in step.fallback_strategy:
            return RefinementDecision(action=RefinementActionType.SKIP_STEP, reason="Fallback strategy permits skip")
        return RefinementDecision(action=RefinementActionType.ABORT, reason="No safe refinement action available")
