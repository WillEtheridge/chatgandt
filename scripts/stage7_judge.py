"""Run isolated Codex judge contexts for Stage 7 calibration and sealed packets."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.evaluation_protocol import (  # noqa: E402
    canonical_records_sha256,
    load_protocol,
    read_jsonl,
    render_pairwise_response,
    validate_judge_manifest,
)
from chatgnt.records import ContractError, canonical_json, canonical_line, strict_json_loads  # noqa: E402


QUALITATIVE_SCHEMA = ROOT / "schemas" / "stage7-qualitative-decision-v1.schema.json"
PAIRWISE_SCHEMA = ROOT / "schemas" / "stage7-pairwise-decision-v1.schema.json"
CALIBRATION = ROOT / "data" / "evaluation" / "judge-calibration-v1.jsonl"
MODEL_ID = "gpt-5.6-terra"
JUDGE_IDENTITY = "openai-codex-cli-gpt-5.6-terra"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _event_thread_id(stdout: str) -> str:
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str):
            return event["thread_id"]
    raise ContractError("Codex judge output did not expose a thread ID")


def _invoke(packet_key: str, kind: str, prompt: str) -> dict[str, Any]:
    schema = QUALITATIVE_SCHEMA if kind == "qualitative" else PAIRWISE_SCHEMA
    with tempfile.TemporaryDirectory(prefix="chatgnt-stage7-judge-") as directory:
        root = Path(directory)
        output = root / "decision.json"
        command = [
            "codex", "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--sandbox", "read-only", "--skip-git-repo-check", "--json", "-C", str(root),
            "--model", MODEL_ID, "--output-schema", str(schema), "--output-last-message", str(output), "-",
        ]
        completed = subprocess.run(command, input=prompt, text=True, capture_output=True)
        if completed.returncode != 0:
            raise ContractError(
                f"Codex judge failed for {packet_key}: exit={completed.returncode}; "
                f"stdout={completed.stdout[-1500:]}; stderr={completed.stderr[-1000:]}"
            )
        decision = strict_json_loads(output.read_text(encoding="utf-8"))
        if not isinstance(decision, dict):
            raise ContractError(f"Codex judge returned a non-object for {packet_key}")
        return {
            "packet_key": packet_key,
            "kind": kind,
            "judge_identity": JUDGE_IDENTITY,
            "exposed_model_id": MODEL_ID,
            "judge_session_id": _event_thread_id(completed.stdout),
            "decision": decision,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        }


def _qualitative_calibration_prompt(record: dict[str, Any], manifest: dict[str, Any], rubric: dict[str, Any]) -> str:
    response = render_pairwise_response(record["candidate_response"]).rstrip("\n")
    packet = manifest["qualitative"]["packet_template"].format(
        packet_id=record["calibration_id"],
        user_prompt=record["user_prompt"],
        candidate_response=response,
        rubric_json=canonical_json(rubric),
    )
    return (
        manifest["qualitative"]["instruction"] + "\n\n" + packet
        + "\n\nDo not use tools or outside information. The controller binds provenance separately. "
          "Return only the decision fields required by the supplied output schema."
    )


def _pairwise_calibration_prompt(record: dict[str, Any], manifest: dict[str, Any]) -> str:
    candidate = record["candidate_response"]
    packet = manifest["pairwise"]["packet_template"].format(
        packet_id=record["calibration_id"],
        user_prompt=record["user_prompt"],
        response_a=render_pairwise_response(candidate["a"]).rstrip("\n"),
        response_b=render_pairwise_response(candidate["b"]).rstrip("\n"),
    )
    return (
        manifest["pairwise"]["instruction"] + "\n\n" + packet
        + "\n\nDo not use tools or outside information. The controller binds provenance separately. "
          "Return only the decision fields required by the supplied output schema."
    )


def calibrate(output_path: Path, workers: int) -> dict[str, Any]:
    if output_path.exists():
        raise ContractError(f"refusing to replace judge calibration evidence: {output_path}")
    manifest, manifest_sha = validate_judge_manifest()
    rubric = strict_json_loads((ROOT / manifest["qualitative"]["rubric_path"]).read_text(encoding="utf-8"))
    records = read_jsonl(CALIBRATION)
    jobs = []
    for record in records:
        kind = record["kind"]
        prompt = (
            _qualitative_calibration_prompt(record, manifest, rubric)
            if kind == "qualitative" else _pairwise_calibration_prompt(record, manifest)
        )
        jobs.append((record, prompt))
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_invoke, record["calibration_id"], record["kind"], prompt): record
            for record, prompt in jobs
        }
        for future in as_completed(futures):
            record = futures[future]
            result = future.result()
            expected = record["expected"] if record["kind"] == "qualitative" else record["expected_choice"]
            observed = result["decision"]["scores"] if record["kind"] == "qualitative" else result["decision"]["choice"]
            result["expected"] = expected
            result["exact_match"] = observed == expected
            result["focus"] = record["focus"]
            results.append(result)
    results.sort(key=lambda item: item["packet_key"])
    sessions = [item["judge_session_id"] for item in results]
    if len(sessions) != len(set(sessions)):
        raise ContractError("calibration did not use one fresh Codex context per packet")
    evidence = {
        "schema_version": 1,
        "calibration_id": "stage7-judge-calibration-20260717",
        "judge_manifest_sha256": manifest_sha,
        "calibration_packets_sha256": _sha256(CALIBRATION),
        "decision_schema_sha256": {
            "qualitative": _sha256(QUALITATIVE_SCHEMA),
            "pairwise": _sha256(PAIRWISE_SCHEMA),
        },
        "judge_identity": JUDGE_IDENTITY,
        "exposed_model_id": MODEL_ID,
        "fresh_context_count": len(sessions),
        "exact_match_count": sum(item["exact_match"] for item in results),
        "discrepancy_count": sum(not item["exact_match"] for item in results),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("xb") as handle:
        handle.write(canonical_line(evidence))
    return {
        "result": "complete",
        "packet_count": len(results),
        "exact_match_count": evidence["exact_match_count"],
        "discrepancy_count": evidence["discrepancy_count"],
        "output_path": output_path.as_posix(),
    }


def _production_prompt(kind: str, packet_text: str, manifest: dict[str, Any]) -> str:
    instruction = manifest["qualitative" if kind == "qualitative" else "pairwise"]["instruction"]
    return (
        instruction + "\n\n" + packet_text
        + "\n\nDo not use tools or outside information. The controller binds provenance separately. "
          "Return only the decision fields required by the supplied output schema."
    )


def _read_existing_decisions(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = read_jsonl(path)
    required = {
        "packet_key", "kind", "judge_identity", "exposed_model_id", "judge_session_id",
        "decision", "recorded_at_utc", "stdout_sha256",
    }
    if any(set(item) != required for item in records):
        raise ContractError("existing raw judge decisions have an invalid closed shape")
    packet_ids = [item["packet_key"] for item in records]
    sessions = [item["judge_session_id"] for item in records]
    if len(packet_ids) != len(set(packet_ids)) or len(sessions) != len(set(sessions)):
        raise ContractError("existing raw judge decisions contain duplicate packets or contexts")
    return records


def _qualitative_record(
    result: dict[str, Any], packet: dict[str, Any], identities: dict[str, str], manifest: dict[str, Any]
) -> dict[str, Any]:
    scores = result["decision"]["scores"]
    unable = "unable_to_assess" in scores.values()
    return {
        "record_schema_version": 1,
        "judgment_id": f"qual-v1-primary-{packet['packet_id'].removeprefix('qual-packet-v1-')}",
        "protocol_sha256": identities["protocol"],
        "heldout_records_sha256": identities["heldout"],
        "run_records_sha256": identities["run_records"],
        "generation_manifest_sha256": identities["generation_manifest"],
        "rubric_sha256": identities["rubric"],
        "judge_manifest_sha256": identities["judge_manifest"],
        "instruction_sha256": manifest["qualitative"]["instruction_sha256"],
        "packet_id": packet["packet_id"],
        "packet_sha256": packet["packet_sha256"],
        "prompt_id": packet["prompt_id"],
        "response_id": packet["response_id"],
        "blinded_label": "candidate_response",
        "judge_role": "llm",
        "judge_identity": f"{JUDGE_IDENTITY}:{result['judge_session_id']}",
        "judge_session_id": result["judge_session_id"],
        "exposed_model_id": result["exposed_model_id"],
        "judgment_round": "primary",
        "prior_judgment_id": None,
        "resolution_status": "pending_second" if unable else "resolved",
        "scores": scores,
        "rationales": result["decision"]["rationales"],
        "recorded_at_utc": result["recorded_at_utc"],
    }


def _pairwise_record(
    result: dict[str, Any], packet: dict[str, Any], identities: dict[str, str], manifest: dict[str, Any]
) -> dict[str, Any]:
    choice = result["decision"]["choice"]
    return {
        "record_schema_version": 1,
        "judgment_id": f"pair-v1-primary-{packet['packet_id'].removeprefix('pair-packet-v1-')}",
        "protocol_sha256": identities["protocol"],
        "heldout_records_sha256": identities["heldout"],
        "run_records_sha256": identities["run_records"],
        "generation_manifest_sha256": identities["generation_manifest"],
        "judge_manifest_sha256": identities["judge_manifest"],
        "instruction_sha256": manifest["pairwise"]["instruction_sha256"],
        "packet_id": packet["packet_id"],
        "packet_sha256": packet["packet_sha256"],
        "renderer_id": manifest["pairwise"]["renderer_id"],
        "prompt_id": packet["prompt_id"],
        "response_a_id": packet["response_a_id"],
        "response_b_id": packet["response_b_id"],
        "order_schedule_sha256": packet["order_schedule_sha256"],
        "judge_role": "llm",
        "judge_identity": f"{JUDGE_IDENTITY}:{result['judge_session_id']}",
        "judge_session_id": result["judge_session_id"],
        "exposed_model_id": result["exposed_model_id"],
        "judgment_round": "primary",
        "prior_judgment_id": None,
        "resolution_status": "pending_second" if choice == "unable_to_assess" else "resolved",
        "choice": choice,
        "rationale": result["decision"]["rationale"],
        "recorded_at_utc": result["recorded_at_utc"],
    }


def judge(derived_dir: Path, output_dir: Path, workers: int) -> dict[str, Any]:
    queue = read_jsonl(derived_dir / "llm-judging-queue.jsonl")
    queue_by_id = {item["packet_id"]: item for item in queue}
    if len(queue) != len(queue_by_id) or any(item["kind"] not in {"qualitative", "pairwise"} for item in queue):
        raise ContractError("production judge queue is invalid or duplicated")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "raw-primary-decisions.jsonl"
    qualitative_path = output_dir / "qualitative-judgments-llm.jsonl"
    pairwise_path = output_dir / "pairwise-judgments-llm.jsonl"
    summary_path = output_dir / "primary-judging-summary.json"
    if any(path.exists() for path in (qualitative_path, pairwise_path, summary_path)):
        raise ContractError("sealed production judgment outputs already exist")
    existing = _read_existing_decisions(raw_path)
    existing_by_id = {item["packet_key"]: item for item in existing}
    if not set(existing_by_id).issubset(queue_by_id):
        raise ContractError("raw judge decisions contain packets outside the sealed queue")
    missing = [item for item in queue if item["packet_id"] not in existing_by_id]
    judge_manifest = validate_judge_manifest()[0]

    mode = "ab" if raw_path.exists() else "xb"
    with raw_path.open(mode) as handle:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _invoke, item["packet_id"], item["kind"],
                    _production_prompt(item["kind"], item["packet_text"], judge_manifest),
                ): item
                for item in missing
            }
            for future in as_completed(futures):
                result = future.result()
                handle.write(canonical_line(result))
                handle.flush()
                os.fsync(handle.fileno())

    results = _read_existing_decisions(raw_path)
    by_id = {item["packet_key"]: item for item in results}
    if set(by_id) != set(queue_by_id):
        raise ContractError("production judging remains incomplete")

    manifest, manifest_sha = validate_judge_manifest()
    protocol, protocol_sha = load_protocol()
    del protocol
    heldout = read_jsonl(ROOT / "data" / "evaluation" / "heldout-v1" / "prompts.jsonl")
    run_records = read_jsonl(derived_dir / "run-records.jsonl")
    generation_manifest = strict_json_loads((derived_dir / "generation-manifest.json").read_text(encoding="utf-8"))
    identities = {
        "protocol": protocol_sha,
        "heldout": canonical_records_sha256(heldout),
        "run_records": canonical_records_sha256(run_records),
        "generation_manifest": hashlib.sha256(canonical_json(generation_manifest).encode()).hexdigest(),
        "rubric": _sha256(ROOT / manifest["qualitative"]["rubric_path"]),
        "judge_manifest": manifest_sha,
    }
    qualitative_packets = {item["packet_id"]: item for item in read_jsonl(derived_dir / "qualitative-packets.jsonl")}
    pairwise_packets = {item["packet_id"]: item for item in read_jsonl(derived_dir / "pairwise-packets.jsonl")}
    qualitative = []
    pairwise = []
    for item in queue:
        result = by_id[item["packet_id"]]
        if item["kind"] == "qualitative":
            qualitative.append(_qualitative_record(result, qualitative_packets[item["packet_id"]], identities, manifest))
        else:
            pairwise.append(_pairwise_record(result, pairwise_packets[item["packet_id"]], identities, manifest))
    qualitative.sort(key=lambda item: item["packet_id"])
    pairwise.sort(key=lambda item: item["packet_id"])
    for path, records in (
        (qualitative_path, qualitative),
        (pairwise_path, pairwise),
    ):
        with path.open("xb") as handle:
            handle.write(b"".join(canonical_line(item) for item in records))
    sessions = [item["judge_session_id"] for item in results]
    if len(sessions) != len(set(sessions)):
        raise ContractError("production judging did not use one fresh context per packet")
    pending = sum(item["resolution_status"] == "pending_second" for item in (*qualitative, *pairwise))
    summary = {
        "result": "complete" if pending == 0 else "pending_second_judgments",
        "queue_count": len(queue),
        "qualitative_count": len(qualitative),
        "pairwise_count": len(pairwise),
        "fresh_context_count": len(sessions),
        "pending_second_count": pending,
        "judge_identity": JUDGE_IDENTITY,
        "exposed_model_id": MODEL_ID,
    }
    with summary_path.open("xb") as handle:
        handle.write(canonical_line(summary))
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    calibration = sub.add_parser("calibrate")
    calibration.add_argument("--output", type=Path, required=True)
    calibration.add_argument("--workers", type=int, default=2, choices=range(1, 5))
    production = sub.add_parser("judge")
    production.add_argument("--derived-dir", type=Path, required=True)
    production.add_argument("--output-dir", type=Path, required=True)
    production.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        result = (
            calibrate(arguments.output, arguments.workers)
            if arguments.command == "calibrate"
            else judge(arguments.derived_dir, arguments.output_dir, arguments.workers)
        )
        print(canonical_json(result))
        return 0
    except BaseException as exc:
        print(canonical_json({"error": {"type": exc.__class__.__name__, "message": str(exc)}}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
