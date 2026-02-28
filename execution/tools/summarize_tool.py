from __future__ import annotations

import json
from typing import Any

from execution.tool_schemas import SummarizeArgs, SummarizeResult
from llm.provider import get_provider


def summarize_tool(args: SummarizeArgs, ctx: Any) -> SummarizeResult:
    provider = get_provider(ctx.config)
    text = args.text
    if not text and getattr(ctx, "short_term_memory", None):
        text = json.dumps(ctx.short_term_memory.state, sort_keys=True, default=str)
    summary = provider.generate_text(text, text=text, max_sentences=args.max_sentences)
    if args.style == "bullet":
        pieces = [p.strip() for p in summary.split(".") if p.strip()]
        summary = "\n".join(f"- {p}" for p in pieces[: args.max_sentences])
    return SummarizeResult(
        ok=True,
        message="summarize completed",
        data={"style": args.style},
        summary=summary,
    )

