from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from core.config import load_config
from core.types import RunTrace
from eval.runner import run_scenarios
from execution.tool_registry import ToolRegistry
from main import run_orchestration
from memory.long_term import LongTermMemory

from .render import render_eval_summary, render_trace


def register_commands(app: typer.Typer) -> None:
    console = Console()

    @app.command()
    def run(
        request: str = typer.Option("", help="Raw user request"),
        request_file: str = typer.Option("", help="Path to JSON file with {'request': '...'}"),
        context_json: str = typer.Option("", help="Optional context JSON object"),
        no_export_trace: bool = typer.Option(False, help="Disable trace export"),
    ) -> None:
        if request_file:
            payload = json.loads(Path(request_file).read_text(encoding="utf-8"))
            request_text = payload.get("request") or payload.get("raw_goal") or ""
            context = payload.get("context", {})
        else:
            request_text = request
            context = {}
        if context_json:
            context.update(json.loads(context_json))
        if not request_text:
            raise typer.BadParameter("Provide --request or --request-file")
        trace, _ = run_orchestration(request_text, context=context, export_trace=not no_export_trace)
        render_trace(trace, console=console)

    @app.command()
    def demo(name: str = typer.Argument("happy")) -> None:
        demos = {
            "happy": "Fetch mock data, calculate result, summarize, and write file",
            "refinement": "Fetch from flaky endpoint and summarize result after retry flaky",
            "stop": "Fetch malformed endpoint repeatedly and stop safely malformed safe exit",
        }
        if name not in demos:
            raise typer.BadParameter(f"Unknown demo: {name}")
        trace, _ = run_orchestration(demos[name], context={"demo": name})
        render_trace(trace, console=console)

    @app.command()
    def eval(
        scenarios_path: str = typer.Option("eval/scenarios.json", help="Path to eval scenarios JSON"),
        export_dir: str = typer.Option("runtime/traces", help="Directory to export eval traces"),
    ) -> None:
        summary = run_scenarios(scenarios_path, export_dir)
        render_eval_summary(summary, console=console)

    @app.command("show-trace")
    def show_trace(path: str) -> None:
        trace = RunTrace.model_validate_json(Path(path).read_text(encoding="utf-8"))
        render_trace(trace, console=console)

    @app.command("list-tools")
    def list_tools() -> None:
        registry = ToolRegistry()
        registry.register_defaults()
        for tool in registry.catalog():
            console.print(f"- {tool.name}: {tool.description} [{', '.join(tool.tags)}]")

    @app.command("seed-memory")
    def seed_memory() -> None:
        cfg = load_config()
        ltm = LongTermMemory(cfg.sqlite_path, schema_path=Path("sql/schema.sql"), seed_path=Path("sql/seed_data.sql"))
        ltm.add_memory_entry("facts", "seed:mock-api", "Mock API /data endpoint returns numbers and sum fields", {"source": "cli"})
        ltm.add_memory_entry("facts", "seed:refinement", "Flaky endpoints may succeed on retry after transient failure", {"source": "cli"})
        console.print("Seeded long-term memory entries.")

