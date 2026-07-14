"""Verify the frozen System A/B development mapping."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.prompting import validate_development_ab_system_set
from chatgnt.records import ContractError


def main() -> int:
    try:
        result = validate_development_ab_system_set()
    except (ContractError, OSError) as exc:
        print(json.dumps({"result": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
