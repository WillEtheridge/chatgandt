# Experiment Plan

## Primary research question

> How does LoRA-based supervised fine-tuning compare with a strong five-shot prompt in producing schema-valid, useful, metaphorically coherent, and stylistically consistent ChatG&T responses on unseen prompts, and what trade-offs does it introduce in prompt-token usage and latency?

## Why this question matters

The experiment is intended to determine how supervised fine-tuning compares with the strong prompt-engineered solution that would realistically be built without training. It evaluates a hard technical requirement—generating schema-valid JSON—alongside response quality and recurring inference efficiency.

The question is designed to be:

- falsifiable;
- measurable;
- comparative;
- appropriately scoped;
- neutral about the outcome;
- focused on generalisation to unseen prompts; and
- capable of exposing quality–efficiency trade-offs rather than assuming that one system must be the universal winner.

## Systems compared

The experiment will use `Qwen/Qwen2.5-1.5B-Instruct` as the selected base model in a two-by-two design:

| System | Model | ChatG&T prompt | Role |
| --- | --- | --- | --- |
| A | Base model | None | Negative control |
| B | Base model | Detailed five-shot | Prompt-engineering system |
| C | Fine-tuned model | None | Fine-tuning system |
| D | Fine-tuned model | Detailed five-shot | Combined system |

All four systems will be evaluated offline. The public Tasting Room will primarily compare System B with System C, with response order randomised and model identities hidden until after voting.

The comparisons answer different questions:

- **A vs B:** What effect does the detailed five-shot prompt have on the base model?
- **A vs C:** What effect does the LoRA adapter have without a ChatG&T prompt?
- **B vs D:** What additional effect does the adapter have when both systems receive the detailed five-shot prompt?
- **C vs D:** Does the fine-tuned model still benefit from the detailed five-shot prompt?
- **B vs C:** How does prompt engineering alone compare with fine-tuning alone as a product strategy?

“No ChatG&T prompt” means that Systems A and C receive an explicit system message with empty content followed by the user message. Qwen’s official chat template otherwise injects its vendor identity message when no system message is supplied. The empty message suppresses that content without replacing the official template. The fine-tuned model will use the same base model with the trained LoRA adapter applied.

The detailed prompt used by Systems B and D will be supplied as the system message and will contain exactly five high-quality worked examples alongside the instructions and schema. It represents the prompt-engineered solution that would realistically be built if fine-tuning were unavailable. No additional vendor identity message will be included. The exact prompt and examples must receive a fair, documented development process and be frozen before use on the held-out test set.

For every generation, the experiment will capture the message array supplied to the tokenizer, the rendered chat-template text, and the resulting input-token count. This makes runtime defaults visible and permits the prompt-token comparison to be reproduced.

Raw experimental outputs will not use JSON repair, automatic retries, or constrained generation. Inference controls will be defined before baseline evaluation.

## Normal-response contract

The normal response behaviour and structure are defined in the [ChatG&T behavioural contract](behavioural-contract.md).

Each normal response will be a JSON object containing exactly `title`, `ingredients`, `method`, and `garnish`. It will contain three to eight conceptual ingredients, and its method will contain two to five ordered preparation steps. Unexpected fields will cause a schema failure.

Exact character limits are deferred until a broader set of ideal examples has been examined. The project’s safety scope is described below.

## Safety scope

ChatG&T is a novelty fine-tuning experiment, not a general-purpose or professional advice service. The project will preserve rather than deliberately train away safety behaviour inherited from the base model, but it will not build a separate safety schema, routing system, or safety-specific training programme.

Professional, emergency, and crisis advice are outside the intended scope. Any concerning behaviour observed during testing will be documented as a limitation; the project will not claim that the model is safe for high-stakes reliance.

## Evaluation population

The intended prompt population, intent families, reporting slices, and exclusions are defined in [Evaluation population](evaluation-population.md).

The target population is limited to English-language, single-turn, low-stakes prompts answerable concisely using stable general knowledge without external tools. Results will be reported separately for target-use, cross-domain, and robustness prompts.

The test set will contain 60 prompts using the frozen cross-cutting blueprint in the evaluation-population record. Photography, tabletop games, and pottery/ceramics form the 5-by-3 project-withheld topic matrix. The operational project-unseen rule, collision controls, and authoring sequence are defined in the [Stage 3 evaluation protocol](stage-3-evaluation-protocol.md). Exact held-out prompts will be authored after training and validation data freeze but before any fine-tuning begins.

## Evaluation metrics

The structural, qualitative, pairwise, and efficiency measurements are defined in [Evaluation metrics](evaluation-metrics.md).

A full response passes only when it is schema-valid and receives at least an acceptable score for underlying-answer quality, metaphorical coherence, and recipe-style execution. System-level results will report observed quality and efficiency differences with uncertainty rather than collapsing them into one winner score or imposing an arbitrary deployment-acceptance threshold.

## Terms to operationalise

The qualitative terms in the research question are operationalised by the three dimensions in the evaluation metrics. A prompt is sufficiently **unseen within this project** when the frozen exact and retrieved semantic review finds that it does not duplicate the same user goal, substantive situation or artefact, and reusable answer content. This narrower statement does not claim absence from the base model's pretraining data.

## Limitations and validity

Threats to internal, evaluation, statistical, and external validity are recorded in [Limitations and validity register](limitations.md).

The experiment will control important risks where practical, measure relevant uncertainty, and disclose residual limitations. Its claims will remain specific to the documented model, dataset, prompts, inference environment, and evaluation population.
