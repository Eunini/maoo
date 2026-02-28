from __future__ import annotations

from memory.short_term import ShortTermMemory


def test_short_term_memory_tracks_retries_and_signatures():
    stm = ShortTermMemory({"x": 1})
    assert stm.retry_count("s1") == 0
    stm.mark_retry("s1")
    assert stm.retry_count("s1") == 1
    sig = stm.step_signature("calc", {"expression": "1+1"})
    stm.step_signature("calc", {"expression": "1+1"})
    assert stm.signature_count(sig) == 2

