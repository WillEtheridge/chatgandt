"""Run the canonical live Stage 3 review gates and, optionally, freeze.

The same process that executes the gates owns the only lifecycle transition.
Persisted verification evidence is useful for later integrity and reproduction
checks, but it is never accepted as transition authorization.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Callable

from jsonschema import Draft202012Validator, FormatChecker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.evaluation_protocol import (
    PROTOCOL_PATH,
    _utc_artifact_time,
    validate_freeze_transition,
    validate_protocol_manifest,
    validate_protocol_value,
)
from chatgnt.records import ContractError, canonical_json, read_strict_json
from scripts.capture_stage3_verification import capture_live_gates


ORCHESTRATOR_PATH = Path(__file__).resolve()
REVIEW_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "stage3-review-artifact-v1.schema.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _contained(relative: str, parent: str, suffix: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ContractError(f"{parent} path must be project-relative")
    value = (PROJECT_ROOT / relative).resolve()
    try:
        value.relative_to((PROJECT_ROOT / parent).resolve())
    except ValueError as exc:
        raise ContractError(f"path must resolve beneath {parent}/") from exc
    if value.suffix != suffix:
        raise ContractError(f"path must end in {suffix}")
    return value


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def _write_new(path: Path, content: bytes) -> None:
    """Create an immutable-by-convention evidence file without overwriting history."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise ContractError(f"refusing to overwrite existing evidence: {path.relative_to(PROJECT_ROOT)}") from exc


def _validate_review_artifact(value: dict[str, object]) -> None:
    schema, _ = read_strict_json(REVIEW_SCHEMA_PATH)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value))
    if errors:
        raise ContractError("Stage 3 review artifact schema failure: " + "; ".join(item.message for item in errors))


def prepare_frozen_transition(
    candidate: dict[str, object], evidence: dict[str, object], authorization: object, *,
    evidence_path: str, review_artifact_path: str, review_id: str,
    reviewer_identity: str, report_path: str, completed_at_utc: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build and live-authorize the status-only transition without writing it."""

    manifest = validate_protocol_manifest(protocol=candidate)
    if evidence.get("protocol_aggregate_sha256") != manifest["aggregate_sha256"]:
        raise ContractError("live evidence does not name the candidate aggregate")
    evidence_file = _contained(evidence_path, "reviews", ".json")
    review_file = _contained(review_artifact_path, "reviews", ".json")
    if evidence_file == review_file:
        raise ContractError("verification evidence and review artifact require distinct paths")
    report_file = _contained(report_path, "docs", ".md")
    if not report_file.is_file():
        raise ContractError("independent review report does not exist")
    completed = _utc_artifact_time(completed_at_utc, "Stage 3 independent review completion")
    evidence_created = _utc_artifact_time(
        evidence.get("created_at_utc"), "Stage 3 verification evidence creation",
    )
    if completed < evidence_created:
        raise ContractError("independent review completion predates live verification evidence")
    evidence_sha = hashlib.sha256(_canonical_bytes(evidence)).hexdigest()
    orchestrator_sha = hashlib.sha256(ORCHESTRATOR_PATH.read_bytes()).hexdigest()
    review = {
        "schema_version":1,
        "review_id":review_id,
        "reviewer_identity":reviewer_identity,
        "reviewed_manifest_sha256":manifest["manifest_sha256"],
        "reviewed_aggregate_sha256":manifest["aggregate_sha256"],
        "verdict":"pass",
        "unresolved_blocking_findings":0,
        "report_path":report_path,
        "report_sha256":hashlib.sha256(report_file.read_bytes()).hexdigest(),
        "verification_evidence_path":evidence_file.relative_to(PROJECT_ROOT).as_posix(),
        "verification_evidence_sha256":evidence_sha,
        "transition_orchestrator_sha256":orchestrator_sha,
        "completed_at_utc":completed_at_utc,
    }
    _validate_review_artifact(review)
    frozen = copy.deepcopy(candidate)
    frozen["status"] = "frozen"
    frozen["freeze_gate"] = {
        "independent_review_required":True,
        "review_id":review_id,
        "reviewer_identity":reviewer_identity,
        "review_verdict":"pass",
        "unresolved_blocking_findings":0,
        "frozen_at_utc":completed_at_utc,
        "review_artifact_path":review_file.relative_to(PROJECT_ROOT).as_posix(),
        "review_artifact_sha256":hashlib.sha256(_canonical_bytes(review)).hexdigest(),
        "verification_evidence_path":evidence_file.relative_to(PROJECT_ROOT).as_posix(),
        "verification_evidence_sha256":evidence_sha,
        "transition_orchestrator_sha256":orchestrator_sha,
    }
    validate_protocol_value(frozen)
    validate_freeze_transition(candidate, frozen, live_gate_authorization=authorization)
    return frozen, review


def orchestrate(
    *, mode: str, evidence_path: str, review_artifact_path: str | None = None,
    review_id: str | None = None, reviewer_identity: str | None = None,
    report_path: str | None = None,
    capture: Callable[[], tuple[dict[str, object], object]] = capture_live_gates,
) -> dict[str, object]:
    """Execute live gates and perform no transition unless freeze inputs pass."""

    if mode not in {"dry-review", "freeze"}:
        raise ContractError("mode must be dry-review or freeze")
    candidate, _ = read_strict_json(PROTOCOL_PATH)
    validate_protocol_value(candidate)
    if candidate["status"] != "review_candidate":
        raise ContractError("Stage 3 orchestration requires a review_candidate")

    # No lifecycle file is touched before this call returns successfully.
    evidence, authorization = capture()
    evidence_file = _contained(evidence_path, "reviews", ".json")
    if mode == "dry-review":
        _write_new(evidence_file, _canonical_bytes(evidence))
        return {"result":"pass", "mode":mode, "transition":"not_attempted", "evidence_path":evidence_path}

    if not all(isinstance(value, str) and value.strip() for value in (
        review_artifact_path, review_id, reviewer_identity, report_path,
    )):
        raise ContractError("freeze mode requires review artifact, review ID, reviewer identity, and report")
    completed_at = utc_now()
    frozen, review = prepare_frozen_transition(
        candidate, evidence, authorization,
        evidence_path=evidence_path, review_artifact_path=review_artifact_path,
        review_id=review_id, reviewer_identity=reviewer_identity,
        report_path=report_path, completed_at_utc=completed_at,
    )

    # Evidence and review are written first; the lifecycle transition is the
    # final write and therefore cannot exist after a controlled gate failure.
    review_file = _contained(review_artifact_path, "reviews", ".json")
    _write_new(evidence_file, _canonical_bytes(evidence))
    _write_new(review_file, _canonical_bytes(review))
    PROTOCOL_PATH.write_bytes(_canonical_bytes(frozen))
    return {
        "result":"pass", "mode":mode, "transition":"frozen",
        "evidence_path":evidence_path, "review_artifact_path":review_artifact_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("dry-review", "freeze"))
    parser.add_argument("--evidence-output", required=True)
    parser.add_argument("--review-artifact-output")
    parser.add_argument("--review-id")
    parser.add_argument("--reviewer-identity")
    parser.add_argument("--report")
    arguments = parser.parse_args()
    try:
        result = orchestrate(
            mode=arguments.mode, evidence_path=arguments.evidence_output,
            review_artifact_path=arguments.review_artifact_output,
            review_id=arguments.review_id, reviewer_identity=arguments.reviewer_identity,
            report_path=arguments.report,
        )
    except ContractError as exc:
        print(canonical_json({"result":"fail", "error":str(exc)}), file=sys.stderr)
        return 1
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
