# Inference Harness Implementation Check

## Outcome

Step 7 specification version 1.2 has been implemented and passes its compilation, unit, CPU model/adapter, and real-CUDA end-to-end acceptance checks. Step 7 is complete.

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

## Real-CUDA acceptance

The local environment reports `torch.cuda.is_available() == false`, so specification requirement `VER-002` was executed on a compatible Runpod L4 rather than simulated locally.

Command:

```bash
uv run --frozen python -m chatgnt.harness cuda-smoke \
  --device cuda:0 \
  --adapter-path artifacts/diagnostics/lora-lifecycle-adapter
```

The run used the frozen dependency environment and pinned Qwen model revision. It exercised the actual two-runtime CUDA path, paired sampling, synchronization and timing, append-only evidence writer, and completeness inspector.

Result:

- Date: 2026-07-14
- Run ID: `20260714T151316Z-0879c92d`
- Device: NVIDIA L4 with 23,034 MiB reported by `nvidia-smi`
- Observed host driver: 580.126.20
- Locked PyTorch: 2.12.1+cu130
- PyTorch CUDA build: 13.0
- BF16 support: confirmed by a real CUDA tensor calculation before the harness run
- Scheduled attempts: 2
- Successful response records: 2
- Missing, duplicate, unexpected, or malformed records: 0
- Integrity errors: 0
- Inspector result: `complete: true`
- Process exit status: 0
- Runpod session charge: $0.10

The base runtime generated in 237,515,608 ns and the unmerged adapter-backed runtime generated in 328,834,723 ns. These two timings are acceptance observations from one trivial prompt, not comparative performance estimates.

The lifecycle adapter is a disposable technical fixture. Identical base and adapted text in this run is expected and does not test whether fine-tuning produces ChatG&T behaviour. The diagnostic establishes that the adapter-backed execution path works; quality claims remain reserved for later development and held-out evaluation.

The immutable evidence bundle is preserved in:

- [manifest.json](../artifacts/diagnostics/inference-harness-cuda/20260714T151316Z-0879c92d/manifest.json)
- [prompts.jsonl](../artifacts/diagnostics/inference-harness-cuda/20260714T151316Z-0879c92d/prompts.jsonl)
- [responses.jsonl](../artifacts/diagnostics/inference-harness-cuda/20260714T151316Z-0879c92d/responses.jsonl)

The diagnostic manifest transparently records one non-blocking metadata collection error: PyTorch 2.12.1 does not expose the attempted `torch.cuda.driver_version` attribute. The driver version was observed independently through `nvidia-smi`. This did not affect CUDA execution, response capture, or evidence integrity, but the collector should use a supported source before a formal experimental run.

Across the earlier $0.14 feasibility session and this $0.10 acceptance session, recorded Runpod expenditure is $0.24 against the $20 training budget.
