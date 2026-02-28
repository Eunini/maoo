from __future__ import annotations

import json
from typing import Any


def pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)

