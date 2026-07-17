# Dataset v1 Proportionate Contamination Audit

- **Date:** 2026-07-16
- **Stage:** 4, Step 10
- **Status:** Complete after amendments 001–002 and a clean v1.2 rerun
- **Initial machine findings:** `data/dataset-v1/audit/findings-v1.json`
- **Passing v1.1 rerun findings:** `data/dataset-v1/audit/findings-v1.1.json`
- **Passing v1.2 rerun findings:** `data/dataset-v1/audit/findings-v1.2.json`
- **Command:** `UV_CACHE_DIR=/tmp/chatgnt-uv-cache HF_HUB_OFFLINE=1 uv run --frozen python scripts/audit_dataset_v1.py`

## Purpose

This audit protects the credibility of the eventual prompt-engineering versus fine-tuning comparison. It asks four practical questions:

1. Does the supervised dataset contain duplicate or near-duplicate lessons?
2. Does it reuse any of the five System B worked examples or 20 spent prompt-development inputs?
3. Are photography, tabletop games, and pottery/ceramics still genuinely withheld?
4. Do the responses show obvious template collapse?

It does not try to prove independence from unknown model pretraining, inspect exact held-out prompts, or turn every shared cocktail phrase into a review case.

## Method

The script validated and loaded all 200 terminally accepted records. Normalized exact comparisons covered prompts, scenario identities, complete responses, prior prompts, and worked responses. A pinned local `sentence-transformers/all-MiniLM-L6-v2` encoder at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` retrieved a deliberately bounded set of complete records:

- 50 closest internal scenario pairs;
- five neighbours for each of 20 development and five worked-example prompts (125 pairs); and
- five response neighbours for each worked response (25 pairs).

All 200 retrieved pairs were reviewed as complete records. Scores were used only for retrieval. The review question was whether the pair teaches substantially the same lesson—not whether it shares a broad intent family, task subtype, cocktail language, or constraint pattern.

The script also searched a narrow withheld-domain vocabulary and aggregated duplicate titles, repeated measure sequences, repeated four-word method openings, and repeated eight-word method phrases.

## Automatic results

- 200 accepted examples loaded and their complete authoring lifecycle validated.
- No exact duplicate prompts, scenario IDs, or complete responses.
- No exact match to a prior prompt or worked response.
- No withheld-domain vocabulary match.
- No duplicate cocktail title.
- No repeated method opening across three or more examples.
- One eight-word phrase occurred twice: “one practical offer if you'd like i can,” in `dataset-v1-102` and `dataset-v1-161`.
- The most common complete measure sequences appeared six times each (3% of the corpus), which is ordinary cocktail convention rather than response copying.
- MiniLM embedded 430 texts; none exceeded its 256-wordpiece input limit.

## Complete-record review

Most retrieved similarities were legitimate shared task families: two different notices, two different story premises, or two different supportive situations. Shared response structure was allowed where it was required by the behavioural contract or a user constraint. Worked-response neighbours shared cocktail voice but did not copy distinctive content.

Seven examples did cross the practical boundary:

| Example | Collision | Decision rationale |
| --- | --- | --- |
| `dataset-v1-003` | `dev-v1-explanation-clean` | Both ask why equal-temperature metal feels colder than wood; this is a direct paraphrase of the same explanation. |
| `dataset-v1-005` | `dev-v1-emotional-naturalistic` | Both concern replaying a small mistake at work and seek the same perspective and recovery advice. |
| `dataset-v1-014` | `dev-v1-advice-robustness` | Both ask for practical packing help for a short weekend/three-day trip; the fifteen-minute evening schedule narrows but does not change the underlying task enough. |
| `dataset-v1-041` | `dev-v1-advice-constrained` | Both prepare a difficult housemate conversation and require an opening sentence; shared bills merely instantiate the spent development scenario. |
| `dataset-v1-118` | `dev-v1-explanation-naturalistic` | The candidate's password-manager comparison directly teaches the core function asked about in the spent development prompt. |
| `dataset-v1-158` | `dataset-v1-004` | Both explain escaping embedded quotes and backslashes in a Windows path encoded as a JSON string; the examples and methods are interchangeable. |
| `dataset-v1-161` | `dataset-v1-102` | Both require exactly one validating sentence and one practical offer for a discouraged friend; the responses share a distinctive eight-word template as well as the same answer shape. |

The community-club mascot pair (`dataset-v1-044` / `dataset-v1-145`) was retained. It shares a creative task subtype, but the character concepts, teaching content, and organisation-specific execution are distinct. Similarly, overlap between worked-example topics and broader task subtypes was not treated as reuse unless the substantive lesson or answer could be transferred with only surface changes.

## Initial outcome and boundary

Step 10 does not pass yet. The seven current records should be replaced, then the same script and bounded review should be rerun. Their accepted history must not be silently rewritten: the current dataset contract binds each acceptance to the existing content and has no supersession state. The next action is therefore a small versioned representation for replacements—not another general audit framework.

The first 41,957-flag attempt remains documented in `docs/dataset-contamination-audit-generation-001.md`. Its 149 MB untracked payload and unused implementation were removed; the report, reviews, and learning remain.

## Amendment and rerun

Amendment 001 retained the seven original records and their event histories as immutable evidence, then mapped them out of the active set in favour of seven new accepted records:

| Superseded | Replacement |
| --- | --- |
| `dataset-v1-003` | `dataset-v1-201` |
| `dataset-v1-005` | `dataset-v1-202` |
| `dataset-v1-014` | `dataset-v1-203` |
| `dataset-v1-041` | `dataset-v1-204` |
| `dataset-v1-118` | `dataset-v1-205` |
| `dataset-v1-158` | `dataset-v1-206` |
| `dataset-v1-161` | `dataset-v1-207` |

Each replacement preserves the superseded record's intent family, coverage slice, input form, complexity, constraint status, robustness role, and task subtype. The active v1.1 view therefore retains the original experimental quotas while changing the substantive scenario and answer.

The same audit was rerun without changing its retrieval population or interpretation rule. The v1.1 result has:

- exactly 200 terminally accepted active examples;
- no exact prompt, scenario-ID, or complete-response duplicate;
- no exact prior-prompt or worked-response match;
- no withheld-domain match;
- no duplicate title, repeated eight-word method phrase, or repeated method opening;
- no new substantive collision among the 50 internal, 125 prior-prompt, and 25 worked-response pairs reviewed; and
- no MiniLM truncation among the 430 embedded texts.

Repeated measurement sequences remain benign cocktail conventions: the largest sequence frequency is six of 200 examples. The nearest retained semantic pairs are broad task-family similarities already allowed in the initial review, such as different community taglines or different mascot briefs with distinct content.

The passing findings SHA-256 is `379ef3fb530a212c32a3b659eb34e3a4323e40cd2e12719339f0cb7196121aa4`. The active candidate and workflow-event collection identities are `45611ddfbfc42a323c61773d081c414026cf53788d3d78fe64d0f070ad3b73cc` and `b3f827e01e682a72cecd5e733fdb3b58578bae9964fe309e11786095e4d7f7a3` respectively.

Before freeze, amendment 002 replaced `dataset-v1-201` and `dataset-v1-202` with content-equivalent `dataset-v1-208` and `dataset-v1-209`, restoring the corpus's required seven- and eight-ingredient examples. The same audit was rerun once more. It produced no exact, withheld-domain, repeated-phrase, worked-response, or substantive-neighbour failure. Its findings SHA-256 is `9d0b3cccc137ce3a96f004218c8b75dee14f8c671c9fa9735e9fb5bcaa2d86f2`.

Stage 4 Step 10 is complete on active v1.2. This result supports project-level fairness; it does not prove independence from unknown pretraining data.
