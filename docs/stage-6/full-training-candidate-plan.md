# Stage 6 Full-Training Candidate Plan

- **Purpose:** Predeclare a small, interpretable adapter comparison before full-corpus GPU training
- **First-round limit:** Three configurations
- **Conditional second-round limit:** At most two additional configurations
- **Status:** Frozen before implementation and GPU execution
- **Date:** 2026-07-17

## Design rule

Each candidate represents one understandable hypothesis. Candidate 1 is the anchor. The exposure challenger and capacity challenger will each differ from the anchor in one conceptual way. The frozen training and validation data, model, tokenizer, renderer, loss mask, generation settings, behavioural contract, and held-out boundary remain unchanged.

Infrastructure failures that produce no inspectable model evidence may be rerun unchanged under a new run ID. A configuration whose validation or generated behaviour is inspected counts as a scientific candidate.

## Candidate 1 — full-corpus anchor

### Question

Was the pilot behaviourally insufficient primarily because it used only 40 training examples and 15 optimiser updates?

### Configuration

| Setting | Value |
| --- | ---: |
| Training examples | 160 |
| Validation examples | 40 |
| Epochs | 3 |
| Micro-batch size | 2 |
| Gradient accumulation | 4 |
| Effective batch size | 8 |
| Optimiser updates per epoch | 20 |
| Total optimiser updates | 60 |
| LoRA rank | 8 |
| LoRA alpha | 16 |
| LoRA targets | `q_proj`, `v_proj` |
| LoRA dropout | 0.05 |
| Learning rate | `2e-4` |
| Weight decay | 0.01 |
| Maximum gradient norm | 1.0 |
| Precision | BF16 |
| Maximum sequence length | 512 |
| Seed | `20260715` |

The runner uses assistant-only loss, forbids truncation, measures baseline and per-epoch validation loss without gradient updates, and saves one provenance-bound checkpoint after every epoch.

### Interpretation

Candidate 1 changes only the amount and breadth of supervised exposure relative to the pilot. It uses all four times as many unique training examples and produces 60 rather than 15 optimiser updates while preserving the pilot recipe. It is the necessary reference for determining whether stronger candidates add value beyond simply using the complete planned corpus.

## Candidate 2 — exposure challenger

### Question

Is the complete training corpus sufficient, but does the desired behaviour require more repeated exposure to overcome the base model's ordinary-prose tendency?

### Configuration

Candidate 2 is identical to Candidate 1 except for training duration:

| Setting | Candidate 1 | Candidate 2 |
| --- | ---: | ---: |
| Epochs | 3 | 6 |
| Optimiser updates per epoch | 20 | 20 |
| Total optimiser updates | 60 | 120 |

All 160 training examples therefore appear six times. The runner measures validation loss and saves an adapter checkpoint after every epoch, allowing later deterioration to remain visible rather than reporting only the endpoint.

### Interpretation

Candidate 2 cleanly doubles exposure while preserving the dataset, LoRA capacity and targets, learning rate, batch shape, optimiser, regularisation, precision, sequence limit, loss mask, and seed. Improvement over Candidate 1 can therefore be attributed to additional repeated training under this recipe. Falling training loss accompanied by rising validation loss or worsening permitted behavioural evidence would indicate overfitting rather than useful added exposure.

## Candidate 3 — capacity challenger

### Question

Was the pilot adapter attached too narrowly to exert enough control over complete generated behaviour?

### Configuration

Candidate 3 is identical to Candidate 1 except for the LoRA target surface:

| Setting | Candidate 1 | Candidate 3 |
| --- | --- | --- |
| Epochs | 3 | 3 |
| LoRA rank | 8 | 8 |
| LoRA alpha | 16 | 16 |
| Target modules | `q_proj`, `v_proj` | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| Approximate trainable parameters | 1.09 million | 2.18 million |
| Total optimiser updates | 60 | 60 |

All other data, optimisation, regularisation, precision, batching, masking, sequence, checkpoint, and seed settings remain unchanged.

### Interpretation

Candidate 3 approximately doubles trainable capacity by extending rank-8 LoRA across the complete attention projection set rather than increasing rank inside the existing two modules. It tests target-surface breadth while avoiding the much larger intervention of adding feed-forward projections. Improvement over Candidate 1 can therefore be interpreted as evidence that broader attention control adds value beyond the anchor's `q_proj`/`v_proj` placement.

## Stopping policy

If at least one first-round candidate is viable, select under the frozen rule and stop training. If none is viable, classify the shared failure before proposing another run.

A second round is permitted only when the first round identifies a specific, addressable cause. It may contain at most two configurations, both frozen before either runs and each tied to a written hypothesis. If neither is viable, stop training and report the result or explicitly reframe the system claim. Do not continue adapting configurations against validation evidence.

Mechanical recovery of an unchanged configuration does not consume the scientific-candidate limit when the failed run produced no inspectable model evidence.

## Checkpoint selection

Each training configuration saves and measures one checkpoint after every epoch. Represent each candidate with its mechanically valid checkpoint having the lowest complete-validation loss. If multiple checkpoints have exactly equal loss, choose the earliest epoch.

Validation loss chooses within one fixed training trajectory; it does not rank the three represented candidates against one another. No generated held-out response contributes to checkpoint selection.

## Behavioural inspection

Run the selected checkpoint from each candidate on the same frozen ten-prompt pilot-behaviour population with the minimal prompt, frozen generation settings, and paired per-prompt seeds. This produces 30 immutable responses.

Apply the frozen structural validator first. Blind candidate identity while scoring every schema-valid response on underlying-answer quality, metaphorical coherence, and recipe-style execution. Invalid responses receive no qualitative score and cannot pass jointly.

## Viability gate

A candidate is viable only when it satisfies all three non-compensatory population requirements:

1. at least eight of ten responses are schema-valid;
2. at least seven of ten responses receive a full joint pass; and
3. every intent family contains at least one full joint pass across its two prompts.

These are engineering go/no-go thresholds for the bounded diagnostic population, not confidence-qualified estimates of true deployment rates.

## Candidate ranking

If exactly one candidate is viable, select it. If several are viable, rank them lexicographically by:

1. higher full joint-pass count;
2. higher schema-valid count;
3. higher total qualitative score across resolved eligible responses;
4. lower average inference latency;
5. lower average generated-token count; and
6. simpler configuration in the fixed order Candidate 1, Candidate 2, Candidate 3.

Validation loss is not an across-candidate ranking criterion because the user-facing objective is generated behaviour. Simplicity is used only after the behavioural and operational evidence ties.

If no candidate passes the complete viability gate, select none. Record the common failure, loss trajectories, and relative movement before deciding whether the bounded second round has a specific hypothesis to test.
