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

- freeze evaluation rules before supervised data, then freeze the held-out set before training;
- do not inspect held-out outputs during development;
- use development and validation data for iteration;
- check exact, lexical, semantic, and metadata neighbours under a recorded substantive rule;
- second-review every rejection and uncertainty plus a deterministic audit of accepts; and
- record any accidental exposure.

### Near-duplicate scenarios

Different wording can express the same underlying scenario. Exact-string matching is therefore insufficient. Prompt overlap is reviewed semantically as well as mechanically. RapidFuzz can inflate subset matches and the pinned MiniLM model truncates at 256 wordpieces, so scores retrieve candidates rather than decide them.

Only three subject domains are deliberately withheld. Their 15 crossed prompts test several capabilities within those domains but do not amount to 15 independent topic-transfer tests.

The MiniLM semantic retriever sees at most 256 wordpieces. Pre-truncation counts, flags, lexical/metadata neighbours, and manual complete-text review control this limitation but cannot make the omitted suffix part of the embedding. The calibration collection is small and synthetic; recall on it verifies plumbing rather than estimating real collision-detection accuracy.

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

One evaluator does not represent population preference. Every eligible output receives one LLM-judge score, while one project-author human calibration covers 24 response packets and 15 pairs. Exact and weighted agreement will be reported, but this remains a limited calibration rather than representative human preference evidence.

The 24 and 15 counts are pragmatic coverage choices rather than statistically powered sample sizes. Persistently unresolved qualitative or pairwise judgments remain visible with achieved denominators; they may reduce effective sample size.

### Judgment and response-review chronology

Judgment and response-similarity review records retain UTC timestamps and are bound to the frozen generation and packet identities, but this Stage 3 protocol does not yet enforce one cross-artifact temporal order for every primary judgment, second judgment, human calibration judgment, response-similarity review, and final analysis event. Reviewer/session separation and predecessor links remain executable; the remaining chronology control is disclosed future hardening rather than a claim that repository timestamps independently prove when every review occurred. Before production evaluation is presented as externally attested, a later version should enforce those event-order relationships or obtain them from an independently controlled judging service or CI ledger.

### Response-similarity interpretation

Similarity to a project response is not proof of a causal memorisation mechanism. Reference exposure differs by system: B/D see worked responses, while C/D see training responses. Cross-collection matches for unexposed systems are diagnostic controls. Within-system repetition is reported separately as generic collapse rather than folded into memorisation claims.

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

### Synthetic supervised dataset

The 200 active supervised examples are synthetic and were primarily authored and reviewed by frontier-model agents under project-master supervision. Separate author and reviewer roles, recorded revisions, deterministic acceptance, contamination checks, and a frozen validation split improve traceability, but they do not provide independent human authorship or external quality assurance. Two explicit pre-freeze amendments also mean dataset v1.2 is an active view over retained history rather than an untouched first-pass corpus.

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

## Remaining deferred decisions

Later stages must determine and record:

- any separately scoped multi-seed stability study; and
- deployment-specific application and cold-start measurements.
