from __future__ import annotations

from pathlib import Path
from typing import Any

from core.exceptions import ToolExecutionError
from core.types import FailureType
from execution.tool_schemas import FileWriteArgs, FileWriteResult


def file_write_tool(args: FileWriteArgs, ctx: Any) -> FileWriteResult:
    root = Path(getattr(ctx.config, "file_workspace_root"))
    root.mkdir(parents=True, exist_ok=True)
    candidate = root / args.relative_path
    resolved = candidate.resolve()
    root_resolved = root.resolve()
    if root_resolved not in resolved.parents and resolved != root_resolved:
        raise ToolExecutionError(
            "file_write path escapes workspace",
            failure_type=FailureType.POLICY_VIOLATION,
            diagnostics={"path": args.relative_path},
        )
    if args.create_dirs:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    if resolved.exists() and not args.overwrite:
        raise ToolExecutionError(
            "file exists and overwrite=False",
            failure_type=FailureType.TOOL_ERROR,
            diagnostics={"path": str(resolved)},
        )
    data = args.content.encode("utf-8")
    resolved.write_bytes(data)
    return FileWriteResult(
        ok=True,
        message="file_write completed",
        data={"relative_path": args.relative_path},
        path=str(resolved),
        bytes_written=len(data),
    )

