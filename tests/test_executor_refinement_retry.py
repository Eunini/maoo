from __future__ import annotations

from core.exceptions import ToolExecutionError
from core.types import BudgetGuard, FailureType, PerceptionResult, Plan, PlanStep, RunStatus, TaskType
from execution.executor import Executor
from execution.tool_schemas import CalcArgs, CalcResult


def test_executor_retries_and_recovers_with_refinement(registry, run_trace, run_context_factory):
    attempts = {"n": 0}

    def flaky_calc(args: CalcArgs, ctx):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ToolExecutionError("transient calc failure", failure_type=FailureType.TOOL_ERROR)
        return CalcResult(ok=True, message="ok", data={}, result=3)

    registry.get("calc").handler = flaky_calc

    perception = PerceptionResult(
        intent="calc",
        task_type=TaskType.CALCULATION,
        entities={"raw_goal": "calculate"},
        constraints=[],
        success_criteria=["calculation result available"],
        initial_state={},
    )
    plan = Plan(
        steps=[
            PlanStep(
                step_id="s1",
                objective="calc",
                tool_name="calc",
                tool_args={"expression": "1 + 2"},
                expected_observation="3",
                fallback_strategy="retry",
            )
        ],
        max_steps=3,
        max_retries_per_step=2,
        budget_guard=BudgetGuard(max_cost_units=10),
    )
    run_ctx = run_context_factory(run_trace)
    result = Executor().run(plan, perception, run_ctx)
    assert attempts["n"] == 2
    assert result.status == RunStatus.COMPLETED
    assert any(r.action.value == "patch_and_retry" for r in run_ctx.trace.refinements)

