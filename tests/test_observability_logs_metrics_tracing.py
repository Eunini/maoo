from __future__ import annotations

from core.logger import StructuredLogger
from core.metrics import MetricsRegistry
from core.tracing import new_step_attempt_id, new_trace_id


def test_trace_id_and_step_attempt_id_generation():
    trace_id = new_trace_id()
    step_attempt_id = new_step_attempt_id()
    assert len(trace_id) == 32
    assert len(step_attempt_id) == 16


def test_metrics_and_structured_logger_emit_json(capsys):
    metrics = MetricsRegistry()
    metrics.inc("tool_calls_total", labels={"tool": "calc", "status": "success"})
    snap = metrics.snapshot()
    assert any(k.startswith("tool_calls_total") for k in snap)

    logger = StructuredLogger(component="test", context={"trace_id": "t", "run_id": "r"}, log_file=None)
    logger.info("event_name", "message", x=1)
    captured = capsys.readouterr()
    assert '"event": "event_name"' in captured.out
    assert '"trace_id": "t"' in captured.out
