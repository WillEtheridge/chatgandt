"""Summarize and select local System B prompt versions."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.prompt_development_analysis import summarize_prompt_versions
from chatgnt.records import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="append",
        nargs=5,
        metavar=("VERSION", "SCORING_SOURCE", "RUN_DIR", "STRUCTURE_DIR", "SCORING_DIR"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    versions = [
        (version, source, Path(run), Path(structure), Path(scoring))
        for version, source, run, structure, scoring in args.version
    ]
    print(canonical_json(summarize_prompt_versions(versions, args.output)))


if __name__ == "__main__":
    main()
