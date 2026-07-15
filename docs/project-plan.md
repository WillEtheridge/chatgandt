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

## Stage 3 — Design and freeze the evaluation

| Step | Status | Expected outcome |
| --- | --- | --- |
| 1. Confirm the inherited experimental boundary | Completed | Stage 2 closes with the model, v3 prompt, generation profile, seed policy, harness, validator, and development evidence frozen; no held-out output has been generated |
| 2. Define the held-out sample architecture | Not started | A justified total size and quotas across intent families, reporting slices, input forms, difficulty, constraints, and robustness roles |
| 3. Operationalise “unseen” and contamination controls | Not started | Exact and semantic overlap rules for worked examples, development prompts, training data, validation data, and held-out prompts, with a documented review procedure |
| 4. Finalise the qualitative scoring rubric | Not started | Anchored 1–3 criteria for underlying-answer quality, metaphorical coherence, and recipe-style execution, including `unable_to_assess` and the joint-pass rule |
| 5. Define evaluator calibration and judge roles | Not started | Agreed human and LLM-judge responsibilities, calibration examples, judgment counts, disagreement handling, and agreement reporting |
| 6. Define the blinded pairwise procedure | Not started | Exact B-versus-C eligibility, response-order randomisation, tie handling, identity reveal, conditional preference, and end-to-end outcome rules |
| 7. Finalise automatic, efficiency, and uncertainty measurements | Not started | Frozen schema checks, token and response-length accounting, synchronized latency procedure, aggregation rules, confidence intervals, and reporting slices |
| 8. Define memorisation and response-similarity checks | Not started | Exact and semantic procedures for detecting suspicious overlap with worked examples and training responses without overstating what can be proven |
| 9. Author the held-out prompts to the frozen blueprint | Not started | A complete prompt set written without model generation, balanced against the agreed quotas, and separated from all development and training assets |
| 10. Adversarially review the evaluation package | Not started | Independent challenges to prompt coverage, ambiguity, leakage, rubric clarity, pairwise fairness, measurement validity, and executable feasibility before freeze |
| 11. Freeze and version all evaluation assets | Not started | Canonically stored prompts, digests, specifications, rubrics, procedures, and automated identity checks that cannot be silently edited after training begins |
| 12. Repair the clean-clone adapter test fixture | Not started | The adapter-loading unit test creates its own disposable fixture and the complete suite passes without relying on ignored local artefacts |
| 13. Conduct the Stage 3 readiness review | Not started | Confirmation that evaluation design and held-out prompts are frozen, executable, uncontaminated, and ready before pilot fine-tuning begins |

### Stage 3 boundaries

Stage 3 will not:

- generate model responses for held-out prompts;
- use held-out prompts to revise the five-shot baseline, response contract, or evaluation criteria;
- create fine-tuning examples from held-out scenarios;
- begin pilot training before the evaluation package is frozen;
- present development results as estimates of held-out performance; or
- treat one evaluator or one model judge as representative of public preference.

### Expected Stage 3 records

- Held-out sample and quota plan
- Operational unseen and contamination protocol
- Final qualitative rubric and evaluator-calibration procedure
- Blind pairwise evaluation specification
- Automatic, efficiency, and uncertainty analysis plan
- Memorisation and similarity-check procedure
- Reviewed and frozen held-out prompt set
- Versioned evaluation configuration and identity checks
- Clean-clone test-fixture correction
- Stage 3 readiness review

### Stage 3 exit condition

The complete evaluation procedure is documented and executable; the held-out prompts and every result-affecting scoring rule are frozen before training begins; contamination checks pass; and the project can run the later held-out comparison without making new interpretive decisions after seeing model outputs.

## Stage 4 — Run a pilot fine-tune

- Create approximately 30–50 original training examples.
- Review coverage, quality, variety, and consistency.
- Run the first LoRA fine-tuning experiment.
- Inspect training and validation loss alongside generated responses.
- Diagnose failures and record what was learned.

### Stage 4 exit condition

The complete training workflow has been exercised, and the pilot results provide evidence for how the full dataset and training setup should change.

## Stage 5 — Build and train dataset v1

- Expand the dataset to approximately 150–300 examples.
- Maintain distinct training and validation data.
- Document dataset composition and creation decisions.
- Run a small number of justified training experiments.
- Select a candidate adapter using validation evidence.

### Stage 5 exit condition

A documented candidate adapter is ready for the frozen held-out evaluation.

## Stage 6 — Conduct the held-out evaluation

- Run every agreed system using controlled inference settings.
- Calculate structural and operational metrics.
- Conduct blinded qualitative scoring and pairwise comparisons.
- Check for memorisation and suspicious similarity.
- Analyse failures, trade-offs, and uncertainty.

### Stage 6 exit condition

The research question can be answered using recorded evidence, including negative or inconclusive results.

## Stage 7 — Build the public experience

- Build the Spirit Guide interaction.
- Build the randomised, blind Tasting Room comparison.
- Build the Lab explanation.
- Build the Results presentation.
- Capture votes without revealing model identity before selection.
- Deploy the model adapter and application.

### Stage 7 exit condition

Visitors can use ChatG&T, take part in a fair blind comparison, and understand the experiment and its results.

## Stage 8 — Publish the case study

- Explain the motivation, method, and major decisions.
- Present successes, failures, and inconclusive findings honestly.
- Document limitations and possible follow-up experiments.
- Prepare the project for portfolio, interview, and LinkedIn use.

### Stage 8 exit condition

The project tells a clear, evidence-backed story about what was built, what was learned, and what fine-tuning changed.

## Next step

Begin Stage 3 Step 2 by defining the held-out sample architecture before writing any prompt text: total size, intent-family quotas, reporting slices, input-form coverage, difficulty, constraints, and robustness allocation. Fix the non-portable adapter unit-test fixture before the next formal model run and no later than the Stage 3 readiness review.
