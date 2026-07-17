# Stage 7 Held-Out Evaluation Execution Plan

- **Run plan:** `heldout-evaluation-v1`
- **Run ID:** `heldout-evaluation-v1-20260717-run01`
- **Status:** Frozen before held-out generation
- **Maximum provider cost:** `$5.00`

## Purpose

Execute the already-frozen `chatgnt-evaluation-v1` protocol once. This plan adds no new scientific treatment or scoring rule. It binds the exact operational inputs needed to turn the protocol into one complete 240-attempt harness run.

## Fixed treatments

Systems A–D use `config/systems/evaluation-abcd-v1.json`. A and C use the empty minimal prompt; B and D use frozen `five-shot-v3`. A and B use the untouched base model. C and D use the unmerged Candidate 3 adapter from `full-candidate-3-v1-20260717-run01`, digest `0eef1d5da017a18f571a5e37cc152d1351bfbda9f0d343c3f376a1f68a2d4249`.

Candidate 3 remains a non-viable diagnostic treatment. The held-out result cannot select it as a product adapter, substitute another checkpoint, restart training, or alter the Stage 6 gate.

## Execution boundary

The deterministic harness projection contains the exact IDs, prompt text, and metadata from the 60 frozen held-out records. The run uses master seed `20260715`, one sampled response per system and prompt, the frozen BF16 generation profile, batch size one, and one matched CUDA device for the complete run.

The provider policy prefers one Secure Cloud RTX 4090 with at least 24 GiB advertised VRAM, host support for CUDA 13, BF16 support, and Runpod's official PyTorch template. A four-hour automatic termination guard is mandatory. Total Stage 7 provider spend may not exceed `$5.00` without new project-author approval.

Mechanical provisioning failures may be retried only before the first held-out output exists. Once generation begins, outputs are immutable. Invalid JSON, schema failures, low-quality responses, and isolated generation errors are results and are never repaired or regenerated. An identity mismatch, evidence corruption, fatal CUDA error, or projected budget breach stops the operation.

## Procedure

1. Verify the plan, frozen protocol, held-out population, quotas, system-set digest, Candidate 3 digest, judge manifest, repository identity, and complete regression suite.
2. Complete the frozen six-packet judge calibration gate and record discrepancies before production judging.
3. Provision one guarded Pod through the official template and prove SSH, CUDA 13 compatibility, BF16 matrix work, and the expected GPU identity.
4. Reproduce the exact clean project commit, install the locked environment, obtain the pinned base-model snapshot, and transfer Candidate 3 with digest verification.
5. Rerun the clean preflight and launch the single 240-attempt harness run detached under the fixed run ID.
6. Inspect completeness on the Pod. Retrieve the immutable run, compare archive and file identities, and independently inspect the local copy.
7. Remove all paid resources and verify zero Pods, volumes, endpoints, and active hourly spend.
8. Derive structural evidence and blinded packet inventories from the inspected run without rewriting raw output.
9. Complete fresh-context primary qualitative and B-versus-C pairwise judgments, the frozen response-similarity review, and the deterministic aggregate analysis.
10. Prepare the 24-response and 15-pair project-author human calibration sample as the only required human handoff.

## Completion

Stage 7 is complete only when the generation run and all automatic, primary LLM, pairwise, similarity, uncertainty, calibration, cost, and teardown evidence validate under the frozen protocol. Negative, mixed, or inconclusive results are complete results.
