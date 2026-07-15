# Dataset Split and Pilot Selection Specification

- **Stage:** 4 — Build and freeze dataset v1
- **Step:** 6 — Scenario-isolated allocation
- **Status:** Implementation specification
- **Date:** 2026-07-15

## Purpose

This specification makes the already-agreed split rule executable. It assigns terminally accepted, unallocated dataset-v1 candidates to training or validation without crossing scenario groups, then selects a representative 40-example pilot from training.

The procedure is deterministic, read-only unless an explicit output directory is supplied, and independent of model behaviour. It does not author, revise, review, accept, or reject examples; generate held-out prompts; load a model; or train an adapter.

## Inputs and preconditions

The allocator accepts canonical `candidates.jsonl` and `workflow-events.jsonl` governed by the dataset-v1 contract.

Before allocation:

- every candidate passes authoring-mode validation;
- every candidate has one terminal `accepted` or `rejected` workflow event;
- exactly 200 candidates are accepted and each intent family contains 40 accepted examples;
- all accepted and rejected candidates have `split: null` and `pilot_member: false`;
- every scenario ID belongs to exactly one intent family; and
- rejected candidates remain in the candidate collection but are never allocated.

A scenario spanning intent families is treated as a classification error rather than silently split or optimised as a multi-family group. Under the frozen substantive scenario rule, the same user goal and situation should have the same primary intent family.

## Required artefacts

- `config/dataset-split-v1.json` — seed, algorithm identities, target counts, and coverage requirements;
- `schemas/dataset-allocation-report-v1.schema.json` — deterministic allocation evidence;
- `chatgnt/dataset_split.py` — allocation and pilot-selection implementation;
- `scripts/assign_dataset_splits.py` — dry-run and explicit-write CLI; and
- `contract_tests/test_dataset_split.py` — synthetic allocation tests outside the Stage 3-frozen suite.

No real dataset file is created while implementing or testing this step.

## Deterministic scenario identity

Accepted records are grouped by exact `scenario_id`. Every record in a group receives the same split.

Validation priority for a scenario is the lowercase SHA-256 of:

```text
dataset-validation-allocation-v1|20260715|<scenario_id>
```

This digest is only a deterministic tie-breaker. It is not randomness evidence and does not override count or coverage objectives.

## Validation coverage mask

The allocator represents the hard validation coverage requirements as a bit mask covering:

- all three input forms;
- standard and composed complexity;
- target-use, breadth, and robustness slices;
- at least one compatible constraint; and
- format, behaviour, and serialization robustness roles.

The mask for a scenario group is the union of the labels carried by its accepted records.

## Validation allocation algorithm

### Family subset states

For each intent family independently, dynamic programming considers whole scenario groups and retains one deterministic best selection for every attainable pair:

```text
(validation example count, validation coverage mask)
```

When multiple group subsets produce the same pair, the selection with the lexicographically smallest tuple of scenario-priority digests wins.

### Cross-family selection

The five family state sets are combined. A complete allocation must satisfy the full global validation coverage mask. Candidate allocations are ordered by:

1. smallest maximum absolute deviation from the target of eight validation examples in any family;
2. smallest sum of absolute per-family deviations;
3. smallest absolute deviation from 40 validation examples overall; and
4. lexicographically smallest combined scenario-priority signature.

The search increases the permitted maximum family deviation from zero upward and stops at the first radius containing a full-coverage allocation. This implements the stated objective order. Exact 8-per-family and 40-overall allocation therefore always wins when it is feasible with full validation coverage.

If no scenario-isolated full-coverage allocation exists, the command fails with a diagnostic. It never weakens validation coverage or crosses scenarios.

### Non-exact outcome

When the chosen allocation is not exactly 32 training and eight validation examples per family, the report sets `split_deviation_required: true`. It records achieved counts and affected scenario IDs but does not create or approve a split-deviation record. The later freeze still requires the project-author-approved, digest-bound deviation artefact defined by the dataset contract.

## Pilot selection

Pilot priority for an accepted training example is the lowercase SHA-256 of:

```text
dataset-pilot-selection-v1|20260715|<example_id>
```

The allocator selects exactly eight training examples per intent family. Selection is deterministic greedy coverage: at each step it prefers the record adding the most still-unrepresented pilot coverage labels, then a new topic, then a new task subtype, then the lowest priority digest.

Pilot coverage labels include input form, complexity, coverage slice, compatible-constraint presence, and non-null robustness role.

The completed pilot must contain:

- exactly 40 examples and eight per intent family;
- only training examples;
- within every family, both complexity levels, at least two input forms, at least two coverage slices, and at least one compatible constraint; and
- overall, all three input forms, all three coverage slices, and all three robustness roles.

If the selected training split cannot support these requirements, allocation fails rather than silently producing an unrepresentative pilot. The pilot is a diagnostic subset, not a statistical holdout, so scenario groups need not be all-in or all-out of the pilot.

## Outputs

The pure Python operation returns:

- a deep-copied candidate collection with accepted allocation fields set;
- unchanged workflow events;
- canonical train, validation, and pilot projections ordered by ascending `example_id`; and
- a deterministic allocation report.

Rejected records remain unassigned. Input objects are never mutated.

The allocation report binds:

- allocation and dataset-contract identities;
- algorithm IDs and seed;
- source candidate and event digests;
- allocated candidate, train, validation, and pilot digests;
- accepted, rejected, scenario, total split, and per-family counts;
- exact-versus-deviation status;
- validation and pilot coverage; and
- selected validation scenario IDs and pilot example IDs.

## CLI

Dry run:

```bash
uv run --frozen python scripts/assign_dataset_splits.py \
  --candidates PATH \
  --events PATH
```

Dry run validates and prints the canonical allocation report without writing files.

Explicit write:

```bash
uv run --frozen python scripts/assign_dataset_splits.py \
  --candidates PATH \
  --events PATH \
  --output-dir PATH
```

The output directory must not already exist. The command creates it atomically and writes canonical `candidates.jsonl`, `workflow-events.jsonl`, `train.jsonl`, `validation.jsonl`, `pilot.jsonl`, and `allocation-report.json`. A failure leaves no partial final directory.

Success prints one canonical report and exits 0. `ContractError` prints one canonical error object to stderr and exits 2. The command never modifies its input paths.

## Tests and acceptance

Synthetic tests cover:

- reproducibility and input immutability;
- exact singleton-scenario allocation;
- multi-record scenario isolation;
- deterministic tie-breaking;
- a non-exact result that requires later approval;
- validation coverage preservation;
- pilot size, family balance, eligibility, and coverage;
- rejection of unresolved, preallocated, cross-family-scenario, insufficient-coverage, and malformed inputs;
- report-schema validity and digest binding; and
- dry-run versus explicit atomic write behaviour.

Step 6 is complete when the focused contract suites, contract CLI, allocation configuration check, all 128 existing frozen tests, compilation, JSON parsing, and `git diff --check` pass without creating real data or performing a model operation.
