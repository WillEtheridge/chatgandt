"""Strict, non-repairing validation of untouched ChatG&T responses."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterator

from jsonschema import Draft202012Validator, ValidationError, validators

from .records import ContractError, read_strict_json, strict_json_loads


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESPONSE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "chatgnt-response-v1.schema.json"
RESPONSE_SCHEMA_ID = "urn:chatgnt:schema:response:v1"
JSON_WHITESPACE = " \t\n\r"

FAILURE_LABELS = (
    "markdown_fence",
    "surrounding_text",
    "duplicate_key",
    "json_syntax",
    "wrong_top_level_type",
    "missing_field",
    "unexpected_field",
    "wrong_field_type",
    "ingredient_count",
    "method_count",
    "null_value",
    "blank_string",
    "non_positive_amount",
)
_LABEL_INDEX = {label: index for index, label in enumerate(FAILURE_LABELS)}

_FENCE_RE = re.compile(
    r"\A```(?:[ \t]*[A-Za-z0-9][A-Za-z0-9._+-]*)?[ \t]*(?:\r\n|\n)"
    r"(?:(?P<body>.*)(?:\r\n|\n))?```[ \t]*\Z",
    re.DOTALL,
)
_SURROGATE_RE = re.compile("[\ud800-\udfff]")

NORMATIVE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": RESPONSE_SCHEMA_ID,
    "title": "ChatG&T response v1",
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "ingredients", "method", "garnish"],
    "properties": {
        "title": {"type": "string", "pattern": r"\S"},
        "ingredients": {
            "type": "array",
            "minItems": 3,
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["amount", "unit", "name"],
                "properties": {
                    "amount": {"type": "number", "exclusiveMinimum": 0},
                    "unit": {"type": "string", "pattern": r"\S"},
                    "name": {"type": "string", "pattern": r"\S"},
                },
            },
        },
        "method": {
            "type": "array",
            "minItems": 2,
            "maxItems": 5,
            "items": {"type": "string", "pattern": r"\S"},
        },
        "garnish": {"type": "string", "pattern": r"\S"},
    },
}


@dataclass(frozen=True)
class JsonNumberToken:
    """An exact finite JSON-number lexeme used only during validation."""

    lexeme: str

    @property
    def sign(self) -> int:
        """Return -1, 0, or 1 without materialising the number's magnitude."""
        coefficient = self.lexeme.lstrip("-").split("e", 1)[0].split("E", 1)[0]
        nonzero = any(character != "0" for character in coefficient if character != ".")
        if not nonzero:
            return 0
        return -1 if self.lexeme.startswith("-") else 1


@dataclass(frozen=True)
class _PairsObject:
    pairs: tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class _Duplicate:
    path: str
    key: str


@dataclass(frozen=True)
class _DecodeResult:
    value: Any | None
    end: int | None
    error_kind: str | None
    error_position: int | None


@dataclass(frozen=True)
class LoadedResponseSchema:
    """The checked exact schema, its supplied bytes, and configured validator."""

    value: dict[str, Any]
    raw_bytes: bytes
    sha256: str
    validator: Any


class _InvalidConstant(ValueError):
    pass


def _pairs_object(pairs: list[tuple[str, Any]]) -> _PairsObject:
    return _PairsObject(tuple(pairs))


def _number_token(lexeme: str) -> JsonNumberToken:
    return JsonNumberToken(lexeme)


def _invalid_constant(_constant: str) -> None:
    raise _InvalidConstant


_DECODER = json.JSONDecoder(
    object_pairs_hook=_pairs_object,
    parse_int=_number_token,
    parse_float=_number_token,
    parse_constant=_invalid_constant,
)


def _is_number(checker: Any, instance: Any) -> bool:
    if isinstance(instance, JsonNumberToken):
        return True
    return Draft202012Validator.TYPE_CHECKER.is_type(instance, "number")


def _exclusive_minimum(
    validator: Any, minimum: Any, instance: Any, schema: dict[str, Any]
) -> Iterator[ValidationError]:
    if isinstance(instance, JsonNumberToken):
        if type(minimum) is not int or minimum != 0:
            raise ContractError(
                "JsonNumberToken supports exclusiveMinimum only at the frozen boundary 0"
            )
        if instance.sign <= 0:
            yield ValidationError("project-owned numeric-bound failure")
        return
    yield from Draft202012Validator.VALIDATORS["exclusiveMinimum"](
        validator, minimum, instance, schema
    )


_TYPE_CHECKER = Draft202012Validator.TYPE_CHECKER.redefine("number", _is_number)
_ResponseValidator = validators.extend(
    Draft202012Validator,
    validators={"exclusiveMinimum": _exclusive_minimum},
    type_checker=_TYPE_CHECKER,
)


def _same_typed_value(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _same_typed_value(actual[key], expected[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _same_typed_value(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def load_response_schema_bytes(
    raw_bytes: bytes, source: str = "response schema"
) -> LoadedResponseSchema:
    """Load and fail fast unless bytes encode the complete normative schema."""
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raise ContractError(f"{source}: UTF-8 byte-order marks are not permitted")
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(f"{source}: invalid UTF-8: {exc}") from exc
    try:
        value = strict_json_loads(text)
    except ContractError as exc:
        raise ContractError(f"{source}: {exc}") from exc
    try:
        Draft202012Validator.check_schema(value)
    except Exception as exc:
        raise ContractError(f"{source}: failed Draft 2020-12 meta-schema check") from exc
    if not _same_typed_value(value, NORMATIVE_SCHEMA):
        raise ContractError(f"{source}: schema differs from frozen response schema v1")
    return LoadedResponseSchema(
        value=value,
        raw_bytes=raw_bytes,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        validator=_ResponseValidator(value),
    )


def load_response_schema(path: Path = RESPONSE_SCHEMA_PATH) -> LoadedResponseSchema:
    """Load the exact response schema from a strict configuration file."""
    try:
        value, raw_bytes = read_strict_json(path)
    except OSError as exc:
        raise ContractError(f"{path}: cannot read response schema") from exc
    try:
        Draft202012Validator.check_schema(value)
    except Exception as exc:
        raise ContractError(f"{path}: failed Draft 2020-12 meta-schema check") from exc
    if not _same_typed_value(value, NORMATIVE_SCHEMA):
        raise ContractError(f"{path}: schema differs from frozen response schema v1")
    return LoadedResponseSchema(
        value=value,
        raw_bytes=raw_bytes,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        validator=_ResponseValidator(value),
    )


def _skip_whitespace(text: str, offset: int) -> int:
    while offset < len(text) and text[offset] in JSON_WHITESPACE:
        offset += 1
    return offset


def _decode_at(text: str, offset: int) -> _DecodeResult:
    try:
        value, end = _DECODER.raw_decode(text, offset)
        return _DecodeResult(value, end, None, None)
    except _InvalidConstant:
        return _DecodeResult(None, None, "invalid_constant", None)
    except json.JSONDecodeError as exc:
        return _DecodeResult(None, None, "syntax", exc.pos)


def _complete_decode(text: str) -> _DecodeResult:
    start = _skip_whitespace(text, 0)
    if start == len(text):
        return _DecodeResult(None, None, "empty", None)
    decoded = _decode_at(text, start)
    if decoded.error_kind is not None:
        return decoded
    assert decoded.end is not None
    remainder = _skip_whitespace(text, decoded.end)
    if remainder != len(text):
        return _DecodeResult(None, None, "syntax", remainder)
    return decoded


def _pointer_component(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _child_path(parent: str, component: str | int) -> str:
    escaped = _pointer_component(str(component))
    return f"{parent}/{escaped}" if parent else f"/{escaped}"


def _convert_pairs(value: Any, path: str = "") -> tuple[Any, list[_Duplicate]]:
    duplicates: list[_Duplicate] = []
    if isinstance(value, _PairsObject):
        converted: dict[str, Any] = {}
        seen: set[str] = set()
        for key, item in value.pairs:
            item_path = _child_path(path, key)
            converted_item, nested = _convert_pairs(item, item_path)
            duplicates.extend(nested)
            if key in seen:
                duplicates.append(_Duplicate(item_path, key))
            else:
                converted[key] = converted_item
                seen.add(key)
        return converted, duplicates
    if isinstance(value, list):
        converted_items: list[Any] = []
        for index, item in enumerate(value):
            converted_item, nested = _convert_pairs(item, _child_path(path, index))
            converted_items.append(converted_item)
            duplicates.extend(nested)
        return converted_items, duplicates
    return value, duplicates


def _duplicate_diagnostics(duplicates: list[_Duplicate]) -> list[dict[str, str]]:
    return [
        {
            "label": "duplicate_key",
            "path": duplicate.path,
            "detail": "Object contains duplicate key "
            + json.dumps(duplicate.key, ensure_ascii=False, separators=(",", ":"))
            + ".",
        }
        for duplicate in duplicates
    ]


def _multiple_values(text: str) -> tuple[bool, list[_Duplicate]]:
    offset = _skip_whitespace(text, 0)
    values = 0
    duplicates: list[_Duplicate] = []
    while offset < len(text):
        decoded = _decode_at(text, offset)
        if decoded.error_kind is not None:
            return False, []
        assert decoded.end is not None
        _converted, found = _convert_pairs(decoded.value)
        duplicates.extend(found)
        values += 1
        if decoded.end == len(text):
            return values >= 2, duplicates
        next_offset = _skip_whitespace(text, decoded.end)
        if next_offset == decoded.end:
            return False, []
        if next_offset == len(text):
            return values >= 2, duplicates
        offset = next_offset
    return False, []


def _syntax_diagnostic(text: str, failure: _DecodeResult) -> dict[str, str]:
    if failure.error_kind == "empty":
        detail = "Output does not contain a JSON value."
    elif failure.error_kind == "invalid_constant":
        detail = "JSON contains an invalid numeric constant."
    else:
        multiple, _duplicates = _multiple_values(text)
        if multiple:
            detail = "Output contains multiple complete JSON values."
        elif failure.error_position is not None:
            detail = f"JSON syntax error at character {failure.error_position}."
        else:
            detail = "Output is not one complete strict JSON value."
    return {"label": "json_syntax", "path": "", "detail": detail}


def _surrounding_text_diagnostics(text: str) -> list[dict[str, str]] | None:
    trimmed = text.strip(JSON_WHITESPACE)
    spans: list[tuple[int, int, list[_Duplicate]]] = []
    for start, character in enumerate(trimmed):
        if character not in "{[":
            continue
        decoded = _decode_at(trimmed, start)
        if decoded.error_kind is not None or decoded.end is None:
            continue
        _converted, duplicates = _convert_pairs(decoded.value)
        if trimmed[:start].strip(JSON_WHITESPACE) or trimmed[decoded.end :].strip(
            JSON_WHITESPACE
        ):
            spans.append((start, decoded.end, duplicates))
    maximal = [
        span
        for span in spans
        if not any(
            other[0] <= span[0]
            and span[1] <= other[1]
            and (other[0], other[1]) != (span[0], span[1])
            for other in spans
        )
    ]
    if len(maximal) != 1:
        return None
    first_delimiter = min(
        (position for position, character in enumerate(trimmed) if character in "{["),
        default=-1,
    )
    start, _end, duplicates = maximal[0]
    if start != first_delimiter:
        return None
    return [
        {
            "label": "surrounding_text",
            "path": "",
            "detail": "A complete JSON object or array has non-whitespace text outside it.",
        },
        *_duplicate_diagnostics(duplicates),
    ]


def _parse_diagnostics(text: str) -> tuple[bool, Any | None, list[dict[str, str]]]:
    primary = _complete_decode(text)
    if primary.error_kind is None:
        converted, duplicates = _convert_pairs(primary.value)
        if not duplicates:
            return True, converted, []
        return False, None, _duplicate_diagnostics(duplicates)

    fence = _FENCE_RE.fullmatch(text.strip(JSON_WHITESPACE))
    if fence is not None:
        diagnostics = [
            {
                "label": "markdown_fence",
                "path": "",
                "detail": "Output is wrapped in a Markdown code fence.",
            }
        ]
        body = fence.group("body") if fence.group("body") is not None else ""
        inner = _complete_decode(body)
        if inner.error_kind is None:
            _converted, duplicates = _convert_pairs(inner.value)
            if duplicates:
                diagnostics.extend(_duplicate_diagnostics(duplicates))
        else:
            diagnostics.append(_syntax_diagnostic(body, inner))
        return False, None, diagnostics

    multiple, duplicates = _multiple_values(text)
    if multiple:
        return False, None, [
            *_duplicate_diagnostics(duplicates),
            {
                "label": "json_syntax",
                "path": "",
                "detail": "Output contains multiple complete JSON values.",
            },
        ]

    surrounding = _surrounding_text_diagnostics(text)
    if surrounding is not None:
        return False, None, surrounding
    return False, None, [_syntax_diagnostic(text, primary)]


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, JsonNumberToken):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise ContractError("validator encountered a non-JSON instance type")


def _error_path(error: ValidationError) -> str:
    path = ""
    for component in error.absolute_path:
        path = _child_path(path, component)
    return path


def _schema_diagnostics(
    instance: Any, loaded_schema: LoadedResponseSchema
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    for error in loaded_schema.validator.iter_errors(instance):
        keyword = error.validator
        path = _error_path(error)
        if keyword == "required":
            missing = set(error.validator_value) - set(error.instance)
            diagnostics.extend(
                {
                    "label": "missing_field",
                    "path": _child_path(path, key),
                    "detail": "Required field is missing.",
                }
                for key in missing
            )
        elif keyword == "additionalProperties":
            permitted = set(error.schema["properties"])
            unexpected = set(error.instance) - permitted
            diagnostics.extend(
                {
                    "label": "unexpected_field",
                    "path": _child_path(path, key),
                    "detail": "Field is not permitted.",
                }
                for key in unexpected
            )
        elif keyword == "type":
            if error.instance is None:
                diagnostics.append(
                    {"label": "null_value", "path": path, "detail": "Null is not permitted."}
                )
            elif not error.absolute_path:
                diagnostics.append(
                    {
                        "label": "wrong_top_level_type",
                        "path": "",
                        "detail": f"Expected object at root; observed {_type_name(error.instance)}.",
                    }
                )
            else:
                diagnostics.append(
                    {
                        "label": "wrong_field_type",
                        "path": path,
                        "detail": f"Expected {error.validator_value}; observed {_type_name(error.instance)}.",
                    }
                )
        elif keyword in ("minItems", "maxItems"):
            if path == "/ingredients":
                diagnostics.append(
                    {
                        "label": "ingredient_count",
                        "path": path,
                        "detail": f"Expected 3–8 items; observed {len(error.instance)}.",
                    }
                )
            elif path == "/method":
                diagnostics.append(
                    {
                        "label": "method_count",
                        "path": path,
                        "detail": f"Expected 2–5 items; observed {len(error.instance)}.",
                    }
                )
            else:
                raise ContractError("unexpected array-bound path in exact response schema")
        elif keyword == "pattern":
            diagnostics.append(
                {
                    "label": "blank_string",
                    "path": path,
                    "detail": "String must contain a non-whitespace character.",
                }
            )
        elif keyword == "exclusiveMinimum":
            diagnostics.append(
                {
                    "label": "non_positive_amount",
                    "path": path,
                    "detail": "Amount must be greater than zero.",
                }
            )
        else:
            raise ContractError(f"unmapped response-schema keyword: {keyword}")
    return diagnostics


def _ordered_diagnostics(diagnostics: list[dict[str, str]]) -> list[dict[str, str]]:
    for diagnostic in diagnostics:
        if diagnostic["label"] not in _LABEL_INDEX:
            raise ContractError("unknown validation failure label")
    return sorted(
        diagnostics,
        key=lambda item: (_LABEL_INDEX[item["label"]], item["path"], item["detail"]),
    )


def validate_response(raw_output: str, schema: LoadedResponseSchema) -> dict[str, Any]:
    """Validate one untouched decoded output against one exact loaded schema."""
    if not isinstance(raw_output, str):
        raise TypeError("raw_output must be a string")
    if not isinstance(schema, LoadedResponseSchema):
        raise TypeError("schema must be a LoadedResponseSchema")
    raw_bytes = raw_output.encode("utf-8")
    json_valid, parsed, diagnostics = _parse_diagnostics(raw_output)
    if json_valid:
        diagnostics.extend(_schema_diagnostics(parsed, schema))
    diagnostics = _ordered_diagnostics(diagnostics)
    labels_present = {diagnostic["label"] for diagnostic in diagnostics}
    failure_labels = [label for label in FAILURE_LABELS if label in labels_present]

    top_level_keys: list[str] | None = None
    ingredient_count: int | None = None
    method_step_count: int | None = None
    if json_valid and isinstance(parsed, dict):
        top_level_keys = sorted(parsed)
        if isinstance(parsed.get("ingredients"), list):
            ingredient_count = len(parsed["ingredients"])
        if isinstance(parsed.get("method"), list):
            method_step_count = len(parsed["method"])

    return {
        "record_schema_version": 1,
        "validator_version": "1",
        "response_schema_id": RESPONSE_SCHEMA_ID,
        "response_schema_sha256": schema.sha256,
        "raw_output_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "json_valid": json_valid,
        "schema_valid": json_valid and not diagnostics,
        "failure_labels": failure_labels,
        "diagnostics": diagnostics,
        "observations": {
            "raw_character_count": len(raw_output),
            "top_level_keys": top_level_keys,
            "ingredient_count": ingredient_count,
            "method_step_count": method_step_count,
        },
    }


def canonical_validation_line(result: dict[str, Any]) -> bytes:
    """Serialize a validation record canonically and safely as strict UTF-8."""
    serialized = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    escaped = _SURROGATE_RE.sub(lambda match: f"\\u{ord(match.group()):04x}", serialized)
    return (escaped + "\n").encode("utf-8")
