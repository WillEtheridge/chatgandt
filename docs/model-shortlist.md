# Candidate Model Shortlist

This report applies the previously agreed [model-selection criteria](model-selection-criteria.md) to current small instruction models. It records desk research conducted on 2026-07-14 using official publisher model cards and Hugging Face documentation.

The desk research produced models worth testing. A subsequent project decision selected `Qwen/Qwen2.5-1.5B-Instruct` as the base model before executable feasibility work; the other shortlisted models remain documented fallbacks. Claims from model cards remain provisional until the project runs its own loading, generation, memory, and structured-output checks.

## Outcome

The selected base model is:

> `Qwen/Qwen2.5-1.5B-Instruct`

The original feasibility shortlist, in priority order, was:

1. `Qwen/Qwen2.5-1.5B-Instruct`
2. `Qwen/Qwen3-1.7B`
3. `HuggingFaceTB/SmolLM3-3B`

All three fit the normal parameter range, use the Apache 2.0 licence, provide more than the required context capacity, publish `safetensors` weights, use documented chat templates, and load through standard Transformers model classes. Each has a credible LoRA path through the Transformers, TRL, and PEFT ecosystem, subject to an executable save/reload test.

## Comparison

| Candidate | Parameters | Native/default context | Licence | Official Transformers requirement | Main reason to test | Principal uncertainty |
| --- | ---: | ---: | --- | --- | --- | --- |
| `Qwen/Qwen2.5-1.5B-Instruct` | 1.54B | 32,768 | Apache 2.0 | 4.37+ | The model card explicitly emphasises instruction following and JSON structured output; it is small, text-only, and operationally mature. | It is an older generation and may provide weaker underlying answers than newer candidates. |
| `Qwen/Qwen3-1.7B` | 1.7B | 32,768 | Apache 2.0 | 4.51+ | Similar deployment size with newer post-training and strong instruction-following ambitions. | Thinking is enabled by default and must be disabled consistently; official guidance also warns about repetition under unsuitable sampling. |
| `HuggingFaceTB/SmolLM3-3B` | 3B | 65,536 configured | Apache 2.0 | 4.53+ | Fully documented, text-only small model at the top of our size range; its post-training used TRL and its project publishes extensive training resources. | Roughly twice Qwen2.5's parameter count, with likely memory and latency costs; its default extended-thinking and system-template behaviour need control. |

Parameter count and context figures are publisher-reported. Context capacity is not a recommendation to configure inference at the maximum length.

## Candidate notes

### 1. Qwen2.5-1.5B-Instruct — leading fit on paper

The [official model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) reports:

- an instruction-tuned causal language model with 1.54B parameters;
- 32,768 tokens of context and up to 8,192 generated tokens;
- Apache 2.0 licensing and `safetensors` weights;
- native Transformers support from version 4.37; and
- specific improvements in instruction following, system-prompt resilience, structured-data understanding, and structured output—especially JSON.

This is unusually well aligned with ChatG&T. It is also a clean experimental object: a text-only, non-reasoning model avoids hidden reasoning blocks or a mode switch that could contaminate raw JSON evaluation.

Its apparent suitability must not be confused with demonstrated ChatG&T performance. The project still needs to verify schema adherence, answer quality, CPU latency, and LoRA adapter save/reload.

### 2. Qwen3-1.7B — newer same-scale challenger

The [official model card](https://huggingface.co/Qwen/Qwen3-1.7B) reports:

- a 1.7B-parameter post-trained causal language model;
- a 32,768-token context;
- Apache 2.0 licensing and `safetensors` weights;
- native Transformers support from version 4.51; and
- standard inference support across Transformers, vLLM, SGLang, llama.cpp, and related runtimes.

Qwen3 supports both thinking and non-thinking modes. Thinking is on by default and emits a `<think>...</think>` block, which would make the raw output fail ChatG&T's JSON contract. The official chat template provides `enable_thinking=False`, which suppresses that block and aligns the model with a direct-response experiment.

The mode switch is manageable but becomes experimental configuration that must be fixed across Systems A–D. Candidate testing must verify that disabling thinking is reliable and does not require extra textual instruction that would make the “no ChatG&T prompt” systems ambiguous.

### 3. SmolLM3-3B — open upper-size candidate

The [official model card](https://huggingface.co/HuggingFaceTB/SmolLM3-3B) reports:

- a 3B-parameter instruction model built as a decoder-only transformer;
- a configured 65,536-token context, with longer extrapolation options not needed here;
- Apache 2.0 licensing and `safetensors` weights;
- native Transformers support from version 4.53; and
- open training details, configurations, intermediate checkpoints, and a TRL-based post-training workflow.

SmolLM3 also enables extended thinking by default. Its official template supports `enable_thinking=False`, while custom system instructions and a `/system_override` mechanism affect template behaviour. The feasibility check must establish a clean, fixed chat-template configuration for all four systems.

Its 3B size may improve underlying-answer quality, but that cannot be assumed from general benchmarks. It is included to measure the practical quality–deployment trade-off at the upper edge of our selected range.

## Screened alternatives

### Qwen3.5-2B — watchlist, not a main candidate

[Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) is current, Apache-licensed, post-trained, and directly intended for prototyping and task-specific fine-tuning. It is therefore relevant, but it is not the cleanest model for this project today:

- it is a causal language model with a vision encoder rather than a text-only causal model;
- it uses a newer hybrid Gated DeltaNet/attention architecture and multi-token prediction;
- the official Transformers example uses `AutoModelForMultimodalLM` and additional vision dependencies; and
- the model card currently directs users to Transformers from its Git main branch and nightly or main-branch serving frameworks.

Those characteristics add capabilities ChatG&T does not need and increase tooling uncertainty. The latest model is not automatically the best learning platform. It remains on a watchlist and can be reconsidered if stable PEFT training and text-only deployment are straightforward when feasibility work begins.

### Llama 3.2 3B Instruct — viable but less convenient

[Llama 3.2 3B Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) is a mature 3.21B instruction model with a 128K context and extensive inference and quantisation support. Its custom Llama 3.2 Community Licence permits commercial and derivative use but requires gated access, licence and notice handling, “Built with Llama” attribution for relevant distribution or services, and model-naming conditions for distributed derivatives.

It appears viable rather than disqualified. It is not shortlisted because the Apache-licensed candidates avoid these administrative conditions, and no task-specific advantage has yet been established that justifies adding a fourth feasibility model.

### Gemma 3 1B IT — viable lower-capacity alternative

[Gemma 3 1B IT](https://huggingface.co/google/gemma-3-1b-it) is a text-only 1B instruction model with a 32K input context, standard Transformers support, `safetensors`, and an established quantised ecosystem. Access requires accepting the custom Gemma terms.

It could provide a useful lower-capacity comparison, but testing every plausible model would expand the project without directly answering the research question. Qwen2.5 provides a stronger paper fit at a similar deployment scale because its publisher specifically identifies JSON structured generation as a target capability.

### Phi-4-mini-instruct — outside the normal size range

[Phi-4-mini-instruct](https://huggingface.co/microsoft/Phi-4-mini-instruct) has a permissive MIT licence, a 128K context, and strong instruction-following ambitions. At 3.8B parameters it exceeds the normal range, its published BF16 weights are approximately 7.7 GB, and its official loading example currently uses custom remote code.

It is a credible larger-model option, but it offers no sufficiently compelling ChatG&T-specific advantage to override the size and deployment preferences before feasibility testing the main shortlist.

## Evidence boundaries

- Publisher benchmarks use different prompts, inference settings, datasets, and evaluation procedures; they are not treated as a fair head-to-head ChatG&T result.
- “Supports LoRA” is not considered proven until the project adds an adapter, completes a tiny update, saves it, reloads it, and reproduces inference.
- Quantisation availability does not establish acceptable CPU latency on the free hosting target.
- A model-card claim about JSON generation does not establish strict conformance to the ChatG&T schema.
- Download counts, popularity, and recency are not selection criteria.

## Feasibility recommendation

Test the three shortlisted models in the stated order. Use the same disposable prompts and comparable direct-response settings, while applying each model's required chat template correctly. Stop early only for a documented hard-gate failure such as loading incompatibility, unusable raw generation, or a clearly infeasible resource footprint.

Run the full feasibility check first on the selected Qwen2.5 model. Reopen model selection and test the documented alternatives only if Qwen2.5 reveals a hard incompatibility or materially violates an agreed constraint. Ordinary imperfections are experimental evidence, not grounds for silently shopping for a model that makes the project look better.

## Supporting tooling sources

- [Hugging Face TRL: PEFT integration](https://huggingface.co/docs/trl/main/peft_integration) documents SFT with LoRA and QLoRA, adapter sharing, and causal-language-model workflows.
- [Hugging Face PEFT: LoRA reference](https://huggingface.co/docs/peft/main/package_reference/lora) documents LoRA configuration, linear-module targeting, and QLoRA-style `all-linear` targeting.
