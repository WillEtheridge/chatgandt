# Experiment page claim ledger

This ledger is the factual control for the public Experiment page. It follows the repository's canonical reading order and distinguishes completed evidence from planned protocol. Public copy should use the plain formulation while retaining the stated boundary.

## Governing story

| Public claim | Evidence | Boundary |
| --- | --- | --- |
| ChatG&T was designed as a controlled comparison between prompt engineering and LoRA fine-tuning. | `pyproject.toml:1-5`; `docs/experiment-plan.md:3-23` | The repository does not record a previous product that depended on a long prompt. |
| The five-shot prompt was created as a realistic alternative to fine-tuning. | `docs/experiment-plan.md:7-19, 42-46`; `docs/decisions.md:165-185` | Do not describe it as an incumbent prompt that the project set out to replace. |
| The experiment asked about quality and efficiency without assuming that fine-tuning would win. | `docs/decisions.md:141-163`; `docs/experiment-plan.md:3-19` | Prompt-token reduction was one measured trade-off, not the origin story. |
| The exact research question compares schema validity, usefulness, metaphor, style, prompt tokens and latency. | `docs/experiment-plan.md:3-5` | Use the recorded question verbatim when labelling it as the formal question. |

## Behavioural contract

| Public claim | Evidence | Boundary |
| --- | --- | --- |
| A ChatG&T response must answer the user's request through a coherent metaphorical cocktail recipe in strict JSON. | `docs/behavioural-contract.md:3-31`; `docs/decisions.md:58-84` | The cocktail form is part of the answer, not decoration applied after it. |
| The object contains exactly `title`, `ingredients`, `method` and `garnish`. | `docs/experiment-plan.md:50-56`; `docs/decisions.md:63-74` | Valid JSON alone is not enough; unexpected fields and wrong shapes fail the schema. |
| A full pass requires schema validity plus acceptable underlying-answer quality, metaphorical coherence and recipe-style execution. | `docs/decisions.md:187-208`; `docs/experiment-plan.md:72-76` | The three quality scores cannot compensate for one another or for structural failure. |
| The target population is English-language, single-turn, low-stakes and answerable from stable general knowledge without tools. | `docs/decisions.md:112-139`; `docs/experiment-plan.md:64-70` | Do not imply coverage of high-stakes, live, tool-dependent, multi-turn or non-English use. |

## Experimental design

| Public claim | Evidence | Boundary |
| --- | --- | --- |
| The design varied two interventions: adapter state and prompt treatment. | `docs/decisions.md:28-55`; `docs/experiment-plan.md:21-44` | The treatments necessarily differ; say conditions were matched wherever applicable, not identical. |
| A was base + minimal, B base + five-shot, C Candidate 3 + minimal, and D Candidate 3 + five-shot. | `docs/stage-7/execution-plan.md:12-16`; `docs/decisions.md:1958-1974` | C and D are diagnostic treatments because Candidate 3 failed the Stage 6 viability gate. |
| B versus C compared the two practical engineering strategies. | `docs/experiment-plan.md:34-40`; `docs/limitations.md:24-41` | It is not the isolated causal effect of fine-tuning because prompt and adapter state both change. |
| The complete two-by-two design provides context for prompting, adaptation and their interaction. | `docs/decisions.md:46-55`; `docs/limitations.md:24-35` | The project did not estimate a universal factorial effect beyond this experiment. |

## Stage 2: technical and prompt baseline

| Public claim | Evidence | Boundary |
| --- | --- | --- |
| Qwen2.5-1.5B-Instruct was selected against requirements defined before candidate research. | `docs/stage-2/model/model-selection-criteria.md:3-87`; `docs/stage-2/model/model-shortlist.md:1-29` | It was selected for experimental fit, not because it was expected to favour fine-tuning. |
| The model, tokenizer, environment, harness, generation settings and strict validator were pinned and verified before final evaluation. | `docs/stage-2/stage-2-readiness-review.md:14-28, 44-58` | Internal hashes support reproducibility inside the repository trust boundary, not external attestation. |
| A representative BF16 LoRA workload used 7.93 GiB peak reserved memory on a 24 GB RTX 3090. | `docs/stage-2/model/gpu-feasibility-check.md:41-70` | This was an infrastructure check, not ChatG&T training evidence. |
| Twenty development prompts were separated from later data and used to develop four prompt versions. | `docs/stage-2/stage-2-readiness-review.md:24-28`; `docs/stage-2/prompt-development/prompt-development-results.md:1-12` | Development results are diagnostics, not held-out performance estimates. |
| Version 3 won the frozen local selection rule; version 4 regressed, so prompt development stopped. | `docs/stage-2/prompt-development/prompt-development-results.md:20-31, 43-50` | Do not call v3 simply the strongest prompt. Its pinned-runtime transfer was mixed. |
| Pinned v3 produced 12/20 schema-valid and 5/20 full-pass responses. | `docs/stage-2/prompt-development/prompt-development-results.md:52-58`; `docs/stage-2/stage-2-readiness-review.md:30-42` | Pinned v1 had fewer schema-valid responses but one more full pass; the selection rule, not dominance on every measure, kept v3. |

## Stage 3: evaluation frozen before supervision

| Public claim | Evidence | Boundary |
| --- | --- | --- |
| The project decided how the systems would be tested before creating the training data. | `docs/project-plan.md:79-122`; `docs/stage-3/stage-3-readiness-review.md:8-12, 34-48` | This is the central chronology of the method. |
| The frozen plan covered the 60-prompt blueprint, quality rubric, evaluator roles, pairwise comparison, efficiency, uncertainty and similarity review. | `docs/stage-3/stage-3-readiness-review.md:34-48` | Exact held-out prompts and supervised examples did not yet exist. |
| Uncertainty used Wilson intervals and paired prompt-ID bootstrap resampling. | `docs/stage-3/stage-3-readiness-review.md:43-45`; `docs/limitations.md:140-154` | The intervals describe variation within an authored population and do not remove authoring bias. |

## Stages 4 and 5: supervised data and held-out separation

| Public claim | Evidence | Boundary |
| --- | --- | --- |
| The supervised corpus contained 200 terminally accepted examples, balanced at 40 per intent family. | `docs/stage-4/production/dataset-production-summary.md:1-10, 19-31`; `docs/stage-4/stage-4-readiness-review.md:14-27` | The data was synthetic and primarily authored and reviewed by frontier-model agents under project-master supervision. |
| The first deterministic allocation produced 160 training examples, 40 validation examples and a 40-example pilot drawn only from training. | `docs/stage-4/audit/dataset-v1.2-freeze.md:9-21`; `docs/stage-4/stage-4-readiness-review.md:22-25` | The pilot is not a third independent split. |
| Scenario groups were isolated across training and validation. | `docs/stage-4/audit/dataset-v1.2-freeze.md:11-21`; `docs/stage-4/stage-4-readiness-review.md:22-25` | This controls observable scenario overlap, not unknown pretraining exposure. |
| Exact held-out prompts were authored only after the prompt and supervised data were frozen, and before fine-tuning. | `docs/project-plan.md:176-191`; `docs/stage-5/stage-5-readiness-review.md:8-12` | The held-out set was authored, not randomly sampled from production traffic. |
| Heldout v1 contained exactly 60 prompts: 12 per intent family, with 30 target-use, 15 cross-domain and 15 robustness prompts. | `docs/stage-5/stage-5-readiness-review.md:14-28` | The three withheld domains do not establish general topic transfer. |
| Stage 5 compared the set with 231 prohibited project prompts and found no exact or bounded lexical flags. | `docs/project-plan.md:180-185`; `docs/stage-5/stage-5-readiness-review.md:25-28, 37-39`; `data/evaluation/heldout-v1/audit.json` | Do not claim that the checked-in Stage 5 evidence proves execution of the broader semantic and metadata-assisted protocol. |
| No model response was generated or inspected while heldout v1 was authored and frozen. | `docs/stage-5/stage-5-readiness-review.md:10-12, 25-28` | “Unseen” means unseen within observable project material, not necessarily absent from Qwen pretraining. |

## Stage 6: bounded adapter search

| Public claim | Evidence | Boundary |
| --- | --- | --- |
| A 40-example pilot proved the training mechanics but produced 0/10 schema-valid adapted responses. | `docs/stage-6/pilot-training-results.md:9-13, 15-56`; `docs/stage-6/pilot-behavioural-inspection-results.md:22-47` | Falling validation loss did not establish successful free generation. |
| The search allowed three first-round candidates and at most two second-round candidates, each tied to a written hypothesis. | `docs/stage-6/full-training-candidate-plan.md:1-13, 97-103` | No sixth candidate or post-hoc relaxation was permitted. |
| Validation loss selected checkpoints within trajectories; generated behaviour determined candidate viability. | `docs/stage-6/full-training-candidate-plan.md:105-144` | Lower validation loss did not make one candidate a better product system. |
| Viability required at least 8/10 schema-valid, 7/10 full passes and one full pass in all five families. | `docs/stage-6/full-training-candidate-plan.md:119-127` | These were engineering gates on a small diagnostic population, not confidence-qualified deployment rates. |
| Candidate results were C1 7/10 and 3/10; C2 9/10 and 4/10; C3 10/10 and 6/10; C4 9/10 and 6/10; C5 9/10 and 4/10 for structure and full passes respectively. | `docs/stage-6/full-training-candidate-selection-results.md:18-28`; `docs/stage-6/second-round-results.md:41-58` | None passed the complete gate. |
| No viable or product-quality adapter was selected. | `docs/stage-6/second-round-results.md:52-58, 78-80`; `docs/decisions.md:1945-1956` | Do not say “no production adapter”; Candidate 3 was later published and served as a diagnostic demonstration. |
| Candidate 3 was bound before held-out generation as the most informative diagnostic treatment. | `docs/decisions.md:1958-1980`; `docs/stage-7/execution-plan.md:12-16` | Held-out results could characterise it but could not select it, restart tuning or reverse the gate failure. |

## Stage 7: one frozen held-out run

| Public claim | Evidence | Boundary |
| --- | --- | --- |
| Four systems each answered the same 60 prompts, producing 240 first attempts. | `docs/stage-7/execution-plan.md:8-24`; `docs/stage-7/primary-results.md:7-11` | One response per prompt does not estimate within-prompt sampling variance. |
| The run used one matched RTX 4090, BF16, batch size one, master seed 20260715 and paired per-prompt sampling. | `docs/stage-7/execution-plan.md:18-24`; `config/generation.toml:1-75`; `config/inference.toml:1-17` | Hardware-specific latency should not be generalised to other serving systems. |
| Every first attempt counted; outputs were not repaired, extracted, regenerated or replaced. | `docs/stage-7/execution-plan.md:18-37`; `docs/decisions.md:1987-1999` | Mechanical failure before evidence existed had a separate recovery policy. |
| Structural validation ran before qualitative judging, and all 143 schema-valid responses were judged. | `docs/project-plan.md:229-236`; `docs/stage-7/primary-results.md:15-22` | Schema-invalid responses remained failures in the full 60-prompt denominator. |
| The primary judge was identity-blinded and calibrated before generation; project-author calibration was sealed and reported separately. | `docs/stage-7/execution-plan.md:26-37`; `docs/stage-7/judge-calibration-assessment.md:1-26`; `docs/stage-7/primary-results.md:28-48` | Model-based quality judgments are not objective ground truth or representative human preference. |
| Input tokens, generated tokens and synchronised `model.generate()` latency were measured. | `docs/stage-7/primary-results.md:50-58`; `docs/limitations.md:184-198` | The timing excludes loading, tokenisation, network and application rendering. |
| Generated responses were checked against worked examples, training responses and other outputs using exact, lexical and MiniLM neighbours followed by blinded review. | `docs/stage-7/response-similarity-results.md:1-30` | Review flags are not proof of memorisation, and Qwen's unknown pretraining corpus cannot be inspected. |

## Claim boundary

The public page may say:

> The experiment tells us what these four frozen systems did on the same authored prompt population under the recorded conditions.

It must not say:

- fine-tuning is generally better or worse than prompting;
- B versus C isolates a single causal effect;
- 60 authored prompts represent all users;
- one automated judge represents human preference;
- the human calibration establishes public preference;
- fewer prompt tokens guarantee lower cost or latency;
- response-similarity flags prove memorisation;
- Candidate 3 passed the product-quality gate; or
- held-out prompts were absent from the base model's unknown pretraining data.

Sources: `docs/limitations.md:7-13, 22-67, 69-96, 98-178, 184-204`.

## Editorial controls

- Ask “What are we actually trying to say?” before each passage.
- Use Claim → Evidence → Meaning → Boundary.
- Prefer counts over percentages where both fit.
- Separate deterministic structure from subjective quality.
- Explain technical terms where they matter; omit them where they do not.
- Use British English.
- Do not invent an origin story.
- Do not describe v3 as universally strongest.
- Keep “no viable adapter” and “Candidate 3 diagnostic treatment” together.
- Make the freeze order visible: evaluation protocol → supervised data → exact held-out prompts → training → one held-out run.
