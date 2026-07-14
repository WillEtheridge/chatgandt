"""Offline evaluation runner, immutable evidence writer, and inspector CLI."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
import fcntl
import importlib.metadata
import os
from pathlib import Path
import platform
import secrets
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterator

import torch

from . import __version__
from .configuration import (
    ADAPTER_PROVENANCE_KEYS, CONFIG_ROOT, PROJECT_ROOT, ContractError, Prompt, ProjectConfiguration,
    SystemDefinition, adapter_identity, load_project_configuration, load_prompts,
    load_system_set, project_path, verify_model_files,
)
from .identity import (
    derive_seed, execution_order_seed, file_identity, schedule_attempts,
    sha256_bytes, sha256_file, sha256_text, tree_digest,
)
from .inference import InferenceEngine, cuda_health_probe, load_engine
from .records import (
    ATTEMPT_KEYS, GenerationRequest, ScheduledAttempt, canonical_json,
    canonical_line, make_attempt_record, read_strict_json, require_digest,
    require_exact_keys, require_identifier, require_int, strict_json_loads,
)

SPECIFICATION_VERSION = "1.2"
MANIFEST_KEYS = {"schema_version", "specification_version", "run_id", "created_at_utc", "diagnostic", "implementation", "prompt_set", "system_set", "schedule", "model", "tokenizer", "adapter", "configuration", "environment", "timing", "warmup"}
REPORT_KEYS = {"schema_version", "run_id", "scheduled_count", "response_line_count", "valid_response_count", "unique_recorded_attempt_count", "missing_attempt_indices", "duplicate_attempt_indices", "unexpected_attempt_indices", "malformed_line_numbers", "integrity_errors", "complete"}


class RuntimeAbort(RuntimeError):
    pass


def _path_value(path: Path) -> str:
    return project_path(path)["value"]


def _snapshot_path(project: ProjectConfiguration) -> Path:
    base = project.model.values["base_model"]
    return PROJECT_ROOT / "artifacts" / "models" / base["id"].replace("/", "--") / base["revision"]


def _canonical_prompts(prompts: list[Prompt]) -> bytes:
    return b"".join(canonical_line(prompt.to_dict()) for prompt in prompts)


def _implementation_identity() -> dict[str, Any]:
    package = PROJECT_ROOT / "chatgnt"
    files = [file_identity(path, PROJECT_ROOT) for path in sorted(package.glob("*.py")) if path.is_file()]
    commit: str | None = None; dirty: bool | None = None
    try:
        commit_value = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True).stdout.strip()
        if len(commit_value) == 40:
            commit = commit_value
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True).stdout)
    except (OSError, subprocess.SubprocessError):
        pass
    return {"package_version": __version__, "behaviour_files": files,
        "behaviour_digest": tree_digest(files), "pyproject_sha256": sha256_file(PROJECT_ROOT / "pyproject.toml"),
        "uv_lock_sha256": sha256_file(PROJECT_ROOT / "uv.lock"), "git_commit": commit, "git_dirty": dirty}


def _version(distribution: str) -> str:
    return importlib.metadata.version(distribution)


def _environment(device: torch.device, attention: str) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    driver = None
    try:
        getter = getattr(torch.cuda, "driver_version")
        driver = str(getter())
    except BaseException as exc:
        errors.append({"field": "cuda_driver", "type": exc.__class__.__name__, "message": str(exc)})
    return {
        "python": platform.python_version(), "platform": platform.platform(), "torch": torch.__version__,
        "transformers": _version("transformers"), "peft": _version("peft"),
        "tokenizers": _version("tokenizers"), "safetensors": _version("safetensors"),
        "accelerate": _version("accelerate"), "torch_cuda_build": torch.version.cuda,
        "cuda_driver": driver, "cudnn": torch.backends.cudnn.version(), "device": str(device),
        "device_name": torch.cuda.get_device_name(device),
        "device_total_memory_bytes": torch.cuda.get_device_properties(device).total_memory,
        "bf16_supported": torch.cuda.is_bf16_supported(), "attention_implementation": attention,
        "collection_errors": sorted(errors, key=lambda item: (item["field"], item["type"], item["message"])),
    }


def _verify_device(device_text: str) -> torch.device:
    if not device_text.startswith("cuda:") or not device_text[5:].isdigit():
        raise ContractError("formal runner requires an explicit logical cuda:N device")
    device = torch.device(device_text)
    assert device.index is not None
    if not torch.cuda.is_available() or device.index >= torch.cuda.device_count():
        raise ContractError(f"CUDA device unavailable: {device_text}")
    if not torch.cuda.is_bf16_supported():
        raise ContractError(f"BF16 is unsupported on {device_text}")
    return device


@contextmanager
def _runs_lock(runs_root: Path) -> Iterator[None]:
    runs_root.mkdir(parents=True, exist_ok=True)
    lock_path = runs_root / ".chatgnt-harness.lock"
    with lock_path.open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ContractError(f"runs root is already locked: {runs_root}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _scan_asset_history(runs_root: Path, systems: list[SystemDefinition]) -> None:
    current = {(system.prompt_asset.prompt_asset_id, system.prompt_asset.version): system.prompt_asset.source_sha256 for system in systems}
    for manifest_path in sorted(runs_root.glob("*/manifest.json")):
        try:
            manifest, _ = read_strict_json(manifest_path)
            require_exact_keys(manifest, MANIFEST_KEYS, str(manifest_path))
            prior_systems = manifest["system_set"]["systems"]
            if not isinstance(prior_systems, list):
                continue
            prior_assets: list[tuple[tuple[str, str], str]] = []
            for system in prior_systems:
                require_exact_keys(system, {"system_id", "adapter_enabled", "prompt_asset"}, "prior system")
                asset = system["prompt_asset"]
                require_exact_keys(asset, {"source_path", "source_sha256", "schema_version", "prompt_asset_id", "version", "worked_example_count", "content"}, "prior prompt asset")
                require_identifier(asset["prompt_asset_id"], "prior prompt_asset_id")
                if not isinstance(asset["version"], str) or not asset["version"]:
                    raise ContractError("prior prompt asset version is invalid")
                require_digest(asset["source_sha256"], "prior prompt asset digest")
                prior_assets.append(((asset["prompt_asset_id"], asset["version"]), asset["source_sha256"]))
        except (ContractError, KeyError, TypeError):
            continue
        for key, digest in prior_assets:
            if key in current and current[key] != digest:
                raise ContractError(f"prompt asset version was reused with changed bytes: {key}")


def _warmup(engine: InferenceEngine, runtime_mode: str, profile: Any) -> None:
    asset_sha = "0" * 64
    request = GenerationRequest(
        "warmup", "Respond with exactly READY.", "A" if runtime_mode == "base" else "C",
        "minimal-v1", asset_sha, "", runtime_mode == "adapted", 0,
        derive_seed("warmup", [runtime_mode]),
    )
    diagnostic_profile = replace(profile, profile_id="warmup-sampled-v1", max_new_tokens=1)
    from .records import TimingPolicy
    result = engine.generate(request, diagnostic_profile, TimingPolicy("disabled-diagnostic", False, False, False))
    if result.attempt_status != "success":
        raise ContractError(f"{runtime_mode} warm-up failed: {result.error}")


def _make_manifest(
    run_id: str, prompts_path: Path, prompts_raw: bytes, prompts: list[Prompt], frozen: bytes,
    system_path: Path, system_raw: bytes, systems: list[SystemDefinition], schedule: list[ScheduledAttempt],
    project: ProjectConfiguration, model_files: list[dict[str, Any]], snapshot: Path,
    engines: dict[str, InferenceEngine], adapter_path: Path | None,
    diagnostic: dict[str, Any] | None,
) -> dict[str, Any]:
    base_engine = engines.get("base") or engines["adapted"]
    adapter_value = None
    if "adapted" in engines:
        evidence = engines["adapted"].runtime_evidence["adapter"]
        adapter_value = {
            "path": project_path(adapter_path.resolve()), "adapter_id": evidence["adapter_id"],
            "adapter_version": evidence["adapter_version"], "adapter_digest": evidence["adapter_digest"],
            "behaviour_files": evidence["behaviour_files"], "provenance": evidence["provenance"],
            "provenance_sha256": evidence["provenance_sha256"], "peft_config": evidence["peft_config"],
            "active_adapters": evidence["active_adapters"],
            "trainable_parameter_count": evidence["trainable_parameter_count"],
            "parameter_dtypes": evidence["parameter_dtypes"], "merged": evidence["merged"],
        }
    tokenizer = base_engine.tokenizer
    config = project.generation.values
    warmup_profile = replace(project.primary_profile, profile_id="warmup-sampled-v1", max_new_tokens=1).__dict__.copy()
    warmup_profile["eos_token_ids"] = list(warmup_profile["eos_token_ids"])
    return {
        "schema_version": 1, "specification_version": SPECIFICATION_VERSION, "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds"), "diagnostic": diagnostic,
        "implementation": _implementation_identity(),
        "prompt_set": {"source_path": _path_value(prompts_path), "source_sha256": sha256_bytes(prompts_raw),
            "frozen_sha256": sha256_bytes(frozen), "prompt_count": len(prompts),
            "prompt_ids": [item.prompt_id for item in prompts]},
        "system_set": {"source_path": _path_value(system_path), "source_sha256": sha256_bytes(system_raw),
            "systems": [item.manifest_value() for item in systems]},
        "schedule": {"run_seed": schedule[0].generation_seed * 0,  # replaced by caller
            "order_seed": 0, "seed_algorithm": "sha256-first-8-big-endian-v1", "order_algorithm": "sha256-sort-v1",
            "primary_samples_per_system_prompt": 1, "scheduled_attempt_count": len(schedule),
            "attempts": [item.to_dict() for item in schedule]},
        "model": {"model_id": project.model.values["base_model"]["id"],
            "revision": project.model.values["base_model"]["revision"], "snapshot_path": _path_value(snapshot),
            "architecture": project.model.values["base_model"]["architecture"], "model_type": "qwen2",
            "parameter_count": base_engine.runtime_evidence["parameter_count"], "dtype": "bfloat16",
            "max_context_tokens": project.model.values["base_model"]["max_context_tokens"],
            "weights_sha256": project.model.values["base_model"]["weights_sha256"],
            "behaviour_files": model_files,
            "effective_generation_config": base_engine.runtime_evidence["effective_generation_config"]},
        "tokenizer": {"class": tokenizer.__class__.__name__, "length": len(tokenizer),
            "chat_template_sha256": sha256_text(tokenizer.chat_template), "eos_token_id": tokenizer.eos_token_id,
            "generation_eos_token_ids": config["stopping"]["eos_token_ids"],
            "pad_token_id": config["stopping"]["pad_token_id"], "all_special_ids": sorted(tokenizer.all_special_ids)},
        "adapter": adapter_value,
        "configuration": {"model": project.model.manifest_value(), "generation": project.generation.manifest_value(),
            "inference": project.inference.manifest_value()},
        "environment": _environment(base_engine.device, base_engine.runtime_evidence["attention_implementation"]),
        "timing": {key: config["timing"][key] for key in ("metric", "clock", "cuda_synchronize", "include_prompt_prefill", "include_output_generation", "include_tokenization", "include_model_loading", "batch_size", "reusable_conversation_cache")},
        "warmup": {"per_loaded_runtime": 1, "profile": warmup_profile,
            "timed": False, "base_runtime_performed": "base" in engines, "adapted_runtime_performed": "adapted" in engines},
    }


def _publish(run_dir: Path, manifest: dict[str, Any], frozen_prompts: bytes) -> Any:
    created = False
    created_files: list[Path] = []
    response: Any = None
    try:
        run_dir.mkdir(parents=False, exist_ok=False); created = True
        manifest_path = run_dir / "manifest.json"; created_files.append(manifest_path)
        with manifest_path.open("xb") as handle:
            handle.write(canonical_line(manifest)); handle.flush(); os.fsync(handle.fileno())
        prompts_path = run_dir / "prompts.jsonl"; created_files.append(prompts_path)
        with prompts_path.open("xb") as handle:
            handle.write(frozen_prompts); handle.flush(); os.fsync(handle.fileno())
        response_path = run_dir / "responses.jsonl"; created_files.append(response_path)
        response_fd = os.open(response_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o666)
        response = os.fdopen(response_fd, "ab")
        response.flush(); os.fsync(response.fileno())
        directory_fd = os.open(run_dir, os.O_RDONLY)
        try: os.fsync(directory_fd)
        finally: os.close(directory_fd)
        return response
    except BaseException:
        if created:
            try:
                if response is not None and not response.closed:
                    response.close()
                for path in reversed(created_files):
                    if path.exists(): path.unlink()
                run_dir.rmdir()
            except BaseException as cleanup:
                raise ContractError(f"initialization failed and cleanup failed: {cleanup}")
        raise


def execute_run(
    prompts_path: Path, system_set_path: Path, run_seed: int, device_text: str,
    adapter_path: Path | None = None, run_id: str | None = None,
    runs_root: Path = PROJECT_ROOT / "experiments" / "runs",
    diagnostic: dict[str, Any] | None = None,
    allow_unprovenanced_diagnostic_adapter: bool = False,
) -> tuple[int, Path | None, dict[str, Any] | None]:
    require_int(run_seed, "run_seed", 0, 2**64 - 1)
    run_id = run_id or f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
    require_identifier(run_id, "run_id")
    runs_root = runs_root.resolve()
    if diagnostic is None and runs_root != (PROJECT_ROOT / "experiments" / "runs").resolve():
        # A caller may intentionally choose a formal alternate root; still formal.
        pass
    with _runs_lock(runs_root):
        if (runs_root / run_id).exists():
            raise ContractError(f"run ID already exists: {run_id}")
        project = load_project_configuration()
        prompts, prompts_raw = load_prompts(prompts_path.resolve())
        systems, system_raw = load_system_set(system_set_path.resolve(), adapter_path)
        _scan_asset_history(runs_root, systems)
        device = _verify_device(device_text)
        snapshot = _snapshot_path(project)
        model_files = verify_model_files(snapshot)
        needs_base = any(not item.adapter_enabled for item in systems)
        needs_adapter = any(item.adapter_enabled for item in systems)
        engines: dict[str, InferenceEngine] = {}
        if needs_base:
            engines["base"] = load_engine(snapshot, str(device), "base", project, formal_cuda=True)
        if needs_adapter:
            engines["adapted"] = load_engine(snapshot, str(device), "adapted", project,
                adapter_path=adapter_path, allow_unprovenanced_diagnostic_adapter=allow_unprovenanced_diagnostic_adapter,
                formal_cuda=True)
        if len(engines) == 2:
            left, right = engines["base"].runtime_evidence, engines["adapted"].runtime_evidence
            for key in ("parameter_count", "base_dtypes", "attention_implementation"):
                if left[key] != right[key]:
                    raise ContractError(f"base/adapted runtime mismatch: {key}")
        for mode, engine in engines.items(): _warmup(engine, mode, project.primary_profile)
        schedule = schedule_attempts(run_seed, [item.prompt_id for item in prompts], [item.system_id for item in systems])
        frozen = _canonical_prompts(prompts)
        manifest = _make_manifest(run_id, prompts_path.resolve(), prompts_raw, prompts, frozen,
            system_set_path.resolve(), system_raw, systems, schedule, project, model_files, snapshot,
            engines, adapter_path, diagnostic)
        manifest["schedule"]["run_seed"] = run_seed
        manifest["schedule"]["order_seed"] = execution_order_seed(run_seed)
        run_dir = runs_root / run_id
        response_handle = _publish(run_dir, manifest, frozen)
        prompt_map = {item.prompt_id: item for item in prompts}
        system_map = {item.system_id: item for item in systems}
        try:
            for planned in schedule:
                prompt = prompt_map[planned.prompt_id]; system = system_map[planned.system_id]
                request = GenerationRequest(prompt.prompt_id, prompt.prompt, system.system_id,
                    system.prompt_asset.prompt_asset_id, system.prompt_asset.source_sha256,
                    system.prompt_asset.content, system.adapter_enabled, planned.repeat_index, planned.generation_seed)
                engine = engines["adapted" if system.adapter_enabled else "base"]
                result = engine.generate(request, project.primary_profile, project.timing_policy)
                record = make_attempt_record(run_id, planned, request, result)
                response_handle.write(canonical_line(record)); response_handle.flush(); os.fsync(response_handle.fileno())
                if result.attempt_status == "generation_error":
                    if engine.last_failure_fatal:
                        raise RuntimeAbort(f"fatal attempt {planned.attempt_index}: {result.error}")
                    try: cuda_health_probe(device)
                    except BaseException as exc: raise RuntimeAbort(f"CUDA health probe failed: {exc}") from exc
        except KeyboardInterrupt:
            response_handle.close(); raise
        finally:
            if not response_handle.closed: response_handle.close()
        report = inspect_run(run_dir)
        return (0 if report["complete"] else 3), run_dir, report


def _integrity(location: str, code: str, message: str) -> dict[str, str]:
    return {"location": location, "code": code, "message": message}


def _blank_report() -> dict[str, Any]:
    return {"schema_version": 1, "run_id": None, "scheduled_count": 0,
        "response_line_count": 0, "valid_response_count": 0,
        "unique_recorded_attempt_count": 0, "missing_attempt_indices": [],
        "duplicate_attempt_indices": [], "unexpected_attempt_indices": [],
        "malformed_line_numbers": [], "integrity_errors": [], "complete": False}


def _validate_attempt(record: dict[str, Any], expected: dict[str, Any], manifest: dict[str, Any], prompts: dict[str, Prompt]) -> None:
    require_exact_keys(record, ATTEMPT_KEYS, "attempt")
    for key in ("attempt_index", "repeat_index", "generation_seed", "input_token_count", "generated_token_count", "visible_output_token_count"):
        require_int(record[key], key)
    if record["schema_version"] != 1:
        raise ContractError("attempt schema_version mismatch")
    for key in ("attempt_index", "prompt_id", "system_id", "repeat_index", "generation_seed"):
        if record[key] != expected[key]: raise ContractError(f"scheduled identity mismatch: {key}")
    if record["run_id"] != manifest["run_id"]: raise ContractError("run_id mismatch")
    systems = {item["system_id"]: item for item in manifest["system_set"]["systems"]}
    system = systems[record["system_id"]]; asset = system["prompt_asset"]
    if record["adapter_enabled"] != system["adapter_enabled"] or record["prompt_asset_id"] != asset["prompt_asset_id"] or record["prompt_asset_sha256"] != asset["source_sha256"]:
        raise ContractError("system/asset identity mismatch")
    expected_messages = [{"role": "system", "content": asset["content"]}, {"role": "user", "content": prompts[record["prompt_id"]].prompt}]
    if record["messages"] != expected_messages: raise ContractError("messages mismatch")
    if not isinstance(record["input_token_ids"], list) or len(record["input_token_ids"]) != record["input_token_count"]: raise ContractError("input count mismatch")
    if not isinstance(record["generated_token_ids"], list) or len(record["generated_token_ids"]) != record["generated_token_count"]: raise ContractError("generated count mismatch")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in record["input_token_ids"] + record["generated_token_ids"]): raise ContractError("token IDs must be integers")
    if not isinstance(record["adapter_enabled"], bool) or not isinstance(record["reached_max_new_tokens"], bool): raise ContractError("attempt boolean field mismatch")
    status = record["attempt_status"]
    if status not in ("success", "input_context_exceeded", "generation_error"): raise ContractError("invalid attempt status")
    if status == "success":
        if record["error"] is not None or not isinstance(record["raw_output"], str) or require_digest(record["raw_output_sha256"], "raw_output_sha256") != sha256_text(record["raw_output"]): raise ContractError("success output/digest invariant")
        if not isinstance(record["generation_duration_ns"], int) or isinstance(record["generation_duration_ns"], bool) or record["generation_duration_ns"] < 0: raise ContractError("success duration invariant")
        special = set(manifest["tokenizer"]["all_special_ids"])
        if sum(item not in special for item in record["generated_token_ids"]) != record["visible_output_token_count"]: raise ContractError("visible count mismatch")
        maximum = manifest["configuration"]["generation"]["values"]["primary"]["max_new_tokens"]
        reached = len(record["generated_token_ids"]) == maximum
        if record["reached_max_new_tokens"] != reached: raise ContractError("maximum flag mismatch")
        eos = manifest["tokenizer"]["generation_eos_token_ids"]
        last = record["generated_token_ids"][-1] if record["generated_token_ids"] else None
        if last in eos:
            if record["termination_reason"] != "eos_token" or record["terminal_token_id"] != last: raise ContractError("EOS termination invariant")
        elif reached:
            if record["termination_reason"] != "max_new_tokens" or record["terminal_token_id"] is not None: raise ContractError("maximum termination invariant")
        else: raise ContractError("unexpected successful termination")
    else:
        if not isinstance(record["error"], dict) or set(record["error"]) != {"type", "message"} or not all(isinstance(item, str) for item in record["error"].values()): raise ContractError("failure error invariant")
        if any((record["generated_token_ids"], record["generated_token_count"], record["visible_output_token_count"])) or record["raw_output"] is not None or record["raw_output_sha256"] is not None or record["terminal_token_id"] is not None or record["generation_duration_ns"] is not None or record["reached_max_new_tokens"] is not False or record["termination_reason"] != "error": raise ContractError("failure nullability invariant")
        if status == "input_context_exceeded" and (record["error"]["type"] != "InputContextExceededError" or record["rendered_prompt"] is None): raise ContractError("context failure invariant")


def _validate_manifest(manifest: dict[str, Any], run_dir: Path) -> None:
    require_exact_keys(manifest, MANIFEST_KEYS, "manifest")
    if manifest["schema_version"] != 1 or manifest["specification_version"] != SPECIFICATION_VERSION:
        raise ContractError("manifest version mismatch")
    require_identifier(manifest["run_id"], "run_id")
    if not isinstance(manifest["created_at_utc"], str): raise ContractError("created_at_utc must be a string")
    try: created = datetime.fromisoformat(manifest["created_at_utc"])
    except ValueError as exc: raise ContractError("created_at_utc is not ISO-8601") from exc
    if created.utcoffset() != timezone.utc.utcoffset(created): raise ContractError("created_at_utc must be UTC")
    nested = {
        "implementation": {"package_version", "behaviour_files", "behaviour_digest", "pyproject_sha256", "uv_lock_sha256", "git_commit", "git_dirty"},
        "prompt_set": {"source_path", "source_sha256", "frozen_sha256", "prompt_count", "prompt_ids"},
        "system_set": {"source_path", "source_sha256", "systems"},
        "schedule": {"run_seed", "order_seed", "seed_algorithm", "order_algorithm", "primary_samples_per_system_prompt", "scheduled_attempt_count", "attempts"},
        "model": {"model_id", "revision", "snapshot_path", "architecture", "model_type", "parameter_count", "dtype", "max_context_tokens", "weights_sha256", "behaviour_files", "effective_generation_config"},
        "tokenizer": {"class", "length", "chat_template_sha256", "eos_token_id", "generation_eos_token_ids", "pad_token_id", "all_special_ids"},
        "configuration": {"model", "generation", "inference"},
        "environment": {"python", "platform", "torch", "transformers", "peft", "tokenizers", "safetensors", "accelerate", "torch_cuda_build", "cuda_driver", "cudnn", "device", "device_name", "device_total_memory_bytes", "bf16_supported", "attention_implementation", "collection_errors"},
        "timing": {"metric", "clock", "cuda_synchronize", "include_prompt_prefill", "include_output_generation", "include_tokenization", "include_model_loading", "batch_size", "reusable_conversation_cache"},
        "warmup": {"per_loaded_runtime", "profile", "timed", "base_runtime_performed", "adapted_runtime_performed"},
    }
    for key, keys in nested.items(): require_exact_keys(manifest[key], keys, key)
    implementation = manifest["implementation"]
    require_digest(implementation["behaviour_digest"], "behaviour_digest"); require_digest(implementation["pyproject_sha256"], "pyproject_sha256"); require_digest(implementation["uv_lock_sha256"], "uv_lock_sha256")
    if tree_digest(implementation["behaviour_files"]) != implementation["behaviour_digest"]: raise ContractError("implementation tree digest mismatch")
    for file in implementation["behaviour_files"]:
        require_exact_keys(file, {"path", "size_bytes", "sha256"}, "implementation file")
        require_int(file["size_bytes"], "implementation file size"); require_digest(file["sha256"], "implementation file digest")
    expected_implementation_paths = [path.relative_to(PROJECT_ROOT).as_posix() for path in sorted((PROJECT_ROOT / "chatgnt").glob("*.py")) if path.is_file()]
    if [item["path"] for item in implementation["behaviour_files"]] != expected_implementation_paths:
        raise ContractError("implementation file list does not cover every chatgnt/*.py file")
    prompt_set = manifest["prompt_set"]
    require_digest(prompt_set["source_sha256"], "prompt source digest"); require_digest(prompt_set["frozen_sha256"], "frozen prompt digest")
    require_int(prompt_set["prompt_count"], "prompt_count")
    if not isinstance(prompt_set["prompt_ids"], list) or not all(isinstance(item, str) for item in prompt_set["prompt_ids"]):
        raise ContractError("prompt_ids must be a string list")
    systems = manifest["system_set"]["systems"]
    require_digest(manifest["system_set"]["source_sha256"], "system-set source digest")
    if not isinstance(systems, list) or not 1 <= len(systems) <= 4:
        raise ContractError("manifest systems must contain one to four entries")
    seen_systems: set[str] = set()
    for system in systems:
        require_exact_keys(system, {"system_id", "adapter_enabled", "prompt_asset"}, "manifest system")
        if system["system_id"] not in "ABCD" or system["system_id"] in seen_systems:
            raise ContractError("manifest system identity is invalid or duplicated")
        if system["adapter_enabled"] != (system["system_id"] in "CD"):
            raise ContractError("manifest system adapter flag mismatch")
        seen_systems.add(system["system_id"])
        asset = system["prompt_asset"]
        require_exact_keys(asset, {"source_path", "source_sha256", "schema_version", "prompt_asset_id", "version", "worked_example_count", "content"}, "manifest prompt asset")
        require_digest(asset["source_sha256"], "prompt asset digest"); require_identifier(asset["prompt_asset_id"], "prompt_asset_id")
        if asset["schema_version"] != 1 or not isinstance(asset["version"], str) or not asset["version"] or not isinstance(asset["content"], str):
            raise ContractError("manifest prompt asset value mismatch")
        count = require_int(asset["worked_example_count"], "worked_example_count")
        if system["system_id"] in "AC" and (asset["content"] != "" or count != 0): raise ContractError("manifest minimal asset invariant")
        if system["system_id"] in "BD" and (not asset["content"] or count != 5): raise ContractError("manifest five-shot asset invariant")
    schedule = manifest["schedule"]
    require_int(schedule["run_seed"], "run_seed", 0, 2**64 - 1); require_int(schedule["order_seed"], "order_seed", 0, 2**64 - 1)
    if schedule["order_seed"] != execution_order_seed(schedule["run_seed"]): raise ContractError("order seed mismatch")
    if schedule["seed_algorithm"] != "sha256-first-8-big-endian-v1" or schedule["order_algorithm"] != "sha256-sort-v1" or schedule["primary_samples_per_system_prompt"] != 1:
        raise ContractError("schedule algorithm mismatch")
    if not isinstance(schedule["attempts"], list) or schedule["scheduled_attempt_count"] != len(schedule["attempts"]): raise ContractError("schedule count mismatch")
    for index, attempt in enumerate(schedule["attempts"]):
        require_exact_keys(attempt, {"attempt_index", "prompt_id", "system_id", "repeat_index", "generation_seed"}, "scheduled attempt")
        if attempt["attempt_index"] != index: raise ContractError("attempt indices must be contiguous")
    for file in manifest["model"]["behaviour_files"]:
        require_exact_keys(file, {"path", "size_bytes", "sha256"}, "model behaviour file")
        require_int(file["size_bytes"], "model file size"); require_digest(file["sha256"], "model file digest")
    model = manifest["model"]
    require_int(model["parameter_count"], "model parameter_count"); require_int(model["max_context_tokens"], "model max_context_tokens", 1)
    require_digest(model["weights_sha256"], "model weights digest")
    if not isinstance(model["effective_generation_config"], dict): raise ContractError("effective generation configuration must be an object")
    tokenizer = manifest["tokenizer"]
    require_int(tokenizer["length"], "tokenizer length", 1); require_int(tokenizer["eos_token_id"], "tokenizer EOS")
    require_int(tokenizer["pad_token_id"], "tokenizer padding ID"); require_digest(tokenizer["chat_template_sha256"], "chat-template digest")
    if not isinstance(tokenizer["generation_eos_token_ids"], list) or not tokenizer["generation_eos_token_ids"] or any(isinstance(item, bool) or not isinstance(item, int) for item in tokenizer["generation_eos_token_ids"]): raise ContractError("generation EOS IDs are invalid")
    if not isinstance(tokenizer["all_special_ids"], list) or any(isinstance(item, bool) or not isinstance(item, int) for item in tokenizer["all_special_ids"]): raise ContractError("special-token IDs are invalid")
    for name, entry in manifest["configuration"].items():
        require_exact_keys(entry, {"source_path", "source_sha256", "values"}, f"configuration.{name}")
        require_digest(entry["source_sha256"], f"configuration.{name}.source_sha256")
        if not isinstance(entry["values"], dict): raise ContractError("configuration values must be objects")
    adapter = manifest["adapter"]
    if adapter is not None:
        require_exact_keys(adapter, {"path", "adapter_id", "adapter_version", "adapter_digest", "behaviour_files", "provenance", "provenance_sha256", "peft_config", "active_adapters", "trainable_parameter_count", "parameter_dtypes", "merged"}, "adapter")
        require_exact_keys(adapter["path"], {"kind", "value"}, "adapter.path")
        if adapter["path"]["kind"] not in ("project-relative", "host-absolute"): raise ContractError("adapter path kind mismatch")
        require_digest(adapter["adapter_digest"], "adapter digest")
        if tree_digest(adapter["behaviour_files"]) != adapter["adapter_digest"]: raise ContractError("adapter tree digest mismatch")
        if adapter["active_adapters"] != ["chatgnt"] or adapter["trainable_parameter_count"] != 0 or adapter["merged"] is not False:
            raise ContractError("adapter runtime invariant mismatch")
        if adapter["provenance"] is None and manifest["diagnostic"] is None:
            raise ContractError("null adapter provenance requires the CUDA-smoke diagnostic declaration")
        if adapter["provenance"] is not None:
            require_exact_keys(adapter["provenance"], ADAPTER_PROVENANCE_KEYS, "adapter provenance")
            require_digest(adapter["provenance_sha256"], "adapter provenance digest")
        elif adapter["provenance_sha256"] is not None:
            raise ContractError("null provenance requires a null provenance digest")
        if not isinstance(adapter["peft_config"], dict) or not isinstance(adapter["parameter_dtypes"], list) or not all(isinstance(item, str) for item in adapter["parameter_dtypes"]):
            raise ContractError("adapter PEFT config or dtype evidence is invalid")
    if manifest["diagnostic"] is not None:
        require_exact_keys(manifest["diagnostic"], {"kind", "experimental_result", "adapter_provenance_bypass", "adapter_provenance_bypass_reason"}, "diagnostic")
        if manifest["diagnostic"] != {"kind": "cuda-smoke", "experimental_result": False, "adapter_provenance_bypass": True, "adapter_provenance_bypass_reason": "lifecycle adapter predates formal provenance"}: raise ContractError("invalid diagnostic declaration")
    formal_root = (PROJECT_ROOT / "experiments" / "runs").resolve()
    if run_dir.resolve().is_relative_to(formal_root) and (manifest["diagnostic"] is not None or (manifest["adapter"] is not None and manifest["adapter"]["provenance"] is None)):
        raise ContractError("diagnostic provenance bypass is forbidden in formal runs")


def inspect_run(run_dir: Path) -> dict[str, Any]:
    report = _blank_report(); errors: list[dict[str, str]] = []
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        report["integrity_errors"] = [_integrity("run_dir", "unreadable", "run directory is missing or unreadable")]
        return report
    manifest_path = run_dir / "manifest.json"
    try:
        raw = manifest_path.read_bytes(); manifest = strict_json_loads(raw.decode("utf-8"))
        if raw != canonical_line(manifest): raise ContractError("manifest is not canonically serialized")
        _validate_manifest(manifest, run_dir); report["run_id"] = manifest["run_id"]
    except BaseException as exc:
        report["integrity_errors"] = [_integrity("manifest.json", "invalid", str(exc))]
        return report
    prompts_by_id: dict[str, Prompt] = {}
    try:
        prompts, frozen = load_prompts(run_dir / "prompts.jsonl")
        expected_frozen = _canonical_prompts(prompts)
        if frozen != expected_frozen: raise ContractError("prompts.jsonl is not canonically serialized")
        if sha256_bytes(frozen) != manifest["prompt_set"]["frozen_sha256"]: raise ContractError("frozen prompt digest mismatch")
        if [p.prompt_id for p in prompts] != manifest["prompt_set"]["prompt_ids"] or len(prompts) != manifest["prompt_set"]["prompt_count"]: raise ContractError("frozen prompt identity mismatch")
        prompts_by_id = {p.prompt_id: p for p in prompts}
        regenerated = schedule_attempts(manifest["schedule"]["run_seed"], [p.prompt_id for p in prompts], [s["system_id"] for s in manifest["system_set"]["systems"]])
        if [item.to_dict() for item in regenerated] != manifest["schedule"]["attempts"]:
            raise ContractError("frozen schedule does not match seed, prompts, and systems")
    except BaseException as exc:
        errors.append(_integrity("prompts.jsonl", "invalid", str(exc)))
    attempts = manifest["schedule"]["attempts"]
    report["scheduled_count"] = len(attempts)
    if manifest["schedule"]["scheduled_attempt_count"] != len(attempts): errors.append(_integrity("manifest.schedule", "count", "scheduled attempt count mismatch"))
    expected = {item["attempt_index"]: item for item in attempts if isinstance(item, dict) and "attempt_index" in item}
    seen: dict[int, int] = {}
    unexpected: set[int] = set(); malformed: list[int] = []; valid = 0; line_count = 0
    response_path = run_dir / "responses.jsonl"
    try:
        response_lines = response_path.read_bytes().splitlines(keepends=True)
    except BaseException as exc:
        response_lines = []; errors.append(_integrity("responses.jsonl", "unreadable", str(exc)))
    for line_number, raw_line in enumerate(response_lines, 1):
        line_count += 1
        try:
            if not raw_line.endswith(b"\n"): raise ContractError("partial line")
            record = strict_json_loads(raw_line[:-1].decode("utf-8"))
            if raw_line != canonical_line(record): raise ContractError("noncanonical record")
            if not isinstance(record, dict): raise ContractError("record must be object")
            require_exact_keys(record, ATTEMPT_KEYS, "attempt")
            index = require_int(record.get("attempt_index"), "attempt_index")
        except BaseException as exc:
            malformed.append(line_number); errors.append(_integrity(f"responses.jsonl:{line_number}", "invalid", str(exc)))
            continue
        if index not in expected:
            unexpected.add(index); errors.append(_integrity(f"responses.jsonl:{line_number}", "unexpected", "unexpected attempt index")); continue
        seen[index] = seen.get(index, 0) + 1
        try:
            _validate_attempt(record, expected[index], manifest, prompts_by_id)
            valid += 1
        except BaseException as exc:
            errors.append(_integrity(f"responses.jsonl:{line_number}", "integrity", str(exc)))
    duplicates = sorted(index for index, count in seen.items() if count > 1)
    report.update({"response_line_count": line_count, "valid_response_count": valid,
        "unique_recorded_attempt_count": len(seen), "missing_attempt_indices": sorted(set(expected) - set(seen)),
        "duplicate_attempt_indices": duplicates, "unexpected_attempt_indices": sorted(unexpected),
        "malformed_line_numbers": sorted(set(malformed))})
    report["integrity_errors"] = sorted(errors, key=lambda item: (item["location"], item["code"], item["message"]))
    report["complete"] = not report["missing_attempt_indices"] and not duplicates and not unexpected and not malformed and not errors and valid == len(expected)
    return report


def _diagnostic_declaration() -> dict[str, Any]:
    return {"kind": "cuda-smoke", "experimental_result": False, "adapter_provenance_bypass": True,
        "adapter_provenance_bypass_reason": "lifecycle adapter predates formal provenance"}


def cuda_smoke(device: str, adapter_path: Path) -> tuple[int, Path | None, dict[str, Any] | None]:
    expected_adapter = (PROJECT_ROOT / "artifacts" / "diagnostics" / "lora-lifecycle-adapter").resolve()
    if adapter_path.resolve() != expected_adapter:
        raise ContractError("CUDA smoke provenance bypass is restricted to the lifecycle adapter")
    root = PROJECT_ROOT / "artifacts" / "diagnostics" / "inference-harness-cuda"
    with tempfile.TemporaryDirectory(prefix="chatgnt-cuda-smoke-") as temporary:
        tmp = Path(temporary); asset = tmp / "minimal.json"
        asset.write_bytes(canonical_line({"schema_version": 1, "prompt_asset_id": "minimal-v1", "version": "1", "worked_example_count": 0, "content": ""}))
        prompts = tmp / "prompts.jsonl"; prompts.write_bytes(canonical_line({"prompt_id": "cuda-smoke", "prompt": "Respond briefly.", "metadata": {"diagnostic": True}}))
        systems = tmp / "systems.json"; systems.write_bytes(canonical_line({"schema_version": 1, "systems": [
            {"system_id": "A", "prompt_asset_path": "minimal.json", "adapter_enabled": False},
            {"system_id": "C", "prompt_asset_path": "minimal.json", "adapter_enabled": True}]}))
        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
        return execute_run(prompts, systems, 20260714, device, adapter_path, run_id, root,
            _diagnostic_declaration(), True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m chatgnt.harness")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run"); run.add_argument("--prompts", type=Path, required=True); run.add_argument("--system-set", type=Path, required=True); run.add_argument("--run-seed", type=int, required=True); run.add_argument("--device", required=True); run.add_argument("--adapter-path", type=Path); run.add_argument("--run-id"); run.add_argument("--runs-root", type=Path, default=PROJECT_ROOT / "experiments" / "runs")
    inspect = sub.add_parser("inspect"); inspect.add_argument("--run-dir", type=Path, required=True)
    cuda = sub.add_parser("cuda-smoke"); cuda.add_argument("--device", required=True); cuda.add_argument("--adapter-path", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            report = inspect_run(args.run_dir); print(canonical_json(report))
            return 0 if report["complete"] else (2 if not args.run_dir.is_dir() else 1)
        if args.command == "cuda-smoke":
            code, run_dir, report = cuda_smoke(args.device, args.adapter_path)
        else:
            code, run_dir, report = execute_run(args.prompts, args.system_set, args.run_seed, args.device,
                args.adapter_path, args.run_id, args.runs_root)
        print(canonical_json({"exit_status": code, "run_dir": str(run_dir) if run_dir else None, "completeness": report}))
        return code
    except KeyboardInterrupt:
        return 130
    except RuntimeAbort as exc:
        print(canonical_json({"error": {"type": exc.__class__.__name__, "message": str(exc)}}), file=sys.stderr); return 3
    except BaseException as exc:
        print(canonical_json({"error": {"type": exc.__class__.__name__, "message": str(exc)}}), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
