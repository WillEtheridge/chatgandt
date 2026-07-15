# Response Similarity and Memorisation Protocol

**Status:** Frozen

This procedure looks for suspicious reproduction of project-authored ideal responses. It can flag evidence consistent with memorisation; it cannot prove a causal mechanism or inspect Qwen's unknown pretraining corpus.

## Attribution-aware reference sets

Each held-out system response is compared with sources that system was exposed to:

| System | Worked-example responses | Training responses |
| --- | --- | --- |
| A — base, minimal prompt | Diagnostic comparison only; not exposed | Not exposed |
| B — base, five-shot prompt | Primary exposure set | Not exposed |
| C — fine-tuned, minimal prompt | Not exposed | Primary exposure set |
| D — fine-tuned, five-shot prompt | Primary exposure set | Primary exposure set |

All four systems may be run through every reference collection as a diagnostic control, but suspicious flags and conclusions must retain source collection and exposure status. A similarity between System A and a training response is not evidence that Stage 4 training caused copying.

## Retrieval and exact checks

For every response:

1. create one **complete-text view** by flattening fixed field labels plus title, ingredient amounts, units and names, every method step, and garnish; invalid output uses normalized complete raw text;
2. hash that same view for exact identity;
3. retrieve lexical and semantic neighbours from that same view; and
4. review the merged candidates without system identity or exposure label visible.

MiniLM's 256-wordpiece limit and truncation flag apply here too. If a response or reference is truncated, the reviewer manually inspects the complete text. No numerical similarity threshold is called memorisation.

Before production retrieval, the two frozen response-calibration packets must pass their closed record checks and place the same-task target above a deliberately structure-similar hard distractor in lexical and semantic retrieval. This is a narrow diagnostic for the frozen complete-text representation, not proof that later flags are correct.

For both lexical and semantic calibration, the target and hard distractor must be present in the top five and the target must rank above the hard distractor. This is the response-specific counterpart to the 12/12 prompt-retrieval recall gate; the two calibration populations are reported separately rather than averaged.

The reviewer records whether there is distinctive overlap in title, ingredient concepts and quantities, method progression, garnish, phrasing, and substantive answer. Generic schema labels, ordinary cocktail language, and unavoidable task wording are not suspicious by themselves. Outcomes are `no_concern`, `review_flag`, or `exact_project_response`; each includes a rationale. System and exposure identity are revealed only after blind review.

## Separate generic-collapse check

Repetition across held-out outputs is not memorisation from a reference example, but it may reveal generic collapse. Within each system, exact/lexical/semantic retrieval is run on the single complete-text view among its 60 outputs, excluding self-matches. Reviewers flag repeated titles, near-identical ingredient lists, templated methods, or the same substantive advice across meaningfully different prompts.

These within-system flags are reported separately as **output-diversity diagnostics** using the same view. They are not added to the training-response memorisation count. Response evidence uses `response-similarity-review-v1`, not prompt-overlap questions or records.

The production aggregate validator consumes the actual raw/parsed response records, actual worked-example/training reference records, every review, and generated semantic/token evidence. It recomputes the single text view, exact and lexical evidence, system exposure mapping, view hashes, and the complete MiniLM embedding inventory. Stored token diagnostics, cosine scores, ranks, and per-source retrieval unions must exactly match that recomputation. It requires one review for every retrieved or exact pair and no orphan review. An exact project-reference view must be `exact_project_response`; an exact same-system held-out view must be `generic_collapse_flag`.

## Reporting boundary

Report:

- exact matches by source collection and system;
- blind review-flag counts by system and exposure status;
- examples with reviewer rationale;
- within-output generic-collapse flags; and
- the truncation and retrieved-neighbour diagnostics.

Use language such as "suspicious overlap with a training response" or "no exact project-response reproduction detected." Do not claim that the model memorised or did not memorise its original pretraining data, and do not infer absence of memorisation merely because a top-five retriever did not flag a response.
