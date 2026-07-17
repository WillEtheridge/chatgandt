"""Compute the frozen primary Stage 7 analysis from immutable artifacts."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.evaluation_protocol import (  # noqa: E402
    paired_bootstrap_interval, read_jsonl, weighted_cohens_kappa, wilson_interval,
)
from chatgnt.records import ContractError, canonical_line, strict_json_loads  # noqa: E402


DIMENSIONS = ("underlying_answer_quality", "metaphorical_coherence", "recipe_style_execution")


def rate(successes: int, total: int) -> dict[str, Any]:
    if total == 0:
        return {"successes": successes, "total": 0, "rate": None, "wilson_95": None}
    lower, upper = wilson_interval(successes, total)
    return {"successes": successes, "total": total, "rate": successes / total,
            "wilson_95": {"lower": lower, "upper": upper}}


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values); position = (len(ordered) - 1) * probability
    low = int(position); high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (position - low) * (ordered[high] - ordered[low])


def continuous(values: list[float], include_std: bool) -> dict[str, Any]:
    result = {"count": len(values), "mean": statistics.fmean(values), "median": statistics.median(values),
              "interquartile_range": quantile(values, .75) - quantile(values, .25)}
    if include_std: result["standard_deviation"] = statistics.stdev(values) if len(values) > 1 else 0.0
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--heldout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    derived = args.evaluation_dir / "derived"; judging = args.evaluation_dir / "judging"
    run_records = read_jsonl(derived / "run-records.jsonl")
    harness = read_jsonl(args.run_dir / "responses.jsonl")
    heldout = read_jsonl(args.heldout); metadata = {item["prompt_id"]: item for item in heldout}
    qualitative = read_jsonl(judging / "qualitative-judgments-llm.jsonl")
    pairwise = read_jsonl(judging / "pairwise-judgments-llm.jsonl")
    pair_packets = read_jsonl(derived / "pairwise-packets.jsonl")
    structural = strict_json_loads((args.evaluation_dir / "structure/summary.json").read_text())
    q_by_response = {item["response_id"]: item for item in qualitative}
    run_by = {(item["prompt_id"], item["system_id"]): item for item in run_records}
    harness_by = {(item["prompt_id"], item["system_id"]): item for item in harness}

    systems = {}
    full_pass_by: dict[str, dict[str, bool]] = defaultdict(dict)
    for system in "ABCD":
        records = [item for item in run_records if item["system_id"] == system]
        judgments = [q_by_response[item["response_id"]] for item in records if item["response_id"] in q_by_response]
        full_passes = 0
        dimensions = {}
        for dimension in DIMENSIONS:
            resolved = [item["scores"][dimension] for item in judgments if isinstance(item["scores"][dimension], int)]
            accepted = sum(score >= 2 for score in resolved)
            dimensions[dimension] = {
                "score_distribution": {str(key): value for key, value in sorted(Counter(resolved).items())},
                "conditional_acceptability": rate(accepted, len(resolved)),
                "end_to_end_success": rate(accepted, 60),
            }
        for item in records:
            judgment = q_by_response.get(item["response_id"])
            passed = bool(item["schema_valid"] and judgment and
                          all(isinstance(judgment["scores"][d], int) and judgment["scores"][d] >= 2 for d in DIMENSIONS))
            full_pass_by[system][item["prompt_id"]] = passed
            full_passes += passed
        source = [item for item in harness if item["system_id"] == system]
        systems[system] = {
            "completion": rate(sum(item["attempt_status"] == "success" for item in source), 60),
            "json_validity": rate(structural["systems"][system]["json_valid"], 60),
            "schema_validity": rate(structural["systems"][system]["schema_valid"], 60),
            "structural_failure_labels": structural["systems"][system]["failure_labels"],
            "dimensions": dimensions,
            "full_response_pass": rate(full_passes, 60),
            "efficiency": {
                "input_tokens": continuous([item["input_token_count"] for item in source], False),
                "generated_tokens": continuous([item["generated_token_count"] for item in source], False),
                "raw_output_characters": continuous([len(item["raw_output"]) for item in source], True),
                "latency_seconds": continuous([item["generation_duration_ns"] / 1e9 for item in source], True),
            },
        }

    def json_valid(item: dict[str, Any]) -> bool:
        try: strict_json_loads(item["raw_output"]); return True
        except ContractError: return False

    binary_measures = {
        "completion_rate_C_minus_B": lambda pid, system: harness_by[(pid, system)]["attempt_status"] == "success",
        "json_validity_rate_C_minus_B": lambda pid, system: json_valid(run_by[(pid, system)]),
        "schema_validity_rate_C_minus_B": lambda pid, system: run_by[(pid, system)]["schema_valid"],
        "full_response_pass_rate_C_minus_B": lambda pid, system: full_pass_by[system][pid],
    }
    for dimension in DIMENSIONS:
        binary_measures[f"{dimension}_end_to_end_rate_C_minus_B"] = lambda pid, system, d=dimension: bool(
            run_by[(pid, system)]["schema_valid"]
            and q_by_response.get(run_by[(pid, system)]["response_id"])
            and isinstance(q_by_response[run_by[(pid, system)]["response_id"]]["scores"][d], int)
            and q_by_response[run_by[(pid, system)]["response_id"]]["scores"][d] >= 2
        )
    paired = {}
    for name, getter in binary_measures.items():
        values = [{"prompt_id": item["prompt_id"], "B": getter(item["prompt_id"], "B"),
                   "C": getter(item["prompt_id"], "C")} for item in heldout]
        paired[name] = paired_bootstrap_interval(values, "paired_rate_difference")
    for name, getter in (
        ("input_tokens_mean_C_minus_B", lambda item: item["input_token_count"]),
        ("generated_tokens_mean_C_minus_B", lambda item: item["generated_token_count"]),
        ("raw_output_characters_mean_C_minus_B", lambda item: len(item["raw_output"])),
        ("latency_seconds_mean_C_minus_B", lambda item: item["generation_duration_ns"] / 1e9),
    ):
        values = [{"prompt_id": item["prompt_id"], "B": getter(harness_by[(item["prompt_id"], "B")]),
                   "C": getter(harness_by[(item["prompt_id"], "C")])} for item in heldout]
        paired[name] = paired_bootstrap_interval(values, "paired_mean_difference")

    packets = {item["prompt_id"]: item for item in pair_packets}
    judgments = {item["prompt_id"]: item for item in pairwise}
    conditional = Counter()
    end_to_end = Counter()
    for prompt in heldout:
        prompt_id = prompt["prompt_id"]; b = run_by[(prompt_id, "B")]["schema_valid"]; c = run_by[(prompt_id, "C")]["schema_valid"]
        if b and c:
            packet = packets[prompt_id]; judgment = judgments[prompt_id]
            if judgment["choice"] == "tie": winner = "tie"
            else:
                chosen_id = packet["response_a_id"] if judgment["choice"] == "response_a" else packet["response_b_id"]
                winner = "B_win" if chosen_id == run_by[(prompt_id, "B")]["response_id"] else "C_win"
            conditional[winner] += 1; end_to_end[winner] += 1
        elif b: end_to_end["B_win"] += 1
        elif c: end_to_end["C_win"] += 1
        else: end_to_end["both_failed"] += 1
    pairwise_result = {
        "conditional_both_schema_valid": {key: rate(conditional[key], sum(conditional.values())) for key in ("B_win", "C_win", "tie")},
        "end_to_end_all_prompts": {key: rate(end_to_end[key], 60) for key in ("B_win", "C_win", "tie", "both_failed")},
        "decisive_only_C_preference": rate(conditional["C_win"], conditional["B_win"] + conditional["C_win"]),
    }

    subgroups = {}
    for field in ("intent_family", "reporting_slice"):
        subgroups[field] = {}
        for value in sorted({item[field] for item in heldout}):
            ids = [item["prompt_id"] for item in heldout if item[field] == value]
            subgroups[field][value] = {
                system: {"full_passes": sum(full_pass_by[system][pid] for pid in ids), "total": len(ids),
                         "rate": sum(full_pass_by[system][pid] for pid in ids) / len(ids)}
                for system in "ABCD"
            }
    agreement = None
    human_q_path = judging / "qualitative-judgments-human.jsonl"
    human_p_path = judging / "pairwise-judgments-human.jsonl"
    if human_q_path.exists() and human_p_path.exists():
        human_q = read_jsonl(human_q_path); human_p = read_jsonl(human_p_path)
        llm_q = {item["packet_id"]: item for item in qualitative}
        dimension_agreement = {}
        for dimension in DIMENSIONS:
            pairs = [(llm_q[item["packet_id"]]["scores"][dimension], item["scores"][dimension]) for item in human_q]
            dimension_agreement[dimension] = {
                "exact_score_agreement": rate(sum(left == right for left, right in pairs), len(pairs)),
                "binary_acceptability_agreement": rate(sum((left >= 2) == (right >= 2) for left, right in pairs), len(pairs)),
                "weighted_cohens_kappa": weighted_cohens_kappa(pairs),
            }
        llm_p = {item["packet_id"]: item for item in pairwise}
        pair_matches = sum(llm_p[item["packet_id"]]["choice"] == item["choice"] for item in human_p)
        agreement = {"qualitative_sample_count": len(human_q), "dimensions": dimension_agreement,
                     "pairwise_sample_count": len(human_p), "pairwise_exact_choice_agreement": rate(pair_matches, len(human_p))}
    similarity_path = args.evaluation_dir / "similarity/summary.json"
    similarity = strict_json_loads(similarity_path.read_text()) if similarity_path.exists() else None
    result = {
        "schema_version": 1, "analysis_status": "complete" if agreement else "primary_llm_complete_human_calibration_pending",
        "denominator_per_system": 60, "systems": systems, "paired_B_C": paired,
        "pairwise_B_C": pairwise_result, "subgroup_diagnostics": subgroups,
        "response_similarity": similarity,
        "human_llm_agreement": agreement,
        "judge": {"identity": qualitative[0]["judge_identity"].split(":")[0],
                  "model_id": qualitative[0]["exposed_model_id"], "qualitative_count": len(qualitative),
                  "pairwise_count": len(pairwise), "unresolved_count": sum(item["resolution_status"] != "resolved" for item in qualitative + pairwise)},
        "interpretation_guard": "Quality and efficiency are separate outcomes; no universal exchange rate is applied.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_line(result))
    print(json.dumps({"result": "complete", "output": str(args.output),
                      "full_pass": {s: systems[s]["full_response_pass"]["successes"] for s in "ABCD"},
                      "pairwise_end_to_end": dict(end_to_end)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
