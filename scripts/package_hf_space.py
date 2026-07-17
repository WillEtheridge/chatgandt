#!/usr/bin/env python3
"""Build the allowlisted Hugging Face Space bundle."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "deployment/huggingface/space"
DEFAULT_OUTPUT = ROOT / "artifacts/deployment/hf-space"
FILES = (
    "chatgnt/__init__.py",
    "chatgnt/configuration.py",
    "chatgnt/identity.py",
    "chatgnt/inference.py",
    "chatgnt/live_service.py",
    "chatgnt/records.py",
    "chatgnt/validation.py",
    "config/generation.toml",
    "config/inference.toml",
    "config/model-files.json",
    "config/model.toml",
    "config/prompts/five-shot-v3.json",
    "config/prompts/minimal-v1.json",
    "schemas/chatgnt-response-v1.schema.json",
)


def package(output: Path) -> tuple[str, ...]:
    output = output.resolve()
    if ROOT not in output.parents:
        raise ValueError("output must be inside the project")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name in ("README.md", "app.py", "requirements.txt"):
        shutil.copy2(SOURCE / name, output / name)
    for relative in FILES:
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    inference_path = output / "chatgnt/inference.py"
    inference = inference_path.read_text(encoding="utf-8")
    load_needle = "            low_cpu_mem_usage=False,\n        )"
    freeze_needle = "        active = sorted(model.active_adapters)"
    if inference.count(load_needle) != 1 or inference.count(freeze_needle) != 1:
        raise ValueError("frozen inference loader no longer matches the ZeroGPU packaging transform")
    inference = inference.replace(
        load_needle,
        '            low_cpu_mem_usage=False, torch_device="cpu",\n        )',
    ).replace(
        freeze_needle,
        "        for parameter in model.parameters():\n            parameter.requires_grad_(False)\n        active = sorted(model.active_adapters)",
    )
    inference_path.write_text(inference, encoding="utf-8")
    return tuple(sorted(path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    for relative in package(args.output):
        print(relative)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
