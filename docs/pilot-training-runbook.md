# Runbook: Stage 6 Pilot Training

- **Run:** one 40-example LoRA pipeline rehearsal
- **Configuration:** `config/pilot-training-v1.toml`
- **Execution commit:** set after the pilot implementation is committed
- **Expected GPU time:** comfortably below one hour on a suitable 24 GB NVIDIA GPU
- **Status:** Prepared; not yet executed

This runbook contains only the run-specific steps. Use the existing reusable Runpod workflow for account, SSH, persistent-volume, model-download, and stop-versus-terminate guidance.

## 1. Local gate before renting a GPU

From the repository root:

```bash
uv run --frozen python scripts/run_pilot_training.py --check-inputs
uv run --frozen python -m unittest discover -s tests
git status --short
```

Expected input evidence:

- 40 pilot and 40 validation records;
- pilot token range 148–321 and validation range 150–287;
- no truncation;
- effective batch size 8; and
- exactly 15 optimiser steps.

Commit and push the complete pilot implementation before starting paid compute. Record that exact commit in this runbook; the Pod command refuses a dirty checkout.

## 2. Prepare the Pod

Use the cheapest available BF16-capable NVIDIA Pod with at least 24 GB VRAM. After connecting:

```bash
nvidia-smi
df -h /workspace
cd /workspace/chatgnt
git fetch origin
git checkout --detach EXECUTION_COMMIT
git status --short
```

The status must be empty. Install `uv 0.11.28`, run `uv sync --frozen`, and download the already pinned Qwen snapshot exactly as described in the reusable workflow. Then set offline mode:

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
export HF_HOME=/workspace/.cache/huggingface
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

## 3. Final paid-compute gate

```bash
uv run --frozen python scripts/verify_environment.py
uv run --frozen python scripts/verify_model.py
uv run --frozen python scripts/run_pilot_training.py --check-inputs
uv run --frozen python -m unittest discover -s tests
git status --short
```

Stop if any command fails or the status is non-empty. Do not edit dependencies, data, configuration, or code on the Pod.

## 4. Execute once

Copy the live compute price shown by Runpod, then choose a unique ID:

```bash
RUN_ID="pilot-training-v1-$(date -u +%Y%m%d)-run01"
HOURLY_PRICE_USD="DISPLAYED_COMPUTE_PRICE"
test ! -e "experiments/training/$RUN_ID"

uv run --frozen python scripts/run_pilot_training.py \
  --run-id "$RUN_ID" \
  --hourly-price-usd "$HOURLY_PRICE_USD"
```

A successful command reports `result: pass` and the report hash. Do not retry under the same run ID. Preserve a failed partial directory as evidence.

## 5. Retrieve the complete run

From the local machine, substitute the SSH details shown by Runpod:

```bash
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 -r \
  root@POD_PUBLIC_IP:/workspace/chatgnt/experiments/training/RUN_ID \
  /home/wje/Documents/chatgnt/experiments/training/
```

Locally:

```bash
sha256sum experiments/training/RUN_ID/report.json
jq '{run_id,result,training_shape,baseline_validation,epochs:[.epochs[]|{epoch,training_micro_batch_loss_mean,validation}],checks,gpu}' \
  experiments/training/RUN_ID/report.json
```

Record the final Runpod charge separately; the report's estimate covers only measured script time. Once the local copy and hash are verified, stop or terminate the Pod according to whether the full-training candidate run is genuinely imminent.
