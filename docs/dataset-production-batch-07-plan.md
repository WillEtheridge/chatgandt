# Dataset v1 Production Batch 07 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted
- **Batch:** `dataset-v1-batch-07`
- **Planned candidates:** 20 (`dataset-v1-111`–`dataset-v1-130`)
- **Prior accepted corpus:** 110 examples, 22 per intent family after Batch 06 closes
- **Event-ID block:** `dataset-event-v1-0601`–`dataset-event-v1-0699`
- **Matrix:** [`production-matrix.json`](../data/dataset-v1/authoring/batch-07/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Coverage shape

Batch 07 contains four slots per family: three target-use slots and one robustness slot. Every family adds one question, two direct requests or commands, and one statement or fragment; two standard and two composed examples; and exactly one compatible constraint-bearing example.

All five robustness examples are composed but carry no compatible substantive constraint. Behaviour pressure applies to advice, explanation, emotional support, and creative generation; format pressure applies to transformation. This separation makes contract persistence and ordinary constraint-following independently observable within the batch.

The scenarios deliberately add sparse family-topic pairings and underrepresented operations while avoiding reusable answers from the first 90 accepted records. Their scenario identity, requested artefact, and coverage metadata are frozen before exact prompts or responses are drafted.

## Matrix self-audit

- IDs are contiguous and unique from `dataset-v1-111` through `dataset-v1-130`.
- Each of the five intent families has exactly four slots.
- Each family has exactly three `target_use` and one `robustness` slot.
- Each family has exactly one question, two direct requests or commands, and one statement or fragment.
- Each family has exactly two standard and two composed slots.
- Each family has exactly one compatible constraint-bearing slot, always a target-use slot distinct from robustness pressure.
- Robustness roles match the frozen production schedule: four `behaviour_pressure` slots and one transformation `format_pressure` slot.
- All 20 scenario IDs and scenario summaries are distinct, and none reuses a scenario from the first 90 accepted records.
- Every composed slot has a valid complexity source; every standard slot has none; constraint and robustness fields agree with their labels.
- Photography, tabletop games, and pottery or ceramics are absent.

## Boundaries

- Exact prompts must include all short source material needed to fulfil transformation or other supplied-content tasks.
- The robustness pressure must remain focused and must not displace the legitimate underlying task.
- Photography, tabletop games, and pottery or ceramics remain withheld and must not appear.
- No exact held-out prompt, Qwen output, split assignment, or model-performance signal may influence authoring or review.
- Candidate provenance must identify the actual authoring model and retain null split allocation during authoring.
- A fresh author drafts the batch and a separate fresh reviewer judges every validated snapshot.
- At most one consolidated repair pass and one fresh terminal review are authorised before escalation.
- Passing candidates are terminalised deterministically; frontier models do not issue acceptance events.

## Planned event allocation

The batch owns the disjoint event block `0601`–`0699`. The expected no-repair path is:

- initial draft events: `0601`–`0620`;
- first quality-review events: `0621`–`0640`; and
- deterministic acceptance events: `0641`–`0660`.

Unused event IDs remain available for one bounded repair cycle and its fresh terminal review. Event IDs are append-only and are never renumbered after use.

## Completion evidence

Before the batch closes, record:

- matrix, candidate, and workflow-event SHA-256 identities;
- lifecycle totals for accepted, rejected, and unresolved candidates;
- mechanical coverage counts and diversity findings;
- independent review outcomes and any bounded repairs;
- deterministic terminalisation and idempotence results; and
- authoring-validator and relevant contract-test results.

Batch 07 was produced concurrently with Batch 06 in Wave 2. Its first review passed eight candidates, requested 11 local revisions, and recommended replacing one semantic near-duplicate of Batch 06. The consolidated repair varied repeated measurement constructions, corrected one word-count claim, and replaced `dataset-v1-119` with a substantively distinct scenario in the same quota cell. That replacement required an explicit matrix update; final quotas remained unchanged. A live cross-batch audit also caught a measurement sequence introduced concurrently by Batch 06 before terminal review. A fresh reviewer passed all 12 changed records.

This batch demonstrates that unique IDs and scenario IDs are necessary but insufficient under concurrent authoring: semantic and construction-level collision checks must run against the combined live wave before closure.

Final evidence:

- final matrix SHA-256: `4015d8b433672687ce5745988cc26c901f42c5e5bf83edcab604d459fe464216`;
- candidate SHA-256: `bf2473ba4bcd44290ea0b09907ccea9bdc8086677f1a36637d03786079715dbf`;
- workflow-event SHA-256: `00718c9942a4fa78023013115eca159eb1d99ae362772c2604dcc85f86167a7f`;
- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- review: eight initial passes, 12 bounded replacements or revisions, and 12 terminal passes;
- deterministic acceptance events: `dataset-event-v1-0665`–`dataset-event-v1-0684`;
- achieved coverage: 15 target-use, five robustness, 10 standard, 10 composed, and five constraint-bearing;
- authoring validation: pass with no warnings; and
- terminalizer dry run, write, and idempotence run: pass.
