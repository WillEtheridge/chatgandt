"""Execute and capture the three canonical Stage 3 verification gates.

This module executes the live Stage 3 gates.  Its standalone command captures
reproducibility evidence but deliberately cannot freeze the protocol.  The
canonical review/freeze orchestrator imports :func:`capture_live_gates` and
receives an unpersisted authorization object only after every gate passes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version as package_version
import json
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.evaluation_protocol import (
    load_stage3_verification_evidence,
    validate_protocol_manifest,
    validate_stage3_verification_evidence,
)
from chatgnt.records import ContractError


COMMANDS = {
    "ordinary_verifier":"uv run --frozen python scripts/verify_evaluation_protocol.py",
    "semantic_verifier":"uv run --frozen python scripts/verify_evaluation_protocol.py --semantic",
    "full_test_suite":"uv run --frozen python -m unittest discover -s tests",
}


class _LiveGateAuthorization:
    """Unserializable proof that this process just completed the live gates.

    This is a local process-control boundary, not a security token.  The class
    intentionally has no JSON representation and its constructor is guarded so
    stored verification evidence cannot be supplied as transition authority.
    """

    __slots__ = ("protocol_normative_sha256", "protocol_aggregate_sha256", "_guard")

    def __init__(self, normative_sha256: str, aggregate_sha256: str, guard: object) -> None:
        if guard is not _AUTHORIZATION_GUARD:
            raise TypeError("live gate authorization is issued only by the canonical capture runner")
        self.protocol_normative_sha256 = normative_sha256
        self.protocol_aggregate_sha256 = aggregate_sha256
        self._guard = guard


_AUTHORIZATION_GUARD = object()


def is_live_gate_authorization(value: object, normative_sha256: str, aggregate_sha256: str) -> bool:
    """Return whether *value* is the in-process result for this exact candidate."""

    return (
        type(value) is _LiveGateAuthorization
        and value._guard is _AUTHORIZATION_GUARD
        and value.protocol_normative_sha256 == normative_sha256
        and value.protocol_aggregate_sha256 == aggregate_sha256
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_gate(command: str, implementation_sha256: str) -> dict[str, object]:
    started_at = utc_now()
    started = time.monotonic()
    completed = subprocess.run(
        shlex.split(command), cwd=PROJECT_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    duration = time.monotonic() - started
    completed_at = utc_now()
    try:
        stdout = completed.stdout.decode("utf-8", errors="strict")
        stderr = completed.stderr.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ContractError("canonical gate emitted non-UTF-8 output, which cannot enter JSON evidence") from exc
    combined = stdout + stderr
    return {
        "command":command, "exit_status":completed.returncode,
        "result":"pass" if completed.returncode == 0 else "fail",
        "stdout":stdout, "stdout_sha256":digest_text(stdout),
        "stderr":stderr, "stderr_sha256":digest_text(stderr),
        "combined_output_policy":"stdout_bytes_then_stderr_bytes",
        "combined_output":combined, "combined_output_sha256":digest_text(combined),
        "implementation_sha256":implementation_sha256,
        "started_at_utc":started_at, "completed_at_utc":completed_at,
        "duration_seconds":duration,
    }


def capture_live_gates() -> tuple[dict[str, object], _LiveGateAuthorization]:
    """Execute all canonical gates and return evidence plus ephemeral authority.

    A failed gate raises before either value is returned.  Consequently a
    caller cannot reach a lifecycle transition after a controlled gate fails.
    """

    # This validates the candidate aggregate before the first command starts. The
    # observation timestamp therefore has an explicit chronological meaning.
    manifest = validate_protocol_manifest()
    candidate_observed = utc_now()
    verifier_sha = hashlib.sha256((PROJECT_ROOT / "scripts" / "verify_evaluation_protocol.py").read_bytes()).hexdigest()
    test_entries = [
        {"path":path.relative_to(PROJECT_ROOT).as_posix(), "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted((PROJECT_ROOT / "tests").glob("test_*.py"))
    ]
    tests_sha = hashlib.sha256(json.dumps(test_entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    gates = {
        "ordinary_verifier":run_gate(COMMANDS["ordinary_verifier"], verifier_sha),
        "semantic_verifier":run_gate(COMMANDS["semantic_verifier"], verifier_sha),
        "full_test_suite":run_gate(COMMANDS["full_test_suite"], tests_sha),
    }
    failed = [name for name, record in gates.items() if record["exit_status"] != 0]
    if failed:
        raise ContractError("Stage 3 live gates failed: " + ", ".join(failed))
    uv_version = subprocess.run(["uv", "--version"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    evidence = {
        "schema_version":1,
        "evidence_id":"stage3-verification-v1-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "status":"pass",
        "capture_runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_normative_sha256":manifest["protocol_normative_sha256"],
        "protocol_aggregate_sha256":manifest["aggregate_sha256"],
        "protocol_manifest_sha256":manifest["manifest_sha256"],
        "candidate_identity_observed_at_utc":candidate_observed,
        "environment":{
            "python":platform.python_version(), "platform":platform.platform(), "uv":uv_version,
            "packages":{name:package_version(name) for name in ("jsonschema","rapidfuzz","torch","transformers")},
        },
        **gates,
        "created_at_utc":utc_now(),
    }
    validate_stage3_verification_evidence(evidence)
    authorization = _LiveGateAuthorization(
        evidence["protocol_normative_sha256"], evidence["protocol_aggregate_sha256"],
        _AUTHORIZATION_GUARD,
    )
    return evidence, authorization


def _contained_output(path: Path) -> Path:
    output = (PROJECT_ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        output.relative_to((PROJECT_ROOT / "reviews").resolve())
    except ValueError as exc:
        raise ContractError("--output must resolve beneath the repository reviews directory") from exc
    if output.suffix != ".json":
        raise ContractError("--output must name a JSON file")
    return output


def write_evidence(evidence: dict[str, object], output_path: Path) -> Path:
    """Write already captured evidence to a contained canonical JSON file."""

    output = _contained_output(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    _, _, result = load_stage3_verification_evidence(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True, help="contained reviews/*.json evidence path")
    arguments = parser.parse_args()
    try:
        evidence, _ = capture_live_gates()
        output = write_evidence(evidence, arguments.output)
    except ContractError as exc:
        print(json.dumps({"result":"fail", "error":str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    result = validate_stage3_verification_evidence(evidence)
    print(json.dumps({**result, "output":output.relative_to(PROJECT_ROOT).as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
