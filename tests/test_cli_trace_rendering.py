from __future__ import annotations

from io import StringIO

from rich.console import Console

from cli.render import render_trace
from core.types import RunStatus, RunTrace, StopReason, StopReasonType


def test_cli_render_contains_required_sections():
    trace = RunTrace(
        trace_id="t",
        run_id="r",
        request={"raw_goal": "hello", "context": {}},
        status=RunStatus.COMPLETED,
        final_output={"message": "done"},
        stop_reason=StopReason(type=StopReasonType.SUCCESS_CRITERIA_MET, message="done"),
    )
    sio = StringIO()
    console = Console(file=sio, force_terminal=False, width=120, color_system=None)
    render_trace(trace, console=console)
    out = sio.getvalue()
    assert "User Request" in out
    assert "Perceived Intent + Structured State" in out
    assert "Plan (Steps)" in out
    assert "Execution Logs + Tool Calls" in out
    assert "Final Output" in out

