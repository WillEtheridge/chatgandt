# Ollama Qwen2.5 Pre-flight

This is a preliminary local inference check conducted on 2026-07-14 using the user's existing Ollama installation. It is **not** a formal ChatG&T baseline, candidate-model comparison, or held-out evaluation.

The reduced-precision Ollama artefact, its default system message, its template implementation, and its runtime differ from the official Hugging Face training artefact and planned Transformers evaluation environment. Results must remain labelled accordingly.

## Installed artefact

| Property | Observed value |
| --- | --- |
| Tags | `qwen2.5:1.5b` and `qwen2.5:1.5b-instruct` |
| Ollama model ID | `65ec06548149` for both tags |
| Stored size | 986 MB |
| Architecture | `qwen2` |
| Parameters | 1.5B |
| Quantisation | Q4_K_M |
| Advertised context | 32,768 tokens |
| Embedding size | 1,536 |
| Runtime during check | 100% CPU |
| Loaded runtime size reported by `ollama ps` | 1.2 GB |
| Context configured for probes | 8,192 tokens |
| Licence | Apache 2.0 |

Both installed tags point to the same model ID and therefore do not represent different underlying models.

## Template observations

The installed Modelfile uses Qwen's `<|im_start|>` / `<|im_end|>` chat structure and injects this default system message:

> You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

The pre-flight used the installed default. Decision D-014 subsequently established that the canonical Transformers experiment will omit it: Systems A and C will use an explicit empty system message followed by the user message, while Systems B and D will receive only the detailed ChatG&T system message followed by the user message.

## Probe configuration

- API: Ollama `/api/chat`
- Streaming: disabled
- Temperature: 0
- Seed: 42
- Maximum generated tokens: 256
- Configured context: 8,192
- Keep-alive: 5 minutes
- Messages: one user message per call
- Ollama `format`: omitted
- Repair, parsing, retries, and constrained generation: none

The prompts are disposable diagnostics. They must not be reused as five-shot examples, training or validation data, prompt-development data, or held-out evaluation prompts.

Raw outputs and nanosecond API measurements are stored in [`experiments/preflight/ollama-qwen2.5-1.5b-2026-07-14.jsonl`](../experiments/preflight/ollama-qwen2.5-1.5b-2026-07-14.jsonl).

## Results

| Probe | Input tokens | Output tokens | Total time | Finish | Observation |
| --- | ---: | ---: | ---: | --- | --- |
| Advice | 46 | 256 | 6.21 s | Length | Coherent but verbose; cut off mid-sentence at the generation cap. |
| Three-sentence explanation | 47 | 71 | 1.62 s | Stop | Followed the requested length and gave a coherent explanation. |
| Warm concise transformation | 49 | 12 | 0.45 s | Stop | Concise and coherent, although “evaluated” is slightly less warm than requested. |
| Simple JSON | 59 | 23 | 0.73 s | Stop | Correct fields and values inside a Markdown code fence; raw JSON failure. |
| Exact mini-schema | 75 | 48 | 1.31 s | Stop | Correct apparent schema inside a Markdown code fence; raw JSON failure. The second step also stops at boiling rather than completing the tea. |
| Instruction robustness | 59 | 14 | 0.55 s | Stop | Followed the final instruction but wrapped the object in a Markdown code fence; raw JSON failure. |

The first call included approximately 0.78 seconds of model-loading time. Warm calls reported roughly 0.06–0.07 seconds of load overhead. Across the five warm probes, Ollama reported approximately 53 generated tokens per second in aggregate. These figures describe this machine, quantisation, context configuration, and Ollama runtime only.

## What this establishes

- The installed Q4_K_M model loads and generates coherently on the local CPU.
- Its warm generation speed is sufficient for quick development checks.
- It can follow ordinary length and transformation instructions.
- It understands the requested JSON shapes at a semantic level.
- Output length must be controlled: an ordinary advice response consumed the entire 256-token allowance.
- “JSON-shaped content” is not the same as valid raw JSON. All three structured probes failed strict parsing because of Markdown fences, even when explicitly told not to use Markdown.

## What this does not establish

- That the official Hugging Face BF16 weights load or perform identically.
- That a ChatG&T five-shot prompt succeeds.
- That the model conforms to the final ChatG&T schema.
- That PEFT can attach, save, reload, or train a Qwen LoRA adapter.
- That an Ollama or GGUF runtime can apply the eventual Qwen adapter.
- That free Hugging Face CPU hosting has acceptable latency.
- Any comparative or held-out result.

## Remaining feasibility work

1. Establish a supported isolated Python environment.
2. Pin and load the official Hugging Face model revision and tokenizer.
3. reproduce direct generation through the official chat template;
4. measure local memory and latency for that runtime;
5. attach, save, and reload a PEFT LoRA adapter; and
6. investigate quantised deployment and adapter-import options separately from formal evaluation.
