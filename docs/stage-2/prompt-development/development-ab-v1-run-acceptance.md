# Development System A/B v1 Run Acceptance

- **Accepted:** 2026-07-15
- **Run ID:** `development-ab-v1-20260715`
- **Status:** Accepted as development evidence with disclosed metadata limitations
- **Final Runpod charge:** `$0.15`

## Acceptance scope

This record establishes the identity, completeness, integrity, and operational provenance of the first controlled System A/B development run. It does not score JSON/schema validity, inspect answer quality, select a prompt version, or support a held-out generalisation claim.

No user-prompt text or generated-answer text was inspected while preparing this acceptance record. The response file was queried only for closed operational fields such as attempt identity, status, termination reason, error presence, and stored output hashes.

## Immutable evidence

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `manifest.json` | 27,636 | `415408d949c9f8487c6ce6688f04a12fee98a5cee408d225a35e8bd08f5609ce` |
| `prompts.jsonl` | 6,666 | `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` |
| `responses.jsonl` | 751,515 | `0bfb4e728a5b8e941445a150536fd74c27e9aeebc0b8331d0a31193c9f59bed4` |

The hashes printed locally matched those printed on the Pod before termination.

The shared inspector reported:

- `complete: true`;
- 40 scheduled attempts and 40 unique recorded attempts;
- 40 structurally valid response records;
- no missing, duplicate, unexpected, malformed, or integrity-failing records;
- 20 attempts for System A and 20 for System B;
- 40 `success` attempt statuses;
- 40 `eos_token` termination reasons;
- no error records and no response reaching `max_new_tokens`; and
- 40 distinct stored raw-output hashes.

These are harness-record validity statements, not claims that the stored model text is valid JSON or a good ChatG&T answer.

## Frozen experimental identity

| Component | Recorded identity |
| --- | --- |
| Behaviour commit | `4c15262a621ae42090ba0da2ea3390b44a87de3a` |
| Behaviour digest | `823568ceb5fcc2cae1207f58b505875ed234c984af37c3d3ca40a764baaa8c99` |
| Harness specification | `1.2` |
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Model revision | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |
| Weight digest | `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee` |
| Weight dtype | BF16 |
| Development prompt set | 20 prompts; `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` |
| System set | `c2c59b412f7982d07b026e61a347f03acdbbf2f7c8aa4136bf5094fecbae45cc` |
| Master run seed | `20260714` |
| Execution-order seed | `17625029341685692511` |
| Samples | One per system/prompt combination |

System A used the empty `minimal-v1` prompt asset with no adapter. System B used `five-shot-v1`, containing the detailed instructions and five worked examples, with no adapter. The prompt-asset digests recorded in the manifest match their frozen reviewed identities.

## Recorded execution environment

| Field | Recorded value |
| --- | --- |
| Manifest creation time | `2026-07-15T08:42:54.390807+00:00` |
| GPU | NVIDIA L4 |
| Logical device | `cuda:0` |
| Reported device memory | 23,659,151,360 bytes |
| BF16 supported | Yes |
| PyTorch | `2.12.1+cu130` |
| PyTorch CUDA build | `13.0` |
| cuDNN | `92000` |
| Python | `3.12.13` |
| Transformers | `5.12.1` |
| PEFT | `0.19.1` |
| Attention implementation | SDPA |
| Platform | `Linux-6.8.0-106-generic-x86_64-with-glibc2.39` |

The operator confirmed a final charge of `$0.15` and that the Pod and associated billable storage were terminated after the local evidence passed inspection.

## Disclosed metadata limitations

### Self-induced Git dirty flag

The manifest records `git_dirty: true`. Code inspection shows that the harness enters `_runs_lock`, which creates the untracked `experiments/runs/.chatgnt-harness.lock`, before `_make_manifest` calls `_implementation_identity` and runs `git status --porcelain`. The harness therefore makes its own Git cleanliness measurement dirty.

This flag cannot establish whether unrelated working-tree changes existed before execution. It does not alter the recorded behavior: the exact commit, every `chatgnt/*.py` behavior file, the behavior tree, `pyproject.toml`, `uv.lock`, model files, configuration sources, prompt set, and system assets are separately digest-bound in the immutable manifest.

The run remains suitable as development evidence, but Git cleanliness collection must be corrected and tested before the next formal GPU run.

### CUDA driver collection

The manifest records `cuda_driver: null` and preserves the collection error `AttributeError: module 'torch.cuda' has no attribute 'driver_version'`. The formal specification permits a null driver when the pinned public API cannot collect it and requires the error to be retained, which occurred here.

CUDA 13, BF16 support, the NVIDIA L4 identity, device memory, and successful synchronized generation are recorded. The exact `nvidia-smi` driver version was not retained outside the terminated Pod. This limits exact environment reconstruction but does not invalidate the within-session A/B behavior comparison.

### Provider administration metadata

The Pod ID, region, template/image tag, displayed compute/storage rate split, storage allocation, and exact session start/end times were not retained. They are recorded as unavailable rather than reconstructed from memory. Their absence limits the operational cost breakdown, not the identity or integrity of the model-behavior evidence.

## Acceptance decision

The run is accepted for its intended purpose: development analysis of the untouched base model under System A and the initial five-shot System B prompt.

The run is not a held-out evaluation, final model comparison, deployment benchmark, or generalisation result. Latency observations remain descriptive and should carry the missing-driver limitation. No response-quality conclusion is made until the prompt-development stopping and selection rule is frozen and the stored text is evaluated under the agreed schema and qualitative rubric.

## Required follow-up

1. Freeze the prompt-development stopping and version-selection rule before inspecting answer text.
2. Correct the self-induced Git dirty measurement before another formal GPU run.
3. Automate capture of useful Pod administration and `nvidia-smi` metadata where practical.
4. Evaluate the accepted run without modifying its immutable files.

The source-control measurement and historical-inspection issues were corrected during the subsequent prompt-development milestone. The harness now captures implementation identity before creating its lock, obtains the CUDA driver through `nvidia-smi`, and validates a historical behaviour-file inventory against its recorded state rather than the present package tree. The original manifest remains unchanged, and a regression test requires this accepted run to continue passing inspection.
