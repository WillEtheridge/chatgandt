# Learnings Log

This log captures the concepts and practical lessons learned while developing ChatG&T.

## 2026-07-13 — What makes a good research question?

A good research question should be:

- **Falsifiable:** The result could genuinely be “no.”
- **Measurable:** Every important term can be translated into an evaluation.
- **Comparative:** There is a meaningful baseline.
- **Scoped:** It doesn’t claim more than one experiment can establish.
- **Neutral:** It doesn’t assume fine-tuning will succeed.
- **Generalisation-focused:** Success is measured on unseen prompts, not training examples.

## 2026-07-13 — Why use a two-by-two experimental design?

A comparison can be useful without identifying what caused the difference. Comparing a prompted base model directly with an unprompted fine-tuned model changes two variables at once: the model and the prompt. This is a **confounded comparison**.

A two-by-two design tests every combination of the two interventions:

| | No ChatG&T prompt | Detailed ChatG&T prompt |
| --- | --- | --- |
| Base model | A | B |
| Fine-tuned model | C | D |

This design lets us examine:

- the effect of prompting;
- the effect of fine-tuning;
- whether prompting and fine-tuning interact; and
- the practical comparison between prompt engineering alone and fine-tuning alone.

The wider lesson is that when multiple things change between two systems, their performance difference cannot safely be attributed to just one of those changes. Adding appropriate control conditions makes causal explanations more credible.

## 2026-07-14 — What is an evaluation population?

An **evaluation population** is the conceptual universe of inputs to which we want the experiment’s conclusions to apply. It is different from the **evaluation sample** or **test set**, which is the finite collection of prompts actually used to estimate performance on that population.

For example, ChatG&T’s population might consist of English-language, single-turn, low-stakes prompts asking for advice, explanation, decision support, emotional support, transformation, or creative generation. A held-out set of prompts selected from that population would be the evaluation sample.

A good evaluation population should:

- match the system’s intended use;
- have clear inclusion and exclusion boundaries;
- cover different user intents and input forms, not only different topics;
- contain meaningful variation in familiarity and difficulty;
- include awkward and adversarial cases rather than only favourable examples;
- focus primarily on tasks the base model can reasonably perform, so missing knowledge is not confused with failure to learn the target behaviour;
- be divided into useful groups so that failures can be diagnosed; and
- remain small and specific enough that the resulting claims are honest.

Useful dimensions include:

- **Topic:** What is the prompt about?
- **Intent:** Is the user asking for an explanation, advice, comparison, transformation, support, or creative output?
- **Input form:** Is it a question, request, command, statement, or fragment?
- **Familiarity:** Is it in-domain, cross-domain, or an unusual combination?
- **Difficulty:** Is it straightforward, ambiguous, or multi-constraint?
- **Robustness:** Is it ordinary or attempting to break the target behaviour?

“Unseen” means more than using different wording. A held-out prompt should not be an exact match, close paraphrase, or substantially duplicated scenario from the training or validation data. It must not be used to refine the model, detailed prompt, or evaluation design.

The practical process is to:

1. define the target-population statement;
2. choose the important dimensions and groups;
3. assign evaluation quotas;
4. write and review prompts for those quotas;
5. check for semantic overlap with development data;
6. freeze and version the held-out set before full training; and
7. report group-level results alongside any overall score.

Public submissions are self-selected and uncontrolled. They can provide useful supplementary evidence, but they do not replace a curated held-out evaluation.

## 2026-07-14 — How should a multi-objective generative system be evaluated?

Training and validation loss are useful diagnostics, but they do not establish whether a model performs the intended behaviour on unseen prompts. Output evaluation should use several layers because different measurements answer different questions:

1. **Execution:** Did generation complete, and how long and large was the response?
2. **Structure:** Is the raw output valid JSON that conforms to the required schema?
3. **Quality:** Is the response useful, metaphorically coherent, and stylistically consistent?
4. **Comparison:** Which system does a blinded evaluator prefer?

Important qualities should be reported separately rather than hidden inside one average. An excellent style score must not compensate for a useless answer.

When the research question requires several qualities simultaneously, use a **joint pass**. For ChatG&T, this could require schema-valid JSON and a minimum acceptable score on every qualitative dimension.

Pairwise evaluation can answer two distinct questions:

- **Conditional preference:** Which response is better when both systems produce structurally valid output?
- **End-to-end performance:** Which system produces a successful experience more reliably, including structural failures?

Results should be broken down by evaluation slice because an overall result can conceal cross-domain or robustness failures. Metrics, analysis rules, and any thresholds used to support a claim should be chosen before inspecting the final fine-tuned results so that the interpretation is not changed to suit the outcome.

Finally, model results and project success are different. A system comparison need not be reduced to one binary winner. The research project can succeed with a negative, mixed, or inconclusive model result if the comparison is fair, reproducible, and honestly reported.

## 2026-07-14 — Why should the baseline reflect a realistic engineering alternative?

A weak baseline creates a **strawman comparison**: the new technique appears successful because the alternative was not developed competently. A fair baseline should reflect what an engineer would realistically build if the technique under investigation were unavailable.

For ChatG&T, the prompt-engineered baseline will contain detailed instructions, the schema, and five high-quality examples because that is the prompt the project author would ordinarily expect to produce good results. Its development and failures must be documented, and it must be frozen before held-out evaluation.

A strong baseline can change what counts as an interesting result. Fine-tuning may fail to improve response quality while still reducing recurring prompt tokens, context usage, or latency. Conversely, fewer tokens do not guarantee lower latency because adapter execution, caching, output length, and the inference implementation also matter. Quality and efficiency therefore need separate measurements.

## 2026-07-14 — When does a measured trade-off require an acceptance threshold?

A **response-level threshold** is necessary when each response must be classified as passing or failing. ChatG&T’s joint pass requires schema validity and an acceptable score on every qualitative dimension.

A **system-level acceptance threshold** is only necessary when the experiment must decide which system should be deployed. A descriptive comparison can instead report the observed differences in quality, prompt tokens, and latency with uncertainty.

Whether a quality reduction is worth an efficiency improvement depends on real deployment context: traffic, cost, latency requirements, and tolerance for errors. When that context is hypothetical, declaring a universal acceptable trade-off introduces an arbitrary value judgment. The experiment should measure the trade-off accurately and allow its implications to be considered in context.

## 2026-07-14 — How do limitations differ from confounding factors?

A **confounding factor** offers an alternative explanation for an observed difference. A **bias** systematically influences data or judgment. A **source of uncertainty** makes an estimate noisy. A **limitation** restricts how far the result can generalise.

For example, testing only one base model is an external-validity limitation; it does not by itself invalidate the result for that model. Using different generation temperatures between two systems would be a confounder because temperature could explain the observed difference.

The goal is not to claim that an experiment has no limitations. A credible process decides whether each important risk should be:

- **controlled**, by changing the experimental design;
- **measured**, so its effect or uncertainty is visible; or
- **disclosed**, when it cannot reasonably be removed.

The final claim must remain inside the evidence boundary. For ChatG&T, the experiment can describe what happened for the documented model, dataset, prompt, inference environment, and evaluation population. It cannot establish that fine-tuning is universally better or worse than prompting.

## 2026-07-14 — Why separate training and hosting constraints?

Training compute and deployment compute have different cost shapes. Fine-tuning is a bounded experimental activity, so a rented GPU can be inexpensive if it is used briefly and stopped promptly. Hosting is a recurring commitment: even a modest hourly rate becomes expensive when a model is kept warm continuously.

Infrastructure planning should therefore use separate constraints for:

- **one-off experimentation**, including training runs and failed attempts; and
- **ongoing serving**, including idle time, cold starts, traffic, and storage.

The cheapest suitable environment may differ at each stage. A hybrid design can use local hardware for development and evaluation, rented accelerators for short training runs, and free or scale-to-zero infrastructure for a low-traffic demonstration. The final deployment choice should follow measurements of memory, latency, cold-start behaviour, and likely usage rather than training hardware alone.

## 2026-07-14 — Why separate eligibility gates from selection preferences?

A model-selection criterion can play two different roles:

- An **eligibility gate** identifies a requirement whose failure makes the candidate unusable, such as incompatible licensing or an unsupported training workflow.
- A **selection preference** helps distinguish between candidates that are all viable, such as better documentation, lower latency, or stronger JSON adherence.

Combining both types immediately into a weighted score can hide fatal weaknesses: excellent benchmark performance might numerically compensate for terms that prevent public deployment. Apply hard gates first, then compare the surviving candidates while keeping important trade-offs visible.

Criteria should also be defined before inspecting favoured candidates. Otherwise the selection process can quietly change to justify an attractive model after the fact. Candidate testing should establish basic suitability using disposable development inputs, not optimise against the held-out evaluation set.

## 2026-07-14 — Why isn't the newest model automatically the best candidate?

Model selection is an engineering decision, not a recency contest. A newer model may improve general benchmarks while also introducing a new architecture, unstable dependencies, additional modalities, special output modes, or serving requirements that are irrelevant to the intended task.

For a learning project, ecosystem maturity affects both reproducibility and what the work teaches. A well-supported text model can provide a cleaner LoRA experiment than a newer multimodal model that requires development versions of several libraries. This is not a claim that the older model is more capable; it is a claim that capability is only one part of suitability.

Desk research should produce a shortlist rather than a winner. Model-card claims, general benchmarks, and advertised context lengths establish plausible candidates, but they do not demonstrate task-specific JSON reliability, memory use, latency, or adapter compatibility in the project environment. Those require comparable executable feasibility checks.

## 2026-07-14 — Why is JSON-shaped output not necessarily valid JSON?

A response can contain a perfectly formed JSON object and still fail raw JSON parsing. Common causes include Markdown fences, introductory prose, trailing commentary, multiple objects, or truncated generation.

In the Ollama pre-flight, Qwen2.5 produced the requested fields and values for three structured prompts, but wrapped every object in a Markdown code fence—even when explicitly told not to use Markdown. All three are semantic format successes but strict raw-JSON failures.

This distinction explains why ChatG&T evaluates the unmodified model output before any repair or extraction. Stripping fences would measure the application's ability to recover JSON, not the model's ability to generate schema-valid JSON. Similarly, constrained decoding can be valuable in a product but would answer a different experimental question by preventing some structural failures rather than observing them.

## 2026-07-14 — Why are runtime defaults part of the experimental system?

A model name alone does not fully specify a generation system. A runtime can silently add a system message, choose a chat template, set stop sequences, change the context allocation, quantise weights, or apply default sampling parameters. Each can alter both output behaviour and measured efficiency.

The Ollama Qwen2.5 package injected a helpful-assistant identity message even though the API request contained only a user message. That is reasonable product behaviour, but it means the resulting prompt was not actually user-only.

Formal model comparisons should therefore capture:

- the structured message array;
- the fully rendered prompt sent to the model;
- the tokenizer and chat template;
- generation and stopping parameters; and
- any defaults contributed by the runtime.

For ChatG&T, inspection of Qwen's official template revealed that a user-only message array still triggers a default vendor system message. The canonical no-prompt systems therefore use an explicit empty system message followed by the user message, while the prompted systems use the frozen ChatG&T system message followed by the same user prompt. This preserves the official template, keeps the intervention explicit, and makes its token cost measurable.

## 2026-07-14 — What makes a Python environment reproducible?

A virtual environment provides **isolation**, but isolation alone does not provide reproducibility. Installing an unbounded list of packages on two different days can produce different transitive dependencies inside two equally isolated environments.

A reproducible project needs several complementary records:

- a supported Python range and selected interpreter version;
- declared direct dependencies that communicate intent;
- a lockfile containing the exact resolved dependency graph and artefact hashes;
- exclusion of the materialised virtual environment from version control; and
- an executable check that imports the important libraries and reports what actually ran.

Hardware support is another layer. The same PyTorch package can contain CUDA libraries while correctly falling back to CPU on a machine with no CUDA device. Recording both the build capability and the detected runtime device prevents “CUDA-enabled package” from being confused with “GPU execution verified.”

## 2026-07-14 — Which context-length value should be trusted?

Different files in one model repository can advertise different context lengths. A tokenizer's `model_max_length` may be a generous generic value and does not prove that the model architecture or trained position encoding supports that many tokens.

For the pinned Qwen2.5 snapshot, the tokenizer reported 131,072 tokens while the model configuration declared 32,768 positions. The project adopts the lower model-config value as its operational limit.

The wider lesson is to record the source of every capacity claim. If a project wants to exceed the architectural configuration using RoPE scaling or another extension technique, that becomes a separate intervention requiring its own configuration, feasibility check, and limitations—not a value to infer from tokenizer metadata.

## 2026-07-14 — What does it mean to verify the LoRA lifecycle?

Successfully constructing a LoRA configuration does not establish that an adapter works with a chosen model and environment. Compatibility should be tested as a complete round trip:

```text
attach → verify → update → save → reload → reproduce
```

First, a newly attached adapter should be behaviour-neutral. LoRA adapters are normally initialised so that their contribution is zero, allowing training to begin from the base model's existing behaviour rather than disturbing it randomly. Under deterministic conditions, this is best checked by comparing the base and adapter-backed logits within a small numerical tolerance, not merely by observing that they generate the same text.

A disposable optimisation step should then demonstrate that gradients reach the LoRA parameters, their values change, the loss remains finite, and the frozen base-model parameters do not change. This proves more than adapter attachment alone because it exercises the actual training path.

The first optimization step also makes LoRA's zero-output initialisation visible. When one matrix in each low-rank pair starts at zero, only the other matrix receives a non-zero gradient on that first backward pass. A zero gradient on half of the paired matrices is therefore expected at initialization, not evidence that the adapter is disconnected. Optimizer behaviour still matters: decoupled weight decay can update a trainable matrix even when its gradient values are zero.

Finally, the adapter should be saved separately, loaded onto a clean instance of the exact pinned base model, and shown to reproduce its pre-save behaviour. A successful save call is not evidence that the artefact is complete or reloadable; only a clean round trip establishes that.

This feasibility check removes adapter-plumbing risk before real training. It does not demonstrate that LoRA can teach ChatG&T—that claim still depends on the training dataset and held-out evaluation.

## 2026-07-14 — When is QLoRA an unnecessary complication?

Quantisation is a response to a resource constraint, not an automatic requirement for parameter-efficient fine-tuning. QLoRA can make much larger models trainable on limited hardware by storing the frozen base weights at lower precision, but it also adds quantisation libraries, configuration, compatibility requirements, and different numerical behaviour.

For ChatG&T, the 1.54B-parameter BF16 base weights are approximately 3.09 GB and the disposable LoRA adapter contains only about 1.09 million trainable parameters. On a 24 GB GPU, activations and runtime overhead are more likely to determine feasibility than the adapter state. The cleaner initial experiment is therefore ordinary BF16 LoRA, with QLoRA retained as a fallback only if representative peak-memory measurements show it is necessary.

The rented-GPU measurement supported that reasoning: a two-example, 512-token BF16 workload peaked at 7.9336 GiB reserved on a 24 GB RTX 3090 without gradient checkpointing. QLoRA would have added complexity to solve a constraint the representative workload did not exhibit.

## 2026-07-14 — What does “CUDA compatible” mean on a rented GPU?

GPU compatibility is a relationship between several independently versioned layers:

```text
GPU architecture ↔ host driver ↔ PyTorch CUDA runtime ↔ framework code
```

The CUDA value printed by `nvidia-smi` describes the newest CUDA family supported by the host driver; it does not prove that the same toolkit is installed in the container or that a particular PyTorch wheel is compatible. A template can also include its own PyTorch and CUDA libraries while a project-local environment uses different ones.

ChatG&T's first 24 GB L4 allocation exposed driver 570.195.03 and CUDA 12.8 support. The locked PyTorch wheel uses CUDA 13.0, which requires an R580-or-newer driver, so the machine was rejected before environment download. The successful RTX 3090 exposed driver 580.159.03 and ran the unchanged CUDA 13 lock.

The wider lesson is to inspect the real machine before installing dependencies. GPU name and VRAM are necessary capacity facts, but driver compatibility is a separate feasibility gate.

## 2026-07-14 — Why should planned and observed infrastructure metadata remain distinct?

Cloud capacity is live inventory. The planned RTX 4090 was unavailable, a CUDA-compatible L4 could not be allocated, and the eventual run used an allowed 24 GB RTX 3090 fallback. Rewriting the raw report's planned GPU and rate after execution would make the evidence appear cleaner while obscuring what actually happened.

A reproducible record should preserve both layers: the intended configuration and the hardware, driver, price, timing, and cost actually observed. When they differ, a reconciliation note is more trustworthy than silently editing generated evidence.

## 2026-07-14 — What is the difference between greedy decoding and sampling?

A language model produces a probability distribution over possible next tokens. A decoding strategy determines how one token is selected from that distribution.

**Greedy decoding** always selects the highest-probability token. With fixed inputs and a deterministic runtime, it is straightforward to reproduce and removes sampling variance from comparisons. It can also favour safe, repetitive, or bland continuations, which may under-represent a creative application's intended behaviour.

**Sampling** draws from a filtered probability distribution. Temperature controls how sharp or flat that distribution is; top-p retains the smallest high-probability set whose cumulative probability reaches a threshold; and top-k limits consideration to a fixed number of likely tokens. Sampling can produce more varied and natural creative responses, but individual outputs include random variation.

A fixed seed makes the pseudorandom draws repeatable within a recorded environment. Giving compared systems the same derived seed provides the same random-number stream, but it does not give them the same semantic opportunity or sampled token: different model or prompt conditions produce different probability distributions.

For a fair sampled comparison, the seed should be derived independently of system identity and reset before every response. Execution order then cannot change which random stream a system receives. Generated token IDs, settings, seed, software, and hardware should still be retained because fixed seeds do not guarantee bit-for-bit identity across every device and implementation.

Greedy and sampled runs answer slightly different questions. Greedy decoding asks how each system behaves along its single highest-probability path. Sampling asks what a user is likely to experience when the creative system is operated as intended. ChatG&T uses sampling for the primary comparison and reserves multi-seed stability analysis as a separate secondary experiment.

## 2026-07-14 — Why should a specification be tested against the pinned libraries?

A design can be conceptually sound and still be impossible through the APIs actually installed. ChatG&T initially specified passing a dedicated random generator into `model.generate()`. Inspection of Transformers 5.12.1 showed that its ordinary sampling loop calls `torch.multinomial()` through the device-default RNG and rejects `generator` as an unused argument.

The reproducible solution is therefore library-specific but auditable: derive the per-prompt seed, create a dedicated device RNG state, install it only inside `torch.random.fork_rng`, run serialized generation, and let the context restore the previous state. The intent—execution-order-independent random streams—remains the same, but the mechanism now matches reality.

Adversarial review also revealed that implementation details can change what an experiment measures. Running the base systems through a disabled PEFT wrapper would not represent a realistic prompt-only deployment, and verifying a nonexistent `hf_device_map` attribute would reject a correctly loaded single-device model. The specification now uses separate stable base and adapted runtimes and verifies actual parameter/buffer placement.

The wider lesson is that implementation-grade specifications should be challenged at three levels:

1. **Scientific:** Does the design answer the intended comparison fairly?
2. **Evidential:** Would the records prove what actually ran?
3. **Executable:** Do the pinned libraries and hardware expose the assumed behavior?

A specification is not solid merely because it is detailed. It becomes solid when its important claims survive attempts to falsify them against the real environment.

## 2026-07-14 — What does an end-to-end CUDA acceptance test prove?

Environment discovery and actual execution answer different questions. `nvidia-smi` can identify a GPU and host driver, while `torch.cuda.is_available()` can show that PyTorch sees a device. Neither proves that the project's pinned model, adapter wrapper, generation settings, RNG handling, synchronization, timing, and evidence writer work together.

ChatG&T therefore accepted its inference harness only after the frozen environment performed a real BF16 tensor calculation and then completed sampled inference through two independently loaded CUDA runtimes: the untouched base model and the same base with an unmerged LoRA lifecycle adapter. The inspector found exactly two scheduled response records with no missing, duplicate, malformed, unexpected, or integrity-failing entries.

This is technical acceptance, not model-quality evidence. The lifecycle adapter exists to exercise attachment, loading, and inference machinery; it was not trained to produce ChatG&T responses. A good diagnostic is deliberately narrow about the claim it supports.

Observability failures should also remain visible. The run succeeded even though the attempted PyTorch CUDA-driver metadata accessor did not exist in the pinned version. The manifest retained that collection error, while `nvidia-smi` independently supplied the driver version. Optional metadata failure need not invalidate successful model execution, but it should be fixed before formal evidence collection rather than silently omitted.

Finally, short-lived GPU verification can be very inexpensive when setup is prepared and the pod is terminated promptly. The end-to-end L4 session cost $0.10; together with the earlier $0.14 training-feasibility session, recorded Runpod spend was $0.24 against the $20 training budget.

## 2026-07-14 — Where does engineering end and evaluation begin?

An experiment does not require knowingly sending a broken system into final evaluation. Before systems are frozen, the appropriate engineering objective is to get them working: build objective feedback tools, test on development prompts, improve the five-shot prompt, diagnose formatting failures, improve training data, and select a viable adapter using validation evidence.

The research boundary begins when the systems and evaluation procedure are frozen. Held-out prompts then measure whether the developed behaviour generalises. Changing a system in response to development failures is engineering; changing it after inspecting held-out failures is test leakage.

A useful working rule is:

> Before the freeze, get it working. After the freeze, find out whether it generalises.

This also separates the experimental question from a later production question. A deployed system might use constrained decoding, retries, repair, or other reliability controls. Those can be valuable engineering choices, but introducing them into the primary comparison would obscure what prompting and fine-tuning themselves changed. Any production safeguard should therefore be evaluated and labelled as a separate intervention.

## 2026-07-14 — Why can a small validator require adversarial design review?

A structural validator is measurement instrumentation. If two reasonable implementations assign different labels or validity booleans to the same output, the resulting system comparison can change even though the models did not. Apparently peripheral parser details are therefore part of the experimental method.

Adversarial review of ChatG&T's validator specification exposed several such details. Python's ordinary numeric conversions do not cover every JSON number lexeme; nested recipe arrays complicated surrounding-text discovery; multiple top-level values overlapped with that category; a same-identifier but modified schema could introduce unmapped errors; Markdown fences needed exact precedence and grammar; duplicate keys needed pair-preserving objects to retain nested paths; and escaped surrogate keys could break otherwise deterministic UTF-8 evidence serialization.

The broader lesson is not that every application needs an elaborate parser. It is that a research metric needs an explicit operational definition at every boundary that can change classification. Exact schema identity, stable label precedence, project-owned diagnostics, and adversarial boundary cases turn “valid JSON” from an intuition into reproducible evidence.

## 2026-07-14 — What is a prompt-development set for?

A prompt-development set is an engineering workbench, not a miniature held-out evaluation. Its outputs may be inspected repeatedly, and observed failures may directly influence the system prompt. That makes the set useful for getting the system working but disqualifies its results from supporting final generalisation claims.

Freezing the development inputs before model generation still matters. It prevents difficult prompts from being silently replaced after their failures are seen and makes successive system-prompt versions comparable on the same tasks and random streams. Purposeful roles—clean, naturalistic, constrained, and robustness—provide more diagnostic value than a larger collection of loosely varied questions.

Once inspected, a development prompt and its close paraphrases are spent for held-out purposes. Keeping them out of training data, validation data, five-shot examples, and the final test set preserves clear evidence boundaries. Formal cross-domain status must also wait until the training topics are known; a topic cannot be called withheld before the source domain has been defined.

## 2026-07-14 — What makes a useful few-shot example set?

Few-shot examples are behavioural demonstrations, not decorative illustrations. A strong set should show the range of transformations the system must perform, including intent inference, concrete constraint fulfilment, format persistence, and delivery of finished artefacts. Five clean examples from different topics would provide topical variety but teach little about difficult behaviour.

For ChatG&T, one example per intent family gives breadth while deliberately varying the example roles. The repeated constrained role reflects the central quality risk: producing an entertaining recipe that fails to complete the user's actual task.

Worked examples also create an evidence boundary. Their inputs, ideal outputs, and close paraphrases have influenced the system directly, so they cannot later demonstrate generalisation and must remain outside development, training, validation, and held-out data. Freezing their exact content and validating their outputs before prompt assembly separates example design from later model-driven iteration.

## 2026-07-14 — What exactly does a tokenizer result's length measure?

Token accounting must inspect token IDs rather than assume that `len(tokenizer_output)` means token count. In the pinned Transformers version, Qwen's `apply_chat_template(..., tokenize=True)` returns a `BatchEncoding` with `input_ids` and `attention_mask`. Its Python length is therefore two—the number of mapping fields—not the number of tokens.

The correct measurement is `len(result["input_ids"])`. After correcting that boundary, ChatG&T's five-shot prompt added 2,319 tokens to every paired development input, rather than the impossible zero initially suggested by measuring both container lengths as two.

This is another example of why evidence code must be tested against actual library return types. A plausible-looking scalar can be internally consistent, reproducible, and completely wrong if the measured object is misunderstood. Sanity checks against content-only tokenisation and known chat-template overhead help expose such failures before results are recorded.

## 2026-07-14 — What does an inference seed actually do?

Sampling settings define the probability landscape; a seed makes the random draws from that landscape repeatable. At each generated token, the model assigns probabilities to possible continuations. A pseudorandom number selects among the permitted candidates, and the seed determines the reproducible sequence of those numbers. Changing temperature or the prompt changes the distribution, while changing only the seed changes the sampled path through it.

The same seed does not force two systems to emit the same token. If their prompts produce different probability distributions, applying the same random number can select different outcomes. Pairing seeds is still useful because it prevents execution order or an unrelated random history from deciding which pseudorandom stream each system receives.

ChatG&T uses one master run seed to derive independent per-prompt generation seeds and a separately namespaced execution-order seed. System identity is excluded from generation-seed derivation, so Systems A and B receive paired streams for the same prompt. The seed controls inference sampling and schedule order; it does not alter model weights, training data, or prompt content, and it cannot by itself guarantee bit-identical results across different software or hardware.

## 2026-07-15 — What is a runbook?

A runbook is an operational checklist for performing one concrete technical task safely and repeatably. A project plan explains where the work is going, and a specification defines how a system must behave; a runbook gives the operator the exact commands, order, expected observations, stop conditions, recovery boundaries, and evidence-preservation steps for a real execution.

This is especially useful for temporary paid infrastructure. Preparing the commands before a Runpod session reduces time spent improvising on a billed machine, while explicit failure rules discourage ad hoc dependency changes, silent retries, or evidence loss under pressure. Copying results home and verifying them before deleting the Pod is part of the operation, not administrative cleanup afterward.

A runbook is not necessarily automation. Its first job is to make the human procedure inspectable and reproducible. Once the procedure has been exercised and stabilised, repetitive pieces may be automated without losing the documented operational boundary.

## 2026-07-15 — Does reproducibility require a fresh machine for every run?

No. Reproducibility requires independently verifiable experimental identity, not the ritual of rebuilding identical infrastructure. The same rented Pod can support multiple runs when each one rechecks the pinned code, dependencies, model, prompts, configuration, seeds, hardware path, and unique output destination.

This separates persistent state from trusted evidence. Model files and dependency caches may survive beneath `/workspace` to save setup time, but they remain subject to checksum and environment checks. Raw run evidence is copied and verified locally after every execution rather than relying on the continued existence of the Pod.

Stopping a Pod between nearby iterations can also separate storage cost from GPU cost. The convenience creates a new operational risk—forgotten billable storage—so reuse needs an explicit stop-versus-terminate rule and a reminder to review stopped resources. Fresh infrastructure is still appropriate when the old environment is unsuitable or can no longer be verified confidently.

## 2026-07-15 — Can measurement instrumentation contaminate its own evidence?

Yes. ChatG&T's first formal development manifest reported a dirty Git tree even though the run procedure checked out a frozen revision. Inspection showed that the harness created its untracked lock file before asking Git whether the tree was dirty. The instrumentation changed the state it intended to measure.

This did not change the model behavior because the manifest independently hashed the implementation tree, project files, model, configuration, prompts, and systems. It did make the general `git_dirty` field incapable of proving pre-run cleanliness. The correct response is to retain the surprising value, explain its cause, narrow the claim supported by the run, and fix the measurement order before relying on that field again.

The broader lesson is that provenance collection has an observer effect whenever it creates files, imports mutable state, or starts services before taking its snapshot. Evidence capture should either occur before those mutations or explicitly exclude and test its own operational artefacts.

## 2026-07-15 — Must prompt development use the formal inference environment?

No. Prompt development and formal evaluation have different jobs. A fast local approximation can expose structural, instructional, and stylistic failures cheaply; the formal environment establishes exact model identity, matched measurements, and publishable evidence.

The distinction only works when transfer is tested rather than assumed. ChatG&T keeps every inspected prompt version visible, compares candidates on one local runtime, labels those outputs as diagnostics, and sends the selected unchanged prompt back through the pinned BF16 harness. This creates a quick inner engineering loop inside a controlled outer research loop.

Hardware freshness is not rigor by itself. The defensible boundary is whether a claim is supported by the environment that produced it: local runs can justify prompt edits, while formal comparative claims must wait for the pinned harness.

## 2026-07-15 — What did the prompt-development loop teach us?

Prompt quality and prompt length did not move monotonically. Adding a concrete, recent JSON skeleton in version 3 produced the strongest full-pass result, even though it was the longest candidate. Compressing the main instructions in version 4 saved an average of 182 input tokens relative to v3 but reduced every quality count. Efficiency is a useful tie-breaker, not a substitute for meeting the behaviour contract.

More explicit wording also showed diminishing returns. Versions 2 and 3 improved full responses, but schema validity plateaued at 11 out of 20 and recurring failures remained. This suggests a practical ceiling for prompt engineering with this small model and unconstrained sampled decoding on the development population. That is exactly the kind of gap fine-tuning can now be asked to address; it is not a reason to keep rewriting the prompt around known cases.

Finally, equal aggregate metrics do not establish runtime equivalence. Local quantised v1 and formal BF16 v1 both produced nine schema-valid responses, yet only four local responses and six formal responses passed every qualitative dimension. A fast local workbench can guide engineering, but transfer has to be measured on the intended formal stack.

## 2026-07-15 — Is an experimental stopping rule an engineering definition of “good enough”?

No. An engineer developing a product may continue iterating until the system meets its operational requirements or the expected benefit no longer justifies the work. A researcher stops at a predeclared boundary so that the observed comparison remains interpretable. These are different objectives rather than competing standards of competence.

ChatG&T's four-version prompt budget was a methodological guardrail, not evidence that four is a universally optimal number of prompt iterations. It limited repeated adaptation to the same 20 known development prompts and reduced the freedom to keep changing the baseline after seeing unfavourable results.

Stopping at version 3 therefore does not mean that the prompt is production-ready or incapable of further improvement. It means that version 3 is the strongest prompt produced inside the declared experimental procedure. Further prompt refinement, constrained decoding, retries, or output repair can still be explored later as a separately labelled product-engineering phase.

A protocol can be amended after results are seen, but the change becomes post-hoc and must be disclosed. If further prompt development were necessary, a cleaner extension would declare a new revision budget before generation and use fresh development prompts rather than repeatedly tailoring the prompt to these same 20 cases.

## 2026-07-15 — How should an inspector treat historical evidence after the codebase changes?

An immutable run should not become invalid merely because later development adds a new source file. During the prompt-development audit, the original GPU run initially failed inspection because the current package contained new evaluation modules that did not exist when the run manifest was created. The inspector was comparing a historical file inventory with the present working tree.

The correct reference is the state recorded by the run. The manifest's behaviour-file identities and tree digest establish internal integrity, while a clean recorded Git commit can establish which package files existed at that revision. The current checkout is not evidence of what should have existed in an earlier commit.

This distinction is important for long-lived experiments: verification code may become stricter, but it should verify historical claims against historical identities rather than silently redefining them using today's repository contents. A regression test now requires the accepted 40-attempt run to remain inspectable after later package files are added.

## 2026-07-15 — Can a local ignored artefact hide a non-portable test?

Yes. ChatG&T's adapter-loading unit test referred to the lifecycle adapter generated during an earlier local diagnostic. The artefact was correctly excluded from Git, but its presence made the test pass locally. On a fresh Runpod clone the same test failed before reaching its mocked adapter loader because the directory did not exist.

A unit test should create every disposable fixture it needs or mock the boundary it is not testing. Depending on leftover local state makes a test result describe the workstation rather than the repository. Fresh-clone execution is therefore a useful portability check even when the code already passes locally.

The failure did not invalidate the base-only v3 confirmation path, but it exposed a test-design defect that must be fixed before the next formal run. More generally, ignored files should be treated as absent when assessing whether a test suite is reproducible.

## 2026-07-15 — Does better schema adherence imply a better complete response?

No. Pinned prompt v3 improved schema validity from v1's 9 out of 20 responses to 12 out of 20, but full response passes fell from six to five. Five structurally valid v3 responses lost the natural recipe voice and became ordinary prose placed inside recipe-shaped JSON. Four structurally valid responses also failed the user's underlying task.

This is why structural and qualitative evaluation cannot be collapsed into one metric. A concrete output skeleton can help a model reproduce braces, fields, and arrays without teaching it to reason accurately, deliver a requested artefact, or sustain a coherent style.

Local-to-formal transfer can also differ by dimension. V3's local structural count transferred closely, while its local recipe-style result did not. A fast approximate runtime can identify promising interventions, but candidate confirmation must examine the complete behaviour rather than only the metric the intervention directly targeted.

The mixed result is useful for fine-tuning design. Training data must repeatedly demonstrate the joint behaviour—correct task completion, coherent metaphor, natural recipe execution, and valid JSON—because optimising only the easiest objective can move failures into a softer dimension.

## 2026-07-15 — What is a readiness review for?

A readiness review asks whether a stage has produced enough trustworthy evidence to support the next kind of work. It is not a demand that the whole project be finished or defect-free.

Unresolved items should be classified by consequence. A **blocker** prevents the next stage from producing valid work. A **hard gate for a later action** permits current progress but must be resolved before a named future operation. A **limitation** does not necessarily require correction, but constrains what can be claimed.

For ChatG&T, the non-portable adapter unit test does not block held-out evaluation design, so Stage 3 can begin. It does block the next formal model run, making it a concrete gate before Stage 6 GPU execution. Mixed prompt-transfer results are limitations and design evidence rather than unfinished prompt work.

This classification prevents both extremes: declaring readiness while hiding consequential defects, or keeping a stage open indefinitely because unrelated later decisions remain. A useful exit decision states what is ready, what remains, when each remaining item becomes mandatory, and which claims are still unavailable.

## 2026-07-15 — What does evaluation sample size change?

A measured rate from a held-out set is an estimate, not the system's exact underlying performance. If a system wins 60% of 40 prompts, another reasonable sample of 40 prompts could produce a noticeably different result. More prompts reduce the influence of any one unusual case, but uncertainty shrinks slowly: approximately four times as many independent observations are needed to halve a margin of error.

Near a 50% result, rough 95% margins of error are about 15 percentage points for 40 observations, 13 for 60, and 11 for 80. These are planning approximations rather than final confidence intervals. The final analysis should calculate intervals from the observed outcomes and respect ties and the paired comparison design.

Sample size also limits subgroup claims. Sixty prompts can provide 12 examples in each of five equally sized intent families, which is useful for locating failure patterns but too small for precise family-level performance estimates. ChatG&T will therefore use its 60-prompt evaluation for an honest portfolio-scale comparison: overall results can describe large differences and trade-offs, while slices remain diagnostic and small apparent advantages will not be overstated.

## 2026-07-15 — How can one small evaluation cover several kinds of variation?

An evaluation prompt can carry several cross-cutting labels at once. Intent family, reporting slice, input form, task complexity, and constraint status describe different properties of the same example; they are not separate datasets whose quotas should be added together. This makes purposeful coverage possible without inflating a portfolio-scale sample.

Coverage labels should also be observable enough to apply before outputs exist. “Hard” is subjective and may be influenced by which system later struggles. “Composed,” by contrast, can be defined from visible features such as multiple outcomes, supplied material, explicit constraints, competing considerations, or connected steps. Freezing those definitions before prompt authoring makes the sample easier to audit and reduces post-hoc relabelling.

## 2026-07-15 — Should exact held-out prompts be written before the training data?

Not necessarily. Freezing exact test prompts first can expose the exam questions to the people creating supervised examples, allowing training data to be shaped around them. Writing the test last can create the opposite risk: its author may tailor the evaluation to flatter or punish the completed dataset.

The useful separation is to freeze the **evaluation rules** before dataset creation, freeze the **training and validation data** before exact test authoring, and freeze the **held-out prompts** before any model training. The fixed blueprint constrains later test selection, while the absent exact prompts prevent dataset authors from training toward known cases. Predeclared collision rules and a retained replacement log make legitimate test-candidate rejection distinguishable from silent cherry-picking.

Cross-domain policy must be established before supervised data are written. Otherwise a test author could inspect the finished dataset and opportunistically call any convenient omission “withheld.” This sequence cannot eliminate every judgment in a small hand-authored experiment, but it makes the direction and timing of those judgments visible.

## 2026-07-15 — Why should similarity retrieval not decide contamination?

Lexical and embedding similarity answer “which existing records should a reviewer inspect?” They do not answer “is this a duplicated experimental scenario?” Shared wording can support different goals, while disguised paraphrases can share little wording. Embedding scores also inherit truncation and model-specific biases.

A stronger process combines exact, lexical, semantic, and metadata retrieval, then applies an explicit substantive rule: same goal, same situation or requested artefact, and an answer reusable through surface substitutions. Retrieval reduces memory burden; recorded judgment preserves the meaning of generalisation.

## 2026-07-15 — Why audit accepted test candidates as well as rejections?

Second-reviewing only rejected candidates can detect overzealous removal, but it cannot show whether the primary reviewer is quietly allowing collisions. A deterministic audit of accepted candidates tests both directions while keeping the workload proportionate. The second reviewer should not see the first decision, because even a short label can anchor the supposedly independent review.

## 2026-07-15 — Why are prompt contamination and response memorisation different?

Prompt contamination is a pre-generation design question: does the evaluation ask a task already used in project development or supervision? Response similarity is a post-generation diagnostic: does the model output suspiciously reproduce an authored answer? A test prompt can be novel while its output echoes training data, and a duplicated prompt can produce a novel response.

Both checks can reuse retrieval machinery, but their sources, timing, review questions, and claims differ. Similarity is evidence worth inspecting, not proof that a particular training example caused the output—especially when the base model's pretraining is unknown.

## 2026-07-15 — What does human calibration of an LLM judge establish?

A small human-scored sample does not turn model judgments into human evaluation or prove that the judge represents public taste. It shows how one recorded human application of the frozen rubric agrees or disagrees with the automated judge under these conditions.

Keeping exact score agreement, pass/fail agreement, and weighted agreement visible is more informative than silently adjudicating differences. A predeclared sample and no post-hoc agreement threshold also prevent inconvenient disagreement from becoming a reason to rewrite the evaluation after seeing results.

## 2026-07-15 — What does an embedding's maximum length mean for overlap checks?

`all-MiniLM-L6-v2` accepts at most 256 wordpieces in this protocol. Wordpieces are tokenizer units, not words or characters. A short-looking code fragment can split heavily, while ordinary words may be one piece. Anything after the limit is absent from the vector, so a semantic similarity score cannot provide evidence about that omitted content.

A reproducible overlap tool should therefore record the untruncated token count and an explicit truncation flag. Truncated prompts still receive lexical, metadata, and complete-text semantic review. A real long supplied-text calibration case is more informative than merely documenting the limit because it proves the diagnostic path works.

## 2026-07-15 — How should unresolved judgments affect denominators?

`unable_to_assess` is useful only if it does not become a quiet way to discard difficult failures. After one fresh blinded judgment, a still-unresolved qualitative dimension remains visible, cannot full-pass, and is excluded only from a separately labelled resolved-score denominator. A persistently unresolved pair likewise stays visible outside the resolved conditional preference denominator and as an unresolved end-to-end outcome.

Every rate should show both numerator and denominator. This makes the difference between "not applicable," "failed," and "not resolved" inspectable rather than allowing whichever denominator looks best after results.

## 2026-07-15 — Why bootstrap prompt IDs rather than individual system rows?

B and C answer the same prompts, so their outcomes are paired. Resampling their rows independently would break that relationship and overstate or misstate uncertainty. A paired bootstrap samples prompt IDs and carries both systems' values for each selected prompt together.

The interval then describes how the observed C-minus-B difference varies when prompts from this authored sample are resampled. It does not correct biased prompt selection, estimate generation-seed variability, or turn 60 prompts into a population survey.

## 2026-07-15 — Why attribute response similarity to system exposure?

System B sees the worked responses at inference, C sees training responses through fine-tuning, and D sees both; A sees neither. The same exact or semantic match therefore has a different interpretation for each system. Retaining the reference collection and exposure status prevents a base-model coincidence from being described as fine-tuning memorisation.

Repeated outputs across unrelated prompts are another problem again: generic collapse or low diversity. It can reuse the same retrieval machinery, but should be reported separately from copying a project-authored reference.

## 2026-07-15 — When is a digest evidence of a process rather than a self-consistent claim?

A digest proves that some named bytes have not changed relative to that digest; by itself it does not prove where those bytes came from or that a command was executed. Provenance becomes materially stronger when the consumer starts from the producing system's real artifact, reruns its ordinary integrity checks, and derives downstream records from those exact bytes instead of accepting caller-composed summaries.

The same distinction applies to verification logs. Stored JSON can be checked for internal integrity and reproduced later, but a person who controls the machine can fabricate code, output, clocks, and hashes together. ChatG&T therefore allows only the process that just completed all live gates to hold the in-memory capability for a freeze transition. This prevents accidental or API-level reuse of stale evidence, while the documentation remains honest that independent attestation would require an external trust anchor such as protected CI and signed provenance.

Time is also part of provenance. Individually valid timestamps can still describe an impossible history. Cross-artifact validation should enforce one explicit UTC chronology—from source freezes through authoring, reviews, semantic checks, bundle freeze, candidate observation, live gates, and review completion—and reject future-dated records. Equality may be legitimate when several operations share the clock's recording resolution.

## 2026-07-15 — Why is a version label not a treatment identity?

A prompt can call itself `five-shot-v3`, contain five plausible examples, and carry perfectly consistent replacement digests without being the prompt selected by the experiment. Labels and internal consistency establish shape; they do not establish experimental identity.

The formal evaluation must reach the same canonical identity mechanism used when the prompt was selected: deterministic assembly, exact frozen bytes, the expected digest, and the selected source path. The aggregate must also bind the harness and configuration sources that interpret those bytes. Otherwise a later code or configuration change can alter the treatment while leaving the high-level A/B/C/D description apparently intact.

## 2026-07-15 — When should an adversarial review loop stop?

An adversarial review needs an explicit stopping rule. Without one, each successful repair creates a larger system with new surfaces to challenge, and the work can drift from protecting the experiment into designing audit infrastructure.

For ChatG&T, a finding blocks freeze only when it could change the compared treatments, evaluation population, scoring rules, denominators, leakage boundary, or interpretation of the primary result. Reproducibility weaknesses that constrain a claim should be documented; resistance to a malicious maintainer who controls the repository requires an external trust system and is not a reasonable local portfolio requirement.

The practical lesson is to define the required assurance level before beginning review, classify findings by their effect on the research question, and stop once material blockers are resolved and remaining limitations are explicit.

## 2026-07-15 — How should a long-running delegated goal define “done”?

A long-running goal needs more than an objective. It should also define the expected assurance level, which findings count as blockers, what may be recorded as a limitation, how many review cycles are proportionate, and the required handoff state.

For a portfolio project, “credible and proportionate” is different from production, compliance, or adversarial-security hardening. A useful delegation can state that only findings capable of materially invalidating the experiment should trigger another revision; lesser reproducibility or trust concerns should be documented. It can also cap review rounds and require a pause before expanding scope.

The agent shares responsibility for this boundary. Even without a perfect initial instruction, it should recognise diminishing returns, explain when work is moving beyond the project's purpose, and ask before continuing into a materially larger assurance problem.

A practical template is:

> Complete the stage autonomously to portfolio quality. Use one implementation pass and one critical review. Fix findings that could materially invalidate the experiment, record lesser concerns as limitations, and ask before exceeding two revision cycles. Finish with passing tests and the requested commit or handoff state.

## 2026-07-15 — Why is dataset size more than an example count?

Example count is useful for planning coverage and review effort, but optimisation operates on tokens. Two datasets with 200 records can provide very different learning signals when one contains much longer responses, concentrates length in one intent family, or silently truncates examples at the training sequence limit.

A small supervised dataset should therefore freeze both record counts and token distributions. Prompt, response, and supervised-token totals should be reported by split and important coverage groups, with every truncation visible.

Validation and pilot data also have different jobs. Validation contains scenario-isolated examples used for loss and model-selection evidence; a pilot is a fixed subset of training used to prove the pipeline and observe early learning. Treating the pilot as another evaluation set or presenting validation as final held-out performance would blur those boundaries.

## 2026-07-15 — How much of a small dataset should be controlled by quotas?

Quotas are most useful when they protect something that could otherwise disappear unnoticed: an intent family, input form, hard joint behaviour, compatible user constraint, or robustness pressure. These dimensions can cross the same examples. A composed robustness prompt can simultaneously be a direct request in the explanation family, so its labels should not be treated as separate pools whose counts are added together.

Dense quotas for every topic, tone, title shape, ingredient count, or garnish style would create a false sense of precision and encourage filler. For those properties, concentration limits and diversity audits are more useful: they reveal collapse or templating while leaving room to prefer natural, high-quality examples.

The practical distinction is between **coverage needed to test the learning claim**, which deserves a hard target, and **variation that keeps the dataset healthy**, which usually deserves an audit and a review trigger.

## 2026-07-15 — Why give composed examples substantial representation?

A small instruction model may learn the visible JSON and recipe shape before it learns to combine that shape with usefulness, supplied material, explicit constraints, and resistance to contrary instructions. If almost every example is simple, training success can amount to format imitation while the central joint behaviour remains weak.

ChatG&T therefore targets 40% composed examples. This is not a claim that real traffic contains exactly that proportion. It is a supervision choice: difficult joint behaviours need enough demonstrations to be learnable, while a majority of standard examples still teaches the ordinary intended experience.

## 2026-07-15 — Why separate dataset content from workflow history and model rendering?

A supervised example, the process that produced it, and the messages eventually consumed by one model are three different things. Combining them makes records noisy, couples authored data to a particular model, and encourages mutable review state to leak into the training representation.

A cleaner design keeps one semantic source record, records drafting and review events separately, and derives model-ready messages deterministically. The source remains readable and reusable; the event history makes provenance inspectable; and the renderer makes every model-specific transformation reproducible.

Some explicit metadata may repeat facts that could be inferred—for example, a constraint flag and its constraint descriptions. That redundancy is useful for human inspection only when validators enforce agreement. Unchecked redundancy creates ambiguity rather than clarity.

## 2026-07-15 — Why separate topic from task subtype?

Topic answers “what is this about?” while task subtype answers “what operation does the user want?” A career prompt may ask for advice, explanation, emotional support, creative material, or a rewrite. Collapsing those dimensions would make a diverse-looking dataset repeatedly teach the same capability within each domain.

One controlled primary label on each axis produces countable coverage without requiring multi-label taxonomy work. Broad registries prevent trivial spelling variants from masquerading as diversity, while concentration limits and cross-family coverage encourage meaningful combinations. Pressure from a robustness prompt remains another independent label; it does not erase the ordinary task the model must still complete.

## 2026-07-15 — Why should content identity exclude later dataset allocation?

An example can be written, revised, reviewed, and accepted before its scenario group is assigned to training or validation. If the workflow digest covers `split` and `pilot_member`, allocation changes the supposedly terminal content identity and makes the event history impossible to reconcile without pretending a split decision was an authored revision.

The cleaner boundary is to hash all authored supervision, metadata, and provenance as content while excluding only allocation fields. Freeze records and derived files still bind the complete allocated record. This preserves both claims: the reviewed content did not change, and the eventual split is exactly identifiable.

Authoring and freeze validation therefore have different responsibilities. Authoring may contain an accepted but unassigned example; freeze may not. A validation mode should enforce the invariants that are knowable at that lifecycle stage rather than prematurely requiring future state.

## 2026-07-15 — How can later tests coexist with historically frozen evidence?

Stage 3 evidence bound the exact digest set of `tests/test_*.py`. Adding a Stage 4 test file under that glob correctly changed the identity and caused the old attestation to fail. Recreating the historical evidence would make it appear that the expanded suite had been part of the earlier freeze.

The proportional solution is an additive test boundary: preserve the original command and files, place the new contract suite in a separately named directory, and run both commands. More generally, a frozen verification manifest should identify the suite it attests without preventing later stages from adding independently identified checks.

## 2026-07-15 — Why is splitting by scenario different from splitting by record?

Two records can look distinct while asking for substantively reusable answers. Assigning them independently can put one paraphrase in training and another in validation, making recall look like transfer. The unit of allocation should therefore be the scenario group whenever the research claim concerns generalisation beyond seen situations.

Once groups are indivisible, exact row counts may not always be attainable. A useful allocator makes that trade-off visible: attempt the target, preserve isolation, report the achieved deviation, and require an attributable decision rather than quietly breaking the group or pretending the target was exact.

## 2026-07-15 — What does a seed do in deterministic allocation?

A seed can break ties reproducibly without turning a hand-authored dataset into a random sample. ChatG&T hashes the seed, a purpose-specific namespace, and the scenario or example ID. Count and coverage objectives decide first; the digest matters only when alternatives are otherwise equally valid.

Separate namespaces for validation allocation and pilot selection prevent a coincidental ordering in one procedure from controlling the other. The result is stable across file order and repeated runs, but the statistical claim remains about this deliberately constructed dataset rather than a randomly sampled population.

## 2026-07-15 — Why should split assignment consider coverage as well as counts?

An exact 160/40 split can still be unusable if validation contains no robustness pressure, no composed tasks, or only one input form. Count balance and behavioural coverage answer different questions.

A coverage-aware allocator treats the required validation labels as feasibility constraints, then optimises count deviations among feasible scenario-group assignments. This prevents a tidy count from taking priority over the reason validation exists: monitoring whether learning transfers across the behaviours the model is meant to acquire.
