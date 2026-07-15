# Stage 2 Readiness Review

- **Review date:** 2026-07-15
- **Decision:** Pass
- **Stage 2 status:** Complete
- **Next stage:** Stage 3 — Design and freeze the evaluation

## Review question

Has ChatG&T established a reproducible technical baseline, trustworthy measurement tooling, and a credible prompt-engineered baseline without using held-out evaluation data?

Yes. Every Stage 2 exit criterion has recorded evidence. No unresolved issue prevents evaluation design from beginning.

## Exit-criterion assessment

| Criterion | Result | Evidence |
| --- | --- | --- |
| Selected model runs reproducibly | Pass | Qwen2.5-1.5B-Instruct is pinned by model revision, individual file identities, tokenizer identity, weight digest, Python lock, and executable verification |
| Available compute is sufficient | Pass | BF16 LoRA feasibility peaked at 7.9336 GiB reserved on a 24 GB RTX 3090, leaving substantial headroom |
| LoRA lifecycle works | Pass | Attach, neutral initialisation, update, save, clean reload, and exact reproduction were exercised end to end |
| Inference evidence is trustworthy | Pass | The frozen harness records messages, rendered prompts, tokens, seeds, timing, model and adapter identity, environment, errors, and immutable responses |
| CUDA execution is real | Pass | BF16 tensor execution and base/adapted end-to-end CUDA inference completed on rented NVIDIA hardware |
| Structural measurement works | Pass | The exact JSON Schema, strict parser, stable failure labels, evidence serializer, and adversarial tests pass |
| Development population is separated | Pass | Twenty frozen development prompts and the five worked examples are versioned and excluded from training, validation, and later held-out use |
| Prompt baseline is credible | Pass | Four prompt versions were developed under a predeclared revision budget and selection rule; v3 remains frozen after mixed pinned transfer |
| Systems A and B have development baselines | Pass | System A, pinned B/v1, local B/v1–v4, and pinned B/v3 retain raw outputs and structural and qualitative evaluations |
| Operational cost is bounded | Pass | Four short Runpod sessions total `$0.53`, well inside the `$20` one-off training budget |
| Held-out boundary is intact | Pass | No final held-out prompt set has been generated or inspected, and no development output is presented as final generalisation evidence |

## Baseline established

The pinned development results are:

| Condition | JSON valid | Schema valid | Full response passes |
| --- | ---: | ---: | ---: |
| System A — empty system message | 1 / 20 | 0 / 20 | 0 / 20 by structural gate |
| System B — five-shot v1 | 14 / 20 | 9 / 20 | 6 / 20 |
| System B — selected five-shot v3 | 16 / 20 | 12 / 20 | 5 / 20 |

Version 3 is a credible but imperfect prompt baseline. It improved schema adherence without improving the end-to-end full-pass count. That mixed result strengthens the experiment: fine-tuning will be compared against a prompt that received genuine development effort, while the remaining failures provide concrete behaviours for training data to address.

These are development diagnostics, not final performance estimates.

## Evidence and tooling ready for Stage 3

Stage 3 can rely on:

- the defined research question and two-by-two system design;
- the normal-response contract and exact schema;
- the target evaluation population and exclusions;
- the layered execution, structure, quality, comparison, and efficiency framework;
- a frozen base model, tokenizer, chat-template policy, generation profile, and seed derivation;
- the immutable inference harness and inspector;
- the strict structural evaluator;
- identity-blinded qualitative packet preparation and score aggregation; and
- a frozen five-shot prompt for Systems B and D.

Stage 3 still has substantive work to do. The development rubric and blind-scoring mechanism are evidence that the approach is executable; they do not silently freeze the final judge calibration, held-out sample, pairwise protocol, or uncertainty analysis.

## Carry-forward work

### Hard gate before the next formal model run

The adapter-loading unit test must create its own disposable adapter fixture. Its current dependency on a Git-ignored local diagnostic artefact caused one error in a fresh Runpod checkout. This did not affect the base-only v3 run, but another formal run cannot pass preflight until the test is self-contained and passes from a clean clone.

### Required during Stage 3

- define held-out sample size, quotas, and reporting slices;
- define how held-out prompts will later be written, reviewed, de-duplicated, and frozen after supervised data freeze;
- finalise anchored human and LLM-judge calibration;
- define blind pairwise eligibility, order randomisation, and tie handling;
- finalise memorisation and semantic-overlap checks;
- specify uncertainty reporting; and
- freeze the final efficiency measurement and interpretation procedure.

### Deferred to the pilot fine-tune

Exact LoRA training hyperparameters and checkpoint-selection rules belong to Stage 6's pilot design. The dependency environment and feasible training mechanism are already established; pretending to know the final training configuration before seeing pilot behaviour would not improve Stage 2 readiness.

## Limitations carried forward

- Prompt development used 20 deliberately diagnostic prompts rather than a representative final sample.
- Local prompt selection used quantised Ollama inference; pinned transfer was mixed.
- Pinned v1 and v3 ran in different GPU sessions, so their latency is not a matched comparison.
- Development qualitative scores came from one LLM-judge session whose exact backend snapshot was unavailable.
- Human calibration and inter-rater agreement remain Stage 3 requirements.
- Testing one small base model does not support claims about fine-tuning or prompting generally.

None of these limitations is hidden by the pass decision. They constrain later claims and shape Stage 3's design.

## Decision

Stage 2 is complete. ChatG&T may proceed to Stage 3 without creating more prompt versions or generating held-out outputs.

The immediate next task is to define the final held-out evaluation sample and judging procedure before authoring or inspecting that sample. The adapter-test fixture is recorded as mandatory maintenance before the next formal model execution.
