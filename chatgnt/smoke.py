"""Local CPU base/adapter diagnostic for the shared inference boundary."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import sys
from typing import Any

from .configuration import PROJECT_ROOT, load_project_configuration, verify_model_files
from .identity import derive_seed
from .inference import load_engine
from .records import GenerationRequest, TimingPolicy, canonical_json


def run_cpu_smoke(device: str = "cpu") -> dict[str, Any]:
    if device != "cpu":
        raise ValueError("the local smoke command supports exactly --device cpu")
    project = load_project_configuration()
    base = project.model.values["base_model"]
    snapshot = PROJECT_ROOT / "artifacts" / "models" / base["id"].replace("/", "--") / base["revision"]
    verify_model_files(snapshot)
    profile = replace(project.primary_profile, profile_id="cpu-smoke-sampled-v1", max_new_tokens=8)
    timing = TimingPolicy("disabled-diagnostic", False, False, False)
    digest = "0" * 64
    base_engine = load_engine(snapshot, "cpu", "base", project, formal_cuda=False)
    base_request = GenerationRequest("cpu-smoke", "Respond with exactly READY.", "A", "minimal-v1", digest, "", False, 0, derive_seed("cpu-smoke", ["base"]))
    base_result = base_engine.generate(base_request, profile, timing)
    checks: list[dict[str, Any]] = [{
        "runtime_mode": "base", "adapter_enabled": False,
        "messages": list(base_result.messages), "rendered_prompt": base_result.rendered_prompt,
        "generated_token_ids": list(base_result.generated_token_ids), "raw_output": base_result.raw_output,
        "attempt_status": base_result.attempt_status,
    }]
    adapter_path = PROJECT_ROOT / "artifacts" / "diagnostics" / "lora-lifecycle-adapter"
    if adapter_path.is_dir():
        adapted_engine = load_engine(snapshot, "cpu", "adapted", project, adapter_path,
            allow_unprovenanced_diagnostic_adapter=True, formal_cuda=False)
        adapted_request = GenerationRequest("cpu-smoke", "Respond with exactly READY.", "C", "minimal-v1", digest, "", True, 0, derive_seed("cpu-smoke", ["adapted"]))
        result = adapted_engine.generate(adapted_request, profile, timing)
        evidence = adapted_engine.runtime_evidence["adapter"]
        checks.append({"runtime_mode": "adapted", "adapter_enabled": True,
            "messages": list(result.messages), "rendered_prompt": result.rendered_prompt,
            "generated_token_ids": list(result.generated_token_ids), "raw_output": result.raw_output,
            "attempt_status": result.attempt_status, "active_adapters": evidence["active_adapters"],
            "trainable_parameter_count": evidence["trainable_parameter_count"], "merged": evidence["merged"]})
    success = all(item["attempt_status"] == "success" for item in checks) and len(checks) == (2 if adapter_path.is_dir() else 1)
    profile_value = profile.__dict__.copy(); profile_value["eos_token_ids"] = list(profile_value["eos_token_ids"])
    return {"schema_version": 1, "diagnostic": "cpu-smoke", "experimental_result": False,
        "success": success, "device": "cpu", "local_files_only": True,
        "generation_profile": profile_value, "timing": {"enabled": False, "canonical": False,
            "note": "CPU diagnostic timing is not an experimental measurement"},
        "snapshot_path": snapshot.relative_to(PROJECT_ROOT).as_posix(), "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m chatgnt.smoke")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args(argv)
    try:
        report = run_cpu_smoke(args.device)
        print(canonical_json(report)); return 0 if report["success"] else 1
    except BaseException as exc:
        print(canonical_json({"schema_version": 1, "diagnostic": "cpu-smoke", "experimental_result": False,
            "success": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
