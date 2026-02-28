from __future__ import annotations

import re
from typing import Any


def extract_intent_and_entities(raw_goal: str, context: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    context = context or {}
    lower = raw_goal.lower()
    entities: dict[str, Any] = {"raw_goal": raw_goal}

    url_match = re.search(r"https?://[^\s]+", raw_goal)
    if url_match:
        entities["url"] = url_match.group(0)

    if any(t in lower for t in ["save", "write"]):
        entities["write_requested"] = True
    if any(t in lower for t in ["summary", "summarize"]):
        entities["summarize_requested"] = True
    if any(t in lower for t in ["calc", "calculate", "multiply"]) or re.search(r"\bsum\b", lower):
        entities["calc_requested"] = True
        expr_match = re.search(r"calc(?:ulate)?[:\s]+([0-9\+\-\*\/\(\)\.\s%]+)", lower)
        if expr_match:
            entities["expression"] = expr_match.group(1).strip()
    if any(t in lower for t in ["db", "database", "sql"]):
        entities["db_requested"] = True

    if "flaky" in lower:
        entities["endpoint_mode"] = "flaky"
    if "slow" in lower:
        entities["endpoint_mode"] = "slow"
    if "malformed" in lower:
        entities["endpoint_mode"] = "malformed"

    if "non-existent tool" in lower:
        entities["force_invalid_tool"] = True
    if "invalid args" in lower:
        entities["force_invalid_args"] = True
    if "example.com" in lower:
        entities["external_url"] = "http://example.com"
    if "delete row" in lower or "drop table" in lower:
        entities["unsafe_sql"] = True
    if "../" in raw_goal or "..\\" in raw_goal:
        entities["unsafe_path"] = True
    if "__import__" in raw_goal:
        entities["unsafe_calc"] = True
    if "long plan" in lower:
        entities["force_long_plan"] = True
    if "budget test" in lower:
        entities["force_budget_heavy"] = True
    if "early stop" in lower:
        entities["force_extra_steps_after_success"] = True

    if context:
        entities["context"] = context

    if any(t in lower for t in ["post", "submit"]):
        intent = "submit data and inspect response"
    elif any(t in lower for t in ["fetch", "get", "retrieve", "flaky", "slow", "malformed"]):
        intent = "retrieve data"
    elif "db" in lower or "sql" in lower:
        intent = "query database"
    elif any(t in lower for t in ["calc", "calculate"]) or re.search(r"\bsum\b", lower):
        intent = "calculate a value"
    elif "summarize" in lower:
        intent = "summarize content"
    else:
        intent = "orchestrate a multi-step task"
    return intent, entities
