from __future__ import annotations

from core.exceptions import ToolExecutionError
from core.types import BudgetGuard, FailureType, PerceptionResult, Plan, PlanStep, RunStatus, StopReasonType, TaskType
from execution.executor import Executor
from execution.tool_schemas import CalcArgs


def _perception() -> PerceptionResult:
    return PerceptionResult(
        intent="calc",
        task_type=TaskType.CALCULATION,
        entities={"raw_goal": "calc"},
        constraints=[],
        success_criteria=["calculation result available"],
        initial_state={},
    )


def test_executor_stops_on_max_retries(registry, run_trace, run_context_factory):
    def always_fail(args: CalcArgs, ctx):
        raise ToolExecutionError("fail", failure_type=FailureType.TOOL_ERROR)

    registry.get("calc").handler = always_fail
    plan = Plan(
        steps=[PlanStep(step_id="s1", objective="calc", tool_name="calc", tool_args={"expression": "1+1"}, expected_observation="", fallback_strategy="retry")],
        max_steps=5,
        max_retries_per_step=1,
        budget_guard=BudgetGuard(max_cost_units=10),
    )
    run_ctx = run_context_factory(run_trace)
    result = Executor().run(plan, _perception(), run_ctx)
    assert result.status == RunStatus.STOPPED
    assert result.stop_reason.type == StopReasonType.MAX_RETRIES


def test_executor_stops_on_budget_guard(registry, run_trace, run_context_factory):
    plan = Plan(
        steps=[
            PlanStep(step_id="s1", objective="calc", tool_name="calc", tool_args={"expression": "1+1"}, expected_observation="", fallback_strategy="abort"),
            PlanStep(step_id="s2", objective="calc", tool_name="calc", tool_args={"expression": "2+2"}, expected_observation="", fallback_strategy="abort"),
        ],
        max_steps=5,
        max_retries_per_step=1,
        budget_guard=BudgetGuard(max_cost_units=1),
    )
    # Require summary criteria so success does not stop after first calc.
    perception = _perception().model_copy(update={"success_criteria": ["summary produced"]})
    run_ctx = run_context_factory(run_trace)
    result = Executor().run(plan, perception, run_ctx)
    assert result.status == RunStatus.STOPPED
    assert result.stop_reason.type == StopReasonType.BUDGET_GUARD


def test_executor_stops_on_non_progress(registry, run_trace, run_context_factory, test_config):
    def always_fail(args: CalcArgs, ctx):
        raise ToolExecutionError("fail", failure_type=FailureType.TOOL_ERROR)

    registry.get("calc").handler = always_fail
    test_config.non_progress_threshold = 1
    plan = Plan(
        steps=[PlanStep(step_id="s1", objective="calc", tool_name="calc", tool_args={"expression": "1+1"}, expected_observation="", fallback_strategy="retry")],
        max_steps=5,
        max_retries_per_step=5,
        budget_guard=BudgetGuard(max_cost_units=10),
    )
    run_ctx = run_context_factory(run_trace)
    result = Executor().run(plan, _perception(), run_ctx)
    assert result.status == RunStatus.STOPPED
    assert result.stop_reason.type == StopReasonType.NON_PROGRESS

