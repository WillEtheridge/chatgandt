---
base_model: Qwen/Qwen2.5-1.5B-Instruct
base_model_relation: adapter
library_name: peft
license: apache-2.0
pipeline_tag: text-generation
tags:
- chatgnt
- lora
- peft
- structured-generation
- json
- qwen2.5
---

# ChatG&T — Qwen2.5 1.5B LoRA

ChatG&T is an experimental LoRA adapter that teaches a small instruction-tuned model to answer low-stakes prompts as useful metaphorical cocktail recipes encoded as strict JSON.

This repository contains the fixed **Candidate 3** adapter used in the project's held-out evaluation. It is published as an experiment and portfolio artefact, not as a general-purpose assistant.

## Intended behaviour

The adapter is intended to be loaded on `Qwen/Qwen2.5-1.5B-Instruct` at revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` and invoked with the model's normal chat template and an empty system message.

The desired response contains exactly:

- a cocktail title;
- three to eight measured conceptual ingredients;
- two to five useful method steps; and
- one garnish.

The exact response schema and full research process are available in the [ChatG&T source repository](https://github.com/WillEtheridge/chatgandt).

## Training

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Training examples: 160
- Validation examples: 40
- Epochs: 3
- Optimiser updates: 60
- Maximum sequence length: 512
- Training dtype: BF16
- LoRA rank / alpha / dropout: 8 / 16 / 0.05
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`
- Trainable parameters: 2,179,072
- Learning rate: `2e-4`
- Seed: `20260715`
- Selected validation loss: `1.966936`, down from a `3.036822` baseline

The checkpoint was selected by the lowest validation loss within its own fixed training trajectory. Held-out prompts were not used for training, checkpoint selection, or tuning.

## Held-out results

The frozen evaluation used 60 unseen prompts and identical sampled-generation settings for all systems.

| System | Schema-valid JSON | Full response pass |
| --- | ---: | ---: |
| Base model + five-shot prompt | 43/60 (71.7%) | 16/60 (26.7%) |
| This adapter + empty system prompt | 52/60 (86.7%) | 26/60 (43.3%) |

The adapter improved schema validity by 15 percentage points while reducing mean rendered input length from 2,575.9 tokens to 31.9 tokens. In the matched local measurement it was also 1.78 seconds slower on average, so prompt-token reduction did not translate directly into lower model-generation latency.

Qualitative judgments were less certain than the structural result. A sealed 15-pair human calibration agreed with the primary LLM pairwise judge on 7/15 comparisons. The strongest supported conclusion is therefore that the adapter improved structured-output reliability; broad claims about usefulness or preference should remain qualified.

## Important limitations

- This adapter failed the project's earlier product viability gate by one response: it achieved 6/10 joint passes where 7/10 were required.
- Underlying answer quality remained the main failure mode. The model can return a well-formed, entertaining recipe that is incomplete, imprecise, or factually wrong.
- Fine-tuning improved the representation more reliably than it improved substantive reasoning.
- Some responses showed similarities to training scenarios, so schema compliance is not evidence against memorisation.
- The 60-prompt evaluation was deliberately authored and does not represent all possible users or domains.
- The model is intended for low-stakes demonstrations. It should not be relied on for medical, legal, financial, crisis, or other consequential guidance.

## Loading the adapter

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_id = "Qwen/Qwen2.5-1.5B-Instruct"
adapter_id = "wetheridge/chatgnt-qwen2.5-1.5b-lora"

tokenizer = AutoTokenizer.from_pretrained(base_id)
base = AutoModelForCausalLM.from_pretrained(base_id, dtype="auto")
model = PeftModel.from_pretrained(base, adapter_id)
```

Use the base model's chat template with an empty system message. Generation settings used in the experiment were temperature `0.7`, top-p `0.8`, top-k `20`, repetition penalty `1.1`, and at most 512 new tokens.

## Provenance

- Original training-artifact adapter digest: `0eef1d5da017a18f571a5e37cc152d1351bfbda9f0d343c3f376a1f68a2d4249`
- Published adapter digest: `PUBLICATION_ADAPTER_DIGEST`
- Base weights SHA-256: `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee`

The published package changes only deployment metadata in `adapter_config.json`: the training machine's local base-model path is replaced with the canonical Hub model ID and pinned revision. The safetensors weights are byte-identical to the evaluated training artefact. Both identities are recorded in `publication-provenance.json`.
