"""Deterministically terminalise independently reviewed dataset candidates."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from chatgnt.dataset import content_sha256, validate_authoring_dataset
from chatgnt.records import ContractError, canonical_line


EVENT_ID = re.compile(r"^dataset-event-v1-([0-9]{4})$")
DEFAULT_ACTOR_IDENTITY = "chatgnt-dataset-terminalizer-v1"


def utc_now_seconds() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def terminalize_passing_reviews(
    candidates: list[dict[str, Any]],
    events: list[dict[str, Any]],
    contract: dict[str, Any],
    *,
    recorded_at_utc: str,
    actor_identity: str = DEFAULT_ACTOR_IDENTITY,
) -> dict[str, Any]:
    """Return a validated event collection with every eligible pass accepted."""

    validate_authoring_dataset(candidates, events, contract)
    if not isinstance(actor_identity, str) or not actor_identity or actor_identity != actor_identity.strip():
        raise ContractError("terminalization actor identity must be a trimmed non-empty string")

    chains: dict[str, list[dict[str, Any]]] = defaultdict(list)
    maximum_event_number = 0
    for event in events:
        match = EVENT_ID.fullmatch(event["event_id"])
        if match is None:
            raise ContractError(f"terminalization: unsupported event ID {event['event_id']}")
        maximum_event_number = max(maximum_event_number, int(match.group(1)))
        chains[event["example_id"]].append(event)

    eligible: list[dict[str, Any]] = []
    blockers: list[str] = []
    for candidate in sorted(candidates, key=lambda item: item["example_id"]):
        chain = chains[candidate["example_id"]]
        latest = chain[-1]
        if latest["event_type"] in {"accepted", "rejected"}:
            continue
        if latest["event_type"] != "quality_review" or latest["outcome"] != "pass":
            blockers.append(candidate["example_id"])
        else:
            eligible.append(candidate)
    if blockers:
        raise ContractError(f"terminalization requires a passing final review for every unresolved candidate: {blockers}")
    if maximum_event_number + len(eligible) > 9999:
        raise ContractError("terminalization would exceed the version-1 event ID range")

    added: list[dict[str, Any]] = []
    for offset, candidate in enumerate(eligible, 1):
        latest = chains[candidate["example_id"]][-1]
        added.append({
            "record_schema_version": 1,
            "event_id": f"dataset-event-v1-{maximum_event_number + offset:04d}",
            "example_id": candidate["example_id"],
            "prior_event_id": latest["event_id"],
            "event_type": "accepted",
            "content_sha256": content_sha256(candidate),
            "actor_type": "automated_validator",
            "actor_identity": actor_identity,
            "model_id": None,
            "recorded_at_utc": recorded_at_utc,
            "outcome": "accepted",
            "reason_codes": [],
            "notes": "Terminalised automatically after an independent passing qualitative review and successful contract validation.",
        })

    result_events = [*events, *added]
    report = validate_authoring_dataset(candidates, result_events, contract)
    return {
        "events": result_events,
        "added_events": added,
        "accepted_example_ids": [item["example_id"] for item in added],
        "validation_report": report,
    }


def write_events_atomically(path: Path, events: list[dict[str, Any]], *, expected_existing_bytes: bytes) -> None:
    """Replace one canonical JSONL event file atomically in its own directory."""

    path = path.resolve()
    if path.read_bytes() != expected_existing_bytes:
        raise ContractError("terminalization: event file changed after validation")
    payload = b"".join(canonical_line(event) for event in events)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
