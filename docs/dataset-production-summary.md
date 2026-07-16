# Dataset v1 Production Summary

- **Stage:** 4, Steps 8–9
- **Status:** Complete; formal duplication, contamination, and exclusions audit remains Step 10
- **Produced:** 200 terminally accepted examples in Batches 01–11
- **Authoring standard:** `chatgnt-dataset-authoring-v1.3`

## Outcome

The authoring pipeline produced exactly 200 accepted examples without inspecting held-out prompts, querying Qwen, assigning splits, or training a model. All 200 examples have unique example IDs, scenario IDs, user prompts, and cocktail titles. Combined authoring validation reports 200 accepted, 0 rejected, 0 unresolved, and no warnings.

The batch-ordered collection identities are:

- candidates SHA-256: `65a29225f94cd062344b34adf368fd6c8b0a5d84a911eb91a7c60a983e10c2ac`;
- workflow events SHA-256: `585babc1a883cbecd6e39f8b5b6426c894a9c4af4fad108285b1e8d2ecea5c3e`.

These identities describe the concatenation of Batch 01 through Batch 11 in numeric order. They do not yet represent a frozen split package.

## Frozen quota result

Every intent family contains exactly 40 accepted examples and independently reaches the same crossed targets:

| Axis | Per family | Corpus total |
| --- | ---: | ---: |
| Target-use / breadth / robustness | 28 / 6 / 6 | 140 / 30 / 30 |
| Question / direct / statement | 10 / 20 / 10 | 50 / 100 / 50 |
| Standard / composed | 24 / 16 | 120 / 80 |
| Constraint-bearing | 12 | 60 |
| Behaviour / format / serialization pressure | 2 / 2 / 2 | 10 / 10 / 10 |

Each family contains eight task subtypes and between 14 and 19 topics. The corpus has 200 unique scenarios.

## Workflow evidence

The append-only lifecycle contains 784 events from 47 recorded actor identities:

- 200 initial drafts;
- 298 qualitative reviews: 210 passes, 84 revision requests, and four rejection recommendations;
- 86 model revisions or replacements; and
- 200 deterministic acceptance events.

The counts are not a claim that 86 final records are weak. They show that failed snapshots and replacement attempts remain visible instead of being overwritten. In particular, one Batch 10 replacement failed fresh semantic review and was replaced again under a separately recorded terminal event chain.

## Master-agent production pattern

After calibration and the first sequential batches, remaining work used four concurrent waves: 04–05, 06–07, 08–09, and 10–11. Concurrency was limited to work with disjoint candidate ranges, event blocks, and file paths. Each wave synchronized before the next:

1. freeze two quota-correct scenario matrices;
2. author both batches in parallel;
3. review both batches independently in parallel;
4. make one consolidated local repair pass per batch where possible;
5. run fresh terminal review of changed snapshots;
6. audit the combined live wave for exact and semantic collisions; and
7. record deterministic acceptance only after every current snapshot passed.

The master retained global authority over quota arithmetic, cross-batch collision review, lifecycle validation, terminal acceptance, and stopping conditions. This prevented concurrent agents from accepting their own work or silently resolving conceptual conflicts.

## Verification

- Combined 200-example authoring validation: pass, no warnings.
- Per-family frozen quota arithmetic: exact for every axis.
- Exact uniqueness: 200/200 IDs, scenarios, prompts, and titles.
- Focused contract suite: 19 tests passed.
- Frozen historical regression suite: 128 tests passed in an isolated run.
- Python compilation check: pass.
- `git diff --check`: pass.

An earlier regression invocation was intentionally discarded because two copies of the suite were accidentally run concurrently against shared provenance fixtures. The isolated rerun passed all 128 tests; recording the contaminated run avoids presenting a convenient rerun as unexplained evidence.

## Boundary and next action

This completes candidate authoring, qualitative review, revision, and terminal acceptance. It does not freeze dataset v1. Stage 4 Step 10 must now run the formal duplication, contamination, and exclusions audit against supervised examples, worked baseline examples, development prompts, and withheld domains. Split assignment, pilot selection, manifest creation, and dataset freeze follow only after that audit closes.
