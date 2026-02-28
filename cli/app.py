from __future__ import annotations

import typer

from .commands import register_commands

app = typer.Typer(help="MAOO CLI")
register_commands(app)

