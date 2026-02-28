from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import Config, load_config
from core.exceptions import PlanValidationError
from core.logger import get_logger
from core.metrics import MetricsRegistry
from core.tracing import new_run_id, new_trace_id, trace_export_path, utc_now_iso
from core.types import (
    PerceptionResult,
    Plan,
    RunContext,
    RunStatus,
    RunTrace,
    StopReason,
    StopReasonType,
)
from execution.executor import Executor
from execution.monitors import Monitors
from execution.refinement import RefinementEngine
from execution.tool_registry import ToolRegistry
from llm.provider import get_provider
from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory
from perception.agent import PerceptionAgent
from planning.plan_validator import validate_plan
from planning.planner import PlannerAgent
from planning.policy import PolicyEngine


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def export_trace_json(trace: RunTrace, export_dir: Path, prefix: str = "trace") -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    path = trace_export_path(export_dir, trace.trace_id, prefix=prefix)
    path.write_text(trace.model_dump_json(indent=2), encoding="utf-8")
    return path


def run_orchestration(
    raw_goal: str,
    context: dict[str, Any] | None = None,
    config_overrides: dict[str, Any] | None = None,
    export_trace: bool = True,
    trace_prefix: str = "trace",
) -> tuple[RunTrace, Config]:
    config = load_config(config_overrides)
    metrics = MetricsRegistry()
    trace_id = new_trace_id()
    run_id = new_run_id()
    logger = get_logger(config, component="maoo", trace_id=trace_id, run_id=run_id)
    logger.info("run_start", "Starting orchestration run", raw_goal=raw_goal)

    root = _project_root()
    long_term = LongTermMemory(
        sqlite_path=config.sqlite_path,
        schema_path=root / "sql" / "schema.sql",
        seed_path=root / "sql" / "seed_data.sql",
    )
    llm_provider = get_provider(config)
    perception_agent = PerceptionAgent(llm_provider, long_term_memory=long_term)
    planner = PlannerAgent(config, long_term_memory=long_term)
    policy = PolicyEngine(config)
    registry = ToolRegistry()
    registry.register_defaults()
    monitors = Monitors()
    refinement = RefinementEngine()
    executor = Executor()

    trace = RunTrace(
        trace_id=trace_id,
        run_id=run_id,
        request={"raw_goal": raw_goal, "context": context or {}},
        status=RunStatus.RECEIVED,
    )

    try:
        trace.status = RunStatus.PERCEIVED
        perception: PerceptionResult = perception_agent.run(raw_goal, context)
        trace.perception = perception
        logger.info("perception_done", "Perception completed", perception=perception.model_dump())

        trace.status = RunStatus.PLANNED
        plan: Plan = planner.build_plan(perception, registry.catalog(), scratchpad={})
        trace.plan = plan
        logger.info("planning_done", "Planning completed", plan_steps=len(plan.steps))

        trace.status = RunStatus.VALIDATED
        validated = validate_plan(plan, registry, policy)
        trace.plan = validated.plan
        if validated.warnings:
            logger.warning("plan_warnings", "Plan validation warnings", warnings=validated.warnings)

        short_term = ShortTermMemory(initial_state=perception.initial_state)
        run_ctx = RunContext(
            config=config,
            logger=logger,
            metrics=metrics,
            trace=trace,
            registry=registry,
            policy=policy,
            short_term_memory=short_term,
            long_term_memory=long_term,
            planner=planner,
            monitors=monitors,
            refinement=refinement,
        )
        _ = executor.run(validated.plan, perception, run_ctx)

        if trace.status in {RunStatus.COMPLETED, RunStatus.STOPPED, RunStatus.FAILED}:
            logger.info("run_done", "Run completed", status=trace.status.value, stop_reason=trace.stop_reason.type.value)
        else:
            trace.status = RunStatus.FAILED
            trace.stop_reason = StopReason(type=StopReasonType.FAILED, message="Unexpected terminal state")

    except PlanValidationError as exc:
        trace.status = RunStatus.FAILED
        trace.stop_reason = StopReason(type=StopReasonType.VALIDATION_FAILED, message=str(exc))
        trace.finished_at = utc_now_iso()
        logger.error("plan_validation_error", "Plan validation failed", error=str(exc))
    except Exception as exc:
        trace.status = RunStatus.FAILED
        trace.stop_reason = StopReason(type=StopReasonType.FAILED, message=str(exc))
        trace.finished_at = utc_now_iso()
        logger.error("run_exception", "Unhandled orchestration exception", error=str(exc))

    trace.metrics_snapshot = metrics.snapshot()
    if not trace.finished_at:
        trace.finished_at = utc_now_iso()

    # Persist trace and store a compact memory entry for future retrieval.
    try:
        long_term.save_trace(trace)
        long_term.add_memory_entry(
            namespace="facts",
            key=f"run:{trace.run_id}",
            value_text=json.dumps(
                {
                    "request": raw_goal,
                    "status": trace.status.value,
                    "stop_reason": trace.stop_reason.type.value,
                    "summary": trace.final_output.get("message", ""),
                }
            ),
            metadata={"trace_id": trace.trace_id},
        )
    except Exception as exc:  # pragma: no cover - persistence failures should not mask primary result
        logger.error("persist_error", "Failed to persist trace", error=str(exc))

    if export_trace:
        path = export_trace_json(trace, config.traces_dir, prefix=trace_prefix)
        trace.final_output.setdefault("meta", {})["trace_path"] = str(path)

    return trace, config


def main() -> None:
    # Minimal direct entrypoint; richer UX via `python -m cli`.
    trace, _ = run_orchestration("Fetch mock data and summarize the result")
    print(trace.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
