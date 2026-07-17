"""Prepare and extract the frozen Stage 7 held-out evaluation."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.configuration import PROJECT_ROOT, adapter_identity, load_prompts
from chatgnt.evaluation_protocol import (
    build_evaluation_generation_manifest,
    build_judgment_packets,
    canonical_records_sha256,
    evaluation_run_records_from_harness,
    load_protocol,
    read_jsonl,
    select_human_pair_calibration,
    select_human_response_calibration,
    validate_heldout_quotas,
    validate_heldout_records,
    validate_judge_manifest,
    validate_protocol_manifest,
)
from chatgnt.records import ContractError, canonical_json, canonical_line, strict_json_loads


DEFAULT_PLAN = PROJECT_ROOT / "config" / "runs" / "heldout-evaluation-v1.json"
PLAN_KEYS = {
    "schema_version", "run_plan_id", "run_id", "heldout_records_path",
    "heldout_records_sha256", "harness_prompts_path", "system_set_path",
    "system_set_sha256", "adapter_path", "adapter_sha256", "run_seed", "device",
    "scheduled_attempt_count", "provider", "gpu_policy", "maximum_provider_cost_usd",
    "automatic_termination_hours",
}
GPU_POLICY_KEYS = {
    "preferred_gpu", "minimum_vram_gib", "minimum_cuda_version", "require_bfloat16",
    "require_single_matched_gpu_for_complete_run", "official_template_required",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_plan(path: Path) -> dict[str, Any]:
    value = strict_json_loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != PLAN_KEYS:
        raise ContractError("Stage 7 run plan has an invalid closed shape")
    if value["schema_version"] != 1 or value["run_plan_id"] != "heldout-evaluation-v1":
        raise ContractError("Stage 7 run plan identity mismatch")
    if set(value["gpu_policy"]) != GPU_POLICY_KEYS:
        raise ContractError("Stage 7 GPU policy has an invalid closed shape")
    if value["scheduled_attempt_count"] != 240 or value["run_seed"] != 20260715:
        raise ContractError("Stage 7 attempt count or run seed mismatch")
    if value["device"] != "cuda:0" or value["maximum_provider_cost_usd"] != 5.0:
        raise ContractError("Stage 7 device or cost guard mismatch")
    return value


def _path(value: str) -> Path:
    path = (PROJECT_ROOT / value).resolve()
    if not path.is_relative_to(PROJECT_ROOT.resolve()):
        raise ContractError("Stage 7 plan path escapes the project")
    return path


def _projected_prompts(heldout: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for item in heldout:
        metadata = {key: value for key, value in item.items() if key not in {"prompt_id", "prompt"}}
        records.append({"prompt_id": item["prompt_id"], "prompt": item["prompt"], "metadata": metadata})
    return records


def _write_new(path: Path, content: bytes) -> None:
    if path.exists():
        raise ContractError(f"refusing to replace existing Stage 7 output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    _write_new(path, b"".join(canonical_line(item) for item in records))


def _git_state() -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
    ).stdout.splitlines()
    return {"commit": commit, "dirty": bool(dirty), "dirty_entry_count": len(dirty)}


def preflight(plan_path: Path, *, write_harness_prompts: bool, require_clean_git: bool) -> dict[str, Any]:
    plan = _load_plan(plan_path)
    heldout_path = _path(plan["heldout_records_path"])
    systems_path = _path(plan["system_set_path"])
    adapter_path = _path(plan["adapter_path"])
    harness_prompts_path = _path(plan["harness_prompts_path"])
    if _sha256(heldout_path) != plan["heldout_records_sha256"]:
        raise ContractError("frozen held-out record digest mismatch")
    if _sha256(systems_path) != plan["system_set_sha256"]:
        raise ContractError("frozen A-D system-set digest mismatch")

    heldout = read_jsonl(heldout_path)
    heldout_report = validate_heldout_records(heldout)
    quota_report = validate_heldout_quotas(heldout)
    if len(heldout) != 60:
        raise ContractError("Stage 7 requires exactly 60 frozen held-out records")
    systems = strict_json_loads(systems_path.read_text(encoding="utf-8"))
    expected_systems = {
        "schema_version": 1,
        "systems": [
            {"adapter_enabled": False, "prompt_asset_path": "../prompts/minimal-v1.json", "system_id": "A"},
            {"adapter_enabled": False, "prompt_asset_path": "../prompts/five-shot-v3.json", "system_id": "B"},
            {"adapter_enabled": True, "prompt_asset_path": "../prompts/minimal-v1.json", "system_id": "C"},
            {"adapter_enabled": True, "prompt_asset_path": "../prompts/five-shot-v3.json", "system_id": "D"},
        ],
    }
    if systems != expected_systems:
        raise ContractError("Stage 7 system set is not the frozen A-D treatment design")
    adapter = adapter_identity(adapter_path, False)
    if adapter["adapter_digest"] != plan["adapter_sha256"]:
        raise ContractError("Candidate 3 adapter digest mismatch")

    protocol, protocol_sha256 = load_protocol()
    protocol_manifest = validate_protocol_manifest()
    judge_manifest, judge_manifest_sha256 = validate_judge_manifest()
    if protocol["status"] != "frozen":
        raise ContractError("evaluation protocol is not frozen")

    projection = _projected_prompts(heldout)
    projected_bytes = b"".join(canonical_line(item) for item in projection)
    if write_harness_prompts:
        _write_new(harness_prompts_path, projected_bytes)
    if harness_prompts_path.exists():
        loaded, raw = load_prompts(harness_prompts_path)
        if raw != projected_bytes or len(loaded) != 60:
            raise ContractError("harness prompt projection differs from frozen held-out records")

    git = _git_state()
    if require_clean_git and git["dirty"]:
        raise ContractError("formal Stage 7 preflight requires a clean Git checkout")
    return {
        "result": "pass",
        "run_plan_id": plan["run_plan_id"],
        "run_id": plan["run_id"],
        "run_seed": plan["run_seed"],
        "scheduled_attempt_count": plan["scheduled_attempt_count"],
        "heldout": heldout_report,
        "quotas": quota_report,
        "heldout_records_sha256": plan["heldout_records_sha256"],
        "harness_prompts_sha256": hashlib.sha256(projected_bytes).hexdigest(),
        "system_set_sha256": plan["system_set_sha256"],
        "adapter_sha256": adapter["adapter_digest"],
        "adapter_id": adapter["adapter_id"],
        "adapter_version": adapter["adapter_version"],
        "protocol_sha256": protocol_sha256,
        "protocol_aggregate_sha256": protocol_manifest["aggregate_sha256"],
        "judge_manifest_sha256": judge_manifest_sha256,
        "judge_manifest_id": judge_manifest["judge_manifest_id"],
        "maximum_provider_cost_usd": plan["maximum_provider_cost_usd"],
        "git": git,
    }


def _automatic_results(run_records: list[dict[str, Any]], harness_manifest_path: Path) -> dict[str, Any]:
    harness_responses = read_jsonl(harness_manifest_path.parent / "responses.jsonl")
    by_system: dict[str, dict[str, Any]] = {}
    for system in "ABCD":
        source = [item for item in harness_responses if item["system_id"] == system]
        formal = [item for item in run_records if item["system_id"] == system]
        json_valid = 0
        for item in formal:
            try:
                strict_json_loads(item["raw_output"])
                json_valid += 1
            except ContractError:
                pass
        latencies = [item["generation_duration_ns"] / 1_000_000_000 for item in source]
        by_system[system] = {
            "scheduled": 60,
            "completed": sum(item["attempt_status"] == "success" for item in source),
            "json_valid": json_valid,
            "schema_valid": sum(item["schema_valid"] for item in formal),
            "input_tokens_mean": statistics.fmean(item["input_token_count"] for item in source),
            "generated_tokens_mean": statistics.fmean(item["generated_token_count"] for item in source),
            "latency_seconds_mean": statistics.fmean(latencies) if latencies else None,
            "attempt_statuses": dict(sorted(Counter(item["attempt_status"] for item in source).items())),
        }
    return {"schema_version": 1, "systems": by_system}


def extract(plan_path: Path, harness_manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise ContractError(f"refusing to replace existing Stage 7 extract: {output_dir}")
    plan = _load_plan(plan_path)
    heldout = read_jsonl(_path(plan["heldout_records_path"]))
    manifest_rel = harness_manifest_path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    run_records = evaluation_run_records_from_harness(heldout, manifest_rel)
    generation_manifest = build_evaluation_generation_manifest(
        heldout, run_records, source_harness_manifest_path=manifest_rel
    )
    response_packets, pair_packets, pair_order = build_judgment_packets(
        heldout, run_records, generation_manifest
    )
    output_dir.mkdir(parents=True)
    (output_dir / "generation-manifest.json").write_bytes(canonical_line(generation_manifest))
    (output_dir / "automatic-results.json").write_bytes(
        canonical_line(_automatic_results(run_records, harness_manifest_path))
    )
    for name, records in (
        ("run-records.jsonl", run_records),
        ("qualitative-packets.jsonl", response_packets),
        ("pairwise-packets.jsonl", pair_packets),
        ("pair-order.jsonl", pair_order),
    ):
        (output_dir / name).write_bytes(b"".join(canonical_line(item) for item in records))

    qualitative_blind = [
        {"kind": "qualitative", "packet_id": item["packet_id"], "packet_sha256": item["packet_sha256"],
         "packet_text": item["packet_text"]}
        for item in response_packets if item["schema_valid"]
    ]
    pairwise_blind = [
        {"kind": "pairwise", "packet_id": item["packet_id"], "packet_sha256": item["packet_sha256"],
         "packet_text": item["packet_text"]}
        for item in pair_packets if item["conditional_eligible"]
    ]
    (output_dir / "llm-judging-queue.jsonl").write_bytes(
        b"".join(canonical_line(item) for item in (*qualitative_blind, *pairwise_blind))
    )

    selected_response_ids = set(select_human_response_calibration(response_packets))
    selected_pair_prompts = set(select_human_pair_calibration(pair_packets))
    human_packets = [
        {"kind": "qualitative", "packet_id": item["packet_id"], "packet_sha256": item["packet_sha256"],
         "packet_text": item["packet_text"]}
        for item in response_packets if item["packet_id"] in selected_response_ids
    ] + [
        {"kind": "pairwise", "packet_id": item["packet_id"], "prompt_id": item["prompt_id"],
         "packet_sha256": item["packet_sha256"], "packet_text": item["packet_text"]}
        for item in pair_packets if item["prompt_id"] in selected_pair_prompts
    ]
    (output_dir / "human-calibration-packets.jsonl").write_bytes(
        b"".join(canonical_line(item) for item in human_packets)
    )
    summary = {
        "result": "pass",
        "run_id": generation_manifest["run_id"],
        "run_records": len(run_records),
        "schema_valid_responses": sum(item["schema_valid"] for item in run_records),
        "qualitative_packets": len(qualitative_blind),
        "pairwise_packets": len(pairwise_blind),
        "human_calibration_packets": len(human_packets),
        "run_records_sha256": canonical_records_sha256(run_records),
    }
    (output_dir / "extract-summary.json").write_bytes(canonical_line(summary))
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight")
    pre.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    pre.add_argument("--write-harness-prompts", action="store_true")
    pre.add_argument("--require-clean-git", action="store_true")
    ext = sub.add_parser("extract")
    ext.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    ext.add_argument("--harness-manifest", type=Path, required=True)
    ext.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        if arguments.command == "preflight":
            result = preflight(
                arguments.plan,
                write_harness_prompts=arguments.write_harness_prompts,
                require_clean_git=arguments.require_clean_git,
            )
        else:
            result = extract(arguments.plan, arguments.harness_manifest, arguments.output_dir)
        print(canonical_json(result))
        return 0
    except BaseException as exc:
        print(canonical_json({"error": {"type": exc.__class__.__name__, "message": str(exc)}}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
