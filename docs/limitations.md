# Limitations and Validity Register

This document records threats to the interpretation and generalisation of the ChatG&T experiment. The aim is to control important risks where practical, measure relevant uncertainty, and disclose what remains unresolved.

Planned controls are commitments for later stages, not claims that the controls have already been implemented.

## Claim boundary

The experiment can establish how the four ChatG&T systems compare under the documented model, data, prompting, inference, hardware, and evaluation conditions.

It cannot establish that fine-tuning is universally better or worse than prompting. The appropriate conclusion will be:

> This is what happened in the ChatG&T experiment under these conditions.

## Key concepts

- A **confounding factor** offers an alternative explanation for an observed difference.
- A **bias** systematically influences data creation, judging, or measurement.
- A **source of uncertainty** makes the observed result noisy or imprecise.
- A **limitation** restricts the populations or situations to which the result can generalise.

## Internal validity

### Strategy comparison versus isolated causal effect

System B differs from System C in both its prompt and its adapter state. Their comparison answers which engineering strategy performs better, not the isolated causal effect of one variable.

The complete two-by-two design provides additional controls:

- A versus B examines the five-shot prompt on the base model.
- A versus C examines the adapter without a ChatG&T prompt.
- B versus D examines the adapter when both systems receive the same five-shot prompt.
- C versus D examines whether the fine-tuned model still benefits from the prompt.

The final report must distinguish the B-versus-C strategy comparison from these more controlled comparisons.

### Unequal information exposure

The five-shot system sees five examples at inference, while the fine-tuned system may see 150–300 examples during training. This reflects the real engineering strategies but does not answer what would happen if both systems received equal quantities of information.

The prompt examples, training-example count, and creation process must be disclosed.

### Unequal development effort

Prompt wording, example selection, dataset creation, checkpoint selection, and LoRA settings all receive engineering attention. A weakly developed baseline or an over-optimised fine-tune would distort the comparison.

Controls:

- version prompts, datasets, and training runs;
- develop systems on non-test data;
- record the rationale for material revisions;
- give the five-shot prompt a genuine development process; and
- freeze all systems before held-out evaluation.

Prompt development used a predeclared four-version ceiling and lexicographic selection rule. The selected v3 prompt transferred closely on structure but not on full-response quality, and no fifth version is authorised from the spent development set.

### Inference configuration

Temperature, sampling, chat templates, generation limits, quantisation, random seeds, and adapter loading can change quality and latency.

Controls:

- use the same base model and tokenizer;
- match inference settings wherever applicable;
- record every material setting;
- record whether the adapter is merged or dynamically loaded; and
- disclose unavoidable differences.

## Data contamination and memorisation

### Held-out leakage

The held-out test set ceases to be held out if its prompts or outputs influence prompt wording, training examples, hyperparameters, checkpoint selection, or evaluation design.

Controls:

- freeze and version the held-out set;
- do not inspect held-out outputs during development;
- use development and validation data for iteration;
- check for exact and semantic overlap; and
- record any accidental exposure.

### Near-duplicate scenarios

Different wording can express the same underlying scenario. Exact-string matching is therefore insufficient. Prompt and response overlap must be reviewed semantically as well as mechanically.

### Unknown base-model pretraining

The original pretraining data is not fully observable. The experiment can investigate reproduction of the project’s fine-tuning examples, but it cannot claim that the base model never encountered similar material.

Memorisation claims must be limited accordingly.

## Evaluation validity

### Development transfer evidence

Prompt v1 and v3 were confirmed in separate rented-GPU sessions, while prompt selection used a local quantised Ollama runtime. Their development counts can diagnose transfer but are not a matched latency comparison or a statistically reliable prompt ranking.

The development qualitative evaluation used one blinded LLM-judge session whose exact backend snapshot was unavailable. These scores guide engineering and dataset design; final conclusions require the frozen Stage 3 procedure and separately labelled human calibration.

### Qualitative subjectivity

Underlying-answer quality, metaphorical coherence, and recipe-style execution require judgment.

Controls:

- use short, anchored rubric questions;
- blind system identities;
- calibrate evaluators with examples;
- permit `unable_to_assess` rather than forcing guesses;
- examine agreement between human and LLM judges; and
- retain meaningful disagreements.

### LLM-judge and author bias

An LLM that helps create training examples may prefer similar language when judging outputs. The project author may also favour responses that match their own examples and expectations.

Controls:

- use a separate judging context;
- provide only the user prompt, candidate response, and frozen rubric;
- hide system identities;
- record the judge model and version;
- label LLM-judge and human scores separately; and
- use human judgments to calibrate the LLM judge.

These controls reduce but do not eliminate dependence between authorship and evaluation.

### Pairwise presentation effects

Evaluators may prefer the first or second response, longer answers, confident language, or elaborate metaphors.

Response order will be randomised, rendering will be matched, and order balance will be recorded.

## Statistical and measurement uncertainty

### Finite evaluation sample

A limited set of prompts can only estimate performance on the target population. Counts, percentages, and uncertainty intervals will be reported. Results will be separated by evaluation slice, with small subgroup results interpreted cautiously.

### Stochastic generation

One sampled generation may be unusually strong or weak. The primary comparison uses one response per system and prompt with paired, deterministically derived seeds. This preserves a broad evaluation population but does not estimate within-prompt sampling variance. Any later multi-seed stability study will be a separately reported secondary run rather than selective replacement of primary responses.

### Limited evaluators

One evaluator does not represent population preference. The number of evaluators, judgments per prompt, and agreement statistics must be reported. Exact judge counts remain deferred.

## External validity

The findings are limited by:

- one base model and model size;
- one LoRA approach and a small number of training configurations;
- one hand-authored dataset;
- English-language prompts;
- single-turn interaction;
- low-stakes use;
- a concise JSON response contract;
- five defined intent families; and
- the measured training and inference environments.

Claims outside the evaluation population are not supported by the experiment.

## Efficiency limitations

### Tokens and latency measure different things

A five-shot prompt uses more input tokens, but latency also depends on prefix caching, quantisation, adapter implementation, output length, hardware, inference software, and warm-up state.

The primary experiment reports complete rendered-input tokens, generated tokens, and synchronized `model.generate()` latency. It does not claim time-to-first-token, throughput, application latency, or tail-latency results. Static-prefix reuse is disabled, and the base and adapted strategies use separately warmed stable runtimes on matched hardware.

### Hardware-specific results

Generation-latency results apply directly only to the measured environment. Other hardware and serving systems may behave differently.

### Upfront and recurring costs

Training time and adapter size are measurable, but human dataset-authoring and experimentation effort are difficult to reduce to a comparable cost figure. These costs will be described rather than combined into a manufactured total.

## Public evaluation limitations

Tasting Room participants and prompts are self-selected. Participants may vote multiple times, recognise stylistic patterns, or judge entertainment differently from the curated rubric.

Public votes are supplementary observational evidence and do not replace the frozen held-out evaluation.

## Deferred operational decisions

Later stages must determine and record:

- held-out sample size and quotas;
- operational definition of semantic overlap;
- number of human and LLM judges;
- evaluator-calibration procedure;
- uncertainty calculations;
- any separately scoped multi-seed stability study; and
- deployment-specific application and cold-start measurements.
