# Step 8 Schema Validation Specification

- **Specification version:** 1.3
- **Status:** Frozen; passed adversarial review; approved for implementation
- **Date:** 2026-07-14

## Review history

The specification received four fresh adversarial reviews:

1. Version 1.0 was blocked because ordinary Python integer and `Decimal` conversion cannot represent every valid JSON number, and nested recipe objects made the surrounding-text candidate rule inconsistent.
2. Version 1.1 was blocked because multiple top-level values conflicted with surrounding-text classification, schema loading did not enforce the exact normative schema, and invalid content inside fences had ambiguous label combinations.
3. Version 1.2 was blocked because escaped surrogate keys could make canonical UTF-8 serialization fail and the Markdown-fence definition was not executable enough to stabilize labels.
4. Version 1.3 passed with no remaining material scientific, evidential, or executable blocker.

## Purpose

This specification defines the executable hard-structure check for an untouched ChatG&T model response. It converts the normal-response rules in [ChatG&T behavioural contract](behavioural-contract.md) into a strict parser, a portable JSON Schema, stable failure labels, deterministic diagnostics, and an acceptance-test suite.

The validator measures what the model returned. It must not extract, coerce, repair, retry, or replace model output. Usefulness, metaphorical coherence, and recipe-style execution remain separate qualitative judgments.

## Implementation boundary

Step 8 will add:

```text
schemas/chatgnt-response-v1.schema.json
chatgnt/validation.py
tests/test_validation.py
```

[`jsonschema==4.26.0`](https://pypi.org/project/jsonschema/4.26.0/) will be added as a direct, exactly pinned dependency and resolved into `uv.lock`. The implementation will extend `jsonschema.Draft202012Validator` only for the lossless internal JSON-number type defined below; dialect selection and all other keywords retain the pinned Draft 2020-12 implementation.

The validator is independent of PyTorch and model loading. Its core operation is a pure function of:

1. one Python `str` containing the untouched decoded model output; and
2. the exact response-schema bytes.

The inference harness remains responsible for execution status and raw response evidence. A future evaluation layer may link a validation result to `run_id` and `attempt_index`, but those scheduling identities are not inputs to the core validator.

## Response schema

The schema uses JSON Schema Draft 2020-12 and the stable identifier:

```text
urn:chatgnt:schema:response:v1
```

It has the following normative structure:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:chatgnt:schema:response:v1",
  "title": "ChatG&T response v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["title", "ingredients", "method", "garnish"],
  "properties": {
    "title": {
      "type": "string",
      "pattern": "\\S"
    },
    "ingredients": {
      "type": "array",
      "minItems": 3,
      "maxItems": 8,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["amount", "unit", "name"],
        "properties": {
          "amount": {
            "type": "number",
            "exclusiveMinimum": 0
          },
          "unit": {
            "type": "string",
            "pattern": "\\S"
          },
          "name": {
            "type": "string",
            "pattern": "\\S"
          }
        }
      }
    },
    "method": {
      "type": "array",
      "minItems": 2,
      "maxItems": 5,
      "items": {
        "type": "string",
        "pattern": "\\S"
      }
    },
    "garnish": {
      "type": "string",
      "pattern": "\\S"
    }
  }
}
```

Normative interpretations:

- Objects are closed at the response and ingredient levels.
- JSON object key order is irrelevant.
- `amount` accepts positive integer or fractional JSON numbers. JSON booleans do not satisfy `number`.
- `unit` has an open vocabulary.
- A string must contain at least one non-whitespace character.
- No minimum or maximum character lengths are introduced in version 1.
- Array boundaries are inclusive.
- Required values cannot be `null`.
- The schema must pass `Draft202012Validator.check_schema` before it can be used.

Schema loading is fail-fast configuration work, not a response-validation result. It uses the project's ordinary strict configuration-file loader, not the response parser or `JsonNumberToken`. Invalid UTF-8 or JSON, a byte-order mark, a duplicate schema key, a failed meta-schema check, or any parsed value not structurally equal to the complete normative schema above raises a configuration error before output evaluation. Structural equality includes `$schema`, `$id`, every keyword and value, and every array item in the shown order; JSON object member order and file formatting remain irrelevant. The digest still covers the exact supplied schema-file bytes.

This equality gate proves before validation that the only active instance-validation keywords are `type`, `required`, `additionalProperties`, `minItems`, `maxItems`, `items`, `pattern`, and `exclusiveMinimum` with boundary `0`. Any schema change requires a new specification version rather than being discovered as an unmapped error during response evaluation.

## Strict parsing

The primary parse operates on the complete raw string.

It must:

- allow only JSON-defined leading and trailing whitespace: space, tab, line feed, and carriage return;
- require exactly one complete JSON value;
- reject empty or malformed output;
- reject duplicate object keys at every nesting level;
- reject `NaN`, `Infinity`, and `-Infinity`;
- preserve finite JSON numbers without coercing strings or booleans; and
- perform no Markdown removal, substring extraction, normalization, repair, or retry.

The grammar decoder uses an `object_pairs_hook` that returns an internal immutable, pair-preserving object rather than immediately converting to `dict`. A recursive post-parse walk then identifies every repeated key with its full RFC 6901 path and converts duplicate-free objects to ordinary dictionaries. This is required because an exception raised directly inside `object_pairs_hook` cannot identify the parent path of a nested duplicate.

The decoder rejects non-standard constants through `parse_constant`. Both `parse_int` and `parse_float` return an internal immutable `JsonNumberToken` containing the exact number lexeme. They must not call `int`, `float`, or `decimal.Decimal` on the complete token.

This lossless representation avoids Python's integer-string digit limit and the finite exponent range of `Decimal`. `JsonNumberToken` exposes only the operations required by the frozen schema:

- recognition as a JSON Schema `number`; and
- exact classification as negative, zero, or positive from its sign and coefficient digits.

The project validator extends the Draft 2020-12 number type check to accept `JsonNumberToken` while continuing to reject booleans. Its `exclusiveMinimum` implementation accepts these tokens only for the frozen numeric boundary `0` and determines the result from the token's exact sign/zero classification. Encountering any other numeric-bound keyword or boundary with a `JsonNumberToken` is a fail-fast schema-configuration error, not an approximate comparison.

Parsed values and number tokens are internal only and are not persisted in the result. Thus arbitrarily long integers and exponent fields remain valid JSON without requiring the application to materialise their mathematical magnitude, while the only response-schema question—whether an ingredient amount is greater than zero—is answered exactly.

`json_valid` is true for any value that passes this parser, including a scalar, array, or `null`. The schema separately determines whether that parsed value is a ChatG&T response.

### Parse and classification algorithm

The grammar decoder can decode one value from a specified offset and report its end offset. Strict success additionally requires complete consumption apart from JSON whitespace and no duplicate keys.

Classification follows this fixed precedence:

1. Decode the complete raw output. If its grammar is complete and it has no duplicate keys, set `json_valid: true` and proceed to schema validation.
2. If the complete grammar succeeds but duplicate keys exist, set `json_valid: false`, emit `duplicate_key` diagnostics, and stop parse classification.
3. If complete decoding fails, check for one recognized outer Markdown fence. Parse only its body for diagnostics using the fence rules below, then stop parse classification.
4. Otherwise, attempt to segment the entire whitespace-trimmed output into two or more complete JSON values separated only by JSON whitespace. If successful, emit `json_syntax` with the multiple-values detail below, add any duplicate-key diagnostics discovered within those values, and stop. This rule applies to values of every top-level type and precedes surrounding-text discovery.
5. Otherwise, perform the object/array span discovery defined for `surrounding_text`. Emit that label, plus any duplicate-key diagnostics inside the sole eligible span, only if its complete eligibility rule passes.
6. Otherwise emit `json_syntax` using the primary decoder's stable failure position where available.

No branch feeds a diagnostic candidate into schema validation.

## Failure classification

Failure labels are stable project vocabulary. Library exception messages are never used as metric labels.

The canonical label order is:

1. `markdown_fence`
2. `surrounding_text`
3. `duplicate_key`
4. `json_syntax`
5. `wrong_top_level_type`
6. `missing_field`
7. `unexpected_field`
8. `wrong_field_type`
9. `ingredient_count`
10. `method_count`
11. `null_value`
12. `blank_string`
13. `non_positive_amount`

Labels are deduplicated and emitted in this order. Multiple independent failures may be retained.

### Parse labels

- `markdown_fence`: the complete fence grammar below matches. The wrapper remains part of the raw response and therefore makes `json_valid` false. Fence handling is exclusive: a duplicate-free, complete inner JSON value produces only `markdown_fence`; a complete inner value with duplicates produces `markdown_fence` plus `duplicate_key`; every other inner body produces `markdown_fence` plus `json_syntax`. `surrounding_text` discovery never runs inside a recognized fence, and inner content is never schema-validated.
- `surrounding_text`: exactly one maximal grammar-complete object or array can be decoded from a contiguous substring, with non-whitespace, non-fence content before or after it. Candidate starts are inspected at `{` and `[` characters. Any successful span strictly contained inside another successful span is discarded before counting, so nested ingredient objects and arrays do not make a complete response ambiguous. The sole remaining span must begin at the first object/array delimiter in the whitespace-trimmed raw text; this prevents a valid nested array inside a malformed outer object from being misclassified as surrounding text. Zero or multiple eligible maximal spans receive `json_syntax` instead. Duplicates inside the eligible span add `duplicate_key`; they do not prevent `surrounding_text`. Diagnostic extraction must not change `json_valid` or feed extracted content into schema validation.
- `duplicate_key`: strict parsing encounters a repeated key. This label applies at any nesting depth.
- `json_syntax`: the response is empty, contains an invalid constant, is malformed, contains two or more top-level JSON values, or otherwise cannot be classified more specifically.

Diagnostic inspection must remain bounded to the current string. It does not call a model, retry generation, or create a replacement response.

### Markdown-fence grammar

Fence recognition first removes JSON whitespace characters—space, tab, line feed, and carriage return—from both ends of the complete raw string. It then applies this anchored regular expression with Python `re.DOTALL`:

~~~regex
\A```(?:[ \t]*[A-Za-z0-9][A-Za-z0-9._+-]*)?[ \t]*(?:\r\n|\n)(?:(?P<body>.*)(?:\r\n|\n))?```[ \t]*\Z
~~~

Therefore:

- delimiters contain exactly three backticks;
- the opening delimiter has zero indentation after the outer whitespace removal;
- an optional ASCII language identifier may follow immediately or after spaces/tabs;
- only letters, digits, `.`, `_`, `+`, and `-` occur in that identifier;
- only LF or CRLF ends the opening line and the optional final body line;
- an empty body is allowed for classification and subsequently fails inner JSON parsing;
- the closing delimiter begins at the start of its line, contains exactly three backticks, and permits only spaces/tabs afterward;
- JSON whitespace may surround the complete outer fence; and
- bare-CR line endings, four-or-more-backtick delimiters, closing indentation, a multi-token info string, a same-line body/closing delimiter, or non-whitespace after the closing line do not form a recognized outer fence.

If the optional body group does not participate, its diagnostic body is the empty string. If it participates, the separating final LF or CRLF is excluded from the body.

### Schema labels

Schema errors map as follows:

| Condition | Label |
| --- | --- |
| Non-null top-level value is not an object | `wrong_top_level_type` |
| Required property absent | `missing_field` |
| Property outside a closed object | `unexpected_field` |
| Present non-null value has the wrong type | `wrong_field_type` |
| `ingredients` has fewer than 3 or more than 8 items | `ingredient_count` |
| `method` has fewer than 2 or more than 5 items | `method_count` |
| A required or schema-governed value is `null` | `null_value` |
| A governed string contains no non-whitespace character | `blank_string` |
| An ingredient amount is zero or negative | `non_positive_amount` |

Cascade rules:

- `null_value` replaces a type label for the same path.
- Top-level `null` receives `null_value`; other non-object top-level values receive `wrong_top_level_type`.
- A value of the wrong array type does not also receive a count label.
- A non-object ingredient receives `wrong_field_type`; missing or unexpected ingredient fields are not inferred for that item.
- A boolean ingredient amount receives `wrong_field_type`, not `non_positive_amount`.
- Repeated occurrences retain separate diagnostics but only one copy of the label.

The mapper uses structured `ValidationError` attributes, never `ValidationError.message`:

- `required` diagnostics are derived from the set difference between the keyword's required names and the instance keys;
- `additionalProperties` diagnostics are derived from instance keys absent from the exact schema's `properties`;
- `type`, `minItems`, `maxItems`, `pattern`, and `exclusiveMinimum` use the error's keyword, instance, instance path, and frozen schema value; and
- any other error keyword is a configuration error because exact schema equality should have made it impossible.

`generation_failure` is not emitted by this validator. The evaluation layer derives it from a non-success inference attempt and does not call structural validation when no visible successful output exists.

## Validation result

The result is a closed, deterministic, JSON-serializable record with exactly these fields:

```json
{
  "record_schema_version": 1,
  "validator_version": "1",
  "response_schema_id": "urn:chatgnt:schema:response:v1",
  "response_schema_sha256": "64 lowercase hexadecimal characters",
  "raw_output_sha256": "64 lowercase hexadecimal characters",
  "json_valid": true,
  "schema_valid": false,
  "failure_labels": ["ingredient_count"],
  "diagnostics": [
    {
      "label": "ingredient_count",
      "path": "/ingredients",
      "detail": "Expected 3–8 items; observed 2."
    }
  ],
  "observations": {
    "raw_character_count": 217,
    "top_level_keys": ["garnish", "ingredients", "method", "title"],
    "ingredient_count": 2,
    "method_step_count": 3
  }
}
```

Rules:

- SHA-256 digests are calculated over the exact UTF-8 raw-output bytes and exact schema-file bytes.
- `schema_valid` is false whenever `json_valid` is false.
- A valid non-object JSON value has `json_valid: true` and `schema_valid: false`.
- `schema_valid` is true exactly when strict parsing succeeds and the exact response schema reports no errors.
- `failure_labels` contains exactly the distinct labels represented by `diagnostics`, in canonical order. A schema-valid result has empty labels and diagnostics.
- Diagnostics contain exactly `label`, `path`, and `detail`.
- Paths use RFC 6901 JSON Pointer. The root path is the empty string.
- Missing and unexpected properties point to the absent or extra property path.
- Diagnostic text is generated from project-owned templates, never copied from `jsonschema` messages.
- Diagnostics are sorted by canonical label order, then path, then detail.
- `raw_character_count` uses Python string length before any processing.
- Parsed-value observations are derived only from the primary strict value when `json_valid` is true. Diagnostic fence or surrounding-text candidates never populate them.
- `top_level_keys` is a sorted array only when that primary value is an object; otherwise it is `null`.
- Ingredient and method counts are integers only when the corresponding field of that primary object is an array; otherwise they are `null`.
- No parsed, normalized, extracted, or repaired response is included.
- No timestamp or machine identity is included.

Canonical persisted serialization first uses `json.dumps` with `ensure_ascii=False`, sorted object keys, compact separators, and `allow_nan=False`. Before UTF-8 encoding, every Python code point from U+D800 through U+DFFF in the serialized string is replaced by the six ASCII characters `\u` followed by its four lowercase hexadecimal digits. This applies to isolated surrogates and surrogate pairs; every other non-ASCII character remains unescaped. The resulting string receives one trailing newline and is then encoded as strict UTF-8.

This surrogate-escaping pass is part of canonical serialization, not response repair. It allows observations and diagnostics derived from valid JSON escape sequences such as `"\ud800"` to remain representable without changing `json_valid`, `schema_valid`, paths, or labels. Repeated validation and serialization of the same raw output and schema must be byte-equivalent.

### Diagnostic templates

The following text is normative. `{key}` uses compact `ensure_ascii=False` JSON-string encoding. `{expected}` and `{observed}` use the canonical type names `object`, `array`, `string`, `number`, `boolean`, and `null`. Character positions are zero-based Python string indices.

| Label and condition | Path | Detail |
| --- | --- | --- |
| `markdown_fence` | empty root path | `Output is wrapped in a Markdown code fence.` |
| `surrounding_text` | empty root path | `A complete JSON object or array has non-whitespace text outside it.` |
| `duplicate_key` | duplicated property path | `Object contains duplicate key {key}.` |
| `json_syntax`, empty | empty root path | `Output does not contain a JSON value.` |
| `json_syntax`, multiple values | empty root path | `Output contains multiple complete JSON values.` |
| `json_syntax`, invalid constant | empty root path | `JSON contains an invalid numeric constant.` |
| `json_syntax`, other known position | empty root path | `JSON syntax error at character {position}.` |
| `json_syntax`, no position | empty root path | `Output is not one complete strict JSON value.` |
| `wrong_top_level_type` | empty root path | `Expected object at root; observed {observed}.` |
| `missing_field` | missing property path | `Required field is missing.` |
| `unexpected_field` | extra property path | `Field is not permitted.` |
| `wrong_field_type` | failing value path | `Expected {expected}; observed {observed}.` |
| `ingredient_count` | `/ingredients` | `Expected 3–8 items; observed {count}.` |
| `method_count` | `/method` | `Expected 2–5 items; observed {count}.` |
| `null_value` | null value path | `Null is not permitted.` |
| `blank_string` | blank value path | `String must contain a non-whitespace character.` |
| `non_positive_amount` | amount path | `Amount must be greater than zero.` |

When a recognized fence body is not strict JSON, its `json_syntax` diagnostic uses the same template selection with positions relative to the body. Duplicate diagnostics are ordered by their full escaped pointer path; repeated duplicate occurrences may therefore have identical diagnostic records and are retained.

## Acceptance tests

Implementation is accepted only when all of the following pass locally without a model or GPU.

### Valid cases

- The canonical behavioural-contract example passes.
- Reordered object fields pass.
- Ingredient counts 3 and 8 pass.
- Method counts 2 and 5 pass.
- Positive integer and fractional amounts pass.
- Unusual non-blank units pass.
- JSON leading and trailing whitespace passes.

### Parser cases

- A valid object in a Markdown fence fails with `markdown_fence`.
- Leading or trailing prose around a valid object fails with `surrounding_text`.
- Duplicate keys fail at the top and ingredient levels.
- Empty, malformed, `NaN`, and infinity inputs fail.
- Multiple JSON values fail.
- Both `{} 1` and `1 {}` receive `json_syntax`, not `surrounding_text`.
- An integer longer than Python's configured integer-string conversion limit remains valid JSON.
- A syntactically valid finite number whose exponent exceeds `Decimal`'s supported exponent range remains valid JSON.
- Valid scalar, array, and `null` inputs parse but fail the response schema.
- Prose around the complete canonical nested ChatG&T object receives `surrounding_text` rather than being made ambiguous by nested arrays or objects.
- A malformed outer object containing one valid nested array receives `json_syntax`, not `surrounding_text`.
- Valid fenced JSON receives only `markdown_fence`; a fenced complete object with a duplicate key receives `markdown_fence` plus `duplicate_key`; any other invalid fence body receives `markdown_fence` plus `json_syntax` and never `surrounding_text`.
- Unlabelled and labelled fences, optional permitted info-string spacing, LF and CRLF, and permitted outer/trailing whitespace match the exact fence grammar.
- Bare-CR endings, four-backtick delimiters, closing indentation, multi-token info strings, same-line closers, and trailing non-whitespace do not receive `markdown_fence`; when they contain one eligible valid object, they receive `surrounding_text`.

### Schema cases

- Missing and unexpected fields fail at both closed-object levels.
- Wrong response-field, array-item, ingredient, and ingredient-field types fail.
- Ingredient counts 2 and 9 fail.
- Method counts 1 and 6 fail.
- Null values fail without a duplicate type label at the same path.
- Empty and whitespace-only strings fail.
- Zero and negative amounts fail.
- Boolean amounts fail as the wrong type.
- Numeric strings are not coerced.

### Failure and evidence cases

- Labels are deduplicated and canonically ordered.
- Independent failures retain multiple diagnostics.
- Cascade suppression follows this specification.
- Diagnostic JSON Pointers identify the correct paths.
- Duplicate keys in nested ingredient objects identify their complete escaped property paths.
- Every diagnostic uses the exact frozen template for its condition.
- A same-`$id` schema containing any added, removed, or changed keyword fails at load time before output evaluation.
- Fenced JSON remains invalid even when its inner content is schema-valid.
- The same inputs produce equal records and byte-equivalent canonical serialization.
- A raw-output change changes `raw_output_sha256`.
- A schema-byte change changes `response_schema_sha256`.
- The result round-trips through JSON without information loss.
- Unexpected and duplicate keys written as escaped lone surrogates serialize to valid UTF-8 using lowercase `\uXXXX` escapes and round-trip without information loss.
- The result contains no unknown or missing fields.

## Completion condition

Step 8 is complete when:

1. the exact schema exists and passes its Draft 2020-12 meta-schema check;
2. `jsonschema==4.26.0` is directly pinned and the lock remains reproducible;
3. the strict parser, label mapper, deterministic result, and canonical serializer implement this specification;
4. every acceptance test passes; and
5. the implementation and check result are documented.

Running a model, changing prompts, repairing saved outputs, or evaluating qualitative quality is outside Step 8.
