from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FaultMode(str, Enum):
    NONE = "none"
    FLAKY = "flaky"
    SLOW = "slow"
    MALFORMED = "malformed"


class SubmitPayload(BaseModel):
    message: str = "hello"
    metadata: dict[str, Any] = Field(default_factory=dict)

