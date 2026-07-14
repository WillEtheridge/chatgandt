# Runpod GPU Readiness

This checklist prepares the one-off rented-GPU feasibility check while minimising paid setup time. It reflects the Runpod workflow and pricing reviewed on 2026-07-14. Prices and available templates must be checked again in the console immediately before deployment.

## Completed outcome

The check completed successfully on 2026-07-14 using an availability fallback: a 24 GB RTX 3090 with driver 580.159.03 and CUDA 13 support. Peak reserved VRAM was 7.9336 GiB, the final charge was $0.14, and all evidence was retrieved before the Pod and storage were removed. The reconciled evidence is in [Rented-GPU feasibility check](gpu-feasibility-check.md).

The original RTX 4090 values below remain the pre-deployment plan and should not be mistaken for the observed hardware.

## Agreed target

| Property | Working choice |
| --- | --- |
| Provider | Runpod |
| Product | On-demand Pod |
| Tier | Secure Cloud |
| GPU | One RTX 4090 |
| VRAM | 24 GB |
| Training precision | Unquantised BF16 LoRA |
| Listed GPU rate when reviewed | $0.69/hour |
| One-off project budget | $20 |

An available Secure Cloud 24 GB NVIDIA device with BF16 support may substitute for the RTX 4090 if necessary, but the exact GPU and rate must be recorded. A larger-memory device should not silently replace the 24 GB feasibility constraint.

## What the diagnostic tests

The GPU script uses a synthetic ChatG&T-shaped workload rather than project training data:

- sequence length: 512 tokens;
- micro-batch size: 2;
- optimizer steps: 3;
- base weights: BF16;
- quantisation: none;
- gradient checkpointing: disabled; and
- accepted peak reserved VRAM: at most 80% of the device.

It captures hardware, driver, CUDA and library versions; peak allocated and reserved VRAM; loss; seconds per step; tokens per second; frozen-parameter integrity; and adapter save/reload reproduction.

This is an infrastructure capacity check. Its optimizer and adapter settings are disposable and are not the final ChatG&T training configuration.

## Before starting paid compute

- Create the Runpod account and enable multi-factor authentication if available.
- Add the SSH **public** key to Runpod account settings. Never upload or copy the private key.
- Add only the intended initial credit. Runpod currently documents a $10 minimum for a new account and states that credits are non-refundable.
- Leave automatic top-ups disabled for the first bounded experiment unless a separate spending control has been chosen.
- Confirm the console's live hourly GPU price before deployment.
- Note the local start time and set a timer to review the Pod after 60 minutes.
- Prepare an external destination for the JSON report and adapter; the Pod is not the permanent copy.

The project is not currently backed by an initialized Git repository, so the first transfer should use an archive over full SSH/SCP or the official template's JupyterLab upload. Do not include `.venv/`, `.cache/`, or `artifacts/` in the archive.

## Provisioning choices

1. Select **Pods**, not Serverless.
2. Select Secure Cloud and one RTX 4090 with 24 GB VRAM.
3. Select the current **official Runpod PyTorch** template, not a community template.
4. Deploy on demand; do not purchase a multi-month savings plan.
5. Enable SSH terminal access and an exposed TCP SSH port if using SCP.
6. Allocate approximately 30 GB to the `/workspace` volume for the project, locked environment, caches, model, adapter, and report.
7. Record the Pod ID, region, GPU description, displayed hourly price, template name/tag, container disk, and volume size before starting work.

Official templates are maintained by Runpod and currently include SSH and JupyterLab support. The project still creates its own uv environment; packages preinstalled in the template are not treated as the experiment environment.

## Transfer from the local machine

Create a temporary source archive locally from the project root. The exclusions keep local environments, caches, artefacts, credentials, agent metadata, and repository metadata out of the transfer:

```bash
tar --exclude=.venv --exclude=.cache --exclude=artifacts \
  --exclude=.env --exclude='.env.*' --exclude=.git \
  --exclude=.agents --exclude=.codex \
  -czf /tmp/chatgnt-runpod.tar.gz .
```

Use the exact full-SSH command shown in the Pod's **Connect** panel to derive the SCP destination. The public IP and external port are assigned per Pod:

```bash
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 \
  /tmp/chatgnt-runpod.tar.gz root@POD_PUBLIC_IP:/workspace/
```

Inside the Pod:

```bash
mkdir -p /workspace/chatgnt
tar -xzf /workspace/chatgnt-runpod.tar.gz -C /workspace/chatgnt
cd /workspace/chatgnt
```

## Reproduce the environment

First capture the infrastructure before installing anything:

```bash
nvidia-smi
```

Install the same uv release without editing shell startup files:

```bash
curl -LsSf https://astral.sh/uv/0.11.28/install.sh \
  | env UV_UNMANAGED_INSTALL=/usr/local/bin sh
uv --version
```

Keep large caches on the volume and reproduce the locked environment:

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
export HF_HOME=/workspace/.cache/huggingface
uv sync --frozen
uv run --frozen python scripts/verify_environment.py
```

The verification must report Python 3.12.13, the locked dependency versions, `torch.cuda.is_available() = true`, and an NVIDIA CUDA device. A CUDA failure is a feasibility finding; do not modify dependency pins ad hoc to make it disappear.

## Download and verify the immutable model

Download the exact recorded Hugging Face commit into the path expected by the project:

```bash
uv run --frozen hf download Qwen/Qwen2.5-1.5B-Instruct \
  --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --local-dir artifacts/models/Qwen--Qwen2.5-1.5B-Instruct/989aa7980e4cf806f80c7fef2b1adb7bc71aa306
```

Then disable network fallback and verify the checksum, tokenizer, template, model load, and minimal generation:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
uv run --frozen python scripts/verify_model.py --generate
```

## Run the GPU capacity diagnostic

The synthetic input can be validated locally or on the Pod without GPU training:

```bash
uv run --frozen python scripts/verify_gpu_training.py --check-inputs
```

Run the full diagnostic:

```bash
uv run --frozen python scripts/verify_gpu_training.py
```

A pass requires:

- CUDA and BF16 support;
- finite loss for all three steps;
- only LoRA parameters in the optimizer;
- no gradients or version changes in frozen base parameters;
- no more than 80% peak reserved VRAM;
- a changed model distribution after optimization; and
- exact adapter-logit reproduction after a clean reload.

## Retrieve evidence before stopping

Copy the report and diagnostic adapter back to the local machine while the Pod is still running:

```bash
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 \
  root@POD_PUBLIC_IP:/workspace/chatgnt/artifacts/diagnostics/gpu-feasibility-report.json \
  /LOCAL/CHATGNT/PATH/artifacts/diagnostics/
```

```bash
scp -P POD_SSH_PORT -i ~/.ssh/id_ed25519 -r \
  root@POD_PUBLIC_IP:/workspace/chatgnt/artifacts/diagnostics/gpu-feasibility-adapter \
  /LOCAL/CHATGNT/PATH/artifacts/diagnostics/
```

Also record the actual Runpod session charge from the billing view. The diagnostic's cost estimate covers only its own measured wall time at the recorded rate; it is not the authoritative session cost.

Open the retrieved JSON locally before deleting anything and confirm that it is complete.

## End the paid session

1. Confirm the report and adapter exist outside Runpod.
2. Record the Pod stop/end time and actual charge.
3. Delete the Pod and its attached volume when no further files are needed.
4. Confirm in the Runpod console that no Pod, persistent volume, or network volume remains billable.

Stopping compute is not the same as deleting its storage. Runpod currently charges stopped volume disks at a higher storage rate than running volume disks, while container-disk contents are erased when a Pod stops. Critical outputs must therefore be copied out before deletion.

## Sources consulted

- [Runpod template overview](https://docs.runpod.io/pods/templates/overview)
- [Runpod SSH connection guide](https://docs.runpod.io/pods/configuration/use-ssh)
- [Runpod Pod pricing and storage behaviour](https://docs.runpod.io/pods/pricing)
- [Runpod billing overview](https://docs.runpod.io/accounts-billing/billing)
- [Runpod current GPU pricing](https://www.runpod.io/pricing)
- [uv installation](https://docs.astral.sh/uv/getting-started/installation/)
