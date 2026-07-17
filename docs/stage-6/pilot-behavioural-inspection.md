# Stage 6 Pilot Behavioural Inspection

- **Inspection ID:** `pilot-behaviour-v1`
- **Systems:** A (untouched base, minimal prompt) and C (pilot adapter, minimal prompt)
- **Run seed:** `20260715`
- **Population:** ten validation prompts; two per intent family
- **Status:** Prepared locally; execution commit must be bound before GPU execution
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

## How to execute it

### 1. Bind and retrieve the implementation

Commit and push this setup before provisioning. Record that commit as `INSPECTION_COMMIT`, then use it unchanged on the Pod:

```bash
git clone https://github.com/WillEtheridge/chatgandt.git /workspace/chatgnt
cd /workspace/chatgnt
git checkout --detach INSPECTION_COMMIT
git status --short
```

The status output must be empty at this point.

### 2. Reproduce the environment and model

On a fresh BF16-capable NVIDIA Pod with at least 24 GB VRAM:

```bash
nvidia-smi
curl -LsSf https://astral.sh/uv/0.11.28/install.sh | env UV_UNMANAGED_INSTALL=/usr/local/bin sh
export UV_CACHE_DIR=/workspace/.cache/uv
export HF_HOME=/workspace/.cache/huggingface
uv sync --frozen
uv run --frozen python scripts/verify_environment.py
uv run --frozen hf download Qwen/Qwen2.5-1.5B-Instruct \
  --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --local-dir artifacts/models/Qwen--Qwen2.5-1.5B-Instruct/989aa7980e4cf806f80c7fef2b1adb7bc71aa306
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
uv run --frozen python scripts/verify_model.py
```

### 3. Transfer the final adapter

On the Pod, create a location outside the Git checkout:

```bash
mkdir -p /workspace/chatgnt-inputs/pilot-training-v1-20260717-run01
```

Then, from the local machine, substitute the Pod connection details and copy the adapter:

```bash
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 -r \
  /home/wje/Documents/chatgnt/experiments/training/pilot-training-v1-20260717-run01/adapter \
  root@POD_PUBLIC_IP:/workspace/chatgnt-inputs/pilot-training-v1-20260717-run01/
```

Back on the Pod, verify its formal identity:

```bash
uv run --frozen python -c "from pathlib import Path; from chatgnt.configuration import adapter_identity; import json; print(json.dumps(adapter_identity(Path('/workspace/chatgnt-inputs/pilot-training-v1-20260717-run01/adapter')),indent=2))"
```

The adapter digest must be `1386a85dd3c5c4c047c2e991dc1dd125ef871f795f91446d4d28654499d624ba`.

### 4. Run the paired inspection once

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

Do not rerun under the same run ID or change prompts, settings, or adapter on the Pod.

### 5. Inspect and retrieve the evidence

```bash
uv run --frozen python -m chatgnt.harness inspect \
  --run-dir experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717
```

The inspection must report 20 scheduled and 20 valid response records with no missing, duplicate, malformed, or unexpected attempts.

From the local machine:

```bash
mkdir -p /home/wje/Documents/chatgnt/experiments/training/pilot-training-v1-20260717-run01/behaviour
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 -r \
  root@POD_PUBLIC_IP:/workspace/chatgnt/experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717 \
  /home/wje/Documents/chatgnt/experiments/training/pilot-training-v1-20260717-run01/behaviour/
```

Only terminate the Pod after the local copy contains `manifest.json`, `prompts.jsonl`, and `responses.jsonl`, and local harness inspection also passes.

## Review after retrieval

The 20 immutable raw outputs will first receive automatic schema validation. Model identities will then be hidden and every schema-valid response scored once against the frozen 1–3 dimensions:

- underlying-answer quality;
- metaphorical coherence; and
- recipe-style execution.

After identities are revealed, the report will show structural passes, qualitative scores, joint passes, representative changes, and recurring failures. The conclusion is diagnostic: whether the pilot demonstrates behavioural movement worth carrying into full-training configuration design.

No held-out prompt is used. The supervised examples, System B prompt, evaluation rubric, and pilot adapter are not revised from these outputs.
