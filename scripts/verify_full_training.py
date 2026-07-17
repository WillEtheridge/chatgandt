"""Verify the frozen Stage 6 candidate contract without changing Stage 3 tests."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import torch
from peft import LoraConfig, TaskType, get_peft_model
from transformers import AutoModelForCausalLM


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.configuration import adapter_identity, load_project_configuration  # noqa: E402
from chatgnt.identity import sha256_file  # noqa: E402
from chatgnt.records import ContractError  # noqa: E402
from scripts.run_full_training import CANDIDATE_CONFIGS  # noqa: E402
from scripts.run_pilot_training import (  # noqa: E402
    collate,
    load_toml,
    model_path,
    tokenize_record,
    training_collection,
    validate_config,
    write_adapter_provenance,
)


EXPECTED_DATA = {
    "data/dataset-v1/frozen-v1.2/train.jsonl": "1690561db24ba4d2ae3c56f0ba4e988643994cb2add51f01beef901ebf5095b2",
    "data/dataset-v1/frozen-v1.2/validation.jsonl": "b9e344f6582a9ebe4d9b83801cf71acc2abf2c4f95efd71bcd58eafbfb36bdc5",
    "data/dataset-v1/frozen-v1.2/workflow-events.jsonl": "9fb18167271982dd808a0b3d5892050952e97366188dd77cdb8f140cca4c86f9",
    "data/dataset-v1/frozen-v1.2/dataset-manifest.json": "bbc749a1a840213fa9b09680df9da7b06e35cb0c7deceab60ecd2744e354aca5",
}


class FakeTokenizer:
    def apply_chat_template(self, messages: list[dict[str, str]], **kwargs: object) -> SimpleNamespace:
        values = [11, 12, 13] if kwargs["add_generation_prompt"] else [11, 12, 13, 21, 22]
        return SimpleNamespace(input_ids=torch.tensor([values]))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def normalized_pair(
    left: dict[str, object], right: dict[str, object], *, duration: bool, targets: bool
) -> tuple[dict[str, object], dict[str, object]]:
    left = copy.deepcopy(left)
    right = copy.deepcopy(right)
    for config in (left, right):
        config["run"].pop("config_id")
        config["run"].pop("adapter_id")
        if duration:
            config["optimization"].pop("epochs")
            config["acceptance"].pop("expected_optimizer_steps")
        if targets:
            config["adapter"].pop("target_modules")
            config["acceptance"].pop("expected_trainable_parameter_count")
    return left, right


def verify_configs() -> dict[str, object]:
    configs = {key: load_toml(path) for key, path in CANDIDATE_CONFIGS.items()}
    shapes = {key: validate_config(config) for key, config in configs.items()}
    require([shapes[key]["total_optimizer_steps"] for key in "123"] == [60, 120, 60], "candidate step counts drifted")
    for config in configs.values():
        require(training_collection(config) == ("train", "training_path", "expected_training_count"), "candidate is not full training")
        require(config["data"]["expected_training_count"] == 160, "training count drifted")
        require(config["data"]["expected_validation_count"] == 40, "validation count drifted")
    left, right = normalized_pair(configs["1"], configs["2"], duration=True, targets=False)
    require(left == right, "Candidate 2 changes more than duration")
    left, right = normalized_pair(configs["1"], configs["3"], duration=False, targets=True)
    require(left == right, "Candidate 3 changes more than target surface")
    require(configs["3"]["adapter"]["target_modules"] == ["q_proj", "k_proj", "v_proj", "o_proj"], "Candidate 3 targets drifted")
    return {"config_sha256": {key: sha256_file(path) for key, path in CANDIDATE_CONFIGS.items()}, "shapes": shapes}


def verify_data() -> dict[str, str]:
    actual = {path: sha256_file(ROOT / path) for path in EXPECTED_DATA}
    require(actual == EXPECTED_DATA, "frozen dataset identity drifted")
    return actual


def verify_loss_boundary() -> dict[str, object]:
    messages = [
        {"role": "system", "content": ""},
        {"role": "user", "content": "Question"},
        {"role": "assistant", "content": "Answer"},
    ]
    with patch("scripts.run_pilot_training.render_training_messages", return_value=messages):
        item = tokenize_record({"example_id": "example-1"}, [], {}, FakeTokenizer(), 512)
    require(item["input_ids"].tolist() == [11, 12, 13, 21, 22], "complete token sequence drifted")
    require(item["labels"].tolist() == [-100, -100, -100, 21, 22], "assistant-only labels drifted")
    batch = collate([
        {"input_ids": torch.tensor([1, 2, 3]), "labels": torch.tensor([-100, 2, 3])},
        {"input_ids": torch.tensor([4, 5]), "labels": torch.tensor([-100, 5])},
    ], pad_token_id=0)
    require(batch["labels"].tolist() == [[-100, 2, 3], [-100, 5, -100]], "padding entered the loss")
    return {"prompt_tokens_masked": 3, "supervised_tokens": 2, "padding_masked": True}


def verify_provenance() -> dict[str, object]:
    model_config = load_project_configuration().model.values
    with tempfile.TemporaryDirectory() as directory:
        adapter = Path(directory)
        (adapter / "adapter_config.json").write_text("{}\n")
        weights = adapter / "adapter_model.safetensors"
        weights.write_bytes(b"checkpoint-weights")
        identity = write_adapter_provenance(
            adapter,
            adapter_id="chatgnt-full-candidate-1-v1",
            adapter_version="full-candidate-1-v1-run01-epoch-01",
            training_run_id="full-candidate-1-v1-run01",
            model_config=model_config,
            data_evidence={
                "dataset_id": "chatgnt-dataset-v1.2",
                "training_role": "train",
                "training": {"sha256": EXPECTED_DATA["data/dataset-v1/frozen-v1.2/train.jsonl"]},
            },
        )
        require(identity["provenance"]["training_dataset_id"] == "chatgnt-dataset-v1.2:train", "training provenance role drifted")
        weights.write_bytes(b"changed-checkpoint-weights")
        try:
            adapter_identity(adapter)
        except ContractError as exc:
            require("adapter digest mismatch" in str(exc), "unexpected tamper failure")
        else:
            raise RuntimeError("checkpoint weight tampering was not detected")
        return {"formal_identity": True, "weight_tampering_detected": True}


def verify_model_capacity() -> dict[str, int]:
    project = load_project_configuration()
    base = project.model.values["base_model"]
    snapshot = model_path(base["id"], base["revision"])
    model = AutoModelForCausalLM.from_pretrained(
        snapshot,
        local_files_only=True,
        dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        attn_implementation="sdpa",
    )
    adapted = get_peft_model(model, LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        task_type=TaskType.CAUSAL_LM,
        init_lora_weights=True,
    ))
    count = sum(parameter.numel() for parameter in adapted.parameters() if parameter.requires_grad)
    require(count == 2179072, "Candidate 3 trainable parameter count drifted")
    return {"candidate_3_trainable_parameter_count": count}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-capacity", action="store_true", help="Load the pinned base model and verify Candidate 3's actual trainable parameter count.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = {
        "result": "pass",
        "configuration": verify_configs(),
        "data": verify_data(),
        "loss_boundary": verify_loss_boundary(),
        "checkpoint_provenance": verify_provenance(),
        "model_capacity": verify_model_capacity() if args.model_capacity else {"executed": False},
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
