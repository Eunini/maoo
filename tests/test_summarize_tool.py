from __future__ import annotations

from core.types import ToolExecutionContext
from execution.tool_schemas import SummarizeArgs
from execution.tools.summarize_tool import summarize_tool
from memory.short_term import ShortTermMemory


def test_summarize_tool_uses_heuristic_provider_in_no_llm_mode(test_config):
    ctx = ToolExecutionContext(
        trace_id="t",
        run_id="r",
        step_id="s1",
        attempt=1,
        config=test_config,
        logger=None,
        short_term_memory=ShortTermMemory({"note": "x"}),
        long_term_memory=None,
        metrics=None,
    )
    res = summarize_tool(
        SummarizeArgs(text="Sentence one. Sentence two. Sentence three.", max_sentences=2, style="brief"),
        ctx,
    )
    assert res.ok is True
    assert "Sentence one." in res.summary

