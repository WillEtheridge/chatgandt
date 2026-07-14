# Prompt-Development Set Check

- **Date:** 2026-07-14
- **Result:** Pass
- **Model generation performed:** No

## Accepted artefact

The frozen development workbench is [`data/development/prompts-v1.jsonl`](../data/development/prompts-v1.jsonl).

- Version: 1
- Records: 20
- SHA-256: `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1`
- Intent families: 5
- Roles per family: clean, naturalistic, constrained, and robustness
- Family/role combinations: all 20 present exactly once

## Review performed

The exact wording was checked against the frozen scenario blueprint before any model saw the prompts. The set contains ordinary questions, requests, commands, statements, fragments, quoted text, code, braces, and backslashes. Each task is low-stakes, single-turn, answerable from stable general knowledge, and has a recognisable underlying objective.

Clean prompts provide ordinary use cases. Naturalistic prompts require intent inference. Constrained prompts contain meaningful requirements. Robustness prompts retain a legitimate task while directly conflicting with ChatG&T's required response format.

The set contains no ideal responses. Its prompts and close paraphrases remain excluded from fine-tuning training and validation data, the five system-prompt examples, and held-out evaluation.

## Automated contract

`chatgnt.development.validate_development_prompts` checks:

- the exact 20-record count;
- a closed metadata schema and controlled vocabularies;
- canonical, unique prompt identifiers;
- exactly one of every family/role pair;
- known, unique, sorted challenge tags;
- canonical UTF-8 JSON Lines serialization; and
- identity with the frozen version 1 SHA-256 digest.

Run the check with:

```bash
uv run --frozen python scripts/verify_development_prompts.py
```

The dedicated acceptance tests cover the committed artefact, closed metadata and identifier rules, unknown challenge tags, and non-canonical serialization.

Verification results:

- prompt-development verifier: pass;
- dedicated acceptance tests: 3/3 pass; and
- complete regression suite: 76/76 pass.

## Evidence boundary

This acceptance establishes the identity and composition of the engineering workbench. It makes no claim about model quality, system-prompt quality, or generalisation. System A has not yet been run on these inputs, so the set was frozen without inspecting development outputs.
