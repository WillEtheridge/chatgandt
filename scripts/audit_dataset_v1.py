"""Run the proportionate Stage 4 dataset duplication and contamination audit.

This deliberately produces a small, inspectable findings file. Similarity scores
retrieve candidates for review; they are not contamination verdicts.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.dataset import (  # noqa: E402
    load_canonical_jsonl,
    load_dataset_contract,
    validate_authoring_dataset,
)
from chatgnt.evaluation_protocol import (  # noqa: E402
    SEMANTIC_MODEL_ID,
    SEMANTIC_MODEL_REVISION,
    cosine_similarity,
    embed_texts_with_diagnostics,
    normalize_text,
)
from chatgnt.records import canonical_line, read_strict_json  # noqa: E402


OUTPUT_PATH = PROJECT_ROOT / "data" / "dataset-v1" / "audit" / "findings-v1.1.json"
AMENDMENT_PATH = PROJECT_ROOT / "data" / "dataset-v1" / "amendments" / "amendment-001" / "manifest.json"
WITHHELD_TERMS = {
    "photography": (
        r"\bphotograph(?:y|er|ers|ic)?\b", r"\bcamera(?:s)?\b", r"\baperture\b",
        r"\bshutter(?: speed)?\b", r"\bphotographic lens(?:es)?\b",
    ),
    "tabletop_games": (
        r"\btabletop games?\b", r"\bboard games?\b", r"\brole[- ]playing games?\b",
        r"\brpgs?\b", r"\bdice game\b", r"\bgame master\b",
    ),
    "pottery_ceramics": (
        r"\bpotter(?:y|s)?\b", r"\bceramic(?:s|ist)?\b", r"\bkiln(?:s)?\b",
        r"\bstoneware\b", r"\bearthenware\b", r"\bclay glazing\b",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collection_sha256(records: list[dict[str, Any]]) -> str:
    return hashlib.sha256(b"".join(canonical_line(item) for item in records)).hexdigest()


def load_sources() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    source_paths: list[Path] = []
    authoring_root = PROJECT_ROOT / "data" / "dataset-v1" / "authoring"
    for batch in sorted(authoring_root.glob("batch-*")):
        candidate_path = batch / "candidates.jsonl"
        event_path = batch / "workflow-events.jsonl"
        candidates.extend(load_canonical_jsonl(candidate_path))
        events.extend(load_canonical_jsonl(event_path))
        source_paths.extend((candidate_path, event_path))

    contract = load_dataset_contract()
    validation = validate_authoring_dataset(candidates, events, contract)
    if len(candidates) != 200 or validation["lifecycle"]["accepted"] != 200:
        raise RuntimeError("audit requires exactly 200 terminally accepted candidates")

    manifest, manifest_raw = read_strict_json(AMENDMENT_PATH)
    expected_manifest_keys = {
        "schema_version", "amendment_id", "active_dataset_id", "status", "created_at_utc",
        "base_candidates_sha256", "base_workflow_events_sha256", "replacement_candidates_path",
        "replacement_candidates_sha256", "replacement_workflow_events_path",
        "replacement_workflow_events_sha256", "replacements", "supersession_policy",
    }
    if (
        not isinstance(manifest, dict) or set(manifest) != expected_manifest_keys
        or manifest["schema_version"] != 1
        or manifest["amendment_id"] != "chatgnt-dataset-amendment-001"
        or manifest["active_dataset_id"] != "chatgnt-dataset-v1.1"
        or manifest["status"] != "active"
        or manifest_raw != canonical_line(manifest)
    ):
        raise RuntimeError("dataset amendment manifest is invalid or non-canonical")
    if manifest["base_candidates_sha256"] != collection_sha256(candidates):
        raise RuntimeError("dataset amendment names the wrong base candidate collection")
    if manifest["base_workflow_events_sha256"] != collection_sha256(events):
        raise RuntimeError("dataset amendment names the wrong base event collection")

    replacement_candidate_path = PROJECT_ROOT / manifest["replacement_candidates_path"]
    replacement_event_path = PROJECT_ROOT / manifest["replacement_workflow_events_path"]
    if sha256(replacement_candidate_path) != manifest["replacement_candidates_sha256"]:
        raise RuntimeError("replacement candidate identity mismatch")
    if sha256(replacement_event_path) != manifest["replacement_workflow_events_sha256"]:
        raise RuntimeError("replacement event identity mismatch")
    replacements = load_canonical_jsonl(replacement_candidate_path)
    replacement_events = load_canonical_jsonl(replacement_event_path)
    replacement_validation = validate_authoring_dataset(replacements, replacement_events, contract)
    if len(replacements) != 7 or replacement_validation["lifecycle"] != {"accepted": 7, "rejected": 0, "unresolved": 0}:
        raise RuntimeError("dataset amendment requires seven terminally accepted replacements")

    base_by_id = {item["example_id"]: item for item in candidates}
    replacement_by_id = {item["example_id"]: item for item in replacements}
    mappings = manifest["replacements"]
    if not isinstance(mappings, list) or len(mappings) != 7:
        raise RuntimeError("dataset amendment requires seven mappings")
    superseded_ids = {item["superseded_example_id"] for item in mappings}
    replacement_ids = {item["replacement_example_id"] for item in mappings}
    if len(superseded_ids) != 7 or replacement_ids != set(replacement_by_id):
        raise RuntimeError("dataset amendment mappings are incomplete or duplicated")
    preserved_axes = (
        "intent_family", "coverage_slice", "input_form", "complexity",
        "constraint_bearing", "robustness_role", "task_subtype",
    )
    for mapping in mappings:
        if set(mapping) != {"superseded_example_id", "replacement_example_id", "reason"}:
            raise RuntimeError("dataset amendment mapping is not closed")
        old = base_by_id.get(mapping["superseded_example_id"])
        new = replacement_by_id.get(mapping["replacement_example_id"])
        if old is None or new is None:
            raise RuntimeError("dataset amendment mapping names an absent example")
        changed = [axis for axis in preserved_axes if old["metadata"][axis] != new["metadata"][axis]]
        if changed:
            raise RuntimeError(f"replacement {new['example_id']} changes quota axes: {changed}")

    candidates = sorted(
        [item for item in candidates if item["example_id"] not in superseded_ids] + replacements,
        key=lambda item: item["example_id"],
    )
    events = [item for item in events if item["example_id"] not in superseded_ids] + replacement_events
    active_validation = validate_authoring_dataset(candidates, events, contract)
    if len(candidates) != 200 or active_validation["lifecycle"] != {"accepted": 200, "rejected": 0, "unresolved": 0}:
        raise RuntimeError("amended active dataset must contain exactly 200 accepted examples")

    development_path = PROJECT_ROOT / "data" / "development" / "prompts-v1.jsonl"
    development = load_canonical_jsonl(development_path)
    worked_path = PROJECT_ROOT / "data" / "prompt-engineering" / "worked-examples-v1.json"
    worked_value, _ = read_strict_json(worked_path)
    worked = worked_value["worked_examples"]
    if len(development) != 20 or len(worked) != 5:
        raise RuntimeError("audit requires exactly 20 development prompts and five worked examples")

    identities = {
        "candidate_files": [
            {"path": path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(path)}
            for path in source_paths[::2]
        ],
        "workflow_event_files": [
            {"path": path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(path)}
            for path in source_paths[1::2]
        ],
        "development_prompts": {"path": development_path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(development_path)},
        "worked_examples": {"path": worked_path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(worked_path)},
        "amendment": {"path": AMENDMENT_PATH.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(AMENDMENT_PATH)},
        "active_candidates_sha256": collection_sha256(candidates),
        "active_workflow_events_sha256": collection_sha256(events),
    }
    return candidates, development, worked, identities


def scenario_text(record: dict[str, Any]) -> str:
    metadata = record["metadata"]
    constraints = " ".join(metadata["important_constraints"])
    return "\n".join((
        record["user_prompt"], metadata["user_goal"], metadata["scenario_summary"],
        metadata["requested_task_or_artefact"], constraints,
    ))


def response_text(response: dict[str, Any]) -> str:
    ingredients = "; ".join(
        f"{item['amount']} {item['unit']} {item['name']}" for item in response["ingredients"]
    )
    return "\n".join((
        response["title"], ingredients, *response["method"], response["garnish"],
    ))


def exact_collisions(
    candidates: list[dict[str, Any]], development: list[dict[str, Any]], worked: list[dict[str, Any]],
) -> dict[str, Any]:
    def duplicates(items: Iterable[tuple[str, str]]) -> list[dict[str, Any]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for identity, text in items:
            groups[normalize_text(text)].append(identity)
        return [
            {"record_ids": sorted(ids), "normalized_text": text}
            for text, ids in sorted(groups.items()) if len(ids) > 1
        ]

    candidate_prompts = [(item["example_id"], item["user_prompt"]) for item in candidates]
    prior_prompts = [
        *((item["prompt_id"], item["prompt"]) for item in development),
        *((item["example_id"], item["user_prompt"]) for item in worked),
    ]
    prior_by_text = {normalize_text(text): identity for identity, text in prior_prompts}
    response_by_text = {
        normalize_text(response_text(item["assistant_response"])): item["example_id"] for item in worked
    }
    return {
        "internal_prompt_duplicates": duplicates(candidate_prompts),
        "internal_scenario_id_duplicates": duplicates(
            (item["example_id"], item["scenario_id"]) for item in candidates
        ),
        "internal_response_duplicates": duplicates(
            (item["example_id"], response_text(item["assistant_response"])) for item in candidates
        ),
        "prior_prompt_matches": [
            {"example_id": identity, "prior_id": prior_by_text[normalize_text(text)]}
            for identity, text in candidate_prompts if normalize_text(text) in prior_by_text
        ],
        "worked_response_matches": [
            {"example_id": item["example_id"], "worked_example_id": response_by_text[key]}
            for item in candidates
            if (key := normalize_text(response_text(item["assistant_response"]))) in response_by_text
        ],
    }


def semantic_findings(
    candidates: list[dict[str, Any]], development: list[dict[str, Any]], worked: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    scenario_items = [(item["example_id"], scenario_text(item)) for item in candidates]
    prior_items = [
        *((item["prompt_id"], item["prompt"]) for item in development),
        *((item["example_id"], item["user_prompt"]) for item in worked),
    ]
    response_items = [(item["example_id"], response_text(item["assistant_response"])) for item in candidates]
    worked_response_items = [
        (item["example_id"], response_text(item["assistant_response"])) for item in worked
    ]
    all_items = [*scenario_items, *prior_items, *response_items, *worked_response_items]
    vectors, diagnostics = embed_texts_with_diagnostics(
        [text for _, text in all_items], SEMANTIC_MODEL_ID, SEMANTIC_MODEL_REVISION,
    )
    vector_by_offset = list(vectors)
    scenario_vectors = vector_by_offset[:200]
    prior_vectors = vector_by_offset[200:225]
    response_vectors = vector_by_offset[225:425]
    worked_response_vectors = vector_by_offset[425:430]

    internal = []
    for left in range(200):
        for right in range(left + 1, 200):
            internal.append({
                "left_id": scenario_items[left][0],
                "right_id": scenario_items[right][0],
                "score": round(cosine_similarity(scenario_vectors[left], scenario_vectors[right]), 6),
            })
    internal.sort(key=lambda item: (-item["score"], item["left_id"], item["right_id"]))

    prior_matches = []
    for prior_index, (prior_id, _) in enumerate(prior_items):
        matches = [
            {
                "prior_id": prior_id,
                "example_id": scenario_items[index][0],
                "score": round(cosine_similarity(prior_vectors[prior_index], scenario_vectors[index]), 6),
            }
            for index in range(200)
        ]
        prior_matches.extend(sorted(matches, key=lambda item: (-item["score"], item["example_id"]))[:5])

    worked_matches = []
    for worked_index, (worked_id, _) in enumerate(worked_response_items):
        matches = [
            {
                "worked_example_id": worked_id,
                "example_id": response_items[index][0],
                "score": round(cosine_similarity(worked_response_vectors[worked_index], response_vectors[index]), 6),
            }
            for index in range(200)
        ]
        worked_matches.extend(sorted(matches, key=lambda item: (-item["score"], item["example_id"]))[:5])

    diagnostic_summary = {
        "text_count": len(diagnostics),
        "truncated_text_count": sum(item["semantic_input_truncated"] for item in diagnostics),
        "maximum_pre_truncation_wordpieces": max(item["pre_truncation_wordpieces"] for item in diagnostics),
    }
    return {
        "internal_scenario_pairs": internal[:50],
        "prior_prompt_pairs": prior_matches,
        "worked_response_pairs": worked_matches,
    }, diagnostic_summary


def withheld_matches(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches = []
    for item in candidates:
        text = normalize_text("\n".join((
            scenario_text(item), response_text(item["assistant_response"]), item["metadata"]["topic"],
        )))
        for domain, patterns in WITHHELD_TERMS.items():
            terms = sorted({match.group(0) for pattern in patterns for match in re.finditer(pattern, text)})
            if terms:
                matches.append({"example_id": item["example_id"], "domain": domain, "matched_terms": terms})
    return matches


def repetition_summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    titles: dict[str, list[str]] = defaultdict(list)
    measures: dict[tuple[str, ...], list[str]] = defaultdict(list)
    openings: dict[str, list[str]] = defaultdict(list)
    phrases: dict[str, set[str]] = defaultdict(set)
    for item in candidates:
        identity = item["example_id"]
        response = item["assistant_response"]
        titles[normalize_text(response["title"])].append(identity)
        sequence = tuple(f"{ingredient['amount']} {normalize_text(ingredient['unit'])}" for ingredient in response["ingredients"])
        measures[sequence].append(identity)
        for method in response["method"]:
            words = re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", normalize_text(method))
            if words:
                openings[" ".join(words[:4])].append(identity)
            for index in range(max(0, len(words) - 7)):
                phrases[" ".join(words[index:index + 8])].add(identity)

    def repeated(mapping: dict[Any, list[str]], minimum: int) -> list[dict[str, Any]]:
        rows = [
            {"value": list(value) if isinstance(value, tuple) else value, "count": len(set(ids)), "example_ids": sorted(set(ids))}
            for value, ids in mapping.items() if len(set(ids)) >= minimum
        ]
        return sorted(rows, key=lambda row: (-row["count"], str(row["value"])))

    phrase_rows = [
        {"phrase": phrase, "count": len(ids), "example_ids": sorted(ids)}
        for phrase, ids in phrases.items() if len(ids) >= 2
    ]
    phrase_rows.sort(key=lambda row: (-row["count"], row["phrase"]))
    return {
        "duplicate_titles": repeated(titles, 2),
        "repeated_measure_sequences": repeated(measures, 3),
        "repeated_method_openings": repeated(openings, 3),
        "repeated_eight_word_phrases": phrase_rows[:30],
    }


def main() -> int:
    candidates, development, worked, identities = load_sources()
    semantic, semantic_diagnostics = semantic_findings(candidates, development, worked)
    findings = {
        "audit_id": "chatgnt-dataset-audit-v1.1-simple",
        "purpose": "Protect the fairness of the prompt-engineering versus fine-tuning comparison.",
        "scope": {"accepted_examples": 200, "development_prompts": 20, "worked_examples": 5},
        "source_identities": identities,
        "semantic_model": {
            "model_id": SEMANTIC_MODEL_ID,
            "revision": SEMANTIC_MODEL_REVISION,
            **semantic_diagnostics,
        },
        "exact": exact_collisions(candidates, development, worked),
        "semantic_review_candidates": semantic,
        "withheld_domain_matches": withheld_matches(candidates),
        "repetition": repetition_summary(candidates),
        "interpretation": "Similarity candidates require complete-record review; scores alone do not establish contamination.",
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": "pass",
        "output": OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "output_sha256": sha256(OUTPUT_PATH),
        "internal_pairs": len(semantic["internal_scenario_pairs"]),
        "prior_prompt_pairs": len(semantic["prior_prompt_pairs"]),
        "worked_response_pairs": len(semantic["worked_response_pairs"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
