"""Verify the selected prompt and frozen inputs for the pinned confirmation run."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.development import validate_development_prompts
from chatgnt.identity import sha256_bytes
from chatgnt.prompting import (
    validate_development_b_v3_system_set,
    validate_five_shot_prompt_v3,
)
from chatgnt.records import ContractError, read_strict_json

RUN_PLAN = PROJECT_ROOT / "config" / "runs" / "development-b-v3-confirmation.json"
RUN_PLAN_SHA256 = "feb635d9de48a1cabc46b5185c9e1c42708df90f63a6001f57c91d7b7d0faa98"
EXPECTED_RUN_PLAN = {
    "schema_version": 1,
    "run_plan_id": "development-b-v3-confirmation",
    "prompt_set_path": "../../data/development/prompts-v1.jsonl",
    "system_set_path": "../systems/development-b-v3.json",
    "run_seed": 20260714,
    "primary_samples_per_system_prompt": 1,
}


def main() -> int:
    try:
        value, raw = read_strict_json(RUN_PLAN)
        if value != EXPECTED_RUN_PLAN or sha256_bytes(raw) != RUN_PLAN_SHA256:
            raise ContractError(f"{RUN_PLAN}: differs from frozen confirmation plan")
        result = {
            "result": "pass",
            "run_plan_id": value["run_plan_id"],
            "run_plan_sha256": RUN_PLAN_SHA256,
            "run_seed": value["run_seed"],
            "scheduled_attempt_count": 20,
            "development_prompts": validate_development_prompts(),
            "selected_prompt": validate_five_shot_prompt_v3(),
            "system_set": validate_development_b_v3_system_set(),
        }
    except (ContractError, OSError) as exc:
        print(json.dumps({"result": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
