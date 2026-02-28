from __future__ import annotations

from typing import Any

from core.types import TaskType


def build_state(
    raw_goal: str,
    task_type: TaskType,
    entities: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    constraints = ["use allowlisted tools only", "no destructive actions"]
    success_criteria: list[str] = []
    initial_state = {"raw_goal": raw_goal, "context": context or {}, "task_type": task_type.value}
    lower = raw_goal.lower()

    http_requested = bool(
        entities.get("url")
        or entities.get("external_url")
        or entities.get("endpoint_mode")
        or any(t in lower for t in ["fetch", "get", "post", "submit", "http"])
    )
    if http_requested or task_type in {TaskType.DATA_RETRIEVAL, TaskType.DATA_SUBMISSION}:
        success_criteria.append("http result captured")
    if entities.get("db_requested") or task_type == TaskType.DATABASE:
        success_criteria.append("db result captured")
    if entities.get("calc_requested") or task_type == TaskType.CALCULATION:
        success_criteria.append("calculation result available")
    if entities.get("write_requested") or task_type == TaskType.FILE_OPS:
        success_criteria.append("file write acknowledged")
    if entities.get("summarize_requested") or task_type == TaskType.SUMMARIZATION:
        success_criteria.append("summary produced")
    if not success_criteria:
        success_criteria.append("produce final output")

    if "strict json" in raw_goal.lower():
        constraints.append("expect structured json responses")
    if "safe exit" in raw_goal.lower():
        constraints.append("stop safely on repeated failures")

    initial_state["entities"] = entities
    return constraints, success_criteria, initial_state
