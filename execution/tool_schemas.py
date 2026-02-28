from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class HTTPGetArgs(BaseModel):
    url: str
    params: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_s: float = 2.0
    expect_json: bool = True
    allow_malformed: bool = False


class HTTPPostArgs(BaseModel):
    url: str
    json_body: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_s: float = 2.0
    expect_json: bool = True
    idempotency_key: str | None = None


class DBQueryArgs(BaseModel):
    sql: str
    params: list[Any] = Field(default_factory=list)
    readonly: bool = True
    limit: int | None = None


class FileWriteArgs(BaseModel):
    relative_path: str
    content: str
    overwrite: bool = False
    create_dirs: bool = True


class CalcArgs(BaseModel):
    expression: str

    @field_validator("expression", mode="before")
    @classmethod
    def coerce_expression(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError("expression must be a string")
        return value


class SummarizeArgs(BaseModel):
    text: str
    max_sentences: int = 3
    style: Literal["brief", "bullet"] = "brief"


class ToolResultBase(BaseModel):
    ok: bool = True
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class HTTPResult(ToolResultBase):
    status_code: int = 200
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any = None
    malformed: bool = False


class DBQueryResult(ToolResultBase):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0


class FileWriteResult(ToolResultBase):
    path: str
    bytes_written: int = 0


class CalcResult(ToolResultBase):
    result: float | int


class SummarizeResult(ToolResultBase):
    summary: str

