# Stage 6 Second-Round Candidate Plan

- **Purpose:** Test the two specific causes supported by the first-round behavioural diagnosis
- **Candidate limit:** Two; no further training candidates are permitted under the current Stage 6 plan
- **Status:** Frozen before GPU execution
- **Date:** 2026-07-17

## Evidence behind the round

Candidate 3 reached 10/10 structural validity, 10/10 metaphorical-coherence passes, and 10/10 recipe-style passes, but only 6/10 full joint passes. Its remaining failures were substantive: invented facts, a poor decision, an exact constraint violation, and a misleading technical conclusion. Candidate 2 showed that doubling repeated exposure did not resolve the same broad weaknesses, while Candidate 3 showed that broadening LoRA's target surface improved every aggregate behavioural measure.

The second round therefore tests target reach and learning-signal allocation. It does not change the frozen data, base model, prompt, generation settings, evaluation population, rubric, viability gate, checkpoint rule, or held-out boundary.

## Shared configuration

Both candidates use the complete frozen 160-example training split, separate 40-example validation split, three epochs, 60 optimiser updates, BF16, maximum sequence length 512, micro-batches of two, four-way gradient accumulation, AdamW at `2e-4`, weight decay 0.01, maximum gradient norm 1.0, LoRA rank 8, alpha 16, dropout 0.05, and seed `20260715`.

Validation remains ordinary assistant-only token loss without content weights. Checkpoints are saved after every epoch and selected within each trajectory using the unchanged lowest-complete-validation-loss rule.

## Candidate 4 — target-reach challenger

### Hypothesis

Substantive content selection depends on representations outside the attention projections, so adapting all linear attention and feed-forward projections will improve usefulness and constraint adherence while retaining Candidate 3's structural reliability.

### Intervention

Candidate 4 is identical to Candidate 3 except for LoRA targets:

| Setting | Candidate 3 | Candidate 4 |
| --- | --- | --- |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj` | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| Trainable parameters | 2,179,072 | 9,232,384 |
| Training loss | Standard assistant-only | Standard assistant-only |

This is an all-linear rank-8 intervention, not a rank increase. Its higher memory use must still pass the existing 80% reserved-VRAM gate.

## Candidate 5 — learning-signal challenger

### Hypothesis

Candidate 3 learned repeated JSON and recipe patterns faster than unique substantive content because every supervised token contributed equally. Increasing the relative training weight of answer-bearing text will improve usefulness and constraint adherence without changing adapter capacity.

### Intervention

Candidate 5 preserves Candidate 3's target modules and complete optimisation configuration. During training only:

- every supervised assistant token begins with weight `1.0`;
- tokens overlapping the JSON string contents of each `ingredients[*].name` receive weight `2.0`;
- tokens overlapping the JSON string contents of each `method[*]` receive weight `2.0`;
- title, garnish, keys, punctuation, amounts, units, assistant terminal tokens, prompt tokens, and padding receive no increased weight;
- prompt and padding tokens remain excluded entirely; and
- weighted cross-entropy is normalised by the sum of active weights, preserving loss scale.

A token that overlaps any weighted content span receives weight `2.0`, including a token that also contains an adjacent quote or escape character. Token-to-character alignment must reproduce the exact canonical assistant JSON or input validation fails. Validation loss remains the ordinary unweighted assistant-only loss so checkpoint selection retains its existing meaning.

## Selection and stopping

Select the lowest-validation-loss checkpoint within each trajectory. Then run Candidates 4 and 5, alongside Candidate 3 as the unchanged first-round reference, on the identical ten spent-development prompts using the existing minimal-prompt harness and paired seeds. Candidate 3 is not retrained.

Apply the unchanged structural validator and blinded three-dimension scoring process. A new candidate is viable only with at least 8/10 schema-valid responses, at least 7/10 full joint passes, and at least one full joint pass in every intent family.

If one or both new candidates are viable, rank all viable Candidates 3–5 under the existing behavioural, operational, and simplicity ordering, with simplicity ordered Candidate 3, Candidate 4, Candidate 5. Candidate 3 remains non-viable under its recorded 6/10 result unless the threshold is improperly changed; it is included only as an unchanged reference.

If neither Candidate 4 nor Candidate 5 is viable, stop training. Report that the bounded SFT/LoRA search did not produce an adapter meeting the predeclared development gate. Do not add a sixth configuration, revise the ten prompts, or use held-out responses to continue tuning.

## Execution boundary

Configuration, implementation, local verification, and an execution plan may be prepared now. Provisioning paid infrastructure and starting either training run require a separate explicit instruction. Both candidate definitions must remain byte-frozen before either GPU run begins.
