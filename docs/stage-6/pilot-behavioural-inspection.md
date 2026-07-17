# Runbook: Stage 6 Pilot Behavioural Inspection on a Fresh Runpod

- **Inspection ID:** `pilot-behaviour-v1`
- **Systems:** A (untouched base, minimal prompt) and C (pilot adapter, minimal prompt)
- **Run seed:** `20260715`
- **Population:** ten validation prompts; two per intent family
- **Execution commit:** `f1a3e8483ce31ea1dffdf129866e24889298b632`
- **Required GPU:** one BF16-capable NVIDIA GPU with at least 24 GB VRAM
- **Status:** Executed and verified; see `pilot-behavioural-inspection-results.md`
- **Date:** 2026-07-17

## Question

Does the final three-epoch pilot adapter produce visibly better ChatG&T behaviour than the untouched model when both receive the same minimal prompt?

This is a bounded diagnostic between the mechanical pilot and full-training configuration design. It is not the held-out evaluation, a final system comparison, or a statistically powered performance estimate.

## Frozen population

The inspection uses one ordinary and one challenging validation example from each intent family. The challenging slot uses a robustness example where one exists; creative generation instead uses a composed exact-constraint example because the validation split contains no creative robustness example.

| Intent family | Ordinary | Challenge |
| --- | --- | --- |
| Advice and decision support | `dataset-v1-013` | `dataset-v1-192` |
| Creative generation | `dataset-v1-043` | `dataset-v1-185` |
| Explanation and technical understanding | `dataset-v1-035` | `dataset-v1-205` |
| Low-stakes emotional support | `dataset-v1-059` | `dataset-v1-006` |
| Short-form transformation | `dataset-v1-009` | `dataset-v1-200` |

The inference projection is `data/stage-6/pilot-behaviour-v1.jsonl`, frozen at SHA-256 `0b3acdeb84a13acfee45905e6d40cd4c5bf2e26f546299bbd5ab2fec44826cba`. It contains only the source example ID, user prompt, and selection metadata. The ideal validation responses do not enter either model context.

## Systems and generation

`config/systems/pilot-behaviour-ac-v1.json`, frozen at SHA-256 `f8fd4d10ff50aa111caa6ea39e247d92924be2d13d04028e92c9e57db95c9034`, runs both systems in one harness invocation:

- **A:** pinned Qwen2.5-1.5B-Instruct with the empty `minimal-v1` prompt and no adapter;
- **C:** the same base model and prompt with the final adapter from `pilot-training-v1-20260717-run01` active and unmerged.

The shared run seed and existing harness give A and C paired per-prompt generation seeds. The frozen primary generation profile is used unchanged. One run therefore creates exactly 20 responses.

The epoch-one and epoch-two checkpoints are not included initially. The loss report already records their progression, while only the final adapter is a provenance-complete harness input. Earlier checkpoints may be inspected later only if the final behaviour reveals a concrete regression question.

## Fresh Runpod runbook

Run the sections in order. Commands are labelled by where they run. Do not change code, dependencies, prompts, generation settings, or adapter files on the Pod.

### 1. Deploy the Pod — Runpod console

1. Select the official Runpod PyTorch template with SSH enabled.
2. Choose the cheapest available on-demand NVIDIA GPU with at least 24 GB VRAM.
3. Use a CUDA 13-compatible image and an R580-or-newer driver.
4. Allocate at least 30 GB beneath `/workspace`.
5. Note the displayed hourly compute price and set a 30-minute reminder.
6. Deploy the Pod and wait until its **Connect** panel shows an SSH command.

Do not adapt the test to a smaller or incompatible machine. Terminate it and choose another Pod if these requirements are unavailable.

### 2. Connect — local terminal

Use the exact IP address and port from Runpod's **Connect** panel:

```bash
ssh root@POD_PUBLIC_IP -p POD_SSH_PORT -i ~/.ssh/id_ed25519
```

Keep this SSH terminal open. Sections 3–9 run inside it unless explicitly labelled **local terminal**.

### 3. Verify the fresh machine — Pod SSH terminal

```bash
date -u
nvidia-smi
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
df -h /workspace
```

Continue only when one NVIDIA GPU is visible, it reports approximately 24 GB or more VRAM, the driver is R580 or newer, and `/workspace` has at least 15 GB free.

### 4. Clone the exact implementation — Pod SSH terminal

```bash
git clone https://github.com/WillEtheridge/chatgandt.git /workspace/chatgnt
cd /workspace/chatgnt
git checkout --detach f1a3e8483ce31ea1dffdf129866e24889298b632
git rev-parse HEAD
git status --short
```

The revision must be `f1a3e8483ce31ea1dffdf129866e24889298b632`, and `git status --short` must print nothing.

### 5. Reproduce the Python environment — Pod SSH terminal

```bash
curl -LsSf https://astral.sh/uv/0.11.28/install.sh \
  | env UV_UNMANAGED_INSTALL=/usr/local/bin sh
uv --version
export UV_CACHE_DIR=/workspace/.cache/uv
export HF_HOME=/workspace/.cache/huggingface
uv sync --frozen
uv run --frozen python scripts/verify_environment.py
```

Expected `uv` version: `0.11.28`. The environment report must show Python 3.12.13, CUDA 13.0, CUDA available, and one visible GPU. Do not change a package if verification fails.

Prove that BF16 computation really executes on the selected GPU:

```bash
uv run --frozen python -c "import torch; assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported(); x=torch.ones((256,256),device='cuda:0',dtype=torch.bfloat16); y=x@x; torch.cuda.synchronize(); print({'device':torch.cuda.get_device_name(0),'cuda_build':torch.version.cuda,'result_device':str(y.device),'dtype':str(y.dtype),'success':True})"
```

Continue only when `success` is true, the result device is `cuda:0`, and the dtype is `torch.bfloat16`.

### 6. Download and verify the pinned base model — Pod SSH terminal

```bash
uv run --frozen hf download Qwen/Qwen2.5-1.5B-Instruct \
  --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --local-dir artifacts/models/Qwen--Qwen2.5-1.5B-Instruct/989aa7980e4cf806f80c7fef2b1adb7bc71aa306
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
uv run --frozen python scripts/verify_model.py
```

The model check must report weights SHA-256 `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee` and chat-template SHA-256 `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`.

### 7. Transfer the final adapter

First create its destination outside the Git checkout — **Pod SSH terminal**:

```bash
mkdir -p /workspace/chatgnt-inputs/pilot-training-v1-20260717-run01
```

Open a second terminal on the laptop and copy the adapter — **local terminal**:

```bash
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 -r \
  /home/wje/Documents/chatgnt/experiments/training/pilot-training-v1-20260717-run01/adapter \
  root@POD_PUBLIC_IP:/workspace/chatgnt-inputs/pilot-training-v1-20260717-run01/
```

Return to the **Pod SSH terminal** and verify it:

```bash
uv run --frozen python -c "from pathlib import Path; from chatgnt.configuration import adapter_identity; import json; print(json.dumps(adapter_identity(Path('/workspace/chatgnt-inputs/pilot-training-v1-20260717-run01/adapter')),indent=2))"
```

The adapter digest must be `1386a85dd3c5c4c047c2e991dc1dd125ef871f795f91446d4d28654499d624ba`.

### 8. Run the final preflight — Pod SSH terminal

```bash
sha256sum data/stage-6/pilot-behaviour-v1.jsonl
sha256sum config/systems/pilot-behaviour-ac-v1.json
uv run --frozen python -m unittest discover -s tests
git status --short
```

Expected input hashes:

```text
0b3acdeb84a13acfee45905e6d40cd4c5bf2e26f546299bbd5ab2fec44826cba  data/stage-6/pilot-behaviour-v1.jsonl
f8fd4d10ff50aa111caa6ea39e247d92924be2d13d04028e92c9e57db95c9034  config/systems/pilot-behaviour-ac-v1.json
```

All 128 tests must pass and Git status must remain empty.

### 9. Run the paired inspection once — Pod SSH terminal

```bash
uv run --frozen python -m chatgnt.harness run \
  --prompts data/stage-6/pilot-behaviour-v1.jsonl \
  --system-set config/systems/pilot-behaviour-ac-v1.json \
  --run-seed 20260715 \
  --device cuda:0 \
  --adapter-path /workspace/chatgnt-inputs/pilot-training-v1-20260717-run01/adapter \
  --run-id pilot-behaviour-v1-20260717 \
  --runs-root experiments/training/pilot-training-v1-20260717-run01/behaviour
```

Do not rerun under the same run ID. A successful command reports exit status zero and a complete 20-response run.

### 10. Inspect the Pod result — Pod SSH terminal

```bash
uv run --frozen python -m chatgnt.harness inspect \
  --run-dir experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717
sha256sum experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717/manifest.json
sha256sum experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717/prompts.jsonl
sha256sum experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717/responses.jsonl
```

The inspection must report 20 scheduled and 20 valid response records with no missing, duplicate, malformed, or unexpected attempts. Keep the three hashes for comparison after retrieval.

### 11. Copy the evidence home — local terminal

```bash
mkdir -p /home/wje/Documents/chatgnt/experiments/training/pilot-training-v1-20260717-run01/behaviour
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 -r \
  root@POD_PUBLIC_IP:/workspace/chatgnt/experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717 \
  /home/wje/Documents/chatgnt/experiments/training/pilot-training-v1-20260717-run01/behaviour/
```

Verify the returned evidence — **local terminal, from the repository root**:

```bash
uv run --frozen python -m chatgnt.harness inspect \
  --run-dir experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717
sha256sum experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717/manifest.json
sha256sum experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717/prompts.jsonl
sha256sum experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717/responses.jsonl
```

The local inspection must pass and all three hashes must match the Pod values.

### 12. Stop billing — Runpod console

1. Record the final session charge.
2. Confirm the complete, hash-matching run exists locally.
3. Terminate the Pod unless another already-prepared GPU run will begin immediately.
4. Remove any separately billable volume that is no longer required.

Do not terminate the Pod before local verification succeeds.

## Review after retrieval

The 20 immutable raw outputs will first receive automatic schema validation. Model identities will then be hidden and every schema-valid response scored once against the frozen 1–3 dimensions:

- underlying-answer quality;
- metaphorical coherence; and
- recipe-style execution.

After identities are revealed, the report will show structural passes, qualitative scores, joint passes, representative changes, and recurring failures. The conclusion is diagnostic: whether the pilot demonstrates behavioural movement worth carrying into full-training configuration design.

No held-out prompt is used. The supervised examples, System B prompt, evaluation rubric, and pilot adapter are not revised from these outputs.
