# Runbook: Pinned System B v3 Confirmation

- **Purpose:** Confirm that the locally selected prompt transfers unchanged to the pinned Hugging Face BF16 runtime
- **Execution commit:** `8f3d43ea133c7faf385c373fadaf7d13b4f46908`
- **Candidate:** `five-shot-v3`
- **Master seed:** `20260714`
- **Scheduled attempts:** 20
- **Status:** Executed on 2026-07-15; evidence accepted

This document is the complete operator procedure. Follow it from top to bottom during one Runpod session rather than combining it with remembered commands from an earlier run.

The execution produced run `development-b-v3-confirmation-20260715` for a final charge of `$0.14`. Its immutable identities, disclosed preflight deviation, and structural result are recorded in [Development System B v3 confirmation acceptance](development-b-v3-confirmation-acceptance.md). The instructions below are preserved as the repeatable procedure.

The run uses only System B: the untouched base model with the selected five-shot prompt. System A already has accepted pinned development evidence and was not regenerated during local prompt iteration. Because A and B will come from different sessions, do not present their latency as a matched comparison.

## 1. Frozen identity

| Input | Required identity |
| --- | --- |
| Repository commit | `8f3d43ea133c7faf385c373fadaf7d13b4f46908` |
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Model revision | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |
| Base weights | `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee` |
| Development prompts | `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` |
| Five-shot v3 prompt | `cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31` |
| System B/v3 set | `ee85e9a115971b473e4e732eb81a0e904fe8b9405e9b78d2a1f84205f05a92e6` |
| Confirmation plan | `feb635d9de48a1cabc46b5185c9e1c42708df90f63a6001f57c91d7b7d0faa98` |
| uv | `0.11.28` |
| Python | `3.12.13` |
| Weight dtype | BF16 |

Do not change a dependency, prompt, seed, generation setting, precision, or model file on the Pod. A necessary change is prepared and committed locally as a new version before another authorised run.

## 2. Before starting paid compute

Locally, confirm the execution commit is available on GitHub:

```bash
cd /home/wje/Documents/chatgnt
git show --no-patch --oneline 8f3d43ea133c7faf385c373fadaf7d13b4f46908
git status --short
```

Expected:

- `git show` identifies `Complete prompt baseline development and select v3`;
- `git status --short` is empty; and
- the Runpod account has sufficient bounded credit.

Set a 30-minute reminder to review the Pod even if the SSH session is interrupted.

## 3. Provision a suitable Pod

Use an on-demand Pod with:

- one NVIDIA L4, RTX 3090, RTX 4090, or equivalent BF16-capable GPU;
- at least 24 GB VRAM;
- an R580-or-newer NVIDIA driver compatible with the locked CUDA 13 PyTorch build;
- the Runpod PyTorch template;
- SSH enabled; and
- at least 30 GB available beneath `/workspace`.

Choose the cheapest currently available machine meeting these gates. The manifest records the hardware and software identity used by the model.

If resuming a retained Pod, the same checks still apply. Previous successful execution does not establish the restarted session's environment.

## 4. Connect and verify the machine immediately

Use the exact SSH command displayed by Runpod:

```bash
ssh root@POD_PUBLIC_IP -p POD_SSH_PORT -i ~/.ssh/id_ed25519
```

On the Pod:

```bash
date -u
nvidia-smi
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
df -h /workspace
```

Continue only when:

- the intended GPU is visible;
- the driver branch is R580 or newer;
- approximately 24 GB or more VRAM is reported; and
- `/workspace` has sufficient free space.

Terminate an unsuitable Pod before installing dependencies. A displayed CUDA 13 capability does not compensate for an older incompatible driver.

## 5. Check out the exact execution commit

For a new Pod:

```bash
git clone https://github.com/WillEtheridge/chatgandt.git /workspace/chatgnt
cd /workspace/chatgnt
git checkout --detach 8f3d43ea133c7faf385c373fadaf7d13b4f46908
git rev-parse HEAD
git status --short
```

For a retained Pod whose previous evidence has already been copied home and archived outside the checkout:

```bash
cd /workspace/chatgnt
git status --short
git fetch origin
git checkout --detach 8f3d43ea133c7faf385c373fadaf7d13b4f46908
git rev-parse HEAD
git status --short
```

Expected commit: `8f3d43ea133c7faf385c373fadaf7d13b4f46908`.

Both status commands must be empty before continuing. Do not discard an unexplained change or overwrite a previous run directory to make the checkout appear clean.

If GitHub access fails, create and transfer a Git bundle from the local machine:

```bash
cd /home/wje/Documents/chatgnt
git bundle create /tmp/chatgnt-v3-confirmation.bundle HEAD
git bundle verify /tmp/chatgnt-v3-confirmation.bundle
sha256sum /tmp/chatgnt-v3-confirmation.bundle

scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 \
  /tmp/chatgnt-v3-confirmation.bundle \
  root@POD_PUBLIC_IP:/workspace/
```

Record the local bundle hash. Then, on the Pod:

```bash
sha256sum /workspace/chatgnt-v3-confirmation.bundle
git clone /workspace/chatgnt-v3-confirmation.bundle /workspace/chatgnt
cd /workspace/chatgnt
git checkout --detach 8f3d43ea133c7faf385c373fadaf7d13b4f46908
git rev-parse HEAD
git status --short
```

The Pod bundle hash must match the local hash, the exact execution commit must be present, and Git status must be empty. Do not use a source-only archive because the harness must retain Git provenance.

## 6. Reproduce the locked environment

Install the required uv version without editing shell startup files:

```bash
curl -LsSf https://astral.sh/uv/0.11.28/install.sh | env UV_UNMANAGED_INSTALL=/usr/local/bin sh
uv --version
```

Expected: `uv 0.11.28`.

Keep reusable caches on `/workspace`, then reproduce the lock exactly:

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
export HF_HOME=/workspace/.cache/huggingface
uv sync --frozen
uv run --frozen python scripts/verify_environment.py
```

The environment report must show:

- Python `3.12.13`;
- `torch.cuda_available: true`;
- CUDA build `13.0`; and
- one visible CUDA device.

Stop rather than changing a dependency if the frozen environment cannot be reproduced.

## 7. Download and verify the pinned model

```bash
uv run --frozen hf download Qwen/Qwen2.5-1.5B-Instruct \
  --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --local-dir artifacts/models/Qwen--Qwen2.5-1.5B-Instruct/989aa7980e4cf806f80c7fef2b1adb7bc71aa306

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
uv run --frozen python scripts/verify_model.py
```

Expected model evidence includes the model and revision in section 1, the required weight digest, tokenizer class `Qwen2Tokenizer`, and no vendor system message in the canonical prompt.

Stop after any model-file, tokenizer, revision, or digest mismatch. Do not allow an online fallback after this check.

## 8. Verify CUDA with a real BF16 operation

Run this as one physical shell line:

```bash
uv run --frozen python -c "import torch; assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported(); x=torch.ones((256,256),device='cuda:0',dtype=torch.bfloat16); y=x@x; torch.cuda.synchronize(); print({'device':torch.cuda.get_device_name(0),'cuda_build':torch.version.cuda,'result_device':str(y.device),'dtype':str(y.dtype),'success':True})"
```

Expected: `success` is true, `result_device` is `cuda:0`, and `dtype` is `torch.bfloat16`.

## 9. Run the confirmation-specific preflight

```bash
sha256sum \
  data/development/prompts-v1.jsonl \
  config/prompts/five-shot-v3.json \
  config/systems/development-b-v3.json \
  config/runs/development-b-v3-confirmation.json

uv run --frozen python scripts/verify_prompt_confirmation.py
uv run --frozen python -m unittest discover -s tests
git status --short
```

Expected:

- all four hashes exactly match section 1;
- the confirmation verifier reports `"result": "pass"`, seed `20260714`, and 20 scheduled attempts;
- all 102 tests pass; and
- Git status remains empty.

This is the final go/no-go gate. Stop if any expectation fails.

## 10. Choose the unique run ID

```bash
RUN_ID="development-b-v3-confirmation-$(date -u +%Y%m%d)"
echo "$RUN_ID"
test ! -e "experiments/runs/$RUN_ID"
```

The final command must exit successfully. If that path already exists, do not delete or overwrite it. Choose a new descriptive suffix and record why another run identity was required.

## 11. Execute the 20-attempt run

Keep the SSH session open until the command returns:

```bash
uv run --frozen python -m chatgnt.harness run \
  --prompts data/development/prompts-v1.jsonl \
  --system-set config/systems/development-b-v3.json \
  --run-seed 20260714 \
  --device cuda:0 \
  --run-id "$RUN_ID"
```

Do not add `--adapter-path`, retry a response, repair JSON, continue truncated output, or use constrained generation. A successful command should return exit status `0` and report a complete run with 20 scheduled responses.

If the command is interrupted or returns non-zero, do not rerun it under the same ID. Preserve the partial directory, inspect it, copy it home, and record the failure.

## 12. Inspect the Pod evidence without judging answers

```bash
uv run --frozen python -m chatgnt.harness inspect \
  --run-dir "experiments/runs/$RUN_ID"

wc -l \
  "experiments/runs/$RUN_ID/prompts.jsonl" \
  "experiments/runs/$RUN_ID/responses.jsonl"

find "experiments/runs/$RUN_ID" -maxdepth 1 -type f -printf '%f\n' | sort

sha256sum \
  "experiments/runs/$RUN_ID/manifest.json" \
  "experiments/runs/$RUN_ID/prompts.jsonl" \
  "experiments/runs/$RUN_ID/responses.jsonl"

date -u
```

Expected:

- inspector `complete: true`;
- 20 prompt lines and 20 response lines;
- exactly `manifest.json`, `prompts.jsonl`, and `responses.jsonl`; and
- no missing, duplicate, malformed, unexpected, or integrity-failing records.

Copy the three Pod hashes into the session note. Do not inspect individual answer text until the evidence is safely home and paid compute can be stopped.

## 13. Copy the complete run home

On the local machine, set the same printed run ID and use the current Pod address:

```bash
cd /home/wje/Documents/chatgnt
RUN_ID="THE_RUN_ID_PRINTED_ON_THE_POD"

scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 -r \
  "root@POD_PUBLIC_IP:/workspace/chatgnt/experiments/runs/$RUN_ID" \
  /home/wje/Documents/chatgnt/experiments/runs/
```

While the Pod is still available, verify the local copy:

```bash
UV_CACHE_DIR=/tmp/chatgnt-uv-cache uv run --frozen python -m chatgnt.harness inspect \
  --run-dir "experiments/runs/$RUN_ID"

sha256sum \
  "experiments/runs/$RUN_ID/manifest.json" \
  "experiments/runs/$RUN_ID/prompts.jsonl" \
  "experiments/runs/$RUN_ID/responses.jsonl"
```

The local inspector must also report `complete: true`, and all three local hashes must match the Pod hashes exactly. If transfer stalls, retry the file transfer; do not delete the Pod copy until all local checks pass.

## 14. Record cost and stop billing

In the Runpod console, record the final charge and confirm that the Pod and any unneeded separately billable storage are stopped or terminated.

Terminate the Pod and remove unneeded billable storage when no near-term authorised GPU task is ready. Stop it only when another prepared task will genuinely reuse the cached environment soon; stopped storage remains billable and needs a daily reminder.

Do not end the session until the run exists locally, passes inspection, and matches the Pod hashes.

## 15. Evaluate locally after billing has stopped

Create a structural-evaluation directory using the exact run ID:

```bash
UV_CACHE_DIR=/tmp/chatgnt-uv-cache uv run --frozen python scripts/evaluate_structure.py \
  --run-dir "experiments/runs/$RUN_ID" \
  --output-dir "experiments/evaluations/$RUN_ID-structure"
```

Then prepare identity-blinded qualitative-scoring packets:

```bash
UV_CACHE_DIR=/tmp/chatgnt-uv-cache uv run --frozen python scripts/prepare_blind_scoring.py \
  --source formal-v3 \
    "experiments/runs/$RUN_ID" \
    "experiments/evaluations/$RUN_ID-structure" \
  --output-dir "experiments/evaluations/$RUN_ID-blind-scoring"
```

Do not open `identity-mapping.jsonl` while scoring the packets. After the blind scores are complete, reveal and aggregate them with the documented scoring procedure.

Compare the pinned v3 result with local v3 as a transfer check. Report discrepancies; the four-version budget is closed, so the result does not authorise a fifth prompt version.

## Failure rule

Before generation, a failed gate means stop and investigate locally. During or after generation, preserve the immutable complete or partial run under its unique ID before investigating. Never make an unrecorded Pod-side change merely to obtain a successful-looking result.
