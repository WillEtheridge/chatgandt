"""Report the reproducible ML environment without loading model weights."""

from __future__ import annotations

import json
import platform
from importlib.metadata import version

import torch
from peft import LoraConfig


PACKAGES = (
    "accelerate",
    "datasets",
    "huggingface-hub",
    "peft",
    "psutil",
    "safetensors",
    "torch",
    "transformers",
    "trl",
)


def main() -> None:
    """Print machine-readable versions and a minimal PEFT construction check."""
    lora_config = LoraConfig(
        r=4,
        lora_alpha=8,
        target_modules=["q_proj", "v_proj"],
        task_type="CAUSAL_LM",
    )

    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {package: version(package) for package in PACKAGES},
        "torch": {
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
        },
        "peft": {
            "config_constructed": True,
            "rank": lora_config.r,
            "target_modules": sorted(lora_config.target_modules),
            "task_type": str(lora_config.task_type),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
