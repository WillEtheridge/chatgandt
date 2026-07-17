# Rented-GPU Feasibility Check

This record reconciles the planned Runpod configuration with the executable feasibility check completed on 2026-07-14. The raw machine-readable report and diagnostic adapter are retained locally beneath the ignored `artifacts/diagnostics/` directory.

## Question tested

Can the pinned Qwen2.5-1.5B-Instruct weights complete a representative unquantised BF16 LoRA training workload on a single 24 GB NVIDIA GPU using the project's exact locked environment, while retaining at least 20% VRAM headroom?

This was an infrastructure and compatibility test, not a ChatG&T fine-tune or a training-quality experiment.

## Availability and driver findings

The planned Secure Cloud RTX 4090 was unavailable. An initial 24 GB L4 Pod exposed driver `570.195.03` and CUDA 12.8 support. The project lock contains PyTorch's CUDA 13.0 build, for which NVIDIA requires an R580-or-newer driver, so the Pod was terminated before downloading the environment.

The cheapest immediately available CUDA 13 machine was temporarily a 96 GB RTX PRO 6000 at $1.99/hour. It was rejected because it would pay for unnecessary capacity and would not directly test the agreed 24 GB constraint.

The successful substitute was an RTX 3090 with exactly 24 GB advertised VRAM and an R580 driver. This followed the fallback already allowed by D-017: use another BF16-capable 24 GB NVIDIA device when the preferred RTX 4090 is unavailable.

The failed L4 allocation was a useful compatibility result. A GPU model and VRAM total do not establish whether the host driver can run the CUDA runtime bundled with a locked PyTorch build.

## Successful environment

| Property | Observed value |
| --- | --- |
| Provider | Runpod |
| GPU | NVIDIA GeForce RTX 3090 |
| Compute capability | 8.6 |
| Advertised VRAM | 24,576 MiB |
| PyTorch-visible VRAM | 23.5588 GiB |
| NVIDIA driver | 580.159.03 |
| Driver-advertised CUDA | 13.0 |
| Python | 3.12.13 |
| PyTorch | 2.12.1+cu130 |
| Transformers | 5.12.1 |
| PEFT | 0.19.1 |
| Accelerate | 1.14.0 |
| BF16 support | yes |

The official Runpod PyTorch template provided the container and SSH layer. Its preinstalled Python packages were not used as the project environment. `uv sync --frozen` reproduced the project-local environment, and the exact model commit and local weight checksum were verified before the GPU diagnostic ran.

## Representative workload

| Setting | Value |
| --- | --- |
| Sequence length | 512 tokens |
| Micro-batch size | 2 |
| Tokens per step | 1,024 |
| Optimizer steps | 3 |
| Gradient checkpointing | disabled |
| Quantisation | none |
| Base-weight dtype | BF16 |
| LoRA target modules | `q_proj`, `v_proj` |
| LoRA rank / alpha | 8 / 16 |
| Trainable parameters | 1,089,536 |

The input was a deliberately long synthetic ChatG&T-shaped response. It exercised an upper-bound sequence allocation without consuming project training or held-out evaluation data.

## Memory result

| Measurement | Result |
| --- | ---: |
| Allocated before training | 3.1003 GB |
| Peak allocated | 7.2535 GiB |
| Peak reserved | 7.9336 GiB |
| Peak reserved fraction | 33.6757% |
| Remaining fraction | 66.3243% |
| Maximum accepted fraction | 80% |
| Headroom gate | pass |

The representative workload used roughly one third of the available device memory without quantisation or gradient checkpointing. This provides substantial room for ordinary allocator variation and later batch or sequence decisions. It confirms that QLoRA is not required by the current model and hardware plan.

## Training-path result

The three disposable losses were:

```text
0.579144 → 0.511147 → 0.443479
```

The decline only shows that the repeated synthetic batch could be optimized; it is not evidence of generalisation or ChatG&T quality.

Step times were `0.691162`, `0.175955`, and `0.158259` seconds. The first step includes one-time initialization work, so this three-step diagnostic is too short to serve as a full training-duration benchmark. Across the recorded steps, measured throughput was approximately 2,996 tokens per second.

## Integrity and round-trip result

- The untrained adapter's complete next-token logit vector matched the base model exactly.
- No frozen base tensor received a gradient.
- No frozen base tensor version counter changed.
- Optimization changed the model distribution relative to the base model.
- The saved adapter was 4,379,306 bytes.
- A clean base model plus the reloaded adapter reproduced the pre-save logits exactly.

The complete GPU lifecycle therefore passed:

```text
reproduce → load → attach → train → measure → save → reload → reproduce
```

## Cost result

| Cost | Observed value |
| --- | ---: |
| RTX 3090 compute rate | $0.46/hour |
| 30 GB container-storage rate | $0.004/hour |
| Displayed combined rate | $0.46/hour after rounding |
| Final Runpod charge | $0.14 |
| Agreed one-off training budget | $20.00 |

The feasibility session consumed 0.7% of the agreed training budget. All evidence was copied locally and verified before the Pod and remaining storage were removed.

## Raw-report reconciliation

The raw report still contains the planned RTX 4090 and $0.69/hour fields because that configuration was transferred to the Pod before live availability forced the fallback. The same report independently captured the actual GPU, driver, memory, CUDA build, and timing from the running machine. This document preserves both facts instead of rewriting the raw evidence after the event.

`config/gpu-feasibility.toml` now identifies the successful RTX 3090 and $0.46/hour rate for a deliberate rerun. The final $0.14 charge remains an outcome in this record rather than a reusable configuration value.

## Local evidence

| Artefact | SHA-256 |
| --- | --- |
| Raw JSON report | `5236a676ace4a28888f5c43e201c35ff7e9f124d8b3216dfe30267b1db696375` |
| Adapter Safetensors | `46be746fc63ed3dca1623c183df18c14a51453326786817f239640b7c9d92523` |

These diagnostic artefacts are intentionally ignored by source control. The durable project record is this document plus the scripts, immutable model selection, locked environment, and recorded checksums.

## Conclusion

The selected model and standard BF16 LoRA approach are technically feasible on inexpensive rented 24 GB NVIDIA hardware. The model decision no longer has an outstanding executable-compatibility contingency, and Stage 2's model-feasibility step is complete.
