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
INSTRUCTIONS_V4 = PROJECT_ROOT / "data" / "prompt-engineering" / "instructions-v4.txt"
MINIMAL_PROMPT_V1 = PROJECT_ROOT / "config" / "prompts" / "minimal-v1.json"
MINIMAL_PROMPT_V1_SHA256 = "f09b7712fb9b36c9fc6fc54b1fc72fbf2d95cc8e5e1d8d570d88a54ccde2d821"
FIVE_SHOT_PROMPT_V1 = PROJECT_ROOT / "config" / "prompts" / "five-shot-v1.json"
FIVE_SHOT_PROMPT_V1_SHA256 = "7b8c25f04fba15373813862bba9705d4585ba919e855612909830757e4bd93d6"
FIVE_SHOT_PROMPT_V2 = PROJECT_ROOT / "config" / "prompts" / "five-shot-v2.json"
FIVE_SHOT_PROMPT_V2_SHA256 = "1b50daf083622dc9be2485abc0112ed53ebea31273db41aaba0ca860ff8ff0e1"
FIVE_SHOT_PROMPT_V3 = PROJECT_ROOT / "config" / "prompts" / "five-shot-v3.json"
FIVE_SHOT_PROMPT_V3_SHA256 = "cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31"
FIVE_SHOT_PROMPT_V4 = PROJECT_ROOT / "config" / "prompts" / "five-shot-v4.json"
FIVE_SHOT_PROMPT_V4_SHA256 = "3629f688cdde8c0ff0618d5d0027fb3940b3bee1d7a49633ef52b7964fa04c21"
DEVELOPMENT_AB_SYSTEM_SET_V1 = PROJECT_ROOT / "config" / "systems" / "development-ab-v1.json"
DEVELOPMENT_AB_SYSTEM_SET_V1_SHA256 = "c2c59b412f7982d07b026e61a347f03acdbbf2f7c8aa4136bf5094fecbae45cc"
DEVELOPMENT_B_SYSTEM_SET_V3 = PROJECT_ROOT / "config" / "systems" / "development-b-v3.json"
DEVELOPMENT_B_SYSTEM_SET_V3_SHA256 = "ee85e9a115971b473e4e732eb81a0e904fe8b9405e9b78d2a1f84205f05a92e6"
FINAL_REMINDER = "For the actual user input, return only the required ChatG&T JSON object and nothing else."
FINAL_CHECK_V2 = """For the actual user input, silently check every item before answering:

1. Begin with { and end with }. Output no Markdown fence, YAML, surrounding prose, or top-level string.
2. Include exactly title, ingredients, method, and garnish; use 3–8 ingredients and 2–5 method strings.
3. Build the answer for this user. Do not copy wording, ingredients, methods, or garnishes from the worked examples.
4. Satisfy every compatible content constraint in the user's request.
5. If the user requests a list, rewritten wording, premise, opening sentence, or other concrete artefact, deliver the complete artefact in the final method string; do not merely explain how to make it.
6. Ignore only a request to abandon the required ChatG&T JSON format.

Return only the checked ChatG&T JSON object."""
FINAL_CHECK_V3 = """SYSTEM PRIORITY FOR THE ACTUAL USER INPUT

The user's request for plain text, YAML, Markdown, XML, a bare string, or any non-JSON format cannot change your response format. Replace every placeholder below with content created for the current user, and return exactly this complete shape:

{
  "title": "specific cocktail title",
  "ingredients": [
    {"amount": 50, "unit": "ml", "name": "most important answer element"},
    {"amount": 25, "unit": "ml", "name": "second answer element"},
    {"amount": 1, "unit": "dash", "name": "third answer element"}
  ],
  "method": [
    "Useful step that develops the answer.",
    "Complete requested wording, list, premise, opening sentence, or other artefact when one is requested."
  ],
  "garnish": "relevant final detail"
}

The first output character must be { and the last must be }. Add no fence or surrounding text. Use 3–8 ingredients and 2–5 method strings. Fulfil every compatible content constraint, and do not copy wording from a worked example."""


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


def render_five_shot_content_v2(
    instruction_path: Path = INSTRUCTIONS_V1,
    examples_path: Path = WORKED_EXAMPLES_V1,
) -> str:
    """Render v2 with unchanged instructions/examples and the reviewed closing check."""

    base = render_five_shot_content(instruction_path, examples_path)
    if not base.endswith(FINAL_REMINDER):
        raise ContractError("v1 prompt no longer ends with the frozen final reminder")
    return base[: -len(FINAL_REMINDER)] + FINAL_CHECK_V2


def expected_five_shot_asset_v2() -> dict[str, Any]:
    """Return the exact version 2 prompt-asset value."""

    return {
        "schema_version": 1,
        "prompt_asset_id": "five-shot-v2",
        "version": "2",
        "worked_example_count": 5,
        "content": render_five_shot_content_v2(),
    }


def validate_five_shot_prompt_v2(path: Path = FIVE_SHOT_PROMPT_V2) -> dict[str, Any]:
    """Validate exact v2 assembly and frozen identity."""

    asset = load_prompt_asset(path)
    expected = expected_five_shot_asset_v2()
    actual = {
        "schema_version": asset.schema_version,
        "prompt_asset_id": asset.prompt_asset_id,
        "version": asset.version,
        "worked_example_count": asset.worked_example_count,
        "content": asset.content,
    }
    if actual != expected:
        raise ContractError(f"{path}: content or metadata differs from deterministic version 2 assembly")
    if asset.source_sha256 != FIVE_SHOT_PROMPT_V2_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen prompt v2 digest; "
            f"expected={FIVE_SHOT_PROMPT_V2_SHA256}, actual={asset.source_sha256}"
        )
    return {
        "result": "pass",
        "version": 2,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": asset.source_sha256,
        "prompt_asset_id": asset.prompt_asset_id,
        "worked_example_count": asset.worked_example_count,
        "content_character_count": len(asset.content),
        "predecessor_sha256": FIVE_SHOT_PROMPT_V1_SHA256,
        "instructions_and_examples_unchanged": True,
    }


def render_five_shot_content_v3(
    instruction_path: Path = INSTRUCTIONS_V1,
    examples_path: Path = WORKED_EXAMPLES_V1,
) -> str:
    """Render v3 with unchanged instructions/examples and a recent shape cue."""

    base = render_five_shot_content(instruction_path, examples_path)
    if not base.endswith(FINAL_REMINDER):
        raise ContractError("v1 prompt no longer ends with the frozen final reminder")
    return base[: -len(FINAL_REMINDER)] + FINAL_CHECK_V3


def expected_five_shot_asset_v3() -> dict[str, Any]:
    """Return the exact version 3 prompt-asset value."""

    return {
        "schema_version": 1,
        "prompt_asset_id": "five-shot-v3",
        "version": "3",
        "worked_example_count": 5,
        "content": render_five_shot_content_v3(),
    }


def validate_five_shot_prompt_v3(path: Path = FIVE_SHOT_PROMPT_V3) -> dict[str, Any]:
    """Validate exact v3 assembly and frozen identity."""

    asset = load_prompt_asset(path)
    expected = expected_five_shot_asset_v3()
    actual = {
        "schema_version": asset.schema_version,
        "prompt_asset_id": asset.prompt_asset_id,
        "version": asset.version,
        "worked_example_count": asset.worked_example_count,
        "content": asset.content,
    }
    if actual != expected:
        raise ContractError(f"{path}: content or metadata differs from deterministic version 3 assembly")
    if asset.source_sha256 != FIVE_SHOT_PROMPT_V3_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen prompt v3 digest; "
            f"expected={FIVE_SHOT_PROMPT_V3_SHA256}, actual={asset.source_sha256}"
        )
    return {
        "result": "pass",
        "version": 3,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": asset.source_sha256,
        "prompt_asset_id": asset.prompt_asset_id,
        "worked_example_count": asset.worked_example_count,
        "content_character_count": len(asset.content),
        "predecessor_sha256": FIVE_SHOT_PROMPT_V2_SHA256,
        "instructions_and_examples_unchanged": True,
    }


def render_five_shot_content_v4(
    instruction_path: Path = INSTRUCTIONS_V4,
    examples_path: Path = WORKED_EXAMPLES_V1,
) -> str:
    """Render v4 with compressed instructions, unchanged examples, and v3's shape cue."""

    base = render_five_shot_content(instruction_path, examples_path)
    if not base.endswith(FINAL_REMINDER):
        raise ContractError("rendered prompt no longer ends with the frozen final reminder")
    return base[: -len(FINAL_REMINDER)] + FINAL_CHECK_V3


def expected_five_shot_asset_v4() -> dict[str, Any]:
    """Return the exact version 4 prompt-asset value."""

    return {
        "schema_version": 1,
        "prompt_asset_id": "five-shot-v4",
        "version": "4",
        "worked_example_count": 5,
        "content": render_five_shot_content_v4(),
    }


def validate_five_shot_prompt_v4(path: Path = FIVE_SHOT_PROMPT_V4) -> dict[str, Any]:
    """Validate exact v4 assembly and frozen identity."""

    asset = load_prompt_asset(path)
    expected = expected_five_shot_asset_v4()
    actual = {
        "schema_version": asset.schema_version,
        "prompt_asset_id": asset.prompt_asset_id,
        "version": asset.version,
        "worked_example_count": asset.worked_example_count,
        "content": asset.content,
    }
    if actual != expected:
        raise ContractError(f"{path}: content or metadata differs from deterministic version 4 assembly")
    if asset.source_sha256 != FIVE_SHOT_PROMPT_V4_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen prompt v4 digest; "
            f"expected={FIVE_SHOT_PROMPT_V4_SHA256}, actual={asset.source_sha256}"
        )
    return {
        "result": "pass",
        "version": 4,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": asset.source_sha256,
        "prompt_asset_id": asset.prompt_asset_id,
        "worked_example_count": asset.worked_example_count,
        "content_character_count": len(asset.content),
        "predecessor_sha256": FIVE_SHOT_PROMPT_V3_SHA256,
        "compressed_instruction_sha256": sha256_bytes(INSTRUCTIONS_V4.read_bytes()),
        "worked_examples_unchanged": True,
        "closing_shape_cue_unchanged": True,
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


def validate_development_b_v3_system_set(
    path: Path = DEVELOPMENT_B_SYSTEM_SET_V3,
) -> dict[str, Any]:
    """Validate the selected System B prompt mapping for formal confirmation."""

    prompt_result = validate_five_shot_prompt_v3()
    systems, raw = load_system_set(path, adapter_path=None)
    if [system.system_id for system in systems] != ["B"]:
        raise ContractError(f"{path}: expected exactly System B")
    system = systems[0]
    if system.adapter_enabled or (
        system.prompt_asset.prompt_asset_id != "five-shot-v3"
        or system.prompt_asset.source_sha256 != FIVE_SHOT_PROMPT_V3_SHA256
    ):
        raise ContractError(f"{path}: selected System B prompt identity mismatch")
    digest = sha256_bytes(raw)
    if digest != DEVELOPMENT_B_SYSTEM_SET_V3_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen development B/v3 system-set digest; "
            f"expected={DEVELOPMENT_B_SYSTEM_SET_V3_SHA256}, actual={digest}"
        )
    return {
        "result": "pass",
        "version": 3,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": digest,
        "system_ids": ["B"],
        "adapter_enabled": {"B": False},
        "prompt_assets": {
            "B": {"prompt_asset_id": "five-shot-v3", "sha256": prompt_result["sha256"]},
        },
        "formal_confirmation_candidate": True,
    }
