"""Executable contract for ChatG&T supervised dataset v1."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tomllib
from typing import Any, Literal

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from chatgnt.evaluation_protocol import INTENT_FAMILIES, WITHHELD_DOMAINS, normalize_text
from chatgnt.records import ContractError, canonical_json, canonical_line, read_strict_json, strict_json_loads


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = PROJECT_ROOT / "config" / "dataset-v1.json"
ValidationMode = Literal["authoring", "freeze"]


def _path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _collection_bytes(records: list[dict[str, Any]]) -> bytes:
    return b"".join(canonical_line(record) for record in records)


def _collection_digest(records: list[dict[str, Any]]) -> str:
    return _digest_bytes(_collection_bytes(records))


def _load_canonical_object(path: Path) -> dict[str, Any]:
    value, raw = read_strict_json(path)
    if not isinstance(value, dict):
        raise ContractError(f"{path}: expected one JSON object")
    if raw != canonical_line(value):
        raise ContractError(f"{path}: expected canonical JSON plus one terminal LF")
    return value


def load_dataset_contract(path: str | Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    """Load the canonical version-1 dataset contract configuration."""

    resolved = _path(path)
    try:
        return _load_canonical_object(resolved)
    except OSError as exc:
        raise ContractError(f"{resolved}: cannot read dataset contract: {exc}") from exc


def load_canonical_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load strict LF-delimited canonical JSON objects with contextual errors."""

    resolved = Path(path)
    try:
        raw = resolved.read_bytes()
    except OSError as exc:
        raise ContractError(f"{resolved}: cannot read JSONL: {exc}") from exc
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContractError(f"{resolved}:1: UTF-8 byte-order marks are not permitted")
    if b"\r" in raw:
        line = raw[: raw.index(b"\r")].count(b"\n") + 1
        raise ContractError(f"{resolved}:{line}: CR and CRLF line endings are not permitted")
    if raw and not raw.endswith(b"\n"):
        raise ContractError(f"{resolved}:{raw.count(b'\n') + 1}: line must end with LF")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        line = raw[: exc.start].count(b"\n") + 1
        raise ContractError(f"{resolved}:{line}: invalid UTF-8: {exc}") from exc
    records: list[dict[str, Any]] = []
    lines = text.splitlines()
    for line_number, line in enumerate(lines, 1):
        if not line:
            raise ContractError(f"{resolved}:{line_number}: blank lines are not permitted")
        try:
            value = strict_json_loads(line)
        except ContractError as exc:
            raise ContractError(f"{resolved}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ContractError(f"{resolved}:{line_number}: expected JSON object")
        if (line + "\n").encode("utf-8") != canonical_line(value):
            raise ContractError(f"{resolved}:{line_number}: line is not canonical JSON")
        records.append(value)
    return records


def content_sha256(example: dict[str, Any]) -> str:
    """Return the authored-content identity, excluding allocation-only fields."""

    if not isinstance(example, dict):
        raise ContractError("example: expected object")
    content = {key: value for key, value in example.items() if key not in {"split", "pilot_member"}}
    return _digest_bytes(canonical_json(content).encode("utf-8"))


def _schema(contract: dict[str, Any], name: str) -> dict[str, Any]:
    path = _path(contract["schema_paths"][name])
    try:
        value, _ = read_strict_json(path)
    except OSError as exc:
        raise ContractError(f"{path}: cannot read schema: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path}: schema must be an object")
    return value


def _validator(contract: dict[str, Any], name: str) -> Draft202012Validator:
    schema = _schema(contract, name)
    response = _schema(contract, "response")
    registry = Registry().with_resource(response["$id"], Resource.from_contents(response))
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def _validate_schema_instance(value: Any, contract: dict[str, Any], name: str, location: str) -> None:
    errors = sorted(_validator(contract, name).iter_errors(value), key=lambda error: list(error.absolute_path))
    if errors:
        error = errors[0]
        suffix = "".join(f"[{item}]" if isinstance(item, int) else f".{item}" for item in error.absolute_path)
        raise ContractError(f"{location}{suffix}: {error.message}")


def _require_trimmed(value: Any, location: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{location}: expected string")
    if value != value.strip():
        raise ContractError(f"{location}: leading or trailing whitespace is not permitted")
    if not allow_empty and not value:
        raise ContractError(f"{location}: must be non-empty")
    return value


def _model_id_prohibited(value: str, contract: dict[str, Any]) -> bool:
    candidate = value.casefold()
    component = value.rstrip("/").rsplit("/", 1)[-1].casefold()
    prohibited = set(contract["prohibited_model_assistance_ids"])
    prohibited.add(contract["model"]["base_model_id"])
    for item in prohibited:
        target = item.casefold()
        target_component = item.rstrip("/").rsplit("/", 1)[-1].casefold()
        if candidate in {target, target_component} or component in {target, target_component}:
            return True
    return False


def validate_example(example: dict[str, Any], contract: dict[str, Any], *, mode: ValidationMode) -> None:
    """Validate one semantic record and all version-1 cross-field invariants."""

    if mode not in ("authoring", "freeze"):
        raise ContractError(f"example: invalid validation mode {mode!r}")
    _validate_schema_instance(example, contract, "supervised_example", "example")
    _require_trimmed(example["user_prompt"], "example.user_prompt")
    metadata = example["metadata"]
    for key in ("user_goal", "requested_task_or_artefact", "scenario_summary"):
        _require_trimmed(metadata[key], f"example.metadata.{key}")
    for index, item in enumerate(metadata["important_constraints"]):
        _require_trimmed(item, f"example.metadata.important_constraints[{index}]")
    response = example["assistant_response"]
    _require_trimmed(response["title"], "example.assistant_response.title")
    _require_trimmed(response["garnish"], "example.assistant_response.garnish")
    for index, item in enumerate(response["ingredients"]):
        _require_trimmed(item["unit"], f"example.assistant_response.ingredients[{index}].unit")
        _require_trimmed(item["name"], f"example.assistant_response.ingredients[{index}].name")
    for index, item in enumerate(response["method"]):
        _require_trimmed(item, f"example.assistant_response.method[{index}]")
    provenance = example["provenance"]
    if provenance["initial_draft_source"] == "frontier_model":
        model_id = _require_trimmed(provenance["initial_draft_model_id"], "example.provenance.initial_draft_model_id")
        if _model_id_prohibited(model_id, contract):
            raise ContractError("example.provenance.initial_draft_model_id: pinned target model is prohibited")
    family = metadata["intent_family"]
    if metadata["task_subtype"] not in contract["registries"]["task_subtypes_by_family"][family]:
        raise ContractError("example.metadata.task_subtype: not permitted for intent family")


def _parse_utc(value: str, location: str) -> datetime:
    if not value.endswith("Z"):
        raise ContractError(f"{location}: must be an explicit UTC Z timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ContractError(f"{location}: invalid RFC 3339 timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ContractError(f"{location}: must be UTC")
    return parsed


def validate_workflow_event(event: dict[str, Any], contract: dict[str, Any]) -> None:
    """Validate one workflow event independently of chain position."""

    _validate_schema_instance(event, contract, "workflow_event", "event")
    _require_trimmed(event["actor_identity"], "event.actor_identity")
    if event["model_id"] is not None:
        model_id = _require_trimmed(event["model_id"], "event.model_id")
        if _model_id_prohibited(model_id, contract):
            raise ContractError("event.model_id: pinned target model is prohibited")
    _parse_utc(event["recorded_at_utc"], "event.recorded_at_utc")
    _require_trimmed(event["notes"], "event.notes", allow_empty=True)
    reasons = event["reason_codes"]
    outcome = event["outcome"]
    no_reason_outcomes = {"created", "revised", "pass", "accepted"}
    reason_outcomes = {"revision_requested", "rejection_recommended", "rejected"}
    if outcome in no_reason_outcomes and reasons:
        raise ContractError(f"event.reason_codes: outcome {outcome} requires no reason codes")
    if outcome in reason_outcomes and not reasons:
        raise ContractError(f"event.reason_codes: outcome {outcome} requires at least one reason code")
    if reasons and not event["notes"]:
        raise ContractError("event.notes: reason codes require non-empty notes")


def _validate_chain(example: dict[str, Any], chain: list[dict[str, Any]], contract: dict[str, Any]) -> str:
    if not chain:
        raise ContractError(f"workflow {example['example_id']}: missing event chain")
    terminal_seen = False
    previous: dict[str, Any] | None = None
    for index, event in enumerate(chain):
        if event["example_id"] != example["example_id"]:
            raise ContractError(f"workflow {example['example_id']}: cross-example event")
        expected_prior = None if previous is None else previous["event_id"]
        if event["prior_event_id"] != expected_prior:
            raise ContractError(f"workflow {example['example_id']}: event {event['event_id']} does not identify the immediately preceding event")
        if terminal_seen:
            raise ContractError(f"workflow {example['example_id']}: event after terminal disposition")
        if previous is not None:
            earlier = _parse_utc(previous["recorded_at_utc"], "event.recorded_at_utc")
            current = _parse_utc(event["recorded_at_utc"], "event.recorded_at_utc")
            if current < earlier:
                raise ContractError(f"workflow {example['example_id']}: event time reversal")
            changed = event["content_sha256"] != previous["content_sha256"]
            if event["event_type"] in {"model_revision", "human_edit"} and not changed:
                raise ContractError(f"workflow {example['example_id']}: revision event must change content digest")
            if event["event_type"] in {"quality_review", "accepted", "rejected"} and changed:
                raise ContractError(f"workflow {example['example_id']}: review and terminal events must preserve content digest")
        if event["event_type"] == "accepted":
            if previous is None or previous["event_type"] != "quality_review" or previous["outcome"] != "pass":
                raise ContractError(f"workflow {example['example_id']}: acceptance must immediately follow a passing quality review")
        if event["event_type"] in {"accepted", "rejected"}:
            terminal_seen = True
        previous = event
    if chain[-1]["content_sha256"] != content_sha256(example):
        raise ContractError(f"workflow {example['example_id']}: latest event content digest does not match candidate")
    first = chain[0]
    provenance = example["provenance"]
    if first["event_type"] != "draft_created":
        raise ContractError(f"workflow {example['example_id']}: first event must be draft_created")
    if first["actor_type"] != provenance["initial_draft_source"]:
        raise ContractError(f"workflow {example['example_id']}: initial actor disagrees with provenance")
    if first["model_id"] != provenance["initial_draft_model_id"]:
        raise ContractError(f"workflow {example['example_id']}: initial model ID disagrees with provenance")
    if provenance["model_revision_used"] != any(item["event_type"] == "model_revision" for item in chain):
        raise ContractError(f"workflow {example['example_id']}: model revision summary disagrees with event chain")
    if provenance["material_human_edit"] != any(item["event_type"] == "human_edit" for item in chain):
        raise ContractError(f"workflow {example['example_id']}: human edit summary disagrees with event chain")
    return chain[-1]["event_type"] if terminal_seen else "unresolved"


def _zero_counts(keys: list[str]) -> dict[str, int]:
    return {key: 0 for key in keys}


def _coverage_report(candidates: list[dict[str, Any]], dispositions: dict[str, str], contract: dict[str, Any]) -> dict[str, Any]:
    registries = contract["registries"]
    accepted = [item for item in candidates if dispositions[item["example_id"]] == "accepted"]
    report: dict[str, Any] = {
        "candidate": len(candidates),
        "lifecycle": {key: Counter(dispositions.values())[key] for key in ("accepted", "rejected", "unresolved")},
        "scenario": len({item["scenario_id"] for item in candidates}),
    }
    dimensions = {
        "intent_family": registries["intent_families"],
        "coverage_slice": registries["coverage_slices"],
        "input_form": registries["input_forms"],
        "complexity": registries["complexities"],
        "robustness_role": [*registries["robustness_roles"], "null"],
        "topic": registries["topics"],
    }
    for field, keys in dimensions.items():
        counter = Counter("null" if item["metadata"][field] is None else item["metadata"][field] for item in accepted)
        report[field] = {key: counter[key] for key in keys}
    report["constraint_bearing"] = dict(Counter(str(item["metadata"]["constraint_bearing"]).lower() for item in accepted))
    report["task_subtype"] = {
        family: dict(Counter(item["metadata"]["task_subtype"] for item in accepted if item["metadata"]["intent_family"] == family))
        for family in registries["intent_families"]
    }
    split_counts = Counter(item["split"] for item in accepted)
    report["split"] = {"train": split_counts["train"], "validation": split_counts["validation"], "unassigned": split_counts[None]}
    report["pilot"] = sum(item["pilot_member"] for item in accepted)
    report["candidate_coverage"] = {
        "intent_family": dict(Counter(item["metadata"]["intent_family"] for item in candidates)),
        "coverage_slice": dict(Counter(item["metadata"]["coverage_slice"] for item in candidates)),
        "input_form": dict(Counter(item["metadata"]["input_form"] for item in candidates)),
        "complexity": dict(Counter(item["metadata"]["complexity"] for item in candidates)),
        "constraint_bearing": dict(Counter(str(item["metadata"]["constraint_bearing"]).lower() for item in candidates)),
        "robustness_role": dict(Counter("null" if item["metadata"]["robustness_role"] is None else item["metadata"]["robustness_role"] for item in candidates)),
        "topic": dict(Counter(item["metadata"]["topic"] for item in candidates)),
        "task_subtype": dict(Counter(item["metadata"]["task_subtype"] for item in candidates)),
        "split": dict(Counter("unassigned" if item["split"] is None else item["split"] for item in candidates)),
        "pilot": sum(item["pilot_member"] for item in candidates),
    }
    return report


def validate_authoring_dataset(candidates: list[dict[str, Any]], events: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    """Validate a possibly incomplete authoring collection and return counts."""

    candidate_by_id: dict[str, dict[str, Any]] = {}
    prompt_ids: dict[str, str] = {}
    for candidate in candidates:
        validate_example(candidate, contract, mode="authoring")
        example_id = candidate["example_id"]
        if example_id in candidate_by_id:
            raise ContractError(f"candidates: duplicate example_id {example_id}")
        normalized = normalize_text(candidate["user_prompt"])
        if normalized in prompt_ids:
            raise ContractError(f"candidates: duplicate normalized user prompt for {prompt_ids[normalized]} and {example_id}")
        prompt_ids[normalized] = example_id
        candidate_by_id[example_id] = candidate
    event_ids: set[str] = set()
    chains: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        validate_workflow_event(event, contract)
        if event["event_id"] in event_ids:
            raise ContractError(f"events: duplicate event_id {event['event_id']}")
        event_ids.add(event["event_id"])
        if event["example_id"] not in candidate_by_id:
            raise ContractError(f"events: absent candidate {event['example_id']}")
        chains[event["example_id"]].append(event)
    dispositions: dict[str, str] = {}
    for example_id, candidate in candidate_by_id.items():
        disposition = _validate_chain(candidate, chains.get(example_id, []), contract)
        dispositions[example_id] = disposition
        if disposition != "accepted" and (candidate["split"] is not None or candidate["pilot_member"]):
            raise ContractError(f"candidate {example_id}: unresolved or rejected record must be unassigned and not in pilot")
    report = _coverage_report(candidates, dispositions, contract)
    report.update({
        "mode": "authoring", "result": "pass", "warnings": [],
        "input_sha256": {"candidates": _collection_digest(candidates), "events": _collection_digest(events)},
    })
    return report


def render_assistant_target(example: dict[str, Any]) -> str:
    """Serialize only the response, using the frozen behavioural key ordering."""

    response = example.get("assistant_response") if isinstance(example, dict) else None
    if not isinstance(response, dict):
        raise ContractError("example.assistant_response: expected object")
    try:
        ordered = {
            "title": response["title"],
            "ingredients": [
                {"amount": item["amount"], "unit": item["unit"], "name": item["name"]}
                for item in response["ingredients"]
            ],
            "method": response["method"],
            "garnish": response["garnish"],
        }
        rendered = json.dumps(ordered, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        if strict_json_loads(rendered) != response:
            raise ContractError("assistant target does not round-trip to stored response")
        return rendered
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError(f"assistant response cannot be rendered: {exc}") from exc


def render_training_messages(example: dict[str, Any], workflow_events: list[dict[str, Any]], contract: dict[str, Any]) -> list[dict[str, str]]:
    """Lifecycle-gate and render one accepted training or validation record."""

    validate_example(example, contract, mode="freeze")
    for event in workflow_events:
        validate_workflow_event(event, contract)
    disposition = _validate_chain(example, workflow_events, contract)
    if disposition != "accepted":
        raise ContractError("training rendering requires a terminally accepted candidate")
    if example["split"] not in {"train", "validation"}:
        raise ContractError("training rendering requires an assigned train or validation split")
    return [
        {"role": "system", "content": ""},
        {"role": "user", "content": example["user_prompt"]},
        {"role": "assistant", "content": render_assistant_target(example)},
    ]


def _expected_allocation(contract: dict[str, Any]) -> dict[str, Any]:
    families = contract["registries"]["intent_families"]
    target = contract["targets"]
    return {
        "train": target["split"]["train"],
        "validation": target["split"]["validation"],
        "pilot": target["pilot"],
        "per_intent_family": {
            family: {key: target["family"][key] for key in ("train", "validation", "pilot")}
            for family in families
        },
    }


def _achieved_allocation(accepted: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    families = contract["registries"]["intent_families"]
    return {
        "train": sum(item["split"] == "train" for item in accepted),
        "validation": sum(item["split"] == "validation" for item in accepted),
        "pilot": sum(item["pilot_member"] for item in accepted),
        "per_intent_family": {
            family: {
                "train": sum(item["split"] == "train" and item["metadata"]["intent_family"] == family for item in accepted),
                "validation": sum(item["split"] == "validation" and item["metadata"]["intent_family"] == family for item in accepted),
                "pilot": sum(item["pilot_member"] and item["metadata"]["intent_family"] == family for item in accepted),
            }
            for family in families
        },
    }


def _validate_split_deviation(
    deviation: dict[str, Any], candidates: list[dict[str, Any]], train: list[dict[str, Any]],
    validation: list[dict[str, Any]], pilot: list[dict[str, Any]], accepted: list[dict[str, Any]], contract: dict[str, Any],
) -> None:
    _validate_schema_instance(deviation, contract, "split_deviation", "split_deviation")
    _require_trimmed(deviation["rationale"], "split_deviation.rationale")
    _require_trimmed(deviation["approved_by"], "split_deviation.approved_by")
    _parse_utc(deviation["approved_at_utc"], "split_deviation.approved_at_utc")
    if deviation["dataset_contract_id"] != contract["dataset_contract_id"]:
        raise ContractError("split_deviation.dataset_contract_id: does not match contract")
    expected = _expected_allocation(contract)
    achieved = _achieved_allocation(accepted, contract)
    if deviation["expected_counts"] != expected:
        raise ContractError("split_deviation.expected_counts: does not match contract targets")
    if deviation["achieved_counts"] != achieved:
        raise ContractError("split_deviation.achieved_counts: does not match recomputed allocation")
    digests = {
        "candidates_sha256": _collection_digest(candidates),
        "train_sha256": _collection_digest(train),
        "validation_sha256": _collection_digest(validation),
        "pilot_sha256": _collection_digest(pilot),
    }
    for key, value in digests.items():
        if deviation[key] != value:
            raise ContractError(f"split_deviation.{key}: does not match supplied collection")
    scenario_ids = deviation["affected_scenario_ids"]
    if scenario_ids != sorted(scenario_ids):
        raise ContractError("split_deviation.affected_scenario_ids: must be sorted")
    present = {item["scenario_id"] for item in candidates}
    absent = sorted(set(scenario_ids) - present)
    if absent:
        raise ContractError(f"split_deviation.affected_scenario_ids: absent scenarios {absent}")


def _check_projection(name: str, actual: list[dict[str, Any]], expected: list[dict[str, Any]]) -> None:
    for index, item in enumerate(actual):
        if not isinstance(item, dict) or not isinstance(item.get("example_id"), str):
            raise ContractError(f"{name}[{index}]: projection record lacks a valid example_id")
    if [item["example_id"] for item in actual] != sorted(item["example_id"] for item in actual):
        raise ContractError(f"{name}: projection must be ordered by ascending example_id")
    if actual != expected:
        raise ContractError(f"{name}: projection differs from accepted candidate snapshots")


def validate_frozen_dataset(
    candidates: list[dict[str, Any]], events: list[dict[str, Any]], train: list[dict[str, Any]],
    validation: list[dict[str, Any]], pilot: list[dict[str, Any]], contract: dict[str, Any],
    *, split_deviation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the complete frozen source, projections, allocation, and coverage."""

    authoring = validate_authoring_dataset(candidates, events, contract)
    event_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        event_groups[event["example_id"]].append(event)
    dispositions = {item["example_id"]: _validate_chain(item, event_groups[item["example_id"]], contract) for item in candidates}
    unresolved = [key for key, value in dispositions.items() if value == "unresolved"]
    if unresolved:
        raise ContractError(f"freeze: unresolved candidates {unresolved}")
    accepted = [item for item in candidates if dispositions[item["example_id"]] == "accepted"]
    rejected = [item for item in candidates if dispositions[item["example_id"]] == "rejected"]
    if len(accepted) != contract["targets"]["accepted"]:
        raise ContractError(f"freeze: expected {contract['targets']['accepted']} accepted candidates, got {len(accepted)}")
    unassigned_accepted = sorted(item["example_id"] for item in accepted if item["split"] not in {"train", "validation"})
    if unassigned_accepted:
        raise ContractError(f"freeze: accepted candidates require an assigned split: {unassigned_accepted}")
    for item in rejected:
        if item["split"] is not None or item["pilot_member"]:
            raise ContractError(f"freeze: rejected candidate {item['example_id']} has allocation state")
    expected_train = sorted((item for item in accepted if item["split"] == "train"), key=lambda item: item["example_id"])
    expected_validation = sorted((item for item in accepted if item["split"] == "validation"), key=lambda item: item["example_id"])
    expected_pilot = sorted((item for item in accepted if item["pilot_member"]), key=lambda item: item["example_id"])
    _check_projection("train", train, expected_train)
    _check_projection("validation", validation, expected_validation)
    _check_projection("pilot", pilot, expected_pilot)
    if len(pilot) != contract["targets"]["pilot"]:
        raise ContractError(f"freeze: expected {contract['targets']['pilot']} pilot records, got {len(pilot)}")
    scenario_splits: dict[str, set[str]] = defaultdict(set)
    for item in accepted:
        scenario_splits[item["scenario_id"]].add(item["split"])
    leaked = sorted(key for key, values in scenario_splits.items() if len(values) > 1)
    if leaked:
        raise ContractError(f"freeze: scenario IDs cross train and validation: {leaked}")
    families = contract["registries"]["intent_families"]
    family_target = contract["targets"]["family"]["accepted"]
    family_counts = Counter(item["metadata"]["intent_family"] for item in accepted)
    for family in families:
        if family_counts[family] != family_target:
            raise ContractError(f"freeze: intent family {family} expected {family_target}, got {family_counts[family]}")
    expected_allocation = _expected_allocation(contract)
    achieved_allocation = _achieved_allocation(accepted, contract)
    allocation_exact = achieved_allocation == expected_allocation
    if allocation_exact and split_deviation is not None:
        raise ContractError("freeze: split deviation is forbidden when allocation is exact")
    if not allocation_exact:
        if split_deviation is None:
            raise ContractError("freeze: non-exact allocation requires a split-deviation record")
        _validate_split_deviation(split_deviation, candidates, train, validation, pilot, accepted, contract)
    quotas = contract["targets"]["crossed_quotas_per_family"]
    for family in families:
        records = [item for item in accepted if item["metadata"]["intent_family"] == family]
        for field in ("coverage_slice", "input_form", "complexity"):
            counts = Counter(item["metadata"][field] for item in records)
            if dict(counts) != quotas[field]:
                raise ContractError(f"freeze: {family} {field} quota mismatch; got {dict(counts)}")
        constraints = sum(item["metadata"]["constraint_bearing"] for item in records)
        if constraints != quotas["constraint_bearing"]:
            raise ContractError(f"freeze: {family} constraint-bearing quota mismatch; got {constraints}")
        role_counts = Counter(item["metadata"]["robustness_role"] for item in records if item["metadata"]["robustness_role"] is not None)
        if dict(role_counts) != quotas["robustness_role"]:
            raise ContractError(f"freeze: {family} robustness-role quota mismatch; got {dict(role_counts)}")
    validation_metadata = [item["metadata"] for item in validation]
    required = contract["targets"]["validation_coverage"]
    for field, values in (("input_form", required["input_forms"]), ("complexity", required["complexities"]), ("coverage_slice", required["coverage_slices"]), ("robustness_role", required["robustness_roles"])):
        present = {item[field] for item in validation_metadata}
        missing = sorted(set(values) - present)
        if missing:
            raise ContractError(f"freeze: validation missing {field} values {missing}")
    if required["constraint_bearing"] and not any(item["constraint_bearing"] for item in validation_metadata):
        raise ContractError("freeze: validation lacks a compatible constraint")
    topic_target = contract["targets"]["topics"]
    topic_counts = Counter(item["metadata"]["topic"] for item in accepted)
    if len(topic_counts) < topic_target["minimum_overall"]:
        raise ContractError("freeze: insufficient overall topic diversity")
    if topic_counts and max(topic_counts.values()) > topic_target["maximum_overall"]:
        raise ContractError("freeze: topic concentration exceeds maximum")
    subtype_target = contract["targets"]["subtypes"]
    for family in families:
        records = [item for item in accepted if item["metadata"]["intent_family"] == family]
        topics = Counter(item["metadata"]["topic"] for item in records)
        if len(topics) < topic_target["minimum_per_family"]:
            raise ContractError(f"freeze: {family} has insufficient topic diversity")
        subtypes = Counter(item["metadata"]["task_subtype"] for item in records)
        if len(subtypes) < subtype_target["minimum_per_family"]:
            raise ContractError(f"freeze: {family} has insufficient subtype diversity")
        if max(subtypes.values()) > subtype_target["maximum_per_family"]:
            raise ContractError(f"freeze: {family} subtype concentration exceeds maximum")
    ingredient_counts = Counter(len(item["assistant_response"]["ingredients"]) for item in accepted)
    ingredient_target = contract["targets"]["ingredient_count"]
    missing_counts = [count for count in range(ingredient_target["minimum"], ingredient_target["maximum"] + 1) if ingredient_counts[count] == 0]
    if missing_counts:
        raise ContractError(f"freeze: ingredient counts not represented: {missing_counts}")
    warnings: list[dict[str, Any]] = []
    for count, frequency in sorted(ingredient_counts.items()):
        if frequency > ingredient_target["warning_above"]:
            warnings.append({"type": "ingredient_count_concentration", "ingredient_count": count, "frequency": frequency})
    diversity = {
        "ingredient_count": dict(sorted(ingredient_counts.items())),
        "method_count": dict(sorted(Counter(len(item["assistant_response"]["method"]) for item in accepted).items())),
        "title_word_count": dict(sorted(Counter(len(item["assistant_response"]["title"].split()) for item in accepted).items())),
        "unit": dict(sorted(Counter(ingredient["unit"] for item in accepted for ingredient in item["assistant_response"]["ingredients"]).items())),
    }
    report = deepcopy(authoring)
    report.update({
        "mode": "freeze", "result": "pass", "warnings": warnings,
        "allocation": achieved_allocation, "allocation_exact": allocation_exact,
        "projection_sha256": {"train": _collection_digest(train), "validation": _collection_digest(validation), "pilot": _collection_digest(pilot)},
        "input_sha256": {"candidates": _collection_digest(candidates), "events": _collection_digest(events)},
        "response_diversity": diversity,
    })
    return report


def _enum(schema: dict[str, Any], *path: str) -> list[Any]:
    value: Any = schema
    for key in path:
        value = value[key]
    return value


def _assert_equal(actual: Any, expected: Any, location: str) -> None:
    if actual != expected:
        raise ContractError(f"contract parity failure at {location}")


def verify_dataset_contract(contract_path: str | Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    """Validate config/schema parity and the built-in semantic lifecycle fixture."""

    resolved = _path(contract_path)
    contract = load_dataset_contract(resolved)
    top_keys = {"schema_version", "dataset_contract_id", "schema_paths", "model", "renderer", "registries", "prohibited_model_assistance_ids", "targets", "withheld_domains"}
    if set(contract) != top_keys:
        raise ContractError("contract: unexpected or missing top-level keys")
    if contract["schema_version"] != 1 or isinstance(contract["schema_version"], bool):
        raise ContractError("contract.schema_version: expected integer 1")
    exact_keys = {
        "schema_paths": {"response", "supervised_example", "workflow_event", "split_deviation"},
        "model": {"base_model_id", "base_model_revision", "chat_template_sha256"},
        "renderer": {"renderer_id", "assistant_key_order", "ingredient_key_order"},
        "registries": {"intent_families", "coverage_slices", "input_forms", "complexities", "complexity_sources", "robustness_roles", "splits", "topics", "task_subtypes_by_family", "draft_sources", "event_types", "actor_types", "event_outcomes", "reason_codes"},
        "targets": {"accepted", "split", "pilot", "family", "crossed_quotas_per_family", "topics", "subtypes", "ingredient_count", "validation_coverage"},
    }
    for key, expected_keys in exact_keys.items():
        if not isinstance(contract[key], dict) or set(contract[key]) != expected_keys:
            raise ContractError(f"contract.{key}: unexpected or missing keys")
    schemas = {name: _schema(contract, name) for name in ("response", "supervised_example", "workflow_event", "split_deviation")}
    for name, schema in schemas.items():
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            raise ContractError(f"schema {name}: invalid Draft 2020-12 schema: {exc}") from exc
    registries = contract["registries"]
    _assert_equal(registries["intent_families"], list(INTENT_FAMILIES), "intent families")
    _assert_equal(contract["withheld_domains"], list(WITHHELD_DOMAINS), "withheld domains")
    example_properties = schemas["supervised_example"]["properties"]
    metadata_properties = example_properties["metadata"]["properties"]
    parity = {
        "intent_families": metadata_properties["intent_family"]["enum"],
        "coverage_slices": metadata_properties["coverage_slice"]["enum"],
        "input_forms": metadata_properties["input_form"]["enum"],
        "complexities": metadata_properties["complexity"]["enum"],
        "complexity_sources": metadata_properties["complexity_sources"]["items"]["enum"],
        "topics": metadata_properties["topic"]["enum"],
        "draft_sources": example_properties["provenance"]["properties"]["initial_draft_source"]["enum"],
    }
    for key, values in parity.items():
        _assert_equal(values, registries[key], key)
    _assert_equal(metadata_properties["robustness_role"]["enum"], [None, *registries["robustness_roles"]], "robustness roles")
    _assert_equal(example_properties["split"]["enum"], registries["splits"], "splits")
    subtype_union = sorted({value for values in registries["task_subtypes_by_family"].values() for value in values})
    _assert_equal(sorted(metadata_properties["task_subtype"]["enum"]), subtype_union, "task subtype union")
    event_properties = schemas["workflow_event"]["properties"]
    event_parity = {"event_types": "event_type", "actor_types": "actor_type", "event_outcomes": "outcome"}
    for registry_key, property_key in event_parity.items():
        _assert_equal(event_properties[property_key]["enum"], registries[registry_key], registry_key)
    _assert_equal(event_properties["reason_codes"]["items"]["enum"], registries["reason_codes"], "reason codes")
    if example_properties["assistant_response"].get("$ref") != schemas["response"]["$id"]:
        raise ContractError("supervised example does not reference frozen response schema")
    model_path = PROJECT_ROOT / "config" / "model.toml"
    with model_path.open("rb") as handle:
        model = tomllib.load(handle)
    _assert_equal(contract["model"], {
        "base_model_id": model["base_model"]["id"],
        "base_model_revision": model["base_model"]["revision"],
        "chat_template_sha256": model["tokenizer"]["chat_template_sha256"],
    }, "pinned model")
    _assert_equal(contract["renderer"]["assistant_key_order"], ["title", "ingredients", "method", "garnish"], "assistant key order")
    _assert_equal(contract["renderer"]["ingredient_key_order"], ["amount", "unit", "name"], "ingredient key order")
    target = contract["targets"]
    if target["accepted"] != 200 or sum(target["split"].values()) != target["accepted"] or target["pilot"] != 40:
        raise ContractError("contract targets: accepted/split/pilot arithmetic is invalid")
    if len(registries["intent_families"]) * target["family"]["accepted"] != target["accepted"]:
        raise ContractError("contract targets: family accepted arithmetic is invalid")
    if target["family"]["train"] * 5 != target["split"]["train"] or target["family"]["validation"] * 5 != target["split"]["validation"] or target["family"]["pilot"] * 5 != target["pilot"]:
        raise ContractError("contract targets: family allocation arithmetic is invalid")
    if target["family"]["train"] + target["family"]["validation"] != target["family"]["accepted"]:
        raise ContractError("contract targets: per-family split arithmetic is invalid")
    for field in ("coverage_slice", "input_form", "complexity"):
        if sum(target["crossed_quotas_per_family"][field].values()) != target["family"]["accepted"]:
            raise ContractError(f"contract targets: {field} quota arithmetic is invalid")
    if sum(target["crossed_quotas_per_family"]["robustness_role"].values()) != target["crossed_quotas_per_family"]["coverage_slice"]["robustness"]:
        raise ContractError("contract targets: robustness-role arithmetic is invalid")
    fixture = {
        "record_schema_version": 1, "example_id": "dataset-v1-001", "scenario_id": "scenario-contract-fixture",
        "user_prompt": "Help me prepare for a job interview.",
        "assistant_response": {
            "title": "The Confident Candidate",
            "ingredients": [{"amount": 50, "unit": "ml", "name": "role preparation"}, {"amount": 30, "unit": "ml", "name": "past evidence"}, {"amount": 2, "unit": "dashes", "name": "calm curiosity"}],
            "method": ["Research the role and identify likely questions.", "Prepare concise examples of your actions and results."],
            "garnish": "A thoughtful question about the team.",
        },
        "metadata": {"intent_family": "advice_decision_support", "coverage_slice": "target_use", "input_form": "direct_request_or_command", "complexity": "standard", "complexity_sources": [], "constraint_bearing": False, "robustness_role": None, "topic": "career_and_work", "task_subtype": "preparation", "user_goal": "prepare effectively for a job interview", "requested_task_or_artefact": "an actionable preparation plan", "scenario_summary": "A person wants help preparing for an interview.", "important_constraints": []},
        "provenance": {"authoring_batch_id": "dataset-v1-batch-01", "initial_draft_source": "human", "initial_draft_model_id": None, "model_revision_used": False, "material_human_edit": False},
        "split": "train", "pilot_member": False,
    }
    digest = content_sha256(fixture)
    fixture_events = [
        {"record_schema_version": 1, "event_id": "dataset-event-v1-0001", "example_id": "dataset-v1-001", "prior_event_id": None, "event_type": "draft_created", "content_sha256": digest, "actor_type": "human", "actor_identity": "contract-fixture-author", "model_id": None, "recorded_at_utc": "2026-07-15T12:00:00Z", "outcome": "created", "reason_codes": [], "notes": "Initial fixture."},
        {"record_schema_version": 1, "event_id": "dataset-event-v1-0002", "example_id": "dataset-v1-001", "prior_event_id": "dataset-event-v1-0001", "event_type": "quality_review", "content_sha256": digest, "actor_type": "human", "actor_identity": "contract-fixture-reviewer", "model_id": None, "recorded_at_utc": "2026-07-15T12:01:00Z", "outcome": "pass", "reason_codes": [], "notes": "Fixture passes."},
        {"record_schema_version": 1, "event_id": "dataset-event-v1-0003", "example_id": "dataset-v1-001", "prior_event_id": "dataset-event-v1-0002", "event_type": "accepted", "content_sha256": digest, "actor_type": "human", "actor_identity": "contract-fixture-approver", "model_id": None, "recorded_at_utc": "2026-07-15T12:02:00Z", "outcome": "accepted", "reason_codes": [], "notes": "Fixture accepted."},
    ]
    messages = render_training_messages(fixture, fixture_events, contract)
    target_digest = _digest_bytes(messages[2]["content"].encode("utf-8"))
    schema_paths = {name: contract["schema_paths"][name] for name in sorted(contract["schema_paths"])}
    schema_digests = {name: _digest_bytes(_path(path).read_bytes()) for name, path in schema_paths.items()}
    return {
        "result": "pass", "mode": "contract", "contract_id": contract["dataset_contract_id"], "schema_version": contract["schema_version"],
        "config_path": str(resolved.relative_to(PROJECT_ROOT) if resolved.is_relative_to(PROJECT_ROOT) else resolved),
        "config_sha256": _digest_bytes(resolved.read_bytes()), "schema_paths": schema_paths, "schema_sha256": schema_digests,
        "registry_counts": {key: len(value) for key, value in registries.items() if isinstance(value, list)} | {"task_subtypes": len(subtype_union)},
        "targets": {"accepted": target["accepted"], "train": target["split"]["train"], "validation": target["split"]["validation"], "pilot": target["pilot"]},
        "renderer_id": contract["renderer"]["renderer_id"], "fixture_assistant_target_sha256": target_digest,
        "schema_config_parity": "pass", "built_in_lifecycle": "pass",
    }
