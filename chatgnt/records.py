"""Immutable records and strict/canonical JSON helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Literal

IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HEX_RE = re.compile(r"^[0-9a-f]{64}$")
UINT64_MAX = 2**64 - 1


class ContractError(ValueError):
    """A value or artefact does not satisfy the frozen contract."""


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ContractError(f"non-finite JSON number: {value}")


def strict_json_loads(text: str) -> Any:
    if text.startswith("\ufeff"):
        raise ContractError("UTF-8 byte-order marks are not permitted")
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ContractError(str(exc)) from exc


def read_strict_json(path: Path) -> tuple[Any, bytes]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContractError(f"{path}: UTF-8 byte-order marks are not permitted")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(f"{path}: invalid UTF-8: {exc}") from exc
    return strict_json_loads(text), raw


def validate_json_value(value: Any, location: str = "value") -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractError(f"{location}: non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for key, item in value.items():
            validate_json_value(item, f"{location}.{key}")
        return
    raise ContractError(f"{location}: not a JSON-compatible value")


def canonical_json(value: Any) -> str:
    validate_json_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_line(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def require_exact_keys(value: Any, keys: set[str], location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{location}: expected object")
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        unexpected = sorted(actual - keys)
        raise ContractError(
            f"{location}: key mismatch; missing={missing}, unexpected={unexpected}"
        )
    return value


def require_int(value: Any, location: str, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{location}: expected integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise ContractError(f"{location}: integer out of range")
    return value


def require_identifier(value: Any, location: str) -> str:
    if not isinstance(value, str) or IDENTIFIER_RE.fullmatch(value) is None:
        raise ContractError(f"{location}: invalid identifier")
    return value


def require_digest(value: Any, location: str) -> str:
    if not isinstance(value, str) or HEX_RE.fullmatch(value) is None:
        raise ContractError(f"{location}: expected lowercase SHA-256")
    return value


@dataclass(frozen=True)
class ErrorInfo:
    type: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.type, str) or not isinstance(self.message, str):
            raise ContractError("error type and message must be strings")


@dataclass(frozen=True)
class GenerationRequest:
    prompt_id: str
    user_prompt: str
    system_id: Literal["A", "B", "C", "D"]
    prompt_asset_id: str
    prompt_asset_sha256: str
    system_content: str
    adapter_enabled: bool
    repeat_index: int
    generation_seed: int

    def __post_init__(self) -> None:
        require_identifier(self.prompt_id, "prompt_id")
        if not isinstance(self.user_prompt, str) or not self.user_prompt:
            raise ContractError("user_prompt must be a non-empty string")
        if self.system_id not in ("A", "B", "C", "D"):
            raise ContractError("invalid system_id")
        require_identifier(self.prompt_asset_id, "prompt_asset_id")
        require_digest(self.prompt_asset_sha256, "prompt_asset_sha256")
        if not isinstance(self.system_content, str):
            raise ContractError("system_content must be a string")
        if not isinstance(self.adapter_enabled, bool):
            raise ContractError("adapter_enabled must be boolean")
        require_int(self.repeat_index, "repeat_index")
        require_int(self.generation_seed, "generation_seed", 0, UINT64_MAX)


@dataclass(frozen=True)
class GenerationProfile:
    profile_id: str
    do_sample: bool
    temperature: float
    top_p: float
    top_k: int
    repetition_penalty: float
    max_new_tokens: int
    min_new_tokens: int
    eos_token_ids: tuple[int, ...]
    pad_token_id: int
    num_beams: int
    num_return_sequences: int
    use_cache: bool
    cache_implementation: str
    return_dict_in_generate: bool
    output_scores: bool
    output_logits: bool
    stop_strings: None = None

    def __post_init__(self) -> None:
        require_identifier(self.profile_id, "profile_id")
        for field in ("do_sample", "use_cache", "return_dict_in_generate", "output_scores", "output_logits"):
            if not isinstance(getattr(self, field), bool):
                raise ContractError(f"{field} must be boolean")
        for field in ("temperature", "repetition_penalty"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ContractError(f"{field} must be positive")
        if isinstance(self.top_p, bool) or not isinstance(self.top_p, (int, float)) or not 0 < self.top_p <= 1:
            raise ContractError("top_p must be in (0, 1]")
        require_int(self.top_k, "top_k")
        require_int(self.max_new_tokens, "max_new_tokens", 1)
        require_int(self.min_new_tokens, "min_new_tokens")
        if not self.eos_token_ids:
            raise ContractError("eos_token_ids must be non-empty")
        for token_id in self.eos_token_ids:
            require_int(token_id, "eos_token_ids")
        require_int(self.pad_token_id, "pad_token_id")
        require_int(self.num_beams, "num_beams", 1)
        require_int(self.num_return_sequences, "num_return_sequences", 1)
        if not isinstance(self.cache_implementation, str) or not self.cache_implementation:
            raise ContractError("cache_implementation must be non-empty")
        if self.stop_strings is not None:
            raise ContractError("stop_strings must be null")

    def generation_kwargs(self) -> dict[str, Any]:
        return {
            "do_sample": self.do_sample,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "max_new_tokens": self.max_new_tokens,
            "min_new_tokens": self.min_new_tokens,
            "eos_token_id": list(self.eos_token_ids),
            "pad_token_id": self.pad_token_id,
            "num_beams": self.num_beams,
            "num_return_sequences": self.num_return_sequences,
            "use_cache": self.use_cache,
            "cache_implementation": self.cache_implementation,
            "return_dict_in_generate": self.return_dict_in_generate,
            "output_scores": self.output_scores,
            "output_logits": self.output_logits,
        }


@dataclass(frozen=True)
class TimingPolicy:
    metric_id: str
    enabled: bool
    synchronize_cuda: bool
    canonical: bool

    def __post_init__(self) -> None:
        require_identifier(self.metric_id, "metric_id")
        for field in ("enabled", "synchronize_cuda", "canonical"):
            if not isinstance(getattr(self, field), bool):
                raise ContractError(f"{field} must be boolean")


@dataclass(frozen=True)
class GenerationResult:
    attempt_status: Literal["success", "input_context_exceeded", "generation_error"]
    messages: tuple[dict[str, str], dict[str, str]]
    rendered_prompt: str | None
    input_token_ids: tuple[int, ...]
    input_token_count: int
    generated_token_ids: tuple[int, ...]
    generated_token_count: int
    visible_output_token_count: int
    raw_output: str | None
    raw_output_sha256: str | None
    termination_reason: Literal["eos_token", "max_new_tokens", "error"]
    terminal_token_id: int | None
    reached_max_new_tokens: bool
    generation_duration_ns: int | None
    error: ErrorInfo | None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["messages"] = list(value["messages"])
        value["input_token_ids"] = list(self.input_token_ids)
        value["generated_token_ids"] = list(self.generated_token_ids)
        return value


@dataclass(frozen=True)
class ScheduledAttempt:
    attempt_index: int
    prompt_id: str
    system_id: Literal["A", "B", "C", "D"]
    repeat_index: int
    generation_seed: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ATTEMPT_KEYS = {
    "schema_version", "run_id", "attempt_index", "prompt_id", "system_id",
    "repeat_index", "generation_seed", "attempt_status", "adapter_enabled",
    "prompt_asset_id", "prompt_asset_sha256", "messages", "rendered_prompt",
    "input_token_ids", "input_token_count", "generated_token_ids",
    "generated_token_count", "visible_output_token_count", "raw_output",
    "raw_output_sha256", "termination_reason", "terminal_token_id",
    "reached_max_new_tokens", "generation_duration_ns", "error",
}


def make_attempt_record(
    run_id: str,
    schedule: ScheduledAttempt,
    request: GenerationRequest,
    result: GenerationResult,
) -> dict[str, Any]:
    record = {
        "schema_version": 1,
        "run_id": run_id,
        "attempt_index": schedule.attempt_index,
        "prompt_id": schedule.prompt_id,
        "system_id": schedule.system_id,
        "repeat_index": schedule.repeat_index,
        "generation_seed": schedule.generation_seed,
        "adapter_enabled": request.adapter_enabled,
        "prompt_asset_id": request.prompt_asset_id,
        "prompt_asset_sha256": request.prompt_asset_sha256,
        **result.to_dict(),
    }
    if set(record) != ATTEMPT_KEYS:
        raise ContractError("internal attempt-record schema mismatch")
    return record
