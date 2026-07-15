"""Apply frozen structural validation to an immutable generation run."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.records import canonical_json
from chatgnt.structural_evaluation import evaluate_structure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(canonical_json(evaluate_structure(args.run_dir, args.output_dir)))


if __name__ == "__main__":
    main()
