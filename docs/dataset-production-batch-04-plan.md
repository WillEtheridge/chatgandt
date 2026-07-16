# Dataset v1 Production Batch 04 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted
- **Batch:** `dataset-v1-batch-04`
- **Planned candidates:** 20 (`dataset-v1-051`–`dataset-v1-070`)
- **Prior accepted corpus:** 50 examples, 10 per intent family
- **Reserved event block:** `dataset-event-v1-0301`–`dataset-event-v1-0399`
- **Matrix:** [`production-matrix.json`](../data/dataset-v1/authoring/batch-04/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Frozen coverage shape

Batch 04 follows the production schedule exactly. Each intent family has four slots: three target-use and one breadth; one question, two direct requests or commands, and one statement or fragment; three standard and one composed; and exactly one compatible-constraint example. The composed slot is the constraint-bearing breadth slot in every family. There are no robustness slots or robustness roles.

| Axis | Per family | Batch total |
| --- | ---: | ---: |
| Planned candidates | 4 | 20 |
| Target-use / breadth / robustness | 3 / 1 / 0 | 15 / 5 / 0 |
| Question / direct / statement | 1 / 2 / 1 | 5 / 10 / 5 |
| Standard / composed | 3 / 1 | 15 / 5 |
| Constraint-bearing | 1 | 5 |

## Frozen scenario matrix

| ID | Family | Slice | Form | Complexity | Constraint | Subtype | Topic | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `051` | Advice | Target-use | Question | Standard | No | Preparation | History and society | First local-archive visit |
| `052` | Advice | Target-use | Direct | Standard | No | Habit change | Nature and environment | Reusable bags repeatedly left at home |
| `053` | Advice | Target-use | Statement | Standard | No | Problem diagnosis | Money and budgeting | Small purchases derailing a weekly budget |
| `054` | Advice | Breadth | Direct | Composed | Yes | Action planning | Food and cooking | Six-person low-waste picnic |
| `055` | Explanation | Target-use | Question | Standard | No | Misconception correction | History and society | Why the 1800s are the nineteenth century |
| `056` | Explanation | Target-use | Direct | Standard | No | Process explanation | Science and mathematics | How a household siphon flows |
| `057` | Explanation | Target-use | Statement | Standard | No | Cause and effect | Nature and environment | Houseplant leaning toward a window |
| `058` | Explanation | Breadth | Direct | Composed | Yes | Comparison and distinction | Nature and environment | Weather versus climate in two contrasts |
| `059` | Emotional support | Target-use | Question | Standard | No | Boundary reflection | Community and events | Guilt about missing volunteer cleanups |
| `060` | Emotional support | Target-use | Direct | Standard | No | Perspective reframing | Leisure and entertainment | Slower reading pace in a book club |
| `061` | Emotional support | Target-use | Statement | Standard | No | Supporting someone else | Writing and communication | Supporting a friend after story rejection |
| `062` | Emotional support | Breadth | Direct | Composed | Yes | Confidence support | Travel and places | Using basic local phrases on a day trip |
| `063` | Creative | Target-use | Question | Standard | No | Event or experience | Relationships and social life | Monthly family-call ritual |
| `064` | Creative | Target-use | Direct | Standard | No | Slogan or tagline | Business and marketing | Neighbourhood refill-shop tagline |
| `065` | Creative | Target-use | Statement | Standard | No | Character or mascot | Fictional and imaginative worlds | Umbrella-repair story hero |
| `066` | Creative | Breadth | Direct | Composed | Yes | Concept or campaign | History and society | Everyday-objects museum exhibition |
| `067` | Transformation | Target-use | Question | Standard | No | Message or reply drafting | Relationships and social life | Neighbour parcel-collection message |
| `068` | Transformation | Target-use | Direct | Standard | No | Audience adaptation | Learning and study | Child-friendly lost-and-found announcement |
| `069` | Transformation | Target-use | Statement | Standard | No | Notes to finished copy | Community and events | Language-exchange room-change notice |
| `070` | Transformation | Breadth | Direct | Composed | Yes | Audience adaptation | Arts and culture | Plain-language orchestra programme note |

## Authoring boundaries

- The matrix freezes scenario identity and metadata only. It contains no exact user prompt, assistant response, candidate record, workflow event, or held-out content.
- All 20 scenario IDs are new relative to accepted Batches 01–03. The scenarios deliberately vary topic and operation within each family and do not reuse an accepted substantive situation.
- Exact prompts must be answerable from stable, low-stakes general knowledge without browsing, private data, professional advice, or current information.
- Photography, tabletop games, and pottery or ceramics remain excluded.
- The author of `070` must include the complete short orchestra programme note in the prompt. The supplied note must explicitly contain the composer name, composition year, and named instruments that the rewrite is required to preserve; the author may not rely on unstated external facts.
- Every other prompt must include any concrete facts needed to deliver its artefact. In particular, `069` must state Tuesday, Room 2, and Room 5; no response may depend on omitted source material.
- No exact held-out prompt, Qwen query or output, training run, split allocation, pilot allocation, model-performance signal, commit, or push is authorised by this plan.

## Event reservation and next action

Workflow events for Batch 04, when separately authorised and created, must use only the reserved block `dataset-event-v1-0301` through `dataset-event-v1-0399`. Planning consumes no event IDs and creates no event records.

Batch 04 was produced alongside Batch 05 as the first bounded concurrent wave. The two agents owned disjoint candidate, document, and event-ID paths; the master process retained cross-batch quota, diversity, validation, and terminalisation authority.

The independent review passed 19 candidates and requested one local language repair for `dataset-v1-067`. A separate reviser replaced the ambiguous phrase about a delivered parcel without changing its task or metadata, and a fresh terminal reviewer passed the revised snapshot. The deterministic terminalizer then accepted all 20 candidates; an immediate second run proposed zero events.

Final evidence:

- matrix SHA-256: `5501b0df49b97820846478ef2689967ff5b1520ddb30c36430fd3a31df92ebb4`;
- candidate SHA-256: `3043b4c404c4dccba294ab9a6ddaa3706222f21a99e89aca14ad7ad23475ba16`;
- workflow-event SHA-256: `5885b81b02f765aa99c3eca70de7c4291f516b5eacf0eb5d6a37dd680d2c8d2b`;
- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- review: 19 initial passes, one bounded revision, and one terminal pass;
- deterministic acceptance events: `dataset-event-v1-0343`–`dataset-event-v1-0362`;
- achieved coverage: 15 target-use, five breadth, 15 standard, five composed, and five constraint-bearing;
- authoring validation: pass with no warnings; and
- terminalizer dry run, write, and idempotence run: pass.
