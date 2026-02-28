from __future__ import annotations

import json
from typing import Any, Type

import httpx
from pydantic import BaseModel

from core.config import Config

from .provider import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, config: Config) -> None:
        self.config = config
        if not config.openai_base_url or not config.openai_api_key:
            raise ValueError("OpenAI-compatible provider requires base URL and API key")

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        payload = {
            "model": self.config.openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0),
        }
        url = self.config.openai_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.config.openai_api_key}"}
        with httpx.Client(timeout=kwargs.get("timeout", 30)) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def generate_structured(self, prompt: str, schema: Type[BaseModel], **kwargs: Any) -> BaseModel:
        text = self.generate_text(prompt, **kwargs)
        try:
            return schema.model_validate_json(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return schema.model_validate(json.loads(text[start : end + 1]))
            raise

