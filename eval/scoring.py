from __future__ import annotations

from core.types import EvalScenario, EvalScenarioResult, RunTrace


def _trace_event_tokens(trace: RunTrace) -> set[str]:
    tokens: set[str] = set()
    tokens.add(trace.status.value)
    tokens.add(trace.stop_reason.type.value)
    for ev in trace.step_events:
        tokens.add(ev.status.value)
        if ev.refinement_decision:
            tokens.add(ev.refinement_decision.action.value)
        if ev.failure_signal:
            tokens.add(ev.failure_signal.failure_type.value)
    for sig in trace.monitor_signals:
        tokens.add(sig.failure_type.value)
    return tokens


def score_trace(scenario: EvalScenario, trace: RunTrace, trace_path: str | None = None) -> EvalScenarioResult:
    if trace.status.value != scenario.expected_status:
        return EvalScenarioResult(
            scenario_id=scenario.id,
            passed=False,
            reason=f"Status mismatch: expected {scenario.expected_status}, got {trace.status.value}",
            score=0.0,
            trace_path=trace_path,
        )

    if scenario.expected_stop_reason and trace.stop_reason.type.value != scenario.expected_stop_reason:
        return EvalScenarioResult(
            scenario_id=scenario.id,
            passed=False,
            reason=f"Stop reason mismatch: expected {scenario.expected_stop_reason}, got {trace.stop_reason.type.value}",
            score=0.0,
            trace_path=trace_path,
        )

    output_blob = trace.model_dump_json().lower()
    for needle in scenario.required_output_contains:
        if needle.lower() not in output_blob:
            return EvalScenarioResult(
                scenario_id=scenario.id,
                passed=False,
                reason=f"Required output substring missing: {needle}",
                score=0.0,
                trace_path=trace_path,
            )

    tokens = _trace_event_tokens(trace)
    for needle in scenario.required_trace_events:
        if needle not in tokens:
            return EvalScenarioResult(
                scenario_id=scenario.id,
                passed=False,
                reason=f"Required trace token missing: {needle}",
                score=0.0,
                trace_path=trace_path,
            )
    for needle in scenario.forbidden_trace_events:
        if needle in tokens:
            return EvalScenarioResult(
                scenario_id=scenario.id,
                passed=False,
                reason=f"Forbidden trace token present: {needle}",
                score=0.0,
                trace_path=trace_path,
            )

    return EvalScenarioResult(scenario_id=scenario.id, passed=True, reason="pass", score=1.0, trace_path=trace_path)

