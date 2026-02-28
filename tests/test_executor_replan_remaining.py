from __future__ import annotations

from core.exceptions import ToolExecutionError
from core.types import FailureType, RunStatus
from execution.executor import Executor
from execution.tool_schemas import HTTPGetArgs, HTTPResult
from llm.heuristic_provider import HeuristicProvider
from perception.agent import PerceptionAgent
from planning.planner import PlannerAgent


def test_executor_replans_remaining_steps_on_schema_error(test_config, long_term_memory, registry, run_trace, run_context_factory):
    planner = PlannerAgent(test_config, long_term_memory=long_term_memory)
    perception = PerceptionAgent(HeuristicProvider(test_config), long_term_memory).run("Fetch malformed endpoint and summarize malformed")
    plan = planner.build_plan(perception, registry.catalog())

    def fake_http_get(args: HTTPGetArgs, ctx):
        if "/malformed" in args.url:
            raise ToolExecutionError("malformed json", failure_type=FailureType.SCHEMA_ERROR)
        return HTTPResult(ok=True, message="ok", data={}, status_code=200, headers={}, body={"ok": True}, malformed=False)

    registry.get("http_get").handler = fake_http_get

    run_ctx = run_context_factory(run_trace, planner=planner)
    result = Executor().run(plan, perception, run_ctx)
    assert result.status == RunStatus.COMPLETED
    assert any(r.action.value == "replan_remaining" for r in run_ctx.trace.refinements)

