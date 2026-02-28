from __future__ import annotations

import time

from .state import STATE


def flaky_should_fail(key: str, fail_first: int = 1) -> bool:
    count = STATE.bump(f"flaky:{key}")
    return count <= fail_first


def slow_sleep(delay_ms: int) -> None:
    if delay_ms > 0:
        time.sleep(delay_ms / 1000.0)

