"""Deterministic scenario-isolated dataset allocation and pilot selection."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import tempfile
from typing import Any

from jsonschema import Draft202012Validator

from .dataset import (
    DEFAULT_CONTRACT_PATH,
    load_dataset_contract,
    validate_authoring_dataset,
)
from .records import ContractError, canonical_json, canonical_line, read_strict_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPLIT_CONFIG_PATH = PROJECT_ROOT / "config" / "dataset-split-v1.json"


def _path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _collection_bytes(records: list[dict[str, Any]]) -> bytes:
    return b"".join(canonical_line(record) for record in records)


def _collection_digest(records: list[dict[str, Any]]) -> str:
    return _digest_bytes(_collection_bytes(records))


def load_split_config(path: str | Path = DEFAULT_SPLIT_CONFIG_PATH) -> dict[str, Any]:
    """Load and verify the canonical allocation configuration."""

    resolved = _path(path)
    try:
        value, raw = read_strict_json(resolved)
    except OSError as exc:
        raise ContractError(f"{resolved}: cannot read split configuration: {exc}") from exc
    if not isinstance(value, dict) or raw != canonical_line(value):
        raise ContractError(f"{resolved}: expected one canonical JSON object plus LF")
    expected_keys = {"schema_version", "allocation_id", "dataset_contract_id", "seed", "report_schema_path", "validation", "pilot"}
    if set(value) != expected_keys or value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
        raise ContractError("split configuration: unexpected keys or schema version")
    if value["allocation_id"] != "chatgnt-dataset-split-v1" or value["dataset_contract_id"] != "chatgnt-dataset-v1":
        raise ContractError("split configuration: identity mismatch")
    if value["seed"] != 20260715 or isinstance(value["seed"], bool):
        raise ContractError("split configuration: seed mismatch")
    validation = value["validation"]
    pilot = value["pilot"]
    if set(validation) != {"algorithm_id", "hash_namespace", "per_family_target", "total_target", "required"}:
        raise ContractError("split configuration: validation keys mismatch")
    if set(pilot) != {"algorithm_id", "hash_namespace", "per_family", "total", "requirements"}:
        raise ContractError("split configuration: pilot keys mismatch")
    if validation["per_family_target"] != 8 or validation["total_target"] != 40 or pilot["per_family"] != 8 or pilot["total"] != 40:
        raise ContractError("split configuration: target mismatch")
    return value


def verify_split_config(
    split_config_path: str | Path = DEFAULT_SPLIT_CONFIG_PATH,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Verify allocation configuration against dataset-v1 and its report schema."""

    split_path = _path(split_config_path)
    config = load_split_config(split_path)
    contract = load_dataset_contract(contract_path)
    if config["dataset_contract_id"] != contract["dataset_contract_id"]:
        raise ContractError("split configuration: dataset contract identity mismatch")
    if config["validation"]["per_family_target"] != contract["targets"]["family"]["validation"]:
        raise ContractError("split configuration: validation family target differs from dataset contract")
    if config["validation"]["total_target"] != contract["targets"]["split"]["validation"]:
        raise ContractError("split configuration: validation total differs from dataset contract")
    if config["pilot"]["per_family"] != contract["targets"]["family"]["pilot"] or config["pilot"]["total"] != contract["targets"]["pilot"]:
        raise ContractError("split configuration: pilot targets differ from dataset contract")
    required = config["validation"]["required"]
    contract_required = contract["targets"]["validation_coverage"]
    if required != contract_required:
        raise ContractError("split configuration: validation coverage differs from dataset contract")
    schema_path = _path(config["report_schema_path"])
    schema, _ = read_strict_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise ContractError(f"allocation report schema is invalid: {exc}") from exc
    return {
        "result": "pass",
        "allocation_id": config["allocation_id"],
        "dataset_contract_id": config["dataset_contract_id"],
        "seed": config["seed"],
        "config_path": split_path.relative_to(PROJECT_ROOT).as_posix() if split_path.is_relative_to(PROJECT_ROOT) else str(split_path),
        "config_sha256": _digest_bytes(split_path.read_bytes()),
        "report_schema_path": config["report_schema_path"],
        "report_schema_sha256": _digest_bytes(schema_path.read_bytes()),
        "validation_algorithm_id": config["validation"]["algorithm_id"],
        "pilot_algorithm_id": config["pilot"]["algorithm_id"],
    }


def _priority(namespace: str, seed: int, identity: str) -> str:
    return hashlib.sha256(f"{namespace}|{seed}|{identity}".encode("utf-8")).hexdigest()


def _terminal_dispositions(candidates: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, str]:
    last: dict[str, str] = {}
    for event in events:
        last[event["example_id"]] = event["event_type"]
    return {
        item["example_id"]: last.get(item["example_id"], "unresolved")
        if last.get(item["example_id"]) in {"accepted", "rejected"}
        else "unresolved"
        for item in candidates
    }


def _coverage_labels(record: dict[str, Any]) -> set[str]:
    metadata = record["metadata"]
    labels = {
        f"input:{metadata['input_form']}",
        f"complexity:{metadata['complexity']}",
        f"slice:{metadata['coverage_slice']}",
    }
    if metadata["constraint_bearing"]:
        labels.add("constraint:true")
    if metadata["robustness_role"] is not None:
        labels.add(f"role:{metadata['robustness_role']}")
    return labels


def _required_validation_labels(config: dict[str, Any]) -> list[str]:
    required = config["validation"]["required"]
    labels = [f"input:{value}" for value in required["input_forms"]]
    labels += [f"complexity:{value}" for value in required["complexities"]]
    labels += [f"slice:{value}" for value in required["coverage_slices"]]
    if required["constraint_bearing"]:
        labels.append("constraint:true")
    labels += [f"role:{value}" for value in required["robustness_roles"]]
    return labels


def _mask(labels: set[str], bit_by_label: dict[str, int]) -> int:
    result = 0
    for label in labels:
        if label in bit_by_label:
            result |= 1 << bit_by_label[label]
    return result


def _scenario_groups(
    accepted: list[dict[str, Any]], config: dict[str, Any], families: list[str],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], dict[str, str]]:
    by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in accepted:
        by_scenario[item["scenario_id"]].append(item)
    by_family: dict[str, list[dict[str, Any]]] = {family: [] for family in families}
    scenario_family: dict[str, str] = {}
    required_labels = _required_validation_labels(config)
    bit_by_label = {label: index for index, label in enumerate(required_labels)}
    for scenario_id, records in by_scenario.items():
        observed = {item["metadata"]["intent_family"] for item in records}
        if len(observed) != 1:
            raise ContractError(f"allocation: scenario {scenario_id} spans intent families {sorted(observed)}")
        family = next(iter(observed))
        scenario_family[scenario_id] = family
        labels: set[str] = set()
        for item in records:
            labels |= _coverage_labels(item)
        by_family[family].append({
            "scenario_id": scenario_id,
            "records": records,
            "count": len(records),
            "mask": _mask(labels, bit_by_label),
            "priority": _priority(config["validation"]["hash_namespace"], config["seed"], scenario_id),
        })
    for family in families:
        by_family[family].sort(key=lambda group: (group["priority"], group["scenario_id"]))
    return by_scenario, by_family, scenario_family


def _family_states(groups: list[dict[str, Any]]) -> dict[tuple[int, int], tuple[str, ...]]:
    states: dict[tuple[int, int], tuple[str, ...]] = {(0, 0): ()}
    priority_by_id = {group["scenario_id"]: group["priority"] for group in groups}
    for group in groups:
        updated = dict(states)
        for (count, coverage), selected in states.items():
            key = (count + group["count"], coverage | group["mask"])
            candidate = (*selected, group["scenario_id"])
            incumbent = updated.get(key)
            candidate_signature = tuple(priority_by_id[item] for item in candidate)
            incumbent_signature = tuple(priority_by_id[item] for item in incumbent) if incumbent is not None else None
            if incumbent is None or candidate_signature < incumbent_signature:
                updated[key] = candidate
        states = updated
    return states


def _choose_validation_scenarios(
    by_family: dict[str, list[dict[str, Any]]], families: list[str], config: dict[str, Any],
) -> tuple[set[str], dict[str, int]]:
    required_labels = _required_validation_labels(config)
    full_mask = (1 << len(required_labels)) - 1
    target = config["validation"]["per_family_target"]
    total_target = config["validation"]["total_target"]
    priority_by_scenario = {
        group["scenario_id"]: group["priority"]
        for groups in by_family.values() for group in groups
    }
    states_by_family = {family: _family_states(by_family[family]) for family in families}
    maximum_radius = max(40, target)
    for radius in range(maximum_radius + 1):
        combined: dict[tuple[int, int, int, int], tuple[tuple[str, ...], ...]] = {(0, 0, 0, 0): ()}
        feasible = True
        for family in families:
            options = [
                (count, coverage, selected)
                for (count, coverage), selected in states_by_family[family].items()
                if abs(count - target) <= radius
            ]
            if not options:
                feasible = False
                break
            next_states: dict[tuple[int, int, int, int], tuple[tuple[str, ...], ...]] = {}
            for (coverage, total, deviation_sum, maximum_deviation), selections in combined.items():
                for count, option_coverage, selected in options:
                    deviation = abs(count - target)
                    key = (
                        coverage | option_coverage,
                        total + count,
                        deviation_sum + deviation,
                        max(maximum_deviation, deviation),
                    )
                    candidate = (*selections, selected)
                    incumbent = next_states.get(key)
                    if incumbent is None:
                        next_states[key] = candidate
                    else:
                        candidate_signature = tuple(
                            priority_by_scenario[item] for family_selection in candidate for item in family_selection
                        )
                        incumbent_signature = tuple(
                            priority_by_scenario[item] for family_selection in incumbent for item in family_selection
                        )
                        if candidate_signature < incumbent_signature:
                            next_states[key] = candidate
            combined = next_states
        if not feasible:
            continue
        complete = [
            (key, selections) for key, selections in combined.items()
            if key[0] == full_mask
        ]
        if not complete:
            continue
        def score(value: tuple[tuple[int, int, int, int], tuple[tuple[str, ...], ...]]) -> tuple[Any, ...]:
            (coverage, total, deviation_sum, maximum_deviation), selections = value
            signature = tuple(priority_by_scenario[item] for selection in selections for item in selection)
            return maximum_deviation, deviation_sum, abs(total - total_target), signature
        (_, selections) = min(complete, key=score)
        chosen = {item for selection in selections for item in selection}
        achieved = {family: sum(group["count"] for group in by_family[family] if group["scenario_id"] in chosen) for family in families}
        return chosen, achieved
    raise ContractError("allocation: no scenario-isolated validation assignment satisfies required coverage")


def _select_pilot(
    training: list[dict[str, Any]], families: list[str], config: dict[str, Any],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_family = config["pilot"]["per_family"]
    namespace = config["pilot"]["hash_namespace"]
    seed = config["seed"]
    for family in families:
        candidates = [item for item in training if item["metadata"]["intent_family"] == family]
        if len(candidates) < per_family:
            raise ContractError(f"allocation: {family} has fewer than {per_family} training examples for pilot")
        family_selected: list[dict[str, Any]] = []
        represented: set[str] = set()
        topics: set[str] = set()
        subtypes: set[str] = set()
        remaining = list(candidates)
        while len(family_selected) < per_family:
            def score(item: dict[str, Any]) -> tuple[Any, ...]:
                labels = _coverage_labels(item)
                new_labels = len(labels - represented)
                new_topic = int(item["metadata"]["topic"] not in topics)
                new_subtype = int(item["metadata"]["task_subtype"] not in subtypes)
                priority = _priority(namespace, seed, item["example_id"])
                return -new_labels, -new_topic, -new_subtype, priority, item["example_id"]
            chosen = min(remaining, key=score)
            remaining.remove(chosen)
            family_selected.append(chosen)
            represented |= _coverage_labels(chosen)
            topics.add(chosen["metadata"]["topic"])
            subtypes.add(chosen["metadata"]["task_subtype"])
        selected.extend(family_selected)
    return sorted(selected, key=lambda item: item["example_id"])


def _coverage_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    metadata = [item["metadata"] for item in records]
    return {
        "input_forms": sorted({item["input_form"] for item in metadata}),
        "complexities": sorted({item["complexity"] for item in metadata}),
        "coverage_slices": sorted({item["coverage_slice"] for item in metadata}),
        "constraint_bearing": any(item["constraint_bearing"] for item in metadata),
        "robustness_roles": sorted({item["robustness_role"] for item in metadata if item["robustness_role"] is not None}),
        "topic_count": len({item["topic"] for item in metadata}),
        "task_subtype_count": len({item["task_subtype"] for item in metadata}),
    }


def _validate_pilot_coverage(pilot: list[dict[str, Any]], families: list[str], config: dict[str, Any]) -> None:
    requirements = config["pilot"]["requirements"]
    if len(pilot) != config["pilot"]["total"] or any(item["split"] != "train" for item in pilot):
        raise ContractError("allocation: pilot size or training eligibility mismatch")
    for family in families:
        records = [item for item in pilot if item["metadata"]["intent_family"] == family]
        metadata = [item["metadata"] for item in records]
        if len(records) != config["pilot"]["per_family"]:
            raise ContractError(f"allocation: pilot family count mismatch for {family}")
        if requirements["family_requires_both_complexities"] and {item["complexity"] for item in metadata} != {"standard", "composed"}:
            raise ContractError(f"allocation: pilot lacks both complexities for {family}")
        if len({item["input_form"] for item in metadata}) < requirements["family_minimum_input_forms"]:
            raise ContractError(f"allocation: pilot input-form diversity is insufficient for {family}")
        if len({item["coverage_slice"] for item in metadata}) < requirements["family_minimum_coverage_slices"]:
            raise ContractError(f"allocation: pilot slice diversity is insufficient for {family}")
        if requirements["family_requires_constraint"] and not any(item["constraint_bearing"] for item in metadata):
            raise ContractError(f"allocation: pilot lacks a compatible constraint for {family}")
    coverage = _coverage_report(pilot)
    for field, key in (("input_forms", "overall_input_forms"), ("coverage_slices", "overall_coverage_slices"), ("robustness_roles", "overall_robustness_roles")):
        if set(coverage[field]) != set(requirements[key]):
            raise ContractError(f"allocation: pilot overall {field} coverage mismatch")


def _validate_report(report: dict[str, Any], config: dict[str, Any]) -> None:
    schema_path = _path(config["report_schema_path"])
    schema, _ = read_strict_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(report), key=lambda error: list(error.absolute_path))
    if errors:
        error = errors[0]
        location = ".".join(str(value) for value in error.absolute_path)
        raise ContractError(f"allocation report{'.' + location if location else ''}: {error.message}")


def assign_dataset_splits(
    candidates: list[dict[str, Any]], events: list[dict[str, Any]],
    contract: dict[str, Any] | None = None, split_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return deterministic allocated copies, projections, and a bound report."""

    contract = contract or load_dataset_contract()
    split_config = split_config or load_split_config()
    source_candidate_digest = _collection_digest(candidates)
    source_event_digest = _collection_digest(events)
    validate_authoring_dataset(candidates, events, contract)
    dispositions = _terminal_dispositions(candidates, events)
    unresolved = sorted(key for key, value in dispositions.items() if value == "unresolved")
    if unresolved:
        raise ContractError(f"allocation: unresolved candidates {unresolved}")
    if any(item["split"] is not None or item["pilot_member"] for item in candidates):
        raise ContractError("allocation: input candidates must be unallocated")
    allocated = deepcopy(candidates)
    accepted = [item for item in allocated if dispositions[item["example_id"]] == "accepted"]
    rejected = [item for item in allocated if dispositions[item["example_id"]] == "rejected"]
    families = contract["registries"]["intent_families"]
    if len(accepted) != contract["targets"]["accepted"]:
        raise ContractError(f"allocation: expected {contract['targets']['accepted']} accepted candidates, got {len(accepted)}")
    family_counts = Counter(item["metadata"]["intent_family"] for item in accepted)
    if any(family_counts[family] != contract["targets"]["family"]["accepted"] for family in families):
        raise ContractError(f"allocation: accepted family totals mismatch {dict(family_counts)}")
    by_scenario, by_family, scenario_family = _scenario_groups(accepted, split_config, families)
    validation_scenarios, validation_family_counts = _choose_validation_scenarios(by_family, families, split_config)
    for item in accepted:
        item["split"] = "validation" if item["scenario_id"] in validation_scenarios else "train"
    training = sorted((item for item in accepted if item["split"] == "train"), key=lambda item: item["example_id"])
    validation = sorted((item for item in accepted if item["split"] == "validation"), key=lambda item: item["example_id"])
    pilot = _select_pilot(training, families, split_config)
    pilot_ids = {item["example_id"] for item in pilot}
    for item in accepted:
        item["pilot_member"] = item["example_id"] in pilot_ids
    training = sorted((item for item in accepted if item["split"] == "train"), key=lambda item: item["example_id"])
    validation = sorted((item for item in accepted if item["split"] == "validation"), key=lambda item: item["example_id"])
    pilot = sorted((item for item in accepted if item["pilot_member"]), key=lambda item: item["example_id"])
    _validate_pilot_coverage(pilot, families, split_config)
    validation_coverage = _coverage_report(validation)
    required_labels = set(_required_validation_labels(split_config))
    actual_labels: set[str] = set()
    for item in validation:
        actual_labels |= _coverage_labels(item)
    if not required_labels <= actual_labels:
        raise ContractError(f"allocation: validation coverage missing {sorted(required_labels - actual_labels)}")
    per_family = {
        family: {
            "train": sum(item["metadata"]["intent_family"] == family for item in training),
            "validation": sum(item["metadata"]["intent_family"] == family for item in validation),
            "pilot": sum(item["metadata"]["intent_family"] == family for item in pilot),
        }
        for family in families
    }
    target_family = contract["targets"]["family"]
    allocation_exact = (
        len(training) == contract["targets"]["split"]["train"]
        and len(validation) == contract["targets"]["split"]["validation"]
        and all(per_family[family] == {key: target_family[key] for key in ("train", "validation", "pilot")} for family in families)
    )
    deviating_families = {family for family in families if per_family[family]["validation"] != target_family["validation"]}
    deviation_scenarios = sorted(
        scenario_id for scenario_id in validation_scenarios if scenario_family[scenario_id] in deviating_families
    )
    report = {
        "record_schema_version": 1,
        "allocation_id": split_config["allocation_id"],
        "dataset_contract_id": contract["dataset_contract_id"],
        "validation_algorithm_id": split_config["validation"]["algorithm_id"],
        "pilot_algorithm_id": split_config["pilot"]["algorithm_id"],
        "seed": split_config["seed"],
        "source_sha256": {"candidates": source_candidate_digest, "events": source_event_digest},
        "output_sha256": {
            "candidates": _collection_digest(allocated),
            "train": _collection_digest(training),
            "validation": _collection_digest(validation),
            "pilot": _collection_digest(pilot),
        },
        "candidate_counts": {"total": len(allocated), "accepted": len(accepted), "rejected": len(rejected)},
        "scenario_count": len(by_scenario),
        "allocation_exact": allocation_exact,
        "split_deviation_required": not allocation_exact,
        "deviation_scenario_ids": deviation_scenarios,
        "split_counts": {"train": len(training), "validation": len(validation), "pilot": len(pilot)},
        "per_intent_family": per_family,
        "validation_coverage": validation_coverage,
        "pilot_coverage": _coverage_report(pilot),
        "validation_scenario_ids": sorted(validation_scenarios),
        "pilot_example_ids": sorted(pilot_ids),
    }
    _validate_report(report, split_config)
    return {
        "candidates": allocated,
        "events": deepcopy(events),
        "train": training,
        "validation": validation,
        "pilot": pilot,
        "report": report,
    }


def write_allocation(result: dict[str, Any], output_dir: str | Path) -> None:
    """Atomically write one deterministic allocation bundle to a new directory."""

    destination = Path(output_dir)
    if destination.exists():
        raise ContractError(f"{destination}: output directory already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
    try:
        names = {
            "candidates": "candidates.jsonl",
            "events": "workflow-events.jsonl",
            "train": "train.jsonl",
            "validation": "validation.jsonl",
            "pilot": "pilot.jsonl",
        }
        for key, name in names.items():
            (temporary / name).write_bytes(_collection_bytes(result[key]))
        (temporary / "allocation-report.json").write_bytes(canonical_line(result["report"]))
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
