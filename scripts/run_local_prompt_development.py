"""Run one immutable local Ollama System B prompt version."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.local_development import run_local_prompt_version
from chatgnt.records import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-asset", type=Path, required=True)
    parser.add_argument("--prompts", type=Path, default=Path("data/development/prompts-v1.jsonl"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--model", default="qwen2.5:1.5b-instruct")
    args = parser.parse_args()
    print(canonical_json(run_local_prompt_version(args.prompt_asset, args.prompts, args.run_dir, args.model)))


if __name__ == "__main__":
    main()
