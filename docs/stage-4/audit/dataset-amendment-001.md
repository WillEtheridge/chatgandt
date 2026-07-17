# Dataset Amendment 001

- **Date:** 2026-07-16
- **Active dataset identity:** `chatgnt-dataset-v1.1`
- **Manifest:** `data/dataset-v1/amendments/amendment-001/manifest.json`
- **Status:** Applied and audited; followed by amendment 002 before freeze

## Why the amendment exists

The proportionate Stage 4 audit found five supervised examples too close to spent development prompts and two internal lessons that were too reusable with surface changes. Their existing acceptance events bind their existing content, so editing those JSONL lines would make the recorded history false.

Amendment 001 therefore uses a narrow supersession overlay. The original 200 examples and 784 events remain untouched. Seven new examples have new IDs and their own draft, project-master review, and automated acceptance events. The manifest maps each old ID to one new ID and states why.

## Validation rules

The audit executable verifies rather than trusts the overlay:

- base candidate and event collection identities match the original production summary;
- replacement file identities match the amendment manifest;
- all seven replacements pass the existing supervised-example and lifecycle contracts;
- every old and new ID appears exactly once in the mapping;
- intent family, coverage slice, input form, complexity, constraint status, robustness role, and task subtype remain unchanged across each mapping; and
- removing the seven superseded records and adding the seven replacements yields exactly 200 accepted active records with no unresolved or rejected active record.

The seven replacements were authored and reviewed in separate deliberate passes within the same Codex project-master session. This is attributable project review, not an independent human evaluation or a claim of independent model contexts.

## Result

The same bounded audit passed on the active v1.1 set. The subsequent frozen-dataset validator revealed that two superseded records had also carried the corpus's only seven- and eight-ingredient responses. Amendment 002 corrected that overlooked diversity invariant without changing their scenarios. Original records and v1.1 remain historical evidence; downstream work uses active v1.2.
