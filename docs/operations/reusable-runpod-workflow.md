# Reusable Runpod Development Workflow

- **Prepared:** 2026-07-15
- **Status:** Adopted for future prompt-development and training iterations

## Purpose

Reuse one suitable Runpod Pod across nearby development runs without weakening the identity, integrity, or cost controls applied to each experiment.

A fresh physical Pod is not an experimental requirement. Reproducibility comes from verifying and recording the model, code, dependencies, configuration, prompts, seeds, hardware, and raw evidence for every run.

## Storage boundary

Provision the Pod with a volume disk mounted at `/workspace`. Keep all state that must survive a stop beneath that mount, including:

- `/workspace/chatgnt` for the repository;
- `/workspace/.cache/uv` for the uv cache; and
- `/workspace/.cache/huggingface` for the pinned model cache.

Treat the container disk as disposable. Runpod clears it when a Pod is stopped, whereas the volume disk remains available for the life of the Pod.

The persistent workspace is a convenience cache, not the authoritative copy of experimental evidence. Every completed or partial run must still be copied home and verified before the Pod is stopped or terminated.

## First session on a Pod

1. Record the Pod ID, region, template and image tag, GPU, VRAM, driver, storage allocation, and displayed rates.
2. Verify CUDA and BF16 on the selected device.
3. Clone the repository beneath `/workspace` and check out the exact authorised commit.
4. Reproduce the locked environment and download the pinned model beneath `/workspace`.
5. Run the complete project and run-specific preflight.
6. Execute only the frozen run configuration with its unique run ID.

The exact commands, expected results, stop conditions, and evidence checks remain in the applicable run-specific runbook.

## End of every run

1. Inspect structural completeness without judging individual answers.
2. Print hashes for the immutable run files.
3. Copy the complete run directory to the local repository.
4. Run the local inspector and compare the Pod and local hashes.
5. Record the current charge and rates.
6. If retaining the Pod, move the verified Pod copy out of the Git checkout into `/workspace/run-archive/<run-id>` so the next session can begin from a clean working tree.
7. Stop or terminate the Pod according to the rule below.

Never retain the only copy of evidence on a stopped Pod.

## Stop versus terminate

**Stop the Pod** when another authorised run is reasonably expected soon and retaining the environment will save meaningful setup time. Stopping ends GPU compute billing but leaves the volume disk billable. Record the stopped-storage rate and set a reminder to review the Pod daily.

**Terminate the Pod** when:

- prompt development or the current training cycle has ended;
- no next run is prepared;
- the next run is not expected soon enough to justify storage cost;
- the GPU, driver, filesystem, or environment is no longer suitable; or
- the workspace has become difficult to verify confidently.

Before termination, verify that every required result exists locally. Delete any separately billable volume that is no longer needed and confirm that no unintended resource remains billable.

## Resuming the same Pod

After restarting:

1. Record the new session start time and current displayed rates.
2. Run `nvidia-smi` and the BF16 CUDA smoke check again.
3. Fetch the repository and check out the exact new authorised commit in detached mode.
4. Confirm the working tree is clean before the harness creates a new run directory.
5. Run `uv sync --frozen` and all model, prompt, system, run-plan, and schedule identity checks.
6. Confirm the proposed run ID has never been used.
7. Execute the run and preserve its evidence using the same end-of-run procedure.

Do not treat a previously successful session as proof that the restarted session is unchanged. Cached dependencies and model files reduce setup time; their pinned identities must still pass verification.

## Experimental boundary

Reusing a Pod does not authorise prompt edits, dependency changes, retries, repairs, precision substitutions, or configuration changes on the rented machine. Those changes are developed and reviewed locally, committed as a new immutable version, and then checked out on the Pod.

Every run retains its own:

- unique run ID and immutable directory;
- repository and behaviour identity;
- prompt, system, configuration, model, and dependency identities;
- schedule and seed record;
- hardware and timing metadata;
- raw responses and integrity evidence; and
- billing record.

## First-run note

The initial `development-ab-v1-20260715` Pod was terminated after its evidence was copied and verified locally. Its final charge was `$0.15`. The reusable lifecycle begins with the next suitable Pod; the terminated Pod cannot be resumed.
