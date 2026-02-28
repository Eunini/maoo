from __future__ import annotations

from collections import Counter
from typing import Any


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()

    @staticmethod
    def _key(name: str, labels: dict[str, Any] | None = None) -> str:
        if not labels:
            return name
        parts = ",".join(f"{k}={labels[k]}" for k in sorted(labels))
        return f"{name}|{parts}"

    def inc(self, name: str, value: int = 1, labels: dict[str, Any] | None = None) -> None:
        self._counters[self._key(name, labels)] += value

    def snapshot(self) -> dict[str, int]:
        return dict(self._counters)

    def reset(self) -> None:
        self._counters.clear()

