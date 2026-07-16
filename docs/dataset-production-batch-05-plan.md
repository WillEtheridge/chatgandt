# Dataset v1 Production Batch 05 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted
- **Batch:** `dataset-v1-batch-05`
- **Planned candidates:** 20 (`dataset-v1-071`–`dataset-v1-090`)
- **Prior accepted corpus:** 70 examples, 14 per intent family after Batch 04 closes
- **Event-ID block:** `dataset-event-v1-0401`–`dataset-event-v1-0499`
- **Matrix:** [`production-matrix.json`](../data/dataset-v1/authoring/batch-05/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Coverage shape

Batch 05 contains four slots per family: three target-use slots and one robustness slot. Every family adds one question, two direct requests or commands, and one statement or fragment; two standard and two composed examples; and exactly one focused robustness role.

Compatible-constraint counts follow the frozen production schedule: one each for advice, creative generation, and transformation, and two each for explanation and emotional support. The robustness examples apply serialization pressure to advice and creative generation, format pressure to explanation and emotional support, and behaviour pressure to transformation. Robustness pressure remains distinct from compatible content constraints.

The planned scenarios favour operations and topics absent or sparse in the first 50 accepted examples. Scenario identity, intended artefact, and compatible constraints are frozen before exact prompts or responses are drafted.

## Boundaries

- Exact prompts must include all short source material needed to fulfil transformation, serialization, or technical tasks.
- Photography, tabletop games, and pottery or ceramics remain withheld and must not appear.
- No exact held-out prompt, Qwen output, split assignment, or model-performance signal may influence authoring or review.
- Candidate provenance must identify the actual authoring model and retain null split allocation during authoring.
- A fresh author drafts the batch and a separate fresh reviewer judges every validated snapshot.
- At most one consolidated repair pass and one fresh terminal review are authorised before escalation.
- Passing candidates are terminalised deterministically; frontier models do not issue acceptance events.

## Planned event allocation

The batch owns the disjoint event block `0401`–`0499`. The expected no-repair path is:

- initial draft events: `0401`–`0420`;
- first quality-review events: `0421`–`0440`; and
- deterministic acceptance events: `0441`–`0460`.

Unused event IDs remain available for one bounded repair cycle and its fresh terminal review. Event IDs are append-only and are never renumbered after use.

## Completion evidence

Before the batch closes, record:

- matrix, candidate, and workflow-event SHA-256 identities;
- lifecycle totals for accepted, rejected, and unresolved candidates;
- mechanical coverage counts and diversity findings;
- independent review outcomes and any bounded repairs;
- deterministic terminalisation and idempotence results; and
- authoring-validator and relevant contract-test results.

Batch 05 was produced concurrently with Batch 04 in a disjoint working path. The independent review passed 18 candidates and requested local repairs for `dataset-v1-088` and `dataset-v1-090`: one response repeated the batch's transformation scaffold, while the other both repeated that scaffold and invented an unsupported time detail. A separate reviser changed only those two snapshots. A fresh terminal reviewer passed both repairs.

Final evidence:

- matrix SHA-256: `28419ec38a8d70f5a4823189c5a18c16977068d3212d71f85b92269270a06fd1`;
- candidate SHA-256: `025f5a1ca773020d03231de76c515655d2baee0fa28341692c0338380ac004d2`;
- workflow-event SHA-256: `2faf63df545529175426f7107d6f4af4c23324818fd4b2bfce1715f16b04809d`;
- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- review: 18 initial passes, two bounded revisions, and two terminal passes;
- deterministic acceptance events: `dataset-event-v1-0445`–`dataset-event-v1-0464`;
- achieved coverage: 15 target-use, five robustness, 10 standard, 10 composed, and seven constraint-bearing;
- authoring validation: pass with no warnings; and
- terminalizer dry run, write, and idempotence run: pass.
