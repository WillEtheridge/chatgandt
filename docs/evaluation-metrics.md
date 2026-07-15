# Evaluation Metrics

This document defines how ChatG&T responses and experimental systems will be measured. The study reports quality and efficiency as separate outcomes rather than combining them into a single winner score.

## Evaluation layers

Every response is evaluated through four layers:

1. **Execution:** Did generation complete, and what resources did it use?
2. **Structure:** Is the untouched raw output valid JSON that conforms to the ChatG&T schema?
3. **Quality:** Is the response acceptable on each qualitative dimension?
4. **Comparison:** Which system does a blinded evaluator prefer?

Training and validation loss are training diagnostics. They are not evidence that the model performs the intended behaviour on unseen prompts.

## Automatic structural metrics

### Generation completion

Each started attempt records one `attempt_status`: `success`, `input_context_exceeded`, or `generation_error`. `generation_completed` is true only for `success` records. A `max_new_tokens` termination still counts as successful execution; the untouched output can subsequently fail structure or quality checks.

Pre-run identity or loading failures abort before generation. Isolated generation errors are recorded without retry and the run continues only when its runtime remains healthy. A run is complete only when it contains exactly one record for every scheduled system–prompt combination; interrupted partial evidence is preserved without filling missing rows.

### Strict JSON validity

`json_valid` records whether the complete raw output can be parsed as JSON without extraction, repair, or retry.

- Leading and trailing whitespace is permitted.
- Markdown fences and surrounding prose cause failure.
- Duplicate keys, `NaN`, and infinity cause failure.
- Any valid JSON value passes this check, even if it is not an object that conforms to the ChatG&T schema.

### Schema validity

`schema_valid` records whether the parsed output satisfies the complete normal-response contract in [ChatG&T behavioural contract](behavioural-contract.md).

The strict parser, Draft 2020-12 response schema, stable label mapping, and deterministic validation record are defined in [Step 8 schema validation specification](schema-validation-specification.md).

The headline structural measure is **first-attempt schema-valid rate**: schema-valid raw outputs divided by all attempted generations. Outputs are not repaired, extracted, retried, or produced through constrained generation for this measure.

### Structural failure categories

Invalid responses may receive multiple failure labels:

- `generation_failure`
- `surrounding_text`
- `markdown_fence`
- `json_syntax`
- `duplicate_key`
- `wrong_top_level_type`
- `missing_field`
- `unexpected_field`
- `wrong_field_type`
- `ingredient_count`
- `method_count`
- `null_value`
- `blank_string`
- `non_positive_amount`

Diagnostic values such as ingredient count, method-step count, top-level keys, raw character count, and output-token count will also be retained.

## Qualitative dimensions

Schema-valid responses are evaluated on three separate dimensions. These are holistic judgments rather than averages of sub-scores.

### Underlying-answer quality

> Would the substance be a good response to the user’s prompt without relying on the novelty of the cocktail format?

### Metaphorical coherence

> Do the recipe elements meaningfully represent and develop the underlying answer?

### Recipe-style execution

> Does the response sustain a concise, natural cocktail-recipe voice without becoming ordinary prose, forced wordplay, or repetitive?

## Qualitative scoring scale

Each dimension uses the same three-point scale:

| Dimension | 1 — Fails | 2 — Acceptable | 3 — Strong |
| --- | --- | --- | --- |
| Underlying-answer quality | Does not meaningfully fulfil the prompt | Gives a sound, relevant response with noticeable limitations | Fully fulfils the prompt with specific, effective content |
| Metaphorical coherence | Recipe elements feel arbitrary or disconnected | The metaphor generally works but contains weaker elements | The complete recipe forms one meaningful, well-developed metaphor |
| Recipe-style execution | The recipe voice is absent, inconsistent, or badly forced | The recipe voice is clear and readable, with some awkward or generic phrasing | The recipe voice is natural, concise, playful, and strengthens the answer |

A materially incorrect response cannot score above 1 for underlying-answer quality. An evaluator who cannot make a reliable judgment records `unable_to_assess`; the response receives one fresh blinded judgment. If the same dimension remains unresolved, it cannot contribute to a full pass. It remains in schema-valid and all-attempt counts, appears in a separate unresolved count, and is excluded only from the resolved dimension-rate denominator, which must be shown.

The normative anchors are stored in [`evaluation-rubric-v1.json`](../config/evaluation-rubric-v1.json). Missing an essential compatible substantive/content constraint forces underlying-answer quality to 1. Requests to replace JSON with prose, Markdown, XML, or another format—or to abandon the cocktail behaviour—conflict with the frozen contract and are excluded from this penalty. Structural requirements are not scored a second time after schema-valid eligibility has been established.

## Joint response-level pass

A response receives a full pass only when:

```text
schema_valid
AND underlying_answer_quality >= 2
AND metaphorical_coherence >= 2
AND recipe_style_execution >= 2
```

Scores cannot compensate for one another. A response fails if it is structurally invalid or any qualitative dimension scores 1.

**Full-response pass rate** is the percentage of all attempted generations that meet the complete joint rule.

## LLM-judge and human evaluation

One recorded frontier-model judge applies the qualitative rubric once to every schema-valid response, but those results are labelled **LLM-judge scores**, not human scores.

LLM judging follows the exact templates, provider/interface/model-family policy, fallback rule, session disclosure, renderer, and pre-production calibration in [`judge-manifest-v1.json`](../config/judge-manifest-v1.json). Every judgment binds the manifest and packet digests. The chosen interface does not expose a stable backend snapshot or sampling settings, so those values are recorded as unavailable rather than inferred. The project author independently scores 24 deterministically selected eligible response packets. This is pragmatic coverage, not a powered validation study.

Public Tasting Room votes remain separate from the curated evaluation because public participants and prompts are self-selected.

## Pairwise comparison

The primary pairwise comparison is System B against System C.

### Conditional preference

When both responses are schema-valid, a blinded evaluator sees the same user prompt and randomly ordered responses, then selects Response A, Response B, or Tie.

The evaluator answers:

> Which response better fulfils the prompt while sustaining a coherent and natural cocktail-recipe response?

System B preference rate, System C preference rate, and tie rate are all reported. Non-tie preference may be reported as a secondary figure, but ties must not be hidden.

Response order is precomputed and balanced 30/30 across the complete prompt set using the frozen seed and a deterministic hash ordering. Conditional eligibility is assessed later, so its displayed subset may not remain balanced and the achieved order counts are reported. Every conditionally eligible pair receives one primary blinded LLM judgment. One second blinded judgment handles `unable_to_assess`; a second unresolved result remains visible and outside the resolved conditional denominator. A pragmatic 15-pair human calibration sample targets five per slice. Exact rendering, selection, blinding, shortfall, and identity-reveal rules are specified in [Blinded pairwise protocol](blind-pairwise-protocol.md).

### End-to-end outcome

- If both responses are schema-valid, use the blind preference.
- If only one response is schema-valid, the valid response wins the end-to-end outcome.
- If neither response is schema-valid, record `both_failed` rather than a tie.

The conditional and end-to-end results are reported separately because they answer different questions.

## Efficiency metrics

The experiment will record:

- input tokens per request after applying the model’s chat template;
- synchronized `model.generate()` latency, including prompt prefill and output generation;
- output-token count;
- LoRA adapter size; and
- fine-tuning time.

Inputs are tokenized before timing. CUDA is synchronized immediately before and after `model.generate()`, which runs at batch size one after one unmeasured warm-up per loaded runtime. Model loading, tokenization, decoding, persistence, cold starts, application overhead, time to first token, and separate prefill/decode timing are excluded from the primary latency metric.

Measurements must use matched hardware, quantisation, inference software, and generation settings. Recorded system/prompt combinations run independently, without a reusable conversation cache, and in a reproducibly randomized order. The experiment's primary one-sample-per-system/prompt design supports descriptive latency comparisons; dedicated repeated benchmarking and tail-latency claims are outside its scope.

Input-token reduction and latency reduction are reported separately. Fewer input tokens do not by themselves establish lower latency.

## Uncertainty and denominators

Every system has 60 attempted generations. Missing and failed attempts remain in structural and full-response denominators. Overall binary rates receive 95% Wilson score intervals. Pairwise B wins, C wins, and ties retain separate counts and Wilson intervals; a decisive-only preference interval is supplementary.

Matched C-minus-B differences use 10,000 paired non-parametric bootstrap resamples of prompt IDs with seed `20260715` and percentile 95% intervals. Each sampled prompt carries its B and C values together, preserving the paired design. Subgroup results remain diagnostic counts and rates without intervals. The experiment does not use null-hypothesis significance tests or choose among many comparisons according to whichever appears favourable.

Two dimension summaries remain distinct. **Conditional resolved acceptability** is scores `>=2` divided by schema-valid responses with a resolved integer score; unresolved counts are shown beside it. **End-to-end dimension success** is scores `>=2` divided by all 60 attempts, so structural failures and unresolved scores do not succeed without being relabelled as score 1. Full-response pass across structure and all dimensions is the headline quality rate.

## Response similarity

Generated responses are checked for exact, lexical, and semantic overlap with project-authored references under [Response similarity and memorisation protocol](response-similarity-protocol.md). Exposure attribution is retained: worked responses are primary references for B/D, while training responses are primary references for C/D. Cross-collection comparisons for A or other unexposed systems are diagnostic controls, not evidence that project training caused copying. Repetition among one system's held-out outputs is reported separately as generic-collapse/output-diversity evidence rather than memorisation.

## Analysis and interpretation

Results will be reported by system and separately for target-use, cross-domain, and robustness prompts. Individual qualitative dimensions remain visible alongside the joint pass rate.

The comparison will report observed quality and efficiency differences with uncertainty rather than combining them into a single score or declaring an arbitrary universally acceptable trade-off. A deployment decision would require a real context such as traffic, cost, latency requirements, and tolerance for quality differences; that decision is outside this experiment.

The research project succeeds by producing a fair, reproducible, and honestly interpreted comparison, including if prompting matches or outperforms fine-tuning.
