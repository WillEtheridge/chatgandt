# Stage 6 Second-Round Results

- **Date:** 2026-07-17
- **Execution commit:** `c313c5dc47c97c55c2fbb95c6b716a78e6a9d218`
- **Population:** the same ten frozen spent-development prompts used in the first round
- **Result:** neither second-round candidate met the unchanged viability gate
- **Selected adapter:** none
- **Held-out prompts used:** none

## What was run

Candidate 4 extended rank-8 LoRA across all attention and MLP projections, giving 9,232,384 trainable parameters. Candidate 5 retained Candidate 3's attention-wide 2,179,072-parameter adapter and doubled training weight only for tokens overlapping ingredient-name and method-string contents. Both used the same frozen 160-example training split, 40-example validation split, three epochs, 60 optimiser updates, seed, optimiser, learning rate, batch shape, and base model.

Both candidates trained once from the exact clean execution commit. Standard unweighted assistant-only validation loss selected epoch 3 in both trajectories. The selected checkpoints then answered the same ten spent-development prompts through separate adapted-only system-C harness processes with the frozen minimal prompt, generation settings, run seed `20260715`, and paired per-prompt seeds.

All 20 scheduled generations completed. Structural validation preceded qualitative review. The 18 schema-valid responses were shuffled into one identity-blinded packet and scored against the unchanged rubric before the identity mapping was opened.

Both generation manifests recorded `git_dirty: true` because the controller created its untracked operational-log directory beneath `experiments/runs/` immediately before each harness captured repository state. No source or configuration file changed. A post-retrieval audit compared every recorded behaviour file byte-for-byte with commit `c313c5dc47c97c55c2fbb95c6b716a78e6a9d218`; all matched, and both manifests recorded behaviour digest `a0ab38a39f15d204142df24baa5bb0564c38adf51ffbfb530a3a8b501f766944`. The first immutable outputs were retained rather than repeated after inspection for a cosmetic metadata correction.

## Training evidence

Both runs began from the same baseline validation loss of `3.036822` and passed every mechanical gate.

| Candidate | Epoch validation losses | Selected epoch | Selected loss | Peak reserved VRAM | Runner wall time |
| --- | --- | ---: | ---: | ---: | ---: |
| 4 — all-linear LoRA | `2.042355`, `1.919299`, `1.900072` | 3 | `1.900072` | 40.36% | 48.71 s |
| 5 — content-weighted loss | `2.365935`, `2.045509`, `1.968187` | 3 | `1.968187` | 35.96% | 36.21 s |

For both candidates:

- exactly 160 training and 40 validation examples were used with no truncation;
- exactly 60 optimiser updates completed with finite losses and gradients;
- only the expected LoRA parameters were trainable;
- frozen base weights remained unchanged;
- the initially neutral adapter produced a material post-training logit change;
- three complete provenance-bound epoch checkpoints and one final adapter were saved; and
- a clean final-adapter reload reproduced logits exactly.

Candidate 4's selected/final adapter digest is `7528dba56c6ac7d639c816052d45ba082e25a4f7bde349f6e1060ff14890d57f`. Candidate 5's is `75873c36e75629042f215e8d8d13d8c231165f75272069d45072323d461cecc7`.

## Behavioural gate

| Candidate | Schema valid | Joint passes | Families represented | Qualitative score total | Mean latency | Mean generated tokens | Viable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 4 — all-linear LoRA | 9/10 | 6/10 | 4/5 | 56 | 4625.91 ms | 173.8 | No |
| 5 — content-weighted loss | 9/10 | 4/10 | 3/5 | 49 | 3644.66 ms | 167.6 | No |

Viability still required at least 8/10 schema-valid responses, at least 7/10 full joint passes, and at least one full joint pass in every intent family. Both candidates passed only the structural threshold.

Each candidate produced one valid JSON object with only one method step, below the required two-to-five range. Candidate 4's six qualitative passes covered emotional support, advice, creative work, and technical explanation, but neither short-form transformation passed. Its failures included assuming `9` meant `9:00 AM`, recommending a weekly club for a highly variable schedule, and evading the forbidden word `fix` with `fixed`. Candidate 5 additionally failed the indoor-event requirement, practical comparison, and basic headphone troubleshooting, while its exact support-note transformation did pass.

## Interpretation

Candidate 4 reached a lower validation loss than Candidate 3 (`1.900072` versus `1.966936`) but did not improve its 6/10 joint-pass count. It also moved from Candidate 3's 10/10 structure and five-family coverage to 9/10 and four families. Within this bounded experiment, extending LoRA into MLP projections did not resolve the content-selection and exact-constraint bottleneck.

Candidate 5's standard validation loss finished close to Candidate 3, but its behavioural result fell to 4/10 joint passes. Weighting answer-bearing token locations is not the same as teaching those tokens to contain a better decision, correct fact, or honoured constraint. The intervention increased the contribution of content tokens without providing a direct signal for substantive correctness.

The second round therefore does not support either hypothesis strongly enough to select an adapter. Under the predeclared three-plus-two stopping policy, Stage 6 training ends here. No sixth configuration, relaxed gate, added prompt, or held-out inspection is permitted as a continuation of this search.

## Infrastructure, evidence, and cost

The first secure-cloud RTX 4090 allocation was deleted before model work when the environment preflight found a CUDA-12.8 driver beneath the frozen CUDA-13 runtime. An unchanged retry using Runpod's explicit minimum-CUDA-13 requirement produced a secure RTX 4090 with driver `580.159.04`; both training runs completed there at `$0.69/hour`. The behavioural runs used a fresh secure L4 with the same driver at `$0.39/hour`.

The two training runners attributed `$0.0163` to their combined wall time. After delayed billing settled, the complete provider cost was approximately `$0.45`: `$0.20` for the failed preflight plus successful training session, and `$0.25` for the separate behavioural session. Setup, locked dependency transfer, model hashing/loading, adapter transfer, audits, and retrieval dominated the provider bill.

All evidence was checksummed, retrieved, and independently verified locally before each Pod was deleted. Runpod then reported no Pods, network volumes, or endpoints and `$0/hour` active spend.

- Training archive SHA-256: `0ab48012ce782a41d0a6a14d5a242bf7234162d1cbd1b41907a821b5a6b164a7`
- Behaviour archive SHA-256: `46ceb3af0540dae9487a623dfe02f15c5a030fee27ed09d48fb42d14f95f6392`
- Candidate 4 report SHA-256: `444e69794f1cf2b9cc4ecf0befe3cb5409ba19913b2cd6f664e27707a0672691`
- Candidate 5 report SHA-256: `fcdf64d39ede798cfe06c44b9623ed9166eb7714d0e4a530215e7e3f006a5a9e`
- Raw training runs: `experiments/training/full-training-second-round-v1/`
- Generation runs: `experiments/runs/second-round-candidate-*-behaviour-v1-20260717-run01/`
- Structural evaluations: `experiments/evaluations/second-round-candidate-*-behaviour-v1-20260717-run01-structure/`
- Blind evidence: `experiments/evaluations/full-training-second-round-v1-20260717-blind-scoring/`
- Mechanical selection: `experiments/evaluations/full-training-second-round-v1-20260717-selection.json`

## Stage 7 disposition

D-075 freezes Candidate 3 as the sole adapted treatment in the original Stage 7 two-by-two evaluation. This is a diagnostic use, not a reversal of the Stage 6 no-winner decision: Candidate 3 remains below the product viability gate, and held-out evidence cannot select a replacement, restart tuning, or rescue it. The final analysis must report both facts together.
