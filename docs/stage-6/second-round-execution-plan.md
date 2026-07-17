# Stage 6 Second-Round Execution Plan

- **Status:** Completed 2026-07-17; all paid resources removed
- **Candidate count:** Two
- **Maximum training budget:** Existing `$20` project budget

## Goal

Train frozen Candidates 4 and 5 once each on one suitable Runpod Pod, preserve complete evidence, retrieve it locally, and remove all paid infrastructure. This is an agent-operated batch rather than a manual command-by-command runbook.

## Infrastructure boundary

Use Runpod's official PyTorch 2.8.0 template with SSH, CUDA 13 compatibility, BF16 support, at least 24 GB VRAM, at least 30 GB working storage, and an automatic two-hour termination deadline. Prefer an available RTX 4090 or L4 at no more than `$1/hour`. Do not choose a materially more expensive device without a new instruction.

Candidate 4 has 9.23 million trainable parameters but remains expected to fit the existing 24 GB class. The unchanged 80% reserved-VRAM gate decides this mechanically; a memory failure is preserved rather than followed by an unplanned configuration change.

## Batch procedure

1. Confirm no paid Runpod resources are already active and capture the starting balance.
2. Push and record the exact clean execution commit containing both frozen configurations and the verified training implementation.
3. Provision one guarded Pod from the official template and prove SSH, CUDA, BF16, GPU identity, and VRAM.
4. Clone the exact commit, install uv `0.11.28`, reproduce the frozen environment, and download/verify the pinned model.
5. Run the separate second-round verifier, both input checks, and the complete regression suite.
6. Start Candidate 4 and Candidate 5 sequentially with immutable run IDs and the provider's displayed hourly price.
7. Monitor logs, GPU state, exit codes, and storage without changing either scientific configuration.
8. Verify each report, all three epoch checkpoints, adapter provenance, frozen-base evidence, loss finiteness, VRAM gate, and exact reload.
9. Archive and transfer the complete evidence, verify its SHA-256 and both runs locally, then delete the Pod.
10. Confirm no Pods or separately billable resources remain and record the settled provider cost.

Operational logs must be written under an ignored path before the training runner captures Git state, preventing the earlier untracked-log-directory dirty flag.

## After training

Select the lowest-standard-validation-loss checkpoint within each trajectory. Transfer those two adapters to a fresh or still-verifiable inference environment and generate 20 responses: Candidate 4 and Candidate 5 on the identical ten spent-development prompts with the same minimal prompt and paired seeds.

Structurally validate first, create one identity-blinded packet for all eligible Candidate 4/5 responses, complete frozen-rubric scoring before reveal, and apply the unchanged viability gate. Candidate 3's recorded first-round result is a fixed contextual reference and is not regenerated or rescored.

If neither new candidate is viable, stop Stage 6 training. If one or both are viable, rank viable new candidates under the existing ordering, with Candidate 4 simpler than Candidate 5 only at the final tie-break.

## Execution result

Both frozen training and behavioural runs completed with intact locally verified evidence. Neither candidate was viable, so no adapter was selected and the stopping rule ended further training. Runpod was returned to zero active resources and `$0/hour`; exact results and costs are recorded in `docs/stage-6/second-round-results.md`.
