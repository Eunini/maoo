from __future__ import annotations

from core.types import TaskType


def classify_task(raw_goal: str) -> TaskType:
    lower = raw_goal.lower()
    has_sum_word = " sum " in f" {lower} "
    flags = {
        "http": any(t in lower for t in ["fetch", "get", "post", "submit", "flaky", "slow", "malformed", "http"]),
        "db": any(t in lower for t in ["db", "database", "sql"]),
        "file": any(t in lower for t in ["write", "save", "file"]),
        "calc": any(t in lower for t in ["calc", "calculate", "multiply"]) or has_sum_word,
        "summary": any(t in lower for t in ["summary", "summarize"]),
    }
    if sum(1 for v in flags.values() if v) > 1:
        return TaskType.COMPOSITE
    if flags["http"] and any(t in lower for t in ["post", "submit"]):
        return TaskType.DATA_SUBMISSION
    if flags["http"]:
        return TaskType.DATA_RETRIEVAL
    if flags["db"]:
        return TaskType.DATABASE
    if flags["file"]:
        return TaskType.FILE_OPS
    if flags["calc"]:
        return TaskType.CALCULATION
    if flags["summary"]:
        return TaskType.SUMMARIZATION
    return TaskType.UNKNOWN
