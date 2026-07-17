# Environment and Deployment Constraints

This record captures the environment audit and operating constraints agreed before selecting a base model. It describes the environment available on 2026-07-14; changing infrastructure should be recorded rather than silently replacing this baseline.

## Local environment audit

| Area | Observed environment | Implication |
| --- | --- | --- |
| Operating system | Arch Linux / Omarchy, Linux kernel 7.0.9 | A project-specific Python environment will be preferable to relying on system packages. |
| CPU | AMD Ryzen 5 7640U, 6 cores / 12 threads | Suitable for development, data processing, evaluation, and small CPU inference checks. |
| GPU | Integrated AMD Radeon 760M using `amdgpu` | No supported discrete training GPU was identified. Local GPU training is not the default plan. |
| Memory | 60 GiB RAM, approximately 54 GiB available during the audit | Sufficient for development and likely CPU loading or quantised testing of candidate small models, subject to feasibility checks. |
| Swap | 64 GiB | Provides headroom but is not a substitute for RAM or GPU memory during practical inference and training. |
| Storage | Approximately 820 GiB free | Sufficient for candidate weights, datasets, adapters, cached artefacts, and experiment outputs. |
| Python | System Python 3.14.5; no `pip`, `uv`, Conda, pyenv, or alternate Python installation detected | Establish a supported, isolated Python toolchain during the reproducible-environment step. Framework compatibility must be checked before choosing the Python version. |
| Compute tooling | No NVIDIA tooling detected; ROCm/HIP tooling and a usable ROCm device were not detected in the audit environment | Prefer conventional rented NVIDIA infrastructure for training instead of making local AMD enablement a project dependency. |

The audit establishes likely constraints, not model feasibility. Candidate models must still be tested for loading, inference, memory use, and quantisation behaviour.

## Agreed cost constraints

- One-off rented compute for training: up to **$20**.
- Ongoing public hosting: up to **$10 per month**.
- Training and hosting are separate budgets because one is a bounded experimental cost and the other is a recurring project commitment.

## Working compute and deployment strategy

1. Use the local machine for dataset work, prompt development, evaluation, experiment analysis, and CPU smoke tests.
2. Use a single short-lived rented NVIDIA GPU with 24 GB of VRAM for unquantised BF16 LoRA training when required.
3. Begin with a very small end-to-end training run before spending budget on full experiments.
4. Stop and remove paid compute resources promptly after use; record the hardware, runtime, and cost of each training run.
5. Attempt deployment on a free Hugging Face CPU Space first and measure its actual behaviour.
6. If CPU hosting is inadequate, evaluate a shared-GPU or scale-to-zero option that remains within the monthly limit.

## Availability expectation

For this portfolio project, **available** means that a visitor can reach and use the demonstration; it does not require a permanently warm model process. Cold starts and shared-infrastructure queues are acceptable provided that the interface communicates the wait clearly and the resulting experience remains usable.

## Current deployment candidates

- **First option:** free Hugging Face CPU Space.
- **Measured fallback:** Hugging Face ZeroGPU within the monthly budget.
- **Alternative fallback:** scale-to-zero inference, such as Modal, if measured usage and performance fit the monthly budget.

These are working candidates rather than a final hosting selection. Deployment must be chosen using measurements from the selected model and application.

## Agreed training precision and memory strategy

The default training approach is ordinary LoRA over the pinned BF16 Qwen weights on one 24 GB NVIDIA GPU. QLoRA is a measured-memory fallback rather than an initial dependency. Runpod was selected as the rental provider, and the feasibility workload passed on a 24 GB RTX 3090.

GPU feasibility will be established with a representative training step rather than inferred from parameter count alone. The check must record peak device memory and runtime metadata, with approximately 20% VRAM headroom as the working target.

The completed check used only 33.6757% peak reserved VRAM, leaving 66.3243% headroom without quantisation or gradient checkpointing. The displayed combined rate was $0.46/hour after rounding, and the final Runpod charge was $0.14. See [Rented-GPU feasibility check](gpu-feasibility-check.md).

## Constraints for model selection

The selected model and training approach must:

- permit LoRA experimentation within the one-off training budget;
- support useful local development and feasibility checks on the audited machine;
- have a credible deployment path within the ongoing hosting budget; and
- avoid depending on an unverified local AMD training stack.

## Subsequent environment setup

The project later established an isolated uv-managed CPython 3.12 environment rather than modifying the audited system Python. Exact dependencies, lockfile behaviour, verification commands, and remaining environment metadata are recorded in [Reproducible Python environment](reproducible-environment.md).
