"""Apply the frozen Stage 6 second-round viability and ranking rule."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.records import canonical_json  # noqa: E402
from scripts.select_training_candidate import select_candidate  # noqa: E402


SIMPLICITY_ORDER = ("candidate-4", "candidate-5")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", nargs=3, required=True,
                        metavar=("LABEL", "RUN_DIR", "EVALUATION_DIR"))
    parser.add_argument("--scoring-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = [(label, Path(run), Path(evaluation)) for label, run, evaluation in args.source]
    result = select_candidate(
        sources, args.scoring_dir, args.output,
        simplicity_order=SIMPLICITY_ORDER,
        kind="full-training-second-round-candidate-selection",
        simplicity_rule_label="simplicity_candidate_4_to_5",
    )
    print(canonical_json(result))


if __name__ == "__main__":
    main()
