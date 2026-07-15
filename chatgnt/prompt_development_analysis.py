"""Aggregate immutable local prompt-development evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .records import ContractError, canonical_line, read_strict_json, strict_json_loads


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


def summarize_prompt_versions(
    versions: list[tuple[str, str, Path, Path, Path]],
    output_path: Path,
) -> dict[str, Any]:
    """Select the strongest local version using the frozen lexicographic rule."""

    if output_path.exists():
        raise ContractError(f"prompt-development summary already exists: {output_path}")
    summaries: list[dict[str, Any]] = []
    for version, scoring_source, run_dir, structure_dir, scoring_dir in versions:
        manifest, _ = read_strict_json(run_dir / "manifest.json")
        structural, _ = read_strict_json(structure_dir / "summary.json")
        qualitative, _ = read_strict_json(scoring_dir / "summary.json")
        responses = _read_jsonl(run_dir / "responses.jsonl")
        structure = structural["systems"]["B"]
        scores = qualitative["sources"][scoring_source]
        prompt_tokens = [item["prompt_eval_count"] for item in responses]
        durations = [item["total_duration_ns"] for item in responses]
        if (
            len(responses) != 20
            or any(type(value) is not int or value <= 0 for value in prompt_tokens)
            or any(type(value) is not int or value <= 0 for value in durations)
            or scores["schema_valid_scored"] != structure["schema_valid"]
        ):
            raise ContractError(f"{version}: incomplete or inconsistent local evidence")
        selection_vector = [
            scores["full_qualitative_pass"],
            structure["schema_valid"],
            scores["underlying_answer_quality_at_least_2"],
            scores["metaphorical_coherence_at_least_2"],
            scores["recipe_style_execution_at_least_2"],
        ]
        summaries.append(
            {
                "version": version,
                "run_id": manifest["run_id"],
                "prompt_asset_id": manifest["prompt_asset"]["prompt_asset_id"],
                "prompt_asset_sha256": manifest["prompt_asset"]["sha256"],
                "attempts": structure["attempts"],
                "selection_vector": selection_vector,
                "structural_failure_labels": structure["failure_labels"],
                "prompt_eval_tokens": {
                    "minimum": min(prompt_tokens),
                    "maximum": max(prompt_tokens),
                    "total": sum(prompt_tokens),
                    "mean": round(sum(prompt_tokens) / len(prompt_tokens), 4),
                },
                "diagnostic_total_duration_seconds": round(sum(durations) / 1_000_000_000, 4),
            }
        )
    selected = max(
        summaries,
        key=lambda item: (*item["selection_vector"], -item["prompt_eval_tokens"]["total"]),
    )
    result = {
        "schema_version": 1,
        "kind": "local-prompt-development-summary",
        "selection_rule": [
            "full_response_pass_count",
            "schema_valid_count",
            "underlying_answer_quality_at_least_2_count",
            "metaphorical_coherence_at_least_2_count",
            "recipe_style_execution_at_least_2_count",
            "lower_complete_prompt_token_cost",
        ],
        "versions": summaries,
        "selected_version": selected["version"],
        "selected_prompt_asset_id": selected["prompt_asset_id"],
        "selected_prompt_asset_sha256": selected["prompt_asset_sha256"],
        "stopping_reason": "four_version_ceiling_reached_and_v4_regressed",
        "formal_confirmation_required": True,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical_line(result))
    return result
