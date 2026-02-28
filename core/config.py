from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _parse_float(value: str | None, default: float) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _parse_list(value: str | None, default: list[str]) -> list[str]:
    if value is None or value.strip() == "":
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Config(BaseModel):
    app_name: str = "MAOO"
    env: str = "dev"
    log_level: str = "INFO"
    log_to_file: bool = True

    runtime_dir: Path = Path("runtime")
    logs_dir: Path = Path("runtime/logs")
    traces_dir: Path = Path("runtime/traces")
    workspace_dir: Path = Path("runtime/workspace")
    sqlite_dir: Path = Path("runtime/sqlite")
    sqlite_path: Path = Path("runtime/sqlite/maoo.db")
    file_workspace_root: Path = Path("runtime/workspace")

    no_llm_mode: bool = True
    openai_base_url: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    enable_real_http: bool = False
    allowed_http_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "mock-api"])
    mock_api_base_url: str = "http://127.0.0.1:8001"

    default_http_timeout_s: float = 2.0
    default_max_steps: int = 12
    default_max_retries_per_step: int = 2
    default_budget_units: int = 50
    non_progress_threshold: int = 3
    random_seed: int = 42

    enable_db_writes: bool = False

    @classmethod
    def from_env(cls, overrides: dict[str, Any] | None = None) -> "Config":
        load_dotenv(override=False)
        runtime_dir = Path(os.getenv("MAOO_RUNTIME_DIR", "runtime"))
        workspace_dir = Path(os.getenv("MAOO_FILE_WORKSPACE_ROOT", str(runtime_dir / "workspace")))
        sqlite_path = Path(os.getenv("MAOO_SQLITE_PATH", str(runtime_dir / "sqlite" / "maoo.db")))
        data = {
            "app_name": os.getenv("MAOO_APP_NAME", "MAOO"),
            "env": os.getenv("MAOO_ENV", "dev"),
            "log_level": os.getenv("MAOO_LOG_LEVEL", "INFO"),
            "log_to_file": _parse_bool(os.getenv("MAOO_LOG_TO_FILE"), True),
            "runtime_dir": runtime_dir,
            "logs_dir": runtime_dir / "logs",
            "traces_dir": runtime_dir / "traces",
            "workspace_dir": runtime_dir / "workspace",
            "sqlite_dir": runtime_dir / "sqlite",
            "sqlite_path": sqlite_path,
            "file_workspace_root": workspace_dir,
            "no_llm_mode": _parse_bool(os.getenv("MAOO_NO_LLM_MODE"), True),
            "openai_base_url": os.getenv("MAOO_OPENAI_BASE_URL") or None,
            "openai_api_key": os.getenv("MAOO_OPENAI_API_KEY") or None,
            "openai_model": os.getenv("MAOO_OPENAI_MODEL", "gpt-4o-mini"),
            "enable_real_http": _parse_bool(os.getenv("MAOO_ENABLE_REAL_HTTP"), False),
            "allowed_http_hosts": _parse_list(
                os.getenv("MAOO_ALLOWED_HTTP_HOSTS"),
                ["localhost", "127.0.0.1", "mock-api"],
            ),
            "mock_api_base_url": os.getenv("MAOO_MOCK_API_BASE_URL", "http://127.0.0.1:8001"),
            "default_http_timeout_s": _parse_float(os.getenv("MAOO_DEFAULT_HTTP_TIMEOUT_S"), 2.0),
            "default_max_steps": _parse_int(os.getenv("MAOO_DEFAULT_MAX_STEPS"), 12),
            "default_max_retries_per_step": _parse_int(os.getenv("MAOO_DEFAULT_MAX_RETRIES_PER_STEP"), 2),
            "default_budget_units": _parse_int(os.getenv("MAOO_DEFAULT_BUDGET_UNITS"), 50),
            "non_progress_threshold": _parse_int(os.getenv("MAOO_NON_PROGRESS_THRESHOLD"), 3),
            "random_seed": _parse_int(os.getenv("MAOO_RANDOM_SEED"), 42),
            "enable_db_writes": _parse_bool(os.getenv("MAOO_ENABLE_DB_WRITES"), False),
        }
        if overrides:
            for key, value in overrides.items():
                if key in {"sqlite_path", "runtime_dir", "logs_dir", "traces_dir", "workspace_dir", "sqlite_dir", "file_workspace_root"}:
                    data[key] = Path(value)
                else:
                    data[key] = value
        cfg = cls(**data)
        cfg.ensure_runtime_dirs()
        return cfg

    def ensure_runtime_dirs(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_dir.mkdir(parents=True, exist_ok=True)
        self.file_workspace_root.mkdir(parents=True, exist_ok=True)


def load_config(overrides: dict[str, Any] | None = None) -> Config:
    return Config.from_env(overrides)

