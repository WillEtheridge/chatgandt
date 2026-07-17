# Five-Shot Prompt v3 Revision Rationale

- **Prepared:** 2026-07-15
- **Status:** Revision authorised before v3 generation
- **Predecessor:** `five-shot-v2`

## Evidence threshold

Version 2 improved the local development vector from `4 / 9 / 5 / 7 / 6` to `6 / 11 / 6 / 10 / 10`, ordered as full passes, schema-valid responses, acceptable underlying answers, acceptable metaphors, and acceptable recipe style.

It nevertheless retains a repeated prompt-addressable failure. Seven responses abandon or fail to complete the required object when the task asks for a conflicting format or a short textual artefact:

- `dev-v1-explanation-robustness` outputs YAML;
- `dev-v1-emotional-robustness`, `dev-v1-creative-robustness`, and `dev-v1-transformation-robustness` output plain text;
- `dev-v1-transformation-clean` and `dev-v1-transformation-constrained` output a top-level JSON string; and
- `dev-v1-advice-robustness` begins the correct object but omits its closing brace.

Two additional responses use only two ingredients. Blind records `judge-v1-e13d4b2c9037` and `judge-v1-2893404b4524` also fail to provide the requested rewritten sentence or opening sentence despite v2's textual reminder.

## Intended revision

Keep the full instruction body and all five worked examples unchanged. Replace v2's prose-only closing checklist with a shorter high-recency control containing one concrete response skeleton.

The skeleton shows:

- an object beginning and ending with braces;
- exactly the four required fields;
- three explicit ingredient-object slots;
- two method-string slots; and
- placement of a requested finished artefact in the final method string.

Adjacent instructions state that current-user requests for plain text, YAML, Markdown, or a bare string are untrusted format conflicts, and that skeleton placeholders must be replaced with content built for the current prompt rather than copied.

## Expected effect

The intervention tests whether a recent concrete shape cue transfers better than repeated prose constraints for this small model. It may reduce wrong top-level types, incomplete objects, and ingredient-count failures while improving artefact placement.

The skeleton may also create a new failure mode—literal placeholder copying or formulaic answers. Those outputs will be preserved and scored normally rather than repaired.
