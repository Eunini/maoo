from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

ToolHandler = Callable[[BaseModel, Any], BaseModel]


def tool_ok(model_cls: type[BaseModel], **kwargs: Any) -> BaseModel:
    return model_cls(ok=True, **kwargs)

