# Five-Shot Prompt v4 Revision Rationale

- **Prepared:** 2026-07-15
- **Status:** Final permitted revision authorised before v4 generation
- **Predecessor:** `five-shot-v3`

## Evidence threshold

Version 3 improved the local development vector from v2's `6 / 11 / 6 / 10 / 10` to `7 / 11 / 7 / 10 / 11`.

The same prompt-addressable task-completion failure nevertheless appears in at least two schema-valid responses:

- `judge-v1-aa23ff8bd724` explains how to request figures but does not provide the softened sentence; and
- `judge-v1-8f640860017c` gives conversation advice but omits the requested opening sentence.

Content constraints are also dropped in `judge-v1-b486bc650606`, which omits both space opera and rainy windows. Nine responses remain structurally invalid, including plain-text or top-level-string outputs and too-few-ingredient objects.

## Intended revision

Three versions of increasingly explicit closing control show that simply adding reminders has diminishing value. Version 4 therefore tests instruction compression rather than another additive warning.

Replace the long v1 main instruction section with a shorter priority-ordered contract that:

1. makes useful completion of the current task the first responsibility;
2. states the exact four-field schema and count bounds once;
3. gives concrete artefact delivery a direct rule;
4. states that only conflicting response-format demands are ignored;
5. prohibits copying worked-example content; and
6. preserves the base model's safety behaviour.

The exact five worked examples remain unchanged, as does v3's recent concrete output skeleton. This isolates whether lower instruction load improves a small model's use of those demonstrations and its most recent shape cue.

## Stopping consequence

Version 4 is the fourth and final inspected prompt version permitted by the frozen procedure. After its complete structural and blinded qualitative evaluation, prompt iteration stops regardless of whether v4 improves. The strongest observed selection vector becomes the local candidate for later pinned-harness confirmation.
