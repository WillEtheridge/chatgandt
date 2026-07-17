# Stage 6 Automated Full-Training Execution Plan

- **Operator:** Codex through the authenticated Runpod CLI
- **Status:** Ready; paid provisioning requires an explicit start instruction
- **Budget ceiling:** `$20` for training
- **Scientific scope:** The three already-frozen first-round candidates only

## Purpose

Run Candidates 1–3 once on one fresh GPU Pod, preserve complete evidence, retrieve it locally, and terminate the paid resource. This is an agent-operated batch procedure rather than a human copy-and-paste runbook.

## Fixed boundaries

- Execute a clean, pushed Git commit and record that commit in every report.
- Use the pinned Qwen model revision, environment lock, dataset, renderer, seed, and candidate configurations.
- Do not inspect held-out prompts or generate held-out responses.
- Do not change a candidate configuration on the Pod.
- Treat a run with inspectable model evidence as a scientific attempt.
- Rerun unchanged only when a mechanical failure produced no inspectable model evidence.
- Stop rather than exceed the `$20` training budget or broaden the experiment.

## Infrastructure policy

Use one fresh official PyTorch Pod with SSH, at least 24 GB VRAM, BF16 support, 30 GB or more working storage, and an automatic two-hour termination deadline. Prefer an available RTX 4090 or L4 at no more than `$1/hour`; if neither is available within that boundary, stop and report the capacity issue rather than selecting materially more expensive hardware.

No network volume is required because the complete result is retrieved before termination. All generated training output lives below the ignored `experiments/training/` directory, so Candidate 1 does not make the clean checkout fail before Candidates 2 and 3 begin.

## Execution sequence

1. Confirm the local execution commit is pushed, the scoped implementation is clean, Runpod authentication works, no GPU Pod is currently active, and the selected GPU's displayed rate respects the policy.
2. Create the Pod with SSH and the two-hour terminate guard; record its ID, image, GPU, displayed rate, and creation time automatically.
3. Wait for SSH readiness, then verify `nvidia-smi`, CUDA visibility, BF16 matrix execution, available disk, and the expected GPU identity.
4. Clone and detach the exact execution commit. Install the required `uv` version, run `uv sync --frozen`, place caches under `/workspace`, and download the exact pinned model revision.
5. Run the environment, model, full-training contract, candidate-input, and regression preflights. Stop before training on any failure.
6. Launch one detached sequential batch that runs Candidate 1, then Candidate 2, then Candidate 3 under unique immutable run IDs. Capture a separate log and exit status for every candidate.
7. Monitor the process, logs, GPU memory, and provider state. A disconnected local session must not terminate training.
8. For each successful run, verify canonical `report.json`, expected optimiser-step and epoch counts, finite losses, frozen-base checks, VRAM gate, checkpoint files, formal adapter identities, and exact-reload evidence.
9. Create a checksummed archive of the three run directories, retrieve it locally, verify its checksum and adapter identities again, and retain the raw evidence unchanged.
10. Delete the Pod, confirm no active GPU Pod remains, and record the provider's final charge separately from runner-attributed compute time.

## Failure handling

Mechanical recovery is deliberately narrow. Codex may retry SSH readiness, dependency or model transfer, or recreate an unavailable/broken Pod without changing the scientific configuration. CUDA incompatibility, out-of-memory failure, non-finite training, identity drift, failed clean reload, missing evidence, exhausted capacity, or projected budget breach stops the batch for diagnosis. A later candidate is not silently used to replace a failed earlier one.

## Deliverables

- three immutable run directories, including every epoch checkpoint and final adapter;
- one machine-readable report and execution log per candidate;
- verified local checksums and formal adapter identities;
- a concise infrastructure, timing, loss, VRAM, failure, and cost record; and
- the evidence needed to apply the frozen lowest-validation-loss checkpoint rule before behavioural inspection.
