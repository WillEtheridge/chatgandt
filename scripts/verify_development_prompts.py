"""Verify the frozen ChatG&T prompt-development set."""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Direct script execution places ``scripts/`` rather than the repository root on
# ``sys.path``. Keep this verifier usable with the same command style as the
# project's other verification scripts.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.development import validate_development_prompts
from chatgnt.records import ContractError


def main() -> int:
    try:
        result = validate_development_prompts()
    except (ContractError, OSError) as exc:
        print(json.dumps({"result": "fail", "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
