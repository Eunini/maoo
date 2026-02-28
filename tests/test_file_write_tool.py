from __future__ import annotations

import pytest

from core.exceptions import ToolExecutionError
from core.types import ToolExecutionContext
from execution.tool_schemas import FileWriteArgs
from execution.tools.file_write_tool import file_write_tool


def _ctx(test_config):
    return ToolExecutionContext(
        trace_id="t",
        run_id="r",
        step_id="s1",
        attempt=1,
        config=test_config,
        logger=None,
        short_term_memory=None,
        long_term_memory=None,
        metrics=None,
    )


def test_file_write_tool_writes_inside_workspace(test_config):
    res = file_write_tool(FileWriteArgs(relative_path="a/b.txt", content="hello", overwrite=True), _ctx(test_config))
    assert res.ok is True
    assert "b.txt" in res.path


def test_file_write_tool_rejects_escape_path(test_config):
    with pytest.raises(ToolExecutionError):
        file_write_tool(FileWriteArgs(relative_path="../escape.txt", content="x", overwrite=True), _ctx(test_config))

