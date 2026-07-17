"""Run one frozen Stage 6 second-round full-corpus candidate."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_pilot_training import execute  # noqa: E402


CANDIDATE_CONFIGS = {
    "4": ROOT / "config" / "full-training-candidate-4-v1.toml",
    "5": ROOT / "config" / "full-training-candidate-5-v1.toml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=(*CANDIDATE_CONFIGS, "all"), required=True)
    parser.add_argument("--check-inputs", action="store_true",
                        help="Validate and tokenize inputs without CUDA or output files.")
    parser.add_argument("--run-id", help="Unique immutable run directory name; required for GPU execution.")
    parser.add_argument("--hourly-price-usd", type=float, help="Displayed compute price for cost estimation.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.candidate == "all":
        if not args.check_inputs or args.run_id is not None or args.hourly_price_usd is not None:
            raise ValueError("--candidate all is permitted only with --check-inputs and no execution arguments")
        for candidate, config_path in CANDIDATE_CONFIGS.items():
            print(f"=== Candidate {candidate} ===")
            execute(args, config_path, "second-round full training")
        return
    execute(args, CANDIDATE_CONFIGS[args.candidate], "second-round full training")


if __name__ == "__main__":
    main()
