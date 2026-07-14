"""Verify the frozen 40-attempt System A/B development schedule."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.development_run import validate_development_schedule
from chatgnt.records import ContractError


def main() -> int:
    try:
        result = validate_development_schedule()
    except (ContractError, OSError) as exc:
        print(json.dumps({"result": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
