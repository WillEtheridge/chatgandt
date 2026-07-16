# Dataset v1 Production Batch 06 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted
- **Batch:** `dataset-v1-batch-06`
- **Planned candidates:** 20 (`dataset-v1-091`–`dataset-v1-110`)
- **Prior accepted corpus:** 90 examples, 18 per intent family after Batch 05 closes
- **Reserved event block:** `dataset-event-v1-0501`–`dataset-event-v1-0599`
- **Matrix:** [`production-matrix.json`](../data/dataset-v1/authoring/batch-06/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Frozen coverage shape

Batch 06 follows the production schedule exactly. Each intent family has four slots: three target-use and one breadth; one question, two direct requests or commands, and one statement or fragment; three standard and one composed; and exactly one compatible-constraint example. The composed slot is the constraint-bearing breadth slot in every family. There are no robustness slots or robustness roles.

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
| `091` | Advice | Target-use | Question | Standard | No | Interpersonal navigation | Career and work | Teammate's last-minute handoff changes |
| `092` | Advice | Target-use | Direct | Standard | No | Preparation | Travel and places | First solo hostel stay |
| `093` | Advice | Target-use | Statement | Standard | No | Problem diagnosis | Learning and study | Overplanned study sessions that never begin |
| `094` | Advice | Breadth | Direct | Composed | Yes | Risk and trade-off assessment | Consumer choices | Borrow, rent, or buy a weekend tool |
| `095` | Explanation | Target-use | Question | Standard | No | Technical how-to | Travel and places | Reading arrival and departure columns in a bus timetable |
| `096` | Explanation | Target-use | Direct | Standard | No | Worked example | Learning and study | Weighted average of course marks |
| `097` | Explanation | Target-use | Statement | Standard | No | Misconception correction | Arts and culture | Minor keys are not always sad |
| `098` | Explanation | Breadth | Direct | Composed | Yes | Process explanation | Food and cooking | Vinaigrette emulsion in three causal stages |
| `099` | Emotional support | Target-use | Question | Standard | No | Self-compassion | Learning and study | Missed language-practice streak |
| `100` | Emotional support | Target-use | Direct | Standard | No | Conversation preparation | Career and work | Asking a manager about conflicting priorities |
| `101` | Emotional support | Target-use | Statement | Standard | No | Validation and normalisation | Food and cooking | Embarrassment after a dinner dish went wrong |
| `102` | Emotional support | Breadth | Direct | Composed | Yes | Supporting someone else | Nature and environment | Friend's allotment seedling setback |
| `103` | Creative | Target-use | Question | Standard | No | Name generation | Technology and software | Gentle habit-timer app names |
| `104` | Creative | Target-use | Direct | Standard | No | Slogan or tagline | Travel and places | Riverside walking-route slogan |
| `105` | Creative | Target-use | Statement | Standard | No | Scene or opening | Food and cooking | After-hours bakery opening |
| `106` | Creative | Breadth | Direct | Composed | Yes | Idea generation | Science and mathematics | Household-object symmetry demonstrations |
| `107` | Transformation | Target-use | Question | Standard | No | Summarisation | Leisure and entertainment | Reading-group discussion notes |
| `108` | Transformation | Target-use | Direct | Standard | No | Audience adaptation | Technology and software | Router-restart instructions for a beginner |
| `109` | Transformation | Target-use | Statement | Standard | No | Shortening | Career and work | Wordy internal project-status line |
| `110` | Transformation | Breadth | Direct | Composed | Yes | Audience adaptation | Science and mathematics | Child-friendly planetarium text |

## Authoring boundaries

- The matrix freezes scenario identity and metadata only. It contains no exact user prompt, assistant response, candidate record, workflow event, or held-out content.
- All 20 scenario IDs and substantive situations are new relative to accepted Batches 01–05. The matrix favours new family-topic pairings and operations while retaining natural, plausible tasks.
- Exact prompts must be answerable from stable, low-stakes general knowledge without browsing, private data, professional advice, or current information.
- Photography, tabletop games, and pottery or ceramics remain excluded.
- The exact prompt for `096` must supply all marks and weights needed for its worked example. It may not rely on hidden values.
- The exact prompts for `107`–`110` must include their complete short source material. For `110`, that source must explicitly contain the words `orbit` and `axis`; the target must preserve both while satisfying the audience and word-count constraints.
- `094`, `098`, `102`, `106`, and `110` must fulfil every listed compatible constraint. Other slots must not acquire an important constraint merely to make drafting easier.
- No exact held-out prompt, Qwen query or output, training run, split allocation, pilot allocation, model-performance signal, commit, or push is authorised by this plan.

## Event reservation and next action

Workflow events for Batch 06, when separately authorised and created, must use only the reserved block `dataset-event-v1-0501` through `dataset-event-v1-0599`. The expected no-repair path reserves `0501`–`0520` for initial drafts, `0521`–`0540` for first reviews, and the following available IDs for deterministic acceptance. Planning consumes no event IDs and creates no event records.

Batch 06 was produced concurrently with Batch 07 in Wave 2. The first review passed 12 records and requested eight bounded repairs: two responses needed stronger or more accurate recipe execution, two creative methods needed clearer preparation framing, and four adjacent transformations repeated the same scaffold. A separate reviser changed only those records; a fresh reviewer passed all eight.

Final evidence:

- matrix SHA-256: `0c5f49246b2af21db986526883cfac87d185656cee8aa7db3335cfecb473658f`;
- candidate SHA-256: `b829e065135c2c2702d858b8e1008e270efe9d8b697a28daa41f382da18a829f`;
- workflow-event SHA-256: `e7417d303369e7401c1d799f9dd27f58d61f6a7847211e4c4ff8af43f88febf9`;
- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- review: 12 initial passes, eight bounded revisions, and eight terminal passes;
- deterministic acceptance events: `dataset-event-v1-0557`–`dataset-event-v1-0576`;
- achieved coverage: 15 target-use, five breadth, 15 standard, five composed, and five constraint-bearing;
- authoring validation: pass with no warnings; and
- terminalizer dry run, write, and idempotence run: pass.
