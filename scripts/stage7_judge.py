"""Run isolated Codex judge contexts for Stage 7 calibration and sealed packets."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.evaluation_protocol import (  # noqa: E402
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    calibration = sub.add_parser("calibrate")
    calibration.add_argument("--output", type=Path, required=True)
    calibration.add_argument("--workers", type=int, default=2, choices=range(1, 5))
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        result = calibrate(arguments.output, arguments.workers)
        print(canonical_json(result))
        return 0
    except BaseException as exc:
        print(canonical_json({"error": {"type": exc.__class__.__name__, "message": str(exc)}}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
