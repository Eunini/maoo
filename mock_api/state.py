from __future__ import annotations

from collections import defaultdict


class MockState:
    def __init__(self) -> None:
        self.counters: dict[str, int] = defaultdict(int)

    def bump(self, key: str) -> int:
        self.counters[key] += 1
        return self.counters[key]

    def get(self, key: str) -> int:
        return self.counters.get(key, 0)

    def reset(self) -> None:
        self.counters.clear()


STATE = MockState()

