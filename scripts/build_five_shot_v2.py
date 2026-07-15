"""Build or verify the deterministic five-shot prompt v2 asset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.prompting import FIVE_SHOT_PROMPT_V2, expected_five_shot_asset_v2
from chatgnt.records import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    expected = expected_five_shot_asset_v2()
    rendered = json.dumps(expected, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.write:
        if FIVE_SHOT_PROMPT_V2.exists():
            raise SystemExit(f"refusing to overwrite {FIVE_SHOT_PROMPT_V2}")
        FIVE_SHOT_PROMPT_V2.write_text(rendered, encoding="utf-8")
        print(canonical_json({"result": "written", "path": str(FIVE_SHOT_PROMPT_V2)}))
        return
    if not FIVE_SHOT_PROMPT_V2.exists() or FIVE_SHOT_PROMPT_V2.read_text(encoding="utf-8") != rendered:
        raise SystemExit("five-shot-v2 asset is missing or differs from deterministic rendering")
    print(canonical_json({"result": "pass", "path": str(FIVE_SHOT_PROMPT_V2)}))


if __name__ == "__main__":
    main()
