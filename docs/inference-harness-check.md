# Inference Harness Implementation Check

## Outcome

Step 7 specification version 1.2 has been implemented and passes every locally executable acceptance check. The real-CUDA end-to-end diagnostic remains pending because the local machine has no CUDA device. Step 7 is therefore not yet marked complete.

No formal experimental run, fixture result presented as evidence, or fabricated CUDA result was created.

## Specification review

The implementation specification received four independent adversarial reviews:

1. Review one returned `BLOCK` and exposed API-boundary, provenance, schema, completeness, publication, runtime-fairness, and verification gaps.
2. Review two returned `BLOCK` and identified the pinned Transformers RNG incompatibility plus loading, source-identity, CUDA, warm-up, and failure-boundary gaps.
3. Review three returned `BLOCK` and corrected single-device placement verification and exact diagnostic/PEFT evidence schemas.
4. Review four returned `PASS` with no remaining material implementation decision.

The accepted contract is [Step 7 inference and capture harness specification](inference-harness-specification.md).

## Implemented boundaries

- `chatgnt.inference`: device-agnostic shared base/adapted inference engine.
- `chatgnt.harness`: CUDA-only formal runner, immutable evidence capture, completeness inspector, and CUDA diagnostic.
- `chatgnt.records`: strict JSON and immutable request/result/attempt records.
- `chatgnt.configuration`: closed-schema project, prompt, system, model-file, and adapter-provenance checks.
- `chatgnt.identity`: component digests, seed derivation, and deterministic execution order.
- `chatgnt.smoke`: non-experimental CPU base/adapter diagnostic.
- `config/model-files.json`: pinned identities for all behaviour-bearing model and tokenizer files.

## Independent local verification

Compilation:

```bash
.venv/bin/python -m compileall -q chatgnt tests
```

Result: pass.

Unit and component tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Result: 40 of 40 tests passed.

The tests cover strict parsing, A–D system invariants, fixed seed/order vectors, forked RNG restoration, exact generation arguments, message rendering, context limits, timing order, token and termination accounting, runtime loading, adapter state, failure handling, exclusive publication, partial runs, pinned identities, and inspector corruption detection.

Real local model and adapter diagnostic:

```bash
.venv/bin/python -m chatgnt.smoke --device cpu
```

Result: pass.

- The untouched base runtime returned `READY`.
- The separately loaded adapted runtime returned `READY`.
- The adapted runtime reported active adapter `chatgnt`, zero trainable parameters, and unmerged state.
- Both used the exact empty-system-plus-user message construction.
- The report labelled itself diagnostic and non-experimental.

## Pending real-CUDA acceptance

The local environment reports `torch.cuda.is_available() == false`, so specification requirement `VER-002` could not be executed honestly.

On the compatible Runpod environment, run from the repository root:

```bash
uv run --frozen python -m chatgnt.harness cuda-smoke \
  --device cuda:0 \
  --adapter-path artifacts/diagnostics/lora-lifecycle-adapter
```

This diagnostic must exercise the actual two-runtime CUDA path, paired sampling, synchronization and timing, append-only evidence writer, and completeness inspector. It writes only under `artifacts/diagnostics/inference-harness-cuda/`; it cannot create a formal result under `experiments/runs`.

After copying the diagnostic directory back locally, run:

```bash
uv run --frozen python -m chatgnt.harness inspect \
  --run-dir artifacts/diagnostics/inference-harness-cuda/<diagnostic-run-id>
```

Step 7 can be marked complete only when the command exits successfully and the inspector reports `"complete": true` with no integrity errors.
