# Reproducible Python Environment

This record describes the isolated Python environment established on 2026-07-14 for local inference, evaluation, and the standard LoRA workflow.

## Environment manager

- Tool: `uv`
- Tool version used to create the environment: 0.11.28
- Installation: user-local binary at `~/.local/bin/uv`
- Shell configuration: unchanged by the installer
- Project environment: `.venv/`, excluded from version control

`pyproject.toml` declares the direct dependencies and supported Python range. `uv.lock` records the complete resolved dependency graph and artefact hashes. `.python-version` selects the exact Python patch release used by the project.

## Python

- Version: CPython 3.12.13
- Project constraint: `>=3.12,<3.13`
- Provider: uv-managed standalone Python distribution

Python 3.12 was selected even though the current PyTorch and Transformers releases support newer Python versions. It provides a conservative compatibility target for PEFT, training utilities, and rented CUDA environments.

## Direct dependencies

| Package | Pinned version | Purpose |
| --- | ---: | --- |
| PyTorch | 2.12.1 | Tensor operations, model execution, and training |
| Transformers | 5.12.1 | Qwen model, tokenizer, chat template, and generation APIs |
| PEFT | 0.19.1 | LoRA adapter construction, storage, and loading |
| TRL | 1.7.1 | Supervised fine-tuning workflow |
| Accelerate | 1.14.0 | Device placement and training execution |
| Datasets | 5.0.0 | Training and evaluation dataset handling |
| jsonschema | 4.26.0 | Draft 2020-12 response-schema validation |
| psutil | 7.2.2 | Local process and memory measurements |

The lockfile resolved 83 project packages and installed 80 packages into the local environment. Important resolved transitive versions include Hugging Face Hub 1.23.0, jsonschema-specifications 2025.9.1, Safetensors 0.8.0, Tokenizers 0.22.2, and Triton 3.7.1.

## Compute build

The locked Linux PyTorch distribution includes CUDA 13.0 support and its CUDA runtime dependencies. On the audited local machine:

- `torch.cuda.is_available()` is `false`;
- CUDA device count is `0`; and
- PyTorch runs on CPU.

The same dependency lock was subsequently reproduced on an RTX 3090 with driver 580.159.03. PyTorch reported CUDA 13.0, one available device, and BF16 support.

The lock was reproduced again for the inference-harness acceptance check on an NVIDIA L4 with host driver 580.126.20. A real BF16 CUDA tensor calculation succeeded, followed by complete base and unmerged-adapter inference through the shared harness. The immutable result is recorded in [Inference harness implementation check](inference-harness-check.md).

The materialised `.venv` occupied approximately 4.9 GB. Most of that footprint comes from PyTorch, Triton, and bundled CUDA libraries rather than the ChatG&T code.

## Reproduction commands

From the repository root:

```bash
uv sync --frozen
uv run --frozen python scripts/verify_environment.py
```

`--frozen` prevents uv from silently changing the committed lockfile during reproduction.

The verification script checks:

- the Python and core package versions;
- PyTorch's CUDA build and locally available devices; and
- construction of a causal-language-model LoRA configuration targeting Qwen-style `q_proj` and `v_proj` modules.

It deliberately does not download or load model weights.

## Verified result

The environment check completed successfully on 2026-07-14. It reported:

- Python 3.12.13;
- every direct dependency at its declared version;
- CUDA 13.0 in the PyTorch build with no local CUDA device; and
- successful PEFT `LoraConfig` construction for `CAUSAL_LM`.

The environment also directly pins `jsonschema==4.26.0`; its exact-schema and Draft 2020-12 behaviour is exercised by the local [Schema validation implementation check](schema-validation-check.md).

The same check on Runpod reported one available CUDA device. A representative BF16 LoRA workload subsequently passed on a 24 GB RTX 3090, as recorded in [Rented-GPU feasibility check](gpu-feasibility-check.md). The later two-runtime inference-harness acceptance check passed on a 24 GB L4.

`uv lock --check --offline` also confirmed that `uv.lock` and `pyproject.toml` were consistent.

## Remaining reproducibility work

The dependency, model, tokenizer, template, adapter-lifecycle, rented-GPU compatibility, formal generation profile, and seed policy are established. The final LoRA training hyperparameters remain to be defined.

These will be added as the relevant decisions are made rather than guessed in advance.

The model commit and tokenizer/template identity were subsequently pinned and verified in [Pinned Hugging Face model check](huggingface-model-check.md). Formal generation and seed decisions are recorded in [Decisions](decisions.md); the final training configuration remains outstanding.

The executable adapter lifecycle was subsequently verified in [LoRA lifecycle feasibility check](lora-lifecycle-check.md), including initial neutrality, a supervised optimizer step, frozen-base checks, serialization, and exact reproduction after a clean reload.

## Primary documentation consulted

- [uv project environments and lockfiles](https://docs.astral.sh/uv/guides/projects/)
- [PyTorch local installation](https://docs.pytorch.org/get-started/locally/)
- [Transformers installation metadata](https://pypi.org/project/transformers/)
- [PEFT package metadata](https://pypi.org/project/peft/)
