from __future__ import annotations

from core.types import ToolCallRecord, ToolCallStatus
from execution.monitors import Monitors


def test_monitors_classify_timeout_schema_and_error():
    m = Monitors()
    timeout_signals = m.evaluate_tool_call(
        ToolCallRecord(step_id="s1", step_attempt_id="a1", tool_name="http_get", status=ToolCallStatus.TIMEOUT)
    )
    schema_signals = m.evaluate_tool_call(
        ToolCallRecord(step_id="s1", step_attempt_id="a2", tool_name="http_get", status=ToolCallStatus.SCHEMA_ERROR)
    )
    error_signals = m.evaluate_tool_call(
        ToolCallRecord(step_id="s1", step_attempt_id="a3", tool_name="http_get", status=ToolCallStatus.ERROR)
    )
    assert timeout_signals[0].failure_type.value == "timeout"
    assert schema_signals[0].failure_type.value == "schema_error"
    assert error_signals[0].failure_type.value == "tool_error"

