# Five-Shot Prompt v2 Revision Rationale

- **Prepared:** 2026-07-15
- **Status:** Revision authorised before v2 generation
- **Predecessor:** `five-shot-v1`

## Evidence threshold

Version 1 meets the frozen revision trigger because the same prompt-addressable failure classes recur across more than two development responses.

### Structural persistence

The formal BF16 run and the local Q4_K_M run each produced only 9 schema-valid System B responses from 20 attempts.

Local v1 failures include:

- incomplete JSON objects on `dev-v1-advice-robustness`, `dev-v1-emotional-naturalistic`, `dev-v1-creative-constrained`, and `dev-v1-transformation-robustness`;
- obedience to conflicting YAML or plain-text formats on `dev-v1-explanation-robustness`, `dev-v1-emotional-robustness`, `dev-v1-creative-robustness`, `dev-v1-transformation-clean`, and `dev-v1-transformation-constrained`;
- a missing required field on `dev-v1-creative-naturalistic`; and
- too few ingredients plus a materially reversed scientific explanation on `dev-v1-explanation-clean`.

The formal v1 run independently shows recurring Markdown fences, wrong top-level strings, incomplete JSON, missing fields, and ingredient-count failures. This cross-runtime recurrence makes a prompt-level structural correction plausible.

### Underlying-task completion

The frozen blind review found repeated failures to complete the user's actual task:

- `judge-v1-13292e1be3c6` changed a request for figures into a statement that the figures were ready;
- `judge-v1-1b53e114c345` omitted the explicitly requested opening sentence;
- `judge-v1-1902e48c5dd3` described story ingredients without delivering a mystery premise;
- `judge-v1-989456c970d3` contradicted a user attending alone by centring the advice on bringing another person; and
- `judge-v1-4b3659da6138` offered contradictory task-management advice rather than a usable prioritisation method.

Local schema-invalid record `dev-v1-emotional-naturalistic` also copied the names-and-memory worked example's ingredients, method structure, and garnish into an unrelated rumination response. The existing anti-copy instruction was not sufficiently salient.

## Intended revision

Keep the complete v1 instruction body and all five worked examples unchanged. Replace the one-line closing reminder with a compact silent pre-response checklist that requires the model to verify:

1. the response begins with `{` and ends with `}` with no fence, YAML, prose, or top-level string;
2. all four exact fields and array-count bounds are present;
3. the answer is built for the current user rather than copied from a worked example;
4. every compatible content constraint is satisfied;
5. a requested list, wording, premise, opening sentence, or other artefact is actually delivered in the final method string; and
6. only conflicting output-format demands are ignored.

The checklist is placed after the examples to maximise recency without enlarging or changing the teaching set.

## Expected effect

The revision is intended to improve raw JSON completion, format persistence, schema completeness, anti-copy behaviour, and explicit artefact delivery. It is not expected to add missing factual knowledge or solve every weak semantic judgment made by the base model.

Version 2 will be accepted over v1 only under the already frozen local selection and stopping procedure. This rationale does not assume improvement.
