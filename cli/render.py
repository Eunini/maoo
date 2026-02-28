from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.types import EvalSummary, RunTrace
from .formatters import pretty_json


def render_trace(trace: RunTrace, console: Console | None = None) -> None:
    console = console or Console()
    console.print(Panel(pretty_json(trace.request), title="User Request"))
    console.print(Panel(pretty_json(trace.perception.model_dump() if trace.perception else {}), title="Perceived Intent + Structured State"))
    console.print(Panel(pretty_json(trace.plan.model_dump() if trace.plan else {}), title="Plan (Steps)"))

    tool_table = Table(title="Execution Logs + Tool Calls")
    tool_table.add_column("Step")
    tool_table.add_column("Tool")
    tool_table.add_column("Status")
    tool_table.add_column("Latency ms")
    tool_table.add_column("Details")
    for call in trace.tool_calls:
        tool_table.add_row(call.step_id, call.tool_name, call.status.value, str(call.latency_ms), call.error or "ok")
    console.print(tool_table)

    console.print(Panel(pretty_json(trace.final_output), title="Final Output"))
    console.print(Panel(f"status={trace.status.value}\nstop_reason={trace.stop_reason.type.value}", title="Run Status"))


def render_eval_summary(summary: EvalSummary, console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="Evaluation Summary")
    table.add_column("Scenario")
    table.add_column("Pass")
    table.add_column("Score")
    table.add_column("Reason")
    for r in summary.results:
        table.add_row(r.scenario_id, "Y" if r.passed else "N", f"{r.score:.1f}", r.reason)
    console.print(table)
    console.print(f"Passed {summary.passed}/{summary.total}")

