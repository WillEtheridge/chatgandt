# Five-Shot Worked-Examples Check

- **Date:** 2026-07-14
- **Result:** Pass
- **Experimental model generation performed:** No

## Accepted artefact

- Path: [`data/prompt-engineering/worked-examples-v1.json`](../data/prompt-engineering/worked-examples-v1.json)
- SHA-256: `0cb6afd2bf88ed1f9a3edf8e5ffc479e22c69b91ea7220988c5b1dee51f429b6`
- Worked examples: 5
- Intent families represented: 5/5 exactly once
- Role allocation: clean, constrained, naturalistic, robustness, constrained
- Exact development-prompt overlap: 0
- Schema-valid ideal responses: 5/5

## Automated contract

`chatgnt.development.validate_worked_examples` verifies the closed file and record shapes, exact family-role allocation, stable identifiers, unique trimmed inputs, complete family coverage, exact development-prompt separation, response-schema validity, and identity with the frozen artefact digest.

Run the check with:

```bash
uv run --frozen python scripts/verify_worked_examples.py
```

Verification results:

- worked-example verifier: pass;
- combined development-artefact acceptance tests: 6/6 pass; and
- complete regression suite: 79/79 pass.

Close-paraphrase separation and qualitative quality are authoring judgments rather than claims made by the automated check.

## Evidence boundary

This check accepts the content selected to teach the prompt-only baseline. It does not accept the complete system prompt, which has not yet been written, or make any claim about model behaviour. No experimental model saw the development prompts or worked examples during this activity.
