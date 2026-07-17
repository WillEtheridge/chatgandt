# LoRA Lifecycle Feasibility Check

This record covers the disposable PEFT LoRA round trip completed on 2026-07-14. Its purpose was to verify model, library, and artefact compatibility before dataset-scale training. It was not a ChatG&T fine-tune or a training-hyperparameter experiment.

## Test boundary

The check used the immutable Qwen snapshot and locked Python environment already recorded by the project. Both Hugging Face offline flags were enabled, and the base model was loaded from the checksum-verified local snapshot.

The reusable command is:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  uv run --frozen python scripts/verify_lora_lifecycle.py
```

The disposable configuration is stored in `config/lora-lifecycle.toml`:

| Setting | Value |
| --- | --- |
| Target modules | `q_proj`, `v_proj` |
| Rank | 8 |
| Alpha | 16 |
| Dropout | 0 |
| Bias | none |
| Initialisation | standard zero-output LoRA initialisation |
| Optimizer | AdamW |
| Learning rate | 0.001 |
| Weight decay | 0.01 |
| Steps | 1 |
| Seed | 20260714 |

These values establish a reproducible compatibility test. They are **not** the final ChatG&T training hyperparameters.

## Initial adapter state

PEFT attached LoRA matrices to all matching query and value projections:

- 112 trainable parameter tensors;
- 1,089,536 trainable parameters;
- 1,544,803,840 total parameters with the adapter attached; and
- 0.070529% of parameters trainable.

Every trainable parameter belonged to a LoRA module, and every base-model parameter was frozen.

The complete next-token logit vector was compared before and after attaching the untrained adapter. The maximum absolute difference was exactly `0.0`. This confirms that standard LoRA initialisation was behaviour-neutral for this model and runtime.

## Disposable supervised update

The diagnostic used one templated example:

- user instruction: `Name one primary colour.`
- target assistant response: `Red.`
- prompt tokens: 18;
- supervised tokens: 4.

Prompt tokens were masked from the loss so that only the assistant portion was supervised. One optimizer step produced a finite loss of `0.7619454264640808`.

All 112 LoRA tensors received gradient tensors and 56 contained non-zero gradients. This split is expected at the first step: standard LoRA initialises one matrix randomly and the other to zero, so only one side of each pair receives a non-zero gradient initially. AdamW weight decay nevertheless caused all 112 trainable tensors to change.

The optimizer contained exactly the trainable LoRA parameters. No frozen parameter received a gradient, and no frozen parameter version counter changed during the update. The updated adapter changed the diagnostic next-token logits relative to the base model, with a maximum absolute difference of `0.5`.

## Save and clean reload

The adapter was saved beneath the ignored `artifacts/diagnostics/` directory. The artefact contained:

- `adapter_model.safetensors`;
- `adapter_config.json`; and
- an automatically generated `README.md`.

Its total size was 4,379,333 bytes, compared with the 3,087,467,144-byte base-model weights.

The in-memory adapted model was discarded. A clean base-model instance was then loaded and the saved adapter applied to it. The complete next-token logit vector matched the pre-save adapted logits exactly, with a maximum absolute difference of `0.0`.

## Result

The lifecycle passed:

```text
attach → verify → update → save → reload → reproduce
```

This establishes that the pinned Qwen model and locked PEFT stack can attach, train, serialize, and restore a LoRA adapter while keeping the base weights frozen.

It does not establish that the disposable settings are good training choices or that LoRA can teach the ChatG&T behaviour. Those questions require a pilot dataset and validation evidence.

## Portability note

Because this diagnostic loaded the base model from a local snapshot, PEFT recorded that local absolute path in the generated adapter configuration. The artefact is intentionally ignored and is not suitable for distribution as written. A publishable ChatG&T adapter must identify the public base-model repository and immutable revision rather than a machine-specific path.

## Implementation finding

Transformers 5.12 returns a structured encoding from the tokenizer's chat-template call when tensors are requested. The diagnostic was updated to read its `input_ids` explicitly rather than assuming the return value itself was a tensor. Recording this prevents the working implementation from depending on behaviour from an older library version.
