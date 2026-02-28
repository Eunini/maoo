from __future__ import annotations

from pathlib import Path

from core.config import load_config
from memory.long_term import LongTermMemory


def main() -> None:
    cfg = load_config()
    ltm = LongTermMemory(cfg.sqlite_path, schema_path=Path("sql/schema.sql"), seed_path=Path("sql/seed_data.sql"))
    ltm.add_memory_entry("facts", "seed:mock-api", "Mock API /data returns numbers [2,4,8] and sum 14", {"source": "script"})
    ltm.add_memory_entry("facts", "seed:flaky", "Flaky endpoint may fail once and succeed on retry", {"source": "script"})
    print("Seeded long-term memory.")


if __name__ == "__main__":
    main()

