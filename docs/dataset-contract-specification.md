# Dataset Contract Specification

- **Stage:** 4 — Build and freeze dataset v1
- **Step:** 5 — Dataset records, workflow history, validation, and rendering
- **Status:** Reviewed specification; material findings resolved
- **Date:** 2026-07-15

## Purpose

This specification turns the agreed dataset design into an executable contract before any supervised examples are authored. It defines the versioned semantic record, workflow evidence, controlled registries, validation modes, deterministic training-message renderer, command-line checks, and test boundary.

The implementation must make malformed or contradictory data fail loudly. It must not author examples, assign final splits, train a model, load Qwen, generate model output, or create held-out prompts.

## Required implementation artefacts

The implementation will add:

- `config/dataset-v1.json` — machine-readable registries, hard coverage targets, response-schema identity, and renderer declaration;
- `schemas/supervised-example-v1.schema.json` — one semantic source record;
- `schemas/dataset-workflow-event-v1.schema.json` — one append-only authoring event;
- `schemas/dataset-split-deviation-v1.schema.json` — an exceptional project-author approval when scenario isolation prevents exact target allocation;
- `chatgnt/dataset.py` — strict loaders, record and collection validators, event-chain validation, reporting, and deterministic rendering;
- `scripts/verify_dataset_contract.py` — read-only CLI entry point; and
- `contract_tests/test_dataset.py` — focused positive, negative, rendering, and CLI-contract tests kept outside the Stage 3-frozen `tests/test_*.py` identity set.

No candidate, training, validation, pilot, or held-out data will be created by this step.

## Existing normative dependencies

The implementation must reuse rather than redefine:

- `schemas/chatgnt-response-v1.schema.json` for `assistant_response`;
- `chatgnt.records.strict_json_loads` for duplicate-key and non-finite-number rejection;
- `chatgnt.records.canonical_json` and `canonical_line` for record identity and canonical JSONL;
- the five intent-family identifiers already used by the evaluation protocol;
- the input-form, complexity-source, and robustness-role values already used by `schemas/heldout-prompt-v1.schema.json`; and
- `config/model.toml` as the identity of the pinned Qwen model and chat template, without loading either during this step.

The dataset contract may be stricter than the response schema through cross-field or collection rules, but it may not weaken the frozen response schema.

## Source collections and lifecycle

The eventual Stage 4 dataset directory will contain these logical collections:

1. `candidates.jsonl` — the latest semantic snapshot of every drafted candidate, including rejected candidates;
2. `workflow-events.jsonl` — the complete append-only event history for those candidates;
3. `train.jsonl` — a derived canonical export of accepted records assigned to training;
4. `validation.jsonl` — a derived canonical export of accepted records assigned to validation; and
5. `pilot.jsonl` — a derived canonical export of accepted training records marked as pilot members.

The contract implementation validates such paths when supplied but does not create this directory or these files. Candidate snapshots remain the semantic source of truth. Train, validation, and pilot exports must be byte-for-byte canonical projections of the accepted candidate snapshots rather than independently edited copies.

Rejected candidate snapshots retain `split: null` and `pilot_member: false`. An accepted frozen snapshot has a non-null split. Acceptance status is derived only from the terminal workflow event; it is not duplicated in the semantic record.

## Supervised example schema

Every source record contains exactly these top-level fields:

```json
{
  "record_schema_version": 1,
  "example_id": "dataset-v1-001",
  "scenario_id": "scenario-career-interview-preparation",
  "user_prompt": "Help me prepare for a job interview.",
  "assistant_response": {
    "title": "The Confident Candidate",
    "ingredients": [
      {"amount": 50, "unit": "ml", "name": "role-specific preparation"},
      {"amount": 30, "unit": "ml", "name": "evidence from past experience"},
      {"amount": 2, "unit": "dashes", "name": "calm curiosity"}
    ],
    "method": [
      "Research the role and identify the abilities the interviewer is likely to explore.",
      "Prepare three concise examples showing the situation, your actions, and the result."
    ],
    "garnish": "A thoughtful question about the team."
  },
  "metadata": {
    "intent_family": "advice_decision_support",
    "coverage_slice": "target_use",
    "input_form": "direct_request_or_command",
    "complexity": "standard",
    "complexity_sources": [],
    "constraint_bearing": false,
    "robustness_role": null,
    "topic": "career_and_work",
    "task_subtype": "preparation",
    "user_goal": "prepare effectively for a job interview",
    "requested_task_or_artefact": "an actionable preparation plan",
    "scenario_summary": "A person wants general help preparing for an upcoming job interview.",
    "important_constraints": []
  },
  "provenance": {
    "authoring_batch_id": "dataset-v1-batch-01",
    "initial_draft_source": "frontier_model",
    "initial_draft_model_id": "recorded-model-identity",
    "model_revision_used": false,
    "material_human_edit": false
  },
  "split": null,
  "pilot_member": false
}
```

### Identity and text rules

- `record_schema_version` is the JSON integer `1`, not a boolean or quoted value.
- `example_id` matches `^dataset-v1-[0-9]{3}$` and remains stable from first draft through terminal disposition. Gaps caused by rejection are allowed.
- `scenario_id` matches `^scenario-[a-z0-9]+(?:-[a-z0-9]+)*$`.
- User prompts and explanatory metadata are non-empty, contain at least one non-whitespace character, and have no leading or trailing whitespace.
- `important_constraints` contains unique, trimmed, non-empty strings in authored priority order. It is not alphabetically sorted by the validator.
- Each record is a JSON-compatible object with no duplicate keys, byte-order mark, non-finite number, or unexpected property.

### Response rule

`assistant_response` references `chatgnt-response-v1.schema.json`. It therefore contains exactly `title`, `ingredients`, `method`, and `garnish`; three to eight ingredients; two to five method strings; and only positive numeric ingredient amounts. String trimming beyond non-whitespace validity is enforced by the dataset validator so authored targets cannot begin or end with accidental whitespace.

### Closed metadata values

The five intent families are:

- `advice_decision_support`;
- `explanation_technical_understanding`;
- `low_stakes_emotional_support`;
- `creative_generation`; and
- `short_form_transformation`.

Coverage slice is one of `target_use`, `breadth`, or `robustness`.

Input form is one of `question`, `direct_request_or_command`, or `statement_or_fragment`.

Complexity is `standard` or `composed`. Complexity sources are unique values selected from:

- `ordinary_content_constraint`;
- `supplied_content`;
- `multiple_outcomes`;
- `competing_considerations`;
- `connected_steps`; and
- `robustness_pressure`.

Robustness role is null or one of `format_pressure`, `behaviour_pressure`, or `serialization_pressure`.

The exact 20 topics and the eight task subtypes per family are those frozen in D-048 and repeated in `config/dataset-v1.json`. JSON Schema admits the union of all task-subtype strings; executable validation enforces that the selected subtype belongs to the selected intent family.

### Provenance values

- `authoring_batch_id` matches `^dataset-v1-batch-[0-9]{2}$`.
- `initial_draft_source` is `human` or `frontier_model`.
- `initial_draft_model_id` is null for a human initial draft and a trimmed non-empty string for a frontier-model initial draft.
- `model_revision_used` and `material_human_edit` are JSON booleans.
- The pinned Qwen model ID and an exact case-insensitive match of its final path component are prohibited model-assistance identities. The same gate applies to initial drafting and every frontier-model workflow event. This automated check supports, but does not replace, the later source-use audit.

### Record cross-field invariants

JSON Schema should express straightforward conditional rules, and Python validation must enforce all rules with stable, specific failure messages:

1. `coverage_slice: robustness` requires composed complexity, a non-null robustness role, and `robustness_pressure` in `complexity_sources`.
2. A non-robustness record has a null robustness role and does not contain `robustness_pressure`.
3. Standard complexity has an empty complexity-source list, `constraint_bearing: false`, and an empty important-constraints list.
4. Composed complexity has at least one complexity source.
5. A constraint-bearing record is composed, contains `ordinary_content_constraint`, and has at least one important constraint.
6. A non-constraint-bearing record does not contain `ordinary_content_constraint` and has no important constraints.
7. The task subtype belongs to the selected intent family.
8. `pilot_member: true` requires `split: train`.
9. A human initial draft has no initial model ID; a frontier-model initial draft has one.

Authoring mode permits any of the three split states: null, train, or validation. Freeze-mode lifecycle rules further constrain split state according to terminal disposition.

## Workflow event schema

Workflow history is append-only and separate from semantic content. Every event contains exactly:

```json
{
  "record_schema_version": 1,
  "event_id": "dataset-event-v1-0001",
  "example_id": "dataset-v1-001",
  "prior_event_id": null,
  "event_type": "draft_created",
  "content_sha256": "64-lowercase-hex-digest",
  "actor_type": "frontier_model",
  "actor_identity": "recorded-agent-identity",
  "model_id": "recorded-model-identity",
  "recorded_at_utc": "2026-07-15T18:00:00Z",
  "outcome": "created",
  "reason_codes": [],
  "notes": "Initial batch draft."
}
```

### Event values

- `event_id` matches `^dataset-event-v1-[0-9]{4}$` and is globally unique.
- `example_id` follows the supervised-example rule.
- `prior_event_id` is null only for `draft_created`; otherwise it identifies the immediately preceding event for the same example.
- `event_type` is one of `draft_created`, `model_revision`, `human_edit`, `quality_review`, `accepted`, or `rejected`.
- `content_sha256` is the SHA-256 of `canonical_json` applied to the semantic snapshot after removing only the top-level `split` and `pilot_member` fields. It identifies authored supervision, metadata, and provenance without making later allocation look like a content revision. Complete record and export identities, including split and pilot state, are bound separately by freeze reports and the later dataset manifest.
- `actor_type` is `human`, `frontier_model`, or `automated_validator`.
- `actor_identity` is a trimmed non-empty string.
- `model_id` is a trimmed non-empty string only when `actor_type` is `frontier_model`; otherwise it is null.
- `recorded_at_utc` is an RFC 3339 UTC timestamp ending in `Z`.
- `outcome` is one of `created`, `revised`, `pass`, `revision_requested`, `rejection_recommended`, `accepted`, or `rejected`.
- `reason_codes` is a unique array drawn from the versioned registry below.
- `notes` is a trimmed string and may be empty only when the event has no reason codes.

The version 1 reason-code registry is:

- `schema_invalid`;
- `cross_field_invalid`;
- `unclear_underlying_task`;
- `underlying_answer_not_useful`;
- `factual_or_language_error`;
- `metaphor_incoherent`;
- `recipe_execution_weak`;
- `method_not_procedural`;
- `requested_artefact_incomplete`;
- `compatible_constraint_missed`;
- `safety_or_scope_concern`;
- `duplicate_or_near_duplicate`;
- `scenario_collision`;
- `withheld_domain_violation`;
- `coverage_mismatch`;
- `response_templating`; and
- `provenance_invalid`.

There is no `other` reason. A missing legitimate reason requires a documented registry revision before dataset freeze.

### Event-type invariants

1. `draft_created` has no prior event, has outcome `created`, and is performed by a human or frontier model.
2. `model_revision` has outcome `revised` and is performed by a frontier model.
3. `human_edit` has outcome `revised` and is performed by a human.
4. `quality_review` is performed by a human or frontier model and has outcome `pass`, `revision_requested`, or `rejection_recommended`.
5. `accepted` has outcome `accepted`, is performed by a human, has no reason codes, and immediately follows a passing quality review of the same snapshot.
6. `rejected` has outcome `rejected`, may be performed by a human or automated validator, and has at least one reason code.
7. Created, revised, passing, and accepted events have no reason codes. Revision requests, rejection recommendations, and rejections have at least one reason code and non-empty notes.
8. An event after a terminal accepted or rejected event is invalid.
9. Events for one example form exactly one linear chain in file order; forks, missing predecessors, cross-example predecessors, cycles, and time reversal are invalid.
10. A revision event must change `content_sha256` from its predecessor. A review or terminal event must preserve its predecessor's digest.
11. The first event digest matches the initial candidate content only when that content has never been revised. In general, the last event digest must match the latest candidate content identity.
12. Provenance summary agrees with the chain: the initial actor agrees with initial draft source and model ID; `model_revision_used` is true exactly when a model-revision event exists; and `material_human_edit` is true exactly when a human-edit event exists.
13. Every frontier-model event applies the prohibited drafting-model identity gate. The pinned Qwen model may not draft, revise, review, or otherwise influence target selection.

Reason codes describe review and disposition rather than silent content mutation. A revised semantic record therefore needs a new revision event and a new quality review before acceptance.

## Split-deviation schema

This record exists only when an otherwise valid frozen allocation differs from the 160/40 total or 32/8/8 per-family targets because scenario groups are indivisible. It contains exactly:

```json
{
  "record_schema_version": 1,
  "deviation_id": "dataset-split-deviation-v1",
  "dataset_contract_id": "chatgnt-dataset-v1",
  "candidates_sha256": "64-lowercase-hex-digest",
  "train_sha256": "64-lowercase-hex-digest",
  "validation_sha256": "64-lowercase-hex-digest",
  "pilot_sha256": "64-lowercase-hex-digest",
  "expected_counts": {
    "train": 160,
    "validation": 40,
    "pilot": 40,
    "per_intent_family": {
      "advice_decision_support": {"train": 32, "validation": 8, "pilot": 8},
      "explanation_technical_understanding": {"train": 32, "validation": 8, "pilot": 8},
      "low_stakes_emotional_support": {"train": 32, "validation": 8, "pilot": 8},
      "creative_generation": {"train": 32, "validation": 8, "pilot": 8},
      "short_form_transformation": {"train": 32, "validation": 8, "pilot": 8}
    }
  },
  "achieved_counts": {
    "train": 159,
    "validation": 41,
    "pilot": 40,
    "per_intent_family": {
      "advice_decision_support": {"train": 31, "validation": 9, "pilot": 8},
      "explanation_technical_understanding": {"train": 32, "validation": 8, "pilot": 8},
      "low_stakes_emotional_support": {"train": 32, "validation": 8, "pilot": 8},
      "creative_generation": {"train": 32, "validation": 8, "pilot": 8},
      "short_form_transformation": {"train": 32, "validation": 8, "pilot": 8}
    }
  },
  "reason": "scenario_group_indivisibility",
  "affected_scenario_ids": ["scenario-example-group"],
  "rationale": "The indivisible scenario group prevents the exact family allocation without crossing splits.",
  "approved_by": "project-author-identity",
  "approved_at_utc": "2026-07-15T20:00:00Z"
}
```

The four digests bind the exact canonical source and projections being approved. Expected counts must equal the contract configuration; achieved counts and file digests are recomputed rather than trusted. Scenario IDs are unique, sorted, present in the candidate collection, and non-empty. Rationale and approver are trimmed non-empty strings, and approval time is an RFC 3339 UTC timestamp ending in `Z`.

## Strict JSONL rules

All collection loaders must:

- read UTF-8 without a byte-order mark;
- reject invalid UTF-8, blank lines, duplicate object keys, non-object lines, and non-finite numbers;
- require exactly one JSON object per LF-terminated line;
- reject CRLF line endings;
- require every line to equal `canonical_line(parsed_value)`; and
- report the path and one-based line number on failure.

Canonical JSONL sorts object keys for stable record identity. This storage ordering is independent of assistant-target field ordering.

Normalized user-prompt identity reuses `chatgnt.evaluation_protocol.normalize_text`: Unicode NFC; CRLF and CR converted to LF; Unicode-aware case folding; every whitespace run collapsed to one ASCII space; and outer whitespace removed, with punctuation preserved.

## Deterministic assistant and message rendering

The lifecycle-gated training renderer accepts one validated supervised example plus its complete validated workflow chain and returns a new three-message list only when the terminal event is `accepted` and its content digest matches the example:

```json
[
  {"role": "system", "content": ""},
  {"role": "user", "content": "the exact user_prompt"},
  {"role": "assistant", "content": "one compact JSON object"}
]
```

The assistant string is rendered with UTF-8 characters unescaped, no insignificant whitespace, finite JSON numbers, and these explicit field orders:

- top level: `title`, `ingredients`, `method`, `garnish`;
- each ingredient: `amount`, `unit`, `name`.

The renderer reconstructs objects in that order rather than relying on source-key order and does **not** use the repository's sort-key canonical JSON for the assistant target. The semantic value must round-trip through strict JSON and equal the stored response object.

The renderer never includes IDs, metadata, provenance, split, pilot state, or workflow history. It does not add five-shot examples. It does not apply the tokenizer chat template in Step 5. Stage 6 will pass these exact messages to the pinned tokenizer's `apply_chat_template`; the dataset manifest will bind the dataset renderer implementation and the already-pinned chat-template digest.

`render_assistant_target` is a deliberately pure semantic serializer used to establish the exact target string. It does not claim that a record is accepted. The public `render_training_messages` function validates the supplied record and workflow chain before calling that serializer. Rendering is permitted for accepted training or validation records when explicitly requested by later pipeline code. A rejected or unresolved candidate cannot be rendered as supervision. Pilot output is selected only from accepted training records with `pilot_member: true`.

## Validation modes

### Contract mode

Contract mode requires no dataset files. It validates:

- both new JSON Schemas against Draft 2020-12;
- the existing response-schema reference;
- exact agreement between schema enums and `config/dataset-v1.json`;
- exact agreement between task-subtype family mappings and the registry;
- hard-target arithmetic, including 200 total examples, five families of 40, and internally consistent crossed quotas;
- pinned response-schema path and model/chat-template identities; and
- a built-in minimal semantic fixture, workflow chain, and assistant rendering expectation.

This is the completion proof for Step 5 before data exists.

### Authoring mode

Authoring mode accepts candidate and workflow-event JSONL paths and validates:

- strict canonical JSONL;
- every record and event schema;
- record cross-field invariants;
- unique example, event, and user-prompt identities;
- complete linear event chains for all supplied candidate snapshots;
- latest-event digest and provenance-summary agreement;
- no event references an absent candidate; and
- lifecycle consistency without requiring terminal disposition, final counts, or assigned splits.

Authoring mode reports current candidate, accepted, rejected, unresolved, family, slice, input-form, complexity, constraint, robustness-role, topic, subtype, split, and pilot counts. Intermediate imbalance is information, not failure.

### Freeze mode

Freeze mode accepts candidates, events, train, validation, and pilot JSONL paths. It performs every authoring check and additionally requires:

- exactly 200 terminally accepted candidates and zero unresolved candidates; every other candidate has exactly one terminal rejection;
- every accepted candidate assigned to train or validation and every rejected candidate left unassigned;
- target allocation of 160 accepted training records and 40 accepted validation records;
- exactly 40 pilot records, all drawn from training;
- each family totals 40 accepted records, targeting 32 training, eight validation, and eight pilot members;
- within each family: 28/6/6 target-use, breadth, and robustness; 10/20/10 questions, requests, and statements; 24/16 standard and composed; 12 constraint-bearing; and two of each robustness role;
- all three input forms, both complexities, all slices, at least one compatible constraint, and all robustness roles represented in validation;
- at least 12 topics overall and eight within each family, with no topic above 20 accepted records;
- at least six task subtypes in each family, with no subtype above 10 records in that family;
- every ingredient count from three through eight represented at least once;
- no scenario ID split across train and validation;
- no duplicate normalized user prompt;
- terminal acceptance immediately following a passing review of the frozen snapshot;
- exact canonical projection equality for train, validation, and pilot exports, each ordered by ascending `example_id`; and
- a report of token-independent response-diversity distributions and any ingredient-count concentration above 67 examples as a review warning, not an automatic failure.

Exact 160/40 and family-level allocation passes without an exception artefact. If indivisible scenario groups prevent exact target allocation, freeze mode additionally requires a valid `dataset-split-deviation-v1` record. That record binds the contract ID, complete candidate and allocation identities, expected and achieved total and per-family counts, affected scenario IDs, a non-empty scenario-isolation rationale, project-author identity, and UTC approval time. The validator recomputes all achieved counts, requires every listed affected scenario to exist, and still enforces scenario isolation, 200 accepted records, 40 per family, and exactly 40 pilot members. The exception cannot waive any content, lifecycle, coverage, topic, subtype, response, or pilot-eligibility rule.

A split-deviation record is an attributable approval of a visible trade-off, not proof that a mathematical optimum was reached. Step 6's split-assignment procedure must attempt the exact targets first and record its algorithm and achieved deviation. Stage 4 readiness decides whether a reported non-exact allocation remains acceptably small; it may not silently reinterpret an arbitrary split as equivalent to 160/40.

Freeze mode does not attempt semantic duplicate detection, factual verification, qualitative scoring, withheld-domain text classification, or token counting. Those belong to later Stage 4 audits and the tokenizer-aware freeze procedure.

## Configuration contract

`config/dataset-v1.json` contains exactly:

- `schema_version` and `dataset_contract_id`;
- relative paths for the response and new record schemas, including the conditional split-deviation schema;
- the pinned base-model ID, revision, and chat-template SHA-256 copied from `config/model.toml`;
- the renderer ID and ordered response/ingredient keys;
- intent families, coverage slices, input forms, complexities, complexity sources, robustness roles, topics, task subtypes by family, draft sources, event types, actor types, event outcomes, and reason codes;
- prohibited model-assistance IDs applied to every frontier-model workflow event;
- accepted-set, split, pilot, family, crossed-quota, topic, subtype, ingredient-count, and validation-coverage targets; and
- the three withheld domains as audit exclusions.

The file is configuration, not an alternative source of normative prose. Tests and contract-mode validation ensure it matches this specification and the JSON Schemas. It must use canonical JSON plus one terminal LF.

## Public Python interface

`chatgnt.dataset` exposes a small typed or clearly documented interface:

- `load_dataset_contract(path=...) -> dict`;
- `load_canonical_jsonl(path) -> list[dict]`;
- `content_sha256(example) -> str`;
- `validate_example(example, contract, *, mode) -> None`;
- `validate_workflow_event(event, contract) -> None`;
- `validate_authoring_dataset(candidates, events, contract) -> dict`;
- `validate_frozen_dataset(candidates, events, train, validation, pilot, contract) -> dict`;
- `render_assistant_target(example) -> str`;
- `render_training_messages(example, workflow_events, contract) -> list[dict[str, str]]`; and
- `verify_dataset_contract(contract_path=...) -> dict`.

The implementation may add private helpers but should not create a general framework or duplicate the Stage 3 evaluation module.

Every public validation function raises `ContractError` on failure. Reports and CLI success output are JSON-compatible dictionaries rendered with `canonical_json`.

## Command-line contract

The read-only command is:

```bash
uv run --frozen python scripts/verify_dataset_contract.py --mode contract
```

Later authoring checks use:

```bash
uv run --frozen python scripts/verify_dataset_contract.py \
  --mode authoring \
  --candidates PATH \
  --events PATH
```

Freeze checks use:

```bash
uv run --frozen python scripts/verify_dataset_contract.py \
  --mode freeze \
  --candidates PATH \
  --events PATH \
  --train PATH \
  --validation PATH \
  --pilot PATH
```

When target split or per-family allocation is not exact, freeze mode also requires:

```bash
  --split-deviation PATH
```

Supplying a deviation record when every target is exact is an error. Omitting it when any target differs is an error.

Arguments forbidden or required for each mode are enforced. Success prints one canonical JSON object to stdout and exits 0. A `ContractError` prints one canonical error object to stderr and exits 2. Unexpected internal exceptions are not recast as contract failures.

The command never rewrites, canonicalises, splits, or renders input files.

## Required reports

Contract-mode success reports at least:

- result, contract ID, schema version;
- config and schema paths plus SHA-256 identities;
- registry counts;
- target accepted/train/validation/pilot counts;
- renderer ID and expected assistant-target digest for the built-in fixture; and
- confirmation that schema/config parity and the built-in lifecycle checks passed.

Authoring and freeze reports include mode, input identities, candidate lifecycle counts, achieved coverage counts, scenario count, and validation warnings. Freeze reports additionally include projection identities and every achieved hard target.

Reports must not include model-generated content or imply qualitative dataset quality.

## Required tests

Focused tests must cover at least:

### Schema and strict loading

- accepted example and event;
- every missing, extra, incorrectly typed, blank, or invalid-enum field class;
- duplicate JSON keys, blank lines, BOM, CRLF, non-canonical lines, and non-finite numbers;
- response-schema reference and unexpected response fields; and
- ID and UTC timestamp patterns.

### Cross-field behaviour

- every robustness, complexity, constraint, pilot, provenance, and family/subtype invariant in both valid and invalid directions;
- prohibited target-model drafting identity; and
- prohibited target-model revision or review identity; and
- trimmed source and response strings.

### Workflow chains

- valid human and model draft chains;
- model revision and human edit provenance agreement;
- missing, cross-example, forked, cyclical, out-of-order, and post-terminal events;
- changed versus preserved snapshot digests;
- acceptance without a passing review;
- revision after review requiring a new review; and
- latest candidate digest mismatch.

### Rendering

- exact empty system and user messages;
- exact compact assistant string with behavioural field ordering;
- ingredient field ordering;
- Unicode and JSON escaping;
- numeric rendering and semantic round-trip;
- source-key order independence;
- no metadata or provenance leakage; and
- rejection of unresolved or rejected candidates at the collection-to-render boundary.

### Collection modes

- authoring-mode partial coverage succeeds and reports imbalance;
- freeze-mode target fixture succeeds;
- every hard count and coverage gate fails independently;
- scenario leakage, duplicate normalized prompts, invalid lifecycle, and projection drift fail;
- every candidate reaches one terminal disposition at freeze;
- exact allocation rejects an unnecessary deviation record, while non-exact allocation requires a recomputed, bound, project-author-approved deviation record;
- projections are sorted by example ID independently of candidate-file order;
- response-diversity concentration is a warning rather than failure; and
- CLI mode/argument rules, stdout, stderr, and exit status.

The focused suite runs explicitly with `uv run --frozen python -m unittest discover -s contract_tests`. The full existing suite runs separately with its frozen command, `uv run --frozen python -m unittest discover -s tests`, and must continue to pass. Stage 3 evidence binds every `tests/test_*.py` file by digest, so adding a new file under that glob would invalidate historical evidence rather than extend it. Focused contract tests therefore live in their own directory. They construct temporary synthetic records and must not add real supervised examples to the repository.

## Acceptance criteria

Step 5 is complete when:

1. every required artefact exists and matches this reviewed specification;
2. `uv run --frozen python scripts/verify_dataset_contract.py --mode contract` exits 0 with a canonical success report;
3. `uv run --frozen python -m unittest discover -s contract_tests` passes;
4. the complete existing test suite passes;
5. `git diff --check` passes;
6. no supervised or held-out example has been authored;
7. no model has been loaded, trained, or queried; and
8. project records identify the implemented contract and any explicit limitations.

## Review boundary and stopping rule

One fresh adversarial review will challenge whether this contract could corrupt training targets, admit internally contradictory examples, lose provenance, leak non-training fields into supervision, invalidate scenario-isolated splits or coverage claims, or produce non-reproducible rendering.

One repair pass will address material findings. Further review is required only if the reviewer identifies an unresolved issue capable of materially invalidating dataset identity, training input, split isolation, or the later experiment. Style preferences, hypothetical malicious-maintainer resistance, and features belonging to later dataset authoring, audit, tokenisation, training, or evaluation stages are documented or deferred rather than expanding this implementation.
