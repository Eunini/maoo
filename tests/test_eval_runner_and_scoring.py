from __future__ import annotations

import json
from pathlib import Path
import uuid

from core.types import EvalScenario, RunTrace, RunStatus, StopReason, StopReasonType
from core.config import load_config
from eval.runner import run_scenarios
from eval.scoring import score_trace


def _fake_trace() -> RunTrace:
    return RunTrace(
        trace_id="t1",
        run_id="r1",
        request={"raw_goal": "test", "context": {}},
        status=RunStatus.COMPLETED,
        final_output={"message": "ok", "summary": "ok"},
        stop_reason=StopReason(type=StopReasonType.SUCCESS_CRITERIA_MET, message="done"),
    )


def test_scenarios_file_contains_at_least_20_cases():
    scenarios = json.loads(Path("eval/scenarios.json").read_text(encoding="utf-8"))
    assert len(scenarios) >= 20


def test_scoring_returns_pass_for_matching_trace():
    scenario = EvalScenario(
        id="s",
        description="d",
        request="r",
        expected_status="COMPLETED",
        required_output_contains=["ok"],
        required_trace_events=[],
        forbidden_trace_events=[],
    )
    result = score_trace(scenario, _fake_trace(), trace_path="x.json")
    assert result.passed is True


def test_eval_runner_exports_trace_and_summary(monkeypatch):
    base = Path("runtime") / "traces"
    base.mkdir(parents=True, exist_ok=True)
    scenarios_path = base / f"scenarios_{uuid.uuid4().hex}.json"
    scenarios_path.write_text(
        json.dumps(
            [
                {
                    "id": "one",
                    "description": "d",
                    "request": "anything",
                    "expected_status": "COMPLETED",
                    "required_output_contains": [],
                    "required_trace_events": [],
                    "forbidden_trace_events": []
                }
            ]
        ),
        encoding="utf-8",
    )

    def fake_run_orchestration(*args, **kwargs):
        cfg = load_config(
            {
                "runtime_dir": Path("runtime"),
                "logs_dir": Path("runtime/logs"),
                "traces_dir": Path("runtime/traces"),
                "workspace_dir": Path("runtime/workspace"),
                "sqlite_dir": Path("runtime/sqlite"),
                "sqlite_path": Path("runtime/sqlite") / f"eval_{uuid.uuid4().hex}.db",
                "file_workspace_root": Path("runtime/workspace"),
                "log_to_file": False,
            }
        )
        return _fake_trace(), cfg

    import eval.runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_orchestration", fake_run_orchestration)
    monkeypatch.setattr(
        runner_mod,
        "load_config",
        lambda: load_config(
            {
                "runtime_dir": Path("runtime"),
                "logs_dir": Path("runtime/logs"),
                "traces_dir": Path("runtime/traces"),
                "workspace_dir": Path("runtime/workspace"),
                "sqlite_dir": Path("runtime/sqlite"),
                "sqlite_path": Path("runtime/sqlite") / f"eval_runner_{uuid.uuid4().hex}.db",
                "file_workspace_root": Path("runtime/workspace"),
                "log_to_file": False,
            }
        ),
    )

    export_dir = Path("runtime/traces")
    summary = run_scenarios(scenarios_path, export_dir)
    assert summary.total == 1
    assert (export_dir / "one.trace.json").exists()
    assert (export_dir / "eval_summary.json").exists()
