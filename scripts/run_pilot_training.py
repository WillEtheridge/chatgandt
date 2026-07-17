"""Run the verified Stage 6 LoRA workflow; the historical pilot is the default."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
import time
import tomllib
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import peft
import torch
import torch.nn.functional as F
import transformers
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.configuration import adapter_identity, load_project_configuration, verify_model_files  # noqa: E402
from chatgnt.dataset import (  # noqa: E402
    load_canonical_jsonl,
    load_dataset_contract,
    render_training_messages,
)
from chatgnt.identity import sha256_file, sha256_text  # noqa: E402
from chatgnt.records import canonical_line, read_strict_json  # noqa: E402


CONFIG_PATH = ROOT / "config" / "pilot-training-v1.toml"
MODEL_ROOT = ROOT / "artifacts" / "models"
PROBE_PROMPT = "How can I make a good impression during my first week in a new job?"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-inputs", action="store_true", help="Validate and tokenize inputs without CUDA or output files.")
    parser.add_argument("--run-id", help="Unique immutable run directory name; required for GPU execution.")
    parser.add_argument("--hourly-price-usd", type=float, help="Displayed compute price for cost estimation.")
    return parser.parse_args()


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def canonical_bytes(value: object) -> bytes:
    return canonical_line(value)


def file_record(path: Path, relative_to: Path = ROOT) -> dict[str, Any]:
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def model_path(model_id: str, revision: str) -> Path:
    return MODEL_ROOT / model_id.replace("/", "--") / revision


def git_record() -> dict[str, Any]:
    def run(*arguments: str) -> str:
        return subprocess.run(["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()

    return {"commit": run("rev-parse", "HEAD"), "dirty": bool(run("status", "--porcelain"))}


def nvidia_record() -> dict[str, Any]:
    completed = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
    )
    fields = [item.strip() for item in completed.stdout.strip().split(",")]
    if len(fields) != 3:
        raise RuntimeError(f"Unexpected nvidia-smi output: {completed.stdout!r}")
    return {"name": fields[0], "driver_version": fields[1], "reported_memory_mib": int(fields[2])}


def task_type(value: str) -> TaskType:
    try:
        return TaskType[value]
    except KeyError as exc:
        raise ValueError(f"Unsupported task type: {value}") from exc


def group_events(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[event["example_id"]].append(event)
    return grouped


def assistant_content_spans(response: dict[str, Any]) -> tuple[str, list[tuple[int, int]]]:
    """Render canonical JSON and locate answer-bearing ingredient/method string spans."""

    parts: list[str] = []
    spans: list[tuple[int, int]] = []
    length = 0

    def append(value: str) -> None:
        nonlocal length
        parts.append(value)
        length += len(value)

    def append_json_string(value: str, weighted: bool = False) -> None:
        literal = json.dumps(value, ensure_ascii=False, allow_nan=False)
        start = length + 1
        append(literal)
        if weighted:
            spans.append((start, length - 1))

    append('{"title":')
    append_json_string(response["title"])
    append(',"ingredients":[')
    for index, ingredient in enumerate(response["ingredients"]):
        if index:
            append(",")
        append('{"amount":')
        append(json.dumps(ingredient["amount"], ensure_ascii=False, allow_nan=False))
        append(',"unit":')
        append_json_string(ingredient["unit"])
        append(',"name":')
        append_json_string(ingredient["name"], weighted=True)
        append("}")
    append('],"method":[')
    for index, step in enumerate(response["method"]):
        if index:
            append(",")
        append_json_string(step, weighted=True)
    append('],"garnish":')
    append_json_string(response["garnish"])
    append("}")
    return "".join(parts), spans


def content_loss_weights(
    tokenizer: Any,
    complete_ids: torch.Tensor,
    prompt_token_count: int,
    response: dict[str, Any],
    base_weight: float,
    content_weight: float,
) -> tuple[torch.Tensor, int]:
    """Map canonical content spans onto exact assistant token positions."""

    rendered, spans = assistant_content_spans(response)
    content_ids = tokenizer.encode(rendered, add_special_tokens=False)
    content_tensor = torch.tensor(content_ids, dtype=complete_ids.dtype)
    supervised = complete_ids[prompt_token_count:]
    if content_tensor.numel() > supervised.numel() or not torch.equal(
        supervised[: content_tensor.numel()], content_tensor
    ):
        raise ValueError("canonical assistant JSON tokens do not align with the complete chat template")

    prefixes = [
        tokenizer.decode(content_ids[:index], skip_special_tokens=False,
                         clean_up_tokenization_spaces=False)
        for index in range(len(content_ids) + 1)
    ]
    if prefixes[-1] != rendered or any(not rendered.startswith(prefix) for prefix in prefixes):
        raise ValueError("token-to-character alignment does not reproduce canonical assistant JSON")

    weights = torch.zeros(complete_ids.shape[0], dtype=torch.float32)
    weights[prompt_token_count:] = base_weight
    weighted_tokens = 0
    for index in range(len(content_ids)):
        start, end = len(prefixes[index]), len(prefixes[index + 1])
        overlaps = any(start < span_end and end > span_start for span_start, span_end in spans)
        if overlaps:
            weights[prompt_token_count + index] = content_weight
            weighted_tokens += 1
    if weighted_tokens == 0:
        raise ValueError("content-weighted example contains no weighted tokens")
    return weights, weighted_tokens


def tokenize_record(
    record: dict[str, Any],
    events: list[dict[str, Any]],
    contract: dict[str, Any],
    tokenizer: Any,
    maximum_length: int,
    loss_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    messages = render_training_messages(record, events, contract)
    prompt_messages = messages[:-1]
    prompt_ids = tokenizer.apply_chat_template(
        prompt_messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).input_ids[0]
    complete_ids = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=False, return_tensors="pt"
    ).input_ids[0]
    if complete_ids.shape[0] > maximum_length:
        raise ValueError(f"{record['example_id']} has {complete_ids.shape[0]} tokens, exceeding {maximum_length}; truncation is forbidden")
    if not torch.equal(complete_ids[: prompt_ids.shape[0]], prompt_ids):
        raise ValueError(f"{record['example_id']} prompt tokens are not an exact prefix of the complete example")
    labels = complete_ids.clone()
    labels[: prompt_ids.shape[0]] = -100
    supervised = int((labels != -100).sum().item())
    if supervised < 2:
        raise ValueError(f"{record['example_id']} has insufficient supervised tokens")
    result = {
        "example_id": record["example_id"],
        "input_ids": complete_ids,
        "labels": labels,
        "prompt_tokens": int(prompt_ids.shape[0]),
        "total_tokens": int(complete_ids.shape[0]),
        "supervised_tokens": supervised,
    }
    if loss_config is not None and loss_config.get("mode") == "content_weighted_assistant_only":
        weights, weighted_tokens = content_loss_weights(
            tokenizer, complete_ids, int(prompt_ids.shape[0]), record["assistant_response"],
            float(loss_config["base_weight"]), float(loss_config["content_weight"]),
        )
        result["loss_weights"] = weights
        result["content_weighted_tokens"] = weighted_tokens
    return result


def collate(items: list[dict[str, Any]], pad_token_id: int) -> dict[str, torch.Tensor]:
    width = max(item["input_ids"].shape[0] for item in items)
    input_ids = torch.full((len(items), width), pad_token_id, dtype=torch.long)
    attention_mask = torch.zeros((len(items), width), dtype=torch.long)
    labels = torch.full((len(items), width), -100, dtype=torch.long)
    has_weights = ["loss_weights" in item for item in items]
    if any(has_weights) and not all(has_weights):
        raise ValueError("a batch cannot mix weighted and unweighted examples")
    loss_weights = torch.zeros((len(items), width), dtype=torch.float32) if all(has_weights) else None
    for row, item in enumerate(items):
        length = item["input_ids"].shape[0]
        input_ids[row, :length] = item["input_ids"]
        attention_mask[row, :length] = 1
        labels[row, :length] = item["labels"]
        if loss_weights is not None:
            loss_weights[row, :length] = item["loss_weights"]
    result = {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}
    if loss_weights is not None:
        result["loss_weights"] = loss_weights
    return result


def weighted_causal_loss(
    logits: torch.Tensor, labels: torch.Tensor, loss_weights: torch.Tensor
) -> torch.Tensor:
    """Weighted next-token cross-entropy, normalised by active weight mass."""

    shifted_logits = logits[:, :-1, :].contiguous().float()
    shifted_labels = labels[:, 1:].contiguous()
    shifted_weights = loss_weights[:, 1:].contiguous()
    active = shifted_labels != -100
    active_weights = shifted_weights * active
    denominator = active_weights.sum()
    if not bool(torch.isfinite(denominator)) or float(denominator.item()) <= 0.0:
        raise RuntimeError("weighted loss requires positive finite active weight mass")
    token_losses = F.cross_entropy(
        shifted_logits.view(-1, shifted_logits.shape[-1]), shifted_labels.view(-1),
        reduction="none", ignore_index=-100,
    ).view_as(shifted_labels)
    return (token_losses * active_weights).sum() / denominator


def epoch_batches(items: list[dict[str, Any]], batch_size: int, seed: int, epoch: int) -> list[list[dict[str, Any]]]:
    indices = list(range(len(items)))
    random.Random(seed + epoch).shuffle(indices)
    if len(indices) % batch_size:
        raise ValueError("training size must divide exactly by micro-batch size")
    return [[items[index] for index in indices[start : start + batch_size]] for start in range(0, len(indices), batch_size)]


def evaluate(model: torch.nn.Module, items: list[dict[str, Any]], batch_size: int, pad_token_id: int, device: torch.device) -> dict[str, float | int]:
    model.eval()
    loss_sum = 0.0
    token_count = 0
    with torch.inference_mode():
        for start in range(0, len(items), batch_size):
            batch = collate(items[start : start + batch_size], pad_token_id)
            batch = {key: value.to(device) for key, value in batch.items()}
            output = model(**batch)
            count = int((batch["labels"][:, 1:] != -100).sum().item())
            loss_sum += float(output.loss.item()) * count
            token_count += count
    return {"loss": loss_sum / token_count, "supervised_prediction_tokens": token_count}


def last_token_logits(model: torch.nn.Module, input_ids: torch.Tensor) -> torch.Tensor:
    model.eval()
    with torch.inference_mode():
        return model(input_ids=input_ids).logits[:, -1, :].float().cpu().clone()


def load_base(snapshot: Path, device: torch.device, gradient_checkpointing: bool) -> torch.nn.Module:
    model = AutoModelForCausalLM.from_pretrained(
        snapshot,
        local_files_only=True,
        dtype=torch.bfloat16,
        device_map={"": device},
        low_cpu_mem_usage=True,
        attn_implementation="sdpa",
    )
    model.config.use_cache = False
    if gradient_checkpointing:
        model.gradient_checkpointing_enable()
    return model


def training_collection(config: dict[str, Any]) -> tuple[str, str, str]:
    role = config["run"].get("training_role", "pilot")
    if role == "pilot":
        return role, "pilot_path", "expected_pilot_count"
    if role == "train":
        return role, "training_path", "expected_training_count"
    raise ValueError(f"unsupported training role: {role}")


def validate_loss_config(config: dict[str, Any]) -> dict[str, Any]:
    loss = config.get("loss", {"mode": "standard_assistant_only"})
    mode = loss.get("mode")
    if mode == "standard_assistant_only":
        if set(loss) != {"mode"}:
            raise ValueError("standard loss configuration accepts only mode")
        return loss
    expected = {
        "mode", "base_weight", "content_weight", "content_fields", "validation_mode",
    }
    if mode != "content_weighted_assistant_only" or set(loss) != expected:
        raise ValueError("unsupported or incomplete training loss configuration")
    if loss["base_weight"] != 1.0 or loss["content_weight"] != 2.0:
        raise ValueError("content-weighted loss requires frozen weights 1.0 and 2.0")
    if loss["content_fields"] != ["ingredients.name", "method"]:
        raise ValueError("content-weighted loss fields drifted")
    if loss["validation_mode"] != "standard_assistant_only":
        raise ValueError("validation loss must remain standard assistant-only")
    return loss


def prepare_inputs(config: dict[str, Any]) -> tuple[dict[str, Any], Any, list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    project = load_project_configuration()
    selected = project.model.values["base_model"]
    snapshot = model_path(selected["id"], selected["revision"])
    if not snapshot.is_dir():
        raise FileNotFoundError(f"Pinned model snapshot missing: {snapshot}")
    verify_model_files(snapshot)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    if sha256_text(tokenizer.chat_template) != project.model.values["tokenizer"]["chat_template_sha256"]:
        raise ValueError("tokenizer chat template identity mismatch")
    if tokenizer.pad_token_id is None:
        raise ValueError("tokenizer must define a pad token")

    data = config["data"]
    role, training_path_key, expected_count_key = training_collection(config)
    paths = {
        "training": ROOT / data[training_path_key],
        "validation": ROOT / data["validation_path"],
        "workflow_events": ROOT / data["workflow_events_path"],
        "dataset_manifest": ROOT / data["dataset_manifest_path"],
    }
    manifest, _ = read_strict_json(paths["dataset_manifest"])
    if manifest["dataset_id"] != data["expected_dataset_id"] or manifest["status"] != "frozen":
        raise ValueError("unexpected or unfrozen dataset manifest")
    expected_files = {item["path"]: item["sha256"] for item in manifest["files"]}
    for name in ("training", "validation"):
        path = paths[name]
        if sha256_file(path) != expected_files[path.name]:
            raise ValueError(f"{name} file identity does not match the frozen manifest")

    training_records = load_canonical_jsonl(paths["training"])
    validation_records = load_canonical_jsonl(paths["validation"])
    events = group_events(load_canonical_jsonl(paths["workflow_events"]))
    if len(training_records) != data[expected_count_key] or any(item["split"] != "train" for item in training_records):
        raise ValueError("training collection does not match its frozen role")
    if role == "pilot" and any(not item["pilot_member"] for item in training_records):
        raise ValueError("pilot collection contains a non-pilot training record")
    if role == "train" and {item["example_id"] for item in training_records} != {
        item["example_id"] for item in load_canonical_jsonl(ROOT / "data/dataset-v1/frozen-v1.2/train.jsonl")
    }:
        raise ValueError("full training collection is not the complete frozen training split")
    if len(validation_records) != data["expected_validation_count"] or any(item["split"] != "validation" or item["pilot_member"] for item in validation_records):
        raise ValueError("validation collection does not match its frozen role")
    if {item["scenario_id"] for item in training_records} & {item["scenario_id"] for item in validation_records}:
        raise ValueError("training and validation scenarios overlap")

    contract = load_dataset_contract()
    maximum = data["max_sequence_length"]
    loss_config = validate_loss_config(config)
    training = [
        tokenize_record(item, events[item["example_id"]], contract, tokenizer, maximum,
                        loss_config=loss_config)
        for item in training_records
    ]
    validation = [tokenize_record(item, events[item["example_id"]], contract, tokenizer, maximum) for item in validation_records]
    evidence = {
        "dataset_id": manifest["dataset_id"],
        "training_role": role,
        "manifest": file_record(paths["dataset_manifest"]),
        "training": file_record(paths["training"]),
        "validation": file_record(paths["validation"]),
        "workflow_events": file_record(paths["workflow_events"]),
        "training_count": len(training),
        "validation_count": len(validation),
        "training_token_range": [min(item["total_tokens"] for item in training), max(item["total_tokens"] for item in training)],
        "validation_token_range": [min(item["total_tokens"] for item in validation), max(item["total_tokens"] for item in validation)],
        "training_supervised_token_range": [min(item["supervised_tokens"] for item in training), max(item["supervised_tokens"] for item in training)],
        "validation_supervised_token_range": [min(item["supervised_tokens"] for item in validation), max(item["supervised_tokens"] for item in validation)],
        "training_loss_mode": loss_config["mode"],
        "training_content_weighted_token_range": None if loss_config["mode"] == "standard_assistant_only" else [
            min(item["content_weighted_tokens"] for item in training),
            max(item["content_weighted_tokens"] for item in training),
        ],
        "training_content_weighted_token_count_per_epoch": None if loss_config["mode"] == "standard_assistant_only" else sum(
            item["content_weighted_tokens"] for item in training
        ),
        "validation_loss_mode": "standard_assistant_only",
        "truncated_examples": 0,
    }
    return project.model.values, tokenizer, training, validation, evidence


def validate_config(config: dict[str, Any]) -> dict[str, int]:
    validate_loss_config(config)
    optimization = config["optimization"]
    data = config["data"]
    _, _, expected_count_key = training_collection(config)
    training_count = data[expected_count_key]
    micro_batches = training_count // optimization["micro_batch_size"]
    if training_count % optimization["micro_batch_size"]:
        raise ValueError("training count must divide by micro-batch size")
    if micro_batches % optimization["gradient_accumulation_steps"]:
        raise ValueError("micro-batches per epoch must divide by gradient accumulation")
    steps_per_epoch = micro_batches // optimization["gradient_accumulation_steps"]
    total = steps_per_epoch * optimization["epochs"]
    if total != config["acceptance"]["expected_optimizer_steps"]:
        raise ValueError("configured optimiser-step count is inconsistent")
    return {"micro_batches_per_epoch": micro_batches, "optimizer_steps_per_epoch": steps_per_epoch, "total_optimizer_steps": total, "effective_batch_size": optimization["micro_batch_size"] * optimization["gradient_accumulation_steps"]}


def write_adapter_provenance(
    adapter_path: Path,
    *,
    adapter_id: str,
    adapter_version: str,
    training_run_id: str,
    model_config: dict[str, Any],
    data_evidence: dict[str, Any],
) -> dict[str, Any]:
    unprovenanced = adapter_identity(adapter_path, allow_unprovenanced_diagnostic_adapter=True)
    provenance = {
        "schema_version": 1,
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
        "adapter_digest": unprovenanced["adapter_digest"],
        "base_model_id": model_config["base_model"]["id"],
        "base_model_revision": model_config["base_model"]["revision"],
        "base_weights_sha256": model_config["base_model"]["weights_sha256"],
        "training_run_id": training_run_id,
        "training_dataset_id": data_evidence["dataset_id"] + ":" + data_evidence["training_role"],
        "training_dataset_sha256": data_evidence["training"]["sha256"],
        "peft_version": peft.__version__,
    }
    (adapter_path / "adapter-provenance.json").write_bytes(canonical_bytes(provenance))
    return adapter_identity(adapter_path)


def execute(args: argparse.Namespace, config_path: Path, run_kind: str) -> None:
    config_path = config_path.resolve()
    try:
        config_path.relative_to(ROOT / "config")
    except ValueError as exc:
        raise ValueError("training configuration must be contained in config/") from exc
    config = load_toml(config_path)
    shape = validate_config(config)
    model_config, tokenizer, training, validation, data_evidence = prepare_inputs(config)
    config_evidence = file_record(config_path)
    input_report = {"result": "inputs_ready", "config": config_evidence, "shape": shape, "data": data_evidence}
    if args.check_inputs:
        print(json.dumps(input_report, indent=2))
        return

    if not args.run_id or not re_fullmatch_run_id(args.run_id):
        raise ValueError("--run-id is required and must contain only lowercase letters, digits, and hyphens")
    if not torch.cuda.is_available():
        raise RuntimeError(f"CUDA is required for the {run_kind} run")
    if config["acceptance"]["require_bfloat16"] and not torch.cuda.is_bf16_supported():
        raise RuntimeError("GPU does not support bfloat16")
    repository = git_record()
    if config["run"]["require_clean_git"] and repository["dirty"]:
        raise RuntimeError(f"formal {run_kind} requires a clean Git checkout")

    run_dir = ROOT / config["output"]["runs_root"] / args.run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    started_at = datetime.now(UTC)
    wall_started = time.perf_counter()

    seed = config["run"]["seed"]
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False

    device = torch.device("cuda:0")
    device_properties = torch.cuda.get_device_properties(device)
    optimization = config["optimization"]
    adapter = config["adapter"]
    snapshot = model_path(model_config["base_model"]["id"], model_config["base_model"]["revision"])
    base_model = load_base(snapshot, device, optimization["gradient_checkpointing"])
    baseline_validation = evaluate(
        base_model, validation, optimization["micro_batch_size"], tokenizer.pad_token_id, device
    )

    probe_messages = [{"role": "system", "content": ""}, {"role": "user", "content": PROBE_PROMPT}]
    probe_ids = tokenizer.apply_chat_template(probe_messages, tokenize=True, add_generation_prompt=True, return_tensors="pt").input_ids.to(device)
    base_logits = last_token_logits(base_model, probe_ids)

    lora = LoraConfig(
        r=adapter["rank"], lora_alpha=adapter["alpha"], lora_dropout=adapter["dropout"],
        bias=adapter["bias"], target_modules=adapter["target_modules"],
        task_type=task_type(adapter["task_type"]), init_lora_weights=True,
    )
    model = get_peft_model(base_model, lora)
    named_parameters = list(model.named_parameters())
    trainable = [(name, parameter) for name, parameter in named_parameters if parameter.requires_grad]
    frozen = [(name, parameter) for name, parameter in named_parameters if not parameter.requires_grad]
    if not trainable or any("lora_" not in name for name, _ in trainable):
        raise RuntimeError("only LoRA parameters may be trainable")
    trainable_parameter_count = sum(parameter.numel() for _, parameter in trainable)
    expected_trainable = config["acceptance"].get("expected_trainable_parameter_count")
    if expected_trainable is not None and trainable_parameter_count != expected_trainable:
        raise RuntimeError(
            f"trainable parameter count {trainable_parameter_count} does not match expected {expected_trainable}"
        )
    neutral_logits = last_token_logits(model, probe_ids)
    torch.testing.assert_close(neutral_logits, base_logits, rtol=0.0, atol=0.0)
    frozen_versions = {name: parameter._version for name, parameter in frozen}

    optimizer = torch.optim.AdamW(
        [parameter for _, parameter in trainable],
        lr=optimization["learning_rate"], weight_decay=optimization["weight_decay"],
    )
    if {id(item) for group in optimizer.param_groups for item in group["params"]} != {id(item) for _, item in trainable}:
        raise RuntimeError("optimizer contains parameters outside the LoRA adapter")

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    epochs: list[dict[str, Any]] = []
    optimizer_step = 0
    all_step_seconds: list[float] = []
    model.train()
    for epoch in range(1, optimization["epochs"] + 1):
        epoch_started = time.perf_counter()
        batches = epoch_batches(training, optimization["micro_batch_size"], seed, epoch)
        schedule = [[item["example_id"] for item in batch] for batch in batches]
        micro_losses: list[float] = []
        step_records: list[dict[str, Any]] = []
        accumulation_started = 0.0
        optimizer.zero_grad(set_to_none=True)
        for micro_index, items in enumerate(batches, 1):
            if (micro_index - 1) % optimization["gradient_accumulation_steps"] == 0:
                torch.cuda.synchronize(device)
                accumulation_started = time.perf_counter()
            batch = {key: value.to(device) for key, value in collate(items, tokenizer.pad_token_id).items()}
            loss_weights = batch.pop("loss_weights", None)
            if loss_weights is None:
                output = model(**batch)
                loss = output.loss
            else:
                output = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
                loss = weighted_causal_loss(output.logits, batch["labels"], loss_weights)
            if not math.isfinite(float(loss.item())):
                raise RuntimeError("training produced a non-finite loss")
            micro_losses.append(float(loss.item()))
            (loss / optimization["gradient_accumulation_steps"]).backward()
            if micro_index % optimization["gradient_accumulation_steps"] == 0:
                gradient_norm = torch.nn.utils.clip_grad_norm_([parameter for _, parameter in trainable], optimization["max_gradient_norm"])
                if not math.isfinite(float(gradient_norm.item())):
                    raise RuntimeError("training produced a non-finite gradient norm")
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                torch.cuda.synchronize(device)
                optimizer_step += 1
                step_seconds = time.perf_counter() - accumulation_started
                all_step_seconds.append(step_seconds)
                step_records.append({
                    "optimizer_step": optimizer_step,
                    "loss_mean_for_accumulated_micro_batches": sum(micro_losses[-optimization["gradient_accumulation_steps"] :]) / optimization["gradient_accumulation_steps"],
                    "gradient_norm_before_clipping": float(gradient_norm.item()),
                    "seconds": step_seconds,
                })
        torch.cuda.synchronize(device)
        validation_started = time.perf_counter()
        validation_result = evaluate(model, validation, optimization["micro_batch_size"], tokenizer.pad_token_id, device)
        torch.cuda.synchronize(device)
        validation_seconds = time.perf_counter() - validation_started
        checkpoint = run_dir / "checkpoints" / f"epoch-{epoch:02d}"
        model.save_pretrained(checkpoint, safe_serialization=True)
        checkpoint_identity = write_adapter_provenance(
            checkpoint,
            adapter_id=config["run"].get("adapter_id", "chatgnt-pilot-v1"),
            adapter_version=f"{args.run_id}-epoch-{epoch:02d}",
            training_run_id=args.run_id,
            model_config=model_config,
            data_evidence=data_evidence,
        )
        epochs.append({
            "epoch": epoch,
            "optimizer_step_end": optimizer_step,
            "training_micro_batch_loss_mean": sum(micro_losses) / len(micro_losses),
            "training_micro_batch_losses": micro_losses,
            "optimizer_steps": step_records,
            "validation": validation_result,
            "validation_seconds": validation_seconds,
            "epoch_seconds_including_validation_and_checkpoint": time.perf_counter() - epoch_started,
            "micro_batch_schedule": schedule,
            "checkpoint_adapter": {
                key: checkpoint_identity[key]
                for key in ("adapter_id", "adapter_version", "adapter_digest", "provenance_sha256")
            },
            "checkpoint_files": [file_record(path, run_dir) for path in sorted(checkpoint.iterdir()) if path.is_file()],
        })
        model.train()

    if optimizer_step != config["acceptance"]["expected_optimizer_steps"]:
        raise RuntimeError("training completed an unexpected number of optimizer steps")
    if any(parameter.grad is not None for _, parameter in frozen):
        raise RuntimeError("frozen base parameters received gradients")
    if any(parameter._version != frozen_versions[name] for name, parameter in frozen):
        raise RuntimeError("frozen base parameters changed")

    trained_logits = last_token_logits(model, probe_ids)
    logit_change = float((trained_logits - base_logits).abs().max().item())
    if config["acceptance"]["require_adapter_logit_change"] and logit_change == 0.0:
        raise RuntimeError("trained adapter did not change probe logits")

    final_adapter = run_dir / "adapter"
    model.save_pretrained(final_adapter, safe_serialization=True)
    formal_adapter_identity = write_adapter_provenance(
        final_adapter,
        adapter_id=config["run"].get("adapter_id", "chatgnt-pilot-v1"),
        adapter_version=args.run_id,
        training_run_id=args.run_id,
        model_config=model_config,
        data_evidence=data_evidence,
    )

    peak_allocated = torch.cuda.max_memory_allocated(device)
    peak_reserved = torch.cuda.max_memory_reserved(device)
    total_memory = device_properties.total_memory
    reserved_fraction = peak_reserved / total_memory

    del output, loss, optimizer, model, base_model, named_parameters, trainable, frozen
    gc.collect()
    torch.cuda.empty_cache()

    clean_base = load_base(snapshot, device, False)
    reloaded = PeftModel.from_pretrained(clean_base, final_adapter, adapter_name="chatgnt", is_trainable=False)
    reloaded_logits = last_token_logits(reloaded, probe_ids)
    reload_difference = float((trained_logits - reloaded_logits).abs().max().item())
    if config["acceptance"]["require_exact_reload"]:
        torch.testing.assert_close(reloaded_logits, trained_logits, rtol=0.0, atol=0.0)

    wall_seconds = time.perf_counter() - wall_started
    hourly_price = args.hourly_price_usd
    total_training_tokens = sum(item["total_tokens"] for item in training) * optimization["epochs"]
    measured_training_seconds = sum(all_step_seconds)
    report = {
        "schema_version": 1,
        "run_id": args.run_id,
        "result": "pass" if reserved_fraction <= config["acceptance"]["maximum_reserved_vram_fraction"] else "fail_memory_headroom",
        "started_at_utc": started_at.isoformat().replace("+00:00", "Z"),
        "completed_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "wall_seconds": wall_seconds,
        "estimated_compute_cost_usd": None if hourly_price is None else wall_seconds * hourly_price / 3600,
        "displayed_hourly_price_usd": hourly_price,
        "repository": repository,
        "configuration": {"identity": config_evidence, "values": config},
        "model": model_config["base_model"],
        "data": data_evidence,
        "training_shape": shape,
        "training_performance": {
            "input_tokens_processed": total_training_tokens,
            "measured_optimizer_step_seconds": all_step_seconds,
            "measured_training_seconds": measured_training_seconds,
            "input_tokens_per_second": total_training_tokens / measured_training_seconds,
        },
        "baseline_validation": baseline_validation,
        "epochs": epochs,
        "adapter": {**formal_adapter_identity, "trainable_parameter_count": trainable_parameter_count},
        "checks": {"initial_adapter_exactly_neutral": True, "maximum_logit_change_from_base": logit_change, "reload_maximum_logit_difference": reload_difference, "frozen_base_unchanged": True},
        "environment": {"hostname": platform.node(), "python": platform.python_version(), "torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__, "cuda_build": torch.version.cuda, "runpod_pod_id": os.environ.get("RUNPOD_POD_ID")},
        "gpu": {**nvidia_record(), "torch_name": device_properties.name, "total_memory_bytes": total_memory, "peak_allocated_bytes": peak_allocated, "peak_reserved_bytes": peak_reserved, "peak_reserved_fraction": reserved_fraction},
        "probe": {"source": "spent development prompt", "prompt_sha256": sha256_text(PROBE_PROMPT)},
    }
    report_path = run_dir / "report.json"
    report_path.write_bytes(canonical_bytes(report))
    print(json.dumps({"result": report["result"], "run_dir": run_dir.relative_to(ROOT).as_posix(), "report_sha256": sha256_file(report_path)}, indent=2))
    if report["result"] != "pass":
        raise SystemExit(1)


def main() -> None:
    execute(parse_args(), CONFIG_PATH, "pilot")


def re_fullmatch_run_id(value: str) -> bool:
    import re

    return re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is not None


if __name__ == "__main__":
    main()
