# Dataset v1 Production Batch 11 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; final 10 independently reviewed candidates terminally accepted
- **Batch:** `dataset-v1-batch-11`
- **Planned candidates:** 10 (`dataset-v1-191`–`dataset-v1-200`)
- **Planning reference corpus:** 170 accepted examples from Batches 01–09
- **Expected corpus before terminal closure:** 190 accepted examples after Batch 10 closes
- **Reserved event block:** `dataset-event-v1-1001`–`dataset-event-v1-1099`
- **Matrix:** [`production-matrix.json`](../../../data/dataset-v1/authoring/batch-11/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Frozen coverage shape

Batch 11 supplies the final ten scheduled examples. Each intent family has two slots: one breadth and one robustness; one standard and one composed. The robustness slot is composed in every family, leaving the breadth slot standard.

Advice, explanation, emotional support, and creative generation each require one compatible-constraint example. Because their composed slot is also the required format-pressure slot, that single robustness prompt carries both one focused incompatible-format request and one distinct compatible content constraint. This pairing is intentional and follows the accepted Batch 01 precedent; format pressure remains the robustness role, while the compatible requirement remains independently scorable. Transformation requires no compatible constraint.

| Axis | Per family | Batch total |
| --- | ---: | ---: |
| Planned candidates | 2 | 10 |
| Target-use / breadth / robustness | 0 / 1 / 1 | 0 / 5 / 5 |
| Standard / composed | 1 / 1 | 5 / 5 |
| Constraint-bearing | family-specific | 4 |
| Format / serialization pressure | family-specific | 4 / 1 |

The input forms are also frozen by family: advice and explanation each use one direct request and one statement; emotional support and creative generation each use one question and one direct request; transformation uses one question and one direct request.

## Frozen scenario matrix

| ID | Family | Slice | Form | Complexity | Constraint | Role | Subtype | Topic | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `191` | Advice | Breadth | Statement | Standard | No | — | Preparation | History and society | First time hosting a local-history evening |
| `192` | Advice | Robustness | Direct | Composed | Yes | Format | Option comparison | Nature and environment | Allotment versus balcony containers using three factors |
| `193` | Explanation | Breadth | Statement | Standard | No | — | Cause and effect | Arts and culture | Applause settling into a shared rhythm |
| `194` | Explanation | Robustness | Direct | Composed | Yes | Format | Cause and effect | Science and mathematics | Warm water loosening a metal lid, with one analogy |
| `195` | Emotional support | Breadth | Question | Standard | No | — | Self-compassion | Consumer choices | Self-criticism after choosing the slow checkout queue |
| `196` | Emotional support | Robustness | Direct | Composed | Yes | Format | Confidence support | Arts and culture | Discouragement after a first dance class, with one five-minute step |
| `197` | Creative | Breadth | Question | Standard | No | — | Event or experience | Nature and environment | Dusk park event built around attentive listening |
| `198` | Creative | Robustness | Direct | Composed | Yes | Format | Scene or opening | Fictional and imaginative worlds | Two-sentence opening about an unsent-apology vending machine |
| `199` | Transformation | Breadth | Question | Standard | No | — | Clarity edit | History and society | Old community-hall notice rewritten in modern language |
| `200` | Transformation | Robustness | Direct | Composed | No | Serialization | Notes to finished copy | Sync-status support notes containing quotes and a Windows path |

## Final-target arithmetic

Combined with the 170 accepted examples from Batches 01–09 and the frozen Batch 10 schedule, Batch 11 reaches the exact 200-example target. Every intent family finishes with:

- 40 accepted examples;
- 28 target-use, six breadth, and six robustness examples;
- 10 questions, 20 direct requests or commands, and 10 statements or fragments;
- 24 standard and 16 composed examples;
- 12 compatible-constraint examples; and
- two examples for each robustness role: format, behaviour, and serialization pressure.

This arithmetic depends on accepting the scheduled coverage shape, not on accepting weak content. Any rejected candidate must be replaced within the same slot rather than changing the quota labels.

## Diversity and collision audit

- IDs are contiguous and unique from `dataset-v1-191` through `dataset-v1-200`; scenario IDs and substantive situations are distinct from accepted Batches 01–09.
- The breadth slots add new family-topic or operation combinations: small-event hosting in local history, spontaneous crowd synchronisation, self-compassion after a trivial uncertain choice, a sound-centred park experience, and modernisation of an old public notice.
- The four compatible constraints use distinct observable forms: exactly three comparison factors, exactly one analogy, one five-minute practice step, and exactly two fictional sentences.
- The format-pressure scenarios request Markdown, XML, XML, and YAML respectively; the underlying tasks remain legitimate and independently useful.
- The serialization scenario uses a quoted status, a Windows-style path, and a time inside a practical support-update transformation. It differs in both user goal and requested artefact from earlier technical escaping explanations and fictional path-bearing scenarios.
- Photography, tabletop games, pottery and ceramics, and all other frozen exclusions are absent.

## Authoring boundaries

- The matrix freezes scenario identity and metadata only. It contains no exact user prompt, assistant response, workflow event, held-out content, or split allocation.
- Exact prompts must remain answerable from stable, low-stakes general knowledge without browsing, private data, professional advice, or current information.
- `192`, `194`, `196`, and `198` must satisfy their compatible constraints while ignoring only the conflicting presentation request. No other slot may acquire a compatible important constraint.
- `199` and `200` must include their complete short source material in the exact prompt. `200` must naturally include the quoted status, Windows-style path, and time described by the matrix.
- The format-pressure requests must remain focused; do not add behaviour or serialization pressure to those slots. The serialization slot must not also request an incompatible output format or abandonment of ChatG&T behaviour.
- Exact held-out prompts, prompt-development material, worked baseline examples, Qwen queries or outputs, training runs, and model-performance signals remain prohibited inputs.
- A fresh author drafts the batch and a separate fresh reviewer judges every validated snapshot. At most one consolidated repair pass and one fresh terminal review are authorised before escalation.

## Event reservation and next action

Batch 11 owns only `dataset-event-v1-1001` through `dataset-event-v1-1099`. The expected no-repair path reserves `1001`–`1010` for initial drafts, `1011`–`1020` for independent first reviews, and the following available IDs for deterministic acceptance. One consolidated repair cycle and fresh terminal review may use the remaining IDs if needed; events are append-only and never renumbered.

Batch 11 was authored concurrently with Batch 10. The first review passed nine records and found one method-construction collision in `dataset-v1-198`. A local repair preserved its exact two-sentence opening while changing the preparation architecture; fresh terminal review passed it.

Final evidence:

- matrix SHA-256: `bf8e16ee12dbbb336a70675f963ffb7be962d530314207bb9815dbb4e634083e`;
- candidate SHA-256: `478909da8c390c03c050fdd73dd92a3bfe6a3dc863c42392a595526686bc318b`;
- workflow-event SHA-256: `65fec7ddf25228539caa12c732e0155ed3f31330b7d9dd73fb971100091b648d`;
- lifecycle: 10 accepted, 0 rejected, 0 unresolved;
- deterministic acceptance events: `dataset-event-v1-1023`–`dataset-event-v1-1032`;
- exact quota, matrix-parity, cross-wave collision, authoring-validation, and terminalizer-idempotence checks: pass.
