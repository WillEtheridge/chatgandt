# How do prompting and fine-tuning compare?

**Experiment / Prompt engineering × LoRA fine-tuning**

ChatG&T takes an ordinary question and answers it as a metaphorical cocktail recipe. The recipe must still answer the question, make sense as a metaphor, and follow a fixed structure.

We compared two ways of getting the same small model to do that: showing it five examples in the prompt, or fine-tuning it on a larger set of examples.

**One base model / Four systems / 200 supervised examples / Five LoRA candidates / 60 held-out prompts / 240 first attempts**

## The research question

How does LoRA-based supervised fine-tuning compare with a strong five-shot prompt in producing schema-valid, useful, metaphorically coherent, and stylistically consistent ChatG&T responses on unseen prompts—and what trade-offs does it introduce in prompt-token usage and latency?

The question is deliberately neutral. Fine-tuning did not need to win for the experiment to be informative. It might improve the complete response, improve only part of it, reduce recurring prompt context, introduce a latency cost, or make no useful difference at all.

## 01 / 07 — Define the behaviour

The model had to produce the right object and put a good answer inside it.

Each response needed exactly four fields: a title, a list of measured ingredients, a sequence of preparation steps and a garnish. That structure could be checked automatically.

The content required judgement. Did the response answer the user’s real request? Did the cocktail metaphor carry that answer? Did the result read like a coherent recipe rather than ordinary prose pushed into JSON?

A full pass required all four parts: valid structure, an acceptable underlying answer, a coherent metaphor and convincing recipe execution. Good formatting could not rescue poor advice. A clever answer could not rescue an object the product could not interpret.

## 02 / 07 — Design the comparison

The experiment varied two things: whether the model had a LoRA adapter, and whether it received the five-shot prompt.

| | Minimal prompt | Five-shot prompt |
| --- | --- | --- |
| Untouched base model | A — untreated reference | B — prompt engineering |
| Candidate 3 adapter | C — fine-tuning diagnostic | D — combined diagnostic |

The four systems answer different questions. A against B shows what the prompt changes on the untouched model. A against C shows what the adapter changes without ChatG&T instructions. B against D and C against D show how prompting and adaptation behave together.

The practical comparison is B against C: a genuinely developed prompt versus a fine-tuned model with minimal recurring instruction. That comparison changes both the prompt and the adapter state, so it compares two complete engineering strategies. It does not isolate one universal causal effect of fine-tuning.

## 03 / 07 — Build a credible baseline

Fine-tuning was compared with a prompt that had received genuine development effort.

We selected Qwen2.5-1.5B-Instruct against requirements defined in advance: model size, licence, structured-output capability, LoRA support, reproducibility and affordable deployment. We then pinned the model and environment, verified the complete adapter lifecycle, built one inference and evidence-capture harness, and implemented a strict validator that did not repair broken output.

The prompt baseline was developed on a separate workbench of 20 frozen prompts. Four versions were allowed. Each inspected version became immutable, and a fifth version was not permitted after the fourth regressed.

Version 3 won the predeclared local selection rule. Its later pinned-runtime confirmation was mixed: it improved structural validity over version 1, but produced one fewer full pass. We kept version 3 because it won the rule we had set before seeing that result—not because it dominated every measure.

## 04 / 07 — Fix the test before training

We decided how the systems would be judged before creating the material used to fine-tune one of them.

The frozen protocol defined the 60-prompt evaluation blueprint, the meaning of a full pass, the qualitative rubric, the blinded B-versus-C comparison, evaluator calibration, token and latency measurement, uncertainty analysis and response-similarity review.

At this point there were no supervised examples and no exact held-out prompts. Freezing the rules first meant the data could not quietly redefine success, and the final model outputs could not decide how they ought to be scored.

The order mattered:

1. freeze the evaluation rules;
2. build and freeze the supervised dataset;
3. author and freeze the exact held-out prompts;
4. begin fine-tuning; and
5. run the held-out evaluation once.

## 05 / 07 — Keep the training data and test apart

The supervised corpus contained 200 accepted examples across five intent families. The first deterministic allocation placed 160 in training and 40 in validation. A 40-example pilot was drawn only from the training split.

Scenarios, rather than individual rows, were kept together so closely related versions of the same situation could not cross from training into validation. Every accepted response passed the JSON schema and a separate qualitative review.

Only after the supervised data and five-shot prompt were frozen did we write the 60 held-out prompts. They covered the same five intent families while varying target use, cross-domain transfer, robustness pressure, input form, complexity and constraints. The checked-in audit found no exact or bounded lexical flags against 231 prohibited project prompts.

The set was authored rather than randomly sampled. “Unseen” therefore means unseen within the project material we could inspect. It does not mean absent from the base model’s unknown pretraining data.

## 06 / 07 — Let the search end without a winner

The training search was small, written down in advance and allowed to fail.

A 40-example pilot first proved that the LoRA pipeline worked. Validation loss improved and the adapter changed the model’s output, but neither the base model nor the pilot adapter produced a schema-valid response on the ten-prompt behavioural check. A working training loop was not yet a working system.

The full search tested five hypotheses within a fixed three-plus-two allowance: use the complete corpus, increase repeated exposure, broaden LoRA across attention projections, extend it into the MLP projections, and increase the training weight of answer-bearing tokens.

Every candidate answered the same ten spent-development prompts. A candidate was viable only if at least eight responses followed the schema, at least seven passed the complete quality bar, and every intent family contained a full pass. Validation loss selected a checkpoint within each training run; generated behaviour decided whether the candidate was viable.

None of the five candidates passed. Candidate 3 produced ten schema-valid responses and six full passes across all five families, missing the quality gate by one. We did not lower the threshold or train a sixth candidate.

Candidate 3 was retained only as the most informative fixed treatment for the held-out experiment. It remained below the product-quality gate. The final evaluation could characterise what it had changed, but could not turn it into a winner after the fact.

## 07 / 07 — Run the frozen experiment once

Once generation began, every response counted—even when it failed.

All four systems answered the same 60 prompts on one matched RTX 4090 using the pinned BF16 runtime, generation profile and seed policy. Each system received one sampled attempt per prompt, producing 240 responses. There was no JSON repair, constrained decoding, regeneration or manual replacement.

Structure was checked first. Every schema-valid response was then scored by an identity-blinded automated evaluator using the frozen rubric. A sealed sample was later reviewed by the project author to measure agreement with that evaluator, not to overwrite the primary scores or stand in for public preference.

The same harness recorded rendered input tokens, generated tokens and synchronised model-generation time. Paired comparisons kept B and C together by prompt, while uncertainty intervals showed how much the observed differences moved across the authored prompt population.

## What this method can establish

The experiment tells us what four frozen systems did on the same 60 authored prompts under the recorded model, data, generation and hardware conditions. It can compare first-attempt structure, evaluator-derived quality, recurring prompt context and measured generation time.

It cannot establish that prompting or fine-tuning is universally better. It cannot show that one automated judge represents human preference, that the result transfers to larger models, that a single response captures each system’s full stochastic behaviour, or that the measured generation time equals production latency.

The systems were fixed. The test was sealed. Every first attempt was retained.

**So—what changed?**

[View the results →]

## Technical record

| Item | Frozen value |
| --- | --- |
| Base model | Qwen2.5-1.5B-Instruct |
| Prompt development | 20 prompts / four versions / version 3 selected under the frozen rule |
| Supervised dataset | 200 accepted / 160 training / 40 validation |
| Training pilot | 40 examples drawn from training |
| Adapter search | Five candidates / ten spent-development prompts |
| Viable adapter selected | None |
| Final adapted treatment | Candidate 3, diagnostic only |
| Held-out population | 60 authored prompts |
| Final systems | Four |
| Generated responses | 240 first attempts |
| Precision | BF16 |
| Master seed | 20260715 |
| Final hardware | One matched RTX 4090 |
