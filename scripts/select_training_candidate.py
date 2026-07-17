"""Apply the frozen Stage 6 selection rule to candidate evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
from statistics import mean
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.records import ContractError, canonical_json, canonical_line, strict_json_loads


DIMENSIONS = (
    "underlying_answer_quality",
    "metaphorical_coherence",
    "recipe_style_execution",
)
SIMPLICITY_ORDER = ("candidate-1", "candidate-2", "candidate-3")


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


def select_candidate(
    sources: list[tuple[str, Path, Path]], scoring_dir: Path, output_path: Path,
) -> dict[str, Any]:
    """Summarise evidence, apply non-compensatory gates, then rank viable candidates."""
    if output_path.exists():
        raise ContractError(f"selection output already exists: {output_path}")
    labels = [label for label, _, _ in sources]
    if len(sources) != 3 or set(labels) != set(SIMPLICITY_ORDER):
        raise ContractError("sources must contain candidate-1, candidate-2, and candidate-3 exactly once")
    revealed = _read_jsonl(scoring_dir / "revealed-scores.jsonl")
    scores_by_source: dict[str, dict[str, dict[str, Any]]] = {label: {} for label in labels}
    for score in revealed:
        source, prompt_id = score.get("source_label"), score.get("prompt_id")
        if source not in scores_by_source or not isinstance(prompt_id, str) or prompt_id in scores_by_source[source]:
            raise ContractError("revealed scores contain an invalid or duplicate source/prompt identity")
        scores_by_source[source][prompt_id] = score
    results: dict[str, dict[str, Any]] = {}
    shared_prompt_ids: set[str] | None = None
    for label, run_dir, evaluation_dir in sources:
        prompts = _read_jsonl(run_dir / "prompts.jsonl")
        prompt_map = {item.get("prompt_id"): item for item in prompts}
        if len(prompt_map) != 10 or None in prompt_map:
            raise ContractError(f"{label}: expected exactly ten unique prompts")
        prompt_ids = set(prompt_map)
        if shared_prompt_ids is None: shared_prompt_ids = prompt_ids
        elif prompt_ids != shared_prompt_ids: raise ContractError("candidate prompt populations do not match")
        responses = _read_jsonl(run_dir / "responses.jsonl")
        if len(responses) != 10 or any(item.get("system_id") != "C" for item in responses):
            raise ContractError(f"{label}: expected exactly ten system-C responses")
        validations = _read_jsonl(evaluation_dir / "validations.jsonl")
        if len(validations) != 10: raise ContractError(f"{label}: expected exactly ten structural validations")
        valid_prompt_ids = {item["prompt_id"] for item in validations
            if isinstance(item.get("validation"), dict) and item["validation"].get("schema_valid") is True}
        candidate_scores = scores_by_source[label]
        if set(candidate_scores) != valid_prompt_ids:
            raise ContractError(f"{label}: scores must cover every and only schema-valid response")
        passing_prompt_ids = {prompt_id for prompt_id, score in candidate_scores.items()
            if score.get("full_qualitative_pass") is True}
        families = sorted({item["metadata"]["intent_family"] for item in prompts})
        family_passes = {family: sum(prompt_id in passing_prompt_ids for prompt_id, item in prompt_map.items()
            if item["metadata"]["intent_family"] == family) for family in families}
        successful = [item for item in responses if item.get("attempt_status") == "success"]
        if not successful or any(not isinstance(item.get("generation_duration_ns"), int) for item in successful):
            raise ContractError(f"{label}: successful responses require timing evidence")
        schema_valid_count, joint_pass_count = len(valid_prompt_ids), len(passing_prompt_ids)
        gates = {"schema_valid_at_least_8": schema_valid_count >= 8,
            "joint_pass_at_least_7": joint_pass_count >= 7,
            "every_intent_family_represented": all(value >= 1 for value in family_passes.values())}
        results[label] = {"schema_valid_count": schema_valid_count, "joint_pass_count": joint_pass_count,
            "intent_family_joint_pass_counts": family_passes,
            "total_qualitative_score": sum(score["scores"][dimension] for score in candidate_scores.values() for dimension in DIMENSIONS),
            "average_generation_latency_ms": round(mean(item["generation_duration_ns"] for item in successful) / 1_000_000, 6),
            "average_generated_token_count": round(mean(item["generated_token_count"] for item in successful), 6),
            "successful_generation_count": len(successful), "gates": gates, "viable": all(gates.values())}
    viable = [label for label in SIMPLICITY_ORDER if results[label]["viable"]]
    ranked = sorted(viable, key=lambda label: (-results[label]["joint_pass_count"],
        -results[label]["schema_valid_count"], -results[label]["total_qualitative_score"],
        results[label]["average_generation_latency_ms"], results[label]["average_generated_token_count"],
        SIMPLICITY_ORDER.index(label)))
    summary = {"schema_version": 1, "kind": "full-training-candidate-selection",
        "population_size_per_candidate": 10,
        "ranking_rule": ["joint_pass_count_desc", "schema_valid_count_desc", "total_qualitative_score_desc",
            "average_generation_latency_ms_asc", "average_generated_token_count_asc", "simplicity_candidate_1_to_3"],
        "latency_and_token_aggregation": "all generation-completed responses",
        "candidates": {label: results[label] for label in SIMPLICITY_ORDER},
        "viable_candidates_ranked": ranked, "selected_candidate": ranked[0] if ranked else None}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical_line(summary))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", nargs=3, required=True,
                        metavar=("LABEL", "RUN_DIR", "EVALUATION_DIR"))
    parser.add_argument("--scoring-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = [(label, Path(run), Path(evaluation)) for label, run, evaluation in args.source]
    print(canonical_json(select_candidate(sources, args.scoring_dir, args.output)))


if __name__ == "__main__":
    main()
