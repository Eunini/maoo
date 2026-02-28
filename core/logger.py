from __future__ import annotations

import json
import sys
from pathlib import Path
from threading import Lock
from typing import Any

from .tracing import utc_now_iso


class StructuredLogger:
    def __init__(self, component: str = "app", context: dict[str, Any] | None = None, log_file: Path | None = None) -> None:
        self.component = component
        self.context = context or {}
        self.log_file = log_file
        self._lock = Lock()

    def child(self, component: str | None = None, **context: Any) -> "StructuredLogger":
        merged = {**self.context, **context}
        return StructuredLogger(component=component or self.component, context=merged, log_file=self.log_file)

    def _emit(self, level: str, event: str, message: str, **data: Any) -> None:
        payload = {
            "ts": utc_now_iso(),
            "level": level.upper(),
            "component": self.component,
            "event": event,
            "message": message,
            **self.context,
            "data": data or {},
        }
        line = json.dumps(payload, default=str)
        with self._lock:
            print(line, file=sys.stdout, flush=True)
            if self.log_file:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with self.log_file.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")

    def debug(self, event: str, message: str, **data: Any) -> None:
        self._emit("DEBUG", event, message, **data)

    def info(self, event: str, message: str, **data: Any) -> None:
        self._emit("INFO", event, message, **data)

    def warning(self, event: str, message: str, **data: Any) -> None:
        self._emit("WARNING", event, message, **data)

    def error(self, event: str, message: str, **data: Any) -> None:
        self._emit("ERROR", event, message, **data)


def get_logger(config: Any, component: str = "app", **context: Any) -> StructuredLogger:
    log_file = None
    if getattr(config, "log_to_file", False):
        log_file = Path(config.logs_dir) / "maoo.log"
    return StructuredLogger(component=component, context=context, log_file=log_file)

