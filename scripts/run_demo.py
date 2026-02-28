from __future__ import annotations

import sys

from main import run_orchestration


DEMO_REQUESTS = {
    "happy": "Fetch mock data, calculate 2 + 2, summarize the result, and write a file",
    "refinement": "Fetch flaky endpoint and summarize the result after retry flaky",
    "stop": "Fetch URL http://127.0.0.1:8001/flaky?fail_first=10&key=loop and summarize for malformed safe exit",
}


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "happy"
    if name not in DEMO_REQUESTS:
        raise SystemExit(f"Unknown demo '{name}'. Choose from: {', '.join(sorted(DEMO_REQUESTS))}")
    trace, _ = run_orchestration(DEMO_REQUESTS[name], context={"demo": name})
    print(trace.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

