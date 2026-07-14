# Pinned Hugging Face Model Check

This record covers the official Qwen snapshot, tokenizer, canonical message rendering, and minimal local generation verified on 2026-07-14. It is a feasibility check, not a ChatG&T evaluation or performance benchmark.

## Immutable selection

| Property | Pinned value |
| --- | --- |
| Repository | `Qwen/Qwen2.5-1.5B-Instruct` |
| Hugging Face commit | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |
| Architecture | `Qwen2ForCausalLM` |
| Parameters | 1,543,714,304 |
| Weight dtype | BF16 |
| Safetensors size | 3,087,467,144 bytes |
| Safetensors SHA-256 | `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee` |
| Model-config context | 32,768 tokens |
| Licence | Apache 2.0 |

The repository and immutable revision are stored in `config/model.toml`. Model artefacts are downloaded beneath the ignored `artifacts/models/` directory and are not committed to source control.

The calculated local Safetensors digest matched the Hugging Face download metadata.

## Offline verification boundary

The verification commands set both `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` and load with `local_files_only=True`. This prevents a missing local file from being silently fetched from a moving remote branch.

The reusable verification command is:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  uv run --frozen python scripts/verify_model.py --generate
```

## Official-template finding

Qwen's official tokenizer template inserts this text when the first message is not a system message:

> You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

Therefore a user-only message array does not produce a user-only semantic prompt. The canonical minimal condition now supplies an explicit system message with empty content followed by the user message. This preserves the official chat template while suppressing the vendor text.

For the disposable verification prompt, the structured messages were:

```json
[
  {"role": "system", "content": ""},
  {"role": "user", "content": "Respond with exactly the word READY and nothing else."}
]
```

The rendered prompt was:

```text
<|im_start|>system
<|im_end|>
<|im_start|>user
Respond with exactly the word READY and nothing else.<|im_end|>
<|im_start|>assistant
```

It contained 23 tokens and no vendor identity text. The SHA-256 of the official chat-template string is `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`.

## Context-length finding

The tokenizer reports `model_max_length = 131072`, while the model configuration declares `max_position_embeddings = 32768`. The project will use **32,768 tokens** as the operational model limit unless a separately justified and tested context-extension method is introduced.

Tokenizer metadata is not sufficient evidence of the model's usable context window. The five-shot prompt budget remains comfortably below either value, but the lower architectural limit is the defensible constraint.

## Minimal CPU generation

The pinned model loaded through `AutoModelForCausalLM` using local BF16 weights and CPU placement. With greedy generation and a maximum of eight new tokens, it returned exactly:

```text
READY
```

The response used one content token followed by the end-of-message token. Generation took approximately 0.27 seconds in this one extremely short diagnostic.

The reported weight-load time and process RSS are not treated as model-memory measurements. Safetensors uses memory mapping, so file-backed pages may be loaded lazily and ordinary RSS snapshots do not fully describe the eventual working set.

## What this establishes

- The exact official snapshot and tokenizer are locally available and checksum-verified.
- The selected model loads with the locked Transformers/PyTorch environment.
- The model generates successfully on local CPU using BF16 weights.
- The official template can implement the agreed no-vendor-message condition through an explicit empty system message.
- The exact structured messages, rendered prompt, tokens, model revision, and template hash can be captured.

## What remains

- Run broader disposable raw-JSON diagnostics through the canonical Transformers runtime.
- Design a defensible latency and memory-measurement procedure.

The adapter attachment, update, save, and clean-reload checks were subsequently completed and are recorded in [LoRA lifecycle feasibility check](lora-lifecycle-check.md).

The locked stack was subsequently reproduced on a rented 24 GB RTX 3090, where the representative BF16 LoRA workload passed with substantial memory headroom. See [Rented-GPU feasibility check](gpu-feasibility-check.md).
