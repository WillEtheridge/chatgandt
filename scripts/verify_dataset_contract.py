"""Read-only verification entry point for the dataset-v1 contract."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.dataset import (
    load_canonical_jsonl,
    load_dataset_contract,
    validate_authoring_dataset,
    validate_frozen_dataset,
    verify_dataset_contract,
)
from chatgnt.records import ContractError, canonical_json, canonical_line, read_strict_json


class _ContractParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError(f"arguments: {message}")


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = _ContractParser()
    parser.add_argument("--mode", choices=("contract", "authoring", "freeze"), required=True)
    parser.add_argument("--contract", type=Path, default=PROJECT_ROOT / "config" / "dataset-v1.json")
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--events", type=Path)
    parser.add_argument("--train", type=Path)
    parser.add_argument("--validation", type=Path)
    parser.add_argument("--pilot", type=Path)
    parser.add_argument("--split-deviation", type=Path)
    return parser.parse_args(argv)


def _require_mode_paths(arguments: argparse.Namespace) -> None:
    supplied = {name for name in ("candidates", "events", "train", "validation", "pilot", "split_deviation") if getattr(arguments, name) is not None}
    if arguments.mode == "contract":
        if supplied:
            raise ContractError(f"contract mode forbids dataset arguments: {sorted(supplied)}")
    elif arguments.mode == "authoring":
        missing = {"candidates", "events"} - supplied
        forbidden = supplied - {"candidates", "events"}
        if missing or forbidden:
            raise ContractError(f"authoring mode argument mismatch; missing={sorted(missing)}, forbidden={sorted(forbidden)}")
    else:
        missing = {"candidates", "events", "train", "validation", "pilot"} - supplied
        if missing:
            raise ContractError(f"freeze mode missing required arguments: {sorted(missing)}")


def _load_deviation(path: Path | None) -> dict | None:
    if path is None:
        return None
    try:
        value, raw = read_strict_json(path)
    except OSError as exc:
        raise ContractError(f"{path}: cannot read split deviation: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path}: split deviation must be one JSON object")
    if raw != canonical_line(value):
        raise ContractError(f"{path}: split deviation must be canonical JSON plus one terminal LF")
    return value


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = _arguments(argv)
        _require_mode_paths(arguments)
        if arguments.mode == "contract":
            report = verify_dataset_contract(arguments.contract)
        else:
            contract = load_dataset_contract(arguments.contract)
            candidates = load_canonical_jsonl(arguments.candidates)
            events = load_canonical_jsonl(arguments.events)
            if arguments.mode == "authoring":
                report = validate_authoring_dataset(candidates, events, contract)
            else:
                report = validate_frozen_dataset(
                    candidates, events,
                    load_canonical_jsonl(arguments.train),
                    load_canonical_jsonl(arguments.validation),
                    load_canonical_jsonl(arguments.pilot),
                    contract,
                    split_deviation=_load_deviation(arguments.split_deviation),
                )
    except ContractError as exc:
        print(canonical_json({"result": "fail", "error": str(exc)}), file=sys.stderr)
        return 2
    print(canonical_json(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
