# Dataset v1 Production Batch 02 Plan

- **Stage:** 4, Step 8
- **Status:** Closed; 20 independently reviewed candidates terminally accepted by deterministic validator
- **Batch:** `dataset-v1-batch-02`
- **Planned candidates:** 20 (`dataset-v1-011`–`dataset-v1-030`)
- **Matrix:** [`production-matrix.json`](../data/dataset-v1/authoring/batch-02/production-matrix.json)
- **Authoring standard:** `chatgnt-dataset-authoring-v1.2`

## Why this batch has this shape

The final dataset requires 40 accepted examples in each intent family, with 28 target-use, six breadth, and six robustness examples per family. Calibration contributed two examples per family but used different slice combinations. This production batch adds four candidates per family and deliberately brings the cumulative 30-example corpus to the same slice position in every family:

| Cumulative count per family | Target-use | Breadth | Robustness | Total |
| --- | ---: | ---: | ---: | ---: |
| After calibration | Varied | Varied | Varied | 2 |
| After proposed Batch 02 | 4 | 1 | 1 | 6 |
| Final target | 28 | 6 | 6 | 40 |

The batch therefore contains 15 target-use, three breadth, and two robustness slots. It is not intended to reproduce every final-dataset ratio within one small batch. Input form, complexity, compatible constraints, roles, topics, and subtypes make measured progress while later batches retain room to correct achieved counts and genuine quality losses.

## Planned batch counts

| Axis | Proposed Batch 02 | Cumulative after 30 accepted candidates | Final target |
| --- | --- | --- | --- |
| Intent family | 4 each | 6 each | 40 each |
| Coverage slice | 15 target-use, 3 breadth, 2 robustness | 20 / 5 / 5 | 140 / 30 / 30 |
| Input form | 4 questions, 9 direct requests, 7 statements | 7 / 15 / 8 | 50 / 100 / 50 |
| Complexity | 14 standard, 6 composed | 19 / 11 | 120 / 80 |
| Compatible constraint | 6 | 9 | 60 |
| Robustness role | 1 behaviour, 1 serialization | 2 behaviour, 1 format, 2 serialization | 10 each |

The cumulative counts assume all 20 candidates are accepted. Rejections are not backfilled by weakening the acceptance bar; a rejected slot receives a genuinely new scenario in the same planned coverage position.

## Proposed scenario matrix

| ID | Family | Slice | Form | Complexity | Constraint | Role | Subtype | Topic | Scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `011` | Advice | Target-use | Direct | Standard | No | — | Preparation | Career and work | First one-to-one with a new manager |
| `012` | Advice | Target-use | Statement | Standard | No | — | Habit change | Habits and productivity | Losing the evening to phone scrolling |
| `013` | Advice | Target-use | Question | Standard | No | — | Option comparison | Leisure and entertainment | Weekly book club versus flexible solo reading |
| `014` | Advice | Robustness | Direct | Composed | Yes | Behaviour | Action planning | Travel and places | Fifteen-minute carry-on preparation plan |
| `015` | Explanation | Target-use | Direct | Standard | No | — | Concept explanation | Money and budgeting | Why compound interest accelerates |
| `016` | Explanation | Target-use | Direct | Standard | No | — | Process explanation | Nature and environment | How material becomes compost |
| `017` | Explanation | Target-use | Statement | Standard | No | — | Misconception correction | Learning and study | Rereading versus retrieval practice |
| `018` | Explanation | Breadth | Direct | Composed | Yes | — | Comparison | Arts and culture | Tempo versus rhythm |
| `019` | Emotional support | Target-use | Question | Standard | No | — | Validation | Learning and study | Attending a first evening class alone |
| `020` | Emotional support | Target-use | Direct | Standard | No | — | Self-compassion | Personal growth | Guilt about taking a needed rest day |
| `021` | Emotional support | Target-use | Statement | Standard | No | — | Supporting someone | Relationships | Supporting a friend after a flat rejection |
| `022` | Emotional support | Breadth | Direct | Composed | Yes | — | Boundary reflection | Community and events | Declining another organiser role |
| `023` | Creative | Target-use | Question | Standard | No | — | Slogan or tagline | Business and marketing | Neighbourhood tool-sharing tagline |
| `024` | Creative | Target-use | Direct | Standard | No | — | Story premise | Fictional worlds | The mysterious last tram |
| `025` | Creative | Target-use | Statement | Standard | No | — | Scene or opening | Nature and environment | Botanist hears impossible birdsong |
| `026` | Creative | Target-use | Statement | Composed | Yes | — | Concept or campaign | Community and events | Family-friendly library-of-things launch |
| `027` | Transformation | Target-use | Question | Standard | No | — | Tone shift | Home and everyday life | Warmer housemate dishes reminder |
| `028` | Transformation | Target-use | Direct | Standard | No | — | Message drafting | Business and marketing | Café tray-return notice |
| `029` | Transformation | Breadth | Statement | Composed | Yes | — | Constraint-preserving rewrite | History and society | Twelve-word museum-label rewrite |
| `030` | Transformation | Robustness | Statement | Composed | Yes | Serialization | Tone shift | Community and events | Empathetic cancellation with exact quoted title |

## Boundaries and next action

The frozen matrix itself contains scenario identities and metadata only. Drafting has now produced exact user prompts and candidate assistant responses in separate candidate and workflow files. No held-out prompt, split assignment, pilot assignment, Qwen query, or model-performance signal was introduced.

Batch progression:

1. **Complete:** draft the 20 exact prompts and ideal responses in a fresh authoring context under rubric v1.2;
2. **Complete:** run structural, cross-field, canonical-serialization, and frozen-slot validation;
3. **Complete:** perform qualitative review in a separate context;
4. **Complete:** adjudicate the two unsupported templating findings, repair the three confirmed local defects, and obtain fresh independent passes; and
5. **Next:** inspect achieved coverage and response repetition before planning Batch 03.

## Drafting evidence

- Candidate snapshots: 20 canonical JSONL records at `data/dataset-v1/authoring/batch-02/candidates.jsonl`.
- Workflow history: 20 `draft_created` events, `dataset-event-v1-0089` through `dataset-event-v1-0108`.
- Lifecycle: 20 unresolved, 0 accepted, 0 rejected; no qualitative review or terminal event exists.
- Frozen-slot fidelity: pass with zero mismatches across IDs, scenarios, metadata, constraints, and coverage roles.
- Authoring validator: pass with no warnings.
- Matrix SHA-256: `3e75545490a265e1f4447d579bfe55464e431710d17d44401e0579052f765c09`.
- Candidate SHA-256: `28fa610e1634ef344adff9d34b360304f261227824149e920d15725e8629161e`.
- Event SHA-256: `d5b75abc49a684a861ef9c9c31cdd63a2fd61c6420d416e58c88c8f161ff5c21`.
- `git diff --check`: pass.

## Independent qualitative review

The fresh reviewer passed all 20 candidates on underlying-answer quality and metaphorical coherence. It requested revision for recipe-style execution on every candidate using `response_templating`; there were no `rejection_recommended` outcomes and no other reason codes.

The finding is batch-level rather than 20 independent content failures. Across the 20 responses:

- 72 of 85 ingredients use `ml`;
- 11 responses use ml ingredients totalling exactly 100;
- the other responses mostly use descending ml weights with a small `dashes`, `measure`, or real-unit addition;
- `pour` begins 11 method steps, with recurring `stir`, `strain`, and `serve` progressions; and
- titles and garnishes remain individually unique.

The reviewer judged that the repeated normalised weighting and preparation scaffold would teach a narrow response template across unrelated tasks. Because cocktail measures and preparation verbs are also required features of the shared behaviour, the project author adjudicated the finding before revision. The accepted interpretation is not that cocktail vocabulary may not repeat, but that the examples must vary enough in recipe composition and reasoning structure to teach generalisable style rather than one surface formula.

The reviewer completed and appended all 20 review events before exceeding the expected reporting window and being interrupted. Independent verification then confirmed:

- 40 append-only events: 20 drafts and 20 quality reviews;
- review event IDs `dataset-event-v1-0109` through `dataset-event-v1-0128`;
- 20 `revision_requested`, 0 pass, and 0 `rejection_recommended` outcomes;
- 20 uses of the registered `response_templating` reason code;
- unchanged candidate and frozen-matrix identities;
- authoring-validator pass with 20 unresolved candidates and no warnings; and
- current event SHA-256 `507f83835cbe9fca9740c8896cf08ce3b37916d49048b9cc3a1ef995b9901a90`.

## Project-author adjudication and correction overlay

Decision D-055 retains `ml` as the expected ChatG&T default and defines plausible bartender proportions: a meaningful base pour, smaller modifiers, and accents such as smaller ml measures, dashes, drops, splashes, twists, or useful real units. Repeated `ml` and shared bar vocabulary are not templating by themselves. Score-like amount sequences, routine exact-total normalisation, and one generic reasoning scaffold across unrelated tasks remain a failure.

The frozen overlay at `data/dataset-v1/authoring/batch-02/revision-overlay-v1.json` assigns one fitting cocktail construction, ingredient plan, and method architecture to each current candidate while preserving prompts, scenarios, metadata, substantive answers, artefacts, constraints, and central metaphors. Its SHA-256 is `49e5606c11bd1ac333c8ee92afe2d86de5e2caba13a358768aac20c83b3a293b`.

Pre-revision overlay checks pass:

- 20 assignments bound to the current candidate and event identities;
- 20 unique amount-unit sequences;
- three planned exact-100-ml totals, below the frozen maximum of three; and
- method plans spanning two, three, four, and five steps.

Exactly one coordinated revision pass and one separate post-revision review are authorised. The latter is the stopping point for whole-batch correction.

## Coordinated revision evidence

The fresh reviser applied the frozen overlay once to all 20 candidates, changed only `assistant_response` plus `provenance.model_revision_used`, and appended `model_revision` events `dataset-event-v1-0129` through `dataset-event-v1-0148`. It did not score or accept its own work.

Independent post-revision checks confirmed:

- frozen prompt, scenario, metadata, allocation, and non-revision provenance fidelity;
- 20 overlay-matching and unique amount-unit sequences;
- exactly three ml totals of 100;
- method lengths spanning two, three, four, and five steps;
- 20 unique complete method-opening sequences;
- decoded quoted-artefact fidelity for the serialization-pressure candidate;
- authoring-validator pass with 20 unresolved candidates and no warnings;
- revised candidate SHA-256 `1cabbf7f48492483a43648612bca0fbb1525ecc02077df626988577debc76b8b`; and
- post-revision event SHA-256 `0973daf301e060f0156aabe114748f89d4df28ab3c3f479418fefe1e7431b548`.

## Terminal qualitative review

The fresh terminal reviewer appended quality-review events `dataset-event-v1-0149` through `dataset-event-v1-0168`. It returned:

- **Pass (15):** `012`–`017`, `019`–`020`, `022`, `024`–`028`, and `030`.
- **Revision requested (5):** `011`, `018`, `021`, `023`, and `029`.
- **Rejection recommended:** none.

| ID | Reviewer reason | Finding | Independent verification |
| --- | --- | --- | --- |
| `011` | `response_templating` | Claimed an identical `50/25/15/2 dashes` sequence with `021` | Disputed: `011` also contains a 10 ml modifier and has five ingredients; the exact sequence is unique |
| `018` | `factual_or_language_error` | Calls an unspecified long-short pattern “syncopated” without establishing displaced or off-beat emphasis | Confirmed as a concrete local language/factual defect |
| `021` | `response_templating` | Claimed the same exact collision with `011` | Disputed: `021` has four ingredients and no 10 ml modifier; similarity exists, exact identity does not |
| `023` | `underlying_answer_not_useful` | “Good Tools. Shared Doors.” makes the service promise unclear | Confirmed as a concrete local usefulness defect |
| `029` | `factual_or_language_error` | Changes “probably used” into definite “worn as” | Confirmed as a concrete local factual-preservation defect |

The two templating review events remain preserved in the append-only history. Their evidence does not satisfy the frozen exact-sequence collision check, so they require project-author qualitative adjudication rather than automatic revision. The other three findings are bounded candidate-level repairs. No further whole-batch revision is authorised.

Final mechanical verification passed with 80 events, 15 terminal passes, five terminal revision requests, zero rejection recommendations, unchanged candidate/matrix/overlay identities, no validator warnings, rubric/config parity, JSON integrity, all 14 additive dataset-contract tests, and current event SHA-256 `57c709ab09827f699bd6f9fe42bc5f18bfead3bd2b3aa4174ad9dcb081ccd794`.

## Local repairs, independent adjudication, and closure

A bounded reviser changed only the three confirmed local defects:

- `018` now contrasts different clap placements at a fixed 100 BPM without mislabelling an unspecified pattern as syncopation;
- `023` delivers the clear tagline “Share Tools. Build Neighbourhoods.”; and
- `029` preserves the source uncertainty in the 11-word label “Bronze brooch, made in York in 865, probably fastened a cloak.”

Model-revision events `0169`–`0171` bind those snapshots. A fresh reviewer passed all three dimensions for the repaired candidates. A separate fresh adjudication review passed `011` and `021`, confirming that their complete amount-unit sequences are not identical and that shared plausible proportions alone do not satisfy rubric v1.3's templating rule. Quality-review events `0172`–`0176` preserve that evidence.

Decision D-056 then replaced mandatory per-example human acceptance with deterministic terminalisation after independent review. The dry run identified all 20 candidates as eligible. `chatgnt-dataset-terminalizer-v1` atomically appended acceptance events `0177`–`0196`; an idempotence run proposed zero further events.

Final closure evidence:

- lifecycle: 20 accepted, 0 rejected, 0 unresolved;
- candidate SHA-256: `1be38573233b170b3646180c63d7aba2b8e87a581258defad8f1d9897c9316d2`;
- workflow-event SHA-256: `162ef63c0830d5a6c152dc333954acdf32aed063fc5b4e503b9849d188c5c462`;
- amended workflow-schema SHA-256: `ef2885300018f10e528a632552c19663dff090109a9b006bbf9808bcd2725eb0`;
- terminalizer implementation SHA-256: `c9d4e3bdea6a5485455ad354e334a83a0b9fa1085a18468f252da6ce47f07cb1`;
- authoring validator: pass with no warnings;
- terminalizer idempotence: pass with zero additions; and
- additive dataset-contract suite: 18 tests passed.
