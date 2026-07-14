# Schema Validation Implementation Check

Step 8 was implemented locally on 2026-07-14 against frozen [schema-validation specification 1.3](schema-validation-specification.md). No model or GPU was used.

## Implemented boundary

- `schemas/chatgnt-response-v1.schema.json` contains the complete normative Draft 2020-12 schema. Its exact-byte SHA-256 is `107f6f93ed77c1a1c057af78e832ab178f817192b90deb8ca333af458591953d`.
- `chatgnt/validation.py` provides fail-fast exact schema loading, lossless response parsing, stable RFC 6901 diagnostics, deterministic closed results, and surrogate-safe canonical UTF-8 serialization.
- `jsonschema==4.26.0` is a direct exact dependency and `uv.lock` resolves 83 packages consistently.

## Checks

From the repository root:

```bash
.venv/bin/python -m compileall -q chatgnt tests scripts
.venv/bin/python scripts/verify_environment.py
.venv/bin/python -m unittest -v tests.test_validation
.venv/bin/python -m unittest discover -s tests -v
uv lock --check --offline
git diff --check
```

Results:

- compilation passed;
- the machine-readable environment report identified `jsonschema` at the exact direct pin `4.26.0`;
- all 33 focused schema-validation tests passed;
- all 73 project tests passed;
- the frozen lock check passed and resolved 83 packages; and
- the diff whitespace check passed.

The focused suite covers every frozen acceptance category, including exact-schema rejection, classification precedence, pair-preserving nested duplicate detection, unbounded number lexemes, cascade suppression, canonical label and diagnostic ordering, evidence hashes, and lone-surrogate serialization.
