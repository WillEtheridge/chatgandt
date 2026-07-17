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

The full audit is recorded in [Environment and deployment constraints](stage-2/model/environment-constraints.md).

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

The full criteria are recorded in [Model-selection criteria](stage-2/model/model-selection-criteria.md).

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

The full research comparison is recorded in [Candidate model shortlist](stage-2/model/model-shortlist.md).

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

The complete setup and verification procedure is recorded in [Reproducible Python environment](stage-2/model/reproducible-environment.md).

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
- The prepared workflow is recorded in [Runpod GPU readiness](stage-2/model/runpod-readiness.md).

### Outcome

The preferred RTX 4090 and a CUDA 13-compatible L4 were unavailable when the check ran. A 24 GB RTX 3090 with driver 580.159.03 was used instead, preserving the BF16, CUDA 13, and physical 24 GB constraints. The displayed rate was $0.46/hour for compute plus $0.004/hour for container storage, and the final Runpod charge was $0.14.

The full result, including the rejected R570-driver L4 and measured memory, is recorded in [Rented-GPU feasibility check](stage-2/model/gpu-feasibility-check.md).

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

Version 1.2 of [Step 7 inference and capture harness specification](stage-2/inference/inference-harness-specification.md) is the implementation contract for the shared inference engine, offline evaluation runner, and verification suite.

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

The implementation, 33 focused acceptance tests, and complete 73-test regression suite pass as recorded in [Schema validation implementation check](stage-2/inference/schema-validation-check.md).

## D-025 — Use a fixed 20-prompt development workbench

- **Date:** 2026-07-14
- **Status:** Adopted; version 1 frozen and verified

### Decision

ChatG&T prompt development will use exactly 20 user prompts: four prompts in each of the five intent families. Every family contains one clean, naturalistic, constrained, and robustness prompt.

The set is an inspectable engineering workbench for developing the five-shot system prompt and comparing Systems A and B. It contains user prompts and metadata rather than ideal responses, and its outputs are development evidence rather than headline experimental results.

The complete scenario blueprint and authoring rules are recorded in [Prompt-development set plan](stage-2/prompt-development/prompt-development-set-plan.md).

The exact version 1 artefact is [`data/development/prompts-v1.jsonl`](../data/development/prompts-v1.jsonl), frozen at SHA-256 `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1`. It passed the closed composition, metadata, serialization, and identity contract before any model output was generated, as recorded in [Prompt-development set check](stage-2/prompt-development/prompt-development-set-check.md).

### Rationale

The repeated four-role structure creates purposeful diagnostic variation without turning a portfolio-scale development activity into a large pseudo-benchmark. Writing the set before generation prevents individual outputs from determining which tasks are retained, while later held-out prompts provide the genuine generalisation test.

### Implications

- All exact prompt wording will be reviewed and frozen before model outputs are inspected.
- Development prompts and close paraphrases are excluded from training, fine-tuning validation, five-shot examples, and held-out evaluation.
- System A is run once; System B prompt versions use the same development inputs, settings, and derived seeds.
- Development percentages are diagnostic and will not be reported as final performance estimates.
- Formal cross-domain labels remain deferred until training topics and withheld domains are defined.

## D-026 — Use five frozen, cross-family worked examples

- **Date:** 2026-07-14
- **Status:** Adopted; example content frozen and verified

### Decision

The realistic System B prompt baseline will contain exactly five worked examples: one from each intent family. Their roles are clean advice, constrained explanation, naturalistic emotional support, robustness creative generation, and constrained short-form transformation.

The exact user inputs and ideal responses are stored in [`data/prompt-engineering/worked-examples-v1.json`](../data/prompt-engineering/worked-examples-v1.json), frozen at SHA-256 `0cb6afd2bf88ed1f9a3edf8e5ffc479e22c69b91ea7220988c5b1dee51f429b6`. All five ideal responses pass the frozen ChatG&T response schema.

System-prompt development is limited to four total versions: an initial version plus at most three evidence-backed revisions. Revisions must address recurring or generalisable development failures, use unchanged inputs and inference settings, and retain their prompts, results, token counts, and rationales.

### Rationale

One example per family demonstrates semantic breadth, while distributing clean, naturalistic, constrained, and robustness roles teaches more than five straightforward examples would. Repeating the constrained role demonstrates that the cocktail conceit must still deliver explanations and completed artefacts precisely.

A finite, recorded revision budget permits competent prompt engineering without an open-ended search that silently overfits the 20 known development prompts.

### Implications

- Worked-example inputs, outputs, and close paraphrases are excluded from development, training, validation, and held-out data.
- Exact development overlap and response-schema validity are checked automatically; semantic quality and close-paraphrase separation remain reviewed authoring responsibilities.
- The complete System B instruction text and assembled prompt asset are not yet frozen.
- The final version-selection rule must be operationalised before development results select the prompt baseline.

## D-027 — Freeze the initial System B prompt before development generation

- **Date:** 2026-07-14
- **Status:** Adopted; prompt asset version 1 assembled and verified

### Decision

The approved instructions and five worked examples are deterministically assembled into [`config/prompts/five-shot-v1.json`](../config/prompts/five-shot-v1.json). The initial asset has identifier `five-shot-v1`, version `1`, and SHA-256 `7b8c25f04fba15373813862bba9705d4585ba919e855612909830757e4bd93d6`.

The exact prompt explicitly prioritises a useful underlying answer, states the closed JSON contract, distinguishes compatible content constraints from conflicting output-format requests, requires completed artefacts in the final method step, and finishes with a raw-JSON reminder after the five examples.

### Rationale

Assembling and freezing the first prompt before model generation separates prompt authorship from output-driven revision. Deterministic rendering proves that the deployed system content matches the reviewed instruction and example sources rather than an undocumented copy.

The prompt is intentionally a credible five-shot baseline rather than a token-minimised strawman. Across the 20 development prompts it adds exactly 2,319 input tokens relative to the empty-system condition. This recurring cost is material experimental evidence, not a reason to weaken the baseline before comparison.

### Implications

- Version 1 cannot be overwritten after its first run; any revision becomes a new append-only prompt asset.
- The complete rendered five-shot inputs range from 2,344 to 2,394 tokens on the development set and fit comfortably inside the pinned context limit.
- No quality claim is made until the controlled System A/B development run.
- Prompt revisions remain governed by the four-version ceiling and recorded rationale requirement in D-026.

## D-028 — Use master seed 20260714 for prompt development

- **Date:** 2026-07-14
- **Status:** Adopted; frozen before development generation

### Decision

The initial System A/B development run and later System B prompt-version comparisons will use master run seed `20260714`. It is bound to the frozen prompt and system inputs in [`config/runs/development-ab-v1.json`](../config/runs/development-ab-v1.json), SHA-256 `63db3e2cd65354b037c62eda2c5cabc34ae32f336b42aff8cf7f19cd08672271`.

The harness derives each generation seed from the master seed, prompt ID, and repeat index while excluding system identity. It derives the execution-order seed independently in its own namespace. The resulting order seed for this run is `17625029341685692511`.

### Rationale

The number is memorable, valid, and chosen before any development output was observed. A fixed master seed makes the sampled experiment repeatable and gives A, B, and later B prompt versions paired pseudorandom streams without claiming that different probability distributions receive equivalent token choices.

### Implications

- The seed is not changed in response to favourable or unfavourable outputs.
- Prompt versions reuse it for paired development comparison.
- Any later multi-seed stability analysis declares a separate seed set and is reported as a secondary experiment.
- Reproducibility still depends on the recorded model, software, and hardware environment; a fixed seed alone does not promise cross-platform bit identity.

## D-029 — Reuse a stopped Pod across nearby development runs

- **Date:** 2026-07-15
- **Status:** Adopted for future runs

### Decision

A suitable Runpod Pod may be reused across nearby prompt-development or training iterations. All reusable state must remain beneath the Pod's `/workspace` volume disk. After each run, the complete evidence is copied home and verified before the Pod is either stopped or terminated.

The Pod is stopped when another authorised run is reasonably expected soon enough to justify retaining its billable storage. It is terminated when no next run is prepared, the development cycle has ended, the environment is no longer confidently verifiable, or storage retention is no longer economical. A daily reminder guards against forgotten stopped-storage charges.

Restarting the same Pod does not waive preflight. Each session rechecks the GPU and BF16 path, checks out an exact authorised commit, reproduces the frozen dependency state, verifies the pinned model and run inputs, uses a new run ID, and preserves a separate manifest and billing record. The complete procedure is recorded in [Reusable Runpod development workflow](operations/reusable-runpod-workflow.md).

### Rationale

Experimental reproducibility depends on the recorded identity of the behaviour and environment, not on receiving a physically new machine for every run. Reusing verified model files, dependency caches, and repository data reduces repeated setup effort and billed GPU time without changing the comparison, provided every run independently verifies its inputs and preserves its raw evidence.

Stopping rather than leaving the Pod running separates cheap persistence from expensive active compute. Termination remains the correct boundary when reuse is no longer imminent.

### Implications

- The initial `development-ab-v1-20260715` Pod was already terminated after local evidence verification and cost `$0.15`; reuse begins with the next Pod.
- The persistent workspace is a cache and working environment, not the sole copy of any result.
- Prompt and code changes are prepared, reviewed, and committed locally rather than improvised on the Pod.
- Same-Pod runs remain distinct experiments with unique IDs, manifests, immutable outputs, and cost records.
- A stopped Pod and its volume remain subject to active cost review.

## D-030 — Accept the first development A/B run with disclosed metadata limitations

- **Date:** 2026-07-15
- **Status:** Adopted

### Decision

Run `development-ab-v1-20260715` is accepted as complete development evidence for the System A versus initial System B comparison. Its three immutable files passed local integrity inspection, their hashes matched the Pod copies, all 40 scheduled attempts produced one successful record, and the final Runpod charge was `$0.15`.

The acceptance explicitly retains three limitations: the harness's own lock file caused its Git dirty flag, the pinned Torch API could not collect the CUDA driver version, and several provider-administration details were not retained. The exact evidence and assessment are recorded in [Development System A/B v1 run acceptance](stage-2/prompt-development/development-ab-v1-run-acceptance.md).

### Rationale

The missing provider details do not change what either system received. The missing driver value reduces exact environment reconstruction but not the paired within-session comparison. The Git flag is not treated as trustworthy cleanliness evidence; instead, the immutable manifest separately binds the commit, behavior tree, project and dependency files, model, configuration, prompts, systems, schedule, and seeds.

Rejecting a complete development run because of non-behavioral administrative gaps would discard valid evidence without improving the experiment. Hiding those gaps would overstate provenance. Conditional acceptance preserves both the useful evidence and an honest account of its limits.

### Implications

- No schema or quality claim follows from operational acceptance.
- The run may be analysed only after the prompt-version stopping rule is frozen.
- The Git cleanliness measurement must be corrected before the next formal GPU run.
- Future sessions should automate provider and `nvidia-smi` capture where practical.
- These development outputs cannot be used as held-out evidence.

## D-031 — Use local Ollama for prompt iteration and the pinned harness for confirmation

- **Date:** 2026-07-15
- **Status:** Adopted before response-quality inspection

### Decision

System B prompt development will use the installed local Q4_K_M Qwen2.5-1.5B Ollama artefact as a fast diagnostic workbench. Every candidate version, including v1, runs on the same frozen 20-prompt development population with fixed local settings and stable per-prompt seeds. The selected prompt text is then rerun unchanged through the pinned Hugging Face BF16 harness for formal confirmation.

Any prompt whose generated development outputs are inspected becomes an immutable numbered version. The existing ceiling of four total versions still applies. A revision requires the same prompt-addressable failure in at least two responses, and versions are selected by the predeclared full-pass, schema, qualitative-acceptability, and prompt-cost ordering in [Prompt-development procedure](stage-2/prompt-development/prompt-development-procedure.md).

### Rationale

Prompt iteration does not require rented GPU hardware. Local generation makes the engineering feedback loop faster and cheaper, while a final pinned run retains exact model identity, formal evidence capture, and matched performance measurement.

Treating local outputs as formal evidence would overstate comparability because Ollama uses quantised weights and different runtime machinery. Treating a new physical machine as necessary for every wording experiment would instead confuse infrastructure freshness with experimental identity.

### Implications

- Local outputs are labelled diagnostics and never substituted for held-out or formal results.
- All compared prompt versions receive a local run; formal v1 and local candidate metrics are not mixed into one version ranking.
- Inspected prompt variants and unsuccessful revisions remain visible.
- System A is not repeatedly regenerated during the local loop.
- The eventual System B versus System C experiment remains a matched pinned-harness comparison.

## D-032 — Select five-shot prompt v3 and stop prompt development

- **Date:** 2026-07-15
- **Status:** Adopted; pinned structural confirmation complete

### Decision

`five-shot-v3`, SHA-256 `cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31`, is selected as the System B prompt candidate.

Across the unchanged 20-prompt local workbench, versions v1 through v4 produced selection vectors of `4 / 9 / 5 / 7 / 6`, `6 / 11 / 6 / 10 / 10`, `7 / 11 / 7 / 10 / 11`, and `6 / 10 / 6 / 9 / 10`. The vector follows the predeclared order: full passes, schema-valid responses, and acceptable underlying-answer, metaphor, and recipe-style counts.

Prompt iteration stops. Version 4 regressed and the four-version ceiling is exhausted. Version 3 will be rerun unchanged as System B through the pinned BF16 harness before it is treated as the formal baseline.

### Rationale

Version 3 wins on the first and primary selection criterion: seven full response passes. Version 4 reduced mean local prompt tokens from 2,582.15 to 2,400.15, but efficiency is a tie-breaker only when quality is otherwise tied. Choosing v4 would change the frozen rule after seeing the outputs.

### Implications

- Development metrics remain diagnostic and cannot support held-out generalisation claims.
- No fifth prompt version may be derived from these development outputs.
- A material local-to-formal discrepancy is reported rather than tuned away after the revision budget has closed.
- Formal confirmation measured mixed v3 transfer; final B-versus-C quality and latency claims still require a matched held-out run.

## D-033 — Accept the pinned System B v3 confirmation run

- **Date:** 2026-07-15
- **Status:** Adopted; structural and qualitative scoring complete

### Decision

Run `development-b-v3-confirmation-20260715` is accepted as complete development evidence. All 20 scheduled base-System-B attempts completed through the pinned BF16 harness, the immutable local copy passes inspection, and the frozen structural evaluator found 12 schema-valid responses.

The `$0.14` run is accepted despite one preflight unit-test error. That test depended on a Git-ignored diagnostic adapter missing from the fresh clone; the confirmation selected no adapted system and loaded no adapter. The fixture dependency must be removed before the next formal run.

### Rationale

The failure was isolated to test setup for an unused runtime path. The manifest proves that the authorised clean commit, pinned base model, selected v3 prompt, frozen prompts, configuration, seed, and base-only System B path produced the recorded responses. Rejecting those responses would not provide a more faithful measurement of prompt transfer.

Pinned v3's 12 schema-valid responses are close to local v3's 11 and improve on pinned v1 System B's nine. This is structural development evidence only; qualitative scoring and held-out evaluation remain necessary.

### Implications

- The raw run remains immutable and the preflight deviation remains visible.
- The adapter-loading unit test must use a self-contained disposable fixture before another formal run.
- Cross-session A/B latency must not be treated as matched evidence.
- Prompt version 3 remains closed to further development revision.

## D-034 — Treat v3 prompt transfer as structurally successful but qualitatively mixed

- **Date:** 2026-07-15
- **Status:** Adopted

### Decision

Retain `five-shot-v3` as the frozen System B prompt while recording that its pinned transfer result is mixed.

Pinned v3 produced 12 schema-valid responses and five full passes from 20 attempts. Local v3 produced 11 schema-valid responses and seven full passes. Pinned v1 produced nine schema-valid responses and six full passes. V3 therefore improved the structural count without improving the end-to-end full-pass count on the pinned development run.

### Rationale

The prompt was selected by a rule frozen before version outputs were inspected. Reopening prompt development because the confirmation result is less favourable would undermine that boundary and tune further against the same 20 known prompts.

The confirmation has still done its job: it showed which local behaviour transferred and which did not. Structure transferred approximately; natural recipe voice and simultaneous task fulfilment were less reliable. That is actionable evidence for dataset design and the later fine-tuning comparison.

### Implications

- Version 3 remains the five-shot prompt used by Systems B and D.
- Development results do not support a claim that v3 is categorically better than v1.
- Training examples must demonstrate useful task completion and natural recipe execution, not merely valid schema shape.
- Stage 3 evaluation must preserve separate structural and qualitative measurements.

## D-035 — Close Stage 2 and proceed to evaluation design

- **Date:** 2026-07-15
- **Status:** Adopted

### Decision

Stage 2 passes its readiness review and is complete. ChatG&T will proceed to Stage 3 using Qwen2.5-1.5B-Instruct, `five-shot-v3`, the pinned generation profile, and the accepted harness and validation tooling as its technical baseline.

The full assessment is recorded in [Stage 2 readiness review](stage-2/stage-2-readiness-review.md).

### Rationale

The selected model, dependency environment, LoRA lifecycle, representative training workload, base and adapted CUDA inference, evidence harness, structural validator, development population, prompt baseline, and System A/B development evidence have all been exercised and recorded. No held-out evaluation output has been used.

The non-portable adapter-loading unit fixture is a real defect but does not prevent Stage 3's documentation and dataset-design work. It is a hard gate before the next formal model run rather than a reason to keep Stage 2 open.

### Implications

- No further System B prompt revision is authorised from the spent development set.
- Stage 3 must freeze the evaluation protocol before dataset creation begins.
- Development results remain diagnostic and cannot become headline claims.
- The adapter test fixture must be corrected and clean-clone verified before Stage 6 GPU execution.

## D-036 — Use 60 prompts for the held-out evaluation

- **Date:** 2026-07-15
- **Status:** Adopted

### Decision

The frozen held-out evaluation will contain 60 prompts, divided equally across the five intent families at 12 prompts per family. Every family will contain six target-use prompts, three cross-domain prompts, and three robustness prompts, producing overall slice totals of 30, 15, and 15 respectively.

Quotas for input forms, task complexity, ordinary constraints, and robustness roles are decided separately in D-037 before any prompt text is authored.

### Rationale

Forty prompts would be a credible minimum for detecting large effects and recurring failures, but would leave substantial sampling uncertainty and only eight prompts per intent family under an equal allocation. Sixty is a better balance between evidential value and portfolio-scale workload: it permits 12 prompts per family, yields 60 primary B-versus-C comparisons, and remains manageable when four systems produce 240 total responses.

The choice is not presented as a formal power calculation. Near a 50% result, 60 independent observations imply a rough 95% margin of error of about 13 percentage points. The experiment can therefore support descriptive conclusions about large differences, failure patterns, and quality-efficiency trade-offs, but not precise claims about small preference improvements.

Equal representation prevents the overall result from being driven by an intent family that happens to favour one system. The 50/25/25 reporting-slice allocation gives ordinary intended use the greatest weight while retaining meaningful cross-domain and robustness tests in every family.

### Implications

- Overall outcome rates will be accompanied by uncertainty intervals.
- Fine-tuned wins, prompted-baseline wins, and ties will be reported separately.
- A decisive-comparisons-only preference rate may be supplementary, but will not replace the three-way result.
- Intent-family and reporting-slice findings will be treated as diagnostic rather than statistically conclusive.
- D-037 completes the remaining cross-cutting quotas required to close Step 2.

## D-037 — Freeze the remaining held-out sample architecture

- **Date:** 2026-07-15
- **Status:** Adopted

### Decision

The 60-prompt held-out sample will contain 15 questions, 30 direct requests or commands, and 15 statements or fragments. Input form will be classified by communicative function rather than punctuation and may vary naturally by intent family.

Forty prompts will contain one standard task and 20 will be composed from additional context, multiple outcomes, meaningful constraints, supplied material, competing considerations, or connected steps. Ten composed prompts will carry explicit ordinary user constraints, with two in each intent family.

The 15 robustness prompts will comprise five format-pressure, five behaviour-pressure, and five serialization-pressure prompts. Each intent family will contain one prompt in each robustness role, and every robustness prompt must retain a legitimate underlying task.

### Rationale

Input-form coverage prevents the evaluation from quietly becoming a set of uniformly phrased questions. Observable task composition is more reproducible than assigning subjective difficulty labels. Explicit ordinary constraints test whether an answer actually follows the user's request, while the separate robustness roles isolate common pressures on JSON validity and behavioural persistence.

The architecture deliberately permits labels to overlap. These are cross-cutting descriptions of the same 60 prompts, not independent collections to be added together.

### Implications

- Prompt authors must satisfy the complete cross-cutting quota table before the held-out set can freeze.
- Question-shaped requests are classified as requests when task performance is their primary function.
- The intent families need not have identical input-form or complexity distributions.
- Robustness findings support focused contract-persistence claims, not comprehensive security claims.
- Stage 3 Step 2 is complete; exact held-out prompt text will not be authored until the evaluation protocol and supervised data are separately frozen.

## D-038 — Freeze training data before authoring the held-out prompts

- **Date:** 2026-07-15
- **Status:** Adopted

### Decision

ChatG&T will freeze the evaluation rules and sample blueprint first, then create and freeze the training and validation data without exact held-out prompts in view. The 60 held-out prompts will be authored afterwards to the frozen blueprint, collision-checked against all project data, reviewed, and frozen before any pilot or full fine-tuning begins.

If a candidate held-out prompt collides with the already-frozen supervised data, it will be rejected and replaced only under the predeclared overlap rules, with the reason retained in an auditable log. The training data will not be rewritten around a known test prompt.

The cross-domain topic policy must be frozen during evaluation design and enforced during dataset creation so that withheld topics cannot be selected opportunistically after inspecting the training set.

### Rationale

Freezing exact test prompts before authoring supervised data would let dataset authors know the exam questions and could shape training examples around them. Authoring the test after the dataset avoids that direction of leakage. Freezing the evaluation blueprint first prevents the later test author from changing its composition or rules to flatter the finished dataset.

The final gate remains unchanged in substance: no model training and no held-out generation may occur until the exact test set is reviewed and sealed. This separates evaluation-design knowledge from exact test content while keeping the generalisation claim auditable.

### Implications

- Stage 3 freezes the evaluation protocol, not the exact prompts.
- Stage 4 creates and freezes training and validation data without model training.
- Stage 5 authors and freezes the exact held-out set.
- Stage 6 is the first stage permitted to fine-tune the model.
- Any later change to frozen supervised data or evaluation assets requires a versioned protocol amendment and a repeated contamination audit.

## D-039 — Operationalise project-unseen prompts with retrieval and recorded judgment

- **Date:** 2026-07-15
- **Status:** Adopted; version 1 frozen

### Decision

“Unseen” will mean absent as an exact, close-paraphrase, or substantively duplicated scenario within observable ChatG&T project material. Shared domain or task form is allowed when the required substantive answer differs. A duplicated scenario requires the same user goal, substantially the same situation, concept, source, or artefact, and an answer reusable with only surface changes.

Exact normalized matching is followed by top-five RapidFuzz 3.14.5 `token_ratio`, pinned MiniLM semantic, and structured-metadata retrieval. Scores retrieve neighbours but never decide contamination. Every rejection and uncertainty, plus a deterministic 10% audit of accepts, receives a decision-blinded second review. Unresolved cases are conservatively replaced with the history retained.

Photography, tabletop games, and pottery/ceramics are withheld from worked examples, prompt development, training, and validation. Each supplies one cross-domain prompt in every intent family.

### Rationale

Exact text checks miss paraphrases, while numerical similarity cannot distinguish a shared capability from a duplicated answer. Combining several retrieval signals with an executable semantic rule narrows the manual search without outsourcing the scientific judgment to an opaque threshold.

Three crossed domains provide broader capability coverage than three isolated prompts while keeping the exclusion enforceable during dataset creation. The claim remains project-specific because base-model pretraining is unknown.

### Implications

- The held-out set requires full collision records and a replacement log.
- MiniLM's 256-wordpiece truncation and RapidFuzz subset inflation remain disclosed limitations.
- Exact held-out prompts are still authored only after supervised data freeze.
- The protocol must pass independent adversarial review before its identity is frozen.

## D-040 — Freeze judging, pairwise, uncertainty, and similarity procedures before outputs

- **Date:** 2026-07-15
- **Status:** Adopted; version 1 frozen

### Decision

Every schema-valid output receives one blinded LLM-judge application of the anchored three-dimension rubric. The project author independently calibrates 24 response packets and 15 B-versus-C pairs selected by frozen hash rules. Human and LLM evidence remains separately labelled and agreement is reported without a post-hoc pass threshold.

B-versus-C order is deterministically balanced 30/30 across the 60 prompts. Conditional preference uses only pairs where both outputs are schema-valid; the end-to-end outcome additionally awards a sole schema-valid response and records two invalid responses as `both_failed`.

Overall binary rates use 95% Wilson intervals. Paired C-minus-B differences use 10,000 prompt-ID bootstrap resamples with seed `20260715`, always carrying each prompt's paired system outcomes together. Subgroups are diagnostic. Generated-response similarity is checked separately from prompt contamination against worked-example and training responses using exact, lexical, semantic, and recorded human-readable review.

### Rationale

Freezing denominators, eligibility, ties, order, judge roles, calibration samples, uncertainty, and similarity interpretation before output inspection removes many opportunities to select the most flattering analysis later. A limited human calibration is feasible for a portfolio project without misrepresenting one author's judgments as population preference.

### Implications

- Qualitative LLM-judge results are not called human evaluation.
- Schema failures remain end-to-end failures without invented qualitative scores.
- Poor human–LLM agreement limits the claims; it does not trigger rubric tuning on held-out outputs.
- Similarity flags identify suspicious cases but cannot prove fine-tuning memorisation or reveal base-model pretraining.

## D-041 — Pin proportionate retrieval tooling and expose its truncation boundary

- **Date:** 2026-07-15
- **Status:** Adopted; version 1 frozen

### Decision

Lexical retrieval uses RapidFuzz `3.14.5` `fuzz.token_ratio`. Semantic retrieval uses `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, loaded through the pinned Transformers runtime with its documented attention-masked final-hidden-state mean pooling, L2 normalization, 384 dimensions, and cosine ranking.

Semantic inputs truncate at 256 wordpieces. Every retrieval record carries the pre-truncation wordpiece count and truncation flag; truncated candidates or references require complete-text manual review. A deliberately long supplied-text calibration case must prove that diagnostic executes.

### Rationale

The project needs to retrieve neighbours from fewer than 500 short English records, not operate a search service. Exhaustive local comparison with a small encoder is cheaper and more reproducible than a hosted API or vector database. RapidFuzz complements the encoder on surface edits, but neither score is a contamination verdict.

### Implications

- RapidFuzz remains retrieval-only even at very high similarity.
- Content after 256 MiniLM wordpieces is invisible to the semantic vector and cannot be described as checked by that signal.
- The exact model revision, pooling implementation, package version, top-k values, and calibration evidence are part of protocol identity.
- Changing any selected tool or truncation rule requires a new protocol version before results.

## D-042 — Author held-out prompts only through the frozen matrix and replacement process

- **Date:** 2026-07-15
- **Status:** Adopted; version 1 frozen

### Decision

Stage 5 will begin with a blank 60-row quota matrix after supervised data freeze. Candidates receive metadata before collision review and may be replaced only for the seven versioned reasons in the authoring protocol. Rejected candidate identity, rationale, retrieval/review evidence, and replacement linkage remain in the record. No held-out response may exist during authoring.

The held-out set freezes only after exact IDs and every global and crossed quota pass, all collision decisions resolve, the withheld-domain absence check repeats against frozen sources, and the prompt, review, replacement, pair-order, and protocol identities enter one digest manifest.

### Rationale

Writing exact prompts after supervised data protects dataset authors from known exam questions, but creates a risk that the test author selects convenient omissions. A predeclared matrix, closed replacement vocabulary, retained rejected candidates, independent review, and no-output rule make later selection visible and auditable.

### Implications

- A collision replaces the held-out candidate; it does not rewrite frozen supervision.
- Metadata and quota labels cannot be revised around observed system performance.
- Any post-freeze prompt change creates a new held-out version and repeats the collision audit.

## D-043 — Freeze evaluation protocol v1 at a proportionate research boundary

- **Date:** 2026-07-15
- **Status:** Adopted; version 1 frozen

### Decision

Freeze `chatgnt-evaluation-v1` after the final live verifier, semantic calibration, and 128-test suite passed with no unresolved experiment-validity blocker. Preserve one consolidated review summary and the final machine-readable evidence instead of six verbose intermediate review reports.

The protocol protects the compared treatments, population, scoring, denominators, analysis, leakage boundaries, and ordering of later work. It does not claim to defend repository evidence against a person who controls the local machine. Independent attestation would require a separate external trust system and is outside this portfolio experiment.

### Rationale

Adversarial review improved the experiment materially, including exposing a gap where a different five-example prompt could retain the selected version label. Once that treatment identity was fixed, further findings concerned local audit hardening rather than whether the research comparison would answer its question. Continuing indefinitely would consume effort without improving the experiment's practical validity.

### Implications

- Stage 3 is complete and Stage 4 may begin.
- Any normative evaluation change requires a new protocol version.
- The six review cycles are represented by one honest summary, not as six independent human audits.
- Exact held-out prompts remain prohibited until the supervised dataset is frozen.

## D-044 — Store semantic source records and isolate dataset splits by scenario

- **Date:** 2026-07-15
- **Status:** Adopted; Stage 4 design

### Decision

Dataset v1 will store one single-turn user prompt and one schema-valid assistant response object as its canonical source record, with stable example and scenario identities plus metadata and provenance. A deterministic preparation step will add the explicit empty system message, serialize the assistant object as canonical JSON, and apply the pinned Qwen chat template. Model-ready messages are derived artefacts rather than the authored source of truth.

The dataset will use frontier-model-assisted synthetic drafting with recorded provenance, automated structural checks, separate quality review, representative project-author inspection, and project-author responsibility for inclusion. Qwen outputs will not be used as target responses or as signals for choosing examples.

Authors may use the frozen behaviour, schema, safety, coverage, and exclusion rules. Five-shot examples, development scenarios and outputs, later held-out candidates, and target-model outputs may not be used as drafting seeds or templates.

Closely related examples will share a scenario ID when they have the same substantive user goal and situation or artefact, and their answer can be reused through surface substitutions. Split assignment operates on whole scenario groups, with uncertain cases conservatively kept together.

### Rationale

Separating semantic source content from Qwen rendering makes the dataset easier to validate, inspect, and reuse while keeping the exact training representation reproducible. Honest model-assistance provenance is more credible than presenting a large synthetic dataset as hand-written. Restricting existing examples protects the distinction between prompt engineering and fine-tuning, while scenario-group splits prevent validation from being inflated by paraphrases of training examples.

### Implications

- Step 5 must define a closed source-record and provenance schema plus deterministic renderer.
- Training records contain no five-shot context.
- Dataset quality requires review beyond schema validity.
- Split assignment occurs only after scenario grouping.
- Exact held-out prompts remain unavailable throughout Stage 4.

## D-045 — Target 200 accepted examples with a scenario-isolated 160/40 split

- **Date:** 2026-07-15
- **Status:** Adopted; Stage 4 design

### Decision

Dataset v1 will contain 200 accepted supervised examples. The target allocation is 160 training examples and 40 validation examples, with a fixed 40-example pilot selected only from training after split assignment. Authoring may create approximately 220–240 candidates to accommodate recorded rejection, but quality and coverage take precedence over filling the dataset with weak records.

Each of the five intent families initially targets 40 accepted examples: 32 training, eight validation, and eight members of the training-only pilot. Scenario groups are indivisible, so isolation takes precedence over exact split or family arithmetic and any achieved deviation is reported.

The validation split supports loss monitoring, overfitting diagnosis, qualitative transfer inspection, and proportionate configuration selection. It is not held-out evidence. The pilot tests the training pipeline and early learning behaviour; it is not an additional evaluation split and cannot be used to revise examples around Qwen outputs.

Dataset freeze will report prompt, response, and supervised token counts and distributions by split and intent family, plus sequence-length truncation. Example counts alone do not establish a balanced optimisation signal.

### Rationale

Two hundred examples provide enough room for varied demonstrations of the joint ChatG&T behaviour while remaining feasible to review. A 20% validation allocation gives 40 unseen scenarios—large enough to reveal substantial loss or behavioural differences without claiming precise performance estimates. Forty pilot examples provide eight per intent family and are sufficient to exercise the LoRA path cheaply.

Grouping before splitting prevents near-duplicate validation records from inflating apparent transfer. Token reporting prevents short and long examples from appearing balanced merely because their record counts match.

### Implications

- Candidate rejection history is retained; 220–240 is an authoring estimate, not a required count.
- Scenario groups never cross training and validation.
- The pilot is a subset of training and adds no new examples to the dataset total.
- Final held-out performance remains the job of the later frozen 60-prompt evaluation.
- The next decision is the cross-cutting dataset coverage blueprint.

## D-046 — Use cross-cutting coverage targets and audit response diversity

- **Date:** 2026-07-15
- **Status:** Adopted; Stage 4 design

### Decision

Each of the five intent families will contain 40 accepted examples. Within every family, the targets are 28 target-use, six breadth, and six robustness examples; 10 questions, 20 direct requests or commands, and 10 statements or fragments; 24 standard and 16 composed examples; and 12 examples with compatible explicit constraints. Across the full dataset this produces 140/30/30 coverage-slice counts, 50/100/50 input-form counts, 120/80 complexity counts, and 60 compatible-constraint examples.

All 30 robustness examples count as composed. Each family contains two format-pressure, two behaviour-pressure, and two serialization-pressure examples, yielding 10 of each role overall. Robustness pressure is separate from compatible constraints and does not satisfy that quota by itself.

The accepted set will cover at least 12 substantive domains overall and eight per intent family. No topic may exceed 10% of the dataset. Each intent family will cover at least six task subtypes, with no subtype exceeding 25% of that family. Frozen withheld domains remain prohibited.

Ingredient counts, method construction, title and unit patterns, metaphor and advice reuse, garnish style, tone, and lexical and semantic similarity will be audited for diversity rather than assigned dense quotas. Every permitted ingredient count must occur, no one count should occupy more than approximately one third of the set, and repeated distinctive templates or phrases require review.

Validation targets eight examples per family and collectively covers every input form, both complexity levels, all three coverage slices, compatible constraints, and all robustness roles. Scenario isolation remains the higher-priority rule and achieved deviations will be reported.

### Rationale

The model must learn several behaviours simultaneously: answer the underlying request, sustain a coherent cocktail metaphor, obey the JSON contract, and sometimes satisfy supplied constraints or withstand contrary instructions. Forty percent composed examples gives this joint behaviour meaningful supervision rather than teaching only the easiest output shape.

Cross-cutting targets make the intended population inspectable without pretending that every desirable stylistic variation can be independently balanced in a 200-example dataset. Concentration limits prevent narrow topic repetition, while an audit can detect templating and collapse without encouraging filler or unnatural writing solely to hit decorative quotas.

### Implications

- One record carries several coverage labels; quota totals are not added together.
- Step 5 must encode the closed coverage vocabulary and validate the hard counts and concentration limits.
- The authoring guide must define standard versus composed complexity, compatible constraints, coverage slices, robustness roles, and task-subtype assignment.
- Response diversity findings prompt review and justified revision, not automatic rejection based on arbitrary style counts.
- The next decision is the versioned dataset record schema and validator contract.

## D-047 — Separate canonical examples, workflow history, and training rendering

- **Date:** 2026-07-15
- **Status:** Adopted; Stage 4 design

### Decision

The canonical supervised record will contain `record_schema_version`, stable example and scenario IDs, the user prompt, a response object governed by the frozen ChatG&T response schema, coverage and retrieval metadata, a compact provenance summary, split assignment, and pilot membership. Unexpected fields are invalid.

Coverage metadata reuses the held-out protocol's intent, input-form, complexity, constraint, robustness, topic, user-goal, requested-task-or-artefact, scenario-summary, and important-constraints concepts. Dataset records add `coverage_slice` and `task_subtype`. Category fields use closed enums or versioned controlled registries; explanatory metadata remains non-empty text.

The provenance summary records the authoring batch, whether the initial draft was human or frontier-model produced, the initial model identity when applicable, whether a model revision was used, and whether a material human edit occurred. Detailed drafting, revision, review, acceptance, and rejection history is held in separate append-only workflow records keyed by example ID.

Split is null during authoring and becomes `train` or `validation` before freeze. Only training examples can be pilot members. Cross-field validators enforce the relationships among robustness, complexity, constraints, split, pilot status, and scenario grouping.

The deterministic training renderer reads only the user prompt and assistant response. It inserts an empty system message, preserves the user text, canonically serializes the response object, and then applies the pinned Qwen chat template. IDs, metadata, provenance, workflow history, split, and pilot status never enter the training conversation.

### Rationale

One readable semantic record is easier to author, validate, inspect, and reuse than a stored model-specific conversation. Reusing evaluation metadata gives later coverage and contamination tooling a common language. Separate workflow history preserves honest provenance without turning each training example into a project-management document.

Explicit cross-field redundancy makes human inspection easier while executable invariants prevent contradictory classifications. Separating rendering from source data also ensures that changes to model preparation are reproducible transformations rather than silent edits to authored supervision.

### Implications

- The response object must reference `chatgnt-response-v1` rather than duplicate its rules.
- Topic and task-subtype registries must be agreed before the record validator is complete.
- Step 7 closes review outcomes and workflow reason codes.
- Dataset-level validation must enforce ID uniqueness, scenario-isolated splits, quotas, concentration limits, and pilot eligibility beyond single-record JSON Schema checks.
- Frozen manifests bind both the semantic records and the renderer identity.
- Step 5 remains open until the schemas, registries, renderer, and validators are executable and tested.

## D-048 — Classify each example with one controlled topic and one family-specific task subtype

- **Date:** 2026-07-15
- **Status:** Adopted; Stage 4 design

### Decision

Every supervised example receives one primary topic from a 20-value version 1 registry: career and work; learning and study; technology and software; science and mathematics; history and society; money and budgeting; relationships and social life; personal growth and wellbeing; habits and productivity; home and everyday life; travel and places; food and cooking; arts and culture; writing and communication; business and marketing; community and events; consumer choices; nature and environment; leisure and entertainment; or fictional and imaginative worlds.

The primary topic is the context most necessary to answering the prompt, not every subject mentioned. There is no `other` value. A genuinely missing domain requires an explicit registry revision before dataset freeze. Wellbeing excludes medical diagnosis and treatment; money and budgeting excludes personalised investment, tax, and debt-crisis advice; and all frozen withheld-domain rules continue to apply inside broader topics.

Every record also receives one primary task subtype from an eight-value registry specific to its intent family:

- advice and decision support: action planning, option comparison, prioritisation, preparation, habit change, interpersonal navigation, problem diagnosis, and risk-and-tradeoff assessment;
- explanation and technical understanding: concept explanation, process explanation, cause and effect, comparison and distinction, worked example, troubleshooting, misconception correction, and technical how-to;
- low-stakes emotional support: validation and normalisation, perspective reframing, self-compassion, confidence support, manageable next steps, conversation preparation, boundary reflection, and supporting someone else;
- creative generation: name generation, slogan or tagline, character or mascot, story premise or plot, scene or opening, concept or campaign, event or experience, and idea generation; and
- short-form transformation: summarisation, clarity edit, tone shift, audience adaptation, notes to finished copy, shortening, message or reply drafting, and constraint-preserving rewrite.

Topic and task subtype are independent of each other and of intent family, coverage slice, complexity, and robustness role. The existing diversity gates remain: at least 12 topics overall, at least eight per family, no topic above 20 examples, at least six subtypes per family, and no subtype above 10 examples within its family. All eight subtypes are desirable when natural, but equal subtype allocation is not required.

### Rationale

A shared topic registry prevents spelling variants such as work, career, and employment from creating false diversity. A family-specific task registry captures the capability being demonstrated without confusing it with subject matter. Their independence allows the dataset to cross domains and operations instead of teaching simplistic associations between a topic and one kind of answer.

Broad categories keep counts meaningful at portfolio scale. Removing an `other` escape hatch makes gaps visible, while allowing explicit pre-freeze revisions avoids forcing genuinely new material into an inaccurate label. Concentration limits protect diversity without requiring an artificial full factorial or exactly balanced subtype counts.

### Implications

- The record schema must enforce the 20 topic values and the intent-family/task-subtype relationship.
- The authoring guide must include boundary examples for ambiguous family and subtype assignments.
- Coverage reports count one primary topic and one primary subtype per example.
- Robustness records retain their underlying task subtype rather than using the pressure mechanism as the task label.
- Step 5 now requires executable schemas, renderer, and validators rather than further record-shape decisions.

## D-049 — Implement the reviewed dataset-v1 contract without rewriting frozen Stage 3 evidence

- **Date:** 2026-07-15
- **Status:** Adopted and implemented; Stage 4 Step 5 complete

### Decision

Dataset v1 is governed by an executable configuration, a supervised-example schema, a workflow-event schema, and a conditional split-deviation schema. The implementation provides strict canonical JSONL loading, single-record and cross-field validation, append-only lifecycle validation, authoring and freeze modes, deterministic behavioural-order response rendering, canonical train/validation/pilot projection checks, hard coverage gates, and a read-only verification CLI.

Workflow events bind authored `content_sha256`, which excludes only split and pilot allocation. Complete allocated records and projections retain their own identities. This permits project-author acceptance before scenario-level split assignment without presenting allocation as a content revision. Freeze requires every candidate to reach exactly one terminal acceptance or rejection, and public training-message rendering requires a validated terminal acceptance chain.

Exact 160/40 and per-family allocation remains the default. A scenario-driven deviation requires a separate schema-valid record that binds the exact candidate and projection files, recomputed expected and achieved counts, affected scenario groups, rationale, and project-author approval. It cannot waive total accepted count, family totals, scenario isolation, pilot eligibility, content coverage, or any other dataset gate.

The focused dataset contract suite lives under `contract_tests/` rather than `tests/`. Stage 3 evidence intentionally binds every `tests/test_*.py` digest, so adding a new file to that historical identity set would invalidate the evidence. The separate suite extends verification while leaving the frozen 128-test command and evidence unchanged.

### Rationale

Executable contracts prevent inconsistent labels, invalid response objects, provenance gaps, allocation leakage, and renderer drift from becoming silent training inputs. Separating content and allocation identity reflects the real lifecycle: examples are written and reviewed before scenario groups are assigned to splits.

Historical evidence should remain evidence of what was verified at that time. Recapturing Stage 3 merely because Stage 4 adds tests would blur that boundary. An explicitly separate extension suite preserves both the old attestation and the new checks.

### Verification

- Contract CLI: pass, configuration/schema parity and built-in lifecycle confirmed.
- Focused dataset contract suite: 8/8 pass.
- Existing frozen suite: 128/128 pass.
- Python compilation, JSON parsing, and `git diff --check`: pass.
- No supervised or held-out examples were authored.
- No model was loaded, queried, or trained.

### Implications

- Candidate authoring must use the canonical source and workflow contracts rather than ad hoc JSON.
- Authoring mode permits an accepted candidate to remain unassigned; freeze mode requires every accepted candidate to be allocated.
- Stage 6 training may render only terminally accepted records from validated frozen projections.
- Step 6 must implement the scenario-group allocation procedure and attempt exact targets before any deviation is considered.
- Step 7 must turn the reason-code vocabulary into concrete authoring and review guidance before examples are drafted.

## D-050 — Allocate whole scenarios with deterministic coverage-aware optimisation

- **Date:** 2026-07-15
- **Status:** Adopted and implemented; Stage 4 Step 6 complete

### Decision

Terminally accepted, unallocated candidates will be grouped by exact scenario ID. Every scenario group must belong to one intent family and is assigned wholly to training or validation. A deterministic dynamic program enumerates attainable validation counts and coverage masks within each family, then combines the five family state sets.

The selected allocation first minimises the largest absolute deviation from eight validation examples in any family, then the sum of family deviations, then total deviation from 40, and finally a seeded SHA-256 priority signature. Validation must still contain all required input forms, complexity levels, coverage slices, a compatible constraint, and all robustness roles. Exact 8-per-family and 40-overall allocation therefore wins whenever it is feasible with full coverage.

The seed `20260715` and namespace `dataset-validation-allocation-v1` provide reproducible tie-breaking; they do not make the authored sample random. If indivisible scenario groups produce a non-exact allocation, the allocator records the achieved counts and marks that a separate project-author-approved split-deviation artefact is required. It never crosses scenarios or generates that approval itself.

After the split, a second deterministic procedure selects exactly eight training examples per family for the 40-example pilot. Greedy selection prioritises new input-form, complexity, slice, constraint, and robustness-role coverage, then new topics and task subtypes, then a separately namespaced hash tie-breaker. The pilot must remain training-only and pass its frozen representation checks.

### Rationale

Individual random splitting could place paraphrases of the same situation on both sides and inflate validation performance. Scenario-level assignment protects the intended generalisation boundary. Count-only assignment could still create a validation set missing the behaviours it is supposed to monitor, so coverage is part of feasibility rather than a later cosmetic audit.

An explicit optimisation order makes every tie and trade-off reproducible. The hash seed prevents file order or author preference from silently choosing among equally valid allocations without implying population sampling. A separate deviation approval keeps an algorithmic result distinct from a project decision to accept that result.

### Verification

- Split-configuration and report-schema check: pass.
- Additive dataset contract and allocation suite: 14/14 pass.
- Existing frozen suite: 128/128 pass.
- Exact, grouped, cross-family rejection, non-exact, pilot, dry-run, and atomic-write paths exercised with synthetic records.
- Compilation, JSON parsing, and `git diff --check`: pass.
- No real dataset record or model output was created.

### Implications

- Scenario IDs must be final and family-consistent before allocation.
- All candidates must reach terminal disposition before the allocator runs.
- Inputs must be unallocated; the pure operation returns allocated copies and never mutates source objects.
- Exact allocation needs no exception record; non-exact allocation cannot freeze until separately approved and bound.
- Step 7 can author examples against a known, testable split and pilot procedure rather than deciding allocation after seeing model behaviour.

## D-051 — Use non-compensatory pass, revise, or reject judgments for teaching-target quality

- **Date:** 2026-07-15
- **Status:** Adopted; Stage 4 Step 7 complete

### Decision

Dataset candidates are reviewed on the same three conceptual dimensions used by the evaluation—underlying-answer quality, metaphorical coherence, and recipe-style execution—but with a stricter teaching-target question. Each dimension receives `pass`, `revise`, or `reject`, not a numeric model-output score.

All three dimensions must pass. At least one `revise` with no rejection maps to workflow outcome `revision_requested`; any `reject` maps to `rejection_recommended`. Scores cannot compensate across dimensions, and structural validity remains a separate automated eligibility gate rather than a fourth qualitative dimension.

The frozen authoring guide provides boundary rules, calibration fragments, complete reason-code guidance, and a stable review-note shape. It begins with a 10-candidate calibration batch, then permits batches of at most 20. Drafting and review use separate contexts, material revisions require a fresh review, two material revision cycles are the default maximum, and only the project author may record terminal acceptance.

### Rationale

Evaluation asks whether a generated response is acceptable or strong; dataset review asks whether an example is suitable to teach. Reusing the three-point evaluation scale would invite merely acceptable targets into supervision and create false precision about editorial judgments. A categorical repair decision directly determines the next workflow action.

Separating hard gates, per-example quality, and corpus-level diversity avoids both compensation and duplication. Valid JSON cannot rescue poor advice, an excellent metaphor cannot rescue an incomplete artefact, and one ordinary construction need not fail simply because repetition is visible only across a batch.

### Implications

- Candidate authoring starts with a 10-record calibration batch covering all five intent families.
- Calibration fragments in the guide are not eligible dataset records and enter later duplication checks.
- Coverage gaps determine what to draft next but never lower the acceptance bar.
- A passing model review does not itself accept an example; terminal inclusion remains attributable to the project author.
- Step 8 may now begin without reopening the quality dimensions or workflow outcomes.

## D-052 — Treat garnish as an optional recipe flourish, not an overflow field

- **Date:** 2026-07-15
- **Status:** Adopted from calibration evidence; authoring rubric amended to version 1.1

### Decision

A dataset garnish must be a concise optional metaphorical flourish or serving accent. It should read naturally after “Garnish with…” or “Serve with…”, reinforce the particular recipe, and remain removable without making the substantive answer incomplete.

A garnish may not introduce an essential instruction, warning, correction, decision rule, requested artefact, factual explanation, or other answer content. Those belong in ingredients or method. Violations receive `recipe_execution_weak` and cannot pass teaching-target review merely because the extra content is relevant or useful.

### Rationale

Every garnish in the first 10-candidate calibration draft used the field for an additional tip, warning, explanation, choice, catchphrase, or posting instruction. The independent reviewer passed this pattern because version 1 described a garnish broadly as a relevant final detail. Project-author inspection correctly identified that relevance did not make those sentences garnishes.

This is the purpose of a calibration batch: expose a shared interpretation failure before scaling it across the dataset. Tightening the authoring rubric is more honest than individually polishing ten symptoms while leaving the rule that produced them unchanged.

### Experimental boundary

The Stage 3 evaluation protocol and `docs/behavioural-contract.md` remain byte-for-byte unchanged because they are part of the frozen evaluation identity. The existing recipe-style evaluation question already asks whether the response sustains a natural cocktail-recipe voice. Version 1.1 is a stricter teaching-target interpretation for Stage 4, not a silent alteration of the frozen scoring protocol.

### Implications

- The original ten garnishes are recorded as project-author revision requests.
- All ten candidate snapshots require a truthful revision event and fresh review before acceptance.
- Later reviewers must apply the removal test and reject method-like garnish overflow.
- No calibration candidate is accepted solely on the earlier model review.

## D-053 — Apply a holistic bartender test to teaching targets

- **Date:** 2026-07-15
- **Status:** Adopted from calibration evidence; authoring rubric amended to version 1.2

### Decision

A candidate passes recipe-style execution only when, without relying on the JSON field names, its title, measurements, ingredients, preparation language, and garnish still unmistakably sound like a bartender presenting a metaphorical cocktail recipe.

Cocktail-like measures should dominate, with real units retained when they carry useful task meaning. Quantities communicate relative emphasis or composition rather than pretend scoring. Preparation language must map naturally to the substantive reasoning across the method; isolated bar verbs cannot rescue an ordinary checklist. No title or garnish may carry the complete stylistic burden.

### Rationale

After the garnish correction, direct review of candidates 001 and 002 revealed a broader failure: both were useful and structurally recipe-shaped, but their bodies still read as household and consumer checklists. Component-by-component review had rewarded valid fields while missing the overall experience.

The bartender test turns that gestalt into an operational anchor without adding another scored dimension. It preserves the existing three-dimension rubric while making recipe-style execution harder to satisfy through labels alone.

### Calibration exception and stopping rule

The 10-candidate calibration batch receives one bounded whole-response rewrite under version 1.2. For candidates already at the ordinary two-revision limit, this is a documented exception caused by a project-author amendment to the shared quality standard, not another autonomous polishing cycle. No candidate receives a further content revision: a remaining failure after direct inspection is rejected and replaced.

### Implications

- Candidates 001 and 002 use the project-author-approved conversation rewrites.
- Candidates 003–010 receive one whole-response rewrite against the same standard.
- Every rewritten snapshot remains unresolved until direct project-author review.
- Production batches begin under version 1.2 rather than inheriting the calibration failure.

## D-054 — Freeze the first 20-slot production matrix before drafting

- **Date:** 2026-07-16
- **Status:** Project-author approved

### Decision

Freeze `dataset-v1-batch-02` with four planned candidates per intent family and 20 distinct scenario identities before authoring any exact prompt or ideal response. The batch contains 15 target-use, three breadth, and two robustness slots; four questions, nine direct requests, and seven statements or fragments; 14 standard and six composed slots; six compatible-constraint slots; and one behaviour-pressure plus one serialization-pressure slot.

The frozen matrix identity is `3e75545490a265e1f4447d579bfe55464e431710d17d44401e0579052f765c09`. Exact drafting may fill these slots but may not silently change their IDs, scenarios, metadata, or coverage roles.

### Rationale

Calibration left different slice combinations in each family. Adding the proposed slots brings the cumulative 30-example corpus to four target-use, one breadth, and one robustness example in every family. Freezing scenario intent before wording reduces the opportunity to relabel convenient drafts after seeing their quality and keeps coverage pressure separate from acceptance judgment.

### Workflow boundary

A fresh drafting context receives the frozen matrix and authoring standard but does not review or accept its own work. It stops after creating 20 candidate snapshots, corresponding `draft_created` events, and structural-validation evidence. Qualitative review occurs in a separate context, and only the project author may record terminal acceptance.

## D-055 — Treat plausible pours, not unit variety, as the measurement standard

- **Date:** 2026-07-16
- **Status:** Project-author approved; authoring rubric amended to version 1.3

### Decision

Keep `ml` as ChatG&T's expected default measurement. Judge quantities by whether they resemble a plausible bartender composition: a base pour, smaller modifiers, and accents expressed naturally through smaller ml amounts, dashes, drops, splashes, twists, or a substantively useful real unit.

Adopt the Batch 02 review's systematic `response_templating` finding with a narrowed interpretation. Repeated use of `ml` and shared cocktail vocabulary are not failures. The defect is repeated score-like amount sequences, routine normalisation of abstract ingredients to an exact total, and generic preparation scaffolds across unrelated answers.

### Rationale

Cocktails are normally made with measured pours; removing or artificially rationing `ml` would make the teaching targets less authentic. The original ChatG&T example already establishes the desired grammar: a substantial base, smaller supporting pours, and a dash-like accent. Batch 02's first drafts instead made many unrelated answers resemble allocations from the same 100-point template.

The correction should therefore increase compositional authenticity without turning unit diversity into another quota. Recipe construction follows the answer's hierarchy and method, not an arbitrary demand that every record look different.

### Bounded correction

All 20 Batch 02 candidates receive one coordinated material revision because the review finding belongs to the collection. Prompts, scenarios, metadata, substantive goals, and sound underlying answers remain fixed. A frozen per-candidate construction overlay guides one fresh revision pass, followed by one separate post-revision review. That review is the stopping point for whole-batch correction; no further batch-wide polishing loop is authorised.

### Frozen identities

- Authoring guide v1.3: `04a3a75604a2ef77e41a210a20fcb2b054cf07703104954ea198fdab7eb7f2b1`
- Machine-readable rubric v1.3: `4d8df1ee6db926cc4d4e28a55f8bffbe06aa81eac2d1cc959a554364e4a65201`
- Batch 02 revision overlay: `49e5606c11bd1ac333c8ee92afe2d86de5e2caba13a358768aac20c83b3a293b`

## D-056 — Separate qualitative judgment from deterministic terminal acceptance

- **Date:** 2026-07-16
- **Status:** Adopted and implemented; supersedes only the human-only acceptance clauses in D-051 and D-054

### Decision

Retain independent qualitative review as the inclusion judgment: a current review must attest that underlying-answer quality, metaphorical coherence, and recipe-style execution all pass. Replace mandatory per-example project-author acceptance with deterministic terminalisation by `chatgnt-dataset-terminalizer-v1`.

The workflow schema permits `accepted` events from a human or `automated_validator`, but not from a frontier model. Automated acceptance must immediately follow a passing review of the same content digest, use a fixed code-owned identity and null model identity, and have an empty reason-code list. The review actor must differ from the latest actor that drafted or materially revised the current content.

The finalizer validates the complete input collection, fails if any unresolved candidate lacks a current pass, constructs all acceptance events in memory, validates the proposed post-state, checks that the event file has not changed since reading, and atomically replaces only that canonical JSONL file. A repeated run makes no additions.

### Rationale

Batch 02 exposed that human-only acceptance duplicated the already-recorded qualitative decision and would force the project author to approve hundreds of examples individually. Labelling model actions as human would corrupt provenance; allowing the reviewing model to accept directly would blur judgment and bookkeeping. Deterministic terminalisation keeps the substantive model review visible while making the administrative transition reproducible and scalable.

Actor-identity separation is a mechanically checkable proxy, not cryptographic proof that two contexts are epistemically independent. The production workflow therefore also uses fresh reviewer contexts and retains every draft, revision, and review event. Human involvement remains available for genuine changes to the research question or scope, but ordinary example acceptance no longer depends on it.

### Implications

- Existing human acceptance events remain valid historical evidence.
- A `pass` outcome semantically attests that all three frozen qualitative dimensions pass; the validator does not independently judge prose quality.
- Frontier-model authors and revisers cannot review their own current content for automated acceptance.
- Batches fail closed when even one unresolved candidate lacks a passing terminal review.
- Dataset rendering and split assignment still require a validated terminal `accepted` event.

## D-057 — Produce the remaining corpus in four bounded concurrent waves

- **Date:** 2026-07-16
- **Status:** Adopted for Stage 4 production scaling

### Decision

Produce Batches 04–11 in four waves: 04/05, 06/07, 08/09, and 10/11. Batches within a wave may author and review concurrently because they own disjoint example IDs, directories, and reserved workflow-event blocks. The master agent freezes both matrices, waits for both terminal dispositions, audits their combined effect on the accepted corpus, and only then opens the next wave.

The versioned production schedule preallocates the exact remaining per-family slice, input-form, complexity, compatible-constraint, and robustness-role counts needed to reach the 200-example contract from the 50 accepted examples already closed. Full batches contain four candidates per family; the final batch contains two. Reserved 100-ID event blocks remove cross-batch coordination over append order while retaining globally unique IDs.

### Rationale

Independent batch files make drafting and review genuinely parallelisable, but unlimited fan-out would sacrifice adaptive coverage and amplify mistakes. Wave barriers preserve the research benefit of closed-batch audits while using the available agent slots efficiently. Predeclared quota arithmetic prevents concurrent planners from both filling the same apparent gap.

### Guardrails

- No two live agents may edit the same batch files.
- Drafting and review remain separate contexts within each batch.
- Each batch retains one consolidated repair pass and one terminal review.
- Deterministic acceptance occurs only after every unresolved candidate in that batch has an independent pass.
- A wave-wide audit may alter later scenario choices but not the frozen numerical schedule unless a recorded rejection makes exact completion impossible.
- Exact held-out prompts, Qwen outputs, training, and split allocation remain unavailable throughout production.

## D-058 — Freeze the Stage 4 duplication, contamination, and exclusions audit before running it

- **Date:** 2026-07-16
- **Status:** Superseded by D-059 after generation 001 exposed a disproportionate review workload

### Decision

Freeze `chatgnt-dataset-contamination-audit-v1` before inspecting production similarity results. Reuse the Stage 3 normalization, RapidFuzz, pinned MiniLM, top-five retrieval, and three-question semantic-collision rule. The audit covers internal prompt, scenario, response, component, metadata, and structural diversity; worked examples; development prompts and outputs; evaluation calibration text; target-model diagnostic material; provenance; and the three withheld domains.

Automation generates an immutable candidate-pair workload but does not decide semantic equivalence. Every de-duplicated top-five lexical, semantic, and nonzero metadata neighbour, plus all exact, threshold, structural, component, phrase, and withheld-domain flags, receives one attributable complete-text disposition. Thresholds may add review pairs but may not remove the frozen top-five workload.

The machine build and finalization use separate atomic, no-overwrite generations. Human- or agent-authored dispositions and attestations are inputs between them. Exact held-out prompts remain unavailable, and the audit neither assigns splits nor queries Qwen.

### Failure boundary

The audit does not invent an active-set overlay or supersession rule. Any automatic failure, unresolved judgment, or `revise_or_replace` disposition fails Step 10 closed. Candidate replacement requires a separately specified and reviewed dataset-contract amendment that downstream authoring, split, rendering, and freeze validators understand, followed by a new immutable complete audit generation.

### Frozen evidence

- Audit specification SHA-256: `0e87888a02caba963ce37f5d39c8e71929b2f7e89cbab6ef03b85692f1b4f820`
- Adversarial review SHA-256: `cfe0dbcc49e04da09051e0834a207fde92c7acaa869d6de285ebf91a57ab5eb7`

## D-059 — Replace component-level audit machinery with a bounded record-level audit

- **Date:** 2026-07-16
- **Status:** Adopted and executed; Step 10 passed after amendment 001

### Decision

Protect the fairness of the prompt-engineering versus fine-tuning comparison with the smallest audit that can change a relevant decision. One local script loads the 200 terminally accepted examples, the 20 spent development prompts, and the five System B worked examples. It performs normalized exact checks, searches for the three withheld domains, reports simple response-template frequencies, and uses the pinned MiniLM encoder only to retrieve:

- the 50 closest internal complete-scenario pairs;
- the five closest supervised scenarios for each of the 25 prior prompts; and
- the five closest supervised responses for each of the five worked responses.

Similarity retrieves complete records for review and never decides contamination. The audit does not compare every ingredient, method step, garnish, metadata field, output collection, or synthetic view independently. Its durable outputs are one JSON findings file and one readable Markdown report.

### Result

All exact and withheld-domain checks passed. Review of the initial bounded 200 semantic pairs identified seven supervised examples requiring replacement: `dataset-v1-003`, `dataset-v1-005`, `dataset-v1-014`, `dataset-v1-041`, `dataset-v1-118`, `dataset-v1-158`, and `dataset-v1-161`. Amendment 001 superseded them without rewriting their history. The unchanged audit then passed the 200-example active v1.1 set.

## D-060 — Represent the seven audited replacements as a narrow supersession overlay

- **Date:** 2026-07-16
- **Status:** Adopted, applied, and verified

### Decision

Retain every original candidate and workflow event unchanged. Store seven new candidates and their own event chains under amendment 001, and use one closed manifest to map each superseded example ID to one replacement ID. Define `chatgnt-dataset-v1.1` as the active 200-example view produced by excluding the seven superseded records and including their seven terminally accepted replacements.

Every mapping must preserve intent family, coverage slice, input form, complexity, constraint status, robustness role, and task subtype. The executable audit verifies the base and replacement identities, mapping completeness, lifecycle validity, preserved quota axes, and the resulting 200-accepted-record population before doing any similarity work.

### Rationale

Silently editing accepted records would invalidate their content-bound acceptance events. Adding a general supersession state to the frozen workflow schema would be disproportionate for seven pre-freeze repairs. A narrow, explicit overlay preserves both historical truth and a simple downstream active set.

## D-061 — Preserve ingredient-count diversity and accept the first exact deterministic split

- **Date:** 2026-07-16
- **Status:** Adopted, applied, and verified

### Decision

Do not weaken the frozen requirement that ingredient counts three through eight are represented. Amendment 002 restores the lost seven- and eight-ingredient slots while leaving the two replacement scenarios and quota-bearing metadata unchanged. Rerun the same bounded audit once, then feed the passing active v1.2 set to the already frozen split algorithm.

Accept the first allocation that passes every existing gate. Require exactly 160 training, 40 validation, and 40 training-only pilot examples; 32/8/8 of each intent family; complete required validation and pilot coverage; scenario isolation; canonical projections; a passing frozen-dataset validator; and a manifest binding the contract, split configuration, both amendments, passing audit, and every output file.

### Result

The allocation was exact and required no exception. A byte-for-byte reproduction in a separate temporary directory matched the frozen bundle.

## D-062 — Pass the Stage 4 readiness review and preserve System B unchanged

- **Date:** 2026-07-16
- **Status:** Adopted; Stage 4 complete

### Decision

Accept frozen dataset v1.2 for the portfolio experiment. Its 160/40 training-validation split, 40-example training-only pilot, coverage, contamination result, token balance, provenance, identities, and byte-for-byte reproducibility satisfy the Stage 4 exit condition.

Pass all five System B worked examples against the final `chatgnt-dataset-authoring-v1.3` standard. Each substantive answer is complete; each metaphor is coherent; and each response remains unmistakably cocktail-like across title, measures, ingredients, method, and optional garnish. Preserve `five-shot-v3` unchanged because the planned checkpoint found no non-pass dimension and no model result was used to influence the judgment.

### Boundary

This authorises held-out prompt authoring under the frozen Stage 5 protocol. It does not author held-out prompts, train Qwen, select an adapter, or generate evaluation responses.

## D-063 — Use a proportionate held-out authoring and freeze procedure

- **Date:** 2026-07-16
- **Status:** Adopted, applied, and verified; Stage 5 complete

### Decision

Replace the originally specified per-candidate ledger, dual-review, and semantic-evidence package with the smallest procedure that protects the experiment's held-out boundary. Author all 60 prompts without model answers, validate the frozen population matrix mechanically, compare complete prompt text against prohibited project prompts and earlier held-out prompts, review the complete set once for clarity and scoring feasibility, and freeze the first complete set that passes.

A prompt is replaced only if it is unclear, unscorable, duplicated, assigned to the wrong slot, or genuinely overlaps prohibited material. No prompt is revised because a model handles it poorly. The frozen set is hash-bound in one manifest and must not be opened for prompt development, training, validation, or adapter selection.

### Result

Held-out v1 contains exactly 60 schema-valid prompts and no model responses. Every frozen quota passes. A prompt-level comparison against 231 worked-example, development, evaluation-calibration, training, and validation prompts produced no exact or threshold flags, so no replacement cycle was needed. Dataset v1.2 and System B remain unchanged.

### Limitation

The overlap check is an inspectable lexical retrieval control, not proof of semantic independence, and the complete-set judgment was performed by the project agent rather than an independent human panel. Those limitations are proportionate to this portfolio experiment and are recorded rather than disguised with a larger ceremonial evidence package.

## D-064 — Track the diagnostic LoRA adapter as the clean-clone fixture

- **Date:** 2026-07-16
- **Status:** Adopted and verified; Stage 6 preflight step 1 complete

### Decision

Include the existing 4.2 MB diagnostic LoRA adapter in the repository. The adapter-loading unit test already names this artefact, and the same adapter is useful for CUDA smoke testing. Tracking it makes a clean clone portable without changing the hash-pinned Stage 3 test suite or weakening adapter identity checks.

### Result

The three adapter-loading tests and all 128 repository tests pass. The diagnostic weights have SHA-256 `4e274ac2fa442cc688cace097a887e9cc309a78e18f0091b62119e3933bd01cb`. This fixture is diagnostic evidence only; it is not a trained ChatG&T candidate and cannot be used as the Stage 6 selected adapter.

## D-065 — Freeze one bounded 40-example pilot configuration

- **Date:** 2026-07-16
- **Status:** Adopted, executed, and verified

### Decision

Use one BF16 LoRA pilot rather than a pilot hyperparameter search. Train rank-8, alpha-16 `q_proj`/`v_proj` adapters with dropout 0.05, AdamW at `2e-4`, micro-batches of two, four-way gradient accumulation, and three epochs over the frozen 40-example training-only pilot. This yields an effective batch size of eight and exactly 15 optimiser updates. Use the complete 40-example validation split for loss measurement only, never gradient updates.

The runner masks every prompt and padding token, forbids truncation beyond 512 tokens, saves one adapter checkpoint per epoch, proves the frozen base remains unchanged, and verifies the final adapter through exact clean reload. It records baseline and per-epoch validation loss but does not use a loss threshold as a proxy for response quality.

### Boundary

This run proves mechanics and produces observations used to design the small final candidate comparison. It neither selects a final adapter nor accesses held-out prompts. Any failed identity or runtime gate is repaired locally under a new committed version and run ID; configuration is not edited on the Pod.

### Result

Run `pilot-training-v1-20260717-run01` passed every frozen gate on an NVIDIA GeForce RTX 3090. Baseline validation loss was 3.0364 and then fell monotonically to 2.9436, 2.8331, and 2.7339 after epochs one through three. Mean training loss also fell from 2.9995 to 2.7596. The 15 updates had finite losses and gradient norms, the frozen base remained unchanged, the three checkpoints were saved, and the final provenance-bound adapter reloaded with an exact logit match. Peak reserved VRAM was 42.1%.

The result establishes a working pipeline and an encouraging early learning signal, not acceptable ChatG&T behaviour or a selected final configuration. Those questions remain subject to permitted behavioural inspection and later candidate comparison. The complete evidence and interpretation are recorded in `docs/stage-6/pilot-training-results.md`.

## D-066 — Use one bounded A-versus-C pilot behavioural inspection

- **Date:** 2026-07-17
- **Status:** Adopted and prepared; awaiting GPU execution

### Decision

Compare the untouched base model and final three-epoch pilot adapter in one paired harness run. Both systems use the empty minimal prompt and the frozen generation profile. The population contains ten validation prompts: one ordinary and one challenging prompt from each intent family. The shared run seed `20260715` produces paired per-prompt generation seeds and exactly 20 responses.

Apply the existing hard structural validator, then blind system identity while scoring every schema-valid response on underlying-answer quality, metaphorical coherence, and recipe-style execution. Reveal identities only for the diagnostic comparison and failure-pattern summary.

### Rationale and boundary

This is the smallest inspection that can test whether the pilot's improving validation loss corresponds to visible ChatG&T behaviour across every intent family. Epoch-one and epoch-two adapters are excluded initially because the loss curve already records their progression and only the final adapter has complete formal provenance. They may be revisited only if the final outputs create a specific regression question.

The inspection uses no held-out prompt and cannot establish final performance or select the final system. Its outputs may inform the predeclared full-training candidate configurations, but they will not be used to rewrite supervised examples, System B, or the frozen evaluation rules. The population and operational procedure are recorded in `docs/stage-6/pilot-behavioural-inspection.md`.
