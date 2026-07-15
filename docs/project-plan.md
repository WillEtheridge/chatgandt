# ChatG&T Project Plan

This is the living roadmap for the ChatG&T project. It records the order of work, current status, expected outputs, and the conditions for moving between stages.

The plan is distinct from:

- [Experiment plan](experiment-plan.md): what the experiment is testing;
- [Decision log](decisions.md): consequential choices and their rationale; and
- [Learnings log](learnings.md): reusable concepts and practical lessons.

## Status key

- **Not started:** Discussion or work has not begun.
- **In discussion:** The topic is being explored but has not been agreed.
- **Agreed:** The decision has been made and recorded.
- **In progress:** Practical work has begun but the expected outcome is not yet complete.
- **Completed:** The planned practical work and its records are complete.

## Stage 1 — Frame the experiment

| Step | Status | Expected outcome |
| --- | --- | --- |
| 1. Define the research question | Agreed | A falsifiable, measurable, comparative, scoped, neutral, and generalisation-focused primary question |
| 2. Define the systems compared | Agreed | Precisely specified experimental conditions and fair comparisons |
| 3. Define the behavioural contract and JSON schema | Agreed | A clear description of a valid ChatG&T response and a machine-checkable schema |
| 4. Define safety and exception behaviour | Agreed | Rules for sensitive, dangerous, and format-breaking prompts |
| 5. Define the evaluation population | Agreed | Agreed categories of in-domain, out-of-domain, and adversarial prompts |
| 6. Define metrics and interpretation | Agreed | Hard and soft measures, a joint response pass, pairwise comparison, and descriptive quality–efficiency analysis |
| 7. Record limitations and confounding factors | Agreed | An explicit account of what the experiment can and cannot establish |

### Stage 1 exit condition

We can state exactly what is being tested, which systems are being compared, what constitutes a valid and good response, and how success will be recognised.

## Stage 2 — Establish the technical baseline

| Step | Status | Expected outcome |
| --- | --- | --- |
| 1. Audit hardware and deployment constraints | Completed | A documented account of available compute, memory, storage, operating environment, and likely hosting target |
| 2. Define model-selection criteria | Completed | Agreed requirements covering model size, licence, instruction quality, context length, LoRA support, ecosystem maturity, and deployment feasibility |
| 3. Research and shortlist candidate models | Completed | An evidence-backed comparison using current model cards and documentation |
| 4. Run model feasibility checks | Completed | Loading, generation, the LoRA lifecycle, and a representative BF16 training workload passed on a rented 24 GB RTX 3090 with substantial VRAM headroom |
| 5. Select and record the base model | Completed | Qwen2.5-1.5B-Instruct is selected, pinned, justified, and confirmed across local and rented-GPU feasibility checks |
| 6. Establish the reproducible environment | Completed | Python, dependencies, model revision, rented-GPU compatibility, generation profile, and seed policy are pinned and verified; pilot training hyperparameters remain a later experimental decision |
| 7. Build the inference and capture harness | Completed | Specification 1.2 passed four adversarial reviews; implementation, 40 tests, real base/adapter CPU inference, and the two-runtime CUDA end-to-end diagnostic all pass |
| 8. Implement schema validation | Completed | Specification 1.3 is implemented; the exact schema, strict parser, stable diagnostics, deterministic serializer, 33 focused tests, and complete 73-test regression suite pass |
| 9. Create the prompt-development set | Completed | Twenty exact user prompts and closed metadata are reviewed, canonically stored, digest-bound as version 1, and verified before model generation |
| 10. Develop and version the five-shot prompt | Completed | Four frozen prompt versions were compared under a predeclared stopping and selection rule; v3 is selected after v4 regressed |
| 11. Run Systems A and B on development prompts | Completed | Pinned v3 confirmation produced 12/20 schema-valid and 5/20 full-pass responses; transfer is structurally close but qualitatively mixed |
| 12. Conduct the Stage 2 readiness review | Completed | Stage 2 passes with no Stage 3 blocker; one non-portable adapter test fixture is a hard gate before the next formal model run |

### Stage 2 boundaries

Stage 2 will not:

- create or inspect final held-out test outputs;
- fine-tune the model;
- claim final comparative results;
- freeze final test-set quotas; or
- present development metrics as headline findings.

### Expected Stage 2 records

- Hardware and constraints record
- Model-selection report and decision
- Reproducible dependency environment
- Inference and capture harness
- Executable JSON Schema and validator tests
- Prompt-development set
- Versioned five-shot prompts
- Baseline experiment records

### Stage 2 exit condition

The selected base model runs reproducibly in the available environment; raw generations and operational measurements are captured; schema validation works; and Systems A and B have documented development baselines produced without using the held-out test set.

**Exit decision:** Passed on 2026-07-15. See [Stage 2 readiness review](stage-2-readiness-review.md).

## Stage 3 — Design and freeze the evaluation protocol

| Step | Status | Expected outcome |
| --- | --- | --- |
| 1. Confirm the inherited experimental boundary | Completed | Stage 2 closes with the model, v3 prompt, generation profile, seed policy, harness, validator, and development evidence frozen; no held-out output has been generated |
| 2. Define the held-out sample architecture | Completed | The 60-prompt cross-cutting blueprint fixes intent families, reporting slices, input forms, observable task complexity, ordinary constraints, and three robustness roles without authoring prompt text |
| 3. Operationalise “unseen” and contamination controls | Completed | Exact, lexical, semantic, and metadata retrieval; substantive collision rule; independent review/audit; calibration cases; and the three-domain crossed policy are specified and executable |
| 4. Finalise the qualitative scoring rubric | Completed | Versioned anchored 1–3 criteria for underlying-answer quality, metaphorical coherence, and recipe-style execution include `unable_to_assess`, constraint handling, eligibility, and the joint-pass rule |
| 5. Define evaluator calibration and judge roles | Completed | LLM, project-author human, fresh-judge, and public roles; deterministic 24-response and 15-pair calibration samples; shortfalls; and agreement reporting are specified honestly |
| 6. Define the blinded pairwise procedure | Completed | B-versus-C eligibility, deterministic 30/30 response order, rendering, ties, identity reveal, conditional preference, and end-to-end outcomes are fixed |
| 7. Finalise automatic, efficiency, and uncertainty measurements | Completed | Denominators, schema and quality reporting, token/latency aggregation, Wilson intervals, paired bootstrap, missingness, and diagnostic slices are fixed |
| 8. Define memorisation and response-similarity checks | Completed | Exact, lexical, semantic, and review procedures distinguish suspicious generated-response overlap from prompt contamination without claiming proof |
| 9. Define held-out authoring and review | Completed | Authoring after supervised-data freeze, executable quotas, collision review, closed replacement reasons, reviewer separation, and freeze-package requirements are specified |
| 10. Adversarially review the evaluation protocol | Completed | Six fresh LLM review contexts challenged the package; material treatment, coverage, leakage, provenance, and measurement findings were resolved and the proportionality boundary is recorded |
| 11. Freeze and version the evaluation protocol | Completed | The canonical live gates passed and froze the 52-asset protocol aggregate with one final verification and review record |
| 12. Conduct the Stage 3 readiness review | Completed | The final review finds no blocker to supervised-data creation under the frozen evaluation rules |

### Stage 3 boundaries

Stage 3 will not:

- author the exact held-out prompts;
- create training or validation examples;
- generate model responses for held-out prompts;
- revise the frozen five-shot baseline or response contract;
- begin pilot or full fine-tuning;
- present development results as estimates of held-out performance; or
- treat one evaluator or one model judge as representative of public preference.

### Expected Stage 3 records

- Held-out sample and quota plan
- Operational unseen and contamination protocol
- Final qualitative rubric and evaluator-calibration procedure
- Blind pairwise evaluation specification
- Automatic, efficiency, and uncertainty analysis plan
- Memorisation and similarity-check procedure
- Held-out authoring, collision-review, replacement-log, and freeze procedure
- Versioned evaluation protocol, configuration, and identity checks
- Stage 3 readiness review

### Stage 3 exit condition

The complete evaluation protocol is documented, adversarially reviewed, and frozen before training or validation examples are authored. It specifies how the later held-out prompts will be created and checked after those datasets freeze, and removes the need to make new result-affecting decisions after seeing model outputs.

## Stage 4 — Build and freeze dataset v1

| Step | Status | Expected outcome |
| --- | --- | --- |
| 1. Confirm the Stage 4 boundary and unit of data | Completed | One canonical single-turn source record stores the user prompt, schema-valid response object, metadata, and provenance; deterministic Qwen messages are derived, while exact held-out prompts and model training remain excluded |
| 2. Define dataset size and split targets | Completed | Dataset v1 targets 200 accepted examples, a scenario-isolated 160/40 training-validation allocation, and a representative 40-example training-only pilot; achieved counts yield to group isolation and token balance is reported |
| 3. Define the dataset coverage blueprint | Completed | Five balanced intent families cross 140/30/30 target-use, breadth, and robustness examples; fixed input-form, complexity, compatible-constraint, and robustness-role targets are combined with topic concentration limits and a response-diversity audit |
| 4. Define the authoring and provenance policy | Completed | Frontier-model-assisted synthetic drafting, restricted source use, project-author responsibility, compact per-example provenance, and separate append-only workflow history define how creation, revision, review, acceptance, and rejection remain attributable |
| 5. Define the dataset record schema and validators | Completed | The reviewed dataset-v1 configuration, three JSON Schemas, strict JSONL loader, authoring and freeze validators, lifecycle-gated ordered renderer, split-deviation path, read-only CLI, and isolated synthetic contract suite are implemented and verified alongside all 128 frozen existing tests |
| 6. Define scenario identity and split isolation | Completed | A deterministic coverage-aware dynamic program assigns whole single-family scenario groups to validation, targets 8/32 per family, exposes any non-exact allocation for separate approval, and selects an exactly 40-example representative training-only pilot without mutating source records |
| 7. Create the authoring guide and quality rubric | Completed | A frozen guide and machine-readable rubric separate automated hard gates from three non-compensatory `pass`/`revise`/`reject` judgments, anchor every dimension, map all reason codes, and define bounded batch, revision, review, and project-author acceptance workflows |
| 8. Author candidate examples in reviewable batches | Not started | Approximately 220–240 original candidates are drafted in reviewable batches to produce 200 accepted examples without exact held-out prompts, model training, or generation-based selection pressure; the range is a planning estimate, not a quota |
| 9. Validate, review, and revise candidate examples | Not started | Every retained example passes the response schema and a recorded qualitative review; rejected or materially revised candidates retain reasons |
| 10. Audit duplication, contamination, and exclusions | Not started | Exact, lexical, semantic, metadata, and human-readable checks cover internal duplication, worked examples, development prompts, and the frozen withheld-topic policy |
| 11. Assign splits, select the pilot subset, and freeze dataset v1 | Not started | Scenario-isolated training and validation files, a representative training-only pilot subset, coverage reports, identities, and a versioned dataset manifest are sealed |
| 12. Conduct the Stage 4 readiness review | Not started | A proportionate review confirms dataset quality, coverage, isolation, provenance, and frozen identities before exact held-out prompt authoring begins |

### Stage 4 boundaries

Stage 4 will not:

- author or inspect exact held-out prompts;
- fine-tune the model or generate outputs from a candidate adapter;
- use model performance to select, rewrite, or discard supervised examples;
- revise the frozen evaluation protocol, response contract, model, or five-shot baseline;
- include substantive photography, tabletop-games, or pottery/ceramics content in training or validation;
- place the same scenario or a surface-level paraphrase across training and validation; or
- describe validation results as held-out evidence.

### Expected Stage 4 records

- Dataset blueprint and coverage targets
- Dataset authoring and provenance policy
- Versioned supervised-example schema and validators
- Scenario-identity and split-isolation procedure
- Authoring guide and quality rubric
- Candidate, revision, and rejection records
- Frozen training and validation JSONL files
- Coverage, schema, quality, duplication, and exclusion reports
- Frozen 40-example training-only pilot subset
- Dataset manifest and Stage 4 readiness review

### Stage 4 exit condition

Training data, validation data, and the pilot subset are reviewed, contamination-checked, versioned, and frozen without the dataset authors knowing the exact held-out prompts.

## Stage 5 — Author and freeze the held-out set

- Author exactly 60 prompts to the frozen sample blueprint without generating system responses.
- Classify and verify every cross-cutting quota.
- Compare each candidate against worked examples, development prompts, training data, validation data, and other held-out candidates using the frozen exact, lexical, semantic, metadata, and recorded-review procedure.
- Reject and replace collisions only for predeclared reasons, preserving an auditable replacement log.
- Adversarially review ambiguity, coverage, contamination, and scoring feasibility.
- Freeze and version the prompts, metadata, review evidence, identities, and digests.

Stage 5 will not modify the frozen systems, evaluation rules, training data, or validation data; fine-tune the model; or generate held-out responses.

### Stage 5 exit condition

The exact held-out set is balanced, reviewed, demonstrably separate from project development and supervised data under the frozen rules, and sealed before any fine-tuning begins.

## Stage 6 — Train and select a candidate adapter

The frozen supervised corpus contains 200 accepted examples. The training split targets 160 examples and is the only split that updates model weights; the validation split targets 40 and measures loss and behaviour without gradient updates. The fixed pilot is a 40-example subset of training rather than an additional split. Scenario isolation takes precedence over the target allocation, so any approved small deviation changes the achieved train and validation counts reported below without changing their roles.

1. Repair the clean-clone adapter test fixture and pass the complete preflight suite before the next formal model run.
2. Exercise the end-to-end LoRA workflow on the fixed 40-example pilot subset, including rendering, tokenisation, masking, optimisation, checkpoint saving, adapter reload, and recorded diagnostics.
3. Use the pilot only to correct training mechanics and reject clearly unsuitable configurations. Do not rewrite supervised examples around Qwen outputs or inspect held-out responses.
4. Predeclare the small set of justified candidate training configurations and their selection rule before full training.
5. Train every candidate configuration on the complete frozen training split, targeting 160 examples. Compute validation loss and permitted validation diagnostics on the complete separate validation split, targeting 40 examples, without updating weights from them.
6. Use the predeclared validation evidence and already-spent development set to select one candidate adapter. Do not use held-out prompts or responses for selection.
7. Verify, identify, and freeze the selected adapter before generating any held-out response.
8. Record configurations, dataset and renderer identities, checkpoints, training and validation losses, permitted diagnostics, costs, failures, and decisions.

Stage 6 does not perform a final refit on all 200 accepted examples. Once the validation records have influenced configuration or checkpoint selection, training on them would remove the clean validation boundary and create a different final fitting procedure. The selected adapter is therefore one trained on the complete achieved training split.

### Stage 6 exit condition

A documented adapter trained on the complete frozen training split has been selected using only predeclared validation and spent development evidence, then frozen without using held-out prompts or responses to alter the model, dataset, prompt, or training procedure.

## Stage 7 — Conduct the held-out evaluation

- Run every agreed system using controlled inference settings.
- Calculate structural and operational metrics.
- Conduct blinded qualitative scoring and pairwise comparisons.
- Check for memorisation and suspicious similarity.
- Analyse failures, trade-offs, and uncertainty.

### Stage 7 exit condition

The research question can be answered using recorded evidence, including negative or inconclusive results.

## Stage 8 — Build the public experience

- Build the Spirit Guide interaction.
- Build the randomised, blind Tasting Room comparison.
- Build the Lab explanation.
- Build the Results presentation.
- Capture votes without revealing model identity before selection.
- Deploy the model adapter and application.

### Stage 8 exit condition

Visitors can use ChatG&T, take part in a fair blind comparison, and understand the experiment and its results.

## Stage 9 — Publish the case study

- Explain the motivation, method, and major decisions.
- Present successes, failures, and inconclusive findings honestly.
- Document limitations and possible follow-up experiments.
- Prepare the project for portfolio, interview, and LinkedIn use.

### Stage 9 exit condition

The project tells a clear, evidence-backed story about what was built, what was learned, and what fine-tuning changed.

## Next step

Continue Stage 4 by authoring and reviewing the 10-candidate calibration batch in Step 8 under the frozen guide. Do not author exact held-out prompts, query Qwen, or train a model yet. Fix the non-portable adapter unit-test fixture before the first Stage 6 formal model run.
