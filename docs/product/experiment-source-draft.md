# ChatG&T experiment: comprehensive source draft

This document deliberately contains more material than the public Experiment page should use. Its purpose is to hold the complete experimental story in one place before editorial compression. It separates the question, experimental design, development process, evaluation method, controls, and limitations so the public version can remain concise without becoming incomplete or imprecise.

## The experiment in one sentence

We used ChatG&T's demanding response contract to compare two realistic ways of controlling a small language model: a deliberately developed five-shot prompt and LoRA-based supervised fine-tuning.

## The plain question

How do strong prompting and LoRA fine-tuning compare when they are asked to produce the same structured, useful and stylistically distinctive behaviour?

## The formal question

How does LoRA-based supervised fine-tuning compare with a strong five-shot prompt in producing schema-valid, useful, metaphorically coherent, and stylistically consistent ChatG&T responses on unseen prompts, and what trade-offs does it introduce in prompt-token usage and latency?

## Why this was worth testing

ChatG&T asks a language model to perform several tasks at once. It must understand the user’s underlying request, provide a useful answer, translate that answer into a cocktail metaphor, express the metaphor as a plausible recipe, and return the whole response in a strict JSON structure that the frontend can render.

A detailed prompt and a fine-tuned adapter are two credible ways to pursue this behaviour. They place the engineering work in different places: one supplies instructions and examples at inference time; the other uses supervised examples to adapt the model before inference.

The experiment was not simply asking whether fine-tuning “worked”. It compared two practical strategies for producing the same application behaviour:

1. guide the untouched model with a detailed five-shot prompt; or
2. adapt the same base model with supervised fine-tuning and use a minimal runtime prompt.

The comparison covered both response quality and operational cost without assuming that either strategy would win. Fine-tuning could improve structure, quality, both or neither. It could also reduce recurring prompt context while increasing generation time or introducing substantial upfront work. Measuring those outcomes separately kept the question informative even if the quality result was mixed.

## The object being evaluated

A ChatG&T response is a cocktail recipe that carries an answer to the user’s real request. The cocktail presentation is not decoration added after an ordinary answer. The advice, metaphor, ingredients, method, and garnish should form one coherent response.

The product contract required a JSON object with four fields:

- a title;
- an ingredient list containing structured amount, unit, and name values;
- a list of method steps; and
- a garnish.

The schema enforced the structure mechanically. Qualitative evaluation then considered three separate questions:

1. **Underlying-answer quality:** Did the response correctly and usefully fulfil the user’s actual request, including material constraints?
2. **Metaphorical coherence:** Did the cocktail metaphor meaningfully express that answer rather than merely surround it with drinks vocabulary?
3. **Recipe-style execution:** Did the output read as a coherent and plausible cocktail recipe?

A full response passed only when it was schema-valid and received an acceptable score on all three qualitative dimensions. Good formatting could not compensate for bad advice, and strong advice could not compensate for an unusable response object.

## The base model and technical baseline

The project selected Qwen2.5-1.5B-Instruct as the base model after reviewing model size, licence, instruction-following quality, context length, LoRA support, ecosystem maturity, and deployment feasibility. The model was pinned to a specific revision and verified through local and rented-GPU checks.

The inference environment, BF16 runtime, tokenizer, generation profile, seed policy, capture harness, and structural validator were established before the final experiment. The harness retained raw output, token counts, generation timing, model and prompt identities, and the exact configuration associated with every response.

This mattered because the experiment depended on comparing treatments rather than comparing different runtime implementations. Both the prompt-engineered and fine-tuned systems needed to pass through the same capture and validation path.

## Developing a strong prompting baseline

The prompting baseline was developed before fine-tuning and before the final held-out prompts were authored. It was intended to be a credible alternative, not a weak control designed to make fine-tuning look better.

Twenty frozen development prompts were used to compare four prompt versions. Every version kept the same five worked examples. Version 2 replaced the short closing reminder with a detailed checklist. Version 3 replaced that prose checklist with a recent concrete JSON skeleton. Version 4 compressed the main instructions while retaining the examples and skeleton, but regressed under the predefined quality ordering.

The predeclared local selection rule chose version 3 because it produced the most full-response passes on the development workbench. Token count was a tie-breaker only after behavioural quality, so the shorter but weaker version 4 was not selected. No fifth version was written after seeing the results.

Version 3 did not dominate every later measure. In the pinned BF16 confirmation it produced 12 schema-valid responses and five full passes from 20 prompts. Pinned version 1 had produced nine schema-valid responses and six full passes. Version 3 remained frozen because it won the declared selection rule; the mixed transfer result was retained rather than used to reopen prompt development.

The selected `five-shot-v3` prompt was then frozen. Its five examples remained separate from the supervised training examples and were included in later exposure and response-similarity checks.

## Freezing the evaluation before training

The evaluation protocol was designed and frozen before the supervised dataset was created. This reversed a common failure mode in small model projects: train a model first, inspect what it does, and then invent the criteria by which it appears successful.

Before training began, the project fixed:

- the research question;
- the four system configurations;
- the response schema;
- the qualitative rubric and acceptable-score threshold;
- the definition of a full response pass;
- the held-out population architecture;
- the primary B-versus-C comparison;
- the automatic, qualitative, pairwise, efficiency, and uncertainty measurements;
- the evaluator roles and human-calibration procedure;
- the contamination and response-similarity checks; and
- the rule that final outputs could not restart development.

The exact held-out prompts did not yet exist. The protocol specified only their coverage requirements, authoring rules, excluded sources, withheld domains, and review process. This allowed the evaluation design to be fixed without giving dataset authors or model developers access to the future test questions.

## Building the supervised dataset

The supervised corpus contained 200 accepted examples. Each example paired a user request with a complete schema-valid ChatG&T response, metadata, provenance, and independent qualitative review.

The dataset covered five intent families:

1. advice and decision support;
2. explanation and technical understanding;
3. low-stakes emotional support;
4. creative generation; and
5. short-form transformation.

Coverage also varied input form, task complexity, constraints, target use, breadth, and robustness pressure. The aim was to teach the complete joint behaviour rather than fill the dataset with easy format demonstrations.

The accepted examples were divided into 160 training examples and 40 validation examples. A fixed 40-example pilot subset was drawn only from the training split. Scenario groups, rather than individual records, were assigned to splits so that surface-level variants of the same underlying problem could not appear in both training and validation.

The dataset was authored, reviewed, contamination-checked, versioned, and frozen before the exact held-out prompts were written. The five examples in the prompting baseline were also reassessed against the final data-quality standard and kept unchanged.

## Authoring the held-out population

After the dataset and five-shot prompt were frozen, the project authored exactly 60 final prompts. They covered the same five broad intent families while remaining separate from training, validation, prompt-development, and worked-example material.

The held-out population crossed several forms of coverage:

- five intent families;
- target-use, cross-domain, and robustness reporting slices;
- questions, direct requests, and statements or fragments;
- standard and composed complexity;
- ordinary compatible constraints;
- three robustness roles; and
- three withheld subject domains.

Every prompt was reviewed for scope, answerability, ambiguity, natural phrasing, metadata accuracy, and scoring feasibility before any system answered it. Exact and bounded lexical comparison against prohibited project prompts produced no flags. The final records, quota report, audit, and manifest were then frozen with no model responses present.

The 60 prompts were deliberately authored rather than randomly sampled from production traffic. They form a controlled test population, not a statistical representation of all future users.

## Pilot training

Before the full adapter search, the project ran a mechanical LoRA pilot using the 40-example training-only pilot subset and the complete validation split. The pilot verified that the training implementation worked: losses remained finite, only the intended adapter parameters changed, memory stayed within its gate, checkpoints saved and reloaded correctly, and the base model remained frozen.

The pilot adapter then answered ten development prompts. It changed the outputs but produced no schema-valid responses. This result did not trigger changes to the supervised examples, evaluation rubric, or held-out boundary. It showed that a mechanically successful training run was not evidence of successful application behaviour.

## The bounded adapter search

The full search allowed three first-round candidates and, only if the first round produced a specific diagnosis, at most two second-round candidates. There could be no sixth configuration. Each candidate represented a written hypothesis, and its configuration was frozen before it ran.

The first three candidates tested:

1. a full-corpus anchor;
2. greater repeated exposure; and
3. a broader LoRA target across the attention projections.

Every candidate trained on the same frozen training data and used the same separate validation data. Each trajectory saved a checkpoint after every epoch. The lowest complete-validation-loss checkpoint represented that trajectory, but validation loss was not allowed to rank different candidates against one another. Generated behaviour, rather than teacher-forced loss, determined viability.

The selected checkpoint from every candidate answered the same ten spent-development prompts with a minimal prompt, fixed generation settings, and paired per-prompt seeds. Structural validation ran first. Candidate identity was hidden while every schema-valid response was scored for underlying-answer quality, metaphor, and recipe execution.

A candidate was viable only if it met all three predeclared gates:

- at least 8 of 10 responses were schema-valid;
- at least 7 of 10 responses were full passes; and
- every intent family contained at least one full pass.

Candidate 3 was the strongest first-round candidate. It produced 10 schema-valid responses and six full passes across all five families. It missed the full-pass threshold by one response. The no-winner rule therefore selected no viable or product-quality adapter.

The pattern of failure was specific: Candidate 3 consistently produced the ChatG&T format, metaphor, and recipe style, but still made substantive mistakes in the underlying answer. This diagnosis justified the bounded second round.

Candidate 4 extended LoRA to all attention and MLP projections. Candidate 5 retained Candidate 3’s adapter shape but weighted ingredient-name and method-string tokens more heavily during training. Neither improved the complete behavioural result enough to pass the unchanged gate. The search stopped without a sixth candidate or a relaxed threshold.

## Choosing the diagnostic adapter

No adapter passed the product-quality gate. Candidate 3 was nevertheless frozen as the sole adapted treatment for the held-out experiment because it was the most informative diagnostic candidate: it had perfect structure, joint-best full-pass performance, complete family coverage and a simpler adapter than Candidate 4.

This decision did not promote Candidate 3 into a production winner. It allowed the final experiment to answer a narrower question: what had the strongest bounded fine-tuning treatment changed relative to strong prompting?

The adapter was selected before held-out generation. Final results could describe its behaviour, but they could not replace it, restart training, relax the earlier gate, or retroactively select it for deployment.

## The four final systems

The final evaluation used a two-by-two design:

| System | Model state | Prompt treatment | Role |
| --- | --- | --- | --- |
| A | Untouched base model | Minimal prompt | Untreated reference |
| B | Untouched base model | Five-shot v3 | Strong prompting treatment |
| C | Candidate 3 adapter | Minimal prompt | Fine-tuning diagnostic |
| D | Candidate 3 adapter | Five-shot v3 | Combined diagnostic |

The primary practical comparison was B versus C. It compared two complete strategies:

- strong prompting with the untouched model; and
- fine-tuning with almost no recurring instruction.

Because both the prompt and adapter state changed, B versus C does not isolate the causal effect of one variable. Systems A and D completed the two-by-two context, showing the untreated base and the combined treatment. The primary research question was still about the practical strategy comparison rather than a factorial estimate of separate main effects.

## Running the held-out evaluation

The complete final run generated 240 responses: four systems answering each of the 60 frozen prompts.

The run used:

- one matched RTX 4090;
- the pinned Qwen2.5-1.5B-Instruct revision;
- the frozen BF16 generation profile;
- batch size one;
- master seed `20260715` and the frozen seed policy;
- the exact prompt and adapter assets bound to each system; and
- one sampled response per system and prompt.

Every first attempt was retained. Invalid JSON, schema failures, weak answers, and isolated generation errors were experimental results. They were not repaired, regenerated, extracted from surrounding prose, or replaced with better-looking attempts.

Once generation began, only mechanical failures that invalidated the run itself—such as identity mismatch, evidence corruption, fatal CUDA failure, or budget breach—could stop execution. Output quality could not.

## Structural evaluation

Every response first passed through the strict parser and JSON Schema validator. The evaluation recorded:

- scheduled and completed attempts;
- JSON validity;
- schema validity;
- stable structural failure labels;
- input and generated-token counts;
- raw output length; and
- synchronized model-generation time.

Schema-invalid responses remained in the full 60-prompt denominator and automatically failed the complete-response criterion. They were not assigned invented qualitative scores because the qualitative rubric assumed a renderable ChatG&T object.

## Qualitative evaluation

Every schema-valid response was evaluated once on the three frozen qualitative dimensions. The primary automated evaluator saw only:

- the user prompt;
- the candidate response;
- the frozen rubric; and
- the required scoring schema.

It did not see the system identity, prompt treatment, adapter state, other systems’ responses, development results, token counts, latency, or aggregate result.

Each dimension received a score from 1 to 3, with 2 as the minimum acceptable score. Scores could not compensate for one another. A response with an excellent metaphor but an incorrect underlying answer still failed the complete-response criterion.

The automated judge was calibrated on six frozen packets before production judging. Its imperfect agreement with those anchors was recorded rather than used to replace the judge after final outputs existed.

## Human calibration

After the primary judgements were sealed, the project author independently reviewed a predetermined sample of eligible responses and B-versus-C pairs. This sample measured agreement with the automated evaluator; it did not overwrite the primary scores.

The human sample was intentionally described as calibration rather than ground truth. It involved one project-author rater and was not statistically powered to estimate public preference. Weak agreement would reduce confidence in evaluator-derived quality claims without affecting mechanical schema results.

## Blind pairwise comparison

For prompts where both B and C produced schema-valid responses, the automated evaluator also received a blinded pair. Response order was balanced deterministically. The evaluator was asked which response better fulfilled the prompt while sustaining a coherent and natural cocktail-recipe response, with a tie available when neither held a meaningful advantage.

If only one system produced a schema-valid response, that system won the end-to-end comparison mechanically. If neither did, the result was recorded as both failed. Conditional preference and end-to-end outcomes were reported separately so structural eligibility could not be mistaken for subjective preference.

## Efficiency measurements

The experiment measured:

- rendered input tokens;
- generated tokens;
- visible output tokens;
- raw response length; and
- synchronized model-generation latency.

The primary efficiency comparison used paired C-minus-B differences on the same prompts. The latency measure covered the model-generation call in the experimental environment. It excluded model loading, tokenisation, decoding, persistence, network time, application rendering, cold starts, and production tail latency.

Prompt-token reduction could therefore support a recurring-context claim, but it could not automatically be presented as equivalent savings in latency, total serving cost, or complete user-perceived response time.

## Uncertainty

Every system attempted the same authored population of 60 prompts. The analysis reported observed counts and effect sizes rather than relying on a single winner label.

Matched B-versus-C differences used paired bootstrap resampling. Pairing preserved the fact that both systems answered the same prompt. The resulting interval described how much the measured difference changed when prompt pairs were resampled from the authored population.

Overall binary rates received Wilson intervals. Small diagnostic slices were reported as counts and rates without significance claims. The project did not run null-hypothesis tests or search multiple subgroups for favourable findings.

Because each system produced only one response per prompt, the experiment did not estimate within-prompt stochastic variation. A multi-seed evaluation would be a separate experiment rather than a replacement for the retained first attempts.

## Contamination and response similarity

The experiment distinguished two questions:

1. Did a held-out prompt duplicate project development or supervised material before generation?
2. Did a generated response suspiciously reproduce a worked example or training response after generation?

The checked-in Stage 5 evidence records exact and bounded lexical comparison against 231 prohibited project prompts. It produced no threshold flags. The complete set was also reviewed for scope, answerability, natural phrasing, metadata accuracy and scoring feasibility before any system answered it.

The frozen Stage 3 protocol specified broader semantic, metadata-assisted and reviewer-separation controls. The repository does not contain enough Stage 5 execution evidence to claim that every one of those broader controls ran. The public account should therefore state only the exact and bounded lexical check supported by the held-out audit and retain this evidence gap as a limitation.

After generation, every response was compared with worked-example responses, training responses, and other outputs from the same system. Exact equality, lexical neighbours, and semantic neighbours formed a review set. Exposure status remained explicit: B and D saw worked examples, while C and D had access to the training examples through the adapter.

Similarity flags were treated as evidence for review, not proof of memorisation. The audit could not inspect the base model’s unknown pretraining corpus or establish global novelty.

## Reproducibility and evidence integrity

The project bound the model, tokenizer, prompts, adapter, generation settings, seed policy, schemas, rubric, and evaluation assets to versioned files and digests. Training runs saved checkpoint identities, loss records, frozen-base checks, reload evidence, and hardware measurements. Generation runs retained manifests, raw responses, timing, tokens, and inspection results.

The local evidence system protects against accidental drift and makes the experiment internally reproducible. It is not independent third-party attestation: a maintainer with control of the repository and execution machine could alter code and evidence together. Stronger provenance claims would require an external trust anchor such as protected CI and signed artifacts.

For the portfolio page, the useful claim is therefore modest: the experiment was deliberately frozen, versioned, reproducible from the recorded assets, and designed to prevent result-driven changes. It should not claim external certification.

## What the method can establish

The experiment can describe how the frozen prompting and fine-tuning strategies behaved:

- on the same 60 authored prompts;
- using the same base-model family and inference implementation;
- under the same hardware, generation profile, and seed policy;
- on retained first attempts;
- against a predefined structural and qualitative contract; and
- with prompt-token and generation-latency measurements collected by the same harness.

It can support statements about observed structural reliability, evaluator-derived quality, recurring prompt context, and matched generation time inside this experiment.

## What the method cannot establish

The experiment cannot establish:

- that fine-tuning is generally better than prompting;
- that the result transfers to larger or different base models;
- that 60 deliberately authored prompts represent all future users;
- that one sampled response estimates each system’s full stochastic behaviour;
- that the automated evaluator represents human or public preference;
- that the human calibration sample represents a user population;
- that measured generation latency equals production latency;
- that fewer prompt tokens translate directly into proportional cost savings;
- that response-similarity flags prove memorisation; or
- that Candidate 3 passed the product-quality gate.

## The portfolio story

The strongest professional signal is not simply that the project used LoRA. The work demonstrates a complete experimental practice:

- framing a falsifiable comparison;
- building a credible baseline;
- defining the product contract before optimising against it;
- designing data coverage and split isolation;
- preventing held-out leakage;
- bounding the search and respecting a no-winner rule;
- separating mechanical validity from subjective quality;
- calibrating an automated evaluator rather than presenting it as ground truth;
- retaining failures and first attempts;
- measuring operational trade-offs;
- reporting uncertainty; and
- limiting claims to what the evidence supports.

The public Experiment page should make these decisions legible without reproducing the project’s internal lifecycle records. Its job is to help an intelligent reader understand the question, trust the comparison, and know what the test can and cannot say before moving to Results.
