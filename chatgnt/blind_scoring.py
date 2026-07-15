"""Prepare identity-blinded qualitative scoring packets."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .records import ContractError, canonical_json, canonical_line, strict_json_loads


RUBRIC = {
    "schema_version": 1,
    "instruction": "Score each dimension independently. Use only the user prompt, candidate response, and these anchors. Record unable_to_assess instead of guessing.",
    "dimensions": {
        "underlying_answer_quality": {
            "question": "Would the substance be a good response to the user's prompt without relying on the novelty of the cocktail format?",
            "1": "Does not meaningfully fulfil the prompt. A materially incorrect response must receive 1.",
            "2": "Gives a sound, relevant response with noticeable limitations.",
            "3": "Fully fulfils the prompt with specific, effective content.",
        },
        "metaphorical_coherence": {
            "question": "Do the recipe elements meaningfully represent and develop the underlying answer?",
            "1": "Recipe elements feel arbitrary or disconnected.",
            "2": "The metaphor generally works but contains weaker elements.",
            "3": "The complete recipe forms one meaningful, well-developed metaphor.",
        },
        "recipe_style_execution": {
            "question": "Does the response sustain a concise, natural cocktail-recipe voice without becoming ordinary prose, forced wordplay, or repetitive?",
            "1": "The recipe voice is absent, inconsistent, or badly forced.",
            "2": "The recipe voice is clear and readable, with some awkward or generic phrasing.",
            "3": "The recipe voice is natural, concise, playful, and strengthens the answer.",
        },
    },
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = strict_json_loads(line)
        if not isinstance(value, dict):
            raise ContractError(f"{path}:{line_number}: expected object")
        result.append(value)
    return result


def prepare_blind_packets(
    sources: list[tuple[str, Path, Path]],
    output_dir: Path,
    judge_seed: int = 20260715,
    system_id: str = "B",
) -> dict[str, Any]:
    """Create shuffled packets and a separate sealed identity mapping."""

    if output_dir.exists():
        raise ContractError(f"blind scoring directory already exists: {output_dir}")
    packets: list[dict[str, Any]] = []
    mapping: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for source_label, run_dir, evaluation_dir in sources:
        prompts = {item["prompt_id"]: item["prompt"] for item in _read_jsonl(run_dir / "prompts.jsonl")}
        responses = {
            (item["attempt_index"], item["system_id"]): item
            for item in _read_jsonl(run_dir / "responses.jsonl")
        }
        validations = _read_jsonl(evaluation_dir / "validations.jsonl")
        for derived in validations:
            validation = derived.get("validation")
            if derived.get("system_id") != system_id or not isinstance(validation, dict) or validation.get("schema_valid") is not True:
                continue
            key = (derived["attempt_index"], derived["system_id"])
            response = responses.get(key)
            if response is None or not isinstance(response.get("raw_output"), str):
                raise ContractError(f"missing source response for {source_label}:{key}")
            identity = canonical_json(
                {
                    "judge_seed": judge_seed,
                    "source_label": source_label,
                    "source_run_id": derived["source_run_id"],
                    "attempt_index": derived["attempt_index"],
                    "raw_output_sha256": derived["source_raw_output_sha256"],
                }
            )
            blind_id = "judge-v1-" + hashlib.sha256(identity.encode()).hexdigest()[:12]
            if blind_id in seen_ids:
                raise ContractError("blind ID collision")
            seen_ids.add(blind_id)
            prompt_id = derived["prompt_id"]
            packets.append(
                {
                    "packet_schema_version": 1,
                    "blind_id": blind_id,
                    "user_prompt": prompts[prompt_id],
                    "candidate_response": response["raw_output"],
                }
            )
            mapping.append(
                {
                    "mapping_schema_version": 1,
                    "blind_id": blind_id,
                    "source_label": source_label,
                    "source_run_id": derived["source_run_id"],
                    "attempt_index": derived["attempt_index"],
                    "prompt_id": prompt_id,
                    "system_id": system_id,
                    "raw_output_sha256": derived["source_raw_output_sha256"],
                }
            )

    packets.sort(
        key=lambda item: hashlib.sha256(
            canonical_json({"judge_seed": judge_seed, "blind_id": item["blind_id"]}).encode()
        ).digest()
    )
    mapping.sort(key=lambda item: item["blind_id"])
    output_dir.mkdir(parents=True)
    (output_dir / "rubric.json").write_bytes(canonical_line(RUBRIC))
    (output_dir / "packets.jsonl").write_bytes(b"".join(canonical_line(item) for item in packets))
    (output_dir / "identity-mapping.jsonl").write_bytes(
        b"".join(canonical_line(item) for item in mapping)
    )
    return {
        "result": "complete",
        "packet_count": len(packets),
        "judge_seed": judge_seed,
        "system_id": system_id,
        "source_count": len(sources),
    }


def reveal_and_summarize_scores(scoring_dir: Path) -> dict[str, Any]:
    """Validate completed blind scores, reveal identities, and aggregate by source."""

    revealed_path = scoring_dir / "revealed-scores.jsonl"
    summary_path = scoring_dir / "summary.json"
    if revealed_path.exists() or summary_path.exists():
        raise ContractError("revealed scoring outputs already exist")
    packets = {item["blind_id"]: item for item in _read_jsonl(scoring_dir / "packets.jsonl")}
    mapping = {item["blind_id"]: item for item in _read_jsonl(scoring_dir / "identity-mapping.jsonl")}
    scores = {item["blind_id"]: item for item in _read_jsonl(scoring_dir / "scores.jsonl")}
    if not packets or set(packets) != set(mapping) or set(packets) != set(scores):
        raise ContractError("packet, mapping, and score blind IDs must match exactly")
    dimensions = (
        "underlying_answer_quality",
        "metaphorical_coherence",
        "recipe_style_execution",
    )
    revealed: list[dict[str, Any]] = []
    aggregates: dict[str, dict[str, int]] = {}
    evaluator_values: set[str] = set()
    for blind_id in sorted(packets):
        score = scores[blind_id]
        for dimension in dimensions:
            value = score.get(dimension)
            if type(value) is not int or value not in (1, 2, 3):
                raise ContractError(f"{blind_id}: invalid score for {dimension}")
        expected_pass = all(score[dimension] >= 2 for dimension in dimensions)
        if score.get("full_qualitative_pass") is not expected_pass:
            raise ContractError(f"{blind_id}: full qualitative pass disagrees with scores")
        evaluator = score.get("evaluator")
        if not isinstance(evaluator, str) or not evaluator:
            raise ContractError(f"{blind_id}: evaluator identity is required")
        evaluator_values.add(evaluator)
        identity = mapping[blind_id]
        source = identity["source_label"]
        counts = aggregates.setdefault(
            source,
            {
                "schema_valid_scored": 0,
                "full_qualitative_pass": 0,
                "underlying_answer_quality_at_least_2": 0,
                "metaphorical_coherence_at_least_2": 0,
                "recipe_style_execution_at_least_2": 0,
            },
        )
        counts["schema_valid_scored"] += 1
        counts["full_qualitative_pass"] += int(expected_pass)
        for dimension in dimensions:
            counts[f"{dimension}_at_least_2"] += int(score[dimension] >= 2)
        revealed.append(
            {
                "revealed_score_schema_version": 1,
                **identity,
                "scores": {dimension: score[dimension] for dimension in dimensions},
                "full_qualitative_pass": expected_pass,
                "rationale": score.get("rationale"),
                "evaluator": evaluator,
            }
        )
    summary = {
        "schema_version": 1,
        "kind": "revealed-llm-judge-summary",
        "packet_count": len(packets),
        "evaluators": sorted(evaluator_values),
        "sources": {source: values for source, values in sorted(aggregates.items())},
    }
    revealed_path.write_bytes(b"".join(canonical_line(item) for item in revealed))
    summary_path.write_bytes(canonical_line(summary))
    return summary
