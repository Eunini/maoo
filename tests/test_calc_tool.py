from __future__ import annotations

import pytest

from core.exceptions import ToolExecutionError
from core.types import ToolExecutionContext
from execution.tool_schemas import CalcArgs
from execution.tools.calc_tool import calc_tool


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


def test_calc_tool_evaluates_expression(test_config):
    result = calc_tool(CalcArgs(expression="2 + 3 * 4"), _ctx(test_config))
    assert result.result == 14


def test_calc_tool_blocks_unsafe_expression(test_config):
    with pytest.raises(ToolExecutionError):
        calc_tool(CalcArgs(expression="__import__('os').system('bad')"), _ctx(test_config))

