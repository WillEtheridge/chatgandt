# Stage 6 Full-Training Results

- **Date:** 2026-07-17
- **Execution commit:** `b9fe5a894e4905e87c123cd38203dca542c71419`
- **Result:** All three frozen candidates passed their mechanical training gates
- **Selected checkpoints:** Candidate 1 epoch 3; Candidate 2 epoch 6; Candidate 3 epoch 3
- **Candidate selection:** Pending the frozen ten-prompt behavioural inspection

## Purpose and boundary

This batch trained the three predeclared first-round candidates on all 160 frozen training examples and measured loss on all 40 separate validation examples. It selects one checkpoint within each trajectory by the frozen lowest-validation-loss rule. It does not use held-out prompts, rank candidates by validation loss, or establish that any adapter produces acceptable ChatG&T responses.

## Execution

The successful batch ran on one Community Cloud NVIDIA GeForce RTX 4090 provisioned from Runpod's official PyTorch 2.8.0 template at `$0.34/hour`. The host exposed driver `580.126.09`, CUDA 13.0 compatibility, and 24,564 MiB VRAM. The project used its pinned Python 3.12.13 and PyTorch 2.12.1 CUDA 13.0 environment.

Before training, the exact detached commit passed real BF16 matrix execution, model and tokenizer identity checks, the Stage 6 candidate verifier, all three input checks, and the complete 128-test regression suite. Candidate runs were detached, sequential, and immutable.

## Loss and checkpoint results

All candidates began from the same baseline validation loss of `3.036822`.

| Candidate | Epoch validation losses | Selected epoch | Selected loss | Reduction from baseline |
| --- | --- | ---: | ---: | ---: |
| 1 — full-corpus anchor | `2.615171`, `2.241293`, `2.080787` | 3 | `2.080787` | 31.48% |
| 2 — exposure challenger | `2.615393`, `2.241500`, `2.080801`, `2.018080`, `1.990865`, `1.981721` | 6 | `1.981721` | 34.74% |
| 3 — capacity challenger | `2.313389`, `2.043238`, `1.966936` | 3 | `1.966936` | 35.23% |

Validation loss improved at every checkpoint, so the frozen rule selects the final epoch of every trajectory. Candidate 2's gains became progressively smaller after epoch three but did not reverse within six epochs. Candidate 3 learned the teacher-forced validation targets fastest and reached the lowest loss, but validation loss is not an across-candidate ranking criterion.

## Selected checkpoint identities

| Candidate | Adapter digest | Provenance SHA-256 |
| --- | --- | --- |
| 1 epoch 3 | `30c6709ce01cce061254fff45978be80e19cca6f32b888335feeaf1344eed5e4` | `c304fafb861be2d350e28ced935e84125117bacc820fe1e8d85d5b15a7d529e2` |
| 2 epoch 6 | `c3fdec615b09d18c0ccc1c2d6bad12e6d04eec9698afe69f012fccdef9959e0b` | `fbc9c00f3f9aeabecf440f5acd6268db8e6282eae65ac8b1fab52db1e8c4df5b` |
| 3 epoch 3 | `0eef1d5da017a18f571a5e37cc152d1351bfbda9f0d343c3f376a1f68a2d4249` | `95e23cd30675e39bd4363e0a79295067955966958fe444aca807b13c7c4252a4` |

Because every selected checkpoint is the final epoch, its behavioural adapter digest matches the corresponding final adapter. The checkpoint-specific provenance remains separately identified.

## Mechanical evidence

Every run passed the predeclared gates:

- exact clean execution commit and frozen configuration, model, dataset, and renderer identities;
- exactly 160 training and 40 gradient-free validation examples with no truncation;
- exactly 60, 120, and 60 optimiser updates respectively;
- finite losses and gradient norms;
- only the expected 1,089,536 or 2,179,072 LoRA parameters trainable;
- frozen base weights unchanged;
- initially neutral adapters and material post-training logit changes;
- formal provenance on all 12 epoch checkpoints and three final adapters;
- zero logit difference after clean final-adapter reload; and
- peak reserved VRAM of 35.60%, 35.60%, and 36.55%, below the 80% gate.

The retrieved archive SHA-256 is `9663e967baa7a5d3712138a0353fd2d93f1079a84439a5cdfa4d610e60adbeb8`. After extraction, a separate local audit reproduced every report checksum, checkpoint file checksum, provenance identity, adapter digest, step count, and selected epoch.

## Timing and cost

| Candidate | Runner wall time | Measured training time | Runner-attributed compute cost |
| --- | ---: | ---: | ---: |
| 1 | 26.87 s | 21.07 s | `$0.0025` |
| 2 | 49.84 s | 42.73 s | `$0.0047` |
| 3 | 36.49 s | 30.52 s | `$0.0034` |

The runners used 113.21 seconds in total and attributed approximately `$0.0107` to their own wall time. The complete provider session reduced the account balance by `$0.1240`, rounded to `$0.12`; that broader figure includes unsuccessful pre-runtime allocations, environment setup, downloads, preflight tests, evidence verification, and retrieval.

Runpod was verified clean after retrieval: no Pods, network volumes, or serverless endpoints remained, and the reported active spend returned to `$0/hour`.

## Provisioning recovery

Three initial direct-image allocations never progressed beyond `uptimeSeconds: 0` and produced no model evidence. They were deleted as mechanical failures. Provisioning the same image through Runpod's official `runpod-torch-v280` template produced working SSH and CUDA access without changing the experiment.

## Evidence locations

- Raw runs and adapters: `experiments/training/full-training-v1/full-candidate-*/`
- Operational logs: `experiments/training/full-training-v1/runpod-session-20260717-run01/`
- Report SHA-256 values: `c6c78ceb84dac033e1f9e10484df19ea42943a73218db8f9d8352b68c89c6f9b`, `b9a32394dcaeb67964ae0ed3189ae5bc9ab554b17996df5a20977e18a0522f5f`, and `106c10904ec29c7b4d72bd4b876ce8d36500bb844d36fdc05f9ab2ed8978c532`

## Next decision

Run the three selected checkpoints on the same frozen ten-prompt spent-development population. Apply the existing structural gate and blinded qualitative rubric, then select a candidate only under the frozen viability and ranking rules.
