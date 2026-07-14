"""Deterministic assembly and validation of versioned system-prompt assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .configuration import PROJECT_ROOT, load_prompt_asset, load_system_set
from .development import WORKED_EXAMPLES_V1, validate_worked_examples
from .identity import sha256_bytes
from .records import ContractError, read_strict_json

INSTRUCTIONS_V1 = PROJECT_ROOT / "data" / "prompt-engineering" / "instructions-v1.txt"
MINIMAL_PROMPT_V1 = PROJECT_ROOT / "config" / "prompts" / "minimal-v1.json"
MINIMAL_PROMPT_V1_SHA256 = "f09b7712fb9b36c9fc6fc54b1fc72fbf2d95cc8e5e1d8d570d88a54ccde2d821"
FIVE_SHOT_PROMPT_V1 = PROJECT_ROOT / "config" / "prompts" / "five-shot-v1.json"
FIVE_SHOT_PROMPT_V1_SHA256 = "7b8c25f04fba15373813862bba9705d4585ba919e855612909830757e4bd93d6"
DEVELOPMENT_AB_SYSTEM_SET_V1 = PROJECT_ROOT / "config" / "systems" / "development-ab-v1.json"
DEVELOPMENT_AB_SYSTEM_SET_V1_SHA256 = "c2c59b412f7982d07b026e61a347f03acdbbf2f7c8aa4136bf5094fecbae45cc"
FINAL_REMINDER = "For the actual user input, return only the required ChatG&T JSON object and nothing else."


def validate_minimal_prompt(path: Path = MINIMAL_PROMPT_V1) -> dict[str, Any]:
    """Validate System A's explicit empty-system prompt asset."""

    asset = load_prompt_asset(path)
    actual = {
        "schema_version": asset.schema_version,
        "prompt_asset_id": asset.prompt_asset_id,
        "version": asset.version,
        "worked_example_count": asset.worked_example_count,
        "content": asset.content,
    }
    expected = {
        "schema_version": 1,
        "prompt_asset_id": "minimal-v1",
        "version": "1",
        "worked_example_count": 0,
        "content": "",
    }
    if actual != expected:
        raise ContractError(f"{path}: differs from the explicit empty-system contract")
    if asset.source_sha256 != MINIMAL_PROMPT_V1_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen minimal-v1 digest; "
            f"expected={MINIMAL_PROMPT_V1_SHA256}, actual={asset.source_sha256}"
        )
    return {
        "result": "pass",
        "version": 1,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": asset.source_sha256,
        "prompt_asset_id": asset.prompt_asset_id,
        "worked_example_count": asset.worked_example_count,
        "content_character_count": len(asset.content),
        "explicit_empty_system_message": True,
    }


def load_instruction_text(path: Path = INSTRUCTIONS_V1) -> tuple[str, bytes]:
    """Load exact UTF-8 instruction text with one terminal newline."""

    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContractError(f"{path}: byte-order mark is not permitted")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(f"{path}: invalid UTF-8") from exc
    if "\r" in text or not text.endswith("\n") or text.endswith("\n\n"):
        raise ContractError(f"{path}: expected LF endings and exactly one terminal newline")
    content = text[:-1]
    if not content or content != content.strip():
        raise ContractError(f"{path}: instruction content must be non-empty and trimmed")
    return content, raw


def render_five_shot_content(
    instruction_path: Path = INSTRUCTIONS_V1,
    examples_path: Path = WORKED_EXAMPLES_V1,
) -> str:
    """Render the complete single-message prompt from frozen source content."""

    validate_worked_examples(examples_path)
    instructions, _ = load_instruction_text(instruction_path)
    examples_value, _ = read_strict_json(examples_path)

    sections = [instructions, "BEGIN WORKED EXAMPLES"]
    for index, example in enumerate(examples_value["worked_examples"], 1):
        response = json.dumps(example["assistant_response"], ensure_ascii=False, indent=2, allow_nan=False)
        sections.append(
            f"EXAMPLE {index}\n"
            f"User input:\n{example['user_prompt']}\n"
            f"Assistant output:\n{response}"
        )
    sections.extend(["END WORKED EXAMPLES", FINAL_REMINDER])
    return "\n\n".join(sections)


def expected_five_shot_asset() -> dict[str, Any]:
    """Return the exact version 1 prompt-asset value."""

    return {
        "schema_version": 1,
        "prompt_asset_id": "five-shot-v1",
        "version": "1",
        "worked_example_count": 5,
        "content": render_five_shot_content(),
    }


def validate_five_shot_prompt(path: Path = FIVE_SHOT_PROMPT_V1) -> dict[str, Any]:
    """Validate exact assembly, generic asset rules, and frozen identity."""

    asset = load_prompt_asset(path)
    expected = expected_five_shot_asset()
    actual = {
        "schema_version": asset.schema_version,
        "prompt_asset_id": asset.prompt_asset_id,
        "version": asset.version,
        "worked_example_count": asset.worked_example_count,
        "content": asset.content,
    }
    if actual != expected:
        raise ContractError(f"{path}: content or metadata differs from deterministic version 1 assembly")
    if asset.source_sha256 != FIVE_SHOT_PROMPT_V1_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen prompt v1 digest; "
            f"expected={FIVE_SHOT_PROMPT_V1_SHA256}, actual={asset.source_sha256}"
        )
    _, instruction_raw = load_instruction_text()
    return {
        "result": "pass",
        "version": 1,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": asset.source_sha256,
        "prompt_asset_id": asset.prompt_asset_id,
        "worked_example_count": asset.worked_example_count,
        "content_character_count": len(asset.content),
        "instruction_sha256": sha256_bytes(instruction_raw),
        "worked_examples_sha256": validate_worked_examples()["sha256"],
        "deterministic_assembly": True,
    }


def validate_development_ab_system_set(
    path: Path = DEVELOPMENT_AB_SYSTEM_SET_V1,
) -> dict[str, Any]:
    """Validate the frozen base-model A/B development-system mapping."""

    minimal_result = validate_minimal_prompt()
    five_shot_result = validate_five_shot_prompt()
    systems, raw = load_system_set(path, adapter_path=None)
    if [system.system_id for system in systems] != ["A", "B"]:
        raise ContractError(f"{path}: expected exactly Systems A and B")
    expected_assets = {
        "A": ("minimal-v1", MINIMAL_PROMPT_V1_SHA256),
        "B": ("five-shot-v1", FIVE_SHOT_PROMPT_V1_SHA256),
    }
    for system in systems:
        expected_id, expected_digest = expected_assets[system.system_id]
        if system.adapter_enabled:
            raise ContractError(f"{path}: System {system.system_id} must not enable an adapter")
        if (
            system.prompt_asset.prompt_asset_id != expected_id
            or system.prompt_asset.source_sha256 != expected_digest
        ):
            raise ContractError(f"{path}: System {system.system_id} prompt identity mismatch")

    digest = sha256_bytes(raw)
    if digest != DEVELOPMENT_AB_SYSTEM_SET_V1_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen development A/B system-set digest; "
            f"expected={DEVELOPMENT_AB_SYSTEM_SET_V1_SHA256}, actual={digest}"
        )
    return {
        "result": "pass",
        "version": 1,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": digest,
        "system_ids": [system.system_id for system in systems],
        "adapter_enabled": {system.system_id: system.adapter_enabled for system in systems},
        "prompt_assets": {
            "A": {"prompt_asset_id": "minimal-v1", "sha256": minimal_result["sha256"]},
            "B": {"prompt_asset_id": "five-shot-v1", "sha256": five_shot_result["sha256"]},
        },
        "untouched_base_runtime_only": True,
    }
