# Dataset v1 Calibration Batch 01

- **Stage:** 4, Step 8
- **Status:** Closed; all 10 candidates accepted after direct project-author inspection
- **Batch:** `dataset-v1-batch-01`
- **Authoring guide:** `chatgnt-dataset-authoring-v1.2`
- **Candidate path:** `data/dataset-v1/authoring/batch-01/candidates.jsonl`
- **Workflow path:** `data/dataset-v1/authoring/batch-01/workflow-events.jsonl`
- **Frozen matrix path:** `data/dataset-v1/authoring/batch-01/calibration-matrix.json`

## Frozen calibration matrix

| ID | Intent family | Slot |
| --- | --- | --- |
| `dataset-v1-001` | Advice and decision support | Standard target-use |
| `dataset-v1-002` | Advice and decision support | Composed breadth with a compatible constraint |
| `dataset-v1-003` | Explanation and technical understanding | Standard target-use |
| `dataset-v1-004` | Explanation and technical understanding | Composed robustness with serialization pressure |
| `dataset-v1-005` | Low-stakes emotional support | Standard target-use |
| `dataset-v1-006` | Low-stakes emotional support | Composed robustness with behaviour pressure |
| `dataset-v1-007` | Creative generation | Standard breadth |
| `dataset-v1-008` | Creative generation | Composed robustness with format pressure |
| `dataset-v1-009` | Short-form transformation | Standard target-use |
| `dataset-v1-010` | Short-form transformation | Composed target-use with supplied content and compatible constraints |

The batch retains five standard and five composed records, two records per intent family, ten distinct scenarios, null splits, and no pilot members. It does not alter the final dataset quotas.

## Review and repair history

The independent initial review passed six candidates immediately: `001`, `002`, `003`, `005`, `007`, and `008`. It requested local repairs to `004`, `006`, `009`, and `010` for coverage metadata, title or method templating, and weak garnish execution. One consolidated repair pass updated those four snapshots and recorded four model-revision events. The same reviewer then passed the repaired snapshots on all three dimensions and found the earlier batch-level coverage and templating findings resolved.

Direct project-author inspection subsequently identified a systematic problem that the model review had missed: every current garnish contained another instruction, explanation, warning, decision rule, or tip rather than an optional recipe flourish. The guide and rubric were amended to version 1.1 to make the garnish boundary explicit. The project author recorded a human `revision_requested` quality review with `recipe_execution_weak` for each of the ten then-current snapshots. The frontier-model authoring process then changed only the ten garnish strings and set `provenance.model_revision_used` truthfully for every candidate; `material_human_edit` remained false because the project author supplied the criterion and decision while the frontier-model process supplied the replacement wording.

The garnish correction exposed a broader calibration failure: beneath schema-valid recipe fields, all ten responses still read primarily as ordinary prose, explanations, or checklists. Rubric v1.2 therefore added the holistic bartender test. The project author recorded a second batch-wide `revision_requested` review on the then-current snapshots. Decision D-053 authorises one bounded whole-response calibration rewrite; for `004`, `006`, `009`, and `010`, it is an explicit one-time exception beyond the ordinary material-revision limit. A future non-pass is rejected rather than revised again.

The project author approved the complete v1.2 responses for `001` and `002` verbatim. The frontier-model authoring process supplied and recorded the bounded `003`–`010` wording, replacing only `assistant_response` for every candidate. Prompts, metadata, scenario identities, allocation state, and provenance summaries were preserved. The project author subsequently reviewed every current snapshot, passed all ten on all three authoring dimensions, and accepted their current content digests.

## Current v1.2 responses

| ID | Rewrite authority | Current title | Current garnish |
| --- | --- | --- | --- |
| `001` | Project-author approved verbatim | `The Clear-Surface Collins` | `One clear worktop as visible proof of progress.` |
| `002` | Project-author approved verbatim | `The Second-Life Sour` | `A bright peel of second-life satisfaction.` |
| `003` | Bounded frontier-model rewrite | `The Conductivity Cooler` | `A frost-rimmed spoon for the reveal.` |
| `004` | Bounded frontier-model rewrite | `The Backslash Twist` | `Perfectly paired backslashes, curled over the rim.` |
| `005` | Bounded frontier-model rewrite | `The Replay Release` | `One light twist of self-forgiveness.` |
| `006` | Bounded frontier-model rewrite | `The Arrive-Anchor Fizz` | `A twist of self-credit for showing up.` |
| `007` | Bounded frontier-model rewrite | `Pip's Pocket Orchard` | `A sunflower seed tucked into Pip's acorn-cap hat.` |
| `008` | Bounded frontier-model rewrite | `The Moonlit Rail Flight` | `A silver ticket stub resting on the rim.` |
| `009` | Bounded frontier-model rewrite | `The Nine-O'Clock Spritz` | `A tiny clock face marked 9:00.` |
| `010` | Bounded frontier-model rewrite | `The Lift-Notice Highball` | `A slim paper twist in lift-button silver.` |

## Current state and evidence

- Candidates: 10 canonical snapshots.
- Workflow events: 88 append-only events: 10 drafts, 44 quality reviews, 24 model revisions, and 10 acceptance events.
- Current lifecycle: 0 unresolved, 10 accepted, 0 rejected.
- Current latest event for every candidate: `accepted`.
- Allocation: every split is null and every `pilot_member` is false.
- Authoring validator: pass with 10 accepted candidates and no warnings; candidate digest `5c0fcb7c6a2da43f48371fef00bf630c87881a8673b8581328042c26cb5d5dd3`, event digest `81388100b8ac5762157bffd02fcf21b519ed953b55b7070526b82696d12d30d0`.
- Rubric/config parity: pass for `chatgnt-dataset-authoring-v1.2`; all ten dimension reason codes and both explicit failure codes remain members of the frozen dataset registry.
- JSON integrity: pass for both rubric documents, the calibration matrix, all 10 candidate records, and all 88 workflow events.
- Dataset contract regression suite: 14 tests passed.
- Full project regression suite: 128 tests passed.
- `git diff --check`: pass.

## Calibration outcome

The project author accepted all ten current snapshots under rubric v1.2, closing the calibration batch without a remaining unresolved lifecycle. The calibration demonstrated why small batches, direct inspection, role-specific garnish rules, and a holistic bartender test are necessary before scaling. Step 8 remains in progress because the complete dataset has not yet been authored, but production batches of at most 20 may now begin under the calibrated v1.2 standard.
