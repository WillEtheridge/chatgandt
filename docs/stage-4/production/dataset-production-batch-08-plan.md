# Dataset v1 Production Batch 08 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted
- **Batch:** `dataset-v1-batch-08`
- **Planned candidates:** 20 (`dataset-v1-131`–`dataset-v1-150`)
- **Prior accepted corpus:** 130 examples, 26 per intent family after Batch 07 closes
- **Event-ID block:** `dataset-event-v1-0701`–`dataset-event-v1-0799`
- **Matrix:** [`production-matrix.json`](../../../data/dataset-v1/authoring/batch-08/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Frozen coverage shape

Batch 08 follows the production schedule exactly. Each intent family has four slots: three target-use and one breadth; one question, two direct requests or commands, and one statement or fragment; three standard and one composed; and exactly one compatible-constraint example. The breadth slot is both composed and constraint-bearing in every family. There are no robustness slots or robustness roles.

| Axis | Per family | Batch total |
| --- | ---: | ---: |
| Planned candidates | 4 | 20 |
| Target-use / breadth / robustness | 3 / 1 / 0 | 15 / 5 / 0 |
| Question / direct / statement | 1 / 2 / 1 | 5 / 10 / 5 |
| Standard / composed | 3 / 1 | 15 / 5 |
| Constraint-bearing | 1 | 5 |

## Frozen scenario matrix

| ID | Family | Slice | Form | Complexity | Constraint | Subtype | Topic | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `131` | Advice | Target-use | Question | Standard | No | Option comparison | Personal growth and wellbeing | Rest or personal-project progress on one free evening |
| `132` | Advice | Target-use | Direct | Standard | No | Prioritisation | Business and marketing | Ordering mixed feedback for a hobby market stall |
| `133` | Advice | Target-use | Statement | Standard | No | Problem diagnosis | Leisure and entertainment | Repeatedly arriving rushed for anticipated events |
| `134` | Advice | Breadth | Direct | Composed | Yes | Preparation | Science and mathematics | Meteor-shower viewing through four practical checks |
| `135` | Explanation | Target-use | Question | Standard | No | Process explanation | Money and budgeting | Pending card payment becoming complete |
| `136` | Explanation | Target-use | Direct | Standard | No | Cause and effect | Writing and communication | How the position of only changes meaning |
| `137` | Explanation | Target-use | Statement | Standard | No | Comparison and distinction | Leisure and entertainment | Round-robin versus knockout structures |
| `138` | Explanation | Breadth | Direct | Composed | Yes | Concept explanation | Community and events | Time bank with one example and one limitation |
| `139` | Emotional support | Target-use | Question | Standard | No | Perspective reframing | Money and budgeting | Shame after comparing savings with friends |
| `140` | Emotional support | Target-use | Direct | Standard | No | Confidence support | Science and mathematics | Feeling underqualified for a public science talk |
| `141` | Emotional support | Target-use | Statement | Standard | No | Validation and normalisation | Writing and communication | Overinterpreting ordinary edits as inability |
| `142` | Emotional support | Breadth | Direct | Composed | Yes | Conversation preparation | History and society | Asking an older relative about a family story |
| `143` | Creative | Target-use | Question | Standard | No | Idea generation | Writing and communication | Low-pressure writing-group warm-ups |
| `144` | Creative | Target-use | Direct | Standard | No | Event or experience | Career and work | Five-minute preference-sharing team ritual |
| `145` | Creative | Target-use | Statement | Standard | No | Character or mascot | Money and budgeting | Approachable mascot for a money-skills club |
| `146` | Creative | Breadth | Direct | Composed | Yes | Idea generation | Personal growth and wellbeing | Four non-achievement journal prompts |
| `147` | Transformation | Target-use | Question | Standard | No | Clarity edit | Money and budgeting | Plain-language discretionary-spending sentence |
| `148` | Transformation | Target-use | Direct | Standard | No | Shortening | Nature and environment | Shorter park-trail etiquette notice |
| `149` | Transformation | Target-use | Statement | Standard | No | Tone shift | Fictional and imaginative worlds | Warmer imaginary-creature museum welcome |
| `150` | Transformation | Breadth | Direct | Composed | Yes | Constraint-preserving rewrite | Habits and productivity | Ordered after-work notes as a short spoken cue |

## Diversity and collision rationale

The matrix was planned against all 130 accepted records, not merely the preceding wave. It deliberately adds 17 family-topic pairings that were absent from the accepted corpus; the other three slots use sparse pairings with distinct operations and scenarios. No scenario ID, reusable substantive answer, or requested artefact is intentionally reused.

The breadth slots also vary the form of their compatible constraint: a four-check preparation sequence, an example-plus-limitation explanation, a bounded opening-line and permission reminder, a count-plus-exclusion creative artefact, and an ordered phrase-preserving transformation. This avoids turning the constraint-bearing quota into a repeated count-list template.

## Authoring boundaries

- The matrix freezes scenario identity and metadata only. It contains no exact user prompt, assistant response, candidate record, workflow event, or held-out content.
- Exact prompts must be answerable from stable, low-stakes general knowledge without browsing, private data, professional advice, or current information.
- Photography, tabletop games, and pottery or ceramics remain excluded.
- Exact prompts for transformation slots `147`–`150` must include their complete short source material. The source for `150` must make the required action order explicit and contain the exact phrase `keys, wallet, pass`.
- `134`, `138`, `142`, `146`, and `150` must fulfil every compatible constraint listed in the matrix. Other slots must not acquire an important constraint during drafting.
- The meteor-shower answer may recommend checking local conditions but must not claim or require current weather, timing, or location data.
- No exact held-out prompt, Qwen query or output, training run, split allocation, pilot allocation, or model-performance signal may influence authoring.
- A fresh author drafts the batch and a separate fresh reviewer judges every validated snapshot. At most one consolidated repair pass and one fresh terminal review are authorised before escalation.

## Event reservation and completion evidence

Batch 08 owns the disjoint event block `0701`–`0799`. The expected no-repair path reserves `0701`–`0720` for initial drafts, `0721`–`0740` for first quality reviews, and the following available IDs for deterministic acceptance. Unused IDs remain available for one bounded repair pass and fresh terminal review; event IDs are append-only and are never renumbered.

Before closure, record matrix, candidate, and event-file SHA-256 identities; lifecycle and coverage totals; whole-corpus diversity findings; review and repair outcomes; deterministic terminalisation and idempotence; and authoring-validation results.
## Completion evidence

The first review passed 18 candidates. It requested a distinct mascot identity for `dataset-v1-145` after detecting a prior “Pip's Pocket” construction, and stronger procedural cocktail execution for the four prompts in `dataset-v1-146`. One bounded repair pass changed only those records; fresh terminal review passed both.

- matrix SHA-256: `a123d2f0c18f16b45d123184cf3747a09143d3efc5768bfeb006c2608bd3965d`;
- candidate SHA-256: `bae82c15b4c98f41cba8c31b8d36db26a3cdda31150a507c3d3be281ccf26ff9`;
- workflow-event SHA-256: `9a5bcf7a5a8545f4fdf531f81eb6ce182c961c38623fa5f81819d661afc6f1b3`;
- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- review: 18 initial passes, two revisions, two terminal passes;
- acceptance events: `dataset-event-v1-0745`–`dataset-event-v1-0764`; and
- authoring validation and terminalizer idempotence: pass.
