"""Prepare blinded qualitative-scoring packets from structural evaluations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.blind_scoring import prepare_blind_packets, reveal_and_summarize_scores
from chatgnt.records import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reveal", action="store_true")
    parser.add_argument(
        "--source",
        action="append",
        nargs=3,
        metavar=("LABEL", "RUN_DIR", "EVALUATION_DIR"),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--scoring-dir", type=Path)
    parser.add_argument("--judge-seed", type=int, default=20260715)
    args = parser.parse_args()
    if args.reveal:
        if args.scoring_dir is None or args.source or args.output_dir is not None:
            parser.error("--reveal requires only --scoring-dir")
        print(canonical_json(reveal_and_summarize_scores(args.scoring_dir)))
        return
    if not args.source or args.output_dir is None or args.scoring_dir is not None:
        parser.error("packet preparation requires --source and --output-dir")
    sources = [(label, Path(run), Path(evaluation)) for label, run, evaluation in args.source]
    print(canonical_json(prepare_blind_packets(sources, args.output_dir, args.judge_seed)))


if __name__ == "__main__":
    main()
