# Runbook: Stage 6 Pilot Training on a Fresh Runpod

- **Run:** one 40-example LoRA pipeline rehearsal
- **Configuration:** `config/pilot-training-v1.toml`
- **Execution commit:** `81b586df35f45f6acd5145f3bb96b5ebe9f81840`
- **Required GPU:** one BF16-capable NVIDIA GPU with at least 24 GB VRAM
- **Status:** Prepared; not yet executed

This is a self-contained procedure for a brand-new Pod. Run each section in order. Do not repair code, alter dependencies, change the configuration, or retry under the same run ID on the Pod.

## 1. Before deployment

In the Runpod console:

1. Choose the cheapest available on-demand NVIDIA Pod with at least 24 GB VRAM.
2. Use the official Runpod PyTorch template with SSH enabled.
3. Ensure `/workspace` has at least 30 GB available.
4. Note the displayed compute price; it will be supplied to the training command.
5. Set a 30-minute reminder so the Pod is not forgotten if SSH disconnects.

The local pilot gate already established 40 pilot records, 40 validation records, no truncation, an effective batch size of eight, and exactly 15 optimiser steps. All 128 tests passed before the execution commit was frozen.

## 2. Connect to the fresh Pod

Use the exact command shown in Runpod's **Connect** panel:

```bash
ssh root@POD_PUBLIC_IP -p POD_SSH_PORT -i ~/.ssh/id_ed25519
```

Every command through Section 9 runs inside that SSH session unless explicitly labelled as local.

## 3. Verify the machine before installing anything

```bash
date -u
nvidia-smi
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
df -h /workspace
```

Continue only if one NVIDIA GPU is visible, approximately 24 GB or more VRAM is reported, the driver is R580 or newer for the locked CUDA 13 stack, and `/workspace` has at least 15 GB free. Terminate an unsuitable Pod rather than adapting the experiment to it.

## 4. Clone the exact implementation

```bash
git clone https://github.com/WillEtheridge/chatgandt.git /workspace/chatgnt
cd /workspace/chatgnt
git checkout --detach 81b586df35f45f6acd5145f3bb96b5ebe9f81840
git rev-parse HEAD
git status --short
```

Expected commit:

```text
81b586df35f45f6acd5145f3bb96b5ebe9f81840
```

`git status --short` must print nothing. Stop if the commit differs or the checkout is dirty.

## 5. Install the exact environment

Install the project-pinned `uv` release:

```bash
curl -LsSf https://astral.sh/uv/0.11.28/install.sh \
  | env UV_UNMANAGED_INSTALL=/usr/local/bin sh
uv --version
```

Expected: `uv 0.11.28`.

Keep caches on `/workspace` and reproduce the lockfile:

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
export HF_HOME=/workspace/.cache/huggingface
uv sync --frozen
uv run --frozen python scripts/verify_environment.py
```

The environment report must show Python 3.12.13, CUDA 13.0, `cuda_available: true`, and one visible device. Stop rather than changing a package if this fails.

## 6. Download and freeze the pinned model

Network access is required for this download:

```bash
uv run --frozen hf download Qwen/Qwen2.5-1.5B-Instruct \
  --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --local-dir artifacts/models/Qwen--Qwen2.5-1.5B-Instruct/989aa7980e4cf806f80c7fef2b1adb7bc71aa306
```

After it completes, disable network fallback:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
uv run --frozen python scripts/verify_model.py
```

The model check must report:

- model `Qwen/Qwen2.5-1.5B-Instruct`;
- revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`;
- weights SHA-256 `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee`; and
- tokenizer chat-template SHA-256 `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`.

## 7. Prove CUDA and BF16 really execute

Run this as one physical shell line:

```bash
uv run --frozen python -c "import torch; assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported(); x=torch.ones((256,256),device='cuda:0',dtype=torch.bfloat16); y=x@x; torch.cuda.synchronize(); print({'device':torch.cuda.get_device_name(0),'cuda_build':torch.version.cuda,'result_device':str(y.device),'dtype':str(y.dtype),'success':True})"
```

Continue only when `success` is true, the result device is `cuda:0`, and the dtype is `torch.bfloat16`.

## 8. Run the final preflight

```bash
uv run --frozen python scripts/run_pilot_training.py --check-inputs
uv run --frozen python -m unittest discover -s tests
git status --short
```

The pilot input report must show:

- 40 pilot and 40 validation records;
- pilot token range 148–321;
- validation token range 150–287;
- zero truncated examples;
- effective batch size eight; and
- exactly 15 optimiser steps.

All 128 tests must pass and Git status must remain empty. This is the final go/no-go gate.

## 9. Execute the pilot once

Choose a unique run ID. Replace `0.40` below with the compute price currently displayed by Runpod:

```bash
RUN_ID="pilot-training-v1-$(date -u +%Y%m%d)-run01"
HOURLY_PRICE_USD="0.46"
echo "$RUN_ID"
test ! -e "experiments/training/$RUN_ID"
```

If the final command succeeds, start training:

```bash
uv run --frozen python scripts/run_pilot_training.py \
  --run-id "$RUN_ID" \
  --hourly-price-usd "$HOURLY_PRICE_USD"
```

A successful run prints `"result": "pass"`, its run directory, and the report SHA-256. Do not rerun under the same ID. If it fails, preserve and retrieve the partial directory before investigating locally.

## 10. Inspect the result on the Pod

```bash
test -f "experiments/training/$RUN_ID/report.json"
sha256sum "experiments/training/$RUN_ID/report.json"
uv run --frozen python -c "import json,pathlib; r=json.loads(pathlib.Path('experiments/training/$RUN_ID/report.json').read_text()); print(json.dumps({'run_id':r['run_id'],'result':r['result'],'training_shape':r['training_shape'],'baseline_validation':r['baseline_validation'],'epochs':[{'epoch':e['epoch'],'training_micro_batch_loss_mean':e['training_micro_batch_loss_mean'],'validation':e['validation']} for e in r['epochs']],'checks':r['checks'],'gpu':r['gpu']},indent=2))"
```

This inspection checks completeness; do not alter the report or select a model on the Pod.

## 11. Copy the complete run home

Open a second terminal on the local machine. Use the same run ID and the SSH details shown by Runpod:

```bash
RUN_ID="pilot-training-v1-20260717-run01"
mkdir -p /home/wje/Documents/chatgnt/experiments/training
scp -P 40150 -i ~/.ssh/id_ed25519 -r \
  root@213.192.2.75 :/workspace/chatgnt/experiments/training/$RUN_ID \
  /home/wje/Documents/chatgnt/experiments/training/
```

Still locally, verify the copy:

```bash
test -f "/home/wje/Documents/chatgnt/experiments/training/$RUN_ID/report.json"
sha256sum "/home/wje/Documents/chatgnt/experiments/training/$RUN_ID/report.json"
uv run --frozen python -c "import json,pathlib; r=json.loads(pathlib.Path('/home/wje/Documents/chatgnt/experiments/training/$RUN_ID/report.json').read_text()); print(json.dumps({'run_id':r['run_id'],'result':r['result'],'training_shape':r['training_shape'],'baseline_validation':r['baseline_validation'],'epochs':[{'epoch':e['epoch'],'training_micro_batch_loss_mean':e['training_micro_batch_loss_mean'],'validation':e['validation']} for e in r['epochs']],'checks':r['checks'],'gpu':r['gpu']},indent=2))"
```

The local report hash must match the hash printed on the Pod.

## 12. Stop billing safely

1. Record the final charge shown by Runpod.
2. Confirm the complete run and matching report hash exist locally.
3. Stop the Pod if the full-training follow-up will be prepared immediately and set a daily reminder about storage charges.
4. Otherwise terminate the Pod and delete any separately billable volume.

The report's compute estimate covers only measured script time; the Runpod billing total is the authoritative session cost.
