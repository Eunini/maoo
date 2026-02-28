from __future__ import annotations

from typing import Any

from core.types import PerceptionResult
from llm.provider import LLMProvider
from memory.long_term import LongTermMemory
from memory.retrieval import retrieve_memory

from .intent_extractor import extract_intent_and_entities
from .state_builder import build_state
from .task_classifier import classify_task


class PerceptionAgent:
    def __init__(self, llm_provider: LLMProvider, long_term_memory: LongTermMemory | None = None) -> None:
        self.llm_provider = llm_provider
        self.long_term_memory = long_term_memory

    def run(self, raw_goal: str, context: dict[str, Any] | None = None) -> PerceptionResult:
        intent, entities = extract_intent_and_entities(raw_goal, context)
        task_type = classify_task(raw_goal)
        constraints, success_criteria, initial_state = build_state(raw_goal, task_type, entities, context)

        if self.long_term_memory:
            recalled = retrieve_memory(self.long_term_memory, namespace="facts", query=raw_goal, limit=3)
            if recalled:
                initial_state["retrieved_memory"] = [
                    {"key": row.get("key"), "value_text": row.get("value_text")} for row in recalled
                ]

        return PerceptionResult(
            intent=intent,
            task_type=task_type,
            entities=entities,
            constraints=constraints,
            success_criteria=success_criteria,
            initial_state=initial_state,
        )

