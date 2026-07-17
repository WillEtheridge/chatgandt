# Stage 6 Second-Round Implementation Check

- **Date:** 2026-07-17
- **Status:** Local verification passed; GPU execution not started
- **Candidates:** 4 and 5

## What was verified

The second round reuses the proven Stage 6 training core. Candidate 4 requires only a different frozen LoRA target list. Candidate 5 adds deterministic per-token training weights while leaving the model, adapter capacity, data, batching, optimiser, epochs, prompt masking, padding masking, and validation loss unchanged.

The separate verifier established:

- Candidate 4 differs from Candidate 3 only in target surface and operational identity;
- Candidate 5 differs from Candidate 3 only in its training-loss rule and operational identity;
- both use exactly 160 frozen training and 40 frozen validation examples;
- both perform 80 micro-batches and 20 optimiser updates per epoch, 60 updates total;
- Candidate 4 exposes exactly 9,232,384 trainable LoRA parameters on the pinned model;
- Candidate 5 exposes the same 2,179,072 trainable parameters as Candidate 3;
- Candidate 5 maps canonical JSON string spans to tokens across all 160 training examples;
- 18,600 tokens per epoch receive content weight 2, with a per-example range of 50–185;
- prompt and padding positions retain zero loss weight;
- validation examples contain no custom weights and retain standard assistant-only loss;
- the weighted cross-entropy implementation matches an independently calculated toy result and produces finite gradients; and
- the complete historical 128-test regression suite still passes unchanged.

## Frozen configuration identities

| Candidate | Configuration SHA-256 |
| --- | --- |
| 4 | `17900f4797d68e3f53d8b3d2ba2fbc84eaba3e18b0179b8cfc0030ef5d61bf0b` |
| 5 | `3b16dbed50afc1b68373a00fe1f9046cc08bdb36a9818643e1f6b8c7fd866acb` |

## Canonical local commands

```bash
uv run --frozen python scripts/run_second_round_training.py --candidate all --check-inputs
uv run --frozen python scripts/verify_second_round_training.py --model-capacity
uv run --frozen python -m unittest discover -s tests
```

These checks prove configuration, input, masking, weighting, capacity, and regression compatibility. They do not prove CUDA optimisation, VRAM headroom, saved-checkpoint reload, or improved generated behaviour; those remain execution evidence.
