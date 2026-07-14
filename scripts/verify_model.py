"""Verify the pinned Qwen snapshot, canonical chat template, and CPU generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import tomllib
from pathlib import Path

import psutil
import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
MODEL_CONFIG_PATH = ROOT / "config" / "model.toml"
MODEL_ARTIFACTS_ROOT = ROOT / "artifacts" / "models"


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Also load the model and run a short CPU generation.",
    )
    return parser.parse_args()


def load_project_model_config() -> dict:
    """Load the project's immutable model selection."""
    with MODEL_CONFIG_PATH.open("rb") as config_file:
        return tomllib.load(config_file)


def model_path(model_id: str, revision: str) -> Path:
    """Return the expected local snapshot path."""
    repository_directory = model_id.replace("/", "--")
    return MODEL_ARTIFACTS_ROOT / repository_directory / revision


def gibibytes(byte_count: int) -> float:
    """Convert bytes to GiB."""
    return round(byte_count / (1024**3), 3)


def sha256(file_path: Path) -> str:
    """Calculate a file digest without loading the full file into memory."""
    digest = hashlib.sha256()
    with file_path.open("rb") as input_file:
        while chunk := input_file.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """Verify local-only tokenizer loading and optional model generation."""
    args = parse_args()
    project_config = load_project_model_config()
    selected_model = project_config["base_model"]
    selected_chat = project_config["canonical_chat"]
    snapshot_path = model_path(selected_model["id"], selected_model["revision"])

    if not snapshot_path.is_dir():
        raise FileNotFoundError(f"Pinned snapshot not found: {snapshot_path}")

    weights_path = snapshot_path / "model.safetensors"
    weights_sha256 = sha256(weights_path)
    if weights_sha256 != selected_model["weights_sha256"]:
        raise AssertionError("The local model weights do not match the pinned digest")

    model_metadata = AutoConfig.from_pretrained(
        snapshot_path,
        local_files_only=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot_path,
        local_files_only=True,
    )
    messages = [
        {
            "role": "system",
            "content": selected_chat["minimal_system_message"],
        },
        {
            "role": "user",
            "content": "Respond with exactly the word READY and nothing else.",
        }
    ]
    rendered_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=selected_chat["add_generation_prompt"],
    )
    encoded_prompt = tokenizer(
        rendered_prompt,
        add_special_tokens=False,
        return_tensors="pt",
    )

    vendor_message = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
    if selected_chat["vendor_system_message"] is False and vendor_message in rendered_prompt:
        raise AssertionError("Vendor system message was injected into the canonical prompt")

    report: dict = {
        "selection": {
            "model_id": selected_model["id"],
            "revision": selected_model["revision"],
            "snapshot_path": str(snapshot_path.relative_to(ROOT)),
            "weights_sha256": weights_sha256,
        },
        "model_config": {
            "architectures": model_metadata.architectures,
            "max_position_embeddings": model_metadata.max_position_embeddings,
            "model_type": model_metadata.model_type,
            "pinned_max_context_tokens": selected_model["max_context_tokens"],
        },
        "tokenizer": {
            "class": tokenizer.__class__.__name__,
            "length": len(tokenizer),
            "model_max_length": tokenizer.model_max_length,
            "chat_template_sha256": hashlib.sha256(
                tokenizer.chat_template.encode("utf-8")
            ).hexdigest(),
        },
        "canonical_prompt": {
            "messages": messages,
            "rendered": rendered_prompt,
            "token_count": encoded_prompt.input_ids.shape[-1],
            "token_ids": encoded_prompt.input_ids[0].tolist(),
            "vendor_system_message_present": vendor_message in rendered_prompt,
        },
    }

    if args.generate:
        process = psutil.Process()
        rss_before_load = process.memory_info().rss
        load_started = time.perf_counter()
        model = AutoModelForCausalLM.from_pretrained(
            snapshot_path,
            local_files_only=True,
            dtype="auto",
            device_map="cpu",
            low_cpu_mem_usage=True,
        )
        model.eval()
        load_seconds = time.perf_counter() - load_started
        rss_after_load = process.memory_info().rss

        generation_started = time.perf_counter()
        with torch.inference_mode():
            generated_ids = model.generate(
                **encoded_prompt,
                do_sample=False,
                max_new_tokens=8,
            )
        generation_seconds = time.perf_counter() - generation_started
        new_token_ids = generated_ids[0, encoded_prompt.input_ids.shape[-1] :]

        report["model"] = {
            "class": model.__class__.__name__,
            "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
            "parameter_dtypes": sorted(
                {str(parameter.dtype) for parameter in model.parameters()}
            ),
            "device": str(model.device),
            "load_seconds": round(load_seconds, 4),
            "rss_before_load_gib": gibibytes(rss_before_load),
            "rss_after_load_gib": gibibytes(rss_after_load),
        }
        report["generation"] = {
            "do_sample": False,
            "maximum_new_tokens": 8,
            "generated_token_count": new_token_ids.shape[-1],
            "generated_token_ids": new_token_ids.tolist(),
            "raw_output": tokenizer.decode(new_token_ids, skip_special_tokens=True),
            "generation_seconds": round(generation_seconds, 4),
        }

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
