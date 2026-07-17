# Stage 6 Pilot Training Results

- **Run ID:** `pilot-training-v1-20260717-run01`
- **Configuration:** `chatgnt-pilot-training-v1`
- **Execution commit:** `81b586df35f45f6acd5145f3bb96b5ebe9f81840`
- **Date:** 2026-07-17
- **Result:** Pass

## Purpose and boundary

This run exercised the complete supervised LoRA pipeline on the frozen 40-example training-only pilot and measured loss on the separate 40-example validation split. It was a mechanical rehearsal and early learning-signal check, not a final adapter-selection run.

The run did not access held-out prompts, compare final systems, establish response quality, or author or revise supervised examples.

## Recorded result

| Measure | Result |
| --- | ---: |
| Baseline validation loss | 3.0364 |
| Validation loss after epoch 1 | 2.9436 |
| Validation loss after epoch 2 | 2.8331 |
| Validation loss after epoch 3 | 2.7339 |
| Baseline-to-final validation-loss reduction | 10.0% |
| Mean training loss, epoch 1 | 2.9995 |
| Mean training loss, epoch 2 | 2.8792 |
| Mean training loss, epoch 3 | 2.7596 |
| Optimiser updates | 15 |
| Measured training time | 7.08 seconds |
| Complete runner wall time | 15.04 seconds |
| Input throughput | 3,900 tokens/second |
| Peak reserved GPU-memory fraction | 42.1% |
| Trainable LoRA parameters | 1,089,536 |

The baseline and every epoch used all 7,802 supervised validation prediction tokens. All 40 pilot examples appeared exactly once per epoch in a distinct deterministic order, and no pilot or validation example was truncated.

## Mechanical evidence

The run satisfied every frozen pass gate:

- the repository was clean at the expected execution commit;
- the pinned model, tokenizer, dataset, renderer, and configuration identities matched;
- CUDA BF16 training ran on an NVIDIA GeForce RTX 3090;
- all losses and gradient norms were finite across exactly 15 optimiser updates;
- only the LoRA parameters were trainable and the frozen base remained unchanged;
- three epoch checkpoints and the final adapter were saved;
- the trained adapter materially changed the spent-development probe logits;
- loading a clean base model with the saved adapter reproduced the final logits exactly; and
- peak reserved VRAM remained well below the 80% gate.

An independent local inspection confirmed that the returned report is canonical JSON, the frozen dataset hashes still match its recorded identities, all three epoch schedules contain the same 40 unique examples in different orders, and the adapter digest and provenance hash reproduce exactly.

## Interpretation

The monotonic validation-loss reduction is encouraging early evidence that the adapter learned a pattern which transferred beyond the 40 pilot examples. Training and validation loss both improved through epoch 3, so this short run shows no loss-based sign of overfitting.

This does **not** establish that generated responses are valid JSON, useful answers, coherent metaphors, or convincing cocktail recipes. Loss measures target-token prediction, not the project's human-facing success criteria. Behaviour must therefore be inspected separately before the final candidate configurations are frozen.

## Cost record

At the displayed compute rate of `$0.46/hour`, the report attributes approximately `$0.0019` to its 15-second measured wall time. This is not the complete Runpod session charge. The actual rental charge remains to be supplied from the provider billing record.

## Evidence locations

- Machine-readable report: `experiments/training/pilot-training-v1-20260717-run01/report.json`
- Final adapter: `experiments/training/pilot-training-v1-20260717-run01/adapter/`
- Epoch checkpoints: `experiments/training/pilot-training-v1-20260717-run01/checkpoints/`
