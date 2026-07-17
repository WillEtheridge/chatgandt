"""Verify the frozen Stage 6 second-round contract outside the Stage 3 suite."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

import torch
import torch.nn.functional as F
from peft import LoraConfig, TaskType, get_peft_model
from transformers import AutoModelForCausalLM


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.configuration import load_project_configuration  # noqa: E402
from chatgnt.identity import sha256_file  # noqa: E402
from scripts.run_pilot_training import (  # noqa: E402
    collate,
    load_toml,
    model_path,
    prepare_inputs,
    validate_config,
    weighted_causal_loss,
)
from scripts.run_second_round_training import CANDIDATE_CONFIGS  # noqa: E402


REFERENCE_CONFIG = ROOT / "config" / "full-training-candidate-3-v1.toml"
EXPECTED_CONFIG_SHA256 = {
    "4": "17900f4797d68e3f53d8b3d2ba2fbc84eaba3e18b0179b8cfc0030ef5d61bf0b",
    "5": "3b16dbed50afc1b68373a00fe1f9046cc08bdb36a9818643e1f6b8c7fd866acb",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def normalise(config: dict[str, object], *, intervention: str) -> dict[str, object]:
    value = copy.deepcopy(config)
    run = value["run"]
    assert isinstance(run, dict)
    run.pop("config_id")
    run.pop("adapter_id")
    value.pop("output")
    if intervention == "targets":
        adapter = value["adapter"]
        acceptance = value["acceptance"]
        assert isinstance(adapter, dict) and isinstance(acceptance, dict)
        adapter.pop("target_modules")
        acceptance.pop("expected_trainable_parameter_count")
    elif intervention == "loss":
        value.pop("loss", None)
    else:
        raise ValueError("unknown intervention")
    return value


def verify_configs() -> dict[str, object]:
    reference = load_toml(REFERENCE_CONFIG)
    configs = {key: load_toml(path) for key, path in CANDIDATE_CONFIGS.items()}
    shapes = {key: validate_config(config) for key, config in configs.items()}
    require(all(shape["total_optimizer_steps"] == 60 for shape in shapes.values()),
            "second-round optimiser-step count drifted")

    reference_with_standard_loss = copy.deepcopy(reference)
    reference_with_standard_loss["loss"] = {"mode": "standard_assistant_only"}
    require(
        normalise(reference_with_standard_loss, intervention="targets")
        == normalise(configs["4"], intervention="targets"),
        "Candidate 4 changes more than target surface",
    )
    require(
        normalise(reference, intervention="loss")
        == normalise(configs["5"], intervention="loss"),
        "Candidate 5 changes more than training loss",
    )
    require(configs["4"]["adapter"]["target_modules"] == [
        "q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",
    ], "Candidate 4 target surface drifted")
    require(configs["5"]["loss"] == {
        "mode": "content_weighted_assistant_only",
        "base_weight": 1.0,
        "content_weight": 2.0,
        "content_fields": ["ingredients.name", "method"],
        "validation_mode": "standard_assistant_only",
    }, "Candidate 5 loss rule drifted")
    actual_sha = {key: sha256_file(path) for key, path in CANDIDATE_CONFIGS.items()}
    require(actual_sha == EXPECTED_CONFIG_SHA256, "second-round configuration bytes drifted")
    return {"config_sha256": actual_sha, "shapes": shapes}


def verify_weighted_inputs() -> dict[str, object]:
    config = load_toml(CANDIDATE_CONFIGS["5"])
    _, _, training, validation, evidence = prepare_inputs(config)
    require(len(training) == 160 and len(validation) == 40, "frozen split counts drifted")
    require(all("loss_weights" in item for item in training), "training weights missing")
    require(all("loss_weights" not in item for item in validation), "validation was weighted")
    for item in training:
        weights = item["loss_weights"]
        labels = item["labels"]
        require(set(weights.tolist()) <= {0.0, 1.0, 2.0}, "unexpected token weight")
        require(bool(torch.all(weights[labels == -100] == 0.0)), "masked tokens carry loss weight")
        require(int((weights == 2.0).sum().item()) == item["content_weighted_tokens"],
                "weighted-token evidence mismatch")
    require(evidence["training_content_weighted_token_count_per_epoch"] == 18600,
            "weighted-token population drifted")

    batch = collate(training[:2], pad_token_id=0)
    require("loss_weights" in batch and batch["loss_weights"].shape == batch["labels"].shape,
            "weighted collation drifted")
    return {
        "training_example_count": len(training),
        "validation_example_count": len(validation),
        "weighted_token_range": evidence["training_content_weighted_token_range"],
        "weighted_tokens_per_epoch": evidence["training_content_weighted_token_count_per_epoch"],
        "validation_loss_mode": evidence["validation_loss_mode"],
    }


def verify_weighted_loss_math() -> dict[str, object]:
    logits = torch.tensor([[[2.0, 0.0, -1.0], [0.0, 2.0, -1.0], [1.0, 0.0, 2.0]]],
                          requires_grad=True)
    labels = torch.tensor([[-100, 1, 2]])
    weights = torch.tensor([[0.0, 1.0, 2.0]])
    actual = weighted_causal_loss(logits, labels, weights)
    losses = F.cross_entropy(logits[:, :-1, :].reshape(-1, 3), labels[:, 1:].reshape(-1),
                             reduction="none").reshape(1, 2)
    expected = (losses * torch.tensor([[1.0, 2.0]])).sum() / 3.0
    torch.testing.assert_close(actual, expected, rtol=0.0, atol=0.0)
    actual.backward()
    require(bool(torch.isfinite(logits.grad).all()), "weighted loss produced non-finite gradients")
    return {"normalisation": "sum_weighted_token_losses_over_active_weight_mass",
            "finite_gradient": True}


def verify_model_capacity() -> dict[str, int]:
    project = load_project_configuration()
    base = project.model.values["base_model"]
    model = AutoModelForCausalLM.from_pretrained(
        model_path(base["id"], base["revision"]), local_files_only=True,
        dtype=torch.bfloat16, low_cpu_mem_usage=True, attn_implementation="sdpa",
    )
    adapted = get_peft_model(model, LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type=TaskType.CAUSAL_LM, init_lora_weights=True,
    ))
    count = sum(parameter.numel() for parameter in adapted.parameters() if parameter.requires_grad)
    require(count == 9232384, "Candidate 4 trainable parameter count drifted")
    return {"candidate_4_trainable_parameter_count": count}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-capacity", action="store_true",
                        help="Load the pinned model and verify Candidate 4's actual LoRA capacity.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = {
        "result": "pass",
        "configuration": verify_configs(),
        "weighted_inputs": verify_weighted_inputs(),
        "weighted_loss_math": verify_weighted_loss_math(),
        "model_capacity": verify_model_capacity() if args.model_capacity else {"executed": False},
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
