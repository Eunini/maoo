from __future__ import annotations

import re
from typing import Any

from .long_term import LongTermMemory


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(t) > 1}


def retrieve_memory(
    long_term: LongTermMemory,
    namespace: str,
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    query_tokens = _tokenize(query)
    rows = long_term.get_memory_entries(namespace=namespace, limit=200)
    scored: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        value_text = row.get("value_text", "") or ""
        tokens = _tokenize(value_text + " " + (row.get("key", "") or ""))
        score = len(query_tokens.intersection(tokens))
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:limit]]

