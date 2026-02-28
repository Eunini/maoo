from __future__ import annotations

from typing import Any

from core.exceptions import ToolExecutionError
from core.types import FailureType
from execution.tool_schemas import DBQueryArgs, DBQueryResult


def db_query_tool(args: DBQueryArgs, ctx: Any) -> DBQueryResult:
    long_term = getattr(ctx, "long_term_memory", None)
    if long_term is None:
        raise ToolExecutionError("Long-term memory DB is not available", failure_type=FailureType.TOOL_ERROR)
    try:
        rows = long_term.query(args.sql, args.params)
    except Exception as exc:
        raise ToolExecutionError(
            f"db_query failed: {exc}",
            failure_type=FailureType.TOOL_ERROR,
            diagnostics={"sql": args.sql},
        ) from exc
    if args.limit is not None:
        rows = rows[: args.limit]
    return DBQueryResult(
        ok=True,
        message="db_query completed",
        data={"sql": args.sql},
        rows=rows,
        row_count=len(rows),
    )

