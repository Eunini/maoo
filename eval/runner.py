from __future__ import annotations

import json
from pathlib import Path

from core.config import load_config
from core.types import EvalScenario, EvalSummary
from main import run_orchestration
from memory.long_term import LongTermMemory

from .scoring import score_trace
from .trace_export import export_eval_summary, export_trace


def _load_scenarios(scenarios_path: str | Path) -> list[EvalScenario]:
    data = json.loads(Path(scenarios_path).read_text(encoding="utf-8"))
    return [EvalScenario.model_validate(item) for item in data]


def run_scenarios(scenarios_path: str | Path, export_dir: str | Path) -> EvalSummary:
    scenarios = _load_scenarios(scenarios_path)
    results = []
    cfg = load_config()
    long_term = LongTermMemory(cfg.sqlite_path, schema_path=Path("sql/schema.sql"), seed_path=Path("sql/seed_data.sql"))

    for scenario in scenarios:
        trace, _ = run_orchestration(
            raw_goal=scenario.request,
            context=scenario.context,
            config_overrides=scenario.config_overrides,
            export_trace=False,
            trace_prefix=f"eval_{scenario.id}",
        )
        filename = f"{scenario.id}.trace.json"
        trace_path = export_trace(trace, export_dir, filename)
        scored = score_trace(scenario, trace, trace_path=str(trace_path))
        results.append(scored)
        long_term.save_eval_result(scored.scenario_id, scored.passed, scored.reason, scored.score, scored.trace_path)

    summary = EvalSummary(
        total=len(results),
        passed=sum(1 for r in results if r.passed),
        failed=sum(1 for r in results if not r.passed),
        results=results,
    )
    export_eval_summary(summary, export_dir)
    return summary

