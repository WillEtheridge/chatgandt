"""Verify System B prompt v1 and optionally measure pinned-tokenizer cost."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.configuration import EXPECTED_MODEL, load_prompt_asset, load_prompts
from chatgnt.development import DEVELOPMENT_PROMPTS_V1
from chatgnt.prompting import FIVE_SHOT_PROMPT_V1, validate_five_shot_prompt
from chatgnt.records import ContractError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--measure-tokens",
        action="store_true",
        help="Load the pinned local tokenizer and measure full rendered inputs.",
    )
    return parser.parse_args()


def measure_tokens() -> dict:
    from transformers import AutoTokenizer

    model = EXPECTED_MODEL["base_model"]
    snapshot = (
        PROJECT_ROOT
        / "artifacts"
        / "models"
        / model["id"].replace("/", "--")
        / model["revision"]
    )
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    asset = load_prompt_asset(FIVE_SHOT_PROMPT_V1)
    prompts, _ = load_prompts(DEVELOPMENT_PROMPTS_V1)

    empty_counts = []
    five_shot_counts = []
    overheads = []
    for prompt in prompts:
        empty = tokenizer.apply_chat_template(
            [{"role": "system", "content": ""}, {"role": "user", "content": prompt.prompt}],
            tokenize=True,
            add_generation_prompt=True,
        )
        five_shot = tokenizer.apply_chat_template(
            [{"role": "system", "content": asset.content}, {"role": "user", "content": prompt.prompt}],
            tokenize=True,
            add_generation_prompt=True,
        )
        empty_count = len(empty["input_ids"])
        five_shot_count = len(five_shot["input_ids"])
        empty_counts.append(empty_count)
        five_shot_counts.append(five_shot_count)
        overheads.append(five_shot_count - empty_count)

    max_context = model["max_context_tokens"]
    generation_allowance = 512
    return {
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_length": len(tokenizer),
        "development_prompt_count": len(prompts),
        "system_content_tokens_non_additive": len(
            tokenizer(asset.content, add_special_tokens=False)["input_ids"]
        ),
        "complete_empty_system_input_tokens": {
            "minimum": min(empty_counts),
            "maximum": max(empty_counts),
            "mean": round(statistics.mean(empty_counts), 2),
        },
        "complete_five_shot_input_tokens": {
            "minimum": min(five_shot_counts),
            "maximum": max(five_shot_counts),
            "mean": round(statistics.mean(five_shot_counts), 2),
        },
        "paired_five_shot_overhead_tokens": {
            "minimum": min(overheads),
            "maximum": max(overheads),
            "mean": round(statistics.mean(overheads), 2),
            "unique_values": sorted(set(overheads)),
        },
        "pinned_context_tokens": max_context,
        "generation_allowance_tokens": generation_allowance,
        "minimum_context_headroom_tokens": max_context - max(five_shot_counts) - generation_allowance,
        "all_inputs_fit_without_truncation": max(five_shot_counts) + generation_allowance <= max_context,
    }


def main() -> int:
    args = parse_args()
    try:
        result = validate_five_shot_prompt()
        if args.measure_tokens:
            result["token_measurement"] = measure_tokens()
    except (ContractError, OSError, ValueError) as exc:
        print(json.dumps({"result": "fail", "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
