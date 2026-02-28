from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel

from core.types import ToolCatalogEntry


@dataclass
class ToolSpec:
    name: str
    description: str
    args_model: type[BaseModel]
    result_model: type[BaseModel]
    handler: Callable[[BaseModel, Any], BaseModel]
    safe_by_default: bool = True
    tags: list[str] | None = None


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def validate_args(self, name: str, args: dict[str, Any]) -> BaseModel:
        return self.get(name).args_model.model_validate(args or {})

    def execute(self, name: str, args: dict[str, Any], ctx: Any) -> BaseModel:
        spec = self.get(name)
        args_model = spec.args_model.model_validate(args or {})
        return spec.handler(args_model, ctx)

    def catalog(self) -> list[ToolCatalogEntry]:
        out: list[ToolCatalogEntry] = []
        for name in sorted(self._tools):
            spec = self._tools[name]
            out.append(
                ToolCatalogEntry(
                    name=spec.name,
                    description=spec.description,
                    safe_by_default=spec.safe_by_default,
                    tags=spec.tags or [],
                )
            )
        return out

    def register_defaults(self) -> None:
        from execution.tool_schemas import (
            CalcArgs,
            CalcResult,
            DBQueryArgs,
            DBQueryResult,
            FileWriteArgs,
            FileWriteResult,
            HTTPGetArgs,
            HTTPPostArgs,
            HTTPResult,
            SummarizeArgs,
            SummarizeResult,
        )
        from execution.tools import (
            calc_tool,
            db_query_tool,
            file_write_tool,
            http_get_tool,
            http_post_tool,
            summarize_tool,
        )

        self.register(
            ToolSpec(
                "http_get",
                "HTTP GET against allowlisted hosts",
                HTTPGetArgs,
                HTTPResult,
                http_get_tool,
                True,
                ["http", "read"],
            )
        )
        self.register(
            ToolSpec(
                "http_post",
                "HTTP POST against allowlisted hosts",
                HTTPPostArgs,
                HTTPResult,
                http_post_tool,
                True,
                ["http", "write"],
            )
        )
        self.register(
            ToolSpec(
                "db_query",
                "Read-only SQLite query tool",
                DBQueryArgs,
                DBQueryResult,
                db_query_tool,
                True,
                ["db", "read"],
            )
        )
        self.register(
            ToolSpec(
                "file_write",
                "Write text file in sandbox workspace",
                FileWriteArgs,
                FileWriteResult,
                file_write_tool,
                True,
                ["file"],
            )
        )
        self.register(
            ToolSpec("calc", "Safe arithmetic evaluator", CalcArgs, CalcResult, calc_tool, True, ["math"])
        )
        self.register(
            ToolSpec(
                "summarize",
                "LLM-backed or deterministic summarizer",
                SummarizeArgs,
                SummarizeResult,
                summarize_tool,
                True,
                ["llm", "text"],
            )
        )

