"""Create and verify the first deterministic frozen ChatG&T dataset v1.2 bundle."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.dataset import (  # noqa: E402
    load_canonical_jsonl,
    load_dataset_contract,
    validate_frozen_dataset,
)
from chatgnt.dataset_split import (  # noqa: E402
    assign_dataset_splits,
    load_split_config,
    write_allocation,
)
from chatgnt.records import ContractError, canonical_json, canonical_line, read_strict_json  # noqa: E402
from scripts.audit_dataset_v1 import AMENDMENT_002_PATH, AMENDMENT_PATH, load_sources  # noqa: E402


DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "dataset-v1" / "frozen-v1.2"
AUDIT_PATH = PROJECT_ROOT / "data" / "dataset-v1" / "audit" / "findings-v1.2.json"
FROZEN_AT_UTC = "2026-07-16T17:30:00Z"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collection_sha256(records: list[dict[str, Any]]) -> str:
    return hashlib.sha256(b"".join(canonical_line(item) for item in records)).hexdigest()


def load_active_events(expected_sha256: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for batch in sorted((PROJECT_ROOT / "data" / "dataset-v1" / "authoring").glob("batch-*")):
        events.extend(load_canonical_jsonl(batch / "workflow-events.jsonl"))
    for amendment_path in (AMENDMENT_PATH, AMENDMENT_002_PATH):
        manifest, _ = read_strict_json(amendment_path)
        superseded_ids = {item["superseded_example_id"] for item in manifest["replacements"]}
        events = [item for item in events if item["example_id"] not in superseded_ids]
        events.extend(load_canonical_jsonl(PROJECT_ROOT / manifest["replacement_workflow_events_path"]))
    if collection_sha256(events) != expected_sha256:
        raise ContractError("active workflow-event identity differs from the passing audit")
    return events


def build_manifest(output: Path, result: dict[str, Any]) -> dict[str, Any]:
    files = []
    for name in (
        "candidates.jsonl", "workflow-events.jsonl", "train.jsonl",
        "validation.jsonl", "pilot.jsonl", "allocation-report.json",
    ):
        path = output / name
        entry: dict[str, Any] = {"path": name, "sha256": sha256(path)}
        if name.endswith(".jsonl"):
            entry["record_count"] = len(load_canonical_jsonl(path))
        files.append(entry)
    return {
        "schema_version": 1,
        "dataset_id": "chatgnt-dataset-v1.2",
        "status": "frozen",
        "frozen_at_utc": FROZEN_AT_UTC,
        "dataset_contract": {
            "path": "config/dataset-v1.json",
            "sha256": sha256(PROJECT_ROOT / "config" / "dataset-v1.json"),
        },
        "split_config": {
            "path": "config/dataset-split-v1.json",
            "sha256": sha256(PROJECT_ROOT / "config" / "dataset-split-v1.json"),
        },
        "amendments": [
            {"path": path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(path)}
            for path in (AMENDMENT_PATH, AMENDMENT_002_PATH)
        ],
        "passing_audit": {
            "path": AUDIT_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256(AUDIT_PATH),
        },
        "allocation": {
            "seed": result["report"]["seed"],
            "exact": result["report"]["allocation_exact"],
            "train": len(result["train"]),
            "validation": len(result["validation"]),
            "pilot": len(result["pilot"]),
        },
        "files": files,
    }


def freeze(output: Path) -> dict[str, Any]:
    candidates, _, _, identities = load_sources()
    events = load_active_events(identities["active_workflow_events_sha256"])
    if collection_sha256(candidates) != identities["active_candidates_sha256"]:
        raise ContractError("active candidate identity differs from the passing audit")

    contract = load_dataset_contract()
    result = assign_dataset_splits(candidates, events, contract, load_split_config())
    report = result["report"]
    if (
        report["allocation_exact"] is not True
        or report["split_deviation_required"] is not False
        or report["split_counts"] != {"train": 160, "validation": 40, "pilot": 40}
        or any(counts != {"train": 32, "validation": 8, "pilot": 8} for counts in report["per_intent_family"].values())
    ):
        raise ContractError("first deterministic allocation did not meet the exact frozen targets")

    validate_frozen_dataset(
        result["candidates"], result["events"], result["train"],
        result["validation"], result["pilot"], contract,
    )
    write_allocation(result, output)
    manifest = build_manifest(output, result)
    manifest_path = output / "dataset-manifest.json"
    manifest_path.write_bytes(canonical_line(manifest))
    if read_strict_json(manifest_path)[0] != manifest:
        raise ContractError("written dataset manifest did not round-trip")
    return {
        "result": "pass",
        "dataset_id": manifest["dataset_id"],
        "output": output.relative_to(PROJECT_ROOT).as_posix() if output.is_relative_to(PROJECT_ROOT) else str(output),
        "manifest_sha256": sha256(manifest_path),
        "split_counts": report["split_counts"],
        "per_intent_family": report["per_intent_family"],
        "validation_coverage": report["validation_coverage"],
        "pilot_coverage": report["pilot_coverage"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    try:
        result = freeze(arguments.output_dir.resolve())
    except (ContractError, OSError, RuntimeError, ValueError) as exc:
        print(canonical_json({"result": "fail", "error": str(exc)}), file=sys.stderr)
        return 1
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
