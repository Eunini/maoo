from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from core.config import Config
from core.exceptions import PolicyViolationError
from core.types import PlanStep


class PolicyEngine:
    def __init__(self, config: Config) -> None:
        self.config = config

    def validate_step(self, step: PlanStep) -> None:
        if step.tool_name in {"http_get", "http_post"}:
            self._validate_http(step.tool_args)
        elif step.tool_name == "file_write":
            self._validate_file_path(step.tool_args.get("relative_path", ""))
        elif step.tool_name == "db_query":
            self._validate_sql(step.tool_args.get("sql", ""), readonly=bool(step.tool_args.get("readonly", True)))
        elif step.tool_name == "calc":
            self._validate_calc_expression(str(step.tool_args.get("expression", "")))

    def _validate_http(self, tool_args: dict[str, Any]) -> None:
        url = str(tool_args.get("url", ""))
        if not url:
            raise PolicyViolationError("HTTP tool requires URL")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise PolicyViolationError(f"Disallowed URL scheme: {parsed.scheme}", {"url": url})
        host = parsed.hostname or ""
        if host not in self.config.allowed_http_hosts and not self.config.enable_real_http:
            raise PolicyViolationError("Host is not on allowlist", {"host": host, "url": url})

    def _validate_file_path(self, relative_path: str) -> None:
        if not relative_path:
            raise PolicyViolationError("file_write requires relative_path")
        p = Path(relative_path)
        if p.is_absolute():
            raise PolicyViolationError("Absolute paths are not allowed", {"path": relative_path})
        if ".." in p.parts:
            raise PolicyViolationError("Path traversal is not allowed", {"path": relative_path})

    def _validate_sql(self, sql: str, readonly: bool = True) -> None:
        normalized = self._normalize_sql(sql)
        if readonly and not (normalized.startswith("select") or normalized.startswith("pragma")):
            raise PolicyViolationError("Read-only db_query only permits SELECT/PRAGMA", {"sql": sql})
        if not readonly and not self.config.enable_db_writes:
            raise PolicyViolationError("DB writes are disabled", {"sql": sql})

    def _validate_calc_expression(self, expression: str) -> None:
        if not expression:
            raise PolicyViolationError("calc expression required")
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise PolicyViolationError("Invalid calc syntax", {"expression": expression}) from exc
        for node in ast.walk(tree):
            if isinstance(node, (ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp, ast.Load)):
                continue
            if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.UAdd, ast.USub)):
                continue
            raise PolicyViolationError("Unsafe calc expression", {"expression": expression, "node": type(node).__name__})

    @staticmethod
    def _normalize_sql(sql: str) -> str:
        no_comments = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
        return re.sub(r"\s+", " ", no_comments).strip().lower()

