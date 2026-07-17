# Stage 6 Pilot Training Specification

- **Configuration:** `chatgnt-pilot-training-v1`
- **Purpose:** Prove the complete supervised LoRA training pipeline on the frozen 40-example pilot
- **Status:** Frozen before GPU execution
- **Date:** 2026-07-16

## What this run is for

The pilot is a pipeline rehearsal, not a contest to find the best adapter. It must show that the frozen records become the intended Qwen tokens and loss mask, LoRA updates only adapter parameters on CUDA, validation loss can be measured without updates, checkpoints survive save and reload, and the evidence needed to explain the run is retained.

It does not use held-out prompts, establish final quality, compare multiple hyperparameters, or author new training examples.

## Frozen shape

| Setting | Value | Reason |
| --- | ---: | --- |
| Training records | 40 | Frozen training-only pilot, eight per intent family |
| Validation records | 40 | Complete frozen validation split; loss only, with no gradient updates |
| Precision | BF16 | Already verified on a 24 GB GPU; quantisation is unnecessary |
| Maximum sequence length | 512 | Longest pilot record is 321 tokens; truncation is forbidden |
| LoRA targets | `q_proj`, `v_proj` | Small, previously verified adapter surface |
| LoRA rank / alpha | 8 / 16 | Reuses the feasible adapter capacity without expanding the pilot into a search |
| LoRA dropout | 0.05 | Modest regularisation for the small supervised corpus |
| Learning rate | `2e-4` | Conservative LoRA starting point, materially below the disposable `1e-3` infrastructure diagnostic |
| Epochs | 3 | Exposes every pilot record three times without using a long rehearsal to optimise quality |
| Micro-batch | 2 | Previously measured with substantial 24 GB headroom |
| Gradient accumulation | 4 | Effective batch size 8 while retaining the measured micro-batch footprint |
| Optimiser | AdamW | Simple established baseline |
| Weight decay | 0.01 | Small fixed regularisation |
| Maximum gradient norm | 1.0 | Guard against unstable updates |
| Seed | `20260715` | Reuses the project experiment seed |

Forty examples produce 20 micro-batches per epoch. Four-way accumulation produces five optimiser steps per epoch and exactly 15 across the run. The learning rate is constant; a 15-step pilot does not justify scheduler complexity.

## Rendering and loss boundary

Each accepted record is rendered as an empty system message, the stored user input, and the canonical compact JSON assistant target. Qwen's pinned chat template renders both the prompt-only and complete message sequences. The prompt must be an exact token prefix of the complete example.

Every prompt token and padding token receives label `-100`. Only assistant-response and assistant-termination tokens contribute to causal-language-model loss. Any record longer than 512 tokens fails preflight rather than being truncated.

## Pass gates

The pilot passes as a pipeline rehearsal only when:

- the exact frozen dataset, tokenizer, model, configuration, and Git identities match;
- the checkout is clean and CUDA BF16 is available;
- all 40 pilot and 40 validation records render without truncation;
- exactly 15 optimiser steps complete with finite loss and gradients;
- only LoRA parameters are trainable and the frozen base remains unchanged;
- baseline and per-epoch validation loss are recorded without gradients;
- one adapter checkpoint is saved after every epoch;
- the final adapter changes a spent-development probe's logits;
- a clean base plus saved adapter reproduces the final logits exactly;
- peak reserved VRAM is no more than 80% of the device; and
- the complete report and adapter provenance are written under one immutable run ID.

Loss is evidence, not an automatic quality verdict. A noisy or non-monotonic curve can still accompany a mechanically valid pilot; it must be interpreted before defining the final candidate configurations.

## Stop conditions

Stop without changing the Pod when an identity check fails, any example would be truncated, CUDA or BF16 is unavailable, loss or gradient norm becomes non-finite, a base parameter changes, memory crosses the gate, a checkpoint cannot reload, or the intended run directory already exists. A fix is made locally and receives a new committed version and run ID.

No held-out file is read by the configuration or runner.
