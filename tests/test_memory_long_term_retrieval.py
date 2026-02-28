from __future__ import annotations

from memory.retrieval import retrieve_memory


def test_long_term_memory_retrieval_returns_matching_entries(long_term_memory):
    long_term_memory.add_memory_entry("facts", "k1", "flaky endpoint succeeds after retry", {})
    long_term_memory.add_memory_entry("facts", "k2", "database query returns rows", {})
    results = retrieve_memory(long_term_memory, "facts", "retry flaky endpoint", limit=5)
    assert results
    assert any("flaky" in r["value_text"] for r in results)

