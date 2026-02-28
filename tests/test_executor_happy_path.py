from __future__ import annotations

from core.types import BudgetGuard, PerceptionResult, Plan, PlanStep, RunStatus, TaskType
from execution.executor import Executor


def test_executor_happy_path_completes(test_config, registry, run_trace, run_context_factory):
    perception = PerceptionResult(
        intent="calc and summarize",
        task_type=TaskType.COMPOSITE,
        entities={"raw_goal": "calc and summarize"},
        constraints=[],
        success_criteria=["summary produced"],
        initial_state={},
    )
    plan = Plan(
        steps=[
            PlanStep(
                step_id="s1",
                objective="calc",
                tool_name="calc",
                tool_args={"expression": "2 + 2"},
                expected_observation="4",
                fallback_strategy="abort",
            ),
            PlanStep(
                step_id="s2",
                objective="summarize",
                tool_name="summarize",
                tool_args={"text": "hello. world.", "max_sentences": 1, "style": "brief"},
                expected_observation="summary",
                fallback_strategy="abort",
            ),
        ],
        max_steps=5,
        max_retries_per_step=2,
        budget_guard=BudgetGuard(max_cost_units=10),
    )
    run_ctx = run_context_factory(run_trace)
    result = Executor().run(plan, perception, run_ctx)
    assert result.status == RunStatus.COMPLETED
    assert run_ctx.trace.tool_calls

