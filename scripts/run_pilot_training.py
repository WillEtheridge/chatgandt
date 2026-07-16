"""Run the frozen 40-example Stage 6 LoRA pipeline rehearsal."""

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


def tokenize_record(
    record: dict[str, Any],
    events: list[dict[str, Any]],
    contract: dict[str, Any],
    tokenizer: Any,
    maximum_length: int,
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
    return {
        "example_id": record["example_id"],
        "input_ids": complete_ids,
        "labels": labels,
        "prompt_tokens": int(prompt_ids.shape[0]),
        "total_tokens": int(complete_ids.shape[0]),
        "supervised_tokens": supervised,
    }


def collate(items: list[dict[str, Any]], pad_token_id: int) -> dict[str, torch.Tensor]:
    width = max(item["input_ids"].shape[0] for item in items)
    input_ids = torch.full((len(items), width), pad_token_id, dtype=torch.long)
    attention_mask = torch.zeros((len(items), width), dtype=torch.long)
    labels = torch.full((len(items), width), -100, dtype=torch.long)
    for row, item in enumerate(items):
        length = item["input_ids"].shape[0]
        input_ids[row, :length] = item["input_ids"]
        attention_mask[row, :length] = 1
        labels[row, :length] = item["labels"]
    return {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}


def epoch_batches(items: list[dict[str, Any]], batch_size: int, seed: int, epoch: int) -> list[list[dict[str, Any]]]:
    indices = list(range(len(items)))
    random.Random(seed + epoch).shuffle(indices)
    if len(indices) % batch_size:
        raise ValueError("pilot size must divide exactly by micro-batch size")
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
    paths = {key: ROOT / data[key] for key in ("pilot_path", "validation_path", "workflow_events_path", "dataset_manifest_path")}
    manifest, _ = read_strict_json(paths["dataset_manifest_path"])
    if manifest["dataset_id"] != data["expected_dataset_id"] or manifest["status"] != "frozen":
        raise ValueError("unexpected or unfrozen dataset manifest")
    expected_files = {item["path"]: item["sha256"] for item in manifest["files"]}
    for name in ("pilot", "validation"):
        path = paths[f"{name}_path"]
        if sha256_file(path) != expected_files[path.name]:
            raise ValueError(f"{name} file identity does not match the frozen manifest")

    pilot_records = load_canonical_jsonl(paths["pilot_path"])
    validation_records = load_canonical_jsonl(paths["validation_path"])
    events = group_events(load_canonical_jsonl(paths["workflow_events_path"]))
    if len(pilot_records) != data["expected_pilot_count"] or any(item["split"] != "train" or not item["pilot_member"] for item in pilot_records):
        raise ValueError("pilot collection does not match its frozen role")
    if len(validation_records) != data["expected_validation_count"] or any(item["split"] != "validation" or item["pilot_member"] for item in validation_records):
        raise ValueError("validation collection does not match its frozen role")
    if {item["scenario_id"] for item in pilot_records} & {item["scenario_id"] for item in validation_records}:
        raise ValueError("pilot and validation scenarios overlap")

    contract = load_dataset_contract()
    maximum = data["max_sequence_length"]
    pilot = [tokenize_record(item, events[item["example_id"]], contract, tokenizer, maximum) for item in pilot_records]
    validation = [tokenize_record(item, events[item["example_id"]], contract, tokenizer, maximum) for item in validation_records]
    evidence = {
        "dataset_id": manifest["dataset_id"],
        "manifest": file_record(paths["dataset_manifest_path"]),
        "pilot": file_record(paths["pilot_path"]),
        "validation": file_record(paths["validation_path"]),
        "workflow_events": file_record(paths["workflow_events_path"]),
        "pilot_count": len(pilot),
        "validation_count": len(validation),
        "pilot_token_range": [min(item["total_tokens"] for item in pilot), max(item["total_tokens"] for item in pilot)],
        "validation_token_range": [min(item["total_tokens"] for item in validation), max(item["total_tokens"] for item in validation)],
        "pilot_supervised_token_range": [min(item["supervised_tokens"] for item in pilot), max(item["supervised_tokens"] for item in pilot)],
        "validation_supervised_token_range": [min(item["supervised_tokens"] for item in validation), max(item["supervised_tokens"] for item in validation)],
        "truncated_examples": 0,
    }
    return project.model.values, tokenizer, pilot, validation, evidence


def validate_config(config: dict[str, Any]) -> dict[str, int]:
    optimization = config["optimization"]
    data = config["data"]
    micro_batches = data["expected_pilot_count"] // optimization["micro_batch_size"]
    if data["expected_pilot_count"] % optimization["micro_batch_size"]:
        raise ValueError("pilot count must divide by micro-batch size")
    if micro_batches % optimization["gradient_accumulation_steps"]:
        raise ValueError("micro-batches per epoch must divide by gradient accumulation")
    steps_per_epoch = micro_batches // optimization["gradient_accumulation_steps"]
    total = steps_per_epoch * optimization["epochs"]
    if total != config["acceptance"]["expected_optimizer_steps"]:
        raise ValueError("configured optimiser-step count is inconsistent")
    return {"micro_batches_per_epoch": micro_batches, "optimizer_steps_per_epoch": steps_per_epoch, "total_optimizer_steps": total, "effective_batch_size": optimization["micro_batch_size"] * optimization["gradient_accumulation_steps"]}


def main() -> None:
    args = parse_args()
    config = load_toml(CONFIG_PATH)
    shape = validate_config(config)
    model_config, tokenizer, pilot, validation, data_evidence = prepare_inputs(config)
    config_evidence = file_record(CONFIG_PATH)
    input_report = {"result": "inputs_ready", "config": config_evidence, "shape": shape, "data": data_evidence}
    if args.check_inputs:
        print(json.dumps(input_report, indent=2))
        return

    if not args.run_id or not re_fullmatch_run_id(args.run_id):
        raise ValueError("--run-id is required and must contain only lowercase letters, digits, and hyphens")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the pilot run")
    if config["acceptance"]["require_bfloat16"] and not torch.cuda.is_bf16_supported():
        raise RuntimeError("GPU does not support bfloat16")
    repository = git_record()
    if config["run"]["require_clean_git"] and repository["dirty"]:
        raise RuntimeError("formal pilot requires a clean Git checkout")

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
        batches = epoch_batches(pilot, optimization["micro_batch_size"], seed, epoch)
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
            output = model(**batch)
            if not math.isfinite(float(output.loss.item())):
                raise RuntimeError("training produced a non-finite loss")
            micro_losses.append(float(output.loss.item()))
            (output.loss / optimization["gradient_accumulation_steps"]).backward()
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
    unprovenanced = adapter_identity(final_adapter, allow_unprovenanced_diagnostic_adapter=True)
    provenance = {
        "schema_version": 1,
        "adapter_id": "chatgnt-pilot-v1",
        "adapter_version": args.run_id,
        "adapter_digest": unprovenanced["adapter_digest"],
        "base_model_id": model_config["base_model"]["id"],
        "base_model_revision": model_config["base_model"]["revision"],
        "base_weights_sha256": model_config["base_model"]["weights_sha256"],
        "training_run_id": args.run_id,
        "training_dataset_id": data_evidence["dataset_id"] + ":pilot",
        "training_dataset_sha256": data_evidence["pilot"]["sha256"],
        "peft_version": peft.__version__,
    }
    (final_adapter / "adapter-provenance.json").write_bytes(canonical_bytes(provenance))
    formal_adapter_identity = adapter_identity(final_adapter)

    peak_allocated = torch.cuda.max_memory_allocated(device)
    peak_reserved = torch.cuda.max_memory_reserved(device)
    total_memory = device_properties.total_memory
    reserved_fraction = peak_reserved / total_memory

    del output, optimizer, model, base_model, named_parameters, trainable, frozen
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
    total_training_tokens = sum(item["total_tokens"] for item in pilot) * optimization["epochs"]
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


def re_fullmatch_run_id(value: str) -> bool:
    import re

    return re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is not None


if __name__ == "__main__":
    main()
