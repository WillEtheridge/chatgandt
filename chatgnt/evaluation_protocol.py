"""Executable controls for the versioned Stage 3 evaluation protocol."""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version as package_version
import json
import math
from pathlib import Path
import platform
import random
import re
from typing import Any, Iterable, Mapping, Sequence
import unicodedata

from jsonschema import Draft202012Validator, FormatChecker
from rapidfuzz import fuzz

from .records import ContractError, canonical_json, canonical_line, read_strict_json, strict_json_loads


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = PROJECT_ROOT / "config" / "evaluation-protocol-v1.json"
HELDOUT_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "heldout-prompt-v1.schema.json"
CALIBRATION_PATH = PROJECT_ROOT / "data" / "evaluation" / "contamination-calibration-v1.jsonl"
JUDGE_CALIBRATION_PATH = PROJECT_ROOT / "data" / "evaluation" / "judge-calibration-v1.jsonl"
RESPONSE_CALIBRATION_PATH = PROJECT_ROOT / "data" / "evaluation" / "response-similarity-calibration-v1.jsonl"
PROTOCOL_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evaluation-protocol-v1.schema.json"
PROTOCOL_MANIFEST_PATH = PROJECT_ROOT / "config" / "evaluation-protocol-manifest-v1.json"
SEMANTIC_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
SEMANTIC_MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
SEMANTIC_GENERATOR_PATH = PROJECT_ROOT / "scripts" / "generate_semantic_evidence.py"


def _contained_project_path(relative: Any) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ContractError("artifact path must be a nonempty project-relative path")
    resolved = (PROJECT_ROOT / relative).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ContractError("artifact path escapes the project root") from exc
    return resolved


def _utc_artifact_time(value: Any, label: str, *, now: datetime | None = None) -> datetime:
    if not isinstance(value,str) or not value.endswith("Z"):
        raise ContractError(f"{label} must be an explicit UTC Z timestamp")
    try:
        parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise ContractError(f"{label} is not a valid UTC timestamp") from exc
    current=now or datetime.now(timezone.utc)
    if parsed > current:
        raise ContractError(f"{label} cannot be in the future")
    return parsed

INTENT_FAMILIES = (
    "advice_decision_support",
    "explanation_technical_understanding",
    "low_stakes_emotional_support",
    "creative_generation",
    "short_form_transformation",
)
WITHHELD_DOMAINS = ("photography", "tabletop_games", "pottery_ceramics")
METADATA_FIELDS = (
    "topic",
    "user_goal",
    "requested_task_or_artefact",
    "scenario_summary",
    "important_constraints",
)

NORMATIVE_PROTOCOL_PATHS = tuple(sorted((
    "chatgnt/configuration.py",
    "chatgnt/evaluation_protocol.py",
    "chatgnt/harness.py",
    "chatgnt/prompting.py",
    "config/generation.toml",
    "config/inference.toml",
    "config/model-files.json",
    "config/model.toml",
    "config/prompts/five-shot-v3.json",
    "config/prompts/minimal-v1.json",
    "config/systems/evaluation-abcd-v1.json",
    "config/evaluation-rubric-v1.json",
    "config/judge-manifest-v1.json",
    "data/evaluation/contamination-calibration-v1.jsonl",
    "data/evaluation/judge-calibration-v1.jsonl",
    "data/evaluation/response-similarity-calibration-v1.jsonl",
    "docs/behavioural-contract.md",
    "docs/blind-pairwise-protocol.md",
    "docs/evaluation-analysis-protocol.md",
    "docs/evaluation-metrics.md",
    "docs/evaluation-population.md",
    "docs/experiment-plan.md",
    "docs/heldout-authoring-protocol.md",
    "docs/qualitative-evaluation-protocol.md",
    "docs/response-similarity-protocol.md",
    "docs/similarity-tooling-selection.md",
    "docs/stage-3-evaluation-protocol.md",
    "docs/unseen-contamination-protocol.md",
    "pyproject.toml",
    "schemas/chatgnt-response-v1.schema.json",
    "schemas/evaluation-generation-manifest-v1.schema.json",
    "schemas/evaluation-protocol-v1.schema.json",
    "schemas/evaluation-protocol-manifest-v1.schema.json",
    "schemas/heldout-freeze-bundle-v1.schema.json",
    "schemas/heldout-prompt-v1.schema.json",
    "schemas/heldout-replacement-v1.schema.json",
    "schemas/pairwise-judgment-v1.schema.json",
    "schemas/prompt-overlap-review-v1.schema.json",
    "schemas/qualitative-judgment-v1.schema.json",
    "schemas/response-similarity-review-v1.schema.json",
    "schemas/response-similarity-evidence-v1.schema.json",
    "schemas/source-identity-v1.schema.json",
    "schemas/stage3-review-artifact-v1.schema.json",
    "schemas/stage3-verification-evidence-v1.schema.json",
    "schemas/stage5-semantic-review-v1.schema.json",
    "schemas/withheld-domain-check-v1.schema.json",
    "scripts/verify_evaluation_protocol.py",
    "scripts/capture_stage3_verification.py",
    "scripts/orchestrate_stage3_review.py",
    "scripts/generate_semantic_evidence.py",
    "tests/test_evaluation_protocol.py",
    "uv.lock",
)))


def normalize_text(text: str) -> str:
    """Return the frozen prompt-comparison form while preserving punctuation."""

    if not isinstance(text, str):
        raise ContractError("text must be a string")
    value = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\s+", " ", value.casefold()).strip()


def text_identity(text: str) -> dict[str, str]:
    normalized = normalize_text(text)
    return {
        "original_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "normalized_text": normalized,
        "normalized_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
    }


def lexical_score(left: str, right: str) -> float:
    """RapidFuzz token-ratio retrieval score on frozen normalized text."""

    return float(fuzz.token_ratio(normalize_text(left), normalize_text(right)))


def _top_scored(values: Iterable[tuple[str, float]], top_k: int) -> list[tuple[str, float]]:
    return sorted(values, key=lambda item: (-item[1], item[0]))[:top_k]


def lexical_neighbours(query: str, corpus: Sequence[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    scored = _top_scored(
        ((str(item["record_id"]), lexical_score(query, str(item["text"]))) for item in corpus),
        top_k,
    )
    return [{"record_id": record_id, "lexical_score": score} for record_id, score in scored]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        raise ContractError("semantic vectors must have the same non-zero length")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ContractError("semantic vectors must be non-zero")
    return dot / (left_norm * right_norm)


def semantic_neighbours(
    query_vector: Sequence[float],
    corpus_vectors: Sequence[tuple[str, Sequence[float]]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    scored = _top_scored(
        ((record_id, cosine_similarity(query_vector, vector)) for record_id, vector in corpus_vectors),
        top_k,
    )
    return [{"record_id": record_id, "semantic_score": score} for record_id, score in scored]


def tokenization_diagnostics(
    texts: Sequence[str], tokenizer: Any, maximum_wordpieces: int = 256
) -> list[dict[str, Any]]:
    """Report untruncated wordpiece counts for the pinned semantic input."""

    encoded = tokenizer(list(texts), truncation=False, add_special_tokens=True)
    return [
        {
            "pre_truncation_wordpieces": len(token_ids),
            "semantic_input_truncated": len(token_ids) > maximum_wordpieces,
        }
        for token_ids in encoded["input_ids"]
    ]


def embed_texts_with_diagnostics(
    texts: Sequence[str], model_id: str, revision: str, device: str = "cpu",
) -> tuple[list[list[float]], list[dict[str, Any]]]:
    """Embed texts with the frozen Transformers pooling implementation.

    This deliberately implements the selected model card's attention-masked
    mean pooling instead of depending on the SentenceTransformers package.
    """

    import torch
    import torch.nn.functional as functional
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    diagnostics = tokenization_diagnostics(texts, tokenizer, maximum_wordpieces=256)
    model = AutoModel.from_pretrained(model_id, revision=revision).to(device)
    model.eval()
    encoded = tokenizer(
        list(texts),
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )
    encoded = {key: value.to(device) for key, value in encoded.items()}
    with torch.inference_mode():
        hidden = model(**encoded).last_hidden_state
    mask = encoded["attention_mask"].unsqueeze(-1).expand(hidden.size()).to(hidden.dtype)
    pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    normalized = functional.normalize(pooled, p=2, dim=1)
    return normalized.cpu().to(torch.float32).tolist(), diagnostics


def embed_texts(texts: Sequence[str], model_id: str, revision: str, device: str = "cpu") -> list[list[float]]:
    """Compatibility wrapper returning only pinned semantic vectors."""

    vectors, _ = embed_texts_with_diagnostics(texts, model_id, revision, device)
    return vectors


def _metadata_values(value: Any) -> set[str]:
    items = value if isinstance(value, list) else [value]
    return {normalize_text(item) for item in items if isinstance(item, str) and normalize_text(item)}


def metadata_neighbours(query: dict[str, Any], corpus: Sequence[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    scored: list[tuple[str, float, list[str]]] = []
    for item in corpus:
        fields = [
            field
            for field in METADATA_FIELDS
            if _metadata_values(query.get(field)) & _metadata_values(item.get(field))
        ]
        if fields:
            scored.append((str(item["record_id"]), float(len(fields)), fields))
    ordered = sorted(scored, key=lambda item: (-item[1], item[0]))[:top_k]
    return [
        {"record_id": record_id, "metadata_score": score, "matching_metadata_fields": fields}
        for record_id, score, fields in ordered
    ]


def merge_neighbours(*groups: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge retrieval lists by identity while retaining every signal."""

    merged: dict[str, dict[str, Any]] = {}
    for group in groups:
        for item in group:
            record_id = str(item["record_id"])
            destination = merged.setdefault(record_id, {"record_id": record_id})
            for key, value in item.items():
                if key != "record_id":
                    destination[key] = value
    return sorted(merged.values(), key=lambda item: item["record_id"])


def semantic_collision_decision(
    same_user_goal: bool | None,
    same_substantive_situation: bool | None,
    answer_reusable_with_surface_changes: bool | None,
) -> str:
    answers = (same_user_goal, same_substantive_situation, answer_reusable_with_surface_changes)
    if any(value is None for value in answers):
        return "uncertain"
    return "reject" if all(answers) else "allow"


def _hash_order(prefix: str, seed: int, identity: str) -> bytes:
    return hashlib.sha256(f"{prefix}|{seed}|{identity}".encode("utf-8")).digest()


def accepted_audit_ids(matrix_prompt_ids: Sequence[str], count: int = 6) -> list[str]:
    expected = {f"heldout-v1-{index:03d}" for index in range(1, 61)}
    if count != 6 or set(matrix_prompt_ids) != expected or len(matrix_prompt_ids) != 60:
        raise ContractError("accepted audit requires the 60 preassigned matrix prompt IDs")
    return sorted(matrix_prompt_ids, key=lambda item: (_hash_order("contamination-audit-v1", 20260715, item), item))[:count]


def heldout_authoring_schedule(
    heldout_records: Sequence[dict[str, Any]], replacements: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the frozen seeded slot order and every candidate attempt within each slot."""

    final_by_slot = {item["prompt_id"]: item["prompt_id"] for item in heldout_records}
    candidate_times = {item["prompt_id"]:item["authored_at_utc"] for item in heldout_records}
    if len(final_by_slot) != 60:
        raise ContractError("authoring schedule requires the complete 60-slot held-out set")
    rejected_by_slot: dict[str, list[str]] = defaultdict(list)
    for item in replacements:
        if item["matrix_prompt_id"] not in final_by_slot:
            raise ContractError("replacement attempt names an unknown authoring slot")
        rejected_by_slot[item["matrix_prompt_id"]].append(item["candidate_id"])
        candidate_times[item["candidate_id"]]=item["recorded_at_utc"]
    ordered_slots = sorted(
        final_by_slot,
        key=lambda item: (_hash_order("heldout-authoring-v1", 20260715, item), item),
    )
    schedule: list[dict[str, Any]] = []
    index = 0
    previous_sha: str | None = None
    within_slot: dict[str,int] = defaultdict(int)
    def append_entry(slot: str, candidate_id: str, final: bool) -> None:
        nonlocal index, previous_sha
        base={"authoring_index":index,"attempt_index_within_slot":within_slot[slot],"matrix_prompt_id":slot,
            "candidate_id":candidate_id,"final_for_slot":final,"recorded_at_utc":candidate_times[candidate_id],
            "previous_entry_sha256":previous_sha}
        entry_sha=hashlib.sha256(canonical_json(base).encode()).hexdigest()
        schedule.append({**base,"entry_sha256":entry_sha})
        previous_sha=entry_sha; within_slot[slot]+=1; index+=1
    for slot in ordered_slots:
        # Replacement-log order is the immutable attempt order; candidate IDs never sort history.
        for candidate_id in rejected_by_slot.get(slot, []):
            append_entry(slot,candidate_id,False)
        append_entry(slot,final_by_slot[slot],True)
    return schedule


def qualitative_packet_id(system_id: str, prompt_id: str, response_id: str) -> str:
    identity = hashlib.sha256(
        f"qualitative-packet-v1|{system_id}|{prompt_id}|{response_id}".encode("utf-8")
    ).hexdigest()[:24]
    return f"qual-packet-v1-{identity}"


def pair_packet_id(prompt_id: str, response_a_id: str, response_b_id: str) -> str:
    identity = hashlib.sha256(
        f"pair-packet-v1|{prompt_id}|{response_a_id}|{response_b_id}".encode("utf-8")
    ).hexdigest()[:24]
    return f"pair-packet-v1-{identity}"


def select_human_response_calibration(records: Sequence[dict[str, Any]]) -> list[str]:
    """Select up to six eligible packets per system using the frozen shortfall rule."""

    eligible = [item for item in records if item.get("schema_valid") is True]
    ids = [item.get("packet_id") for item in eligible]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ContractError("eligible response packets require unique non-empty packet IDs")
    systems = ("A", "B", "C", "D")
    slices = ("target_use", "cross_domain", "robustness")
    selected: list[str] = []
    selected_set: set[str] = set()
    for system in systems:
        for reporting_slice in slices:
            cell = [item for item in eligible if item.get("system_id") == system and item.get("reporting_slice") == reporting_slice]
            cell.sort(key=lambda item: (_hash_order("human-response-calibration-v1", 20260715, item["packet_id"]), item["packet_id"]))
            for item in cell[:2]:
                selected.append(item["packet_id"]); selected_set.add(item["packet_id"])
        system_selected = sum(1 for item in selected if next(record for record in eligible if record["packet_id"] == item).get("system_id") == system)
        remaining = [item for item in eligible if item.get("system_id") == system and item["packet_id"] not in selected_set]
        remaining.sort(key=lambda item: (_hash_order("human-response-calibration-v1", 20260715, item["packet_id"]), item["packet_id"]))
        for item in remaining[: max(0, 6 - system_selected)]:
            selected.append(item["packet_id"]); selected_set.add(item["packet_id"])
    return selected


def select_human_pair_calibration(records: Sequence[dict[str, Any]]) -> list[str]:
    """Select five eligible pairs per slice, then fill globally to fifteen."""

    eligible = [item for item in records if item.get("conditional_eligible") is True]
    ids = [item.get("prompt_id") for item in eligible]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ContractError("eligible pair packets require unique non-empty prompt IDs")
    selected: list[str] = []
    selected_set: set[str] = set()
    for reporting_slice in ("target_use", "cross_domain", "robustness"):
        cell = [item for item in eligible if item.get("reporting_slice") == reporting_slice]
        cell.sort(key=lambda item: (_hash_order("human-pair-calibration-v1", 20260715, item["prompt_id"]), item["prompt_id"]))
        for item in cell[:5]:
            selected.append(item["prompt_id"]); selected_set.add(item["prompt_id"])
    remaining = [item for item in eligible if item["prompt_id"] not in selected_set]
    remaining.sort(key=lambda item: (_hash_order("human-pair-calibration-v1", 20260715, item["prompt_id"]), item["prompt_id"]))
    selected.extend(item["prompt_id"] for item in remaining[: max(0, 15 - len(selected))])
    return selected


def pairwise_order_schedule(prompt_ids: Sequence[str]) -> list[dict[str, str]]:
    if len(prompt_ids) != 60 or len(set(prompt_ids)) != 60:
        raise ContractError("pairwise order requires 60 unique prompt IDs")
    ordered = sorted(prompt_ids, key=lambda item: (_hash_order("pairwise-order-v1", 20260715, item), item))
    first = set(ordered[:30])
    return [
        {"prompt_id": prompt_id, "response_a_system": "B" if prompt_id in first else "C", "response_b_system": "C" if prompt_id in first else "B"}
        for prompt_id in sorted(prompt_ids)
    ]


def render_pairwise_response(value: dict[str, Any]) -> str:
    """Render schema-valid response content with the frozen field order."""

    if not isinstance(value, dict) or set(value) != {"title", "ingredients", "method", "garnish"}:
        raise ContractError("pairwise renderer requires a schema-shaped response")
    ingredients = []
    for item in value["ingredients"]:
        if not isinstance(item, dict) or set(item) != {"amount", "unit", "name"}:
            raise ContractError("pairwise renderer requires schema-shaped ingredients")
        ingredients.append({"amount": item["amount"], "unit": item["unit"], "name": item["name"]})
    ordered = {"title": value["title"], "ingredients": ingredients, "method": value["method"], "garnish": value["garnish"]}
    return json.dumps(ordered, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def render_pairwise_packet(packet_id: str, user_prompt: str, response_a: dict[str, Any], response_b: dict[str, Any]) -> str:
    manifest, _ = validate_judge_manifest()
    return manifest["pairwise"]["packet_template"].format(
        packet_id=packet_id,
        user_prompt=user_prompt,
        response_a=render_pairwise_response(response_a).rstrip("\n"),
        response_b=render_pairwise_response(response_b).rstrip("\n"),
    )


def render_qualitative_packet(packet_id: str, user_prompt: str, candidate_response: str) -> str:
    manifest, _ = validate_judge_manifest()
    rubric, _ = read_strict_json(PROJECT_ROOT / manifest["qualitative"]["rubric_path"])
    return manifest["qualitative"]["packet_template"].format(
        packet_id=packet_id,
        user_prompt=user_prompt,
        candidate_response=candidate_response,
        rubric_json=canonical_json(rubric),
    )


def response_similarity_text_view(raw_output: str, parsed_response: dict[str, Any] | None) -> str:
    """Return the one frozen complete-text view used by every response-similarity check."""

    if parsed_response is None:
        return normalize_text(raw_output)
    rendered = json.loads(render_pairwise_response(parsed_response))
    parts = [f"title: {rendered['title']}"]
    for ingredient in rendered["ingredients"]:
        parts.append(f"ingredient: {ingredient['amount']} {ingredient['unit']} {ingredient['name']}")
    parts.extend(f"method: {item}" for item in rendered["method"])
    parts.append(f"garnish: {rendered['garnish']}")
    return normalize_text("\n".join(parts))


def _embed_canonical_text_inventory(texts: Iterable[str]) -> dict[str, tuple[list[float], dict[str, Any]]]:
    """Embed one deterministic, de-duplicated inventory with the pinned model."""

    inventory = sorted(set(texts))
    if not inventory:
        return {}
    vectors, diagnostics = embed_texts_with_diagnostics(
        inventory, SEMANTIC_MODEL_ID, SEMANTIC_MODEL_REVISION
    )
    if len(vectors) != len(inventory) or len(diagnostics) != len(inventory):
        raise ContractError("semantic embedder returned an incomplete canonical inventory")
    return {
        text: (vector, diagnostic)
        for text, vector, diagnostic in zip(inventory, vectors, diagnostics, strict=True)
    }


def compute_stage5_semantic_retrieval(
    heldout_records: Sequence[dict[str, Any]],
    replacements: Sequence[dict[str, Any]],
    source_identities: Sequence[dict[str, Any]],
    source_records: Mapping[str, Sequence[dict[str, Any]]],
    authoring_schedule_records: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Recompute the complete Stage 5 semantic inventory from canonical inputs."""

    source_by_id = {item["source_identity_id"]: item for item in source_identities}
    schedule_by_candidate = {item["candidate_id"]: item for item in authoring_schedule_records}
    candidate_text = {item["prompt_id"]: item["prompt"] for item in heldout_records}
    candidate_text.update({item["candidate_id"]: item["candidate_prompt"] for item in replacements})
    if set(candidate_text) != set(schedule_by_candidate) or set(source_records) != set(source_by_id):
        raise ContractError("semantic generator inputs do not describe one complete candidate/source inventory")

    def eligible(candidate_id: str, source_id: str) -> list[dict[str, Any]]:
        records = list(source_records[source_id])
        collection = source_by_id[source_id]["collection"]
        if collection not in {"accepted_heldout_candidates", "rejected_heldout_candidates"}:
            return records
        current_index = schedule_by_candidate[candidate_id]["authoring_index"]
        wanted_final = collection == "accepted_heldout_candidates"
        allowed = {
            item["candidate_id"] for item in authoring_schedule_records
            if item["authoring_index"] < current_index and item["final_for_slot"] is wanted_final
        }
        return [item for item in records if item["record_id"] in allowed]

    all_texts = list(candidate_text.values())
    all_texts.extend(record["text"] for records in source_records.values() for record in records)
    embedded = _embed_canonical_text_inventory(all_texts)
    output: list[dict[str, Any]] = []
    ordered_candidates = [item["candidate_id"] for item in sorted(
        authoring_schedule_records, key=lambda item: item["authoring_index"]
    )]
    for candidate_id in ordered_candidates:
        prompt = candidate_text[candidate_id]
        identity = text_identity(prompt)
        query_vector, query_diagnostic = embedded[prompt]
        for source_id in sorted(source_by_id):
            records = eligible(candidate_id, source_id)
            ranked = semantic_neighbours(
                query_vector,
                [(item["record_id"], embedded[item["text"]][0]) for item in records],
                top_k=5,
            )
            diagnostics = {
                item["record_id"]: embedded[item["text"]][1] for item in records
            }
            output.append({
                "candidate_id": candidate_id,
                "matrix_prompt_id": schedule_by_candidate[candidate_id]["matrix_prompt_id"],
                "candidate_original_sha256": identity["original_sha256"],
                "candidate_normalized_sha256": identity["normalized_sha256"],
                "candidate_pre_truncation_wordpieces": query_diagnostic["pre_truncation_wordpieces"],
                "candidate_semantic_input_truncated": query_diagnostic["semantic_input_truncated"],
                "source_identity_id": source_id,
                "source_content_sha256": source_by_id[source_id]["content_sha256"],
                "reference_diagnostics": [{
                    "reference_id": item["record_id"],
                    "reference_pre_truncation_wordpieces": diagnostics[item["record_id"]]["pre_truncation_wordpieces"],
                    "reference_semantic_input_truncated": diagnostics[item["record_id"]]["semantic_input_truncated"],
                } for item in records],
                "neighbours": [{
                    "reference_id": item["record_id"],
                    "reference_pre_truncation_wordpieces": diagnostics[item["record_id"]]["pre_truncation_wordpieces"],
                    "reference_semantic_input_truncated": diagnostics[item["record_id"]]["semantic_input_truncated"],
                    "semantic_rank": rank,
                    "semantic_score": item["semantic_score"],
                } for rank, item in enumerate(ranked, 1)],
            })
    return output


def compute_response_similarity_semantic_retrieval(
    responses: Sequence[dict[str, Any]],
    references: Mapping[str, Sequence[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Recompute response-similarity ranks, scores, and token diagnostics."""

    views = {
        item["response_id"]: response_similarity_text_view(item["raw_output"], item["parsed_response"])
        for item in responses
    }
    reference_views = {
        collection: {
            item["reference_id"]: response_similarity_text_view(item["raw_output"], item["parsed_response"])
            for item in records
        } for collection, records in references.items()
    }
    embedded = _embed_canonical_text_inventory(
        list(views.values()) + [text for values in reference_views.values() for text in values.values()]
    )
    output: list[dict[str, Any]] = []
    for response in responses:
        response_id = response["response_id"]
        view = views[response_id]
        query_vector, query_diagnostic = embedded[view]
        collections = {
            **reference_views,
            "heldout_system_responses": {
                item["response_id"]: views[item["response_id"]]
                for item in responses
                if item["system_id"] == response["system_id"] and item["response_id"] != response_id
            },
        }
        for collection in ("worked_example_responses", "training_responses", "heldout_system_responses"):
            collection_views = collections[collection]
            ranked = semantic_neighbours(
                query_vector,
                [(record_id, embedded[text][0]) for record_id, text in collection_views.items()],
                top_k=5,
            )
            diagnostics = {record_id: embedded[text][1] for record_id, text in collection_views.items()}
            output.append({
                "response_id": response_id,
                "reference_collection": collection,
                "response_pre_truncation_wordpieces": query_diagnostic["pre_truncation_wordpieces"],
                "response_semantic_input_truncated": query_diagnostic["semantic_input_truncated"],
                "reference_diagnostics": [{
                    "reference_id": record_id,
                    "reference_pre_truncation_wordpieces": diagnostic["pre_truncation_wordpieces"],
                    "reference_semantic_input_truncated": diagnostic["semantic_input_truncated"],
                } for record_id, diagnostic in diagnostics.items()],
                "neighbours": [{
                    "reference_id": item["record_id"],
                    "reference_pre_truncation_wordpieces": diagnostics[item["record_id"]]["pre_truncation_wordpieces"],
                    "reference_semantic_input_truncated": diagnostics[item["record_id"]]["semantic_input_truncated"],
                    "semantic_rank": rank,
                    "semantic_score": item["semantic_score"],
                } for rank, item in enumerate(ranked, 1)],
            })
    return output


def _semantic_generator_stdout(kind: str, records: Sequence[dict[str, Any]]) -> str:
    return canonical_json({
        "generator": "chatgnt-semantic-evidence-v1",
        "kind": kind,
        "model_id": SEMANTIC_MODEL_ID,
        "model_revision": SEMANTIC_MODEL_REVISION,
        "record_count": len(records),
        "records_sha256": canonical_records_sha256(records),
        "result": "pass",
    })


def generate_stage5_semantic_evidence(
    heldout_records: Sequence[dict[str, Any]], replacements: Sequence[dict[str, Any]],
    source_identities: Sequence[dict[str, Any]], source_records: Mapping[str, Sequence[dict[str, Any]]],
    authoring_schedule_records: Sequence[dict[str, Any]], candidate_attestations: Sequence[dict[str, Any]],
    *, artifact_id: str, verifier_identity: str, started_at_utc: str, verified_at_utc: str,
) -> dict[str, Any]:
    records = compute_stage5_semantic_retrieval(
        heldout_records, replacements, source_identities, source_records, authoring_schedule_records
    )
    stdout = _semantic_generator_stdout("stage5", records)
    manifest = validate_protocol_manifest()
    return {
        "schema_version": 1, "artifact_id": artifact_id, "status": "verified",
        "attestation_statement": "The named verifier recomputed semantic embeddings and token diagnostics from the bound complete candidate and source records, and reviewed every final candidate attestation without model outputs.",
        "protocol_aggregate_sha256": manifest["aggregate_sha256"],
        "source_identities_sha256": canonical_records_sha256(source_identities),
        "authoring_schedule_sha256": canonical_records_sha256(authoring_schedule_records),
        "embedding_model_id": SEMANTIC_MODEL_ID, "embedding_model_revision": SEMANTIC_MODEL_REVISION,
        "verifier_identity": verifier_identity,
        "verifier_command": "uv run --frozen python scripts/generate_semantic_evidence.py stage5",
        "verifier_implementation_sha256": hashlib.sha256(SEMANTIC_GENERATOR_PATH.read_bytes()).hexdigest(),
        "verifier_stdout": stdout, "verifier_stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "started_at_utc": started_at_utc, "verified_at_utc": verified_at_utc,
        "retrieval_evidence": records, "candidate_attestations": list(candidate_attestations),
    }


def generate_response_similarity_semantic_evidence(
    responses: Sequence[dict[str, Any]], references: Mapping[str, Sequence[dict[str, Any]]],
    *, artifact_id: str, verifier_identity: str, started_at_utc: str, verified_at_utc: str,
) -> dict[str, Any]:
    records = compute_response_similarity_semantic_retrieval(responses, references)
    stdout = _semantic_generator_stdout("response_similarity", records)
    flattened = [{"reference_collection": collection, **record}
                 for collection in sorted(references) for record in references[collection]]
    return {
        "schema_version": 1, "artifact_id": artifact_id, "status": "verified",
        "model_id": SEMANTIC_MODEL_ID, "model_revision": SEMANTIC_MODEL_REVISION,
        "verifier_identity": verifier_identity,
        "verifier_command": "uv run --frozen python scripts/generate_semantic_evidence.py response-similarity",
        "verifier_implementation_sha256": hashlib.sha256(SEMANTIC_GENERATOR_PATH.read_bytes()).hexdigest(),
        "verifier_stdout": stdout, "verifier_stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "started_at_utc": started_at_utc, "verified_at_utc": verified_at_utc,
        "responses_sha256": canonical_records_sha256(responses),
        "references_sha256": canonical_records_sha256(flattened), "records": records,
    }


def _validate_semantic_verifier_provenance(artifact: Mapping[str, Any], kind: str, records: Sequence[dict[str, Any]]) -> None:
    implementation = hashlib.sha256(SEMANTIC_GENERATOR_PATH.read_bytes()).hexdigest()
    if artifact["verifier_implementation_sha256"] != implementation:
        raise ContractError("semantic artifact is not bound to the canonical verifier implementation")
    stdout = artifact["verifier_stdout"]
    if artifact["verifier_stdout_sha256"] != hashlib.sha256(stdout.encode()).hexdigest():
        raise ContractError("semantic verifier stdout digest does not bind captured bytes")
    try:
        output = strict_json_loads(stdout)
    except ContractError as exc:
        raise ContractError("semantic verifier stdout is not canonical JSON evidence") from exc
    if output != strict_json_loads(_semantic_generator_stdout(kind, records)):
        raise ContractError("semantic verifier stdout does not bind the production semantic records")
    started = datetime.fromisoformat(artifact["started_at_utc"].replace("Z", "+00:00"))
    completed = datetime.fromisoformat(artifact["verified_at_utc"].replace("Z", "+00:00"))
    if started < datetime(2026,7,15,tzinfo=timezone.utc) or completed < started:
        raise ContractError("semantic verifier timing is stale or impossible")


def validate_response_similarity_records(
    responses: Sequence[dict[str, Any]],
    references: Mapping[str, Sequence[dict[str, Any]]],
    reviews: Sequence[dict[str, Any]],
    semantic_evidence: dict[str, Any],
    *, heldout_records: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Validate complete production response-similarity retrieval and review evidence."""

    _validate_records_schema(
        reviews, PROJECT_ROOT / "schemas" / "response-similarity-review-v1.schema.json", "response_similarity_reviews"
    )
    _validate_records_schema(
        [semantic_evidence], PROJECT_ROOT / "schemas" / "response-similarity-evidence-v1.schema.json", "response_similarity_evidence"
    )
    validate_heldout_records(heldout_records)
    response_keys = {"response_id", "prompt_id", "system_id", "raw_output", "parsed_response"}
    reference_keys = {"reference_id", "raw_output", "parsed_response"}
    if not responses or any(not records for records in references.values()) or any(set(item) != response_keys for item in responses) or set(references) != {
        "worked_example_responses", "training_responses"
    } or any(set(item) != reference_keys for records in references.values() for item in records):
        raise ContractError("response-similarity inputs are not closed canonical records")
    expected_population = {(item["prompt_id"], system) for item in heldout_records for system in "ABCD"}
    if len(responses) != 240 or {(item["prompt_id"], item["system_id"]) for item in responses} != expected_population:
        raise ContractError("response similarity requires the complete canonical 4x60 response population")
    response_by_id = {item["response_id"]: item for item in responses}
    if len(response_by_id) != len(responses):
        raise ContractError("response-similarity response IDs must be unique")
    response_schema, _ = read_strict_json(PROJECT_ROOT / "schemas" / "chatgnt-response-v1.schema.json")
    response_validator = Draft202012Validator(response_schema)

    def require_deterministic_parse(raw_output: Any, parsed_response: Any) -> None:
        if not isinstance(raw_output, str):
            raise ContractError("response-similarity raw output must be a string")
        try:
            parsed = strict_json_loads(raw_output)
        except ContractError:
            parsed = None
        valid = parsed is not None and not list(response_validator.iter_errors(parsed))
        if parsed_response != (parsed if valid else None):
            raise ContractError("response-similarity parsed response must be the deterministic strict parse of raw output")

    for item in responses:
        require_deterministic_parse(item["raw_output"], item["parsed_response"])
    reference_by_collection: dict[str, dict[str, dict[str, Any]]] = {}
    for collection, records in references.items():
        by_id = {item["reference_id"]: item for item in records}
        if len(by_id) != len(records):
            raise ContractError("response-similarity reference IDs must be unique within a collection")
        for item in records:
            require_deterministic_parse(item["raw_output"], item["parsed_response"])
        reference_by_collection[collection] = by_id

    flattened_references = [
        {"reference_collection":collection, **record}
        for collection in sorted(references) for record in references[collection]
    ]
    if (
        semantic_evidence["responses_sha256"] != canonical_records_sha256(responses)
        or semantic_evidence["references_sha256"] != canonical_records_sha256(flattened_references)
    ):
        raise ContractError("response semantic evidence is not bound to the actual response/reference records")

    recomputed_semantic_records = compute_response_similarity_semantic_retrieval(responses, references)
    if semantic_evidence["records"] != recomputed_semantic_records:
        raise ContractError("response semantic evidence disagrees with canonical production recomputation")
    _validate_semantic_verifier_provenance(
        semantic_evidence, "response_similarity", recomputed_semantic_records
    )

    evidence_keys = {
        "response_id", "reference_collection", "response_pre_truncation_wordpieces",
        "response_semantic_input_truncated", "reference_diagnostics", "neighbours",
    }
    evidence_neighbour_keys = {
        "reference_id", "reference_pre_truncation_wordpieces", "reference_semantic_input_truncated",
        "semantic_rank", "semantic_score",
    }
    evidence_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for item in semantic_evidence["records"]:
        if set(item) != evidence_keys or any(set(neighbour) != evidence_neighbour_keys for neighbour in item["neighbours"]):
            raise ContractError("response semantic evidence is not closed")
        key = (item["response_id"], item["reference_collection"])
        if key in evidence_by_pair:
            raise ContractError("response semantic evidence pairs must be unique")
        evidence_by_pair[key] = item

    exposure = {
        "A": set(), "B":{"worked_example_responses"}, "C":{"training_responses"},
        "D":{"worked_example_responses", "training_responses"},
    }
    review_by_key = {(item["response_id"], item["reference_collection"], item["reference_id"]):item for item in reviews}
    if len(review_by_key) != len(reviews):
        raise ContractError("response-similarity review targets must be unique")
    expected_review_keys: set[tuple[str, str, str]] = set()
    for response in responses:
        response_id = response["response_id"]
        system_id = response["system_id"]
        response_view = response_similarity_text_view(response["raw_output"], response["parsed_response"])
        response_original_sha = hashlib.sha256(response["raw_output"].encode()).hexdigest()
        response_view_sha = hashlib.sha256(response_view.encode()).hexdigest()
        collections: dict[str, Sequence[dict[str, Any]]] = {
            **references,
            "heldout_system_responses": [
                {"reference_id":item["response_id"], "raw_output":item["raw_output"], "parsed_response":item["parsed_response"]}
                for item in responses if item["system_id"] == system_id and item["response_id"] != response_id
            ],
        }
        for collection, collection_records in collections.items():
            evidence = evidence_by_pair.get((response_id, collection))
            if evidence is None:
                raise ContractError("every response/reference collection requires canonical generator-produced semantic evidence")
            corpus = [
                {"record_id":item["reference_id"], "text":response_similarity_text_view(item["raw_output"], item["parsed_response"])}
                for item in collection_records
            ]
            lexical = lexical_neighbours(response_view, corpus, 5)
            exact_ids = {item["record_id"] for item in corpus if item["text"] == response_view}
            semantic_items = evidence["neighbours"]
            reference_diagnostics = {item["reference_id"]:item for item in evidence["reference_diagnostics"]}
            expected_semantic_count = min(5, len(corpus))
            if (
                len(semantic_items) != expected_semantic_count
                or [item["semantic_rank"] for item in semantic_items] != list(range(1, expected_semantic_count + 1))
                or any(item["reference_id"] not in {record["record_id"] for record in corpus} for item in semantic_items)
                or len(reference_diagnostics) != len(evidence["reference_diagnostics"])
                or set(reference_diagnostics) != {record["record_id"] for record in corpus}
            ):
                raise ContractError(f"response semantic evidence does not contain the complete per-source top-k: {response_id}/{collection}")
            expected_ids = {item["record_id"] for item in lexical} | {
                item["reference_id"] for item in semantic_items
            } | exact_ids
            expected_review_keys.update((response_id, collection, reference_id) for reference_id in expected_ids)
            lexical_by_id = {item["record_id"]:(rank, item["lexical_score"]) for rank, item in enumerate(lexical, 1)}
            semantic_by_id = {item["reference_id"]:item for item in semantic_items}
            collection_by_id = {item["reference_id"]:item for item in collection_records}
            for reference_id in expected_ids:
                review = review_by_key.get((response_id, collection, reference_id))
                reference = collection_by_id[reference_id]
                reference_view = response_similarity_text_view(reference["raw_output"], reference["parsed_response"])
                reference_original_sha = hashlib.sha256(reference["raw_output"].encode()).hexdigest()
                reference_view_sha = hashlib.sha256(reference_view.encode()).hexdigest()
                if review is None or review["system_id"] != system_id:
                    raise ContractError("response retrieval union is missing its review or system attribution")
                expected_exposure = (
                    "within_system_diversity" if collection == "heldout_system_responses"
                    else "exposed" if collection in exposure[system_id] else "diagnostic_not_exposed"
                )
                if review["exposure_status"] != expected_exposure:
                    raise ContractError("response review exposure status disagrees with the frozen system/source mapping")
                if (
                    review["response_original_sha256"] != response_original_sha
                    or review["response_text_view_sha256"] != response_view_sha
                    or review["reference_original_sha256"] != reference_original_sha
                    or review["reference_text_view_sha256"] != reference_view_sha
                    or review["response_pre_truncation_wordpieces"] != evidence["response_pre_truncation_wordpieces"]
                    or review["response_semantic_input_truncated"] != evidence["response_semantic_input_truncated"]
                ):
                    raise ContractError("response review hashes or token diagnostics do not bind the actual text views")
                signals = set()
                if reference_id in exact_ids: signals.add("exact")
                if reference_id in lexical_by_id: signals.add("lexical")
                if reference_id in semantic_by_id: signals.add("semantic")
                if set(review["retrieval_signals"]) != signals or review["exact_text_view_match"] is not (reference_id in exact_ids):
                    raise ContractError("response review retrieval signals disagree with exact/retrieved membership")
                lexical_value = lexical_by_id.get(reference_id)
                if (
                    review["lexical_rank"] != (lexical_value[0] if lexical_value else None)
                    or review["lexical_score"] != (lexical_value[1] if lexical_value else None)
                ):
                    raise ContractError("response lexical rank/score disagrees with recomputation")
                semantic_value = semantic_by_id.get(reference_id)
                reference_diagnostic = reference_diagnostics[reference_id]
                if (
                    review["semantic_rank"] != (semantic_value["semantic_rank"] if semantic_value else None)
                    or review["semantic_score"] != (semantic_value["semantic_score"] if semantic_value else None)
                    or review["reference_pre_truncation_wordpieces"] != reference_diagnostic["reference_pre_truncation_wordpieces"]
                    or review["reference_semantic_input_truncated"] != reference_diagnostic["reference_semantic_input_truncated"]
                ):
                    raise ContractError("response semantic rank/score or token diagnostics disagree with verifier evidence")
                if reference_id in exact_ids:
                    required_decision = "generic_collapse_flag" if collection == "heldout_system_responses" else "exact_project_response"
                    if review["decision"] != required_decision:
                        raise ContractError("exact response view requires its predeclared exact-match decision")
    if set(review_by_key) != expected_review_keys or set(evidence_by_pair) != {
        (response["response_id"], collection)
        for response in responses for collection in ("worked_example_responses", "training_responses", "heldout_system_responses")
    }:
        raise ContractError("response-similarity evidence contains missing, orphaned, or extra coverage")
    return {"result":"pass", "response_count":len(responses), "review_count":len(reviews)}


def canonical_records_sha256(records: Sequence[dict[str, Any]]) -> str:
    return hashlib.sha256(b"".join(canonical_line(item) for item in records)).hexdigest()


def withheld_domain_evidence_sha256(
    source_identity: dict[str, Any], withheld_domain: str, reviewer_identity: str,
    notes: str, decision: str = "absence_confirmed",
) -> str:
    value = {
        "source_identity_id": source_identity["source_identity_id"],
        "source_content_sha256": source_identity["content_sha256"],
        "withheld_domain": withheld_domain,
        "checked_absent": True,
        "decision":decision,"reviewer_identity":reviewer_identity,"notes":notes,
        "attestation_statement":"I reviewed the complete bound source collection for the named withheld domain and found no material occurrence.",
    }
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def normative_protocol_value(value: dict[str, Any]) -> dict[str, Any]:
    """Remove lifecycle evidence so review-candidate and frozen values compare identically."""

    normalized = json.loads(canonical_json(value))
    normalized["status"] = "review_candidate"
    normalized["freeze_gate"] = {
        "independent_review_required": True,
        "review_id": None,
        "reviewer_identity": None,
        "review_verdict": None,
        "unresolved_blocking_findings": None,
        "frozen_at_utc": None,
        "review_artifact_path": None,
        "review_artifact_sha256": None,
        "verification_evidence_path": None,
        "verification_evidence_sha256": None,
        "transition_orchestrator_sha256": None,
    }
    return normalized


def protocol_normative_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(normative_protocol_value(value)).encode("utf-8")).hexdigest()


def protocol_asset_entries() -> list[dict[str, str]]:
    entries = []
    for relative in NORMATIVE_PROTOCOL_PATHS:
        path = PROJECT_ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise ContractError(f"normative protocol asset missing or empty: {relative}")
        entries.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return entries


def protocol_aggregate_sha256(entries: Sequence[dict[str, str]], normative_sha256: str) -> str:
    value = {"protocol_normative_sha256": normative_sha256, "assets": list(entries)}
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_protocol_manifest(
    path: Path = PROTOCOL_MANIFEST_PATH, protocol: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value, raw = read_strict_json(path)
    schema, _ = read_strict_json(PROJECT_ROOT / "schemas" / "evaluation-protocol-manifest-v1.schema.json")
    errors = list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        raise ContractError("protocol manifest schema failure: " + "; ".join(item.message for item in errors))
    if protocol is None:
        protocol, _ = read_strict_json(PROTOCOL_PATH)
        validate_protocol_value(protocol)
    if value["protocol_id"] != protocol["protocol_id"]:
        raise ContractError("protocol manifest protocol identity mismatch")
    normative_sha = protocol_normative_sha256(protocol)
    expected = protocol_asset_entries()
    if value["protocol_normative_sha256"] != normative_sha or value["assets"] != expected:
        raise ContractError("protocol manifest normative asset identities are stale or incomplete")
    aggregate = protocol_aggregate_sha256(expected, normative_sha)
    if value["aggregate_sha256"] != aggregate:
        raise ContractError("protocol manifest aggregate digest mismatch")
    return {
        "result":"pass", "asset_count":len(expected), "aggregate_sha256":aggregate,
        "protocol_normative_sha256":normative_sha, "manifest_sha256":hashlib.sha256(raw).hexdigest(),
    }


def validate_stage3_verification_evidence(value: dict[str, Any]) -> dict[str, Any]:
    """Bind the final ordinary, semantic, and complete-suite gate records to one reviewed package."""

    _validate_records_schema(
        [value], PROJECT_ROOT / "schemas" / "stage3-verification-evidence-v1.schema.json",
        "stage3_verification_evidence",
    )
    manifest = validate_protocol_manifest()
    if any(value[field] != manifest[expected] for field, expected in (
        ("protocol_normative_sha256", "protocol_normative_sha256"),
        ("protocol_aggregate_sha256", "aggregate_sha256"),
        ("protocol_manifest_sha256", "manifest_sha256"),
    )):
        raise ContractError("Stage 3 verification evidence names a stale normative package")
    runner_sha = hashlib.sha256((PROJECT_ROOT / "scripts" / "capture_stage3_verification.py").read_bytes()).hexdigest()
    if value["capture_runner_sha256"] != runner_sha:
        raise ContractError("Stage 3 evidence was not produced by the canonical capture runner implementation")
    expected_packages = {name:package_version(name) for name in ("jsonschema","rapidfuzz","torch","transformers")}
    if (
        value["environment"]["python"] != platform.python_version()
        or not re.fullmatch(r"uv 0\.11\.28(?: .+)?", value["environment"]["uv"])
        or value["environment"]["packages"] != expected_packages
    ):
        raise ContractError("Stage 3 evidence environment does not match the validating pinned environment")
    verifier_sha = hashlib.sha256((PROJECT_ROOT / "scripts" / "verify_evaluation_protocol.py").read_bytes()).hexdigest()
    test_entries = [
        {"path":path.relative_to(PROJECT_ROOT).as_posix(), "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted((PROJECT_ROOT / "tests").glob("test_*.py"))
    ]
    tests_sha = hashlib.sha256(canonical_json(test_entries).encode()).hexdigest()
    expected = {
        "ordinary_verifier": (
            "uv run --frozen python scripts/verify_evaluation_protocol.py", verifier_sha,
        ),
        "semantic_verifier": (
            "uv run --frozen python scripts/verify_evaluation_protocol.py --semantic", verifier_sha,
        ),
        "full_test_suite": (
            "uv run --frozen python -m unittest discover -s tests", tests_sha,
        ),
    }
    earliest = datetime(2026, 7, 15, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    observed = _utc_artifact_time(
        value["candidate_identity_observed_at_utc"], "candidate identity observation", now=now,
    )
    if observed < earliest or observed > now:
        raise ContractError("candidate identity observation has impossible or future timing")
    previous_completed = observed
    for gate, (command, implementation_sha) in expected.items():
        record = value[gate]
        if record["command"] != command or record["implementation_sha256"] != implementation_sha:
            raise ContractError(f"{gate} evidence is not bound to its canonical command and implementation")
        if record["stdout_sha256"] != hashlib.sha256(record["stdout"].encode()).hexdigest():
            raise ContractError(f"{gate} stdout digest does not bind the captured bytes")
        if record["stderr_sha256"] != hashlib.sha256(record["stderr"].encode()).hexdigest():
            raise ContractError(f"{gate} stderr digest does not bind the captured bytes")
        combined = record["stdout"] + record["stderr"]
        if (
            record["combined_output"] != combined
            or record["combined_output_sha256"] != hashlib.sha256(combined.encode()).hexdigest()
        ):
            raise ContractError(f"{gate} combined output does not follow its declared stdout-then-stderr policy")
        started = _utc_artifact_time(record["started_at_utc"], f"{gate} start", now=now)
        completed = _utc_artifact_time(record["completed_at_utc"], f"{gate} completion", now=now)
        elapsed = (completed - started).total_seconds()
        if started < previous_completed or completed <= started or completed > now:
            raise ContractError(f"{gate} has impossible or stale execution timing")
        if abs(record["duration_seconds"] - elapsed) > max(0.25, elapsed * 0.2):
            raise ContractError(f"{gate} duration does not agree with its UTC interval")
        if gate in {"ordinary_verifier", "semantic_verifier"}:
            try:
                output = strict_json_loads(record["stdout"])
            except ContractError as exc:
                raise ContractError(f"{gate} stdout is not its verifier JSON result") from exc
            semantic_executed = output.get("retrieval_calibration",{}).get("semantic",{}).get("executed")
            if output.get("result") != "pass" or semantic_executed is (gate == "ordinary_verifier"):
                raise ContractError(f"{gate} stdout does not prove the requested verifier mode passed")
            if output.get("protocol_manifest",{}).get("aggregate_sha256") != manifest["aggregate_sha256"]:
                raise ContractError(f"{gate} stdout names a stale protocol package")
        else:
            test_matches = re.findall(r"Ran\s+([1-9][0-9]*)\s+tests?", record["combined_output"])
            discovered = 0
            for path in sorted((PROJECT_ROOT / "tests").glob("test_*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                discovered += sum(
                    1 for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
                )
            if (
                test_matches != [str(discovered)]
                or len(re.findall(r"(?m)^OK\s*$", record["combined_output"])) != 1
            ):
                raise ContractError("full test-suite output does not prove the complete current suite passed")
        previous_completed = completed
    created = _utc_artifact_time(value["created_at_utc"], "verification evidence creation", now=now)
    if created < max(_utc_artifact_time(value[gate]["completed_at_utc"], f"{gate} completion", now=now) for gate in expected):
        raise ContractError("verification evidence was created before its gates completed")
    return {"result":"pass", "evidence_id":value["evidence_id"], "test_count":discovered}


def load_stage3_verification_evidence(path: Path) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Load contained canonical JSON bytes and validate their complete Stage 3 evidence contract."""

    if path.is_absolute():
        try:
            relative = path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        except ValueError as exc:
            raise ContractError("verification evidence path escapes the project root") from exc
    else:
        relative = path.as_posix()
    contained = _contained_project_path(relative)
    value, raw = read_strict_json(contained)
    result = validate_stage3_verification_evidence(value)
    return value, hashlib.sha256(raw).hexdigest(), result


def validate_protocol_value(value: Any) -> dict[str, Any]:
    protocol_schema, _ = read_strict_json(PROTOCOL_SCHEMA_PATH)
    Draft202012Validator.check_schema(protocol_schema)
    schema_errors = sorted(Draft202012Validator(protocol_schema).iter_errors(value), key=lambda item: list(item.path))
    if schema_errors:
        raise ContractError("evaluation protocol schema failure: " + "; ".join(error.message for error in schema_errors))
    expected_root = {
        "schema_version","protocol_id","status","protocol_schema_path","protocol_manifest_path","evaluation_generation_manifest_schema_path","review_artifact_schema_path","freeze_gate",
        "documentation_paths","heldout_prompt_schema_path","prompt_overlap_review_schema_path",
        "response_similarity_review_schema_path","response_similarity_evidence_schema_path","source_identity_schema_path","withheld_domain_check_schema_path","heldout_freeze_bundle_schema_path","stage5_semantic_review_schema_path","stage3_verification_evidence_schema_path",
        "qualitative_judgment_schema_path","pairwise_judgment_schema_path","heldout_replacement_schema_path",
        "qualitative_rubric_path","judge_manifest_path","judge_calibration_path","contamination_calibration_path",
        "response_similarity_calibration_path",
        "sample","withheld_domains","contamination","judging","pairwise","measurement","response_similarity","authoring",
    }
    if not isinstance(value, dict) or set(value) != expected_root:
        raise ContractError("evaluation protocol root is not closed")
    closed_sections = {
        "withheld_domains":{"domains","prompts_per_domain","prompts_per_intent_family_domain_pair","prohibited_project_collections"},
        "contamination":{"source_collections","normalization","exact_normalized_match_action","lexical","semantic","metadata","semantic_review_questions","reject_when","review"},
        "judging":{"qualitative_eligibility","primary_llm_judgments_per_eligible_response","human_calibration_response_count","human_calibration_response_allocation","human_calibration_response_ordering","human_calibration_pair_count","human_calibration_selection_seed","llm_unable_to_assess_action","second_unable_to_assess_action","human_and_llm_results_reported_separately","agreement_statistics","no_automatic_agreement_threshold"},
        "pairwise":{"primary_systems","conditional_eligibility","primary_llm_judgments_per_eligible_pair","order_seed","order_algorithm","order_balance","choices","unable_to_assess_action","human_calibration_pair_count","human_calibration_pair_allocation","human_calibration_pair_ordering","both_invalid_outcome","one_valid_outcome","primary_reports","supplementary_report"},
        "measurement":{"binary_interval","paired_difference_interval","paired_difference_direction","bootstrap_binary_unit","bootstrap_continuous_unit","bootstrap_primary_statistics","median_difference_inference","bootstrap_resamples","bootstrap_seed","latency_summaries","token_summaries","quantile_method","subgroup_intervals","missing_attempts_count_as_failures","multiple_comparison_significance_tests"},
        "response_similarity":{"reference_collections","primary_exposure_attribution","text_view","calibration_path","lexical_top_k","semantic_top_k","review_is_flag_not_proof","within_system_output_diversity_check","generic_collapse_reported_separately"},
        "authoring":{"requires_frozen_training_and_validation","requires_no_model_training","requires_no_heldout_generation","authoring_order_seed","candidate_collision_replaces","frozen_supervised_data_is_not_rewritten","replacement_reasons","freeze_assets"},
    }
    for section, keys in closed_sections.items():
        if not isinstance(value.get(section), dict) or set(value[section]) != keys:
            raise ContractError(f"evaluation protocol {section} is not closed")
    nested_sections = {
        ("contamination","lexical"):{"library","version","algorithm","top_k","license"},
        ("contamination","semantic"):{"model_id","revision","license","dimensions","maximum_wordpieces","pooling","normalization","similarity","top_k","record_pre_truncation_wordpieces","record_truncation_flag","truncated_input_action"},
        ("contamination","metadata"):{"fields","top_k"},
        ("contamination","review"):{"second_review_for","accepted_audit_fraction","accepted_audit_selection","second_reviewer_blind_to_first_decision","unresolved_action","retain_all_rationales"},
    }
    for (section, nested), keys in nested_sections.items():
        if not isinstance(value[section].get(nested), dict) or set(value[section][nested]) != keys:
            raise ContractError(f"evaluation protocol {section}.{nested} is not closed")
    if not isinstance(value, dict) or value.get("schema_version") != 1 or value.get("protocol_id") != "chatgnt-evaluation-v1":
        raise ContractError("evaluation protocol identity mismatch")
    status = value.get("status")
    if status not in ("review_candidate", "frozen"):
        raise ContractError("evaluation protocol status must be review_candidate or frozen")
    gate = value.get("freeze_gate")
    gate_fields = {
        "independent_review_required", "review_id", "reviewer_identity", "review_verdict",
        "unresolved_blocking_findings", "frozen_at_utc", "review_artifact_path", "review_artifact_sha256",
        "verification_evidence_path", "verification_evidence_sha256", "transition_orchestrator_sha256",
    }
    if not isinstance(gate, dict) or set(gate) != gate_fields or gate.get("independent_review_required") is not True:
        raise ContractError("evaluation protocol freeze gate is invalid")
    review_values = [gate[key] for key in gate_fields - {"independent_review_required"}]
    if status == "review_candidate" and any(value is not None for value in review_values):
        raise ContractError("review candidate cannot claim completed freeze evidence")
    if status == "frozen":
        if not all(isinstance(gate[key], str) and gate[key].strip() for key in (
            "review_id", "reviewer_identity", "frozen_at_utc", "review_artifact_path", "review_artifact_sha256", "verification_evidence_path",
        )):
            raise ContractError("frozen protocol requires review identity, artifact, and timestamp")
        if gate.get("review_verdict") != "pass" or gate.get("unresolved_blocking_findings") != 0:
            raise ContractError("frozen protocol requires a passing independent review with no blockers")
        _utc_artifact_time(gate["frozen_at_utc"], "Stage 3 freeze")
        if not isinstance(gate["verification_evidence_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", gate["verification_evidence_sha256"]):
            raise ContractError("frozen protocol requires a verification-evidence digest")
        orchestrator_sha = hashlib.sha256((PROJECT_ROOT / "scripts" / "orchestrate_stage3_review.py").read_bytes()).hexdigest()
        if gate["transition_orchestrator_sha256"] != orchestrator_sha:
            raise ContractError("frozen protocol does not name the canonical transition orchestrator")
        if not re.fullmatch(r"[0-9a-f]{64}", gate["review_artifact_sha256"]):
            raise ContractError("frozen protocol requires a review-artifact digest")
        _contained_project_path(gate["review_artifact_path"])
        _contained_project_path(gate["verification_evidence_path"])
    sample = value.get("sample")
    expected_sample = {
        "prompt_count": 60,
        "intent_family_each": 12,
        "reporting_slices": {"target_use": 30, "cross_domain": 15, "robustness": 15},
        "input_forms": {"question": 15, "direct_request_or_command": 30, "statement_or_fragment": 15},
        "complexity": {"standard": 40, "composed": 20},
        "composed_per_intent_family": 4,
        "composed_robustness": 15,
        "composed_non_robustness_per_intent_family": 1,
        "constraint_bearing": 10,
        "constraint_bearing_per_intent_family": 2,
        "robustness_roles": {"format_pressure": 5, "behaviour_pressure": 5, "serialization_pressure": 5},
    }
    if sample != expected_sample:
        raise ContractError("held-out sample configuration mismatch")
    withheld = value.get("withheld_domains", {})
    if (
        withheld.get("domains") != list(WITHHELD_DOMAINS)
        or withheld.get("prompts_per_domain") != 5
        or withheld.get("prompts_per_intent_family_domain_pair") != 1
    ):
        raise ContractError("withheld-domain configuration mismatch")
    semantic = value.get("contamination", {}).get("semantic", {})
    expected = (
        "sentence-transformers/all-MiniLM-L6-v2",
        "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        384,
        256,
    )
    actual = (
        semantic.get("model_id"),
        semantic.get("revision"),
        semantic.get("dimensions"),
        semantic.get("maximum_wordpieces"),
    )
    if actual != expected:
        raise ContractError("semantic retriever identity mismatch")
    lexical = value.get("contamination", {}).get("lexical", {})
    if (lexical.get("library"), lexical.get("version"), lexical.get("algorithm"), lexical.get("top_k")) != (
        "rapidfuzz", "3.14.5", "rapidfuzz.fuzz.token_ratio", 5
    ):
        raise ContractError("lexical retriever identity mismatch")
    if value.get("withheld_domains", {}).get("domains") != list(WITHHELD_DOMAINS):
        raise ContractError("withheld-domain identity mismatch")
    expected_sources = [
        "worked_examples", "prompt_development", "evaluation_calibration", "training",
        "validation", "accepted_heldout_candidates", "rejected_heldout_candidates",
    ]
    if value.get("contamination", {}).get("source_collections") != expected_sources:
        raise ContractError("contamination source-collection identity mismatch")
    expected_paths = {
        "protocol_schema_path": "schemas/evaluation-protocol-v1.schema.json",
        "protocol_manifest_path": "config/evaluation-protocol-manifest-v1.json",
        "review_artifact_schema_path": "schemas/stage3-review-artifact-v1.schema.json",
        "heldout_prompt_schema_path": "schemas/heldout-prompt-v1.schema.json",
        "prompt_overlap_review_schema_path": "schemas/prompt-overlap-review-v1.schema.json",
        "response_similarity_review_schema_path": "schemas/response-similarity-review-v1.schema.json",
        "response_similarity_evidence_schema_path": "schemas/response-similarity-evidence-v1.schema.json",
        "source_identity_schema_path": "schemas/source-identity-v1.schema.json",
        "withheld_domain_check_schema_path": "schemas/withheld-domain-check-v1.schema.json",
        "heldout_freeze_bundle_schema_path": "schemas/heldout-freeze-bundle-v1.schema.json",
        "stage5_semantic_review_schema_path": "schemas/stage5-semantic-review-v1.schema.json",
        "stage3_verification_evidence_schema_path": "schemas/stage3-verification-evidence-v1.schema.json",
        "qualitative_judgment_schema_path": "schemas/qualitative-judgment-v1.schema.json",
        "pairwise_judgment_schema_path": "schemas/pairwise-judgment-v1.schema.json",
        "heldout_replacement_schema_path": "schemas/heldout-replacement-v1.schema.json",
        "qualitative_rubric_path": "config/evaluation-rubric-v1.json",
        "judge_manifest_path": "config/judge-manifest-v1.json",
        "judge_calibration_path": "data/evaluation/judge-calibration-v1.jsonl",
        "contamination_calibration_path": "data/evaluation/contamination-calibration-v1.jsonl",
        "response_similarity_calibration_path": "data/evaluation/response-similarity-calibration-v1.jsonl",
    }
    if any(value.get(key) != path for key, path in expected_paths.items()):
        raise ContractError("evaluation protocol asset-path identity mismatch")
    sample = value.get("sample", {})
    if (
        sample.get("prompt_count"), sample.get("intent_family_each"),
        sample.get("reporting_slices"), sample.get("input_forms"), sample.get("complexity"),
        sample.get("composed_per_intent_family"), sample.get("composed_robustness"),
        sample.get("composed_non_robustness_per_intent_family"),
        sample.get("constraint_bearing"), sample.get("constraint_bearing_per_intent_family"),
        sample.get("robustness_roles"),
    ) != (
        60, 12, {"target_use": 30, "cross_domain": 15, "robustness": 15},
        {"question": 15, "direct_request_or_command": 30, "statement_or_fragment": 15},
        {"standard": 40, "composed": 20}, 4, 15, 1, 10, 2,
        {"format_pressure": 5, "behaviour_pressure": 5, "serialization_pressure": 5},
    ):
        raise ContractError("held-out sample identity mismatch")
    judging = value.get("judging", {})
    if (
        judging.get("qualitative_eligibility"),
        judging.get("primary_llm_judgments_per_eligible_response"),
        judging.get("human_calibration_response_count"),
        judging.get("human_calibration_pair_count"),
        judging.get("human_calibration_selection_seed"),
    ) != ("schema_valid_only", 1, 24, 15, 20260715):
        raise ContractError("judge protocol identity mismatch")
    pairwise = value.get("pairwise", {})
    if (
        pairwise.get("primary_systems"), pairwise.get("conditional_eligibility"),
        pairwise.get("primary_llm_judgments_per_eligible_pair"), pairwise.get("order_seed"),
        pairwise.get("order_balance"), pairwise.get("choices"),
        pairwise.get("human_calibration_pair_count"),
    ) != (
        ["B", "C"], "both_schema_valid", 1, 20260715, {"B_first": 30, "C_first": 30},
        ["response_a", "response_b", "tie"], 15,
    ):
        raise ContractError("pairwise protocol identity mismatch")
    measurement = value.get("measurement", {})
    if (
        measurement.get("binary_interval"), measurement.get("paired_difference_interval"),
        measurement.get("paired_difference_direction"), measurement.get("bootstrap_resamples"),
        measurement.get("bootstrap_seed"), measurement.get("bootstrap_binary_unit"),
        measurement.get("bootstrap_continuous_unit"), measurement.get("bootstrap_primary_statistics"),
        measurement.get("median_difference_inference"),
        measurement.get("missing_attempts_count_as_failures"),
    ) != (
        "wilson_95", "paired_nonparametric_bootstrap_percentile_95", "C_minus_B", 10000,
        20260715, "all_60_prompt_ids_with_B_and_C_values_kept_paired",
        "achieved_matched_prompt_ids_only", ["paired_rate_difference", "paired_mean_difference"],
        "descriptive_only", True,
    ):
        raise ContractError("measurement protocol identity mismatch")
    expected_exposure = {
        "A": [], "B": ["worked_example_responses"], "C": ["training_responses"],
        "D": ["worked_example_responses", "training_responses"],
    }
    if value.get("response_similarity", {}).get("primary_exposure_attribution") != expected_exposure:
        raise ContractError("response-similarity exposure identity mismatch")
    expected_view = "normalized_field_labelled_complete_schema_content_including_amounts_and_units_or_normalized_complete_raw_output_if_invalid"
    if (
        value.get("response_similarity", {}).get("text_view") != expected_view
        or value.get("response_similarity", {}).get("calibration_path") != value.get("response_similarity_calibration_path")
    ):
        raise ContractError("response-similarity view identity mismatch")
    expected_replacements = [
        "scope_or_answerability", "quota_or_metadata", "exact_collision",
        "semantic_scenario_collision", "withheld_domain_violation",
        "internal_heldout_collision", "ambiguous_or_unscorable",
    ]
    if value.get("authoring", {}).get("replacement_reasons") != expected_replacements:
        raise ContractError("held-out replacement-reason identity mismatch")
    return value


def load_protocol(path: Path = PROTOCOL_PATH) -> tuple[dict[str, Any], str]:
    value, raw = read_strict_json(path)
    validate_protocol_value(value)
    manifest = validate_protocol_manifest(PROTOCOL_MANIFEST_PATH, value)
    if value["status"] == "frozen":
        gate = value["freeze_gate"]
        artifact_path = _contained_project_path(gate["review_artifact_path"])
        artifact, artifact_raw = read_strict_json(artifact_path)
        if hashlib.sha256(artifact_raw).hexdigest() != gate["review_artifact_sha256"]:
            raise ContractError("frozen Stage 3 review artifact digest mismatch")
        _validate_records_schema(
            [artifact], PROJECT_ROOT / value["review_artifact_schema_path"], "stage3_review_artifact"
        )
        report_path = _contained_project_path(artifact["report_path"])
        if not report_path.is_file() or hashlib.sha256(report_path.read_bytes()).hexdigest() != artifact["report_sha256"]:
            raise ContractError("frozen Stage 3 review report identity mismatch")
        verification_path = _contained_project_path(gate["verification_evidence_path"])
        verification_value, verification_digest, _ = load_stage3_verification_evidence(verification_path)
        if verification_digest != gate["verification_evidence_sha256"]:
            raise ContractError("frozen Stage 3 verification evidence digest mismatch")
        if (
            artifact["review_id"] != gate["review_id"]
            or artifact["reviewer_identity"] != gate["reviewer_identity"]
            or artifact["verdict"] != gate["review_verdict"]
            or artifact["unresolved_blocking_findings"] != gate["unresolved_blocking_findings"]
            or artifact["completed_at_utc"] != gate["frozen_at_utc"]
            or artifact["reviewed_manifest_sha256"] != manifest["manifest_sha256"]
            or artifact["reviewed_aggregate_sha256"] != manifest["aggregate_sha256"]
            or artifact["verification_evidence_path"] != gate["verification_evidence_path"]
            or artifact["verification_evidence_sha256"] != gate["verification_evidence_sha256"]
            or artifact["transition_orchestrator_sha256"] != gate["transition_orchestrator_sha256"]
        ):
            raise ContractError("frozen Stage 3 review artifact does not match the protocol freeze gate")
        evidence_created = _utc_artifact_time(
            verification_value["created_at_utc"], "Stage 3 verification evidence creation",
        )
        review_completed = _utc_artifact_time(
            artifact["completed_at_utc"], "Stage 3 independent review completion",
        )
        if review_completed < evidence_created:
            raise ContractError("independent review completion predates the captured candidate verification evidence")
    if package_version("rapidfuzz") != value["contamination"]["lexical"]["version"]:
        raise ContractError("installed RapidFuzz version does not match evaluation protocol")
    return value, hashlib.sha256(raw).hexdigest()


def validate_freeze_transition(
    candidate: dict[str, Any], frozen: dict[str, Any], *, live_gate_authorization: object,
) -> dict[str, Any]:
    """Authorize a status-only transition from fresh in-process live gates.

    Stored verification JSON remains reproducibility/integrity evidence for
    ``load_protocol`` and is deliberately not accepted as authorization here.
    """

    validate_protocol_value(candidate)
    validate_protocol_value(frozen)
    if candidate["status"] != "review_candidate" or frozen["status"] != "frozen":
        raise ContractError("freeze transition requires review_candidate then frozen")
    candidate_sha = protocol_normative_sha256(candidate)
    frozen_sha = protocol_normative_sha256(frozen)
    if candidate_sha != frozen_sha:
        raise ContractError("freeze transition changed reviewed normative protocol content")
    manifest = validate_protocol_manifest(protocol=candidate)
    from scripts.capture_stage3_verification import is_live_gate_authorization
    if not is_live_gate_authorization(live_gate_authorization, candidate_sha, manifest["aggregate_sha256"]):
        raise ContractError("freeze transition requires fresh in-process live-gate authorization")
    return {"result":"pass", "protocol_normative_sha256":candidate_sha}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = strict_json_loads(line)
        if not isinstance(value, dict):
            raise ContractError(f"{path}:{line_number}: expected object")
        records.append(value)
    return records


def validate_heldout_records(records: Sequence[dict[str, Any]], schema_path: Path = HELDOUT_SCHEMA_PATH) -> dict[str, Any]:
    schema, _ = read_strict_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for index, record in enumerate(records):
        for error in sorted(validator.iter_errors(record), key=lambda item: (list(item.path), item.message)):
            errors.append(f"record[{index}]/{'/'.join(map(str, error.path))}: {error.message}")
    if errors:
        raise ContractError("held-out schema failures: " + "; ".join(errors))
    prompt_ids = [record["prompt_id"] for record in records]
    if len(prompt_ids) != len(set(prompt_ids)):
        raise ContractError("held-out prompt IDs must be unique")
    expected_ids = {f"heldout-v1-{index:03d}" for index in range(1, 61)}
    if set(prompt_ids) != expected_ids:
        raise ContractError("held-out prompt IDs must be exactly heldout-v1-001 through heldout-v1-060")
    normalized = [text_identity(record["prompt"])["normalized_sha256"] for record in records]
    if len(normalized) != len(set(normalized)):
        raise ContractError("held-out prompts contain normalized exact duplicates")
    return validate_heldout_quotas(records)


def validate_heldout_quotas(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != 60:
        raise ContractError("held-out set must contain exactly 60 prompts")
    expected = {
        "intent_family": {key: 12 for key in INTENT_FAMILIES},
        "reporting_slice": {"target_use": 30, "cross_domain": 15, "robustness": 15},
        "input_form": {"question": 15, "direct_request_or_command": 30, "statement_or_fragment": 15},
        "complexity": {"standard": 40, "composed": 20},
        "robustness_role": {"format_pressure": 5, "behaviour_pressure": 5, "serialization_pressure": 5},
        "withheld_domain": {key: 5 for key in WITHHELD_DOMAINS},
    }
    observed: dict[str, dict[str, int]] = {}
    for field, wanted in expected.items():
        counter = Counter(record[field] for record in records if record[field] is not None)
        observed[field] = dict(sorted(counter.items()))
        if counter != Counter(wanted):
            raise ContractError(f"held-out {field} quota mismatch: {dict(counter)}")
    constraints = Counter(record["intent_family"] for record in records if record["constraint_bearing"])
    if sum(constraints.values()) != 10 or constraints != Counter({key: 2 for key in INTENT_FAMILIES}):
        raise ContractError("constraint-bearing quota mismatch")
    composed = Counter(record["intent_family"] for record in records if record["complexity"] == "composed")
    if composed != Counter({key: 4 for key in INTENT_FAMILIES}):
        raise ContractError("composed complexity requires four prompts per intent family")
    if any(record["complexity"] != "composed" for record in records if record["reporting_slice"] == "robustness"):
        raise ContractError("every robustness prompt must be composed")
    for family in INTENT_FAMILIES:
        family_records = [record for record in records if record["intent_family"] == family]
        composed = [record for record in family_records if record["complexity"] == "composed"]
        non_robust_composed = [record for record in composed if record["reporting_slice"] != "robustness"]
        robustness_constraints = [
            record for record in family_records
            if record["reporting_slice"] == "robustness" and record["constraint_bearing"]
        ]
        if len(composed) != 4 or len(non_robust_composed) != 1 or not non_robust_composed[0]["constraint_bearing"]:
            raise ContractError(f"family complexity matrix mismatch: {family}")
        if len(robustness_constraints) != 1:
            raise ContractError(f"family robustness ordinary-constraint mismatch: {family}")
    family_slice = Counter((record["intent_family"], record["reporting_slice"]) for record in records)
    for family in INTENT_FAMILIES:
        if [family_slice[(family, item)] for item in ("target_use", "cross_domain", "robustness")] != [6, 3, 3]:
            raise ContractError(f"family/slice quota mismatch: {family}")
    family_robustness = Counter(
        (record["intent_family"], record["robustness_role"])
        for record in records
        if record["reporting_slice"] == "robustness"
    )
    for family in INTENT_FAMILIES:
        if any(family_robustness[(family, role)] != 1 for role in ("format_pressure", "behaviour_pressure", "serialization_pressure")):
            raise ContractError(f"family/robustness-role matrix mismatch: {family}")
    cross = Counter(
        (record["intent_family"], record["withheld_domain"])
        for record in records
        if record["reporting_slice"] == "cross_domain"
    )
    if any(cross[(family, domain)] != 1 for family in INTENT_FAMILIES for domain in WITHHELD_DOMAINS):
        raise ContractError("cross-domain matrix must contain every family/domain pair exactly once")
    robustness = Counter(
        (record["intent_family"], record["robustness_role"])
        for record in records
        if record["reporting_slice"] == "robustness"
    )
    roles = ("format_pressure", "behaviour_pressure", "serialization_pressure")
    if any(robustness[(family, role)] != 1 for family in INTENT_FAMILIES for role in roles):
        raise ContractError("robustness matrix must contain every family/role pair exactly once")
    return {"result": "pass", "prompt_count": len(records), "observed": observed}


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if (
        isinstance(successes, bool) or isinstance(total, bool)
        or not isinstance(successes, int) or not isinstance(total, int)
        or not 0 <= successes <= total or total <= 0
    ):
        raise ContractError("Wilson interval requires 0 <= successes <= positive total")
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return centre - radius, centre + radius


def _percentile_type7(values: Sequence[float], probability: float) -> float:
    if not values or not 0 <= probability <= 1:
        raise ContractError("percentile requires values and a probability in [0,1]")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def paired_bootstrap_interval(
    records: Sequence[dict[str, Any]], statistic: str, *, resamples: int = 10000, seed: int = 20260715,
) -> dict[str, Any]:
    """Return a paired C-minus-B percentile interval using prompt IDs as resampling units."""

    if statistic not in ("paired_rate_difference", "paired_mean_difference"):
        raise ContractError("unsupported paired bootstrap statistic")
    if isinstance(resamples, bool) or not isinstance(resamples, int) or resamples <= 0:
        raise ContractError("bootstrap resamples must be a positive integer")
    ids = [item.get("prompt_id") for item in records]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ContractError("paired bootstrap requires unique non-empty prompt IDs")
    if statistic == "paired_rate_difference":
        expected = {f"heldout-v1-{index:03d}" for index in range(1, 61)}
        if set(ids) != expected or len(records) != 60:
            raise ContractError("binary paired bootstrap requires all 60 preassigned prompt IDs")
    pairs: list[tuple[float, float]] = []
    for item in records:
        left, right = item.get("B"), item.get("C")
        if isinstance(left, bool):
            left = int(left)
        if isinstance(right, bool):
            right = int(right)
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise ContractError("paired bootstrap requires achieved numeric B and C values")
        if statistic == "paired_rate_difference" and (left not in (0, 1) or right not in (0, 1)):
            raise ContractError("paired rate values must be binary")
        pairs.append((float(left), float(right)))
    if not pairs:
        raise ContractError("continuous paired bootstrap requires at least one achieved matched prompt")
    estimate = sum(right - left for left, right in pairs) / len(pairs)
    generator = random.Random(seed)
    draws = []
    for _ in range(resamples):
        sample = [pairs[generator.randrange(len(pairs))] for _ in pairs]
        draws.append(sum(right - left for left, right in sample) / len(sample))
    return {
        "estimate": estimate,
        "lower_95": _percentile_type7(draws, 0.025),
        "upper_95": _percentile_type7(draws, 0.975),
        "paired_prompt_count": len(pairs),
        "resamples": resamples,
        "seed": seed,
    }


def weighted_cohens_kappa(pairs: Sequence[tuple[int | str, int | str]]) -> dict[str, Any]:
    """Linearly weighted Cohen's kappa on resolved 1–3 score pairs."""

    resolved = [(left, right) for left, right in pairs if left != "unable_to_assess" and right != "unable_to_assess"]
    if any(left not in (1, 2, 3) or right not in (1, 2, 3) for left, right in resolved):
        raise ContractError("weighted kappa accepts only scores 1, 2, 3, or unable_to_assess")
    if not resolved:
        return {"kappa": None, "paired_count": 0, "undefined_reason": "no_resolved_pairs"}
    n = len(resolved)
    observed = sum(abs(int(left) - int(right)) / 2 for left, right in resolved) / n
    left_counts = Counter(int(left) for left, _ in resolved)
    right_counts = Counter(int(right) for _, right in resolved)
    expected = sum(
        (left_counts[left] / n) * (right_counts[right] / n) * abs(left - right) / 2
        for left in (1, 2, 3) for right in (1, 2, 3)
    )
    if expected == 0:
        return {"kappa": None, "paired_count": n, "undefined_reason": "zero_expected_disagreement"}
    return {"kappa": 1 - observed / expected, "paired_count": n, "undefined_reason": None}


def validate_calibration_records(path: Path = CALIBRATION_PATH) -> dict[str, Any]:
    records = read_jsonl(path)
    required = {
        "calibration_schema_version", "case_id", "existing_id", "existing_prompt",
        "candidate_prompt", "semantic_decision", "case_type", "rationale",
    }
    types: Counter[str] = Counter()
    case_ids: set[str] = set()
    for index, record in enumerate(records):
        if set(record) != required or record["calibration_schema_version"] != 1:
            raise ContractError(f"calibration record {index} has invalid shape")
        if record["semantic_decision"] not in ("allow", "reject"):
            raise ContractError(f"calibration record {index} has invalid decision")
        if not all(isinstance(record[key], str) and record[key].strip() for key in required - {"calibration_schema_version"}):
            raise ContractError(f"calibration record {index} requires non-empty strings")
        if record["case_id"] in case_ids:
            raise ContractError("calibration case IDs must be unique")
        case_ids.add(record["case_id"])
        types[record["case_type"]] += 1
    if not records or not {"allow", "reject"} <= {record["semantic_decision"] for record in records}:
        raise ContractError("calibration must contain allow and reject cases")
    if types["supplied_text_over_256_wordpieces"] != 1:
        raise ContractError("calibration requires exactly one over-256-wordpiece supplied-text case")
    if len(records) != 12:
        raise ContractError("contamination calibration requires exactly 12 cases")
    return {"result": "pass", "case_count": len(records), "case_types": dict(sorted(types.items()))}


def validate_response_similarity_calibration(path: Path = RESPONSE_CALIBRATION_PATH) -> dict[str, Any]:
    """Check lexical-view retrieval against response-specific hard distractors."""

    records = read_jsonl(path)
    required = {
        "calibration_schema_version", "case_id", "query_response", "references", "expected_target_id",
        "hard_distractor_id", "expected_decision", "rationale",
    }
    case_ids: set[str] = set()
    response_schema, _ = read_strict_json(PROJECT_ROOT / "schemas" / "chatgnt-response-v1.schema.json")
    validator = Draft202012Validator(response_schema)
    for index, record in enumerate(records):
        if set(record) != required or record.get("calibration_schema_version") != 1:
            raise ContractError(f"response calibration record {index} has invalid shape")
        if record["case_id"] in case_ids or record.get("expected_decision") != "review_flag":
            raise ContractError("response calibration case identity or decision mismatch")
        case_ids.add(record["case_id"])
        if list(validator.iter_errors(record["query_response"])):
            raise ContractError("response calibration query must satisfy the response schema")
        references = record.get("references")
        if not isinstance(references, list) or len(references) != 6:
            raise ContractError("response calibration requires exactly six references")
        roles = Counter(item.get("role") for item in references)
        ids = [item.get("reference_id") for item in references]
        if roles != Counter({"target":1, "hard_distractor":1, "distractor":4}) or len(ids) != len(set(ids)):
            raise ContractError("response calibration roles or reference IDs mismatch")
        if any(list(validator.iter_errors(item.get("response"))) for item in references):
            raise ContractError("response calibration references must satisfy the response schema")
        role_by_id = {item["reference_id"]:item["role"] for item in references}
        if role_by_id.get(record["expected_target_id"]) != "target" or role_by_id.get(record["hard_distractor_id"]) != "hard_distractor":
            raise ContractError("response calibration target/distractor links mismatch")
        query = response_similarity_text_view("", record["query_response"])
        corpus = [
            {"record_id":item["reference_id"], "text":response_similarity_text_view("", item["response"])}
            for item in references
        ]
        ranked = [item["record_id"] for item in lexical_neighbours(query, corpus, 5)]
        if (
            record["expected_target_id"] not in ranked or record["hard_distractor_id"] not in ranked
            or ranked.index(record["expected_target_id"]) >= ranked.index(record["hard_distractor_id"])
        ):
            raise ContractError("response calibration target must outrank its hard distractor lexically")
    if len(records) != 2:
        raise ContractError("response similarity calibration requires exactly two cases")
    return {"result":"pass", "case_count":len(records), "hard_distractor_count":len(records)}


def validate_judge_calibration(path: Path = JUDGE_CALIBRATION_PATH) -> dict[str, Any]:
    records = read_jsonl(path)
    required = {"calibration_schema_version","calibration_id","kind","focus","user_prompt","candidate_response","expected","expected_choice","rationale"}
    required_focus = {"format_pressure","behaviour_pressure","compatible_content_constraint","dimension_boundary","pairwise_tie","pairwise_preference"}
    seen_ids: set[str] = set()
    focus: set[str] = set()
    response_schema, _ = read_strict_json(PROJECT_ROOT / "schemas" / "chatgnt-response-v1.schema.json")
    response_validator = Draft202012Validator(response_schema)
    score_fields = {"underlying_answer_quality", "metaphorical_coherence", "recipe_style_execution"}
    for index, record in enumerate(records):
        if set(record) != required or record.get("calibration_schema_version") != 1:
            raise ContractError(f"judge calibration record {index} has invalid shape")
        if record.get("calibration_id") in seen_ids or not isinstance(record.get("calibration_id"), str):
            raise ContractError("judge calibration IDs must be unique strings")
        seen_ids.add(record["calibration_id"]); focus.add(record.get("focus"))
        if not isinstance(record.get("user_prompt"), str) or not record["user_prompt"].strip():
            raise ContractError("judge calibration prompt must be non-empty")
        if record.get("kind") == "qualitative":
            expected = record.get("expected")
            if (
                not isinstance(record.get("candidate_response"), dict)
                or list(response_validator.iter_errors(record["candidate_response"]))
                or not isinstance(expected, dict) or set(expected) != score_fields
                or any(value not in (1, 2, 3, "unable_to_assess") for value in expected.values())
                or record.get("expected_choice") is not None
            ):
                raise ContractError("qualitative calibration shape mismatch")
        elif record.get("kind") == "pairwise":
            candidate = record.get("candidate_response")
            if (
                not isinstance(candidate, dict) or set(candidate) != {"a", "b"}
                or any(list(response_validator.iter_errors(candidate[key])) for key in ("a", "b"))
                or record.get("expected") is not None
                or record.get("expected_choice") not in ("response_a","response_b","tie")
            ):
                raise ContractError("pairwise calibration shape mismatch")
        else:
            raise ContractError("judge calibration kind mismatch")
    if len(records) != 6 or focus != required_focus:
        raise ContractError("judge calibration requires the six frozen focus cases")
    return {"result":"pass","packet_count":len(records),"focus":sorted(focus)}


def validate_judge_manifest(path: Path = PROJECT_ROOT / "config" / "judge-manifest-v1.json") -> tuple[dict[str, Any], str]:
    value, raw = read_strict_json(path)
    required = {"schema_version","judge_manifest_id","primary","session_policy","qualitative","pairwise","calibration","binding"}
    if not isinstance(value, dict) or set(value) != required or value.get("schema_version") != 1 or value.get("judge_manifest_id") != "chatgnt-judge-v1":
        raise ContractError("judge manifest identity or shape mismatch")
    if value.get("primary") != {
        "provider":"OpenAI","interface":"Codex interactive agent session","model_family":"GPT-5",
        "exact_backend_snapshot":None,
        "snapshot_disclosure":"The interface does not expose a stable exact backend snapshot; every production judgment records the exposed identity available in that session and does not invent one.",
    }:
        raise ContractError("judge primary identity mismatch")
    if value.get("pairwise", {}).get("renderer_id") != "chatgnt-pairwise-json-v1":
        raise ContractError("pairwise renderer identity mismatch")
    expected_nested = {
        "session_policy":{"one_packet_per_fresh_context","conversation_history_allowed","external_tools_allowed","system_identity_visible","prior_scores_visible","aggregate_results_visible","sampling_controls","settings_disclosure","fallback"},
        "qualitative":{"instruction","instruction_sha256","packet_template","packet_template_sha256","judgment_schema_path","rubric_path","rubric_sha256"},
        "pairwise":{"instruction","instruction_sha256","packet_template","packet_template_sha256","judgment_schema_path","renderer_id","renderer","renderer_test_vector_sha256"},
        "calibration":{"packets_path","packets_sha256","required_packet_count","required_focus","production_gate"},
        "binding":{"judgment_field","packet_field","require_exact_manifest_digest"},
    }
    for section, keys in expected_nested.items():
        if not isinstance(value.get(section), dict) or set(value[section]) != keys:
            raise ContractError(f"judge manifest {section} is not closed")
    for section in ("qualitative", "pairwise"):
        for field in ("instruction", "packet_template"):
            digest = hashlib.sha256(value[section][field].encode("utf-8")).hexdigest()
            if value[section][f"{field}_sha256"] != digest:
                raise ContractError(f"judge manifest {section} {field} digest mismatch")
    calibration_path = PROJECT_ROOT / value["calibration"]["packets_path"]
    if hashlib.sha256(calibration_path.read_bytes()).hexdigest() != value["calibration"]["packets_sha256"]:
        raise ContractError("judge calibration packet digest mismatch")
    rubric_path = PROJECT_ROOT / value["qualitative"]["rubric_path"]
    if hashlib.sha256(rubric_path.read_bytes()).hexdigest() != value["qualitative"]["rubric_sha256"]:
        raise ContractError("judge rubric digest mismatch")
    renderer_vector = {
        "garnish":"G", "method":["M1","M2"], "ingredients":[
            {"name":"N","unit":"ml","amount":5}, {"amount":2,"name":"X","unit":"dashes"},
            {"unit":"parts","amount":1,"name":"Y"},
        ], "title":"T",
    }
    if hashlib.sha256(render_pairwise_response(renderer_vector).encode()).hexdigest() != value["pairwise"]["renderer_test_vector_sha256"]:
        raise ContractError("judge packet renderer test-vector digest mismatch")
    if value["calibration"]["required_packet_count"] != 6 or value["binding"] != {
        "judgment_field":"judge_manifest_sha256","packet_field":"packet_sha256","require_exact_manifest_digest":True,
    }:
        raise ContractError("judge manifest calibration or binding mismatch")
    validate_judge_calibration(PROJECT_ROOT / value["calibration"]["packets_path"])
    return value, hashlib.sha256(raw).hexdigest()


def _validate_records_schema(records: Sequence[dict[str, Any]], schema_path: Path, label: str) -> None:
    schema, _ = read_strict_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for index, record in enumerate(records):
        for error in validator.iter_errors(record):
            errors.append(f"{label}[{index}]/{'/'.join(map(str, error.path))}: {error.message}")
    if errors:
        raise ContractError("; ".join(sorted(errors)))


def evaluation_system_configuration(value: Mapping[str, Any]) -> dict[str, Any]:
    base_keys={"system_id","adapter_enabled","prompt_asset_sha256","model_sha256","generation_config_sha256","adapter_sha256"}
    if set(value) != base_keys or value["system_id"] not in "ABCD" or value["adapter_enabled"] is not (value["system_id"] in "CD"):
        raise ContractError("evaluation system configuration is invalid")
    digest_keys={"prompt_asset_sha256","model_sha256","generation_config_sha256"}
    if any(not isinstance(value[key],str) or not re.fullmatch(r"[0-9a-f]{64}",value[key]) for key in digest_keys):
        raise ContractError("evaluation system configuration digests are invalid")
    if value["system_id"] in "AB" and value["adapter_sha256"] is not None:
        raise ContractError("base evaluation systems cannot name an adapter")
    if value["system_id"] in "CD" and (not isinstance(value["adapter_sha256"],str) or not re.fullmatch(r"[0-9a-f]{64}",value["adapter_sha256"])):
        raise ContractError("adapted evaluation systems require an adapter digest")
    base=dict(value)
    return {**base,"system_configuration_sha256":hashlib.sha256(canonical_json(base).encode()).hexdigest()}


def _formal_harness_generation(source_harness_manifest_path: str) -> dict[str, Any]:
    """Load one complete formal harness run and derive its non-callable identities."""

    manifest_path=_contained_project_path(source_harness_manifest_path)
    if manifest_path.name != "manifest.json" or not manifest_path.is_file():
        raise ContractError("formal generation provenance requires an existing contained manifest.json")
    run_dir=manifest_path.parent
    prompts_path=run_dir/"prompts.jsonl"; responses_path=run_dir/"responses.jsonl"
    if not prompts_path.is_file() or not responses_path.is_file():
        raise ContractError("formal harness evidence requires sibling prompts.jsonl and responses.jsonl")
    from .harness import inspect_run
    report=inspect_run(run_dir)
    if report.get("complete") is not True or report.get("scheduled_count") != 240 or report.get("valid_response_count") != 240:
        raise ContractError("source harness run does not pass the complete 240-attempt harness inspection")
    manifest, manifest_raw=read_strict_json(manifest_path)
    if manifest_raw != canonical_line(manifest) or manifest.get("diagnostic") is not None:
        raise ContractError("formal evaluation cannot use diagnostic or noncanonical harness evidence")
    systems=manifest["system_set"]["systems"]
    if [item["system_id"] for item in systems] != list("ABCD"):
        raise ContractError("formal evaluation harness must contain canonical systems A-D")
    if [item["adapter_enabled"] for item in systems] != [False,False,True,True]:
        raise ContractError("formal evaluation harness adapter flags must be false,false,true,true")
    if manifest.get("adapter") is None or manifest["adapter"].get("provenance") is None:
        raise ContractError("formal evaluation requires a provenance-bound unmerged adapter")

    # The formal treatment uses the repository's canonical prompt validators,
    # including their frozen byte digests and deterministic v3 assembly. A
    # self-consistent alternate five-example prompt is not the selected prompt.
    from .prompting import (
        FIVE_SHOT_PROMPT_V3, MINIMAL_PROMPT_V1,
        validate_five_shot_prompt_v3, validate_minimal_prompt,
    )
    selected_prompt_identities = {
        "minimal": validate_minimal_prompt(MINIMAL_PROMPT_V1),
        "five_shot": validate_five_shot_prompt_v3(FIVE_SHOT_PROMPT_V3),
    }

    embedded_assets=[]
    for system in systems:
        asset=system["prompt_asset"]
        asset_path=_contained_project_path(asset["source_path"])
        selected_path = MINIMAL_PROMPT_V1 if system["system_id"] in "AC" else FIVE_SHOT_PROMPT_V3
        selected_identity = selected_prompt_identities["minimal" if system["system_id"] in "AC" else "five_shot"]
        if asset_path != selected_path.resolve() or asset["source_sha256"] != selected_identity["sha256"]:
            raise ContractError(f"System {system['system_id']} does not use the exact selected prompt identity")
        source, raw=read_strict_json(asset_path)
        if hashlib.sha256(raw).hexdigest() != asset["source_sha256"]:
            raise ContractError("harness prompt asset digest does not match existing source bytes")
        expected_source={key:asset[key] for key in ("schema_version","prompt_asset_id","version","worked_example_count","content")}
        if source != expected_source:
            raise ContractError("harness prompt asset identity/content differs from its existing source")
        embedded_assets.append(expected_source)
    if embedded_assets[0] != embedded_assets[2] or embedded_assets[1] != embedded_assets[3]:
        raise ContractError("A/C and B/D must share exact prompt bytes and identity")
    if embedded_assets[0] != {"schema_version":1,"prompt_asset_id":"minimal-v1","version":"1","worked_example_count":0,"content":""}:
        raise ContractError("A/C must use the exact frozen minimal-v1 prompt")
    if (embedded_assets[1]["schema_version"],embedded_assets[1]["prompt_asset_id"],embedded_assets[1]["version"],embedded_assets[1]["worked_example_count"]) != (1,"five-shot-v3","3",5) or not embedded_assets[1]["content"]:
        raise ContractError("B/D must use the exact frozen five-shot-v3 prompt")

    system_set_path=_contained_project_path(manifest["system_set"]["source_path"])
    selected_system_set=(PROJECT_ROOT/"config/systems/evaluation-abcd-v1.json").resolve()
    if system_set_path != selected_system_set:
        raise ContractError("formal evaluation does not use the selected A-D system-set source")
    system_set, system_set_raw=read_strict_json(system_set_path)
    if hashlib.sha256(system_set_raw).hexdigest() != manifest["system_set"]["source_sha256"]:
        raise ContractError("harness system-set digest does not match existing source bytes")
    expected_system_set={"schema_version":1,"systems":[
        {"system_id":item["system_id"],
         "prompt_asset_path":"../prompts/minimal-v1.json" if item["system_id"] in "AC" else "../prompts/five-shot-v3.json",
         "adapter_enabled":item["adapter_enabled"]} for item in systems]}
    if system_set != expected_system_set:
        raise ContractError("harness system set is not the exact source of its embedded A-D configuration")

    prompt_raw=prompts_path.read_bytes(); response_raw=responses_path.read_bytes()
    if hashlib.sha256(prompt_raw).hexdigest() != manifest["prompt_set"]["frozen_sha256"]:
        raise ContractError("harness frozen prompt bytes disagree with the manifest")
    response_records=read_jsonl(responses_path)
    return {"manifest":manifest,"manifest_sha256":hashlib.sha256(manifest_raw).hexdigest(),
        "prompts_sha256":hashlib.sha256(prompt_raw).hexdigest(),
        "responses_sha256":hashlib.sha256(response_raw).hexdigest(),
        "inspection_sha256":hashlib.sha256(canonical_json(report).encode()).hexdigest(),
        "response_records":response_records}


def _formal_evaluation_systems(harness: Mapping[str, Any]) -> list[dict[str, Any]]:
    manifest=harness["manifest"]
    runtime_sha=hashlib.sha256(canonical_json({"configuration":manifest["configuration"],
        "timing":manifest["timing"],"tokenizer":manifest["tokenizer"]}).encode()).hexdigest()
    adapter_sha=manifest["adapter"]["adapter_digest"]
    return [evaluation_system_configuration({"system_id":item["system_id"],
        "adapter_enabled":item["adapter_enabled"],"prompt_asset_sha256":item["prompt_asset"]["source_sha256"],
        "model_sha256":manifest["model"]["weights_sha256"],"generation_config_sha256":runtime_sha,
        "adapter_sha256":adapter_sha if item["adapter_enabled"] else None}) for item in manifest["system_set"]["systems"]]


def evaluation_run_records_from_harness(
    heldout_records: Sequence[dict[str, Any]], source_harness_manifest_path: str,
) -> list[dict[str, Any]]:
    """Project the inspected harness outputs into the closed judgment input format."""

    validate_heldout_records(heldout_records)
    harness=_formal_harness_generation(source_harness_manifest_path); manifest=harness["manifest"]
    systems=_formal_evaluation_systems(harness); heldout_sha=canonical_records_sha256(heldout_records)
    run_config_sha=evaluation_run_configuration_sha256(manifest["run_id"],harness["manifest_sha256"],heldout_sha,systems)
    system_by_id={item["system_id"]:item for item in systems}
    heldout_by_id={item["prompt_id"]:item for item in heldout_records}
    if set(manifest["prompt_set"]["prompt_ids"]) != set(heldout_by_id):
        raise ContractError("formal harness prompt IDs do not equal the frozen held-out population")
    harness_prompts=read_jsonl(_contained_project_path(source_harness_manifest_path).parent/"prompts.jsonl")
    if {item["prompt_id"]:item["prompt"] for item in harness_prompts} != {key:value["prompt"] for key,value in heldout_by_id.items()}:
        raise ContractError("formal harness user-prompt bytes differ from the frozen held-out population")
    response_schema,_=read_strict_json(PROJECT_ROOT/"schemas"/"chatgnt-response-v1.schema.json")
    validator=Draft202012Validator(response_schema); records=[]
    for source in harness["response_records"]:
        raw=source["raw_output"] if isinstance(source["raw_output"],str) else ""
        try: parsed=strict_json_loads(raw)
        except ContractError: parsed=None
        valid=parsed is not None and not list(validator.iter_errors(parsed))
        response_id=f"response-{source['system_id']}-{source['prompt_id']}"
        records.append({"run_id":manifest["run_id"],"run_configuration_sha256":run_config_sha,
            "system_configuration_sha256":system_by_id[source["system_id"]]["system_configuration_sha256"],
            "attempt_index":source["attempt_index"],"prompt_id":source["prompt_id"],"system_id":source["system_id"],
            "response_id":response_id,"raw_output":raw,"parsed_response":parsed if valid else None,
            "schema_valid":valid,"response_sha256":hashlib.sha256(raw.encode()).hexdigest()})
    return records


def evaluation_run_configuration_sha256(
    run_id: str, source_harness_manifest_sha256: str, heldout_records_sha256: str,
    systems: Sequence[dict[str, Any]],
) -> str:
    value={"run_id":run_id,"source_harness_manifest_sha256":source_harness_manifest_sha256,
        "heldout_records_sha256":heldout_records_sha256,"systems":list(systems)}
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def build_evaluation_generation_manifest(
    heldout_records: Sequence[dict[str, Any]], run_records: Sequence[dict[str, Any]], *,
    source_harness_manifest_path: str,
) -> dict[str, Any]:
    """Build the canonical evaluation extract from one formal harness run."""
    harness=_formal_harness_generation(source_harness_manifest_path); source=harness["manifest"]
    canonical_systems=_formal_evaluation_systems(harness)
    expected_records=evaluation_run_records_from_harness(heldout_records,source_harness_manifest_path)
    if list(run_records) != expected_records:
        raise ContractError("evaluation records are not the exact projection of the inspected harness outputs")
    run_id=source["run_id"]; source_harness_manifest_sha256=harness["manifest_sha256"]
    heldout_sha=canonical_records_sha256(heldout_records)
    run_config_sha=evaluation_run_configuration_sha256(run_id,source_harness_manifest_sha256,heldout_sha,canonical_systems)
    attempt_fields=("attempt_index","prompt_id","system_id","response_id","response_sha256","system_configuration_sha256")
    attempts=[{key:item[key] for key in attempt_fields} for item in run_records]
    return {"schema_version":1,"manifest_id":f"evaluation-generation-manifest-v1-{run_id}","run_id":run_id,
        "source_harness_manifest_path":source_harness_manifest_path,
        "source_harness_manifest_sha256":source_harness_manifest_sha256,"heldout_records_sha256":heldout_sha,
        "source_harness_prompts_sha256":harness["prompts_sha256"],
        "source_harness_responses_sha256":harness["responses_sha256"],
        "source_harness_inspection_sha256":harness["inspection_sha256"],
        "run_configuration_sha256":run_config_sha,"systems":canonical_systems,"scheduled_attempt_count":240,
        "attempts_sha256":canonical_records_sha256(attempts),"run_records_sha256":canonical_records_sha256(run_records)}


def build_judgment_packets(
    heldout_records: Sequence[dict[str, Any]], run_records: Sequence[dict[str, Any]],
    generation_manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    """Derive the only allowed sealed packet inventories from the full 4x60 run records."""

    validate_heldout_records(heldout_records)
    heldout_by_id = {item["prompt_id"]:item for item in heldout_records}
    _validate_records_schema([generation_manifest],PROJECT_ROOT/"schemas"/"evaluation-generation-manifest-v1.schema.json","generation_manifest")
    harness=_formal_harness_generation(generation_manifest["source_harness_manifest_path"])
    expected_records=evaluation_run_records_from_harness(heldout_records,generation_manifest["source_harness_manifest_path"])
    if list(run_records) != expected_records:
        raise ContractError("judgment run records are not the immutable inspected harness outputs")
    if (generation_manifest["source_harness_manifest_sha256"] != harness["manifest_sha256"]
        or generation_manifest["source_harness_prompts_sha256"] != harness["prompts_sha256"]
        or generation_manifest["source_harness_responses_sha256"] != harness["responses_sha256"]
        or generation_manifest["source_harness_inspection_sha256"] != harness["inspection_sha256"]
        or generation_manifest["systems"] != _formal_evaluation_systems(harness)):
        raise ContractError("evaluation generation manifest does not bind its inspected harness evidence")
    run_keys = {"run_id","run_configuration_sha256","system_configuration_sha256","attempt_index","prompt_id","system_id","response_id","raw_output","parsed_response","schema_valid","response_sha256"}
    if len(run_records) != 240 or any(set(item) != run_keys for item in run_records):
        raise ContractError("judgment input requires the closed full 4x60 run-record population")
    response_schema, _ = read_strict_json(PROJECT_ROOT / "schemas" / "chatgnt-response-v1.schema.json")
    validator = Draft202012Validator(response_schema)
    expected_pairs = {(prompt_id, system) for prompt_id in heldout_by_id for system in "ABCD"}
    by_pair = {(item["prompt_id"],item["system_id"]):item for item in run_records}
    if len(by_pair) != 240 or set(by_pair) != expected_pairs:
        raise ContractError("run records must contain every system/prompt attempt exactly once")
    if len({item["response_id"] for item in run_records}) != 240 or len({item["attempt_index"] for item in run_records}) != 240:
        raise ContractError("run response and attempt identities must be unique")
    if sorted(item["attempt_index"] for item in run_records) != list(range(240)):
        raise ContractError("formal generation attempt indices must be the complete contiguous manifest population")
    systems=generation_manifest["systems"]
    system_by_id={item["system_id"]:item for item in systems}
    expected_run_config=evaluation_run_configuration_sha256(generation_manifest["run_id"],
        generation_manifest["source_harness_manifest_sha256"],canonical_records_sha256(heldout_records),systems)
    attempts=[{key:item[key] for key in ("attempt_index","prompt_id","system_id","response_id","response_sha256","system_configuration_sha256")} for item in run_records]
    if ([item["system_id"] for item in systems] != list("ABCD")
        or generation_manifest["heldout_records_sha256"] != canonical_records_sha256(heldout_records)
        or generation_manifest["run_configuration_sha256"] != expected_run_config
        or generation_manifest["run_records_sha256"] != canonical_records_sha256(run_records)
        or generation_manifest["attempts_sha256"] != canonical_records_sha256(attempts)
        or any(item["run_id"] != generation_manifest["run_id"] or item["run_configuration_sha256"] != expected_run_config
               or item["system_configuration_sha256"] != system_by_id[item["system_id"]]["system_configuration_sha256"] for item in run_records)):
        raise ContractError("run records are spliced or disagree with their canonical formal-generation manifest")
    response_packets = []
    for prompt_number, prompt_id in enumerate(sorted(heldout_by_id), 1):
        heldout = heldout_by_id[prompt_id]
        for system_offset, system_id in enumerate("ABCD"):
            record = by_pair[(prompt_id,system_id)]
            if record["response_sha256"] != hashlib.sha256(record["raw_output"].encode()).hexdigest():
                raise ContractError("run response digest does not bind immutable raw output bytes")
            try:
                parsed = strict_json_loads(record["raw_output"])
            except ContractError:
                parsed = None
            schema_valid = parsed is not None and not list(validator.iter_errors(parsed))
            if record["parsed_response"] != (parsed if schema_valid else None) or record["schema_valid"] is not schema_valid:
                raise ContractError("parsed response must be the deterministic strict parse of raw output")
            packet_id = qualitative_packet_id(system_id,prompt_id,record["response_id"])
            packet_text = render_qualitative_packet(packet_id,heldout["prompt"],render_pairwise_response(parsed).rstrip("\n")) if schema_valid else ""
            response_packets.append({"packet_id":packet_id,"prompt_id":prompt_id,"response_id":record["response_id"],
                "system_id":system_id,"reporting_slice":heldout["reporting_slice"],"schema_valid":schema_valid,
                "user_prompt":heldout["prompt"],"response":parsed,"packet_text":packet_text,
                "packet_sha256":hashlib.sha256(packet_text.encode()).hexdigest() if schema_valid else None})
    order = pairwise_order_schedule(sorted(heldout_by_id)); order_sha=canonical_records_sha256(order)
    pair_packets=[]
    for schedule in order:
        prompt_id=schedule["prompt_id"]; a=by_pair[(prompt_id,schedule["response_a_system"])]; b=by_pair[(prompt_id,schedule["response_b_system"])]
        eligible=a["schema_valid"] and b["schema_valid"]
        packet_id=pair_packet_id(prompt_id,a["response_id"],b["response_id"])
        packet_text=render_pairwise_packet(packet_id,heldout_by_id[prompt_id]["prompt"],a["parsed_response"],b["parsed_response"]) if eligible else ""
        pair_packets.append({"packet_id":packet_id,"prompt_id":prompt_id,"reporting_slice":heldout_by_id[prompt_id]["reporting_slice"],
            "conditional_eligible":eligible,"response_a_id":a["response_id"],"response_b_id":b["response_id"],
            "response_a_system":schedule["response_a_system"],"response_b_system":schedule["response_b_system"],
            "user_prompt":heldout_by_id[prompt_id]["prompt"],"response_a":a["parsed_response"],"response_b":b["parsed_response"],
            "packet_text":packet_text,"packet_sha256":hashlib.sha256(packet_text.encode()).hexdigest() if eligible else None,
            "order_schedule_sha256":order_sha})
    return response_packets,pair_packets,order


def validate_judgment_records(
    qualitative: Sequence[dict[str, Any]], pairwise: Sequence[dict[str, Any]],
    *, heldout_records: Sequence[dict[str, Any]], run_records: Sequence[dict[str, Any]],
    generation_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Validate the complete sealed production-judgment batch and its coverage."""

    _validate_records_schema(qualitative, PROJECT_ROOT / "schemas" / "qualitative-judgment-v1.schema.json", "qualitative")
    _validate_records_schema(pairwise, PROJECT_ROOT / "schemas" / "pairwise-judgment-v1.schema.json", "pairwise")
    response_packets, pair_packets, pair_order_schedule_records = build_judgment_packets(heldout_records,run_records,generation_manifest)
    heldout_sha = canonical_records_sha256(heldout_records)
    runs_sha = canonical_records_sha256(run_records)
    generation_manifest_sha = hashlib.sha256(canonical_json(generation_manifest).encode()).hexdigest()
    manifest, actual_manifest_sha = validate_judge_manifest()
    protocol, protocol_sha = load_protocol()
    rubric_path = PROJECT_ROOT / protocol["qualitative_rubric_path"]
    rubric_sha = hashlib.sha256(rubric_path.read_bytes()).hexdigest()
    expected_order = pairwise_order_schedule([f"heldout-v1-{index:03d}" for index in range(1, 61)])
    if list(pair_order_schedule_records) != expected_order:
        raise ContractError("pair-order schedule is not the canonical 60-prompt schedule")
    order_sha = canonical_records_sha256(pair_order_schedule_records)

    response_schema, _ = read_strict_json(PROJECT_ROOT / "schemas" / "chatgnt-response-v1.schema.json")
    response_validator = Draft202012Validator(response_schema)
    response_by_packet: dict[str, dict[str, Any]] = {}
    response_keys = {
        "packet_id", "prompt_id", "response_id", "system_id", "reporting_slice", "schema_valid",
        "user_prompt", "response", "packet_text", "packet_sha256",
    }
    for packet in response_packets:
        if set(packet) != response_keys or packet["packet_id"] in response_by_packet:
            raise ContractError("qualitative packet inventory is not closed or has duplicate IDs")
        expected_id = qualitative_packet_id(packet["system_id"], packet["prompt_id"], packet["response_id"])
        if packet["packet_id"] != expected_id:
            raise ContractError("qualitative packet ID is not bound to system, prompt, and response")
        schema_valid = not list(response_validator.iter_errors(packet["response"]))
        if packet["schema_valid"] is not schema_valid:
            raise ContractError("qualitative packet schema-valid flag disagrees with the sealed response")
        if schema_valid:
            expected_text = render_qualitative_packet(
                packet["packet_id"], packet["user_prompt"], render_pairwise_response(packet["response"]).rstrip("\n")
            )
            if packet["packet_text"] != expected_text or packet["packet_sha256"] != hashlib.sha256(expected_text.encode()).hexdigest():
                raise ContractError("qualitative packet bytes or digest do not match the sealed prompt/output")
        response_by_packet[packet["packet_id"]] = packet

    schedule_by_prompt = {item["prompt_id"]: item for item in pair_order_schedule_records}
    pair_by_packet: dict[str, dict[str, Any]] = {}
    pair_keys = {
        "packet_id", "prompt_id", "reporting_slice", "conditional_eligible", "response_a_id",
        "response_b_id", "response_a_system", "response_b_system", "user_prompt", "response_a",
        "response_b", "packet_text", "packet_sha256", "order_schedule_sha256",
    }
    for packet in pair_packets:
        if set(packet) != pair_keys or packet["packet_id"] in pair_by_packet:
            raise ContractError("pair packet inventory is not closed or has duplicate IDs")
        schedule = schedule_by_prompt.get(packet["prompt_id"])
        if schedule is None or any(packet[key] != schedule[key] for key in ("response_a_system", "response_b_system")):
            raise ContractError("pair packet order disagrees with the canonical schedule")
        expected_id = pair_packet_id(packet["prompt_id"], packet["response_a_id"], packet["response_b_id"])
        if packet["packet_id"] != expected_id or packet["response_a_id"] == packet["response_b_id"]:
            raise ContractError("pair packet identities are not bound to distinct sealed responses")
        a_valid = not list(response_validator.iter_errors(packet["response_a"]))
        b_valid = not list(response_validator.iter_errors(packet["response_b"]))
        if packet["conditional_eligible"] is not (a_valid and b_valid):
            raise ContractError("pair eligibility disagrees with response schema validity")
        if packet["order_schedule_sha256"] != order_sha:
            raise ContractError("pair packet names a stale order schedule")
        if packet["conditional_eligible"]:
            expected_text = render_pairwise_packet(
                packet["packet_id"], packet["user_prompt"], packet["response_a"], packet["response_b"]
            )
            if packet["packet_text"] != expected_text or packet["packet_sha256"] != hashlib.sha256(expected_text.encode()).hexdigest():
                raise ContractError("pair packet bytes or digest do not match the sealed prompt/outputs")
        pair_by_packet[packet["packet_id"]] = packet

    for record in qualitative:
        packet = response_by_packet.get(record["packet_id"])
        if packet is None or record["prompt_id"] != packet["prompt_id"] or record["response_id"] != packet["response_id"]:
            raise ContractError("qualitative judgment does not name its sealed packet/output")
        if (
            record["protocol_sha256"] != protocol_sha or record["heldout_records_sha256"] != heldout_sha
            or record["run_records_sha256"] != runs_sha or record["generation_manifest_sha256"] != generation_manifest_sha
            or record["rubric_sha256"] != rubric_sha
            or record["judge_manifest_sha256"] != actual_manifest_sha
            or record["instruction_sha256"] != manifest["qualitative"]["instruction_sha256"]
            or record["packet_sha256"] != packet["packet_sha256"]
        ):
            raise ContractError("qualitative judgment provenance mismatch")
    for record in pairwise:
        packet = pair_by_packet.get(record["packet_id"])
        if packet is None or any(record[key] != packet[key] for key in ("prompt_id", "response_a_id", "response_b_id")):
            raise ContractError("pairwise judgment does not name its sealed packet/outputs")
        if (
            record["protocol_sha256"] != protocol_sha
            or record["heldout_records_sha256"] != heldout_sha
            or record["run_records_sha256"] != runs_sha
            or record["generation_manifest_sha256"] != generation_manifest_sha
            or record["judge_manifest_sha256"] != actual_manifest_sha
            or record["instruction_sha256"] != manifest["pairwise"]["instruction_sha256"]
            or record["renderer_id"] != manifest["pairwise"]["renderer_id"]
            or record["order_schedule_sha256"] != order_sha
            or record["packet_sha256"] != packet["packet_sha256"]
        ):
            raise ContractError("pairwise judgment provenance mismatch")

    def check_chains(records: Sequence[dict[str, Any]], value_field: str, target_fields: tuple[str, ...]) -> int:
        by_id = {record["judgment_id"]:record for record in records}
        if len(by_id) != len(records):
            raise ContractError("judgment IDs must be unique")
        unresolved = 0
        for record in records:
            if record["judgment_round"] == "second":
                prior = by_id.get(record["prior_judgment_id"])
                if prior is None or prior["judgment_round"] != "primary":
                    raise ContractError("orphan second judgment is forbidden")
        for record in records:
            if record["judgment_round"] != "primary":
                continue
            value = record[value_field]
            unable = value == "unable_to_assess" or (isinstance(value, dict) and "unable_to_assess" in value.values())
            seconds = [item for item in records if item.get("prior_judgment_id") == record["judgment_id"]]
            if unable and len(seconds) != 1:
                raise ContractError("primary unable_to_assess requires exactly one linked second judgment")
            if not unable and seconds:
                raise ContractError("resolved primary judgment cannot have an unable-to-assess second")
            if unable and record["resolution_status"] != "pending_second":
                raise ContractError("primary unable_to_assess must be pending its second judgment")
            if not unable and record["resolution_status"] != "resolved":
                raise ContractError("resolved primary judgment has an inconsistent status")
            if seconds:
                second = seconds[0]
                if any(second[field] != record[field] for field in target_fields + ("packet_id", "packet_sha256")):
                    raise ContractError("second judgment changed the sealed target")
                if second["judge_identity"] == record["judge_identity"] or second["judge_session_id"] == record["judge_session_id"]:
                    raise ContractError("second judgment must use a fresh judge and context")
                second_value = second[value_field]
                second_unable = second_value == "unable_to_assess" or (
                    isinstance(second_value, dict) and "unable_to_assess" in second_value.values()
                )
                expected_status = "unresolved" if second_unable else "resolved"
                if second["resolution_status"] != expected_status:
                    raise ContractError("second judgment resolution status disagrees with its result")
                unresolved += int(second_unable)
        return unresolved

    eligible_response_packets = {item["packet_id"] for item in response_packets if item["schema_valid"]}
    qualitative_primary = [item for item in qualitative if item["judgment_round"] == "primary"]
    if Counter(item["packet_id"] for item in qualitative_primary) != Counter({item:1 for item in eligible_response_packets}):
        raise ContractError("qualitative primary judgments do not cover every eligible response exactly once")
    expected_human_responses = select_human_response_calibration(response_packets)
    qualitative_human = [item for item in qualitative if item["judgment_round"] == "human_calibration"]
    if Counter(item["packet_id"] for item in qualitative_human) != Counter({item:1 for item in expected_human_responses}):
        raise ContractError("qualitative human judgments are not the deterministic 24-packet sample")

    eligible_pair_packets = {item["packet_id"] for item in pair_packets if item["conditional_eligible"]}
    pair_primary = [item for item in pairwise if item["judgment_round"] == "primary"]
    if Counter(item["packet_id"] for item in pair_primary) != Counter({item:1 for item in eligible_pair_packets}):
        raise ContractError("pairwise primary judgments do not cover every eligible pair exactly once")
    expected_human_prompts = set(select_human_pair_calibration(pair_packets))
    pair_human = [item for item in pairwise if item["judgment_round"] == "human_calibration"]
    if Counter(item["prompt_id"] for item in pair_human) != Counter({item:1 for item in expected_human_prompts}):
        raise ContractError("pairwise human judgments are not the deterministic 15-prompt sample")
    llm_sessions = [
        item["judge_session_id"] for item in (*qualitative, *pairwise)
        if item["judgment_round"] in ("primary", "second")
    ]
    if len(llm_sessions) != len(set(llm_sessions)):
        raise ContractError("every LLM primary/second judgment requires a fresh unique context")

    unresolved = check_chains(qualitative, "scores", ("prompt_id", "response_id")) + check_chains(
        pairwise, "choice", ("prompt_id", "response_a_id", "response_b_id")
    )
    return {
        "result":"pass", "qualitative_count":len(qualitative), "pairwise_count":len(pairwise),
        "unresolved_count":unresolved,
        "human_response_achieved":len(expected_human_responses), "human_response_shortfall":24-len(expected_human_responses),
        "human_pair_achieved":len(expected_human_prompts), "human_pair_shortfall":15-len(expected_human_prompts),
    }


def validate_stage5_freeze_bundle(
    heldout_records: Sequence[dict[str, Any]],
    prompt_reviews: Sequence[dict[str, Any]],
    replacements: Sequence[dict[str, Any]],
    source_identities: Sequence[dict[str, Any]],
    source_records: Mapping[str, Sequence[dict[str, Any]]],
    withheld_domain_checks: Sequence[dict[str, Any]],
    semantic_review_artifact: dict[str, Any],
    authoring_schedule_records: Sequence[dict[str, Any]],
    bundle: dict[str, Any],
) -> dict[str, Any]:
    """Enforce Stage 5 cross-record review, replacement, source, and freeze links."""

    validate_heldout_records(heldout_records)
    paths = {
        "reviews": PROJECT_ROOT / "schemas" / "prompt-overlap-review-v1.schema.json",
        "replacements": PROJECT_ROOT / "schemas" / "heldout-replacement-v1.schema.json",
        "sources": PROJECT_ROOT / "schemas" / "source-identity-v1.schema.json",
        "withheld": PROJECT_ROOT / "schemas" / "withheld-domain-check-v1.schema.json",
        "semantic": PROJECT_ROOT / "schemas" / "stage5-semantic-review-v1.schema.json",
        "bundle": PROJECT_ROOT / "schemas" / "heldout-freeze-bundle-v1.schema.json",
    }
    _validate_records_schema(prompt_reviews, paths["reviews"], "prompt_reviews")
    _validate_records_schema(replacements, paths["replacements"], "replacements")
    _validate_records_schema(source_identities, paths["sources"], "source_identities")
    _validate_records_schema(withheld_domain_checks, paths["withheld"], "withheld_domain_checks")
    _validate_records_schema([semantic_review_artifact], paths["semantic"], "semantic_review_artifact")
    _validate_records_schema([bundle], paths["bundle"], "bundle")

    protocol_manifest = validate_protocol_manifest()
    protocol_aggregate_sha256 = protocol_manifest["aggregate_sha256"]
    reviewed_protocol_manifest_sha256 = protocol_manifest["manifest_sha256"]

    source_by_id = {item["source_identity_id"]: item for item in source_identities}
    if len(source_by_id) != len(source_identities):
        raise ContractError("source identity IDs must be unique")
    required_collections = {
        "worked_examples", "prompt_development", "evaluation_calibration", "training", "validation",
        "accepted_heldout_candidates", "rejected_heldout_candidates",
    }
    if Counter(item["collection"] for item in source_identities) != Counter({item: 1 for item in required_collections}):
        raise ContractError("Stage 5 bundle requires exactly one identity for every frozen source collection")
    if any(item["source_identity_id"] != f"source-v1-{item['collection']}" for item in source_identities):
        raise ContractError("source identity IDs must be canonical functions of collection names")
    if set(source_records) != set(source_by_id):
        raise ContractError("Stage 5 requires canonical records for every and only frozen source identity")
    source_record_by_id: dict[str, dict[str, dict[str, Any]]] = {}
    source_record_keys = {"record_id", "text", "metadata"}
    for source_id, records in source_records.items():
        if any(set(record) != source_record_keys for record in records):
            raise ContractError("canonical source records must use the closed record_id/text/metadata shape")
        if any(
            not isinstance(record["record_id"], str) or not record["record_id"]
            or not isinstance(record["text"], str)
            or not isinstance(record["metadata"], dict)
            or set(record["metadata"]) != set(METADATA_FIELDS)
            or any(not isinstance(record["metadata"][field], str) or not record["metadata"][field].strip()
                   for field in METADATA_FIELDS[:-1])
            or not isinstance(record["metadata"]["important_constraints"], list)
            or any(not isinstance(value, str) or not value.strip() for value in record["metadata"]["important_constraints"])
            for record in records
        ):
            raise ContractError("canonical source record identity, text, or metadata is invalid")
        by_record = {record["record_id"]: record for record in records}
        if len(by_record) != len(records):
            raise ContractError("canonical source record IDs must be unique within a source")
        source_record_by_id[source_id] = by_record
        source = source_by_id[source_id]
        if source["record_count"] != len(records) or source["content_sha256"] != canonical_records_sha256(records):
            raise ContractError("source identity does not bind its canonical source records")

    expected_authoring_schedule = heldout_authoring_schedule(heldout_records, replacements)
    if list(authoring_schedule_records) != expected_authoring_schedule:
        raise ContractError("stored authoring schedule is not the seeded complete candidate schedule")
    previous=None
    for index,item in enumerate(authoring_schedule_records):
        base={key:item[key] for key in ("authoring_index","attempt_index_within_slot","matrix_prompt_id","candidate_id","final_for_slot","recorded_at_utc","previous_entry_sha256")}
        if item["authoring_index"] != index or item["previous_entry_sha256"] != previous \
            or item["entry_sha256"] != hashlib.sha256(canonical_json(base).encode()).hexdigest():
            raise ContractError("authoring ledger chain is broken or silently renumbered")
        previous=item["entry_sha256"]
    authoring_by_candidate = {item["candidate_id"]: item for item in authoring_schedule_records}
    if len(authoring_by_candidate) != len(authoring_schedule_records):
        raise ContractError("candidate IDs must be globally unique in the authoring schedule")

    prohibited_collections = {"worked_examples", "prompt_development", "evaluation_calibration", "training", "validation"}
    expected_withheld_pairs = {(domain, collection) for domain in WITHHELD_DOMAINS for collection in prohibited_collections}
    actual_withheld_pairs = {(item["withheld_domain"], item["source_collection"]) for item in withheld_domain_checks}
    if len(withheld_domain_checks) != 15 or actual_withheld_pairs != expected_withheld_pairs:
        raise ContractError("Stage 5 requires exactly one reviewer-attested absence check for every withheld-domain/source pair")
    for item in withheld_domain_checks:
        source = source_by_id.get(item["source_identity_id"])
        expected_check_id = f"withheld-check-v1-{item['withheld_domain']}-{item['source_collection']}"
        if (
            source is None or source["collection"] != item["source_collection"]
            or item["checked_absent"] is not True or item["check_id"] != expected_check_id
            or item["attestation_sha256"] != withheld_domain_evidence_sha256(
                source,item["withheld_domain"],item["reviewer_identity"],item["notes"],item["decision"])
        ):
            raise ContractError("withheld-domain check source identity relationship mismatch")

    source_identities_sha = canonical_records_sha256(source_identities)
    authoring_schedule_sha = canonical_records_sha256(authoring_schedule_records)
    if (
        semantic_review_artifact["protocol_aggregate_sha256"] != protocol_aggregate_sha256
        or semantic_review_artifact["source_identities_sha256"] != source_identities_sha
        or semantic_review_artifact["authoring_schedule_sha256"] != authoring_schedule_sha
    ):
        raise ContractError("semantic review artifact is not bound to this protocol, source set, and authoring schedule")
    final_candidate_ids = {item["prompt_id"] for item in heldout_records}
    attestations = semantic_review_artifact["candidate_attestations"]
    attestation_by_candidate = {item["candidate_id"]: item for item in attestations}
    if len(attestation_by_candidate) != len(attestations) or set(attestation_by_candidate) != final_candidate_ids:
        raise ContractError("semantic review artifact must attest every and only final held-out candidate")
    final_by_slot = {item["prompt_id"]: item for item in heldout_records}
    for candidate_id, attestation in attestation_by_candidate.items():
        candidate = final_by_slot.get(attestation["matrix_prompt_id"])
        identity = text_identity(candidate["prompt"]) if candidate is not None else None
        if (
            candidate is None or candidate_id != candidate["prompt_id"]
            or attestation["candidate_original_sha256"] != identity["original_sha256"]
            or attestation["candidate_normalized_sha256"] != identity["normalized_sha256"]
            or any(attestation[field] is not True for field in (
                "scope_fit", "complexity_correct", "underlying_task_clear", "answerable",
                "natural", "scorable", "complete_text_reviewed",
            ))
        ):
            raise ContractError("final-candidate semantic attestation is false, stale, or linked to the wrong slot")

    recomputed_semantic_records = compute_stage5_semantic_retrieval(
        heldout_records, replacements, source_identities, source_records, authoring_schedule_records
    )
    if semantic_review_artifact["retrieval_evidence"] != recomputed_semantic_records:
        raise ContractError("Stage 5 semantic evidence disagrees with canonical production recomputation")
    _validate_semantic_verifier_provenance(
        semantic_review_artifact, "stage5", recomputed_semantic_records
    )
    semantic_records = semantic_review_artifact["retrieval_evidence"]
    semantic_by_pair = {(item["candidate_id"], item["source_identity_id"]): item for item in semantic_records}
    expected_semantic_pairs = {
        (candidate_id, source_id) for candidate_id in authoring_by_candidate for source_id in source_by_id
    }
    if len(semantic_by_pair) != len(semantic_records) or set(semantic_by_pair) != expected_semantic_pairs:
        raise ContractError("semantic review artifact must contain every candidate/source pair exactly once")
    candidate_prompt_by_id = {item["prompt_id"]: item["prompt"] for item in heldout_records}
    candidate_prompt_by_id.update({item["candidate_id"]: item["candidate_prompt"] for item in replacements})

    def eligible_source_records(candidate_id: str, source_id: str) -> list[dict[str, Any]]:
        records = list(source_records[source_id])
        collection = source_by_id[source_id]["collection"]
        if collection not in {"accepted_heldout_candidates", "rejected_heldout_candidates"}:
            return records
        current_index = authoring_by_candidate[candidate_id]["authoring_index"]
        wanted_final = collection == "accepted_heldout_candidates"
        allowed_ids = {
            item["candidate_id"] for item in authoring_schedule_records
            if item["authoring_index"] < current_index and item["final_for_slot"] is wanted_final
        }
        return [record for record in records if record["record_id"] in allowed_ids]

    for (candidate_id, source_id), evidence in semantic_by_pair.items():
        candidate_text_value = candidate_prompt_by_id[candidate_id]
        candidate_identity = text_identity(candidate_text_value)
        schedule_entry = authoring_by_candidate[candidate_id]
        if (
            evidence["matrix_prompt_id"] != schedule_entry["matrix_prompt_id"]
            or evidence["candidate_original_sha256"] != candidate_identity["original_sha256"]
            or evidence["candidate_normalized_sha256"] != candidate_identity["normalized_sha256"]
            or evidence["source_content_sha256"] != source_by_id[source_id]["content_sha256"]
        ):
            raise ContractError("semantic retrieval evidence has stale candidate, slot, or source identity")
        neighbours = evidence["neighbours"]
        eligible_semantic_records = eligible_source_records(candidate_id, source_id)
        diagnostics = {item["reference_id"]:item for item in evidence["reference_diagnostics"]}
        expected_count = min(5, len(eligible_semantic_records))
        if len(neighbours) != expected_count or [item["semantic_rank"] for item in neighbours] != list(range(1, expected_count + 1)):
            raise ContractError("semantic retrieval evidence does not contain a complete ranked top-k")
        if len({item["reference_id"] for item in neighbours}) != len(neighbours):
            raise ContractError("semantic retrieval evidence contains duplicate references")
        eligible_semantic_ids = {item["record_id"] for item in eligible_semantic_records}
        if any(item["reference_id"] not in eligible_semantic_ids for item in neighbours):
            raise ContractError("semantic retrieval evidence references a record outside its bound source")
        if len(diagnostics) != len(evidence["reference_diagnostics"]) or set(diagnostics) != eligible_semantic_ids:
            raise ContractError("semantic evidence must retain token diagnostics for every eligible reference")

    review_by_id = {item["review_id"]: item for item in prompt_reviews}
    if len(review_by_id) != len(prompt_reviews):
        raise ContractError("prompt review IDs must be unique")
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    accepted_by_id = {item["prompt_id"]: item for item in heldout_records}
    replacement_text = {item["candidate_id"]: item["candidate_prompt"] for item in replacements}
    candidate_text = {**{key:value["prompt"] for key,value in accepted_by_id.items()}, **replacement_text}
    candidate_metadata = {
        **{key:{field:value[field] for field in METADATA_FIELDS} for key,value in accepted_by_id.items()},
        **{item["candidate_id"]:item["candidate_metadata"] for item in replacements},
    }
    for review in prompt_reviews:
        text = candidate_text.get(review["candidate_id"])
        if text is None:
            raise ContractError("prompt review references an unknown candidate")
        schedule_entry = authoring_by_candidate.get(review["candidate_id"])
        if schedule_entry is None or review["matrix_prompt_id"] != schedule_entry["matrix_prompt_id"]:
            raise ContractError("all candidate reviews must agree with the stored candidate/slot schedule")
        identity = text_identity(text)
        if review["candidate_original_sha256"] != identity["original_sha256"] or review["candidate_normalized_sha256"] != identity["normalized_sha256"]:
            raise ContractError("prompt review candidate identity does not match candidate text")
        if review["review_scope"] == "contamination":
            by_candidate[review["candidate_id"]].append(review)
        for neighbour in review["neighbours"]:
            if neighbour["source_identity_id"] not in source_by_id:
                raise ContractError("prompt review references an unknown source identity")
        if review["review_scope"] == "contamination":
            expected_source_ids = set(source_by_id)
            if set(review["searched_source_identity_ids"]) != expected_source_ids:
                raise ContractError("each contamination review must search every frozen source identity")
            coverage_by_source = {item["source_identity_id"]:item for item in review["retrieval_coverage"]}
            if set(coverage_by_source) != expected_source_ids or len(coverage_by_source) != len(review["retrieval_coverage"]):
                raise ContractError("contamination retrieval coverage must contain each source exactly once")
            for source_id, coverage in coverage_by_source.items():
                eligible_records = eligible_source_records(review["candidate_id"], source_id)
                expected_ids = [item["record_id"] for item in eligible_records]
                if coverage["eligible_record_ids"] != expected_ids or coverage["eligible_record_count"] != len(expected_ids):
                    raise ContractError("retrieval eligibility inventory must equal the bound canonical source records")
                if source_by_id[source_id]["collection"] in prohibited_collections and coverage["withheld_domain_checked"] is not True:
                    raise ContractError("every prohibited source retrieval requires a withheld-domain check")
                lexical = lexical_neighbours(
                    text, [{"record_id":item["record_id"], "text":item["text"]} for item in eligible_records], 5
                )
                metadata = metadata_neighbours(
                    candidate_metadata[review["candidate_id"]],
                    [{"record_id":item["record_id"], **item["metadata"]} for item in eligible_records], 5,
                )
                semantic = semantic_by_pair[(review["candidate_id"], source_id)]
                exact_ids = {
                    item["record_id"] for item in eligible_records if normalize_text(item["text"]) == identity["normalized_text"]
                }
                if (
                    coverage["lexical_returned"] != len(lexical)
                    or coverage["semantic_returned"] != len(semantic["neighbours"])
                    or coverage["metadata_returned"] != len(metadata)
                    or coverage["exact_match_count"] != len(exact_ids)
                ):
                    raise ContractError("retrieval coverage counts disagree with recomputed/bound retrieval")
                neighbours = [item for item in review["neighbours"] if item["source_identity_id"] == source_id]
                if any(item["reference_id"] not in expected_ids for item in neighbours):
                    raise ContractError("retrieved neighbour is absent from the source eligibility inventory")
                neighbour_ids = [item["reference_id"] for item in neighbours]
                if len(neighbour_ids) != len(set(neighbour_ids)):
                    raise ContractError("retrieved neighbour identities must be unique within a source")
                neighbour_by_id = {item["reference_id"]:item for item in neighbours}
                for rank, result in enumerate(lexical, 1):
                    neighbour = neighbour_by_id.get(result["record_id"])
                    if (
                        neighbour is None or "lexical" not in neighbour["retrieval_signals"]
                        or neighbour["lexical_rank"] != rank
                        or not math.isclose(neighbour["lexical_score"], result["lexical_score"], abs_tol=1e-9)
                    ):
                        raise ContractError("lexical neighbour rank/score disagrees with canonical recomputation")
                for rank, result in enumerate(metadata, 1):
                    neighbour = neighbour_by_id.get(result["record_id"])
                    if (
                        neighbour is None or "metadata" not in neighbour["retrieval_signals"]
                        or neighbour["metadata_rank"] != rank
                        or neighbour["metadata_score"] != result["metadata_score"]
                        or neighbour["matching_metadata_fields"] != result["matching_metadata_fields"]
                    ):
                        raise ContractError("metadata neighbour rank/score disagrees with canonical recomputation")
                semantic_evidence_by_id = {item["reference_id"]:item for item in semantic["neighbours"]}
                reference_diagnostics = {item["reference_id"]:item for item in semantic["reference_diagnostics"]}
                if (
                    review["candidate_pre_truncation_wordpieces"] != semantic["candidate_pre_truncation_wordpieces"]
                    or review["candidate_semantic_input_truncated"] != semantic["candidate_semantic_input_truncated"]
                ):
                    raise ContractError("candidate token diagnostics disagree with recomputed semantic evidence")
                for reference_id, result in semantic_evidence_by_id.items():
                    neighbour = neighbour_by_id.get(reference_id)
                    if (
                        neighbour is None or "semantic" not in neighbour["retrieval_signals"]
                        or neighbour["semantic_rank"] != result["semantic_rank"]
                        or not math.isclose(neighbour["semantic_score"], result["semantic_score"], abs_tol=1e-9)
                        or neighbour["reference_pre_truncation_wordpieces"] != result["reference_pre_truncation_wordpieces"]
                        or neighbour["reference_semantic_input_truncated"] != result["reference_semantic_input_truncated"]
                    ):
                        raise ContractError("semantic neighbour or token diagnostics disagree with recomputed generator evidence")
                for reference_id, neighbour in neighbour_by_id.items():
                    reference = source_record_by_id[source_id][reference_id]
                    reference_identity = text_identity(reference["text"])
                    reference_diagnostic = reference_diagnostics[reference_id]
                    actual_exact = reference_id in exact_ids
                    if (
                        neighbour["reference_original_sha256"] != reference_identity["original_sha256"]
                        or neighbour["reference_normalized_sha256"] != reference_identity["normalized_sha256"]
                        or neighbour["exact_normalized_match"] is not actual_exact
                        or (("exact" in neighbour["retrieval_signals"]) is not actual_exact)
                        or neighbour["reference_pre_truncation_wordpieces"] != reference_diagnostic["reference_pre_truncation_wordpieces"]
                        or neighbour["reference_semantic_input_truncated"] != reference_diagnostic["reference_semantic_input_truncated"]
                    ):
                        raise ContractError("neighbour identity or exact-match signal disagrees with canonical text")
                    if actual_exact and neighbour["decision"] != "reject":
                        raise ContractError("an exact normalized match must be rejected")
                if not exact_ids.issubset(neighbour_by_id):
                    raise ContractError("all exact normalized matches must be present in the review")
                required_neighbour_ids = (
                    {item["record_id"] for item in lexical}
                    | {item["record_id"] for item in metadata}
                    | set(semantic_evidence_by_id) | exact_ids
                )
                if set(neighbour_by_id) != required_neighbour_ids:
                    raise ContractError("review neighbours must equal the exact union of retrieval outputs")
            has_exact = any(item["exact_normalized_match"] for item in review["neighbours"])
            if has_exact and review["decision"] != "reject":
                raise ContractError("a contamination review with an exact match must reject the candidate")
            decisions = [item["decision"] for item in review["neighbours"]]
            if review["decision"] == "allow" and any(item != "allow" for item in decisions):
                raise ContractError("allow review cannot contain a non-allow neighbour")
            if review["decision"] == "reject" and "reject" not in decisions:
                raise ContractError("reject review requires a rejected neighbour")
            if review["decision"] == "uncertain" and "uncertain" not in decisions:
                raise ContractError("uncertain review requires an uncertain neighbour")

    selection_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for review in prompt_reviews:
        if review["review_scope"] == "selection":
            selection_by_candidate[review["candidate_id"]].append(review)
    selection_final_decisions: dict[str, str] = {}
    for candidate_id, reviews in selection_by_candidate.items():
        primary = [item for item in reviews if item["review_round"] == "primary"]
        second = [item for item in reviews if item["review_round"] == "second"]
        adjudication = [item for item in reviews if item["review_round"] == "adjudication"]
        if len(primary) != 1 or primary[0]["trigger"] != "routine" or primary[0]["prior_review_ids"]:
            raise ContractError(f"{candidate_id}: selection requires one correctly shaped primary review")
        needs_second = primary[0]["decision"] in ("reject","uncertain") or bool(second)
        if needs_second and len(second) != 1:
            raise ContractError(f"{candidate_id}: selection rejection/uncertainty requires exactly one second review")
        if second:
            expected_trigger = "selection_rejection" if primary[0]["decision"] == "reject" else (
                "uncertainty_resolution" if primary[0]["decision"] == "uncertain" else "accepted_audit"
            )
            if (second[0]["trigger"] != expected_trigger or second[0]["prior_review_ids"] != [primary[0]["review_id"]]
                or not second[0]["blind_to_prior_decision"]
                or second[0]["reviewer_identity"] == primary[0]["reviewer_identity"]):
                raise ContractError(f"{candidate_id}: invalid independent selection second review")
        direct = bool(second) and primary[0]["decision"] == second[0]["decision"] and primary[0]["decision"] in ("allow","reject")
        if second and not direct:
            if (len(adjudication) != 1 or adjudication[0]["trigger"] != "disagreement"
                or set(adjudication[0]["prior_review_ids"]) != {primary[0]["review_id"],second[0]["review_id"]}
                or adjudication[0]["decision"] not in ("allow","reject")
                or adjudication[0]["reviewer_identity"] in {primary[0]["reviewer_identity"],second[0]["reviewer_identity"]}):
                raise ContractError(f"{candidate_id}: selection disagreement requires independent adjudication")
            selection_final_decisions[candidate_id]=adjudication[0]["decision"]
        elif adjudication:
            raise ContractError(f"{candidate_id}: unexpected selection adjudication")
        else:
            selection_final_decisions[candidate_id]=second[0]["decision"] if direct else primary[0]["decision"]

    final_decisions: dict[str, str] = {}
    if set(by_candidate) != set(authoring_by_candidate):
        raise ContractError("every scheduled candidate requires exactly one complete contamination review chain")
    for candidate_id, reviews in by_candidate.items():
        primary = [item for item in reviews if item["review_round"] == "primary"]
        second = [item for item in reviews if item["review_round"] == "second"]
        adjudication = [item for item in reviews if item["review_round"] == "adjudication"]
        if len(primary) != 1 or primary[0]["trigger"] != "routine" or primary[0]["prior_review_ids"] or primary[0]["blind_to_prior_decision"]:
            raise ContractError(f"{candidate_id}: requires one correctly shaped primary review")
        needs_second = primary[0]["decision"] in ("reject", "uncertain") or bool(second)
        if needs_second and len(second) != 1:
            raise ContractError(f"{candidate_id}: requires exactly one second review")
        if second:
            expected_trigger = "accepted_audit" if primary[0]["decision"] == "allow" else (
                "rejection_confirmation" if primary[0]["decision"] == "reject" else "uncertainty_resolution"
            )
            if (
                second[0]["trigger"] != expected_trigger or not second[0]["blind_to_prior_decision"]
                or second[0]["prior_review_ids"] != [primary[0]["review_id"]]
                or second[0]["reviewer_identity"] == primary[0]["reviewer_identity"]
            ):
                raise ContractError(f"{candidate_id}: invalid independent second review")
        direct_agreement = bool(second) and primary[0]["decision"] == second[0]["decision"] and primary[0]["decision"] in ("allow", "reject")
        needs_adjudication = bool(second) and not direct_agreement
        if needs_adjudication:
            if (
                len(adjudication) != 1 or adjudication[0]["trigger"] != "disagreement"
                or set(adjudication[0]["prior_review_ids"]) != {primary[0]["review_id"], second[0]["review_id"]}
                or adjudication[0]["decision"] not in ("allow", "reject")
                or adjudication[0]["reviewer_identity"] in {primary[0]["reviewer_identity"], second[0]["reviewer_identity"]}
            ):
                raise ContractError(f"{candidate_id}: disagreement requires linked adjudication")
            final_decisions[candidate_id] = adjudication[0]["decision"]
        elif adjudication:
            raise ContractError(f"{candidate_id}: unexpected adjudication")
        elif direct_agreement:
            final_decisions[candidate_id] = primary[0]["decision"]
        else:
            final_decisions[candidate_id] = primary[0]["decision"]

    accepted_ids = [item["prompt_id"] for item in heldout_records]
    if any(final_decisions.get(item) != "allow" or selection_final_decisions.get(item,"allow") != "allow" for item in accepted_ids):
        raise ContractError("every accepted held-out prompt requires a resolved allow decision")
    expected_audit_slots = set(accepted_audit_ids(accepted_ids))
    expected_audits = {(slot, final_by_slot[slot]["prompt_id"]) for slot in expected_audit_slots}
    actual_audits = {
        (item["matrix_prompt_id"], item["candidate_id"]) for item in prompt_reviews
        if item["review_round"] == "second" and item["trigger"] == "accepted_audit"
    }
    if actual_audits != expected_audits:
        raise ContractError("accepted audit must attach to the final candidate in each deterministic slot")

    replacement_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in replacements:
        replacement_by_candidate[item["candidate_id"]].append(item)
        final_candidate = final_by_slot.get(item["matrix_prompt_id"])
        if (
            item["replacement_status"] != "replaced" or final_candidate is None
            or item["replacement_candidate_id"] != final_candidate["prompt_id"]
            or item["replacement_candidate_id"] == item["candidate_id"]
        ):
            raise ContractError("replacement must be non-self and point to the final candidate in the same slot")
        cited = [review_by_id.get(review_id) for review_id in item["review_ids"]]
        if any(review is None for review in cited) or any(
            review["candidate_id"] != item["candidate_id"] or review["matrix_prompt_id"] != item["matrix_prompt_id"]
            for review in cited
        ):
            raise ContractError("replacement review IDs must belong to the rejected candidate and slot")
        item_identity = text_identity(item["candidate_prompt"])
        if item["original_sha256"] != item_identity["original_sha256"] or item["normalized_sha256"] != item_identity["normalized_sha256"]:
            raise ContractError("replacement candidate hashes do not match its canonical prompt")
        contamination_reviews = by_candidate.get(item["candidate_id"], [])
        contamination_reject = final_decisions.get(item["candidate_id"]) == "reject"
        selection_reject = selection_final_decisions.get(item["candidate_id"]) == "reject"
        selection_reasons = {"scope_or_answerability","quota_or_metadata","ambiguous_or_unscorable"}
        contamination_reasons = {"exact_collision","semantic_scenario_collision","withheld_domain_violation","internal_heldout_collision"}
        if selection_reject and not contamination_reject:
            if item["reason"] not in selection_reasons or item["retrieval_report_sha256"] is not None or item["source_identity_ids"] or item["retrieved_reference_ids"]:
                raise ContractError("selection-only replacement must use a selection reason and no fabricated retrieval evidence")
        else:
            if item["reason"] not in contamination_reasons or item["retrieval_report_sha256"] != canonical_records_sha256(contamination_reviews):
                raise ContractError("contamination replacement reason/evidence does not bind its review chain")
        decisive_neighbours = [
            neighbour for review in contamination_reviews for neighbour in review["neighbours"]
            if neighbour["decision"] in ("reject", "uncertain")
        ]
        if (
            set(item["source_identity_ids"]) != {neighbour["source_identity_id"] for neighbour in decisive_neighbours}
            or set(item["retrieved_reference_ids"]) != {neighbour["reference_id"] for neighbour in decisive_neighbours}
        ):
            raise ContractError("replacement source/reference links do not match its decisive retrieval evidence")
    rejected_ids = ({item for item, decision in final_decisions.items() if decision == "reject"}
        | {item for item, decision in selection_final_decisions.items() if decision == "reject"})
    if set(replacement_by_candidate) != rejected_ids or any(len(items) != 1 for items in replacement_by_candidate.values()):
        raise ContractError("every and only finally rejected candidate requires one replacement link")

    source_by_collection = {item["collection"]:item for item in source_identities}
    accepted_source_id = source_by_collection["accepted_heldout_candidates"]["source_identity_id"]
    rejected_source_id = source_by_collection["rejected_heldout_candidates"]["source_identity_id"]
    expected_accepted_source = [
        {"record_id":item["prompt_id"], "text":item["prompt"],
         "metadata":{field:item[field] for field in METADATA_FIELDS}}
        for item in heldout_records
    ]
    expected_rejected_source = [
        {"record_id":item["candidate_id"], "text":item["candidate_prompt"],
         "metadata":{field:item["candidate_metadata"][field] for field in METADATA_FIELDS}}
        for item in replacements
    ]
    if list(source_records[accepted_source_id]) != expected_accepted_source or list(source_records[rejected_source_id]) != expected_rejected_source:
        raise ContractError("accepted/rejected canonical source records do not equal the frozen candidate records")

    flattened_source_records = [
        {"source_identity_id":source_id, **record}
        for source_id in sorted(source_records) for record in source_records[source_id]
    ]
    expected_hashes = {
        "heldout_prompts_sha256": canonical_records_sha256(heldout_records),
        "prompt_reviews_sha256": canonical_records_sha256(prompt_reviews),
        "replacement_log_sha256": canonical_records_sha256(replacements),
        "source_identities_sha256": canonical_records_sha256(source_identities),
        "source_records_sha256": canonical_records_sha256(flattened_source_records),
        "withheld_domain_checks_sha256": canonical_records_sha256(withheld_domain_checks),
        "semantic_review_artifact_sha256": hashlib.sha256(canonical_json(semantic_review_artifact).encode()).hexdigest(),
        "authoring_schedule_sha256": authoring_schedule_sha,
        "pair_order_schedule_sha256": canonical_records_sha256(pairwise_order_schedule(accepted_ids)),
    }
    if (
        bundle.get("protocol_aggregate_sha256") != protocol_aggregate_sha256
        or bundle.get("reviewed_protocol_manifest_sha256") != reviewed_protocol_manifest_sha256
        or any(bundle.get(key) != digest for key, digest in expected_hashes.items())
    ):
        raise ContractError("Stage 5 freeze bundle digest relationship mismatch")
    if set(bundle["source_identity_ids"]) != set(source_by_id):
        raise ContractError("Stage 5 freeze bundle source identity relationship mismatch")
    if bundle.get("rejected_candidate_count") != len(rejected_ids):
        raise ContractError("Stage 5 freeze bundle rejected-candidate count mismatch")
    if (
        bundle.get("accepted_prompt_count") != 60 or bundle.get("accepted_audit_count") != 6
        or bundle.get("withheld_domain_check_count") != 15 or bundle.get("pair_order_count") != 60
        or bundle.get("model_training_started") is not False or bundle.get("heldout_generation_started") is not False
    ):
        raise ContractError("Stage 5 freeze bundle count or leakage gate mismatch")
    expected_attestation="I reviewed the complete append-only authoring ledger and attest that it contains every candidate attempt, including rejected attempts, in actual authoring order."
    if (bundle["authoring_ledger_entry_count"] != len(authoring_schedule_records)
        or bundle["authoring_ledger_final_entry_sha256"] != authoring_schedule_records[-1]["entry_sha256"]
        or not bundle["authoring_ledger_reviewer_identity"].strip()
        or bundle["authoring_ledger_attestation"] != expected_attestation):
        raise ContractError("authoring ledger lacks its complete-history reviewer attestation")

    # The Stage 5 history is one coherent UTC timeline. Equality is allowed for
    # operations captured at the same clock resolution; reversal and future
    # dating are not.
    now=datetime.now(timezone.utc)
    source_times={item["source_identity_id"]:_utc_artifact_time(item["frozen_at_utc"],f"{item['source_identity_id']} freeze",now=now)
        for item in source_identities}
    ledger_times=[_utc_artifact_time(item["recorded_at_utc"],f"authoring ledger {item['authoring_index']}",now=now)
        for item in authoring_schedule_records]
    if ledger_times != sorted(ledger_times):
        raise ContractError("authoring ledger timestamps must be nondecreasing")
    first_ledger,last_ledger=ledger_times[0],ledger_times[-1]
    for source_id,source_time in source_times.items():
        collection=source_by_id[source_id]["collection"]
        if collection in prohibited_collections and source_time > first_ledger:
            raise ContractError("prohibited source collections must freeze before held-out authoring begins")
        if collection in {"accepted_heldout_candidates","rejected_heldout_candidates"} and source_time < last_ledger:
            raise ContractError("candidate source collections cannot freeze before authoring completes")
    withheld_times=[]
    for item in withheld_domain_checks:
        attested=_utc_artifact_time(item["attested_at_utc"],item["check_id"],now=now); withheld_times.append(attested)
        if attested < source_times[item["source_identity_id"]] or attested > first_ledger:
            raise ContractError("withheld-domain attestation must follow source freeze and precede authoring")
    review_times={item["review_id"]:_utc_artifact_time(item["reviewed_at_utc"],item["review_id"],now=now) for item in prompt_reviews}
    for item in prompt_reviews:
        if review_times[item["review_id"]] < _utc_artifact_time(
            authoring_by_candidate[item["candidate_id"]]["recorded_at_utc"],item["candidate_id"],now=now
        ) or any(review_times[prior] > review_times[item["review_id"]] for prior in item["prior_review_ids"]):
            raise ContractError("prompt review chronology precedes its candidate or prior review")
    replacement_times=[]
    for item in replacements:
        recorded=_utc_artifact_time(item["recorded_at_utc"],item["replacement_record_id"],now=now); replacement_times.append(recorded)
        if any(review_times[review_id] > recorded for review_id in item["review_ids"]):
            raise ContractError("replacement record predates one of its cited decisions")
    ledger_attested=_utc_artifact_time(bundle["authoring_ledger_attested_at_utc"],"authoring ledger attestation",now=now)
    if ledger_attested < last_ledger:
        raise ContractError("authoring ledger cannot be attested before its final entry")
    semantic_started=_utc_artifact_time(semantic_review_artifact["started_at_utc"],"semantic verification start",now=now)
    semantic_verified=_utc_artifact_time(semantic_review_artifact["verified_at_utc"],"semantic verification completion",now=now)
    prerequisites=[*source_times.values(),*ledger_times,*withheld_times,*review_times.values(),*replacement_times,ledger_attested]
    if semantic_started < max(prerequisites) or semantic_verified < semantic_started:
        raise ContractError("semantic verification must follow all bound authoring and review evidence")
    bundle_frozen=_utc_artifact_time(bundle["frozen_at_utc"],"held-out bundle freeze",now=now)
    if bundle_frozen < semantic_verified:
        raise ContractError("held-out bundle cannot freeze before semantic verification completes")
    return {
        "result":"pass", "accepted_prompt_count":60, "accepted_audit_count":6,
        "rejected_candidate_count":len(rejected_ids), "source_identity_count":len(source_identities),
    }
