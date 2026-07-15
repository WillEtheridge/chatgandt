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
| 6. Establish the reproducible environment | In progress | Python, dependencies, model revision, rented-GPU compatibility, generation profile, and seed policy are pinned and verified; the final training configuration remains |
| 7. Build the inference and capture harness | Completed | Specification 1.2 passed four adversarial reviews; implementation, 40 tests, real base/adapter CPU inference, and the two-runtime CUDA end-to-end diagnostic all pass |
| 8. Implement schema validation | Completed | Specification 1.3 is implemented; the exact schema, strict parser, stable diagnostics, deterministic serializer, 33 focused tests, and complete 73-test regression suite pass |
| 9. Create the prompt-development set | Completed | Twenty exact user prompts and closed metadata are reviewed, canonically stored, digest-bound as version 1, and verified before model generation |
| 10. Develop and version the five-shot prompt | Completed | Initial System B prompt v1 is deterministically assembled from reviewed instructions and five frozen examples, digest-bound, schema-checked, and measured at a 2,319-token paired input overhead |
| 11. Run Systems A and B on development prompts | In progress | Prompt assets, base-only A/B mapping, master seed, and complete paired 40-attempt schedule are frozen and verified; the GPU run and analysis remain |
| 12. Conduct the Stage 2 readiness review | Not started | Confirmation that the model, harness, validator, prompt baseline, and records are ready for formal evaluation design |

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

## Stage 3 — Design and freeze the evaluation

- Create an anchored qualitative rubric for human and LLM-judge scoring.
- Define the held-out test categories.
- Write, review, and freeze the held-out prompts.
- Freeze the five-shot prompt before held-out evaluation.
- Define the blind pairwise evaluation procedure.
- Finalise memorisation, input-token, latency, and response-length measurement procedures.

### Stage 3 exit condition

The final evaluation procedure is documented and the held-out prompts are frozen before training begins.

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

Follow the frozen [development A/B Runpod runbook](development-ab-runbook.md) to execute and retrieve the 40-attempt run, record its cost, and terminate all paid resources before inspecting model quality.
