# Decision Log

This log records consequential project decisions, their rationale, and any unresolved implications.

## D-001 — Adopt the primary research question

- **Date:** 2026-07-13
- **Status:** Superseded by D-006

### Decision

The primary research question is:

> To what extent does LoRA-based supervised fine-tuning improve a small instruction-tuned language model’s ability, relative to prompt engineering alone, to generate schema-valid JSON responses that are simultaneously useful, metaphorically coherent, and stylistically consistent on unseen prompts?

ChatG&T responses will be generated as JSON conforming to a defined schema. Structural validity will be evaluated separately from the softer qualities of the response.

### Rationale

The question makes prompt engineering an explicit baseline and tests fine-tuning on unseen prompts. JSON provides an objective structural requirement, while usefulness, metaphorical coherence, and stylistic consistency capture whether a technically valid response is also a good ChatG&T response.

### Implications

- A response can pass structural validation while failing the qualitative evaluation.
- Raw model output must be evaluated separately from any application-level repair or retry mechanism.
- The JSON schema and qualitative terms must be defined before building the evaluation.

## D-002 — Use a two-by-two system comparison

- **Date:** 2026-07-13
- **Status:** Adopted; amended by D-007

### Decision

The offline experiment will compare four systems:

| System | Model | ChatG&T prompt |
| --- | --- | --- |
| A | Base model | None |
| B | Base model | Detailed |
| C | Fine-tuned model | None |
| D | Fine-tuned model | Detailed |

The public Tasting Room will primarily compare System B with System C. All references to input from a visitor or evaluator will use the term **user prompt**, because inputs may be questions, requests, commands, statements, fragments, or adversarial instructions.

### Rationale

Comparing only System B with System C changes both the model and the prompt, so it cannot isolate which intervention caused an observed difference. The two-by-two design measures the effects of prompting and fine-tuning separately, as well as whether they interact.

### Implications

- All four systems must use the same base model, user prompts, chat template, and matched inference settings wherever applicable.
- Systems A and C will receive no ChatG&T instruction.
- The detailed prompt must be developed fairly and frozen before held-out evaluation.
- Raw experimental evaluation will not use JSON repair, automatic retries, or constrained generation.
- The eventual Spirit Guide system will be selected using evidence rather than assumed in advance.

## D-003 — Adopt the normal-response contract

- **Date:** 2026-07-13
- **Status:** Adopted

### Decision

A normal ChatG&T response will be a JSON object containing exactly four top-level fields: `title`, `ingredients`, `method`, and `garnish`.

- Ingredients are metaphorical rather than literal.
- `ingredients` contains three to eight objects.
- Each ingredient contains exactly a positive numeric `amount`, a non-empty `unit`, and a non-empty `name`.
- Measurement units use an open vocabulary.
- `method` contains two to five ordered, non-empty strings.
- Unexpected fields cause a schema failure.

Method steps must collectively answer the prompt while behaving as an actual preparation method. When a user requests a concrete artefact, the final method step supplies the result.

### Rationale

The four-field shape is small enough for a small model to learn while retaining the essential parts of the ChatG&T concept. Representing the method as an array encourages ordered, concise preparation steps and prevents an ordinary essay from being placed inside a recipe-shaped field.

### Implications

- Method quality has both a structural component and a qualitative component.
- Valid JSON and schema conformance remain separate from usefulness and metaphorical coherence.
- Exact field-length constraints remain deferred until more ideal examples have been examined.
- Safety-sensitive exceptions were subsequently resolved by D-004.

## D-004 — Use proportionate safety boundaries

- **Date:** 2026-07-13
- **Status:** Adopted

### Decision

ChatG&T will be treated as a novelty fine-tuning experiment rather than a general-purpose or professional advice service.

- The project will not add a separate safety-response schema or application-level safety-routing system.
- The dataset will not specifically train the model for professional, emergency, or crisis advice.
- Fine-tuning will not deliberately remove or override inherited base-model safety behaviour.
- The Lab page will state that the model is experimental and unsuitable for high-stakes reliance.
- Concerning behaviour found during testing will be documented as a limitation.

### Rationale

The project should acknowledge foreseeable limitations without expanding a portfolio experiment into a production-grade advice or safety system. Preserving inherited safeguards and communicating scope is proportionate to the project’s purpose.

### Implications

- The project will not claim comprehensive safety coverage.
- Professional and crisis use remains outside the target evaluation population.
- Safety-related failures encountered incidentally remain relevant evidence and must not be hidden.

## D-005 — Define the target evaluation population

- **Date:** 2026-07-14
- **Status:** Adopted

### Decision

The target evaluation population consists of English-language, single-turn, low-stakes prompts that can be answered concisely using stable general knowledge. It covers five intent families:

1. advice and decision support;
2. explanation and technical understanding;
3. low-stakes emotional support;
4. creative generation; and
5. short-form transformation.

Evaluation results will be reported separately for target-use, cross-domain, and robustness prompts.

The population excludes professional, emergency, and crisis guidance; live-information and tool-dependent requests; long-context and long-form tasks; obscure factual recall; multi-turn conversations; and non-English prompts.

### Rationale

The population reflects the project’s intended playful, low-stakes use while remaining broad enough to test whether ChatG&T generalises across topics, user intents, and input forms. Explicit exclusions prevent the final results from implying coverage that the experiment has not established.

### Implications

- Conclusions must be limited to the defined population.
- Public Tasting Room submissions will provide supplementary evidence rather than replace the curated evaluation.
- Test-set size, quotas, withheld topics, and the operational definition of “unseen” remain undecided.

## D-006 — Revise the research question around quality and efficiency

- **Date:** 2026-07-14
- **Status:** Adopted

### Decision

The primary research question is revised to:

> How does LoRA-based supervised fine-tuning compare with a strong five-shot prompt in producing schema-valid, useful, metaphorically coherent, and stylistically consistent ChatG&T responses on unseen prompts, and what trade-offs does it introduce in prompt-token usage and latency?

This decision supersedes D-001 while preserving the original question as part of the project history.

### Rationale

A realistic prompt-engineered baseline may match the fine-tuned model’s response quality. Fine-tuning could still produce a meaningful engineering result by retaining similar quality with lower recurring prompt-token or latency overhead. The revised question permits both positive and negative findings without assuming that fine-tuning must improve quality.

### Implications

- Response quality and inference efficiency must be reported separately.
- Fine-tuning is not required to win the quality comparison for the experiment to be informative.
- Input-token reduction does not establish latency reduction; both must be measured.
- One-time dataset and training costs remain relevant context for recurring efficiency differences.

## D-007 — Use a strong five-shot prompt baseline

- **Date:** 2026-07-14
- **Status:** Adopted

### Decision

Systems B and D will use the same detailed prompt containing exactly five high-quality worked examples alongside the ChatG&T instructions and schema.

The prompt represents the solution that would realistically be built if fine-tuning were unavailable. Its wording and example selection will be developed on non-test prompts, versioned, and frozen before held-out evaluation.

### Rationale

A weak or casually written prompt would create a strawman baseline and make fine-tuning appear successful by default. Five examples reflect the project author’s normal prompt-engineering approach and expected standard for obtaining a good response.

### Implications

- Prompt development and example selection are part of the experiment and must be documented.
- Held-out test prompts cannot be used to refine the five-shot prompt.
- The same frozen prompt is applied to Systems B and D.
- Prompt tokens, context use, and latency form part of the engineering comparison.

## D-008 — Adopt the response and system evaluation framework

- **Date:** 2026-07-14
- **Status:** Adopted

### Decision

Every attempted generation will receive automatic execution and structural measurements. Schema-valid responses will be scored holistically on:

1. underlying-answer quality;
2. metaphorical coherence; and
3. recipe-style execution.

Each qualitative dimension uses a three-point scale: 1 — Fails, 2 — Acceptable, and 3 — Strong.

A response receives a full pass only when it is schema-valid and all three qualitative scores are at least 2. The primary pairwise comparison is the blinded System B versus System C comparison, with conditional preference and end-to-end outcomes reported separately.

Efficiency reporting covers input tokens, synchronized `model.generate()` latency, output tokens, adapter size, and fine-tuning time. Application latency, cold starts, time to first token, and prefill/decode decomposition are outside the primary experiment.

### Rationale

Layered measurements reveal whether a response failed execution, structure, substance, metaphor, or style. The joint pass enforces the research question’s simultaneous requirements without allowing a strong score to compensate for a failing dimension.

### Implications

- LLM-judge scores and human scores must be labelled separately.
- Results are reported by evaluation slice as well as overall.
- Quality and efficiency differences are reported descriptively with uncertainty.
- The experiment does not impose a universal system-level threshold for accepting a quality–efficiency trade-off.

## D-009 — Adopt the limitations and validity framework

- **Date:** 2026-07-14
- **Status:** Adopted

### Decision

The experiment will maintain a limitations and validity register covering:

- internal validity and confounding factors;
- data contamination and memorisation;
- qualitative and pairwise evaluation bias;
- statistical and measurement uncertainty;
- external validity;
- efficiency-measurement limitations; and
- public-evaluation limitations.

Each important risk will be controlled where practical, measured where relevant, and disclosed where it remains unresolved.

### Rationale

Not every limitation can or should be eliminated in a portfolio-scale experiment. Recording alternative explanations and claim boundaries makes the final conclusions more credible and prevents results from being generalised beyond the evidence.

### Implications

- The B-versus-C result is described as an engineering-strategy comparison rather than the isolated causal effect of fine-tuning.
- Claims remain limited to the documented model, data, prompt, environment, and evaluation population.
- Later stages must operationalise deferred controls such as sample size, seeds, judge counts, prompt-development stopping rules, and latency procedures.
- Negative, mixed, and uncertain findings must remain visible in the final case study.

## D-010 — Adopt the compute and deployment constraints

- **Date:** 2026-07-14
- **Status:** Adopted

### Decision

ChatG&T will use a hybrid compute strategy:

- local hardware for development, data preparation, evaluation, analysis, and CPU smoke tests;
- short-lived rented NVIDIA GPU compute for LoRA training, with a one-off budget of up to **$20**; and
- free or scale-to-zero infrastructure for the public demonstration, with an ongoing budget of up to **$10 per month**.

Deployment will first be attempted on a free Hugging Face CPU Space. Hugging Face ZeroGPU and scale-to-zero inference are measured fallback options rather than preselected requirements. Cold starts and shared-infrastructure queues are acceptable for the portfolio demonstration; permanent warm availability is not required.

The full audit is recorded in [Environment and deployment constraints](environment-constraints.md).

### Rationale

The local machine has ample system memory and storage but no detected supported discrete training GPU or ready GPU-compute toolchain. Rented NVIDIA compute provides a conventional LoRA training environment without making AMD setup a separate project. Separating one-off experimental compute from recurring hosting cost also prevents an affordable training run from implying an affordable long-lived service.

### Implications

- Candidate models must have a credible path through both the training budget and hosting budget.
- Training should begin with a small end-to-end smoke run before a full paid run.
- Paid compute runtime, hardware, and cost must be captured as experimental metadata.
- CPU deployment must be measured rather than assumed to be adequate.
- The final hosting choice remains open until model latency, memory use, cold-start behaviour, and visitor experience have been tested.

## D-011 — Adopt the model-selection criteria

- **Date:** 2026-07-14
- **Status:** Adopted

### Decision

Candidate models will first be screened using hard eligibility gates and then compared using experiment-relevant preferences. The normal search range is open-weight instruction models with approximately 1–3 billion parameters.

An eligible model must have suitable fine-tuning, adapter-distribution, public-deployment, and commercial-use rights; form a credible prompted JSON baseline; support a standard Transformers and PEFT LoRA workflow; provide at least 8,192 tokens of context; and have credible training and serving paths within the agreed budgets.

The full criteria are recorded in [Model-selection criteria](model-selection-criteria.md).

### Rationale

Defining requirements before researching individual models reduces candidate-driven reasoning. Separating fatal constraints from comparative preferences prevents a model with attractive benchmark results from obscuring a licensing, tooling, or deployment incompatibility.

### Implications

- Candidates that fail a hard gate will not enter the main shortlist.
- Models outside the approximate size range require an explicit practical justification.
- Comparative trade-offs will remain visible rather than being hidden inside an initially arbitrary weighted score.
- Candidate capability checks will use disposable prompts and will not touch training, prompt-development, or held-out evaluation data.
- Advertised capabilities remain provisional until verified in the project environment.

## D-012 — Adopt the candidate-model feasibility shortlist

- **Date:** 2026-07-14
- **Status:** Adopted; base-model selection subsequently made by D-013

### Decision

Advance these models to Stage 2 feasibility testing, in initial priority order:

1. `Qwen/Qwen2.5-1.5B-Instruct`;
2. `Qwen/Qwen3-1.7B`; and
3. `HuggingFaceTB/SmolLM3-3B`.

This is a testing shortlist, not the final base-model selection. `Qwen/Qwen3.5-2B` remains on a watchlist because its current multimodal architecture and bleeding-edge library requirements introduce unnecessary uncertainty for a text-only LoRA experiment.

The full research comparison is recorded in [Candidate model shortlist](model-shortlist.md).

### Rationale

The three shortlisted models satisfy the paper-screening gates and provide useful variation within the agreed range. Qwen2.5 has the clearest explicit JSON-generation fit; Qwen3 tests a newer model at almost the same size; and SmolLM3 tests a fully documented model at the range's upper edge. All use Apache 2.0 and mainstream text-generation tooling.

Restricting executable feasibility work to three candidates keeps model search proportionate. Other screened models remain viable alternatives, but currently introduce custom licence handling, larger footprints, custom code, multimodal dependencies, or less direct evidence of task fit.

### Implications

- Feasibility checks will use the same disposable diagnostic inputs across candidates.
- Thinking output must be disabled through the official chat template for Qwen3 and SmolLM3.
- Model-specific template requirements will be recorded rather than hidden inside prompt wording.
- General publisher benchmarks will not be presented as a direct model comparison.
- The shortlist initially deferred final selection until executable checks; D-013 subsequently selected Qwen2.5 before those checks while retaining a hard-incompatibility contingency.

## D-013 — Select Qwen2.5-1.5B-Instruct as the base model

- **Date:** 2026-07-14
- **Status:** Adopted; complete technical feasibility confirmed

### Decision

ChatG&T will use `Qwen/Qwen2.5-1.5B-Instruct` as its base model. Systems A and B will use the untouched instruction model; Systems C and D will use the same base weights with the project LoRA adapter applied.

The decision will be reopened only if executable feasibility testing identifies a hard incompatibility or a material violation of an agreed constraint. Imperfect ChatG&T or JSON performance is not itself a reason to switch models, because measuring that performance is part of the experiment.

### Rationale

Qwen2.5-1.5B-Instruct offers the best overall fit to the experiment:

- its official model card specifically identifies improvements in instruction following and JSON structured generation;
- its existing structured-output capability supports a credible, non-strawman five-shot baseline;
- its text-only, direct-response design avoids reasoning-mode output and configuration as an experimental confound;
- its 1.54B size preserves the “small model” premise and provides a more credible low-cost deployment path than the 3B candidate;
- its Apache 2.0 licence supports fine-tuning, adapter distribution, public deployment, and commercial use; and
- its established Transformers and serving support favours a reproducible LoRA learning workflow.

The model is not selected because it is expected to make fine-tuning look successful. A strong prompted baseline may match or beat the adapter, which would remain a valid result.

### Implications

- Stage 2 feasibility work will focus on Qwen2.5 rather than benchmarking every shortlisted model.
- Qwen3-1.7B and SmolLM3-3B remain documented fallbacks, not additional experimental systems.
- The exact Hugging Face revision is pinned in `config/model.toml` and verified against the local weight checksum.
- Base loading, raw generation, chat templating, the LoRA lifecycle, and rented-GPU training feasibility are confirmed.
- All four experimental systems will share the same Qwen2.5 tokenizer, chat template, and base weights.

## D-014 — Omit the vendor identity system message

- **Date:** 2026-07-14
- **Status:** Adopted; implementation clarified after the official-template check

### Decision

The canonical Transformers experiment will not reproduce Ollama's default vendor system message:

> You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

The official Qwen chat template injects the vendor message whenever the first message is not a system message. Systems A and C will therefore use an explicit system message with empty content followed by the user prompt. This preserves the official template while suppressing the vendor text. Systems B and D will use the frozen detailed ChatG&T system prompt followed by the same user prompt. No system will receive the vendor identity message.

The exact message array, rendered prompt, and token count will be captured for every experimental generation.

### Rationale

The vendor message is an Ollama Modelfile default rather than part of the user's input or the behaviour under investigation. Retaining it would add recurring tokens to the nominally minimal systems and introduce an identity instruction with no relevance to ChatG&T.

Omitting it gives “no ChatG&T prompt” a precise meaning and makes the recurring input cost of the detailed five-shot intervention directly measurable. An empty system message is preferable to editing the model's official chat template: it removes the irrelevant content while preserving the role structure on which the instruction model was trained. Applying the rule symmetrically to the base and adapter-backed models preserves the two-by-two design.

### Implications

- Ollama pre-flight outputs remain valid diagnostics but are not canonical baseline outputs.
- Systems A and C use an empty system message followed by the user message.
- Systems B and D use the same detailed ChatG&T system message plus the user message.
- Application or serving runtimes must not silently inject an additional system message during formal evaluation.
- Any later public runtime that adds defaults must be configured explicitly and documented separately from the experimental environment.

## D-015 — Use uv with a pinned Python 3.12 ML environment

- **Date:** 2026-07-14
- **Status:** Adopted

### Decision

ChatG&T will use uv to manage a project-local virtual environment and cross-platform lockfile. The environment is pinned to CPython 3.12.13 and initially uses PyTorch 2.12.1, Transformers 5.12.1, PEFT 0.19.1, TRL 1.7.1, Accelerate 1.14.0, Datasets 5.0.0, and psutil 7.2.2.

The complete setup and verification procedure is recorded in [Reproducible Python environment](reproducible-environment.md).

### Rationale

The audited system Python lacked a package-management foundation, and changing system packages would make the project harder to reproduce. A project-local environment isolates dependencies, while the lockfile records the exact transitive resolution.

Python 3.12 provides a conservative compatibility target across local CPU inference, the Hugging Face fine-tuning stack, and rented NVIDIA environments. PyTorch 2.12.1 was chosen over the newly released 2.13.0 to begin from an established patch release rather than the newest available build.

### Implications

- `.venv/` is disposable and excluded from version control; `pyproject.toml`, `.python-version`, and `uv.lock` are the reproducible records.
- Project commands should run through `uv run --frozen` or a frozen synced environment.
- Dependency changes must update both the declaration and lockfile intentionally.
- The current Linux PyTorch lock includes CUDA 13 libraries and occupies more disk than a CPU-only environment.
- The model revision is pinned, and the locked environment has been reproduced successfully on rented CUDA 13 hardware.

## D-016 — Use unquantised BF16 LoRA on one 24 GB NVIDIA GPU

- **Date:** 2026-07-14
- **Status:** Adopted and confirmed on rented 24 GB hardware

### Decision

ChatG&T's initial pilot and full training approach will use the pinned Qwen BF16 weights with ordinary LoRA on a single NVIDIA GPU with 24 GB of VRAM. The base model will not initially be quantised.

QLoRA or another lower-precision base-weight approach will be introduced only if a representative measured workload cannot fit with reasonable sequence length, micro-batch size, gradient accumulation, and—if justified—gradient checkpointing. It is a contingency, not part of the default experiment.

This decision establishes the hardware class and numerical approach. It does not yet select a rental provider, GPU model, sequence-length limit, batch configuration, or final LoRA hyperparameters.

### Rationale

The pinned BF16 base weights occupy approximately 3.09 GB on disk, while the disposable lifecycle adapter added 1,089,536 trainable parameters and produced a 4.38 MB artefact. Adapter weights, gradients, and optimizer states are therefore small relative to a 24 GB device; activations and runtime overhead are expected to be the important variable and must be measured.

A 24 GB device provides a credible margin for this 1.54B-parameter model without introducing quantisation-specific libraries, configuration, or numerical behaviour. Keeping the base model unquantised makes the first training workflow easier to reproduce and keeps the experiment focused on LoRA rather than combining LoRA with a separate compression intervention.

### Implications

- The rented-GPU feasibility check will reproduce the locked environment on a single 24 GB NVIDIA device and exercise a realistic forward, backward, and optimizer step.
- The check will record GPU identity, driver, CUDA and library versions, peak allocated and reserved VRAM, tokens processed, and step duration.
- The representative workload should remain below approximately 80% of available VRAM so ordinary variation does not turn the pilot into an unstable edge case.
- Gradient accumulation may increase the effective batch size without increasing the micro-batch memory requirement.
- Quantisation will not be added merely because it is common in fine-tuning tutorials; any move to QLoRA must be justified by recorded evidence.
- Provider and exact GPU selection remain separate decisions based on availability, workflow, and current cost.

### Outcome

The representative workload passed on a 24 GB RTX 3090 without quantisation or gradient checkpointing. Peak reserved VRAM was 7.9336 GiB, or 33.6757% of the device, leaving 66.3243% headroom. QLoRA remains unnecessary under the measured configuration.

## D-017 — Use a Runpod 24 GB NVIDIA GPU for feasibility

- **Date:** 2026-07-14
- **Status:** Adopted and completed; RTX 3090 availability fallback used

### Decision

The initial rented-GPU feasibility check will use an on-demand Runpod Pod, targeting one Secure Cloud NVIDIA RTX 4090 with 24 GB of VRAM. The current official Runpod PyTorch template will provide the container and connection layer, while the project will reproduce its own uv-managed environment inside it.

If an RTX 4090 is unavailable, another Secure Cloud 24 GB NVIDIA GPU with BF16 support may be used and must be recorded. A larger-memory device will not silently substitute for the agreed 24 GB feasibility constraint.

### Rationale

Runpod provides direct access to a conventional NVIDIA environment without requiring the training program to adopt a provider-specific execution framework. That makes the workflow—provision, inspect, reproduce, train, capture, and terminate—relevant to the project's engineering-learning goal.

The RTX 4090 provides the agreed VRAM class and strong BF16 training throughput. At the $0.69 hourly rate listed when reviewed, infrastructure variability is more consequential to this bounded experiment than the small potential saving from a community-hosted device.

### Implications

- Live availability and pricing will be verified in the Runpod console before deployment.
- The Pod will use an official template, but preinstalled Python packages will not replace the locked project environment.
- GPU and storage charges, runtime metadata, and actual session cost will be captured.
- Critical outputs will be copied off the Pod before deletion.
- Stopped or persistent storage will not be left running unintentionally.
- The prepared workflow is recorded in [Runpod GPU readiness](runpod-readiness.md).

### Outcome

The preferred RTX 4090 and a CUDA 13-compatible L4 were unavailable when the check ran. A 24 GB RTX 3090 with driver 580.159.03 was used instead, preserving the BF16, CUDA 13, and physical 24 GB constraints. The displayed rate was $0.46/hour for compute plus $0.004/hour for container storage, and the final Runpod charge was $0.14.

The full result, including the rejected R570-driver L4 and measured memory, is recorded in [Rented-GPU feasibility check](gpu-feasibility-check.md).

A later Step 7 acceptance session used an available 24 GB NVIDIA L4 with driver 580.126.20. The locked CUDA 13 environment completed real BF16 computation and the two-runtime inference diagnostic for a final charge of $0.10. Total recorded Runpod expenditure across the feasibility and acceptance sessions is therefore $0.24.

## D-018 — Use immutable run artefacts and content-addressed system definitions

- **Date:** 2026-07-14
- **Status:** Adopted; implemented and accepted on real CUDA

### Decision

Every inference run will create a self-contained evidence directory with three primary records:

```text
experiments/runs/<run-id>/
├── manifest.json
├── prompts.jsonl
└── responses.jsonl
```

The manifest is immutable after the run begins and records run-level identity and configuration. The prompt file freezes the exact input population. The response file preserves one raw generation record for each attempted prompt and system combination. Schema results, qualitative scores, pairwise judgments, and summaries are derived records stored separately; they will not rewrite the original generation evidence.

Systems `A` through `D` retain stable experimental meanings:

- `A`: pinned base model with the explicit empty system message;
- `B`: pinned base model with the detailed five-shot ChatG&T system prompt;
- `C`: the same base model plus the selected LoRA adapter and the explicit empty system message; and
- `D`: the same base model plus the selected LoRA adapter and the same detailed five-shot system prompt.

Models, tokenizers, chat templates, system prompts, and adapters will be identified by human-readable versions plus immutable revisions or SHA-256 digests as appropriate. The run manifest will snapshot the complete system-prompt content and message-construction rules in addition to recording their identifiers and digests.

Versioned prompt assets are append-only once used in a recorded run. A changed five-shot prompt becomes a new version rather than overwriting an earlier one. If a requested system component—particularly the adapter for Systems C or D—is unavailable or fails identity verification, the harness must fail or record an explicit configuration error. It must never silently substitute another system.

### Rationale

An experimental label is not sufficient evidence of what a model received. Runtime defaults, template changes, prompt edits, adapter replacement, and missing-component fallbacks can all change behaviour while leaving a label such as “System B” unchanged.

Separating the stable factorial meaning of A–D from the versioned artefacts used in a particular run gives the comparison durable semantics and exact traceability. Preserving original generations separately from later validation and scoring also prevents derived interpretations from mutating the observed evidence.

### Implications

- Run IDs must be unique and their directories must not be silently overwritten.
- `manifest.json` will include model, tokenizer, template, system-prompt, adapter, environment, generation-profile, seed-policy, prompt-set, and hardware identities.
- `prompts.jsonl` and `responses.jsonl` will use stable prompt and system identifiers.
- Exact structured messages, rendered prompts, token IDs, raw decoded outputs, and component hashes will be captured at response level where needed.
- Prompt development may create successive prompt versions, but a version used in a recorded run is immutable.
- Later validator or evaluation failures remain linked derived records rather than edits to the raw response.

## D-019 — Use explicit sampled generation with paired per-prompt seeds

- **Date:** 2026-07-14
- **Status:** Adopted; implemented and accepted on real CUDA

### Decision

The primary ChatG&T comparison will use an explicit sampled generation profile rather than inheriting runtime defaults:

| Setting | Value |
| --- | ---: |
| `do_sample` | `true` |
| `temperature` | `0.7` |
| `top_p` | `0.8` |
| `top_k` | `20` |
| `repetition_penalty` | `1.1` |
| `max_new_tokens` | `512` |
| Batch size | `1` |

Each primary prompt will produce one response per included system. A deterministic generation seed will be derived from the run seed, stable prompt ID, and repeat index. The system ID will not participate in seed derivation, so Systems A–D receive the same pseudorandom stream for a given prompt and repeat regardless of execution order.

Transformers 5.12.1 does not accept a dedicated generator for ordinary sampled `generate()` calls. For each response, the harness will therefore create a dedicated device generator from the derived seed, install its state inside a serialized `torch.random.fork_rng` context, call `generate()`, and allow the context to restore the prior device-default RNG state. RNG setup and restoration occur outside the latency boundary. This preserves per-attempt determinism without patching Transformers or allowing execution order to select the random stream.

The run manifest and response record will capture the run seed, derived generation seed, RNG-application policy, settings, and generated token IDs.

Multi-seed stability testing may be performed later as a separate secondary run on a defined prompt subset. It will not multiply or selectively replace responses in the primary comparison.

The canonical settings are stored in `config/generation.toml`.

### Rationale

ChatG&T is an intentionally creative behaviour. Sampling provides a more representative test of titles, metaphors, recipe language, and useful variation than always taking the highest-probability token. A broad evaluation population provides a better primary view of sampled behaviour than repeatedly sampling a small number of prompts.

Pairing the derived seed across systems removes execution order and independently chosen random streams as avoidable asymmetries. It does not force systems with different token distributions to make equivalent choices, nor does it eliminate sampling variance from the experiment.

A 512-token ceiling gives the model room to close a complete JSON object while bounding runaway output. Actual response length remains an observed metric rather than a target.

### Implications

- The harness must pass every setting in the controlled generation profile explicitly and must not rely on mutable runtime defaults. Any remaining `GenerationConfig` defaults are inherited from the content-pinned model snapshot under the locked Transformers version and recorded as such.
- The explicit return/cache controls include one beam, one returned sequence, tensor output, no score/logit collection, and a fresh dynamic per-call cache. Empty textual stop configuration maps to no stop-string criterion.
- Formal calls are serialized per CUDA device so temporary installation of the forked RNG state cannot overlap another request.
- Model loading and warm-up occur outside recorded response latency; each measured generation uses batch size one and begins with no reusable conversation cache.
- Constrained JSON decoding, beam search, automatic retries, and output repair are excluded from the primary profile.
- All compared systems use the same settings and output-token ceiling.
- Strict reproducibility is scoped to the recorded model, prompt, software, RNG, and hardware context; cross-hardware bit-for-bit identity is not assumed.
- Generated token IDs remain the strongest evidence of what a sampled run actually produced.

## D-020 — Preserve generated tokens and define user-visible raw output precisely

- **Date:** 2026-07-14
- **Status:** Adopted; implemented and accepted on real CUDA

### Decision

For every successful generation, the harness will preserve the exact token IDs produced after the rendered input prompt. `generated_token_ids` and `generated_token_count` include a terminal control token when the model generates one. This token-level sequence is the canonical model output and the basis for compute-oriented output-token accounting.

`raw_output` is the user-visible tokenizer decoding of the generated sequence using:

```python
tokenizer.decode(
    generated_token_ids,
    skip_special_tokens=True,
    clean_up_tokenization_spaces=False,
)
```

No further transformation is permitted. The harness will not strip whitespace, normalize Unicode, remove Markdown fences or commentary, extract a JSON substring, repair syntax, or continue an incomplete response. A SHA-256 digest of the exact decoded string will be recorded.

The harness will record both:

- `generated_token_count`, including generated terminal control tokens, for compute and latency analysis; and
- `visible_output_token_count`, excluding special tokens, for user-visible response-length analysis.

`input_token_ids` and `input_token_count` cover the complete officially rendered prompt, including role markers, system content, five-shot examples, the user prompt, and assistant-generation marker. Input components will not be assigned supposedly additive token counts; paired prompt overhead will be derived from complete System B versus System A inputs for the same user prompt.

The pinned Qwen stopping configuration is explicit:

- `151645` (`<|im_end|>`) and `151643` (`<|endoftext|>`) are permitted end tokens;
- `151643` is the padding token; and
- no textual stop strings or JSON-aware stopping rule are applied.

Every response records one termination reason: `eos_token`, `max_new_tokens`, or `error`, plus any terminal token ID and whether the 512-token ceiling was reached. Length-limited output is preserved as observed and receives no retry or continuation.

Input tokenization uses truncation disabled. An input that exceeds the accepted context is recorded as an `input_context_exceeded` error rather than silently modifying the system prompt, examples, or user prompt.

The canonical policy is stored in `config/generation.toml`.

### Rationale

The terminal chat token is protocol metadata rather than visible assistant content. Treating it as JSON text would make every normally terminated response structurally invalid; silently cleaning any other visible content would instead conceal model failures. Keeping token-level and user-visible records makes this boundary explicit and auditable.

Generated terminal tokens still consume model work, so efficiency accounting should include them even though response-length presentation excludes them. Likewise, the complete five-shot prompt is a recurring model input cost and must not disappear into an unmeasured runtime layer.

Explicit termination and no-truncation policies prevent the harness from making a failing response or oversized prompt appear successful through hidden intervention.

### Implications

- Strict JSON validation will consume `raw_output` exactly as recorded.
- Markdown fences and surrounding prose remain visible and may cause validation failure.
- Leading or trailing JSON whitespace is not stripped; the JSON parser determines whether it is legal JSON whitespace.
- Generated token IDs plus the pinned tokenizer and template permit later decoding audits.
- Output-token efficiency and visible response length remain distinct metrics.
- Hitting `max_new_tokens` is observable failure evidence, not permission to continue or retry.
- Input-length errors remain explicit response attempts in the run evidence.

## D-021 — Measure one synchronized generation latency

- **Date:** 2026-07-14
- **Status:** Adopted; implemented and accepted on real CUDA

### Decision

The primary experiment will measure one latency boundary: the complete `model.generate()` call, including prompt prefill and output generation.

For each recorded response, the harness will:

1. tokenize and prepare the input before starting the clock;
2. synchronize CUDA;
3. start a monotonic high-resolution timer;
4. call `model.generate()` at batch size one;
5. synchronize CUDA again; and
6. stop the timer.

Each response record will include generation duration, complete rendered-input token count, generated token count, prompt ID, and system ID. Model loading, tokenization, decoding, file writes, and one unmeasured warm-up generation per loaded runtime are excluded.

Recorded system/prompt combinations will run independently and in a reproducibly randomized order derived from a recorded order seed. They use matched hardware and generation settings and begin without a reusable conversation cache.

Application latency, cold-start performance, time to first token, and separate prefill/decode timing are deferred to later deployment work rather than measured in the primary experiment.

The canonical timing configuration is stored in `config/generation.toml`.

### Rationale

Synchronized generation time directly tests the relevant engineering trade-off: whether replacing a large five-shot prompt with a small adapter changes model-compute latency. It includes both prompt processing and response generation while avoiding several extra clocks that the current research question does not need.

CUDA synchronization is required because GPU work is asynchronous; without it, a CPU timer can stop before generation has actually finished. Randomized execution order reduces systematic bias from heat, contention, or other drift across a run.

### Implications

- The result is model-generation latency, not user-perceived application latency.
- Input and generated token counts remain necessary for interpreting latency differences.
- Model loading and the first warm-up are not included in response latency.
- The primary one-sample-per-system/prompt design supports descriptive latency comparisons; dedicated repeated performance benchmarking can be added later if needed.
- Static-prefix caching is disabled in the primary comparison rather than modelled as a separate deployment strategy.

## D-022 — Use simple, explicit generation failure semantics

- **Date:** 2026-07-14
- **Status:** Adopted; implemented and accepted on real CUDA

### Decision

Failure handling has three levels:

1. **Pre-run failure:** If the pinned model, tokenizer, required adapter, configuration, or required GPU cannot be loaded and verified, abort before beginning the run.
2. **Attempt failure:** Every started system–prompt attempt records exactly one status: `success`, `input_context_exceeded`, or `generation_error`. A generation error includes its exception type and message. It receives no automatic retry or fabricated output. The run continues only when the runtime remains healthy.
3. **Run interruption:** If the process is interrupted or the GPU becomes unsafe, preserve all records already written and leave all unattempted combinations absent. Do not synthesize missing results.

A CUDA error that may compromise the runtime records the current attempt as `generation_error` where possible and then aborts the run. Other isolated generation errors may be recorded before continuing.

Reaching `max_new_tokens` is a successfully executed generation with a `max_new_tokens` termination reason. Its untouched output remains eligible to fail later JSON, schema, or qualitative evaluation.

A run is complete only when it contains exactly one response record for every system–prompt combination scheduled by its frozen manifest and prompt file. Coverage, rather than a rewritten manifest or imputed rows, determines completeness.

The evaluation harness and future web application will be separate callers of one shared inference engine. The engine owns model and adapter loading, chat-template rendering, generation, decoding, timing, and the attempt result. The evaluation harness adds controlled batch scheduling and evidence capture; the web application adds interactive request and presentation behaviour.

The canonical failure policy is stored in `config/generation.toml`.

### Rationale

These statuses distinguish execution failure from structural and qualitative failure without introducing a recovery framework that could hide model behaviour. Preserving partial evidence makes interruption auditable, while fail-fast identity checks prevent results from being produced by the wrong system.

Sharing the inference engine keeps evaluation and deployment behaviour aligned without forcing research-only concerns such as immutable run artefacts and randomized batch scheduling into the user-facing application.

### Implications

- JSON and schema validation only evaluate `success` records with visible output.
- A successful execution is not automatically a valid or good response.
- Failed attempts remain part of end-to-end denominators.
- Incomplete runs are never silently presented as complete runs.
- Application-layer error messages or future defensive behaviour must not rewrite experimental evidence.

## D-023 — Freeze the reviewed inference-harness specification

- **Date:** 2026-07-14
- **Status:** Adopted; implemented and accepted on real CUDA

### Decision

Version 1.2 of [Step 7 inference and capture harness specification](inference-harness-specification.md) is the implementation contract for the shared inference engine, offline evaluation runner, and verification suite.

The specification was subjected to four independent adversarial reviews. The first three blocked implementation and their material findings were resolved; the fourth passed it without a remaining experimental or schema decision.

Systems A/B will use a separately loaded untouched base runtime, while C/D will use a separately loaded base plus unmerged PEFT runtime. Each loaded runtime receives one sampled, untimed warm-up. This preserves realistic prompt-only versus adapter deployment paths while keeping a system's implementation stable regardless of which other systems are selected.

The formal runtime profile is stored in `config/inference.toml`. Step 7 cannot be marked completed until the unit, compilation, local CPU model/adapter, and real-CUDA end-to-end acceptance checks in the frozen specification pass. If CUDA is unavailable during implementation, that acceptance criterion remains pending rather than silently waived.

### Rationale

The review process exposed several plausible but incorrect assumptions, including an unsupported per-call generator argument in the pinned Transformers version and a single-device placement attribute that the pinned loading path does not create. Freezing only after checking the actual library behavior reduces the chance that the builder must reinterpret the experiment while implementing it.

Separate stable runtimes make latency reflect the two deployment strategies being compared rather than an artificial shared wrapper. Exact implementation, model, tokenizer, prompt, adapter, configuration, environment, token, timing, and failure evidence makes later results auditable.

### Implications

- Material implementation deviations require a specification revision and review before formal results are created.
- Diagnostic provenance bypass is narrowly represented and forbidden for formal runs.
- The shared engine remains device-agnostic; canonical experimental timing remains CUDA-only.
- Web serving will reuse the engine boundary, not the research runner and its artefact machinery.

## D-024 — Use strict, portable, non-repairing schema validation

- **Date:** 2026-07-14
- **Status:** Adopted; specification 1.3 implemented and accepted locally

### Decision

ChatG&T structural evaluation will use a Draft 2020-12 JSON Schema and the directly pinned `jsonschema==4.26.0` implementation. The response schema is closed at the top-level and ingredient-object levels, performs no type coercion, and implements the hard requirements in [ChatG&T behavioural contract](behavioural-contract.md) without introducing the deferred character-length limits.

A separate strict parser will evaluate the complete untouched raw output. It permits JSON whitespace but rejects Markdown fences, surrounding prose, duplicate keys, malformed JSON, non-standard numeric constants, and multiple values. Diagnostic inspection may classify a fence or surrounding text but cannot turn extracted content into a valid response.

Validation produces stable, deduplicated failure labels, path-level diagnostics, structural observations, and hashes binding the result to the exact raw output and schema. It contains no repaired response, timestamp, or machine-specific value, so equal inputs produce byte-equivalent canonical records.

The frozen contract and acceptance suite are recorded in [Step 8 schema validation specification](schema-validation-specification.md). Three fresh reviews blocked earlier versions on material numeric, classification, schema-identity, diagnostic, and serialization problems; a fourth fresh review passed version 1.3 without a remaining material blocker.

### Rationale

Valid JSON and valid ChatG&T structure are separate properties. Preserving that distinction reveals whether a model failed basic serialization or produced machine-readable data with the wrong contract. Refusing extraction and repair keeps first-attempt schema-valid rate a measurement of model behaviour rather than application recovery.

JSON Schema is portable to later Python and web consumers, while an explicit strict-parser layer covers properties that schema validation cannot observe after ordinary parsing, particularly duplicate keys and text outside the JSON value. Stable project-owned labels prevent library message changes from silently changing metrics.

### Implications

- Every fenced preflight JSON response remains a structural failure and is specifically diagnosable as `markdown_fence`.
- Schema validity remains a hard gate; qualitative dimensions cannot compensate for structural failure.
- Execution failures remain owned by the inference/evaluation layer rather than being misreported as JSON errors.
- Future constrained decoding, retry, or repair would be a separately labelled intervention, not part of the primary comparison.
- Step 8 requires no model or GPU and is complete only when the frozen acceptance suite passes.

The implementation, 33 focused acceptance tests, and complete 73-test regression suite pass as recorded in [Schema validation implementation check](schema-validation-check.md).

## D-025 — Use a fixed 20-prompt development workbench

- **Date:** 2026-07-14
- **Status:** Adopted; version 1 frozen and verified

### Decision

ChatG&T prompt development will use exactly 20 user prompts: four prompts in each of the five intent families. Every family contains one clean, naturalistic, constrained, and robustness prompt.

The set is an inspectable engineering workbench for developing the five-shot system prompt and comparing Systems A and B. It contains user prompts and metadata rather than ideal responses, and its outputs are development evidence rather than headline experimental results.

The complete scenario blueprint and authoring rules are recorded in [Prompt-development set plan](prompt-development-set-plan.md).

The exact version 1 artefact is [`data/development/prompts-v1.jsonl`](../data/development/prompts-v1.jsonl), frozen at SHA-256 `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1`. It passed the closed composition, metadata, serialization, and identity contract before any model output was generated, as recorded in [Prompt-development set check](prompt-development-set-check.md).

### Rationale

The repeated four-role structure creates purposeful diagnostic variation without turning a portfolio-scale development activity into a large pseudo-benchmark. Writing the set before generation prevents individual outputs from determining which tasks are retained, while later held-out prompts provide the genuine generalisation test.

### Implications

- All exact prompt wording will be reviewed and frozen before model outputs are inspected.
- Development prompts and close paraphrases are excluded from training, fine-tuning validation, five-shot examples, and held-out evaluation.
- System A is run once; System B prompt versions use the same development inputs, settings, and derived seeds.
- Development percentages are diagnostic and will not be reported as final performance estimates.
- Formal cross-domain labels remain deferred until training topics and withheld domains are defined.
