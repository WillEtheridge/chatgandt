"""Dry-run or atomically write deterministic dataset-v1 split allocation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.dataset import load_canonical_jsonl, load_dataset_contract
from chatgnt.dataset_split import assign_dataset_splits, load_split_config, verify_split_config, write_allocation
from chatgnt.records import ContractError, canonical_json


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError(f"arguments: {message}")


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = _Parser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--events", type=Path)
    parser.add_argument("--contract", type=Path, default=PROJECT_ROOT / "config" / "dataset-v1.json")
    parser.add_argument("--split-config", type=Path, default=PROJECT_ROOT / "config" / "dataset-split-v1.json")
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = _arguments(argv)
        if arguments.check_config:
            if arguments.candidates is not None or arguments.events is not None or arguments.output_dir is not None:
                raise ContractError("arguments: --check-config forbids dataset and output paths")
            report = verify_split_config(arguments.split_config, arguments.contract)
        else:
            if arguments.candidates is None or arguments.events is None:
                raise ContractError("arguments: allocation requires --candidates and --events")
            contract = load_dataset_contract(arguments.contract)
            split_config = load_split_config(arguments.split_config)
            result = assign_dataset_splits(
                load_canonical_jsonl(arguments.candidates),
                load_canonical_jsonl(arguments.events),
                contract,
                split_config,
            )
            if arguments.output_dir is not None:
                write_allocation(result, arguments.output_dir)
            report = result["report"]
    except ContractError as exc:
        print(canonical_json({"result": "fail", "error": str(exc)}), file=sys.stderr)
        return 2
    print(canonical_json(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
