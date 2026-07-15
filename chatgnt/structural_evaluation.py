"""Derived structural evaluation for immutable generation records."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .identity import sha256_file
from .records import ContractError, canonical_line, strict_json_loads
from .validation import load_response_schema, validate_response


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = strict_json_loads(line)
        if not isinstance(value, dict):
            raise ContractError(f"{path}:{line_number}: expected object")
        values.append(value)
    return values


def evaluate_structure(run_dir: Path, output_dir: Path) -> dict[str, Any]:
    """Validate untouched raw outputs and write deterministic derived records."""

    if output_dir.exists():
        raise ContractError(f"evaluation output directory already exists: {output_dir}")
    responses_path = run_dir / "responses.jsonl"
    prompts_path = run_dir / "prompts.jsonl"
    records = _read_jsonl(responses_path)
    schema = load_response_schema()
    derived: list[dict[str, Any]] = []
    counts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "attempts": 0,
            "generation_completed": 0,
            "json_valid": 0,
            "schema_valid": 0,
            "failure_labels": Counter(),
        }
    )
    seen: set[tuple[str, int]] = set()

    for record in records:
        run_id = record.get("run_id")
        attempt_index = record.get("attempt_index")
        prompt_id = record.get("prompt_id")
        system_id = record.get("system_id")
        key = (str(run_id), attempt_index)
        if not isinstance(attempt_index, int) or key in seen:
            raise ContractError("response records require unique integer attempt indices")
        if not all(isinstance(item, str) and item for item in (run_id, prompt_id, system_id)):
            raise ContractError("response record identity is incomplete")
        seen.add(key)
        system = counts[system_id]
        system["attempts"] += 1
        raw_output = record.get("raw_output")
        completed = record.get("attempt_status") == "success" and isinstance(raw_output, str)
        validation = validate_response(raw_output, schema) if completed else None
        labels = validation["failure_labels"] if validation is not None else ["generation_failure"]
        if completed:
            system["generation_completed"] += 1
            system["json_valid"] += int(validation["json_valid"])
            system["schema_valid"] += int(validation["schema_valid"])
        system["failure_labels"].update(labels)
        derived.append(
            {
                "record_schema_version": 1,
                "source_run_id": run_id,
                "attempt_index": attempt_index,
                "prompt_id": prompt_id,
                "system_id": system_id,
                "generation_completed": completed,
                "source_raw_output_sha256": record.get("raw_output_sha256"),
                "validation": validation,
                "failure_labels": labels,
            }
        )

    summary = {
        "schema_version": 1,
        "kind": "derived-structural-evaluation",
        "source": {
            "run_id": records[0]["run_id"] if records else None,
            "responses_path": str(responses_path),
            "responses_sha256": sha256_file(responses_path),
            "prompts_sha256": sha256_file(prompts_path),
        },
        "response_schema_sha256": schema.sha256,
        "record_count": len(records),
        "systems": {
            system_id: {
                **{key: value for key, value in values.items() if key != "failure_labels"},
                "failure_labels": dict(sorted(values["failure_labels"].items())),
            }
            for system_id, values in sorted(counts.items())
        },
    }
    output_dir.mkdir(parents=True)
    (output_dir / "validations.jsonl").write_bytes(
        b"".join(canonical_line(record) for record in derived)
    )
    (output_dir / "summary.json").write_bytes(canonical_line(summary))
    return summary
