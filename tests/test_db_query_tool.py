from __future__ import annotations

from core.types import ToolExecutionContext
from execution.tool_schemas import DBQueryArgs
from execution.tools.db_query_tool import db_query_tool


def test_db_query_tool_returns_seeded_rows(test_config, long_term_memory):
    ctx = ToolExecutionContext(
        trace_id="t",
        run_id="r",
        step_id="s1",
        attempt=1,
        config=test_config,
        logger=None,
        short_term_memory=None,
        long_term_memory=long_term_memory,
        metrics=None,
    )
    result = db_query_tool(DBQueryArgs(sql="SELECT * FROM demo_numbers ORDER BY id", readonly=True, limit=2), ctx)
    assert result.ok is True
    assert result.row_count == 2

