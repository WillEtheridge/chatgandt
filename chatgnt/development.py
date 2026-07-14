"""Closed contract for the frozen prompt-development set."""

from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any

from .configuration import PROJECT_ROOT, load_prompts
from .identity import sha256_bytes
from .records import ContractError, canonical_line

DEVELOPMENT_PROMPTS_V1 = PROJECT_ROOT / "data" / "development" / "prompts-v1.jsonl"
DEVELOPMENT_PROMPTS_V1_SHA256 = "0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1"

FAMILY_SLUGS = {
    "advice_decision_support": "advice",
    "explanation_technical_understanding": "explanation",
    "low_stakes_emotional_support": "emotional",
    "creative_generation": "creative",
    "short_form_transformation": "transformation",
}
DEVELOPMENT_ROLES = ("clean", "naturalistic", "constrained", "robustness")
INPUT_FORMS = {
    "command",
    "command_with_code",
    "direct_request",
    "fragment",
    "informal_fragment",
    "informal_statement",
    "question",
    "request",
}
CHALLENGE_TAGS = {
    "artefact_completion",
    "code_input",
    "exact_text_preservation",
    "format_conflict",
    "intent_inference",
    "json_escaping",
    "length_constraint",
    "multiple_requirements",
    "text_rewriting",
}
METADATA_KEYS = {
    "challenge_tags",
    "development_role",
    "input_form",
    "intent_family",
}


def _require_enum(value: Any, allowed: set[str] | tuple[str, ...], location: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ContractError(f"{location}: unexpected value {value!r}")
    return value


def validate_development_prompts(path: Path = DEVELOPMENT_PROMPTS_V1) -> dict[str, Any]:
    """Validate the v1 development-set composition and canonical serialization."""

    prompts, raw = load_prompts(path)
    if len(prompts) != 20:
        raise ContractError(f"{path}: expected 20 prompts, found {len(prompts)}")

    expected_pairs = set(product(FAMILY_SLUGS, DEVELOPMENT_ROLES))
    observed_pairs: set[tuple[str, str]] = set()

    for index, prompt in enumerate(prompts, 1):
        location = f"{path}:{index}"
        if prompt.prompt != prompt.prompt.strip():
            raise ContractError(f"{location}.prompt: leading or trailing whitespace is not permitted")
        if set(prompt.metadata) != METADATA_KEYS:
            raise ContractError(f"{location}.metadata: keys must be {sorted(METADATA_KEYS)}")

        family = _require_enum(
            prompt.metadata["intent_family"], set(FAMILY_SLUGS), f"{location}.metadata.intent_family"
        )
        role = _require_enum(
            prompt.metadata["development_role"], DEVELOPMENT_ROLES, f"{location}.metadata.development_role"
        )
        _require_enum(prompt.metadata["input_form"], INPUT_FORMS, f"{location}.metadata.input_form")

        tags = prompt.metadata["challenge_tags"]
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ContractError(f"{location}.metadata.challenge_tags: expected a string list")
        if tags != sorted(set(tags)):
            raise ContractError(f"{location}.metadata.challenge_tags: values must be unique and sorted")
        unknown_tags = set(tags) - CHALLENGE_TAGS
        if unknown_tags:
            raise ContractError(f"{location}.metadata.challenge_tags: unknown values {sorted(unknown_tags)}")

        expected_id = f"dev-v1-{FAMILY_SLUGS[family]}-{role}"
        if prompt.prompt_id != expected_id:
            raise ContractError(f"{location}.prompt_id: expected {expected_id!r}")

        pair = (family, role)
        if pair in observed_pairs:
            raise ContractError(f"{location}: duplicate family/role pair {pair!r}")
        observed_pairs.add(pair)

    if observed_pairs != expected_pairs:
        missing = sorted(expected_pairs - observed_pairs)
        unexpected = sorted(observed_pairs - expected_pairs)
        raise ContractError(f"{path}: family/role coverage mismatch; missing={missing}, unexpected={unexpected}")

    canonical = b"".join(canonical_line(prompt.to_dict()) for prompt in prompts)
    if raw != canonical:
        raise ContractError(f"{path}: file is not canonically serialized")
    digest = sha256_bytes(raw)
    if digest != DEVELOPMENT_PROMPTS_V1_SHA256:
        raise ContractError(
            f"{path}: content differs from frozen v1 digest; "
            f"expected={DEVELOPMENT_PROMPTS_V1_SHA256}, actual={digest}"
        )

    return {
        "result": "pass",
        "version": 1,
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path),
        "sha256": digest,
        "prompt_count": len(prompts),
        "intent_family_count": len(FAMILY_SLUGS),
        "development_roles": list(DEVELOPMENT_ROLES),
        "family_role_pairs_complete": True,
        "canonical_jsonl": True,
    }
