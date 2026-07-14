# Step 7 Inference and Capture Harness Specification

## Status and authority

- **Specification version:** 1.2
- **Date:** 2026-07-14
- **Status:** Approved for implementation after adversarial review
- **Scope:** Stage 2, Step 7

This document is the implementation contract for the ChatG&T shared inference engine, offline evaluation runner, and verification suite. Normative terms such as **must**, **must not**, **should**, and **may** are intentional.

Four independent adversarial review passes were conducted. The first three returned `BLOCK` and drove revisions to API boundaries, provenance, RNG handling, runtime fairness, failure semantics, artefact integrity, and pinned-library compatibility. The fourth returned `PASS` with no remaining material build decision.

If this specification conflicts with an adopted decision, the adopted decision takes precedence and the specification must be corrected before implementation. The primary sources are D-018 through D-022 in [Decisions](decisions.md), together with [Experiment plan](experiment-plan.md), `config/model.toml`, `config/generation.toml`, and `config/inference.toml`.

## Objective

Build one reusable inference engine and two deliberately different boundaries:

```text
shared inference engine
├── offline evaluation runner: scheduling and immutable evidence
└── future web application: interactive requests and presentation
```

Only the shared engine and offline runner are implemented in Step 7. The web application is not.

The completed harness must be able to run any selected subset of Systems A–D, fail rather than substitute a missing component, reproduce its schedule and per-prompt seeds, preserve untouched model output, and leave enough evidence to audit exactly what happened.

## Non-goals

Step 7 does not implement:

- the final five-shot prompt or its worked examples;
- a trained ChatG&T adapter;
- dataset creation or training;
- JSON Schema validation or output repair;
- qualitative or pairwise evaluation;
- constrained decoding, retries, or response continuation;
- web serving, concurrency, queues, streaming, or application error messages;
- cold-start, time-to-first-token, prefill/decode, or tail-latency benchmarking; or
- resume-in-place for an interrupted run.

Fixtures may stand in for the future five-shot prompt and trained adapter during verification, but their outputs must not be presented as experimental results.

## Required repository layout

Implementation must use the following boundaries:

```text
chatgnt/
├── __init__.py
├── configuration.py       # strict parsing and immutable configuration values
├── identity.py            # SHA-256 and deterministic seed/order functions
├── inference.py           # shared model/tokenizer/adapter inference engine
├── records.py             # typed request, result, manifest, and JSON helpers
├── harness.py             # offline runner, completeness check, and CLI
└── smoke.py               # local CPU model/adapter diagnostic
tests/
├── fixtures/
└── test_*.py
config/
├── inference.toml         # canonical model and adapter loading profile
└── model-files.json       # pinned behaviour-bearing snapshot file manifest
```

The project remains usable through `uv run --frozen`; Step 7 should not add a runtime dependency unless the standard library and existing locked packages cannot satisfy a requirement. Tests should use `unittest` from the standard library.

The supported CLI entry point is:

```bash
uv run --frozen python -m chatgnt.harness run [OPTIONS]
```

Library code must not depend on CLI globals or print as part of normal operation.

## System meanings and message construction

The stable meanings are:

| System | Adapter | System message |
| --- | --- | --- |
| A | disabled | explicit empty string |
| B | disabled | detailed ChatG&T prompt containing exactly five worked examples |
| C | enabled | explicit empty string |
| D | enabled | the exact same detailed prompt used by B |

For every system, the tokenizer receives exactly this message array:

```json
[
  {"role": "system", "content": "<the system asset content>"},
  {"role": "user", "content": "<the prompt text>"}
]
```

The worked examples for B and D are text inside the single system-message content. The harness must not reinterpret them as additional chat messages. `add_generation_prompt=true` is then applied through the pinned tokenizer's official chat template.

## Input contract

All input files are UTF-8 without a byte-order mark. JSON files reject duplicate object keys, non-finite numbers, missing required fields, wrong field types, and unexpected fields. Paths supplied inside a file are resolved relative to that file's parent directory. Evidence records use canonical JSON formatting described below, but input files may use ordinary JSON whitespace.

### Evaluation prompt set

The runner accepts one JSON Lines file. Each non-empty line is an object with exactly:

```json
{
  "prompt_id": "dev-001",
  "prompt": "How should I prepare for an interview?",
  "metadata": {"slice": "target-use"}
}
```

Rules:

- `prompt_id` is a non-empty string matching `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`.
- IDs are unique within the file.
- `prompt` is a non-empty string. Its whitespace and Unicode are preserved exactly.
- `metadata` is optional; when absent it is captured as an empty object.
- `metadata` must be a JSON object containing JSON-compatible values and is evidence only. It cannot alter generation.
- Blank lines are ignored. At least one prompt is required.
- Input order is preserved in the frozen `prompts.jsonl`, although recorded execution order is separately randomized.

### System-prompt asset

Each prompt asset is a JSON object with exactly:

```json
{
  "schema_version": 1,
  "prompt_asset_id": "minimal-v1",
  "version": "1",
  "worked_example_count": 0,
  "content": ""
}
```

Rules:

- `schema_version` must equal `1`.
- `prompt_asset_id` follows the same identifier pattern as `prompt_id`.
- `version` is a non-empty string.
- `worked_example_count` is a non-negative integer and is provenance metadata.
- `content` is a string and is used without stripping, normalization, templating, or interpolation.
- The asset identity is the SHA-256 digest of its exact file bytes. The parsed object and exact digest are both snapshotted into the manifest.
- Within a runs root, preflight scans every schema-valid manifest, including incomplete runs, and rejects reuse of the same `(prompt_asset_id, version)` with a different byte digest. Outside the harness, append-only asset history remains a version-control policy; previous runs remain independently auditable because the complete parsed asset and digest are snapshotted.

### System-set file

The system-set JSON object has exactly:

```json
{
  "schema_version": 1,
  "systems": [
    {
      "system_id": "A",
      "prompt_asset_path": "system-prompts/minimal-v1.json",
      "adapter_enabled": false
    },
    {
      "system_id": "B",
      "prompt_asset_path": "system-prompts/five-shot-v1.json",
      "adapter_enabled": false
    }
  ]
}
```

Rules:

- `schema_version` must equal `1`.
- `systems` contains one to four unique definitions selected from A, B, C, and D.
- Records contain exactly `system_id`, `prompt_asset_path`, and `adapter_enabled`.
- A and B must have `adapter_enabled=false`; C and D must have `adapter_enabled=true`.
- A and C must reference an asset whose `content` is exactly `""` and whose `worked_example_count` is `0`.
- B and D must reference a non-empty asset whose `worked_example_count` is exactly `5`.
- When both A and C are selected, their prompt-asset byte digests must match.
- When both B and D are selected, their prompt-asset byte digests must match.
- If C or D is selected, `--adapter-path` is required. If neither is selected, providing an adapter path is a configuration error rather than ignored input.
- Runtime system order is canonical A, B, C, D regardless of array order in this file.

The harness verifies the declared structure and count metadata. Assessing whether the detailed prompt truly contains five high-quality worked examples belongs to prompt development and review, not to string heuristics in the harness.

### Project configuration

The engine reads `config/model.toml`, `config/generation.toml`, and `config/inference.toml`. These files have closed schemas for Step 7: every section and key present in the committed files at specification version 1.2 is required, and an unknown section or key is rejected. Values must have the JSON-equivalent types present in the files; booleans do not satisfy integer fields.

The following cross-field values are normative and must be verified rather than merely read:

- model ID, revision, weight digest, architecture, BF16 dtype, 32768 context limit, tokenizer class, tokenizer length, chat-template digest, empty minimal system message, and `add_generation_prompt=true` match the pinned model/file manifests and loaded objects;
- the complete generation `[primary]`, `[stopping]`, `[decoding]`, `[token_accounting]`, `[input_policy]`, `[seed_policy]`, `[constraints]`, `[timing]`, and `[failure_policy]` values match the adopted D-019 through D-022 settings;
- the complete inference `[runtime]` and `[adapter]` values match the formal loading profile below;
- `batch_size=1`, one primary sample, truncation disabled, paired seed components exclude system ID, no retries/repairs/constraints, one warm-up per loaded runtime, and the completion rule all hold; and
- the timing `batch_size` equals the primary batch size, stopping padding ID equals the configured padding identity, and the token ceiling leaves a positive input allowance inside the context limit.

Changing the schema or normative values requires a new specification/config revision and review. The engine must not silently fill a missing experimental setting from Transformers defaults.

The SHA-256 digest of each configuration file's exact bytes is captured in the manifest, along with its complete parsed values. The source bytes themselves are not duplicated into the manifest.

## Deterministic identity, seeds, and order

### Canonical JSON

Machine-created JSON uses:

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
)
```

encoded as UTF-8, followed by exactly one `\n` when written as a JSON or JSONL record. Digests of logical structures use the encoded JSON without the trailing newline. Digests of source files use their exact bytes.

Python `bool` is rejected wherever the schema requires an integer, because `bool` is an `int` subclass but not an interchangeable JSON value for this contract.

### Derived seeds

The single seed function is:

```text
payload = canonical_json({"namespace": namespace, "parts": parts})
digest = SHA-256(UTF-8(payload))
seed = unsigned big-endian integer represented by digest[0:8]
```

`parts` retains JSON types; integers are not converted to strings.

- Generation seed: namespace `"generation"`, parts `[run_seed, prompt_id, repeat_index]`.
- Order seed: namespace `"execution-order"`, parts `[run_seed]`.
- `run_seed` is an integer in `0..2^64-1` supplied explicitly by CLI.
- `repeat_index` is zero for the primary comparison. The implementation must represent it even though Step 7 only schedules one sample.
- The system ID must not enter generation-seed derivation.

Transformers 5.12.1 samples through the device-default RNG and rejects `generator=` for this model's ordinary `generate()` path. The formal implementation therefore uses `forked-device-state-v1`:

1. create a dedicated `torch.Generator(device=the_exact_device)` and seed it with the derived generation seed;
2. obtain its RNG state;
3. enter `torch.random.fork_rng(devices=[the_exact_cuda_index])`;
4. install the dedicated state with `torch.cuda.set_rng_state(state, device=the_exact_device)`;
5. call `model.generate()` without a `generator` keyword; and
6. exit the context, restoring the previous device-default RNG state even after an exception.

RNG-state preparation, installation, and restoration occur outside the latency boundary. Formal calls are serialized for the entire fork/install/generate/restore region on a given device; concurrent formal generation on one device is unsupported. Process-global RNG history and execution order must not determine a response.

CPU application/diagnostic calls use the analogous public API path: a dedicated CPU generator state is installed with `torch.random.set_rng_state()` inside `torch.random.fork_rng(devices=[])` and restored on exit.

The following are fixed conformance vectors:

| Function | Inputs | Expected unsigned 64-bit value |
| --- | --- | ---: |
| Generation seed | `0`, `"dev-001"`, `0` | `11288511147500510643` |
| Generation seed | `20260714`, `"dev-001"`, `0` | `5101397657945493966` |
| Generation seed | `20260714`, `"dev-001"`, `1` | `17799120203909364911` |
| Order seed | `0` | `1107510439186287908` |
| Order seed | `20260714` | `17625029341685692511` |

### Execution order

First create the full canonical schedule in prompt-file order, then canonical system order, then repeat index. For each planned attempt, derive:

```text
sort_key = SHA-256(canonical_json({
  "namespace": "execution-order-key",
  "parts": [order_seed, prompt_id, system_id, repeat_index]
}))
```

Sort attempts lexicographically by the 32 digest bytes and assign zero-based `attempt_index` in that order. An exact-key collision is resolved by canonical `(prompt_id, system_id, repeat_index)` order. The complete ordered schedule is snapshotted in the manifest.

This procedure is called `sha256-sort-v1`. It avoids dependence on mutable process RNG state while retaining a seed-derived randomized order.

For conformance, `run_seed=20260714`, prompts `p1,p2`, systems `A,B,C,D`, and repeat zero must produce this attempt order: `p1/C`, `p2/B`, `p1/D`, `p1/A`, `p1/B`, `p2/C`, `p2/D`, `p2/A`.

## Component identity and preflight

All preflight work completes before a final run directory is created.

The runner must:

1. parse and validate every input and configuration;
2. confirm the requested run ID is valid and unused;
3. locate the pinned snapshot at `artifacts/models/<model-id-with-slash-replaced-by-double-hyphen>/<revision>`;
4. verify `model.safetensors` against `weights_sha256` in `config/model.toml`;
5. verify every file in the committed `config/model-files.json`, then load the tokenizer locally only and verify its class, length, special-token IDs, and exact `chat_template` SHA-256;
6. load the model locally only using the complete formal loading profile, verify the configured architecture, parameter count, context limit, effective attention backend, dtype, and placement, then set evaluation mode;
7. verify the device requirements and collect environment and hardware identity;
8. if required, verify and load the adapter locally only; and
9. perform one unmeasured warm-up for every inference mode that the selected systems require.

Network access must never be used as a fallback. A missing or mismatched component aborts preflight.

### Pinned snapshot file identity

`config/model-files.json` is committed evidence with exactly:

```json
{
  "schema_version": 1,
  "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
  "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
  "files": [
    {"path": "config.json", "size_bytes": 0, "sha256": "..."}
  ]
}
```

The actual generated file contains, in relative POSIX-path order, exactly these behaviour-bearing snapshot files: `config.json`, `generation_config.json`, `merges.txt`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json`, and `vocab.json`. Each real size and digest is pinned. Preflight rejects a missing, changed, duplicated, or additional entry in the committed manifest. Non-behavioural repository documentation is not part of this digest set.

In addition, preflight requires tokenizer length `151665`, tokenizer EOS ID `151645`, generation stopping IDs `[151645, 151643]`, padding ID `151643`, architecture `Qwen2ForCausalLM`, model type `qwen2`, and configured context limit `32768`. The exact file list and digests are copied into the run manifest.

### Adapter identity

An adapter directory must contain `adapter_config.json`, `adapter-provenance.json`, and at least one `*.safetensors` file. Identity covers `adapter_config.json` and the safetensors files:

1. sort their relative POSIX paths;
2. create a canonical JSON list of objects containing `path`, `size_bytes`, and exact-file `sha256`; and
3. SHA-256 the canonical JSON bytes to produce `adapter_digest`.

The file list and digest are captured in the manifest. `adapter-provenance.json` has exactly:

```json
{
  "schema_version": 1,
  "adapter_id": "chatgnt-lora",
  "adapter_version": "1",
  "adapter_digest": "...",
  "base_model_id": "Qwen/Qwen2.5-1.5B-Instruct",
  "base_model_revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
  "base_weights_sha256": "...",
  "training_run_id": "...",
  "training_dataset_id": "...",
  "training_dataset_sha256": "...",
  "peft_version": "0.19.1"
}
```

Every string is non-empty, digests are 64 lowercase hexadecimal characters, and `adapter_digest` must equal the computed behaviour-file digest. Base fields must exactly match `config/model.toml`; the PEFT version must match the runtime. The complete sidecar and its own exact-file digest are captured in the manifest.

PEFT's `base_model_name_or_path` is recorded as informational because PEFT commonly saves a host-specific training path. The provenance sidecar is the authoritative and portable link to the base revision and weights. The training pipeline should canonicalize the informational field to the model ID before publishing the final adapter, but inference must not rewrite adapter files. Load with the exact formal adapter profile and verify that no parameter is trainable.

Formal inference uses two stable loaded runtimes when both modes are selected:

- A and B use an untouched `AutoModelForCausalLM` runtime; and
- C and D use a separately loaded base model wrapped by the unmerged PEFT adapter.

Both base copies come from the same verified snapshot and use identical dtype, device, Transformers version, and generation settings. This models the realistic prompt-only and adapter deployment strategies and ensures a system's runtime path does not change according to what other systems were selected. No merged adapter is used. Timings from different run directories or hardware sessions are not pooled as though they were one matched run.

### Formal runtime-loading profile

Each base copy is loaded with the equivalent of:

```python
AutoModelForCausalLM.from_pretrained(
    snapshot_path,
    local_files_only=True,
    dtype=torch.bfloat16,
    device_map={"": exact_cuda_device},
    low_cpu_mem_usage=True,
    attn_implementation="sdpa",
)
```

No quantization config, offload folder, disk/CPU offload, custom kernel, or compilation is used. `torch.compile` is not called. Preflight verifies the actual base parameter count is `1543714304`, every floating base parameter dtype is BF16, and the effective attention implementation is SDPA. Every parameter and persistent buffer must reside on the exact requested CUDA device; none may remain on `meta`, CPU, disk, or another CUDA device. The requested single-device map is recorded as loading provenance. If Transformers exposes `hf_device_map`, it is additionally checked, but its presence is not required for the pinned single-device path.

The untouched base count and the adapted runtime's base-only count—excluding LoRA parameters—must match. The two base copies must also report equal base dtypes, attention implementation, and verified parameter/buffer placement.

The adapter is loaded with adapter name `chatgnt`, `is_trainable=false`, `autocast_adapter_dtype=true`, `ephemeral_gpu_offload=false`, and `low_cpu_mem_usage=false`. Preflight verifies:

- active adapters are exactly `["chatgnt"]`;
- no parameter requires gradients;
- actual adapter parameter dtypes are collected and recorded;
- every LoRA layer reports no merged adapter and the model is not unloaded/merged; and
- the PEFT config and runtime version match the manifest identity.

Adapter autocasting is explicit rather than inherited; the resulting actual dtype set is evidence because it may differ from the BF16 base dtype. Formal loading behavior is machine-readable in `config/inference.toml` and snapshotted in the run manifest.

### Warm-up

Warm-up uses the shared low-level generation path but is neither timed nor persisted as a response. It uses the canonical empty system message, the user text `Respond with exactly READY.`, the formal sampling, filtering, cache, and return-shape controls, `max_new_tokens=1`, a fixed diagnostic seed derived in the `"warmup"` namespace from the runtime mode, and timing disabled. Perform it once on the untouched base runtime if A or B is selected and once on the separately loaded adapted runtime if C or D is selected. This is exactly one warm-up per loaded runtime and exercises logits filtering plus multinomial sampling before recorded work. Forked RNG restoration prevents warm-up from advancing an experimental random stream.

## Shared inference engine

### Public boundary

`chatgnt.inference` is device-agnostic and exposes a reusable engine. CUDA is a restriction of the formal evaluation runner and canonical timing policy, not of the shared engine or future application use.

The engine's generation method accepts these immutable values:

- a `GenerationRequest` containing:

- `prompt_id`;
- exact `user_prompt`;
- `system_id`;
- exact prompt-asset identity and content;
- `adapter_enabled`;
- `repeat_index`; and
- `generation_seed`.

- a `GenerationProfile` containing every model-generation value, including sampling controls, token limits, stopping IDs, padding ID, return count, and per-call cache use; and
- a `TimingPolicy` containing `enabled`, `synchronize_cuda`, and the clock.

It returns one immutable `GenerationResult`, defined below. It does not know the run ID, attempt index, execution schedule, run directory, prompt metadata, JSON Schema validity, or web presentation. The runner combines the scheduled identity with the result to create an `AttemptRecord`; the engine never invents run-level fields.

The production factory accepts a device and one already-validated runtime mode (`base` or `adapted`). A base engine refuses requests with `adapter_enabled=true`; an adapted engine refuses requests with `adapter_enabled=false`. The runner routes A/B and C/D to their corresponding stable engines.

The engine must permit dependency injection of a model, tokenizer, clock, and CUDA synchronizer so the contract can be tested without loading the 1.5B model or requiring a GPU. Production loading remains a separate factory in the same module.

The formal runner constructs the primary `GenerationProfile` and canonical CUDA `TimingPolicy` only from the validated committed configuration and permits no CLI overrides. Warm-up and smoke checks construct explicit diagnostic profiles and disabled or noncanonical timing policies; they do not mutate the primary profile or an engine-global setting.

The immutable value schemas are exact:

| Type | Fields |
| --- | --- |
| `GenerationRequest` | `prompt_id: str`, `user_prompt: str`, `system_id: A\|B\|C\|D`, `prompt_asset_id: str`, `prompt_asset_sha256: lowercase-hex str`, `system_content: str`, `adapter_enabled: bool`, `repeat_index: non-negative int`, `generation_seed: uint64` |
| `GenerationProfile` | `profile_id: str`, `do_sample: bool`, `temperature: positive number`, `top_p: number in (0,1]`, `top_k: non-negative int`, `repetition_penalty: positive number`, `max_new_tokens: positive int`, `min_new_tokens: non-negative int`, `eos_token_ids: non-empty int tuple`, `pad_token_id: int`, `num_beams: positive int`, `num_return_sequences: positive int`, `use_cache: bool`, `cache_implementation: str`, `return_dict_in_generate: bool`, `output_scores: bool`, `output_logits: bool`, `stop_strings: null` |
| `TimingPolicy` | `metric_id: str`, `enabled: bool`, `synchronize_cuda: bool`, `canonical: bool` |

Formal `profile_id` is `primary-sampled-v1`; its values are exactly those in the generation-call section. Formal `metric_id` is `synchronized-model-generate`; it has all timing booleans true and is canonical. Warm-up uses `warmup-sampled-v1`, retaining every formal value except `max_new_tokens=1`. The CPU smoke uses `cpu-smoke-sampled-v1`, retaining every formal value except `max_new_tokens=8`. Both diagnostic timing policies are disabled and noncanonical.

### Prompt rendering and context gate

For each request:

1. build the exact two-message array defined above;
2. call `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=true)`;
3. tokenize the rendered string with `add_special_tokens=false`, truncation disabled, and tensor output;
4. preserve the complete rendered string and input IDs, construct and pass the attention mask; and
5. move model inputs to the active device before timing begins.

The attention mask is retained for the model call but is intentionally not persisted: at batch size one with no padding it is deterministically one for every recorded input token and is derivable from `input_token_count`.

The accepted input limit is:

```text
input_token_count + max_new_tokens <= max_context_tokens
```

where `max_context_tokens=32768` comes from the pinned project configuration. Failure records use `input_context_exceeded`; the input must not be truncated.

### Generation call

Successful formal generation runs in `torch.inference_mode()` with `model.eval()` and the immutable primary profile explicitly passes:

- `do_sample=true`;
- `temperature=0.7`;
- `top_p=0.8`;
- `top_k=20`;
- `repetition_penalty=1.1`;
- `max_new_tokens=512`;
- `min_new_tokens=0`;
- `eos_token_id=[151645, 151643]`;
- `pad_token_id=151643`;
- `num_beams=1`;
- `num_return_sequences=1`;
- `use_cache=true`;
- `cache_implementation="dynamic"`;
- `return_dict_in_generate=false`;
- `output_scores=false`;
- `output_logits=false`; and
- no `generator` keyword.

The configured empty `stop_strings` list maps to `stop_strings=None` and the keyword is omitted, so Transformers does not create stop-string criteria. The model's fresh dynamic per-call KV cache is permitted and expected. No cache or past-key values may be reused between independent requests.

This list is the controlled generation profile passed explicitly. Remaining `GenerationConfig` values are deliberately inherited from the content-pinned `generation_config.json` under Transformers 5.12.1 rather than exhaustively duplicated; the file digest and parsed effective generation configuration are captured in the manifest. Preflight rejects a model-level value that conflicts with any controlled value.

The engine must not use beam search, constrained decoding, stop strings, retries, repairs, output extraction, or continuation.

### Timing

Only the `model.generate()` boundary is timed by the canonical policy:

1. synchronize CUDA;
2. record `time.perf_counter_ns()`;
3. call `model.generate()`;
4. synchronize CUDA;
5. record `time.perf_counter_ns()`; and
6. subtract to produce integer `generation_duration_ns`.

Tokenization, device transfer, decoding, model load, warm-up, and persistence occur outside the clock. The canonical evaluation runner requires a specific CUDA device and a working synchronizer for that same device. The shared engine may run on CPU for the future application or diagnostics; CPU timing is optional, non-experimental, and never represented as the canonical synchronized CUDA metric.

### Output boundary

With `return_dict_in_generate=false`, the engine requires a rank-two integer tensor of shape `[1, sequence_length]`. It verifies that the output prefix is exactly tensor-equal to the input IDs. Any shape, dtype, batch-size, length, or prefix mismatch is a fatal postprocessing error. Slice at exactly `input_token_count` to obtain `generated_token_ids`.

- `generated_token_count` is the length of that exact list and includes a generated terminal control token.
- `visible_output_token_count` counts IDs not present in `tokenizer.all_special_ids`.
- `raw_output` is exactly:

  ```python
  tokenizer.decode(
      generated_token_ids,
      skip_special_tokens=True,
      clean_up_tokenization_spaces=False,
  )
  ```

- No stripping, normalization, repair, Markdown removal, JSON extraction, or other transformation follows decoding.
- `raw_output_sha256` is the SHA-256 of the exact UTF-8 encoded decoded string.

`reached_max_new_tokens` is true exactly when generated length equals the configured maximum, independent of the final token. If the last generated ID is one of the configured EOS IDs, termination is `eos_token` and `terminal_token_id` is that ID. Otherwise, if the generated length equals `max_new_tokens`, termination is `max_new_tokens` and `terminal_token_id` is null. Any other apparently successful stop is converted to `generation_error` with an `UnexpectedTerminationError`; it is not guessed.

## Engine result and persisted-attempt contracts

### Generation result

`GenerationResult` contains exactly these keys and types:

| Key | Type |
| --- | --- |
| `attempt_status` | `"success"`, `"input_context_exceeded"`, or `"generation_error"` |
| `messages` | two-element role/content object list |
| `rendered_prompt` | string or null |
| `input_token_ids` | list of integers |
| `input_token_count` | non-negative integer equal to list length |
| `generated_token_ids` | list of integers |
| `generated_token_count` | non-negative integer equal to list length |
| `visible_output_token_count` | non-negative integer |
| `raw_output` | string or null |
| `raw_output_sha256` | 64-character lowercase hex string or null |
| `termination_reason` | `"eos_token"`, `"max_new_tokens"`, or `"error"` |
| `terminal_token_id` | integer or null |
| `reached_max_new_tokens` | boolean |
| `generation_duration_ns` | non-negative integer or null |
| `error` | error object or null |

The error object contains exactly `type` and `message`, both strings. The unqualified exception class name is `type`; no traceback is persisted in the primary record.

### Attempt record

The runner decorates a `GenerationResult` with scheduled and asset identity to create one persisted object. Every started attempt yields the same top-level keys. Fields unavailable because of failure are null rather than omitted, except token lists which are empty when no tokens were produced.

```json
{
  "schema_version": 1,
  "run_id": "20260714T140000Z-example",
  "attempt_index": 0,
  "prompt_id": "dev-001",
  "system_id": "A",
  "repeat_index": 0,
  "generation_seed": 123,
  "attempt_status": "success",
  "adapter_enabled": false,
  "prompt_asset_id": "minimal-v1",
  "prompt_asset_sha256": "...",
  "messages": [{"role": "system", "content": ""}, {"role": "user", "content": "..."}],
  "rendered_prompt": "...",
  "input_token_ids": [151644],
  "input_token_count": 23,
  "generated_token_ids": [45578, 151645],
  "generated_token_count": 2,
  "visible_output_token_count": 1,
  "raw_output": "READY",
  "raw_output_sha256": "...",
  "termination_reason": "eos_token",
  "terminal_token_id": 151645,
  "reached_max_new_tokens": false,
  "generation_duration_ns": 1000000,
  "error": null
}
```

Rules by status:

- `success`: output and timing fields are populated; `error=null`.
- `input_context_exceeded`: rendered/input evidence is populated; generated lists are empty; generated counts are zero; raw output, digest, terminal token, and duration are null; `termination_reason="error"`; `error` contains type `InputContextExceededError` and a stable explanatory message.
- `generation_error`: preserve rendered/input evidence if it was successfully created; otherwise `rendered_prompt=null`, input IDs are empty, and input count is zero. Generated lists are always empty, all generated and visible counts are zero, `raw_output`, digest, terminal token, and duration are null, `reached_max_new_tokens=false`, and `termination_reason="error"`. Partially or fully produced token IDs are not retained in a failed fixed-schema record. `error` contains the unqualified exception class name and exact `str(exception)`.

An exception message is evidence, not a control signal. No downstream behaviour should parse it.

An attempt starts when the runner dispatches a validated scheduled request to the engine. Exact message construction cannot fail after validation and is always present. Rendering, tokenization, context checking, device transfer, RNG setup, synchronization, generation, output-shape/prefix validation, slicing, and decoding are all within the attempt boundary.

- Context overflow alone produces `input_context_exceeded` and the runner continues.
- Rendering, tokenization, output-invariant, slicing, or decoding exceptions produce `generation_error`, are fsynced, and then abort the run because they indicate a harness/data-path invariant failure.
- Device-transfer, RNG, synchronization, and any `RuntimeError` from generation are fatal after recording where possible.
- Only a non-`RuntimeError` raised inside `model.generate()` may continue, and only after the explicit CUDA health probe succeeds.

All failed attempts use `generation_duration_ns=null`; partial elapsed time is never mixed with the latency metric.

The attempt-record keys shown above are exact; unexpected or missing keys make the evidence invalid. Runner-owned keys are `schema_version`, `run_id`, `attempt_index`, `prompt_id`, `system_id`, `repeat_index`, `generation_seed`, `adapter_enabled`, `prompt_asset_id`, and `prompt_asset_sha256`. All remaining keys are copied without reinterpretation from `GenerationResult`.

## Offline evaluation runner

### CLI

Required options:

```text
--prompts PATH
--system-set PATH
--run-seed INTEGER
--device cuda:N
```

Optional options:

```text
--adapter-path PATH     required exactly when C or D is selected
--run-id ID             otherwise generated as UTC basic timestamp plus 8 hex characters
--runs-root PATH        defaults to experiments/runs
```

The primary runner accepts only an explicit logical CUDA index such as `cuda:0`; bare `cuda`, CPU, and invalid/unavailable indices are rejected. The seeded `torch.Generator`, model placement, memory/device metadata, health probes, and synchronization all use that same resolved device. `--run-seed` must be explicit; there is no random default. A run ID matches `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`. The runner never overwrites or resumes an existing run directory.

The read-only inspector command is:

```bash
uv run --frozen python -m chatgnt.harness inspect --run-dir PATH
```

It prints one canonical completeness-report JSON object to stdout, writes nothing, and exits `0` only when `complete=true`; an incomplete but readable run exits `1`, while invalid arguments or an unreadable run exit `2`.

Exit status is `0` only for a complete run. Preflight/configuration failure returns `2` without creating a final run directory. A runtime abort after the run begins returns `3` and preserves the partial directory. `KeyboardInterrupt` follows conventional exit status `130` after closing the response file.

### Run creation and writes

The formal runner is single-writer per runs root. Before scanning asset history or checking a run ID, it creates/opens `<runs-root>/.chatgnt-harness.lock` and holds an exclusive nonblocking `fcntl.flock` through preflight, publication, generation, and final inspection. Failure to obtain the lock is a configuration error. The lock file is runs-root coordination metadata, not a primary run artefact. Cross-platform concurrent execution is outside scope; the formal environment is Linux.

After locked preflight and warm-up:

1. reserve the final path with `mkdir(exist_ok=false)`; this is the atomic no-replace operation;
2. create each of `manifest.json`, `prompts.jsonl`, and `responses.jsonl` with exclusive file creation;
3. write and fsync the canonical manifest and prompts and fsync the empty response file;
4. fsync the run directory so the three directory entries are published; and
5. begin scheduled generation.

Initialization failure before step 4 removes only the directory and files exclusively created by this invocation; it must never remove a pre-existing path. If cleanup itself fails, preserve the invalid partial directory, report it, and exit nonzero. The run begins after step 4. This protocol favors portable no-overwrite behavior over a check-then-rename race.

The manifest and frozen prompt file are never opened for writing again. Each response is one canonical JSON line appended only after the attempt result is complete, followed by `flush()` and `os.fsync()` before the next attempt begins. A partial final line caused by operating-system or hardware failure is invalid evidence and must be reported by the completeness inspector rather than repaired in place.

### Run artefacts

Exactly three primary files are created:

```text
experiments/runs/<run-id>/
├── manifest.json
├── prompts.jsonl
└── responses.jsonl
```

The frozen prompt file contains the validated prompt objects in source order, using canonical JSONL. Its exact bytes may differ from the source due to canonical serialization; both source-file and frozen-file SHA-256 digests are recorded.

The immutable manifest contains exactly the top-level keys in this shape:

```json
{
  "schema_version": 1,
  "specification_version": "1.2",
  "run_id": "20260714T140000Z-example",
  "created_at_utc": "2026-07-14T14:00:00.000000+00:00",
  "diagnostic": null,
  "implementation": {},
  "prompt_set": {},
  "system_set": {},
  "schedule": {},
  "model": {},
  "tokenizer": {},
  "adapter": null,
  "configuration": {},
  "environment": {},
  "timing": {},
  "warmup": {}
}
```

Nested objects have these exact keys:

- `diagnostic`: null for formal runs; for CUDA smoke, an object with exactly `kind="cuda-smoke"`, `experimental_result=false`, `adapter_provenance_bypass=true`, and `adapter_provenance_bypass_reason="lifecycle adapter predates formal provenance"`.
- `implementation`: `package_version`, `behaviour_files`, `behaviour_digest`, `pyproject_sha256`, `uv_lock_sha256`, `git_commit`, `git_dirty`; behaviour files contain exactly `path`, `size_bytes`, `sha256`. Git fields are respectively a 40-character commit string or null and a boolean or null when Git metadata is unavailable.
- `prompt_set`: `source_path`, `source_sha256`, `frozen_sha256`, `prompt_count`, `prompt_ids`.
- `system_set`: `source_path`, `source_sha256`, `systems`; each system has `system_id`, `adapter_enabled`, `prompt_asset`, and the asset has `source_path`, `source_sha256`, `schema_version`, `prompt_asset_id`, `version`, `worked_example_count`, `content`.
- `schedule`: `run_seed`, `order_seed`, `seed_algorithm`, `order_algorithm`, `primary_samples_per_system_prompt`, `scheduled_attempt_count`, `attempts`; each attempt has exactly `attempt_index`, `prompt_id`, `system_id`, `repeat_index`, `generation_seed`.
- `model`: `model_id`, `revision`, `snapshot_path`, `architecture`, `model_type`, `parameter_count`, `dtype`, `max_context_tokens`, `weights_sha256`, `behaviour_files`, `effective_generation_config`; each file has `path`, `size_bytes`, `sha256`, and the effective configuration is a JSON object captured after model load and controlled-profile validation.
- `tokenizer`: `class`, `length`, `chat_template_sha256`, `eos_token_id`, `generation_eos_token_ids`, `pad_token_id`, `all_special_ids`.
- `adapter`: null when no adapted system is selected; otherwise `path`, `adapter_id`, `adapter_version`, `adapter_digest`, `behaviour_files`, `provenance`, `provenance_sha256`, `peft_config`, `active_adapters`, `trainable_parameter_count`, `parameter_dtypes`, and `merged`. `path` contains exactly `kind` (`project-relative` or `host-absolute`) and `value` (string). `peft_config` is the strict parsed JSON content of exact `adapter_config.json`, not `PeftConfig.to_dict()`; runtime values are verified against it without persisting sets or enums. `active_adapters` is a sorted string list, `trainable_parameter_count` a non-negative integer, `parameter_dtypes` a sorted string list, and `merged` a boolean.
- `configuration`: `model`, `generation`, and `inference`; each contains `source_path`, `source_sha256`, and `values`.
- `environment`: `python`, `platform`, `torch`, `transformers`, `peft`, `tokenizers`, `safetensors`, `accelerate`, `torch_cuda_build`, `cuda_driver`, `cudnn`, `device`, `device_name`, `device_total_memory_bytes`, `bf16_supported`, `attention_implementation`, `collection_errors`. `cuda_driver` may be null if the pinned public APIs cannot obtain it; the failed collection method is recorded in `collection_errors`. `collection_errors` is a list of objects with exactly string fields `field`, `type`, and `message`, sorted by that tuple, and is empty when collection succeeds. All other formal CUDA-run values are required.
- `timing`: `metric`, `clock`, `cuda_synchronize`, `include_prompt_prefill`, `include_output_generation`, `include_tokenization`, `include_model_loading`, `batch_size`, `reusable_conversation_cache`.
- `warmup`: `per_loaded_runtime`, `profile`, `timed`, `base_runtime_performed`, `adapted_runtime_performed`.

Every digest is 64 lowercase hexadecimal, counts are non-negative JSON integers, timestamp is UTC ISO-8601, `systems` and `attempts` are lists, and `values`, `provenance`, `peft_config`, and `profile` are JSON objects. Unknown or missing nested keys are invalid. The exact parsed configuration values remain nested under `values`; they are not flattened.

For formal runs, adapter `provenance` is the exact strict parsed sidecar object and `provenance_sha256` is its file digest. They may be null only when the exact non-null CUDA-smoke diagnostic object declares the lifecycle-adapter bypass. The inspector rejects a diagnostic object or null provenance for any run located beneath `experiments/runs`.

Under that single CUDA-smoke bypass, `adapter_id` and `adapter_version` are the fixed diagnostic strings `lora-lifecycle-diagnostic` and `unversioned-diagnostic`; they are labels rather than fabricated training provenance.

Implementation identity covers every regular `chatgnt/*.py` file in relative POSIX order. `behaviour_digest` is computed from their canonical file-identity list using the same tree-digest method as adapter identity. Git metadata is supplemental: a dirty or absent repository is allowed because content digests remain authoritative.

These fields collectively capture:

- schema version, specification version, run ID, and UTC creation timestamp;
- source and frozen prompt digests, prompt count, and prompt IDs;
- source system-set digest and parsed system definitions in canonical A–D order;
- complete parsed prompt assets, source paths as project-relative paths where possible, and exact byte digests;
- complete ordered attempt schedule, count, run seed, order seed, seed algorithm, and order algorithm;
- exact model and tokenizer identities, snapshot-relative path, configured revision, weight digest, chat-template digest, classes, architecture, dtype, and context limit;
- adapter identity or null, including behaviour-bearing file list and tree digest;
- complete parsed model and generation configurations plus exact source-file digests;
- Python, platform, Torch, Transformers, PEFT, CUDA build, CUDA runtime/driver, device name, total VRAM, and BF16-support identities; and
- canonical timing boundary and warm-up policy.

Absolute workspace paths must not be the only component identity. Prefer project-relative paths in evidence; when an external adapter path cannot be represented relatively, capture it with `kind="host-absolute"` alongside its content digest.

The manifest has no mutable completion field. Completeness is derived from its schedule and the response records.

### Completeness inspector

The harness exposes a read-only function and CLI-compatible operation that compares a run's manifest schedule with its response JSONL. It reports:

- scheduled count;
- valid response-line count;
- unique recorded attempt count;
- missing attempt indices;
- duplicate attempt indices;
- unexpected attempt identities;
- malformed or partial line numbers; and
- `complete`, true only when every scheduled attempt has exactly one valid matching record and no extra or malformed records exist.

The inspector never modifies evidence. Its output contains exactly:

```json
{
  "schema_version": 1,
  "run_id": null,
  "scheduled_count": 0,
  "response_line_count": 0,
  "valid_response_count": 0,
  "unique_recorded_attempt_count": 0,
  "missing_attempt_indices": [],
  "duplicate_attempt_indices": [],
  "unexpected_attempt_indices": [],
  "malformed_line_numbers": [],
  "integrity_errors": [],
  "complete": false
}
```

Index and line-number lists contain integers. `integrity_errors` contains objects with exactly `location`, `code`, and `message`, all strings. Lists are sorted deterministically.

`run_id` is a string when a valid manifest supplies it and null otherwise. JSONL line numbers are one-based. Index lists sort numerically; integrity errors sort lexicographically by `(location, code, message)`. A missing or malformed manifest produces the same exact report schema with zero scheduled counts, null run ID, and manifest integrity errors; a readable directory with invalid evidence exits `1`. A missing or unreadable run directory still prints the exact null-ID report where stdout is available and exits `2`.

Completeness requires both coverage and integrity. The inspector must:

- parse all JSON with duplicate-key and non-finite rejection and require canonical on-disk serialization;
- validate the exact manifest, prompt, attempt-record, error, and report schemas and all status-dependent nullability rules;
- validate implementation file-list/tree-digest consistency plus the recorded `pyproject.toml` and `uv.lock` digest formats;
- recompute and compare the frozen `prompts.jsonl` digest;
- validate prompt IDs/counts and prompt contents against the manifest;
- verify each response's run/schedule identity and generation seed;
- verify its system adapter flag, prompt-asset ID/digest, and exact two messages against the manifest and frozen prompt;
- require input/generated list lengths to equal their counts;
- recompute `raw_output_sha256` for success records;
- recompute visible token count from `generated_token_ids` and the manifest's `all_special_ids`;
- validate termination, terminal-token, and maximum-length invariants against the snapshotted configuration; and
- reject duplicate, extra, malformed, noncanonical, or partial records.

The inspector performs an internal evidence-integrity check; it does not claim to reproduce tokenization or model generation. Re-rendering prompts and re-decoding token IDs against the pinned tokenizer belongs to a deeper optional audit, not run completeness.

## Failure semantics

### Pre-run failures

Parsing, identity, component loading, device verification, adapter verification, and warm-up failures abort before the final run directory exists. There is no fallback model, tokenizer, template, prompt, adapter, device, dtype, or generation setting.

### Attempt failures

The only statuses are:

- `success`;
- `input_context_exceeded`; and
- `generation_error`.

There is exactly one attempt and at most one response record for each scheduled identity. No automatic retry occurs.

An isolated non-`RuntimeError` raised inside `model.generate()` is recorded with `generation_duration_ns=null`, fsynced, and the runner may continue only after a CUDA health probe succeeds. Every `RuntimeError` during device transfer, RNG installation, generation, or synchronization is fatal, including `torch.OutOfMemoryError`, `torch.AcceleratorError`, `torch.cuda.CudaError`, and `torch.cuda.DeferredCudaCallError` where present in the pinned runtime. Any synchronizer exception or failed health probe is also fatal. The health probe allocates two one-element tensors on the run's exact device, adds them, verifies the scalar result, and synchronizes that device. Exception messages are never parsed for classification. A fatal attempt is recorded and fsynced where Python execution remains possible, then the run aborts.

### Interruption

On interruption, close the response file and leave already fsynced records untouched. Unattempted schedule entries remain missing. Restarting work creates a new run ID; Step 7 does not resume or append to a prior run.

## Verification specification

### Unit and component tests

The standard command is:

```bash
uv run --frozen python -m unittest discover -s tests -v
```

Tests must use fakes or small tensors and cover at least:

1. duplicate-key and non-finite JSON rejection;
2. prompt, prompt-asset, and system-set validation, including every A–D invariant;
3. exact stable seed vectors, including proof that system ID does not affect generation seed;
4. deterministic `sha256-sort-v1` order, full coverage, and unique attempt indices;
5. exact two-message construction and official-template arguments;
6. no-truncation context rejection at both sides of the boundary;
7. dedicated state creation, fork/install/restore behavior, invariance to prior RNG state and execution order, restoration after success and exceptions, absence of a `generator` kwarg, and explicit generation keyword arguments;
8. timing event order: synchronize, start, generate, synchronize, stop;
9. terminal-token accounting, visible-token accounting, exact decode arguments, and preservation of whitespace;
10. `max_new_tokens` termination and unexpected-termination failure;
11. preprocessing, generation, postprocessing, output-shape/prefix, generic `RuntimeError`, deferred-CUDA, synchronizer, health-probe, and safely continuable exception behavior;
12. adapter-required and adapter-forbidden preflight behaviour;
13. exclusive run creation, canonical artefacts, append-only response writes, and refusal to overwrite;
14. completeness for complete, partial, duplicate, unexpected, and malformed response files; and
15. proof that manifest and frozen prompts are not rewritten during a run;
16. formal base/adapter loading keyword arguments, exact parameter/buffer placement, base-only parameter counts, optional `hf_device_map`, effective attention implementation, actual dtypes, active adapter, and unmerged state; and
17. implementation file/tree, `pyproject.toml`, and `uv.lock` identity plus inspector corruption detection.

Tests must assert fixed expected seed and order values rather than only comparing a function with itself.

### Local model and adapter smoke check

A required separate diagnostic command exercises the shared engine against the locally pinned model on CPU using the explicit `cpu-smoke-sampled-v1` profile and disabled timing:

```bash
uv run --frozen python -m chatgnt.smoke --device cpu
```

It prints one canonical JSON report to stdout and does not write under `experiments/runs`.

The smoke report must prove:

- local-only loading of the pinned snapshot;
- exact two-message rendering;
- a generated token sequence and untouched decoded output; and
- clear labelling that its CPU timing and diagnostic generation profile are not experimental measurements.

When `artifacts/diagnostics/lora-lifecycle-adapter` is present, the same diagnostic module must also load it through the new adapted-engine factory and run one adapter-disabled base diagnostic on the untouched runtime and one adapter-enabled diagnostic on the adapted runtime. It verifies that the adapted runtime is unmerged, has zero trainable parameters, and that both calls traverse their intended stable runtime mode. The lifecycle adapter predates formal adapter provenance, so this diagnostic alone may use an explicit `allow_unprovenanced_diagnostic_adapter=true` factory flag; that flag is absent from and cannot be enabled by the formal runner. Diagnostic output is stdout only.

If the pinned snapshot or lifecycle adapter is unavailable in a clean checkout, unit tests still run; the corresponding smoke check fails clearly rather than downloading it. Acceptance criterion 8 applies in the audited development workspace where both are present.

### Real-CUDA end-to-end diagnostic

The implementation must provide:

```bash
uv run --frozen python -m chatgnt.harness cuda-smoke \
  --device cuda:0 \
  --adapter-path artifacts/diagnostics/lora-lifecycle-adapter
```

This subcommand creates its own disposable prompt and prompt-asset inputs, selects diagnostic Systems A and C, and writes only beneath `artifacts/diagnostics/inference-harness-cuda/<diagnostic-run-id>/`. It uses the formal runtime loading, sampled generation controls, forked RNG policy, synchronization/timing boundary, two-runtime routing, append/fsync writer, and completeness inspector. It may bypass formal adapter provenance only for the named lifecycle adapter, records that bypass prominently, and cannot target `experiments/runs`.

The diagnostic must complete at least one A and one C attempt, report a complete three-file evidence set, and record actual CUDA, runtime, dtype, adapter, and latency identities. These are diagnostic engineering results, not experimental ChatG&T results.

If a compatible CUDA device is unavailable during implementation, the command and non-GPU tests must still be built, but `VER-002` and Step 7 acceptance remain explicitly pending. Step 7 must not be marked completed until this exact path passes on the pinned GPU environment.

### Static verification

All implementation modules and tests must compile with:

```bash
uv run --frozen python -m compileall -q chatgnt tests
```

## Acceptance criteria

Step 7 is complete only when all of the following are true:

1. The shared engine can run base and optional unmerged LoRA inference through one tested boundary.
2. Exact messages, rendered prompt, input IDs, generated IDs, untouched output, counts, termination, seed, and synchronized generation duration are returned as specified.
3. The runner produces only the three defined immutable/append-only primary artefacts.
4. A fixed seed and input set reproduce the same schedule and per-prompt generation seeds.
5. Missing or mismatched components fail explicitly and cannot cause system substitution.
6. A complete run and a deliberately interrupted partial run are both classified correctly without evidence mutation.
7. The full unit suite and compilation check pass under the frozen environment.
8. The local model and lifecycle-adapter CPU smoke checks pass in the audited development workspace.
9. No output validation, retry, repair, training, or web concerns leak into Step 7.
10. The implementation is reviewed against every normative requirement in this document, and any deliberate deviation is documented and approved before Step 7 is marked complete.
11. The real-CUDA end-to-end diagnostic passes; without compatible GPU access this criterion remains pending rather than waived.

## Requirements traceability

The following stable requirement groups are the review checklist. The build may split them into finer tests, but it must not silently omit a group.

| Requirement | Source | Implementation boundary | Required evidence |
| --- | --- | --- | --- |
| `CFG-001` | D-018–D-022 | `configuration.py` | Closed-schema and cross-field tests |
| `ID-001` | D-018 | `identity.py`, preflight | Snapshot, prompt, adapter, and config digest tests |
| `ID-002` | D-019 | `identity.py` | Fixed seed/order conformance vectors |
| `INF-001` | Experiment plan, D-018 | `inference.py` | Exact two-message/template test |
| `INF-002` | D-019 | `inference.py` | Explicit profile and forked-device-state tests |
| `INF-003` | D-020 | `inference.py` | Token slicing, decoding, digest, and termination tests |
| `INF-004` | D-021 | `inference.py` | Synchronization/timing event-order test |
| `INF-005` | D-022 | `inference.py` | Exact engine-result/failure tests |
| `RUN-001` | D-018 | `harness.py` | A–D invariant and stable-runtime routing tests |
| `RUN-002` | D-018, D-019 | `harness.py` | Frozen schedule and full-coverage tests |
| `RUN-003` | D-018, D-022 | `harness.py` | Exclusive publication, append/fsync, partial-run tests |
| `REC-001` | D-018, D-020 | `records.py` | Exact schema and canonical JSON tests |
| `REC-002` | D-022 | completeness inspector | Coverage plus integrity corruption tests |
| `REC-003` | D-018 | manifest preflight | Harness/config/lockfile source identity tests |
| `VER-001` | Acceptance 1–8 | tests and diagnostic module | Unit, compile, base smoke, and adapter smoke results |
| `VER-002` | Acceptance 11 | CUDA diagnostic subcommand | Real-CUDA two-runtime complete diagnostic run |
| `WEB-001` | D-010, D-022 | shared engine boundary | Device-agnostic engine test; CUDA-only runner test |

Acceptance review must record pass/fail and a test or inspection reference for every row.

## Implementation hand-off checklist

The build agent must return:

- a concise file-by-file summary;
- all commands run and their outcomes;
- any acceptance criterion not demonstrated;
- any specification ambiguity or deviation encountered; and
- confirmation that no formal experimental result was created from fixtures or diagnostic settings.
