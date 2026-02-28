from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type

from pydantic import BaseModel

from core.config import Config


class LLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_structured(self, prompt: str, schema: Type[BaseModel], **kwargs: Any) -> BaseModel:
        raise NotImplementedError


def get_provider(config: Config) -> LLMProvider:
    if config.no_llm_mode or not config.openai_api_key:
        from .heuristic_provider import HeuristicProvider

        return HeuristicProvider(config=config)
    from .openai_compatible import OpenAICompatibleProvider

    return OpenAICompatibleProvider(config=config)

