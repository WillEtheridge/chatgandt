"""Exercise the disposable PEFT LoRA lifecycle against the pinned base model."""

from __future__ import annotations

import gc
import json
import math
import random
import time
import tomllib
from pathlib import Path

import torch
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
MODEL_CONFIG_PATH = ROOT / "config" / "model.toml"
LORA_CONFIG_PATH = ROOT / "config" / "lora-lifecycle.toml"
MODEL_ARTIFACTS_ROOT = ROOT / "artifacts" / "models"


def load_toml(path: Path) -> dict:
    """Load a TOML file."""
    with path.open("rb") as config_file:
        return tomllib.load(config_file)


def model_path(model_id: str, revision: str) -> Path:
    """Return the expected local path for the immutable model snapshot."""
    repository_directory = model_id.replace("/", "--")
    return MODEL_ARTIFACTS_ROOT / repository_directory / revision


def load_base_model(snapshot_path: Path) -> torch.nn.Module:
    """Load the pinned base model without permitting network access."""
    return AutoModelForCausalLM.from_pretrained(
        snapshot_path,
        local_files_only=True,
        dtype="auto",
        device_map="cpu",
        low_cpu_mem_usage=True,
    )


def last_token_logits(model: torch.nn.Module, input_ids: torch.Tensor) -> torch.Tensor:
    """Return a stable CPU copy of the next-token logits."""
    model.eval()
    with torch.inference_mode():
        return model(input_ids=input_ids).logits[:, -1, :].float().cpu().clone()


def maximum_absolute_difference(left: torch.Tensor, right: torch.Tensor) -> float:
    """Calculate the largest element-wise absolute difference."""
    return float((left - right).abs().max().item())


def task_type(value: str) -> TaskType:
    """Resolve the recorded PEFT task type without relying on an implicit default."""
    try:
        return TaskType[value]
    except KeyError as error:
        raise ValueError(f"Unsupported PEFT task type: {value}") from error


def main() -> None:
    """Attach, update, save, reload, and reproduce a disposable adapter."""
    model_project_config = load_toml(MODEL_CONFIG_PATH)
    lifecycle_config = load_toml(LORA_CONFIG_PATH)
    selected_model = model_project_config["base_model"]
    selected_chat = model_project_config["canonical_chat"]
    adapter_config = lifecycle_config["adapter"]
    diagnostic_config = lifecycle_config["diagnostic"]

    snapshot_path = model_path(selected_model["id"], selected_model["revision"])
    output_path = ROOT / diagnostic_config["adapter_output"]
    if not snapshot_path.is_dir():
        raise FileNotFoundError(f"Pinned snapshot not found: {snapshot_path}")
    if output_path.exists():
        raise FileExistsError(
            f"Diagnostic output already exists: {output_path}. "
            "Move it aside before deliberately rerunning the lifecycle check."
        )

    seed = diagnostic_config["seed"]
    random.seed(seed)
    torch.manual_seed(seed)

    tokenizer = AutoTokenizer.from_pretrained(snapshot_path, local_files_only=True)
    inference_messages = [
        {"role": "system", "content": selected_chat["minimal_system_message"]},
        {"role": "user", "content": "Respond with exactly the word READY and nothing else."},
    ]
    inference_encoding = tokenizer.apply_chat_template(
        inference_messages,
        tokenize=True,
        add_generation_prompt=selected_chat["add_generation_prompt"],
        return_tensors="pt",
    )
    inference_ids = inference_encoding.input_ids

    training_messages = [
        {"role": "system", "content": selected_chat["minimal_system_message"]},
        {"role": "user", "content": "Name one primary colour."},
    ]
    target_messages = [
        *training_messages,
        {"role": "assistant", "content": "Red."},
    ]
    training_prompt_encoding = tokenizer.apply_chat_template(
        training_messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    )
    training_encoding = tokenizer.apply_chat_template(
        target_messages,
        tokenize=True,
        add_generation_prompt=False,
        return_tensors="pt",
    )
    training_prompt_ids = training_prompt_encoding.input_ids
    training_ids = training_encoding.input_ids
    prompt_token_count = training_prompt_ids.shape[-1]
    if not torch.equal(training_ids[:, :prompt_token_count], training_prompt_ids):
        raise AssertionError("Training prompt is not a prefix of the templated target")
    labels = training_ids.clone()
    labels[:, :prompt_token_count] = -100
    supervised_token_count = int((labels != -100).sum().item())
    if supervised_token_count == 0:
        raise AssertionError("The disposable training example has no supervised tokens")

    load_started = time.perf_counter()
    base_model = load_base_model(snapshot_path)
    base_load_seconds = time.perf_counter() - load_started
    base_logits = last_token_logits(base_model, inference_ids)

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
    if any("lora_" in name for name, _ in frozen_parameters):
        raise AssertionError("A LoRA parameter was unexpectedly frozen")

    zero_adapter_logits = last_token_logits(adapted_model, inference_ids)
    initial_maximum_logit_difference = maximum_absolute_difference(
        base_logits,
        zero_adapter_logits,
    )
    torch.testing.assert_close(
        zero_adapter_logits,
        base_logits,
        rtol=0.0,
        atol=0.0,
        msg="The newly attached adapter was not exactly behaviour-neutral",
    )

    trainable_before = {
        name: parameter.detach().cpu().clone()
        for name, parameter in trainable_parameters
    }
    frozen_versions_before = {
        name: parameter._version
        for name, parameter in frozen_parameters
    }
    optimizer = torch.optim.AdamW(
        [parameter for _, parameter in trainable_parameters],
        lr=diagnostic_config["learning_rate"],
        weight_decay=diagnostic_config["weight_decay"],
    )
    optimizer_parameter_ids = {
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
    }
    trainable_parameter_ids = {id(parameter) for _, parameter in trainable_parameters}
    if optimizer_parameter_ids != trainable_parameter_ids:
        raise AssertionError("The optimizer parameter set does not match the LoRA parameters")

    step_losses: list[float] = []
    adapted_model.train()
    training_started = time.perf_counter()
    for _ in range(diagnostic_config["training_steps"]):
        optimizer.zero_grad(set_to_none=True)
        outputs = adapted_model(input_ids=training_ids, labels=labels)
        loss = outputs.loss
        if not math.isfinite(loss.item()):
            raise AssertionError(f"Training produced a non-finite loss: {loss.item()}")
        loss.backward()
        step_losses.append(float(loss.item()))
        optimizer.step()
    training_seconds = time.perf_counter() - training_started

    trainable_gradient_tensors = sum(
        parameter.grad is not None for _, parameter in trainable_parameters
    )
    nonzero_gradient_tensors = sum(
        parameter.grad is not None and bool(torch.count_nonzero(parameter.grad).item())
        for _, parameter in trainable_parameters
    )
    changed_trainable_names = [
        name
        for name, parameter in trainable_parameters
        if not torch.equal(trainable_before[name], parameter.detach().cpu())
    ]
    if not changed_trainable_names:
        raise AssertionError("The optimization step did not change any LoRA parameters")

    frozen_with_gradients = [
        name for name, parameter in frozen_parameters if parameter.grad is not None
    ]
    changed_frozen_versions = [
        name
        for name, parameter in frozen_parameters
        if parameter._version != frozen_versions_before[name]
    ]
    if frozen_with_gradients:
        raise AssertionError("Frozen base-model parameters unexpectedly received gradients")
    if changed_frozen_versions:
        raise AssertionError("Frozen base-model parameters were mutated during optimization")

    post_update_logits = last_token_logits(adapted_model, inference_ids)
    post_update_maximum_logit_difference = maximum_absolute_difference(
        base_logits,
        post_update_logits,
    )
    if post_update_maximum_logit_difference == 0.0:
        raise AssertionError("The trained adapter did not affect the diagnostic logits")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    adapted_model.save_pretrained(output_path, safe_serialization=True)
    saved_files = sorted(path for path in output_path.iterdir() if path.is_file())
    saved_size_bytes = sum(path.stat().st_size for path in saved_files)

    total_parameter_count = sum(parameter.numel() for _, parameter in named_parameters)
    trainable_parameter_count = sum(
        parameter.numel() for _, parameter in trainable_parameters
    )
    trainable_parameter_tensor_count = len(trainable_parameters)
    changed_trainable_tensor_count = len(changed_trainable_names)

    del optimizer
    del adapted_model
    del base_model
    del named_parameters
    del trainable_parameters
    del frozen_parameters
    del trainable_before
    del outputs
    del loss
    gc.collect()

    reload_started = time.perf_counter()
    clean_base_model = load_base_model(snapshot_path)
    reloaded_model = PeftModel.from_pretrained(
        clean_base_model,
        output_path,
        is_trainable=False,
    )
    reload_seconds = time.perf_counter() - reload_started
    reloaded_logits = last_token_logits(reloaded_model, inference_ids)
    reload_maximum_logit_difference = maximum_absolute_difference(
        post_update_logits,
        reloaded_logits,
    )
    torch.testing.assert_close(
        reloaded_logits,
        post_update_logits,
        rtol=0.0,
        atol=0.0,
        msg="The reloaded adapter did not exactly reproduce its pre-save logits",
    )

    report = {
        "result": "pass",
        "selection": {
            "model_id": selected_model["id"],
            "revision": selected_model["revision"],
            "snapshot_path": str(snapshot_path.relative_to(ROOT)),
        },
        "adapter": {
            "target_modules": adapter_config["target_modules"],
            "rank": adapter_config["rank"],
            "alpha": adapter_config["alpha"],
            "dropout": adapter_config["dropout"],
            "bias": adapter_config["bias"],
            "trainable_parameter_tensors": trainable_parameter_tensor_count,
            "trainable_parameter_count": trainable_parameter_count,
            "total_parameter_count_with_adapter": total_parameter_count,
            "trainable_percentage": round(
                100 * trainable_parameter_count / total_parameter_count,
                6,
            ),
        },
        "initial_neutrality": {
            "comparison": "full next-token logit vector",
            "maximum_absolute_difference": initial_maximum_logit_difference,
            "exact_match": True,
        },
        "optimization": {
            "seed": seed,
            "steps": diagnostic_config["training_steps"],
            "learning_rate": diagnostic_config["learning_rate"],
            "weight_decay": diagnostic_config["weight_decay"],
            "losses": step_losses,
            "prompt_token_count": prompt_token_count,
            "supervised_token_count": supervised_token_count,
            "gradient_bearing_lora_tensors": trainable_gradient_tensors,
            "nonzero_gradient_lora_tensors": nonzero_gradient_tensors,
            "changed_lora_tensors": changed_trainable_tensor_count,
            "frozen_base_tensors_with_gradients": len(frozen_with_gradients),
            "changed_frozen_base_version_counters": len(changed_frozen_versions),
            "post_update_maximum_logit_difference_from_base": (
                post_update_maximum_logit_difference
            ),
        },
        "round_trip": {
            "output_path": str(output_path.relative_to(ROOT)),
            "files": [path.name for path in saved_files],
            "total_size_bytes": saved_size_bytes,
            "comparison": "full next-token logit vector",
            "maximum_absolute_difference": reload_maximum_logit_difference,
            "exact_match": True,
        },
        "timings_seconds": {
            "base_load": round(base_load_seconds, 4),
            "single_training_step": round(training_seconds, 4),
            "clean_base_and_adapter_reload": round(reload_seconds, 4),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
