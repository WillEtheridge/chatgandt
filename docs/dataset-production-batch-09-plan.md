# Dataset v1 Production Batch 09 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted
- **Batch:** `dataset-v1-batch-09`
- **Planned candidates:** 20 (`dataset-v1-151`–`dataset-v1-170`)
- **Prior accepted corpus:** 130 examples, 26 per intent family after Batch 07 closes
- **Reserved event block:** `dataset-event-v1-0801`–`dataset-event-v1-0899`
- **Matrix:** [`production-matrix.json`](../data/dataset-v1/authoring/batch-09/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Frozen coverage shape

Batch 09 follows the production schedule exactly. Each intent family has four slots: three target-use and one robustness; one question, two direct requests or commands, and one statement or fragment; two standard and two composed; and exactly one compatible-constraint example. The constraint-bearing target-use slot and the robustness slot are the two composed examples in each family.

The robustness roles are serialization pressure for advice, explanation, emotional support, and creative generation, and behaviour pressure for short-form transformation. Robustness pressure does not count as a compatible substantive constraint.

| Axis | Per family | Batch total |
| --- | ---: | ---: |
| Planned candidates | 4 | 20 |
| Target-use / breadth / robustness | 3 / 0 / 1 | 15 / 0 / 5 |
| Question / direct / statement | 1 / 2 / 1 | 5 / 10 / 5 |
| Standard / composed | 2 / 2 | 10 / 10 |
| Constraint-bearing | 1 | 5 |
| Serialization / behaviour pressure | 4 / 1 | 4 / 1 |

## Frozen scenario matrix

| ID | Family | Slice | Form | Complexity | Constraint | Role | Subtype | Topic | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `151` | Advice | Target-use | Question | Standard | No | — | Habit change | Home and everyday life | Remembering wet laundry |
| `152` | Advice | Target-use | Direct | Standard | No | — | Preparation | Community and events | First food-pantry shift |
| `153` | Advice | Target-use | Direct | Composed | Yes | — | Prioritisation | Home and everyday life | Choosing a weekend home fix with three criteria |
| `154` | Advice | Robustness | Statement | Composed | No | Serialization | Interpersonal navigation | Ambiguous quoted chore labels |
| `155` | Explanation | Target-use | Question | Standard | No | — | Cause and effect | Science and mathematics | Changing shadow length |
| `156` | Explanation | Target-use | Direct | Standard | No | — | Worked example | Money and budgeting | Shared bill plus tip |
| `157` | Explanation | Target-use | Direct | Composed | Yes | — | Troubleshooting | Consumer choices | Mechanical-pencil lead breakage in three checks |
| `158` | Explanation | Robustness | Statement | Composed | No | Serialization | Misconception correction | Technology and software | Escaping a Windows-style path in JSON |
| `159` | Emotional support | Target-use | Question | Standard | No | — | Perspective reframing | Travel and places | Boarding the wrong local bus |
| `160` | Emotional support | Target-use | Direct | Standard | No | — | Boundary reflection | Relationships and social life | Asking for a lent book back |
| `161` | Emotional support | Target-use | Direct | Composed | Yes | — | Supporting someone else | Business and marketing | Friend's quiet first market stall |
| `162` | Emotional support | Robustness | Statement | Composed | No | Serialization | Perspective reframing | Catastrophising over a curt supplied reply |
| `163` | Creative | Target-use | Question | Standard | No | — | Story premise or plot | Fictional and imaginative worlds | Lift opening onto yesterday's office |
| `164` | Creative | Target-use | Direct | Standard | No | — | Idea generation | Home and everyday life | Reusing empty mint tins |
| `165` | Creative | Target-use | Direct | Composed | Yes | — | Name generation | Travel and places | Four tiny-ferry names with exclusions |
| `166` | Creative | Robustness | Statement | Composed | No | Serialization | Story premise or plot | Quoted late-night radio station premise |
| `167` | Transformation | Target-use | Question | Standard | No | — | Message or reply drafting | Travel and places | Polishing a lost-property enquiry |
| `168` | Transformation | Target-use | Direct | Standard | No | — | Notes to finished copy | Food and cooking | Seasonal pear stall card |
| `169` | Transformation | Target-use | Direct | Composed | Yes | — | Constraint-preserving rewrite | Nature and environment | Eighteen-word trail sign |
| `170` | Transformation | Robustness | Statement | Composed | No | Behaviour | Shortening | Travel and places | Hostel checkout note under behaviour pressure |

## Diversity and collision audit

- IDs are contiguous and unique from `dataset-v1-151` through `dataset-v1-170`; all scenario IDs and summaries are distinct.
- The matrix was compared with all 130 accepted records in Batches 01–07. It does not reuse an accepted scenario, source artefact, or substantive answer plan.
- The scenarios add sparse family-topic pairings and underused operations, including household habit support, food-pantry preparation, mechanical-object troubleshooting, emotional support after a navigation error, and constrained trail-sign transformation.
- The four serialization scenarios exercise different natural sources: ambiguous household labels, JSON path escaping, a line-broken personal reply, and fictional station branding. They are legitimate tasks rather than bare serialization traps.
- Compatible constraints are observably distinct: a three-criterion priority rule, a three-check diagnosis, a two-part supportive response, four names with lexical exclusions, and an exact-word-count sign preserving two phrases.
- Photography, tabletop games, pottery and ceramics, and all other frozen exclusions are absent.

## Authoring boundaries

- The exact prompt for every supplied-content scenario must contain the complete short source. The target response may not depend on unstated text, values, or facts.
- Serialization-pressure prompts must contain characters that genuinely require correct JSON escaping, while remaining plausible user inputs with useful underlying tasks.
- `156` must supply the bill amount, tip percentage, and number of people. `158` must include the exact path or string being explained. `169` must include complete trail notes and make an exact 18-word artefact possible.
- `153`, `157`, `161`, `165`, and `169` must satisfy every compatible constraint. No other slot may acquire a compatible important constraint.
- The behaviour-pressure request in `170` must remain focused and must not displace the legitimate shortening task.
- Exact held-out prompts, prompt-development material, worked baseline examples, Qwen queries or outputs, split assignments, training runs, and model-performance signals remain prohibited inputs.

## Event reservation and next action

Batch 09 owns only `dataset-event-v1-0801` through `dataset-event-v1-0899`. The expected no-repair path reserves `0801`–`0820` for initial drafts, `0821`–`0840` for independent first reviews, and the following available IDs for deterministic acceptance. One consolidated repair cycle and fresh terminal review may use the remaining IDs if needed; events are append-only and never renumbered.

The first review passed 15 candidates. One arithmetic repair made `dataset-v1-156`'s four-way split total exactly £94.50; four adjacent transformations received distinct method architectures instead of a shared scaffold. Fresh terminal review passed all five changes.

Final evidence:

- matrix SHA-256: `0b07a25d680974331e7eb742b6598f6fcddcf5a973101820e0b68c0e0d1ffdc5`;
- candidate SHA-256: `19a2a220011b29db9d8c187917fecc1fb1ee49b8556ca67af9be53ee842c87e9`;
- workflow-event SHA-256: `20b8bc197161cbf660734466adc74b08d4dd79b90d49e208ba85f1e55547822a`;
- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- review: 15 initial passes, five revisions, five terminal passes;
- acceptance events: `dataset-event-v1-0851`–`dataset-event-v1-0870`; and
- authoring validation and terminalizer idempotence: pass.
