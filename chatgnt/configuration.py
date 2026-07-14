"""Strict input and project-configuration parsing for specification 1.2."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import tomllib
from typing import Any

from .identity import file_identity, sha256_bytes, sha256_file, tree_digest
from .records import (
    ContractError, GenerationProfile, TimingPolicy, read_strict_json,
    require_digest, require_exact_keys, require_identifier, require_int,
    strict_json_loads, validate_json_value,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_ROOT = PROJECT_ROOT / "config"

EXPECTED_MODEL = {
    "base_model": {
        "id": "Qwen/Qwen2.5-1.5B-Instruct",
        "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
        "source": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct",
        "license": "apache-2.0", "architecture": "Qwen2ForCausalLM",
        "parameter_count": 1543714304, "weight_dtype": "bfloat16",
        "weights_sha256": "dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee",
        "max_context_tokens": 32768,
    },
    "tokenizer": {
        "class": "Qwen2Tokenizer",
        "chat_template_sha256": "cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f",
        "reported_model_max_length": 131072,
    },
    "canonical_chat": {"vendor_system_message": False, "minimal_system_message": "", "add_generation_prompt": True},
}

EXPECTED_GENERATION = {
    "primary": {"do_sample": True, "temperature": .7, "top_p": .8, "top_k": 20,
        "repetition_penalty": 1.1, "max_new_tokens": 512, "batch_size": 1,
        "num_beams": 1, "num_return_sequences": 1, "use_cache": True,
        "cache_implementation": "dynamic", "return_dict_in_generate": False,
        "output_scores": False, "output_logits": False, "min_new_tokens": 0},
    "stopping": {"eos_token_ids": [151645, 151643], "pad_token_id": 151643, "stop_strings": []},
    "decoding": {"skip_special_tokens": True, "clean_up_tokenization_spaces": False,
        "strip_whitespace": False, "unicode_normalization": False},
    "token_accounting": {"generated_count_includes_terminal_token": True,
        "visible_count_excludes_special_tokens": True, "input_count_uses_complete_rendered_prompt": True},
    "input_policy": {"truncation": False, "overlength_action": "record-error"},
    "seed_policy": {"strategy": "derived-per-prompt", "components": ["run_seed", "prompt_id", "repeat_index"],
        "include_system_id": False, "primary_samples_per_system_prompt": 1,
        "rng_application": "forked-device-state-v1"},
    "constraints": {"constrained_decoding": False, "beam_search": False,
        "automatic_retries": False, "output_repair": False},
    "timing": {"metric": "synchronized-model-generate", "clock": "time.perf_counter_ns",
        "cuda_synchronize": True, "include_prompt_prefill": True,
        "include_output_generation": True, "include_tokenization": False,
        "include_model_loading": False, "warmups_per_loaded_runtime": 1,
        "batch_size": 1, "order_strategy": "seeded-random", "reusable_conversation_cache": False},
    "failure_policy": {"preflight_failure_action": "abort-before-run",
        "attempt_statuses": ["success", "input_context_exceeded", "generation_error"],
        "record_exception_type": True, "record_exception_message": True,
        "automatic_retries": False, "continue_after_isolated_generation_error": True,
        "cuda_runtime_error_action": "record-then-abort", "preserve_partial_run": True,
        "impute_missing_attempts": False,
        "completion_rule": "exactly-one-record-per-scheduled-combination"},
}

EXPECTED_INFERENCE = {
    "runtime": {"dtype": "bfloat16", "attention_implementation": "sdpa",
        "device_map_strategy": "single-device", "quantization": False, "compile": False,
        "offload": False, "low_cpu_mem_usage": True},
    "adapter": {"adapter_name": "chatgnt", "is_trainable": False,
        "autocast_adapter_dtype": True, "ephemeral_gpu_offload": False,
        "low_cpu_mem_usage": False, "merged": False},
}


@dataclass(frozen=True)
class SourceConfig:
    path: Path
    sha256: str
    values: dict[str, Any]

    def manifest_value(self) -> dict[str, Any]:
        return {"source_path": self.path.relative_to(PROJECT_ROOT).as_posix(), "source_sha256": self.sha256, "values": self.values}


@dataclass(frozen=True)
class ProjectConfiguration:
    model: SourceConfig
    generation: SourceConfig
    inference: SourceConfig

    @property
    def primary_profile(self) -> GenerationProfile:
        primary = self.generation.values["primary"]
        stopping = self.generation.values["stopping"]
        return GenerationProfile(
            profile_id="primary-sampled-v1", do_sample=primary["do_sample"],
            temperature=primary["temperature"], top_p=primary["top_p"], top_k=primary["top_k"],
            repetition_penalty=primary["repetition_penalty"], max_new_tokens=primary["max_new_tokens"],
            min_new_tokens=primary["min_new_tokens"], eos_token_ids=tuple(stopping["eos_token_ids"]),
            pad_token_id=stopping["pad_token_id"], num_beams=primary["num_beams"],
            num_return_sequences=primary["num_return_sequences"], use_cache=primary["use_cache"],
            cache_implementation=primary["cache_implementation"],
            return_dict_in_generate=primary["return_dict_in_generate"], output_scores=primary["output_scores"],
            output_logits=primary["output_logits"], stop_strings=None,
        )

    @property
    def timing_policy(self) -> TimingPolicy:
        return TimingPolicy("synchronized-model-generate", True, True, True)


def _load_toml_exact(path: Path, expected: dict[str, Any]) -> SourceConfig:
    raw = path.read_bytes()
    try:
        values = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ContractError(f"{path}: {exc}") from exc
    def same_typed_value(actual: Any, reference: Any) -> bool:
        if type(actual) is not type(reference):
            return False
        if isinstance(reference, dict):
            return set(actual) == set(reference) and all(
                same_typed_value(actual[key], reference[key]) for key in reference
            )
        if isinstance(reference, list):
            return len(actual) == len(reference) and all(
                same_typed_value(left, right) for left, right in zip(actual, reference)
            )
        return actual == reference
    if not same_typed_value(values, expected):
        raise ContractError(f"{path}: values or closed schema differ from specification 1.2")
    return SourceConfig(path, sha256_bytes(raw), values)


def load_project_configuration(config_root: Path = CONFIG_ROOT) -> ProjectConfiguration:
    result = ProjectConfiguration(
        _load_toml_exact(config_root / "model.toml", EXPECTED_MODEL),
        _load_toml_exact(config_root / "generation.toml", EXPECTED_GENERATION),
        _load_toml_exact(config_root / "inference.toml", EXPECTED_INFERENCE),
    )
    if result.primary_profile.pad_token_id != result.generation.values["stopping"]["pad_token_id"]:
        raise ContractError("padding identity mismatch")
    if result.primary_profile.max_new_tokens >= result.model.values["base_model"]["max_context_tokens"]:
        raise ContractError("generation ceiling leaves no positive input allowance")
    return result


@dataclass(frozen=True)
class Prompt:
    prompt_id: str
    prompt: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"prompt_id": self.prompt_id, "prompt": self.prompt, "metadata": self.metadata}


def load_prompts(path: Path) -> tuple[list[Prompt], bytes]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContractError(f"{path}: byte-order mark is not permitted")
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ContractError(f"{path}: invalid UTF-8") from exc
    prompts: list[Prompt] = []
    seen: set[str] = set()
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        value = strict_json_loads(line)
        if not isinstance(value, dict) or set(value) not in ({"prompt_id", "prompt"}, {"prompt_id", "prompt", "metadata"}):
            raise ContractError(f"{path}:{line_number}: invalid prompt keys")
        prompt_id = require_identifier(value["prompt_id"], f"{path}:{line_number}.prompt_id")
        if prompt_id in seen:
            raise ContractError(f"{path}:{line_number}: duplicate prompt_id {prompt_id}")
        prompt = value["prompt"]
        if not isinstance(prompt, str) or not prompt:
            raise ContractError(f"{path}:{line_number}: prompt must be non-empty")
        metadata = value.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ContractError(f"{path}:{line_number}: metadata must be object")
        validate_json_value(metadata, "metadata")
        prompts.append(Prompt(prompt_id, prompt, metadata))
        seen.add(prompt_id)
    if not prompts:
        raise ContractError(f"{path}: at least one prompt is required")
    return prompts, raw


@dataclass(frozen=True)
class PromptAsset:
    source_path: Path
    source_sha256: str
    schema_version: int
    prompt_asset_id: str
    version: str
    worked_example_count: int
    content: str

    def manifest_value(self) -> dict[str, Any]:
        return {"source_path": project_path(self.source_path)["value"], "source_sha256": self.source_sha256,
            "schema_version": self.schema_version, "prompt_asset_id": self.prompt_asset_id,
            "version": self.version, "worked_example_count": self.worked_example_count, "content": self.content}


def load_prompt_asset(path: Path) -> PromptAsset:
    value, raw = read_strict_json(path)
    require_exact_keys(value, {"schema_version", "prompt_asset_id", "version", "worked_example_count", "content"}, str(path))
    if require_int(value["schema_version"], "schema_version") != 1:
        raise ContractError(f"{path}: unsupported schema_version")
    asset_id = require_identifier(value["prompt_asset_id"], "prompt_asset_id")
    if not isinstance(value["version"], str) or not value["version"]:
        raise ContractError(f"{path}: version must be non-empty")
    count = require_int(value["worked_example_count"], "worked_example_count")
    if not isinstance(value["content"], str):
        raise ContractError(f"{path}: content must be string")
    return PromptAsset(path.resolve(), sha256_bytes(raw), 1, asset_id, value["version"], count, value["content"])


@dataclass(frozen=True)
class SystemDefinition:
    system_id: str
    adapter_enabled: bool
    prompt_asset: PromptAsset

    def manifest_value(self) -> dict[str, Any]:
        return {"system_id": self.system_id, "adapter_enabled": self.adapter_enabled,
            "prompt_asset": self.prompt_asset.manifest_value()}


def load_system_set(path: Path, adapter_path: Path | None) -> tuple[list[SystemDefinition], bytes]:
    value, raw = read_strict_json(path)
    require_exact_keys(value, {"schema_version", "systems"}, str(path))
    if require_int(value["schema_version"], "schema_version") != 1 or not isinstance(value["systems"], list):
        raise ContractError(f"{path}: invalid system set")
    if not 1 <= len(value["systems"]) <= 4:
        raise ContractError("systems must contain one to four definitions")
    definitions: list[SystemDefinition] = []
    seen: set[str] = set()
    for index, item in enumerate(value["systems"]):
        require_exact_keys(item, {"system_id", "prompt_asset_path", "adapter_enabled"}, f"systems[{index}]")
        system_id = item["system_id"]
        if system_id not in ("A", "B", "C", "D") or system_id in seen:
            raise ContractError(f"systems[{index}]: invalid or duplicate system_id")
        enabled = item["adapter_enabled"]
        if not isinstance(enabled, bool) or enabled != (system_id in ("C", "D")):
            raise ContractError(f"system {system_id}: adapter flag mismatch")
        relative = item["prompt_asset_path"]
        if not isinstance(relative, str) or not relative:
            raise ContractError("prompt_asset_path must be non-empty string")
        asset = load_prompt_asset((path.parent / relative).resolve())
        if system_id in ("A", "C") and (asset.content != "" or asset.worked_example_count != 0):
            raise ContractError(f"system {system_id}: minimal asset invariant failed")
        if system_id in ("B", "D") and (not asset.content or asset.worked_example_count != 5):
            raise ContractError(f"system {system_id}: five-shot asset invariant failed")
        definitions.append(SystemDefinition(system_id, enabled, asset)); seen.add(system_id)
    definitions.sort(key=lambda item: "ABCD".index(item.system_id))
    mapping = {item.system_id: item for item in definitions}
    for left, right in (("A", "C"), ("B", "D")):
        if left in mapping and right in mapping and mapping[left].prompt_asset.source_sha256 != mapping[right].prompt_asset.source_sha256:
            raise ContractError(f"systems {left}/{right}: prompt assets must be byte-identical")
    needs_adapter = any(item.adapter_enabled for item in definitions)
    if needs_adapter != (adapter_path is not None):
        raise ContractError("adapter path is required exactly when C or D is selected")
    return definitions, raw


MODEL_FILE_NAMES = ["config.json", "generation_config.json", "merges.txt", "model.safetensors", "tokenizer.json", "tokenizer_config.json", "vocab.json"]


def verify_model_files(snapshot: Path, manifest_path: Path = CONFIG_ROOT / "model-files.json") -> list[dict[str, Any]]:
    value, _ = read_strict_json(manifest_path)
    require_exact_keys(value, {"schema_version", "model_id", "revision", "files"}, str(manifest_path))
    if value["schema_version"] != 1 or value["model_id"] != EXPECTED_MODEL["base_model"]["id"] or value["revision"] != EXPECTED_MODEL["base_model"]["revision"]:
        raise ContractError("model-files manifest identity mismatch")
    if not isinstance(value["files"], list) or [item.get("path") for item in value["files"] if isinstance(item, dict)] != MODEL_FILE_NAMES:
        raise ContractError("model-files manifest file set/order mismatch")
    seen: set[str] = set()
    for index, expected in enumerate(value["files"]):
        require_exact_keys(expected, {"path", "size_bytes", "sha256"}, f"files[{index}]")
        if expected["path"] in seen:
            raise ContractError("duplicate model-file entry")
        seen.add(expected["path"]); require_int(expected["size_bytes"], "size_bytes"); require_digest(expected["sha256"], "sha256")
        path = snapshot / expected["path"]
        if not path.is_file() or path.stat().st_size != expected["size_bytes"] or sha256_file(path) != expected["sha256"]:
            raise ContractError(f"pinned model file mismatch: {expected['path']}")
    return value["files"]


ADAPTER_PROVENANCE_KEYS = {"schema_version", "adapter_id", "adapter_version", "adapter_digest", "base_model_id", "base_model_revision", "base_weights_sha256", "training_run_id", "training_dataset_id", "training_dataset_sha256", "peft_version"}


def adapter_identity(path: Path, allow_unprovenanced_diagnostic_adapter: bool = False) -> dict[str, Any]:
    config_path = path / "adapter_config.json"
    weights = sorted(path.rglob("*.safetensors"))
    if not config_path.is_file() or not weights:
        raise ContractError("adapter requires adapter_config.json and at least one safetensors file")
    peft_config, _ = read_strict_json(config_path)
    if not isinstance(peft_config, dict):
        raise ContractError("adapter_config.json must be object")
    behaviour_paths = [config_path, *weights]
    files = [file_identity(item, path) for item in behaviour_paths]
    files.sort(key=lambda item: item["path"])
    digest = tree_digest(files)
    provenance_path = path / "adapter-provenance.json"
    if not provenance_path.is_file():
        if not allow_unprovenanced_diagnostic_adapter:
            raise ContractError("adapter-provenance.json is required")
        provenance = None; provenance_sha = None
        adapter_id = "lora-lifecycle-diagnostic"; adapter_version = "unversioned-diagnostic"
    else:
        provenance, raw = read_strict_json(provenance_path)
        require_exact_keys(provenance, ADAPTER_PROVENANCE_KEYS, str(provenance_path))
        if provenance["schema_version"] != 1:
            raise ContractError("adapter provenance schema mismatch")
        for key, item in provenance.items():
            if key != "schema_version" and (not isinstance(item, str) or not item):
                raise ContractError(f"adapter provenance {key} must be non-empty string")
        for key in ("adapter_digest", "base_weights_sha256", "training_dataset_sha256"):
            require_digest(provenance[key], key)
        if provenance["adapter_digest"] != digest:
            raise ContractError("adapter digest mismatch")
        base = EXPECTED_MODEL["base_model"]
        expected = (base["id"], base["revision"], base["weights_sha256"])
        actual = (provenance["base_model_id"], provenance["base_model_revision"], provenance["base_weights_sha256"])
        if actual != expected:
            raise ContractError("adapter base provenance mismatch")
        import peft
        if provenance["peft_version"] != peft.__version__:
            raise ContractError("adapter PEFT version mismatch")
        provenance_sha = sha256_bytes(raw); adapter_id = provenance["adapter_id"]; adapter_version = provenance["adapter_version"]
    return {"adapter_id": adapter_id, "adapter_version": adapter_version, "adapter_digest": digest,
        "behaviour_files": files, "provenance": provenance, "provenance_sha256": provenance_sha,
        "peft_config": peft_config}


def project_path(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    try:
        return {"kind": "project-relative", "value": resolved.relative_to(PROJECT_ROOT).as_posix()}
    except ValueError:
        return {"kind": "host-absolute", "value": str(resolved)}
