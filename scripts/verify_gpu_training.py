"""Measure a representative LoRA training step on a rented NVIDIA GPU."""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import platform
import random
import subprocess
import sys
import time
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import accelerate
import peft
import torch
import transformers
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
MODEL_CONFIG_PATH = ROOT / "config" / "model.toml"
LORA_CONFIG_PATH = ROOT / "config" / "lora-lifecycle.toml"
GPU_CONFIG_PATH = ROOT / "config" / "gpu-feasibility.toml"
MODEL_ARTIFACTS_ROOT = ROOT / "artifacts" / "models"


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check-inputs",
        action="store_true",
        help="Validate the synthetic batch and configuration without requiring a GPU.",
    )
    return parser.parse_args()


def load_toml(path: Path) -> dict:
    """Load a TOML configuration file."""
    with path.open("rb") as config_file:
        return tomllib.load(config_file)


def model_path(model_id: str, revision: str) -> Path:
    """Return the local path for the immutable model snapshot."""
    repository_directory = model_id.replace("/", "--")
    return MODEL_ARTIFACTS_ROOT / repository_directory / revision


def task_type(value: str) -> TaskType:
    """Resolve the explicitly recorded PEFT task type."""
    try:
        return TaskType[value]
    except KeyError as error:
        raise ValueError(f"Unsupported PEFT task type: {value}") from error


def gibibytes(byte_count: int) -> float:
    """Convert bytes to GiB."""
    return round(byte_count / (1024**3), 4)


def nvidia_smi_record() -> dict:
    """Capture selected driver and device fields without invoking a shell."""
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total",
        "--format=csv,noheader,nounits",
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    fields = [field.strip() for field in completed.stdout.strip().split(",")]
    if len(fields) != 3:
        raise RuntimeError(f"Unexpected nvidia-smi output: {completed.stdout!r}")
    return {
        "name": fields[0],
        "driver_version": fields[1],
        "reported_memory_mib": int(fields[2]),
    }


def build_synthetic_batch(
    tokenizer: transformers.PreTrainedTokenizerBase,
    minimal_system_message: str,
    sequence_length: int,
    micro_batch_size: int,
) -> dict[str, torch.Tensor | int]:
    """Build a fixed-length ChatG&T-shaped capacity batch."""
    prompt_messages = [
        {"role": "system", "content": minimal_system_message},
        {
            "role": "user",
            "content": "How should I prepare for a job interview?",
        },
    ]
    long_method = (
        "Research the role and organisation, select concrete examples, rehearse "
        "clear explanations, prepare thoughtful questions, and leave enough time "
        "to arrive calmly. "
    )
    target_content = json.dumps(
        {
            "title": "The Confident Candidate",
            "ingredients": [
                {"amount": 50, "unit": "ml", "name": "role-specific preparation"},
                {"amount": 25, "unit": "ml", "name": "concrete examples"},
                {"amount": 15, "unit": "ml", "name": "calm confidence"},
                {"amount": 2, "unit": "dashes", "name": "curiosity"},
            ],
            "method": [long_method * 5 for _ in range(5)],
            "garnish": "One thoughtful question about the team and its priorities.",
        },
        separators=(",", ":"),
    )
    complete_messages = [
        *prompt_messages,
        {"role": "assistant", "content": target_content},
    ]

    prompt_encoding = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    )
    complete_encoding = tokenizer.apply_chat_template(
        complete_messages,
        tokenize=True,
        add_generation_prompt=False,
        return_tensors="pt",
    )
    prompt_ids = prompt_encoding.input_ids
    complete_ids = complete_encoding.input_ids
    prompt_token_count = prompt_ids.shape[-1]
    untruncated_token_count = complete_ids.shape[-1]

    if not torch.equal(complete_ids[:, :prompt_token_count], prompt_ids):
        raise AssertionError("The synthetic prompt is not a prefix of its target")
    if untruncated_token_count < sequence_length:
        raise AssertionError(
            "The synthetic target is too short for the configured capacity check"
        )

    input_ids = complete_ids[:, :sequence_length].repeat(micro_batch_size, 1)
    attention_mask = torch.ones_like(input_ids)
    labels = input_ids.clone()
    labels[:, :prompt_token_count] = -100
    supervised_token_count = int((labels[0] != -100).sum().item())
    if supervised_token_count == 0:
        raise AssertionError("The synthetic capacity batch has no supervised tokens")

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
        "prompt_token_count": prompt_token_count,
        "supervised_tokens_per_example": supervised_token_count,
        "untruncated_token_count": untruncated_token_count,
    }


def inference_ids(
    tokenizer: transformers.PreTrainedTokenizerBase,
    minimal_system_message: str,
) -> torch.Tensor:
    """Build the deterministic prompt used for adapter comparisons."""
    messages = [
        {"role": "system", "content": minimal_system_message},
        {
            "role": "user",
            "content": "Respond with exactly the word READY and nothing else.",
        },
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).input_ids


def last_token_logits(
    model: torch.nn.Module,
    input_ids: torch.Tensor,
) -> torch.Tensor:
    """Return a CPU FP32 copy of the complete next-token logit vector."""
    model.eval()
    with torch.inference_mode():
        return model(input_ids=input_ids).logits[:, -1, :].float().cpu().clone()


def load_base_model(snapshot_path: Path) -> torch.nn.Module:
    """Load the pinned BF16 model directly onto the first CUDA device."""
    return AutoModelForCausalLM.from_pretrained(
        snapshot_path,
        local_files_only=True,
        dtype=torch.bfloat16,
        device_map={"": 0},
        low_cpu_mem_usage=True,
    )


def main() -> None:
    """Run the local input check or the complete rented-GPU diagnostic."""
    args = parse_args()
    model_config = load_toml(MODEL_CONFIG_PATH)
    lora_project_config = load_toml(LORA_CONFIG_PATH)
    gpu_project_config = load_toml(GPU_CONFIG_PATH)
    selected_model = model_config["base_model"]
    selected_chat = model_config["canonical_chat"]
    adapter_config = lora_project_config["adapter"]
    optimizer_config = lora_project_config["diagnostic"]
    workload_config = gpu_project_config["workload"]
    acceptance_config = gpu_project_config["acceptance"]
    output_config = gpu_project_config["output"]
    rental_config = gpu_project_config["rental"]

    snapshot_path = model_path(selected_model["id"], selected_model["revision"])
    if not snapshot_path.is_dir():
        raise FileNotFoundError(f"Pinned snapshot not found: {snapshot_path}")

    tokenizer = AutoTokenizer.from_pretrained(snapshot_path, local_files_only=True)
    batch = build_synthetic_batch(
        tokenizer,
        selected_chat["minimal_system_message"],
        workload_config["sequence_length"],
        workload_config["micro_batch_size"],
    )
    input_report = {
        "sequence_length": int(batch["input_ids"].shape[-1]),
        "micro_batch_size": int(batch["input_ids"].shape[0]),
        "prompt_token_count": batch["prompt_token_count"],
        "supervised_tokens_per_example": batch["supervised_tokens_per_example"],
        "untruncated_token_count": batch["untruncated_token_count"],
        "optimization_steps": workload_config["optimization_steps"],
        "tokens_per_step": int(batch["input_ids"].numel()),
    }
    if args.check_inputs:
        print(json.dumps({"result": "inputs_ready", "workload": input_report}, indent=2))
        return

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available. Run --check-inputs locally; run the full check "
            "only inside the rented NVIDIA environment."
        )
    if acceptance_config["require_bfloat16"] and not torch.cuda.is_bf16_supported():
        raise RuntimeError("The selected CUDA device does not report BF16 support")
    if workload_config["gradient_accumulation_steps"] != 1:
        raise ValueError("The diagnostic currently expects one optimizer step per batch")

    adapter_output_path = ROOT / output_config["adapter_path"]
    report_output_path = ROOT / output_config["report_path"]
    if adapter_output_path.exists() or report_output_path.exists():
        raise FileExistsError(
            "GPU diagnostic output already exists. Preserve it, then use a clean "
            "workspace for a deliberate rerun."
        )

    started_at = datetime.now(UTC)
    wall_started = time.perf_counter()
    seed = optimizer_config["seed"]
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cuda.matmul.allow_tf32 = False

    device = torch.device("cuda:0")
    device_properties = torch.cuda.get_device_properties(device)
    smi = nvidia_smi_record()
    if gibibytes(device_properties.total_memory) < rental_config["minimum_vram_gib"] - 1:
        raise RuntimeError("The CUDA device does not meet the recorded 24 GB class")

    base_model = load_base_model(snapshot_path)
    if workload_config["gradient_checkpointing"]:
        base_model.gradient_checkpointing_enable()
    base_model.config.use_cache = False

    comparison_ids = inference_ids(
        tokenizer,
        selected_chat["minimal_system_message"],
    ).to(device)
    base_logits = last_token_logits(base_model, comparison_ids)

    lora_config = LoraConfig(
        r=adapter_config["rank"],
        lora_alpha=adapter_config["alpha"],
        lora_dropout=adapter_config["dropout"],
        bias=adapter_config["bias"],
        target_modules=adapter_config["target_modules"],
        task_type=task_type(adapter_config["task_type"]),
        init_lora_weights=adapter_config["init_lora_weights"],
    )
    adapted_model = get_peft_model(base_model, lora_config)
    named_parameters = list(adapted_model.named_parameters())
    trainable_parameters = [
        (name, parameter)
        for name, parameter in named_parameters
        if parameter.requires_grad
    ]
    frozen_parameters = [
        (name, parameter)
        for name, parameter in named_parameters
        if not parameter.requires_grad
    ]
    if not trainable_parameters:
        raise AssertionError("No trainable LoRA parameters were attached")
    if any("lora_" not in name for name, _ in trainable_parameters):
        raise AssertionError("A non-LoRA parameter was unexpectedly trainable")

    neutral_logits = last_token_logits(adapted_model, comparison_ids)
    initial_maximum_difference = float((base_logits - neutral_logits).abs().max().item())
    torch.testing.assert_close(neutral_logits, base_logits, rtol=0.0, atol=0.0)

    trainable_parameter_count = sum(
        parameter.numel() for _, parameter in trainable_parameters
    )
    total_parameter_count = sum(parameter.numel() for _, parameter in named_parameters)
    frozen_versions_before = {
        name: parameter._version for name, parameter in frozen_parameters
    }
    optimizer = torch.optim.AdamW(
        [parameter for _, parameter in trainable_parameters],
        lr=optimizer_config["learning_rate"],
        weight_decay=optimizer_config["weight_decay"],
    )
    optimizer_parameter_ids = {
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
    }
    if optimizer_parameter_ids != {id(parameter) for _, parameter in trainable_parameters}:
        raise AssertionError("The optimizer contains parameters outside the LoRA adapter")

    device_batch = {
        key: value.to(device)
        for key, value in batch.items()
        if isinstance(value, torch.Tensor)
    }
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    memory_before_training = torch.cuda.memory_allocated(device)
    reserved_before_training = torch.cuda.memory_reserved(device)

    losses: list[float] = []
    step_seconds: list[float] = []
    adapted_model.train()
    for _ in range(workload_config["optimization_steps"]):
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.synchronize(device)
        step_started = time.perf_counter()
        outputs = adapted_model(**device_batch)
        loss = outputs.loss
        if not math.isfinite(loss.item()):
            raise AssertionError(f"Training produced a non-finite loss: {loss.item()}")
        loss.backward()
        optimizer.step()
        torch.cuda.synchronize(device)
        step_seconds.append(time.perf_counter() - step_started)
        losses.append(float(loss.item()))

    peak_allocated = torch.cuda.max_memory_allocated(device)
    peak_reserved = torch.cuda.max_memory_reserved(device)
    total_device_memory = device_properties.total_memory
    peak_reserved_fraction = peak_reserved / total_device_memory
    memory_gate_passed = (
        peak_reserved_fraction
        <= acceptance_config["maximum_reserved_vram_fraction"]
    )

    frozen_with_gradients = [
        name for name, parameter in frozen_parameters if parameter.grad is not None
    ]
    changed_frozen_versions = [
        name
        for name, parameter in frozen_parameters
        if parameter._version != frozen_versions_before[name]
    ]
    if frozen_with_gradients:
        raise AssertionError("Frozen base-model parameters received gradients")
    if changed_frozen_versions:
        raise AssertionError("Frozen base-model parameters changed during optimization")

    post_update_logits = last_token_logits(adapted_model, comparison_ids)
    post_update_difference = float(
        (base_logits - post_update_logits).abs().max().item()
    )
    if post_update_difference == 0.0:
        raise AssertionError("The optimizer steps did not affect model logits")

    adapter_output_path.parent.mkdir(parents=True, exist_ok=True)
    adapted_model.save_pretrained(adapter_output_path, safe_serialization=True)
    adapter_files = sorted(path for path in adapter_output_path.iterdir() if path.is_file())
    adapter_size_bytes = sum(path.stat().st_size for path in adapter_files)

    del outputs
    del loss
    del optimizer
    del adapted_model
    del base_model
    del named_parameters
    del trainable_parameters
    del frozen_parameters
    del device_batch
    gc.collect()
    torch.cuda.empty_cache()

    clean_base_model = load_base_model(snapshot_path)
    clean_base_model.config.use_cache = False
    reloaded_model = PeftModel.from_pretrained(
        clean_base_model,
        adapter_output_path,
        is_trainable=False,
    )
    reloaded_logits = last_token_logits(reloaded_model, comparison_ids)
    reload_maximum_difference = float(
        (post_update_logits - reloaded_logits).abs().max().item()
    )
    torch.testing.assert_close(
        reloaded_logits,
        post_update_logits,
        rtol=0.0,
        atol=0.0,
    )

    total_training_tokens = (
        input_report["tokens_per_step"] * workload_config["optimization_steps"]
    )
    measured_training_seconds = sum(step_seconds)
    wall_seconds = time.perf_counter() - wall_started
    recorded_hourly_price = rental_config["recorded_hourly_gpu_price_usd"]
    report = {
        "result": "pass" if memory_gate_passed else "fail_memory_headroom",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "selection": {
            "model_id": selected_model["id"],
            "revision": selected_model["revision"],
            "weight_dtype": selected_model["weight_dtype"],
        },
        "rental": {
            **rental_config,
            "runpod_pod_id": os.environ.get("RUNPOD_POD_ID"),
            "diagnostic_wall_time_cost_usd_at_recorded_rate": round(
                wall_seconds * recorded_hourly_price / 3600,
                6,
            ),
            "actual_session_cost_usd": None,
        },
        "environment": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "peft": peft.__version__,
            "accelerate": accelerate.__version__,
            "torch_cuda_build": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
            "bfloat16_supported": torch.cuda.is_bf16_supported(),
        },
        "gpu": {
            **smi,
            "torch_name": device_properties.name,
            "compute_capability": (
                f"{device_properties.major}.{device_properties.minor}"
            ),
            "total_memory_bytes": total_device_memory,
            "total_memory_gib": gibibytes(total_device_memory),
        },
        "workload": input_report,
        "adapter": {
            "target_modules": adapter_config["target_modules"],
            "rank": adapter_config["rank"],
            "alpha": adapter_config["alpha"],
            "trainable_parameter_count": trainable_parameter_count,
            "total_parameter_count_with_adapter": total_parameter_count,
            "saved_files": [path.name for path in adapter_files],
            "saved_size_bytes": adapter_size_bytes,
        },
        "training": {
            "seed": seed,
            "optimizer": "AdamW",
            "learning_rate": optimizer_config["learning_rate"],
            "weight_decay": optimizer_config["weight_decay"],
            "gradient_checkpointing": workload_config["gradient_checkpointing"],
            "losses": losses,
            "step_seconds": [round(value, 6) for value in step_seconds],
            "mean_step_seconds": round(
                measured_training_seconds / len(step_seconds),
                6,
            ),
            "measured_tokens_per_second": round(
                total_training_tokens / measured_training_seconds,
                3,
            ),
        },
        "memory": {
            "allocated_before_training_bytes": memory_before_training,
            "reserved_before_training_bytes": reserved_before_training,
            "peak_allocated_bytes": peak_allocated,
            "peak_allocated_gib": gibibytes(peak_allocated),
            "peak_reserved_bytes": peak_reserved,
            "peak_reserved_gib": gibibytes(peak_reserved),
            "peak_reserved_fraction": round(peak_reserved_fraction, 6),
            "maximum_accepted_reserved_fraction": acceptance_config[
                "maximum_reserved_vram_fraction"
            ],
            "headroom_gate_passed": memory_gate_passed,
        },
        "checks": {
            "initial_adapter_maximum_logit_difference": initial_maximum_difference,
            "initial_adapter_exactly_neutral": True,
            "frozen_base_tensors_with_gradients": len(frozen_with_gradients),
            "changed_frozen_base_version_counters": len(changed_frozen_versions),
            "post_update_maximum_logit_difference_from_base": post_update_difference,
            "reload_maximum_logit_difference": reload_maximum_difference,
            "reload_exact_match": True,
        },
        "timing": {
            "started_at_utc": started_at.isoformat(),
            "diagnostic_wall_seconds": round(wall_seconds, 4),
        },
    }
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not memory_gate_passed:
        raise SystemExit("GPU diagnostic exceeded the accepted VRAM fraction")


if __name__ == "__main__":
    main()
