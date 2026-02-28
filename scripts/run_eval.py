from __future__ import annotations

from eval.runner import run_scenarios


def main() -> None:
    summary = run_scenarios("eval/scenarios.json", "runtime/traces")
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

