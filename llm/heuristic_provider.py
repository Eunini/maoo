from __future__ import annotations

import re
from typing import Any, Type

from pydantic import BaseModel

from core.config import Config
from core.types import PerceptionResult, Plan

from .provider import LLMProvider


class HeuristicProvider(LLMProvider):
    def __init__(self, config: Config) -> None:
        self.config = config

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        text = kwargs.get("text") or prompt
        max_sentences = int(kwargs.get("max_sentences", 3))
        sentences = re.split(r"(?<=[.!?])\s+", str(text).strip())
        sentences = [s for s in sentences if s]
        return " ".join(sentences[:max_sentences]) if sentences else ""

    def generate_structured(self, prompt: str, schema: Type[BaseModel], **kwargs: Any) -> BaseModel:
        if schema is PerceptionResult:
            return schema(
                intent="heuristic_perception",
                task_type="unknown",
                entities={"raw_prompt_excerpt": prompt[:120]},
                constraints=[],
                success_criteria=["produce final output"],
                initial_state={},
            )
        if schema is Plan:
            return schema(steps=[], planner_notes=["heuristic provider fallback"], max_steps=self.config.default_max_steps)
        return schema.model_validate(kwargs.get("data", {}))

