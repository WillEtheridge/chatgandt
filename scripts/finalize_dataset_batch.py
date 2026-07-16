"""Dry-run or atomically terminalise one independently reviewed dataset batch."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.dataset import load_canonical_jsonl, load_dataset_contract
from chatgnt.dataset_terminalization import (
    DEFAULT_ACTOR_IDENTITY,
    terminalize_passing_reviews,
    utc_now_seconds,
    write_events_atomically,
)
from chatgnt.records import ContractError, canonical_json


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError(f"arguments: {message}")


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = _Parser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=PROJECT_ROOT / "config" / "dataset-v1.json")
    parser.add_argument("--recorded-at-utc")
    parser.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = _arguments(argv)
        candidates = load_canonical_jsonl(arguments.candidates)
        original_event_bytes = arguments.events.read_bytes()
        original_events = load_canonical_jsonl(arguments.events)
        recorded_at_utc = arguments.recorded_at_utc or max(
            utc_now_seconds(),
            max(event["recorded_at_utc"] for event in original_events),
        )
        result = terminalize_passing_reviews(
            candidates,
            original_events,
            load_dataset_contract(arguments.contract),
            recorded_at_utc=recorded_at_utc,
            actor_identity=DEFAULT_ACTOR_IDENTITY,
        )
        if arguments.write:
            write_events_atomically(arguments.events, result["events"], expected_existing_bytes=original_event_bytes)
            if load_canonical_jsonl(arguments.events) != result["events"]:
                raise ContractError("terminalization: written event file does not match the validated result")
        added = result["added_events"]
        report = {
            "result": "pass",
            "written": arguments.write,
            "accepted_count": len(added),
            "accepted_example_ids": result["accepted_example_ids"],
            "event_id_first": added[0]["event_id"] if added else None,
            "event_id_last": added[-1]["event_id"] if added else None,
            "lifecycle": result["validation_report"]["lifecycle"],
        }
    except ContractError as exc:
        print(canonical_json({"result": "fail", "error": str(exc)}), file=sys.stderr)
        return 2
    print(canonical_json(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
