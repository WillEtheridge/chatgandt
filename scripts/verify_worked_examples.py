"""Verify the frozen ChatG&T five-shot worked examples."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.development import validate_worked_examples
from chatgnt.records import ContractError


def main() -> int:
    try:
        result = validate_worked_examples()
    except (ContractError, OSError) as exc:
        print(json.dumps({"result": "fail", "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
