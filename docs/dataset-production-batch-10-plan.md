# Dataset v1 Production Batch 10 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted

## Completion evidence

The first review passed 14 candidates, requested four transformation-method revisions, and identified two semantic duplicates requiring replacement. The replacement for `dataset-v1-171` passed terminal review. The first replacement for `dataset-v1-181` still collided with another same-batch boundary scenario, so it was rejected at the terminal gate and replaced once more with a distinct uncertainty-without-evidence scenario; a final independent reviewer passed it. This extra terminal replacement is recorded rather than hidden as part of the original repair.

- final matrix SHA-256: `cea0cd5422537d4052416106674a831ae79738a238b391f245de1f95dbf5e7c8`;
- candidate SHA-256: `a81bf705ccb1b7e43ee28e023a2a999d7e9e02fc17c24629553aadf70ccae8a1`;
- workflow-event SHA-256: `972b92144bc7feb9ebcd20478bf2814569df9bb1bc976b774c5daad08e948a56`;
- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- deterministic acceptance events: `dataset-event-v1-0955`–`dataset-event-v1-0974`;
- exact quota, matrix-parity, semantic-collision, authoring-validation, and terminalizer-idempotence checks: pass.

- **Batch:** `dataset-v1-batch-10`
- **Planned candidates:** 20 (`dataset-v1-171`–`dataset-v1-190`)
- **Prior accepted corpus:** 170 examples, 34 per intent family after Batch 09 closes
- **Reserved event block:** `dataset-event-v1-0901`–`dataset-event-v1-0999`
- **Matrix:** [`production-matrix.json`](../data/dataset-v1/authoring/batch-10/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Frozen coverage shape

Batch 10 follows the production schedule exactly. Each intent family has four slots: three target-use and one breadth; one question, two direct requests or commands, and one statement or fragment; and exactly one compatible-constraint example. The first four families each have two standard and two composed slots. Short-form transformation has three standard and one composed slot. There are no robustness slots or roles.

| Axis | Advice, explanation, emotional, creative | Transformation | Batch total |
| --- | ---: | ---: | ---: |
| Planned candidates | 4 each | 4 | 20 |
| Target-use / breadth / robustness | 3 / 1 / 0 each | 3 / 1 / 0 | 15 / 5 / 0 |
| Question / direct / statement | 1 / 2 / 1 each | 1 / 2 / 1 | 5 / 10 / 5 |
| Standard / composed | 2 / 2 each | 3 / 1 | 11 / 9 |
| Constraint-bearing | 1 each | 1 | 5 |

## Frozen scenario matrix

| ID | Family | Slice | Form | Complexity | Constraint | Subtype | Topic | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `171` | Advice | Target-use | Question | Standard | No | Option comparison | Consumer choices | Borrow or buy a rarely used household tool |
| `172` | Advice | Target-use | Direct | Standard | No | Preparation | Arts and culture | First community-choir rehearsal |
| `173` | Advice | Target-use | Direct | Composed | Yes | Interpersonal navigation | Writing and communication | Ask for specific feedback in three conversational moves |
| `174` | Advice | Breadth | Statement | Composed | No | Risk and trade-off assessment | Science and mathematics | Contribute reliably to a citizen-science count as a novice |
| `175` | Explanation | Target-use | Question | Standard | No | Cause and effect | Consumer choices | Why wool can shrink and become denser in a wash |
| `176` | Explanation | Target-use | Direct | Standard | No | Technical how-to | Technology and software | Freeze and unfreeze a spreadsheet header row |
| `177` | Explanation | Target-use | Direct | Composed | Yes | Comparison and distinction | Science and mathematics | Evaporation and boiling through three observable differences |
| `178` | Explanation | Breadth | Statement | Composed | No | Process explanation | Writing and communication | How a postcode helps route a physical letter |
| `179` | Emotional support | Target-use | Question | Standard | No | Boundary reflection | Relationships and social life | Guilt after leaving an informal gathering early |
| `180` | Emotional support | Target-use | Direct | Standard | No | Self-compassion | Nature and environment | First houseplant cutting failed to root |
| `181` | Emotional support | Target-use | Direct | Composed | Yes | Manageable next steps | Career and work | Recover from mispronouncing a colleague's name, with a six-word phrase |
| `182` | Emotional support | Breadth | Statement | Composed | No | Validation and normalisation | Consumer choices | Relief and sadness while donating a childhood collection |
| `183` | Creative | Target-use | Question | Standard | No | Story premise or plot | Fictional and imaginative worlds | Lost-property office receives objects before they are lost |
| `184` | Creative | Target-use | Direct | Standard | No | Event or experience | Arts and culture | Quiet phone-free gallery game |
| `185` | Creative | Target-use | Direct | Composed | Yes | Slogan or tagline | Business and marketing | Seven-word bicycle-repair slogan without “fix” |
| `186` | Creative | Breadth | Statement | Composed | No | Character or mascot | Science and mathematics | Lunar trail guide creature and its crater-revealing behaviour |
| `187` | Transformation | Target-use | Question | Standard | No | Tone shift | Habits and productivity | Kinder rewrite of a harsh evening-routine note |
| `188` | Transformation | Target-use | Direct | Standard | No | Message or reply drafting | Consumer choices | Courteous shop message about a cracked lamp |
| `189` | Transformation | Target-use | Direct | Standard | No | Notes to finished copy | Arts and culture | Recital logistics as a welcoming lobby announcement |
| `190` | Transformation | Breadth | Statement | Composed | Yes | Constraint-preserving rewrite | History and society | Family-recipe headnote as a 24-word archive caption |

## Diversity and collision rationale

The matrix was planned against the 170 accepted records in Batches 01–09. Its scenarios, reusable answers, and requested artefacts are semantically distinct from that corpus: occasional tool access is not the prior tool-sharing slogan; choir preparation is not generic class confidence; citizen-science reliability is not meteor-viewing preparation; postal routing is not library shelf location; the failed cutting is not practical herb troubleshooting; and the family-recipe caption is not a museum label, orchestra note, or ordinary cooking rewrite.

Topic-family pairings also stretch sparsely represented parts of the corpus. Consumer choices appears here as practical advice, material explanation, emotional letting-go, and transformation, but each operation and scenario is different. The breadth slots use four different composition mechanisms—competing considerations, connected steps, multiple outcomes, and supplied content—rather than treating breadth as a repeated list-generation pattern.

## Authoring boundaries

- The matrix freezes scenario identity and metadata only. It contains no exact user prompt, assistant response, workflow event, held-out prompt, or model output.
- Exact prompts must be answerable from stable, low-stakes general knowledge without browsing, private data, professional advice, or current information.
- Photography, tabletop games, and pottery or ceramics remain excluded.
- Exact prompts for transformation slots `187`–`190` must include their complete short source material. The source for `190` must contain `1952` and `Dundee` verbatim.
- Slots `173`, `177`, `181`, `185`, and `190` must fulfil every compatible constraint listed in the matrix. The other slots must not acquire an important constraint during drafting.
- The spreadsheet instructions in `176` must remain product-neutral and explain both freezing and unfreezing without relying on a current vendor interface.
- The wool explanation in `175` must avoid claiming that heat alone always causes shrinkage; it should explain the interaction of moisture, movement, temperature, fibre scales, and relaxation at an appropriate level.
- The citizen-science advice in `174` must prioritise following the project's protocol, recording uncertainty, and avoiding guessed identifications; it must not require live data or expert credentials.
- The exact seven-word slogan in `185` must be delivered as the requested artefact inside the recipe response, not replaced by advice about writing slogans.
- No exact held-out prompt, Qwen query or output, training run, split allocation, pilot allocation, or model-performance signal may influence authoring.
- A fresh author drafts the batch and a separate fresh reviewer judges every validated snapshot. At most one consolidated repair pass and one fresh terminal review are authorised before escalation.

## Event reservation and completion evidence

Batch 10 owns the disjoint event block `0901`–`0999`. The expected no-repair path reserves `0901`–`0920` for initial drafts, `0921`–`0940` for first quality reviews, and the following available IDs for deterministic acceptance. Unused IDs remain available for one bounded repair pass and fresh terminal review; event IDs are append-only and are never renumbered.

Before closure, record matrix, candidate, and event-file SHA-256 identities; lifecycle and coverage totals; whole-corpus diversity findings; review and repair outcomes; deterministic terminalisation and idempotence; and authoring-validation results.
