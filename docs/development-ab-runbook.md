# Runbook: Development System A/B v1

- **Runbook version:** 1.0
- **Prepared:** 2026-07-15
- **Status:** Ready to execute
- **Experimental run ID:** `development-ab-v1-20260715`
- **Code revision:** `4c15262a621ae42090ba0da2ea3390b44a87de3a`

## Purpose

Execute the first controlled comparison of System A and System B on the frozen 20-prompt development workbench, preserve the complete raw evidence, and end the paid Runpod session without inspecting or modifying individual model answers on the Pod.

This is development evidence, not a held-out result. The run uses the untouched pinned Qwen base model, one sampled response per prompt and system, master seed `20260714`, and the already frozen 40-attempt order.

## Immutable inputs

| Input | Identity |
| --- | --- |
| Repository revision | `4c15262a621ae42090ba0da2ea3390b44a87de3a` |
| Development prompts | `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` |
| A/B system set | `c2c59b412f7982d07b026e61a347f03acdbbf2f7c8aa4136bf5094fecbae45cc` |
| Run plan | `63db3e2cd65354b037c62eda2c5cabc34ae32f336b42aff8cf7f19cd08672271` |
| Dry schedule | `ae55b4521dfe581c10febbe0c13bcdfd26262de616a493e331c7562e89a36468` |
| Base model revision | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |
| Base weights | `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee` |

Do not edit a prompt, prompt asset, system mapping, generation setting, seed, schedule, dependency, or model file on the Pod.

## 1. Before starting paid compute

- Confirm the local repository has pushed revision `4c15262a621ae42090ba0da2ea3390b44a87de3a`.
- Confirm the Runpod account has enough bounded credit and automatic top-up is configured as intended.
- Prepare the Pod's SSH command and a local destination beneath `experiments/runs/`.
- Note the deployment start time.
- Set a reminder to review the Pod after 30 minutes.

## 2. Provision the Pod

Use an on-demand Pod with:

- one BF16-capable NVIDIA GPU with at least 24 GB VRAM;
- an R580-or-newer NVIDIA driver capable of running the locked CUDA 13 PyTorch build;
- the official Runpod PyTorch template;
- SSH enabled; and
- at least 30 GB available beneath `/workspace` for the environment, caches, model, and run evidence.

An L4, RTX 3090, or RTX 4090 is suitable if it meets those conditions. Do not pay for a substantially larger GPU merely because it is available.

Before deployment, record:

- Pod ID and region;
- GPU model and advertised VRAM;
- displayed compute and storage rates;
- template name and image tag; and
- allocated container and network-volume storage.

Availability and prices are live console facts and must not be copied from an earlier session.

## 3. Verify infrastructure immediately

Connect using the exact SSH command shown by Runpod, then run:

```bash
nvidia-smi
```

Continue only if the output shows the intended GPU and an R580-or-newer driver. A displayed CUDA 13 capability alone is insufficient if the driver branch is older.

Record the complete `nvidia-smi` output. If the driver is incompatible, terminate the Pod before installing anything and select another instance.

## 4. Check out the frozen repository

```bash
git clone https://github.com/WillEtheridge/chatgandt.git /workspace/chatgnt
cd /workspace/chatgnt
git checkout --detach 4c15262a621ae42090ba0da2ea3390b44a87de3a
git rev-parse HEAD
git status --short
```

Expected:

- `git rev-parse HEAD` prints `4c15262a621ae42090ba0da2ea3390b44a87de3a`; and
- `git status --short` prints nothing.

If cloning requires authentication, do not paste a token into shell history. Stop and transfer a clean archive of the same revision over SSH instead.

## 5. Reproduce the locked environment

Install the required uv release without changing shell startup files:

```bash
curl -LsSf https://astral.sh/uv/0.11.28/install.sh | env UV_UNMANAGED_INSTALL=/usr/local/bin sh
uv --version
```

Expected uv version: `0.11.28`.

Keep caches on `/workspace`, then reproduce the lock exactly:

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
export HF_HOME=/workspace/.cache/huggingface
uv sync --frozen
uv run --frozen python scripts/verify_environment.py
```

The environment report must show Python 3.12.13, the locked package versions, CUDA available, and one visible device. Do not change a dependency pin to fix a Pod-specific failure.

## 6. Download and verify the pinned model

Download the exact Hugging Face revision into the path required by the harness:

```bash
uv run --frozen hf download Qwen/Qwen2.5-1.5B-Instruct --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 --local-dir artifacts/models/Qwen--Qwen2.5-1.5B-Instruct/989aa7980e4cf806f80c7fef2b1adb7bc71aa306
```

Disable network fallback for all subsequent model activity:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
uv run --frozen python scripts/verify_model.py
```

Expected model evidence includes:

- model ID `Qwen/Qwen2.5-1.5B-Instruct`;
- revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`;
- weights SHA-256 `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee`;
- tokenizer class `Qwen2Tokenizer`; and
- no vendor system message in the canonical prompt.

Do not continue after a checksum or tokenizer-identity failure.

## 7. Run the complete no-generation preflight

```bash
uv run --frozen python scripts/verify_development_prompts.py
uv run --frozen python scripts/verify_worked_examples.py
uv run --frozen python scripts/verify_minimal_prompt.py
uv run --frozen python scripts/verify_five_shot_prompt.py --measure-tokens
uv run --frozen python scripts/verify_development_systems.py
uv run --frozen python scripts/verify_development_run_plan.py
uv run --frozen python scripts/verify_development_schedule.py
```

Every command must report `"result": "pass"`. The schedule check must report 40 attempts, 20 per system, 20 complete A/B pairs, and exact equality with the production scheduler.

## 8. Exercise CUDA without model generation

Run this as one physical shell line:

```bash
uv run --frozen python -c "import torch; assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported(); x=torch.ones((256,256),device='cuda:0',dtype=torch.bfloat16); y=x@x; torch.cuda.synchronize(); print({'device':torch.cuda.get_device_name(0),'cuda_build':torch.version.cuda,'result_device':str(y.device),'dtype':str(y.dtype),'success':True})"
```

Expected: `success` is true, the result device is `cuda:0`, and the dtype is `torch.bfloat16`.

If this fails, stop. Do not run the experiment on CPU or substitute a different precision.

## 9. Execute the frozen run

Confirm that the run ID has never been used in this checkout:

```bash
test ! -e experiments/runs/development-ab-v1-20260715
```

Then run:

```bash
uv run --frozen python -m chatgnt.harness run \
  --prompts data/development/prompts-v1.jsonl \
  --system-set config/systems/development-ab-v1.json \
  --run-seed 20260714 \
  --device cuda:0 \
  --run-id development-ab-v1-20260715
```

Do not add `--adapter-path`. Do not retry failed attempts automatically. Keep the SSH session open until the command returns.

Expected successful completion:

- exit status `0`;
- run directory `experiments/runs/development-ab-v1-20260715`;
- 40 scheduled and 40 unique recorded attempts;
- no missing, duplicate, malformed, unexpected, or integrity-failing records; and
- exactly three primary files: `manifest.json`, `prompts.jsonl`, and `responses.jsonl`.

## 10. Inspect without reading individual answers

```bash
uv run --frozen python -m chatgnt.harness inspect --run-dir experiments/runs/development-ab-v1-20260715
wc -l experiments/runs/development-ab-v1-20260715/prompts.jsonl
wc -l experiments/runs/development-ab-v1-20260715/responses.jsonl
sha256sum experiments/runs/development-ab-v1-20260715/manifest.json experiments/runs/development-ab-v1-20260715/prompts.jsonl experiments/runs/development-ab-v1-20260715/responses.jsonl
```

Expected line counts are 20 prompts and 40 responses. The inspector must report `complete: true` with no integrity errors.

Do not open `responses.jsonl` or begin prompt revision on the Pod. First preserve the evidence and end paid compute.

## 11. Copy the evidence home

On the local machine, replace the SSH port and public IP with the exact values from Runpod:

```bash
mkdir -p /home/wje/Documents/chatgnt/experiments/runs
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 -r root@POD_PUBLIC_IP:/workspace/chatgnt/experiments/runs/development-ab-v1-20260715 /home/wje/Documents/chatgnt/experiments/runs/
```

While the Pod is still available, inspect the retrieved copy locally:

```bash
cd /home/wje/Documents/chatgnt
UV_CACHE_DIR=/tmp/chatgnt-uv-cache uv run --frozen python -m chatgnt.harness inspect --run-dir experiments/runs/development-ab-v1-20260715
sha256sum experiments/runs/development-ab-v1-20260715/manifest.json experiments/runs/development-ab-v1-20260715/prompts.jsonl experiments/runs/development-ab-v1-20260715/responses.jsonl
```

The local hashes must match those printed on the Pod.

## 12. Record billing and terminate everything

Before deletion, record from the Runpod console:

- stop/end time;
- final session charge;
- actual hourly compute and storage rates; and
- whether any unavailable or incompatible Pod was briefly allocated first.

Then:

1. Confirm the local inspector still reports a complete run.
2. Delete the Pod.
3. Delete any attached persistent or network volume that is no longer needed.
4. Confirm no stopped compute or storage remains billable.

The billing record will be added to the development-run acceptance document alongside the immutable technical evidence.

## Failure handling

- **Infrastructure or CUDA failure before the run:** stop and replace the Pod; no experimental result exists.
- **Model, dependency, prompt, system, run-plan, or schedule identity failure:** stop; do not edit the frozen inputs on the Pod.
- **Harness preflight failure before publication:** preserve the terminal error and diagnose locally before authorising a run.
- **Non-zero exit after a run directory is created:** copy the partial directory and inspect it. Do not delete it, resume it, fill missing attempts, or reuse its run ID.
- **SSH interruption:** reconnect and check whether the process and run directory still exist before taking any action. Do not launch a second run speculatively.
- **Incomplete or surprising result:** preserve first, terminate paid resources, then analyse locally.

## Completion condition

This runbook is complete only when:

- the local copy contains the three immutable run files;
- the local inspector reports all 40 attempts complete and intact;
- Pod and local file hashes match;
- the final Runpod charge and hardware are recorded; and
- no Pod or unwanted storage remains billable.
