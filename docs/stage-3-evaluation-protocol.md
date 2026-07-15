# Stage 3 Evaluation Protocol

- **Protocol ID:** `chatgnt-evaluation-v1`
- **Status:** Frozen
- **Date:** 2026-07-15

This specification turns the Stage 3 evaluation decisions into an executable procedure. It governs dataset boundaries, later held-out authoring, judging, pairwise comparison, automatic measurements, uncertainty, and response-similarity checks. It deliberately contains no exact held-out prompts.

The machine-readable source is [`config/evaluation-protocol-v1.json`](../config/evaluation-protocol-v1.json). The held-out record schema, qualitative rubric, and retrieval calibration cases are separate versioned assets referenced from that file. An independent adversarial review must pass before any asset is labelled frozen.

Normative operational detail is split into reviewable companion records: [tooling selection](similarity-tooling-selection.md), [unseen controls](unseen-contamination-protocol.md), [qualitative calibration](qualitative-evaluation-protocol.md), [blind pairwise](blind-pairwise-protocol.md), [automatic analysis](evaluation-analysis-protocol.md), [response similarity](response-similarity-protocol.md), and [held-out authoring](heldout-authoring-protocol.md). This overview and those records share one protocol identity; a change to any one requires re-verification.

## Claim and timing boundary

“Unseen” means unseen within the observable ChatG&T project process. It does not mean absent from Qwen's unknown pretraining corpus.

The required order is:

1. Freeze this evaluation protocol after independent review.
2. Author and freeze training and validation data without exact held-out prompts in view.
3. Author the 60 held-out prompts to the frozen blueprint.
4. Collision-check, review, replace where authorised, and freeze those prompts.
5. Only then begin pilot or full model training.
6. Generate held-out outputs once the systems and evaluation assets are fixed.

Training or validation data must not be rewritten around a known test prompt. A colliding held-out candidate is replaced with the reason retained. No generated held-out response may influence the prompt set, model, training procedure, rubric, judging instructions, or system definitions.

## 1. Held-out architecture

The 60-prompt population and cross-cutting quotas are defined in [Evaluation population](evaluation-population.md). Every future prompt record must satisfy [`heldout-prompt-v1.schema.json`](../schemas/heldout-prompt-v1.schema.json) and the executable aggregate checks.

The three deliberately withheld domains are:

- `photography`;
- `tabletop_games`; and
- `pottery_ceramics`.

Each domain supplies one prompt in each of the five intent families. This creates the 5-by-3 cross-domain matrix and 15 prompts in total. All three topics are prohibited from worked examples, prompt-development scenarios, training data, and validation data. Incidental generic words such as “game” do not alone establish a topic violation; substantive subject matter, scenario metadata, or answer content about the withheld domain does.

This design provides depth across three withheld domains, not evidence from 15 independent subject areas. Cross-domain results must be described accordingly.

## 2. Prompt contamination and unseen review

### Sources checked

Every candidate held-out prompt is checked against:

- five-shot worked-example user prompts;
- the complete prompt-development set;
- the Stage 3 retrieval-calibration inputs;
- frozen training prompts;
- frozen validation prompts;
- accepted held-out candidates; and
- rejected held-out candidates, to prevent repeatedly proposing the same collision.

The project stores original text, UTF-8 SHA-256, normalized text, and normalized-text SHA-256. Normalization uses Unicode NFC, line-ending normalization, Unicode case-folding, outer trimming, and collapse of whitespace runs to one space. Punctuation is retained because quotes, code, paths, and punctuation can carry task meaning. A normalized exact match is an automatic collision candidate and requires the same independent second review as any rejection.

### Retrieval, not automated judgment

For every non-exact candidate, the tool retrieves and merges:

- the five closest lexical neighbours;
- the five closest semantic neighbours; and
- up to five metadata neighbours with exact normalized overlap in `topic`, `user_goal`, `requested_task_or_artefact`, `scenario_summary`, or `important_constraints`.

The merged record retains every signal and score that brought a neighbour into view. No lexical or semantic threshold automatically approves or rejects a prompt. Every candidate receives nearest neighbours even when all scores are low.

Lexical retrieval uses RapidFuzz 3.14.5 `fuzz.token_ratio`, which returns the maximum of token-set and token-sort similarity. It is fast, deterministic, MIT-licensed, and useful for reordered phrases and small substitutions. The token-set component can score one string very highly when its tokens are a subset of another; that is acceptable for candidate retrieval but is specifically **not** evidence of contamination by itself. See the [official RapidFuzz scorer documentation](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html#token-ratio).

Semantic retrieval uses [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. The model card identifies an Apache-2.0 licence, 384-dimensional sentence vectors, and semantic-search use. It has approximately 22.7 million parameters and is proportionate for fewer than 500 short English records.

The project loads the model through its already pinned Transformers and Torch dependencies. The exact implementation tokenizes with padding and truncation at 256 wordpieces, takes the last hidden state, performs attention-mask-weighted mean pooling, and L2-normalizes each vector. Cosine similarity then ranks corpus entries. This matches the model card's manual Transformers approach rather than relying on an implicit SentenceTransformers wrapper.

The 256-wordpiece limit is a real limitation: wordpieces are tokenizer units, and material after the limit is invisible to the embedding. Every item records its untruncated wordpiece count and a truncation flag. A deliberately over-limit supplied-text calibration case must exercise that path; any truncated real item also receives complete-text manual review alongside lexical and metadata retrieval. If future in-scope prompts routinely approach this limit, this protocol must be versioned rather than silently changing the model or truncation rule.

### Semantic collision rule

Shared domain, task form, response schema, recipe behaviour, or robustness mechanism is allowed. A prompt is a duplicated scenario only when the reviewer answers **yes** to all three questions:

1. Do the prompts have substantially the same user goal?
2. Do they contain substantially the same situation, concept, supplied material, or requested artefact?
3. Could the substantive answer be reused after changing only names, objects, wording, or other surface details?

All three yes means `reject`. A no means `allow`. Insufficient evidence means `uncertain`, never a forced answer.

For transformations, the shared operation “rewrite” is not enough; source material and communicative purpose determine overlap. For creative prompts, a shared artefact type is allowed, but a superficial theme substitution around the same brief is not. For robustness prompts, repeated pressure mechanisms are intentional; the underlying task must differ.

### Review and selection-bias control

The primary reviewer records each retrieved pair, three question answers, decision, and short rationale. Every rejection and uncertainty receives a second review. A deterministic 10% sample of accepted matrix slots also receives a second review. The audit sample is the six preassigned `heldout-v1-NNN` matrix prompt IDs with the lowest SHA-256 values of `contamination-audit-v1|20260715|preassigned_matrix_prompt_id`. A replacement cannot move a slot into or out of the audit.

The second reviewer sees the candidate, neighbour, and frozen rule but not the first decision or rationale. Agreement finalises the decision. Disagreement is adjudicated with both original rationales retained. If the available reviewers cannot resolve uncertainty, the conservative outcome is rejection and replacement.

Reviewer roles must be labelled honestly, such as `primary_llm_review`, `adversarial_llm_review`, or `human_review`. Two model sessions are not represented as two independent human experts.

The calibration asset deliberately includes exact duplicates, paraphrases, disguised duplicates, acceptable same-domain and same-operation pairs, repeated robustness pressure, a changed situation, and supplied code. Retrieval success means the intended neighbour appears in the top five; it does not mean the semantic allow/reject label has been inferred automatically.

## 3. Qualitative scoring

Only schema-valid outputs are eligible for qualitative scoring. A schema-invalid response fails the end-to-end full-response criterion without qualitative scores being imputed.

The normative rubric is [`evaluation-rubric-v1.json`](../config/evaluation-rubric-v1.json). It retains three holistic dimensions rather than creating a checklist of sub-scores:

1. underlying-answer quality;
2. metaphorical coherence; and
3. recipe-style execution.

Each dimension receives `1`, `2`, `3`, or `unable_to_assess`. A score of 2 is the minimum acceptable anchor. Scores do not compensate for one another. A full response passes only when it is schema-valid and all three dimensions are numeric scores of at least 2.

An essential compatible substantive/content constraint belongs to underlying-answer quality: materially missing it forces a score of 1. Requests to replace JSON/cocktail behaviour with prose, Markdown, XML, or an ordinary answer conflict with the frozen contract and are excluded. Structural requirements are not scored again.

`unable_to_assess` is reserved for genuine inability to judge, not mild uncertainty between adjacent scores. One fresh blinded judgment is requested. If that judgment supplies an integer, it resolves the missing dimension while both records remain. If it is also unable to assess, the dimension and full response remain unresolved and cannot count as a pass. The response remains in attempted/schema-valid denominators, receives an explicit unresolved count, and is excluded only from the resolved integer-score distribution and dimension-rate denominator, which must be shown.

## 4. Evaluators and calibration

### Honest roles

- A **primary LLM judge** scores every schema-valid output once in an isolated context containing only the user prompt, candidate response, frozen rubric, and scoring schema. System identity, prompt treatment, adapter state, other systems' responses, development results, and aggregate results are hidden.
- The project author provides a **human calibration score**, not a replacement headline score, on a fixed sample of 24 eligible response packets and 15 eligible B-versus-C pairs.
- A **fresh blinded judge** handles `unable_to_assess`. Any later adjudicator and its relationship to the author are recorded.
- Public Tasting Room voters remain separate, self-selected observational evidence.

[`judge-manifest-v1.json`](../config/judge-manifest-v1.json) freezes exact instructions/templates, OpenAI Codex/GPT-5-family selection, fresh no-tools contexts, fallback stop, renderer, and six calibration packets. The interface exposes neither a stable backend snapshot nor sampling controls; these remain unavailable rather than invented. Every judgment binds manifest and packet digests.

### Calibration sample

After structural validation but before scores are revealed, order each system-by-slice cell by SHA-256 of `human-response-calibration-v1|20260715|packet_id` and take up to two. For each system, fill a shortfall toward six from that system's remaining eligible packets in the same hash order. The achieved sample may be below 24 when a system has fewer than six eligible responses; report it rather than filling from another system.

For pairwise calibration, select five conditionally eligible B-versus-C pairs per reporting slice by SHA-256 of `human-pair-calibration-v1|20260715|prompt_id`, for 15 pairs. Fill a slice shortfall from remaining eligible pairs in global hash order. If fewer than 15 eligible pairs exist, score all and report the shortfall.

The human and LLM judge score independently. Human scores never silently overwrite LLM scores. Report per dimension:

- exact 1/2/3 agreement;
- binary acceptable (`>=2`) versus fail (`1`) agreement; and
- linearly weighted Cohen's kappa, or `undefined` with the reason when the statistic cannot be calculated.

Pairwise exact-choice agreement is also reported. No arbitrary agreement threshold retroactively validates or invalidates the experiment. Poor agreement limits confidence in judge-derived claims and is discussed prominently.

Twenty-four responses and 15 pairs are pragmatic coverage targets, not statistically powered validation samples or estimates of public preference.

## 5. Blinded B-versus-C pairwise procedure

System B versus System C is the primary strategy comparison. Pairwise packets are created only after all raw outputs and structural results are sealed.

For deterministic balanced presentation, sort all 60 prompt IDs by SHA-256 of `pairwise-order-v1|20260715|prompt_id`. Assign System B to Response A for the first 30 and System C to Response A for the remaining 30. Retain this assignment even when a pair is not conditionally eligible, and report the observed A/B balance among displayed pairs.

When both responses are schema-valid, the evaluator sees:

- the same user prompt;
- Response A and Response B rendered from parsed JSON with one deterministic, identical renderer; and
- the frozen question: “Which response better fulfils the prompt while sustaining a coherent and natural cocktail-recipe response?”

The primary LLM judge gives one judgment to every conditionally eligible pair. The normal choices are `response_a`, `response_b`, and `tie`. A tie is appropriate when neither response has a meaningful overall advantage, including when strengths differ without a clear winner. Length is not a criterion by itself. A genuine inability to judge is recorded as `unable_to_assess` and triggers one fresh blinded judgment; if it remains unresolved, it is shown separately and excluded from the resolved conditional denominator. No system label, token count, latency, qualitative score, or provenance is visible before the choice is sealed.

Two outcomes are retained:

- **Conditional preference:** both schema-valid, so the blinded choice determines B win, C win, or tie.
- **End-to-end outcome:** if only one output is schema-valid it wins; if neither is schema-valid record `both_failed`; if both are valid but judgment remains unresolved record `unresolved`; otherwise use the blinded choice.

Report B wins, C wins, and ties separately. Preference among decisive comparisons is supplementary and never hides ties or both-failed prompts. Reveal identities only after every judgment in that batch is immutable.

## 6. Automatic, efficiency, and uncertainty measurements

### Denominators and automatic checks

Each system has 60 scheduled attempts. Generation completion, JSON validity, schema validity, failure labels, output tokens, and raw character length come from the existing immutable harness and strict validator. Missing or failed attempts remain in the denominator and count as structural and full-response failures. No extraction, repair, constrained decoding, or retry changes the headline first attempt.

The formal evaluation extract is accepted only from an existing project-contained harness run whose canonical manifest, frozen prompts, responses, and complete inspection result all match their recorded digests. The ordinary harness inspector must accept all 240 attempts. Evaluation records are a deterministic projection of those response bytes, so caller-created run configurations or complete-looking output splices cannot become production evidence. The inspected manifest must prove the selected two-by-two design: A/C use the exact canonical empty `minimal-v1`, B/D use the exact deterministic and digest-frozen `five-shot-v3`, base model and runtime configuration are pinned, and adapter enablement is exactly A/B off and C/D on. The formal loader invokes the same canonical prompt-identity validators used during prompt development; a different but coherent five-example prompt retaining the v3 label is not the selected treatment and fails.

The normative aggregate includes the implementation and every repository source that determines this formal treatment: `chatgnt/harness.py`, `chatgnt/configuration.py`, `chatgnt/prompting.py`; `config/model.toml`, `config/model-files.json`, `config/generation.toml`, and `config/inference.toml`; the exact `config/prompts/minimal-v1.json` and `config/prompts/five-shot-v3.json` assets; and `config/systems/evaluation-abcd-v1.json`. These are in addition to the evaluation validator, schemas, tests, and analysis specifications already bound by the manifest. The list is deliberately limited to sources that select or interpret model, runtime, prompt, adapter/system, scheduling, and evidence behaviour for the two-by-two run.

Report for each system:

- attempted, completed, JSON-valid, schema-valid, and full-pass counts and rates;
- each dimension's conditional resolved acceptability and all-60 end-to-end success, with structural failures separated rather than assigned score 1;
- unresolved judge counts;
- structural failure labels;
- input tokens, generated tokens, visible output tokens, and raw characters; and
- synchronized generation latency under the frozen procedure in [Evaluation metrics](evaluation-metrics.md).

Efficiency summaries include count, mean, median, and interquartile range for tokens; latency additionally reports standard deviation. C-minus-B paired token and latency differences use only prompts with both measurements; excluded pairs and achieved `n` are reported.

### Uncertainty

Overall binary rates receive 95% Wilson score intervals. The three pairwise outcome proportions are reported with counts and individual Wilson intervals; these intervals are descriptive and do not model the three categories jointly. A decisive-only preference rate may receive a Wilson interval using the number of decisive comparisons as its denominator.

Matched C-minus-B differences use 10,000 paired percentile resamples with seed `20260715`. Binary rates resample all 60 prompt IDs; continuous means resample the achieved matched IDs with resample size equal to achieved `n`. Medians and median differences are descriptive only.

Intent-family, reporting-slice, input-form, and complexity results are counts and rates used diagnostically. They do not receive confidence intervals or significance claims because their samples are small. The project performs no null-hypothesis significance tests and no multiple-comparison fishing. Observed effect sizes and uncertainty answer the research question.

One sampled output per system and prompt does not estimate within-prompt stochastic variation. Any multi-seed study is a separately versioned secondary experiment and cannot replace unfavourable primary generations.

## 7. Memorisation and response similarity

Prompt contamination asks whether the **evaluation task** duplicates project data before generation. Memorisation checking asks whether a **generated response** suspiciously reproduces the authored answers after generation. They are related but not interchangeable.

Every held-out response may be compared with all five-shot worked-example responses and frozen training responses, but attribution retains actual exposure: B/D see worked responses and C/D see training responses; A sees neither. Unexposed collection comparisons are diagnostic controls and cannot support a project-training memorisation claim. Checks use:

1. normalized complete-response SHA-256 equality;
2. the five closest RapidFuzz lexical neighbours; and
3. the five closest MiniLM semantic neighbours.

Response checks freeze one complete-text view: normalized field-labelled title, ingredient amounts/units/names, every method step, and garnish. Invalid output uses normalized complete raw text. Exact identity, lexical retrieval, and semantic retrieval all operate on this same representation so evidence cannot change meaning between checks.

Two synthetic response-calibration packets require the same-task target to outrank a structure-similar hard distractor in lexical and semantic retrieval. They are excluded from project datasets. Passing them confirms only that the frozen complete-text view and retrieval implementation behave as intended on those fixtures.

Exact equality is a high-priority flag, not proof of training-data memorisation, because the base model or a common phrase could produce the same text. Lexical and semantic scores only retrieve suspicious neighbours. Reviewers then consider distinctive phrase overlap, shared ordering and substantive content, whether generic schema language explains the match, and how much editing would be required to transform the reference into the output.

The report distinguishes `exact_match`, `suspicious_similarity`, and `reviewed_not_suspicious`, includes source collection, system, exposure status, examples, and rationales, and never claims to measure all memorisation or identify what appeared in base-model pretraining. A separate within-system comparison flags repeated titles, methods, ingredient structures, or advice across different prompts as generic collapse/output-diversity evidence, not reference memorisation.

## 8. Held-out authoring, replacement, and freeze

### Authoring roles and inputs

Held-out authors receive only the frozen population, quotas, exclusions, withheld domains, metadata schema, and authoring procedure. They do not receive model outputs. Training and validation are already frozen and available only to the collision tooling/reviewer, not as templates for test writing.

Author candidates in a staging file with stable candidate IDs. Complete metadata before collision review. Metadata is a retrieval aid and reporting label; it must describe the prompt rather than be revised after observing a system response.

### Candidate sequence

For each candidate:

1. Check target-population scope, stable answerability, ambiguity, and likely qualitative scorable-ness.
2. Validate the record schema and the current aggregate quota ledger.
3. Run exact, lexical, semantic, and metadata retrieval against every required source.
4. Complete primary semantic review and any required independent review.
5. Check the withheld-domain rule and the crossed matrix.
6. Accept into the staging set or append an immutable replacement-log entry.
7. Re-run internal collision retrieval as the held-out staging set grows.

Allowed replacement reasons are closed vocabulary: `scope_or_answerability`, `quota_or_metadata`, `exact_collision`, `semantic_scenario_collision`, `withheld_domain_violation`, `internal_heldout_collision`, and `ambiguous_or_unscorable`. Each log entry stores candidate ID, text and identity digests, metadata, reason, retrieved neighbour IDs and scores, reviewer records, timestamp, and replacement candidate ID when available. Rejection for expected model difficulty or observed output is impossible because no held-out generation exists.

### Freeze gate

Before freezing, all 60 records must pass their JSON Schema, exact-identity, cross-cutting quota, family/slice, robustness, constraint, and 5-by-3 withheld-domain checks. Every collision record and audit review must be resolved. An independent reviewer then challenges ambiguity, leakage, balance, and scoring feasibility without generating responses.

The freeze package contains canonical prompts and metadata, source-collection identities, retrieval configuration and embedding-model revision, collision reports, accepted audit sample, rejection/replacement log, review records, schemas, protocol config, and SHA-256 digests. Any later change creates a new version and repeats the contamination audit. Silent in-place edits are prohibited.

## 9. Executable evidence and current status

Run:

```bash
uv run --frozen python scripts/verify_evaluation_protocol.py
uv run --frozen python scripts/verify_evaluation_protocol.py --semantic
uv run --frozen python -m unittest discover -s tests
```

The ordinary verifier checks version identities, schemas, calibration records, asset digests, and lexical retrieval. `--semantic` additionally downloads or loads the exact pinned MiniLM revision and reports expected-neighbour recall at five. Retrieval calibration is a smoke test for candidate discovery, not an automated proof that the semantic judgments are correct.

Immediately before the eventual frozen transition, these ordinary and semantic commands plus the complete test suite are rerun against the exact reviewed aggregate. Their commands, implementation digests, output digests, timestamps, and zero exit statuses are stored in a closed `stage3-verification-evidence-v1` artifact. That stored artifact supports later integrity and reproducibility checks only: loading it never authorizes a lifecycle transition.

The only canonical review/freeze command is:

```bash
uv run --frozen python scripts/orchestrate_stage3_review.py \
  --mode dry-review \
  --evidence-output reviews/stage3-verification-v1-YYYYMMDDTHHMMSSZ.json
```

`dry-review` executes all three gates and stores their evidence but never changes protocol status. After a passing independent review, the same command uses `--mode freeze` with `--review-artifact-output`, `--review-id`, `--reviewer-identity`, and `--report`. It validates the current candidate first, executes all gates itself, and receives a deliberately unpersisted in-process authorization only after every gate passes. It then builds and validates the review artifact and status-only transition and writes the protocol last. A controlled gate failure returns no authorization and cannot reach the transition. `capture_stage3_verification.py` remains a useful standalone evidence command, but evidence it wrote—or any other stored evidence—cannot later be presented as freeze authority.

For every gate the live runner records stdout and stderr separately, defines the combined-output view as stdout bytes followed by stderr bytes, and records all three digests, exit status, positive monotonic duration, UTC interval, implementation identity, and the pinned local environment. Later loading checks the current manifest, runner/verifier/test identities, environment, output digests and pass semantics. These checks can detect inconsistency or later mutation within the assumed local repository boundary; they do not establish that the original execution happened on an independently trusted machine.

This is reproducible local provenance, not independent attestation. A person with write access to the repository and machine can alter code, clocks, outputs, and hashes together. The orchestration command prevents accidental or API-level use of stale evidence, but it is not a defence against a malicious local maintainer. Claims requiring independent attestation need an external trust anchor, such as protected CI running from a reviewed commit and publishing immutable logs, plus verified commit/tag signatures or equivalent signed provenance. Without that external control, the honest claim is only that the checked-in evidence is internally reproducible under the local trust assumption.

The protocol completed the review process recorded in [Stage 3 review summary](stage-3-review-summary.md) with no unresolved experiment-validity blocker. The lifecycle status and final evidence identities are stored in the machine-readable protocol and review artefacts. Any change to a normative asset requires a new protocol version before later project data or outputs are inspected.
