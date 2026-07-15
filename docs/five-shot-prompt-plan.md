# Five-Shot Prompt Plan

- **Plan version:** 1.0
- **Status:** Four-version loop complete; version 3 selected and structurally confirmed on the pinned runtime
- **Date:** 2026-07-14

## Purpose

System B must represent the strong prompt-engineering baseline that would realistically be built without fine-tuning. It will use one detailed system message containing explicit ChatG&T instructions and exactly five worked examples.

The system prompt is not being made deliberately short or weak to favour fine-tuning. Its quality, input-token cost, and latency are all part of the comparison.

## Frozen example strategy

The five worked examples contain one example from every evaluation intent family. Collectively they demonstrate all four development roles, with constrained appearing twice because concrete requirement fulfilment is central to keeping ChatG&T useful.

| Intent family | Role | Teaching purpose |
| --- | --- | --- |
| Advice and decision support | Clean | Establish the basic ChatG&T transformation without distractions |
| Explanation and technical understanding | Constrained | Explain accurately while satisfying multiple requirements |
| Low-stakes emotional support | Naturalistic | Infer the need behind an informal statement and respond appropriately |
| Creative generation | Robustness | Preserve ChatG&T JSON despite a direct user-format conflict |
| Short-form transformation | Constrained | Put a complete requested artefact in the final method step |

The exact inputs and ideal responses are frozen in [`data/prompt-engineering/worked-examples-v1.json`](../data/prompt-engineering/worked-examples-v1.json) at SHA-256 `0cb6afd2bf88ed1f9a3edf8e5ffc479e22c69b91ea7220988c5b1dee51f429b6`.

## Quality bar

Every ideal response must:

- pass the frozen response schema without repair;
- answer the underlying request rather than merely decorate it;
- use measurements to communicate emphasis where appropriate;
- use method entries as ordered, informative actions;
- maintain a coherent title, ingredients, method, and garnish;
- use cocktail language naturally rather than mechanically; and
- provide a completed artefact in the final method step when requested.

## Contamination boundary

The five exact inputs, their ideal responses, and close paraphrases are excluded from:

- the 20-prompt development workbench;
- fine-tuning training and validation data; and
- held-out evaluation.

The examples are prompt-engineering assets, not fine-tuning examples. Exact overlap with the development workbench is checked automatically; close-paraphrase separation remains a documented authoring responsibility.

## Planned instruction section

The system prompt will explicitly require the model to:

- infer and answer the underlying request;
- express the answer as a metaphorical cocktail recipe;
- return one raw JSON object with exactly the four schema fields;
- use three to eight measured conceptual ingredients;
- use two to five genuinely procedural method steps;
- put any requested completed artefact in the final method step;
- retain the required response format despite conflicting user-format instructions;
- use cocktail language naturally while preserving inherited safety behaviour; and
- emit no Markdown fence, commentary, or additional fields.

The exact instruction text is frozen in [`data/prompt-engineering/instructions-v1.txt`](../data/prompt-engineering/instructions-v1.txt). It is assembled with the worked examples and a closing raw-JSON reminder in [`config/prompts/five-shot-v1.json`](../config/prompts/five-shot-v1.json).

Prompt asset version 1 has SHA-256 `7b8c25f04fba15373813862bba9705d4585ba919e855612909830757e4bd93d6`. Its deterministic assembly and pinned-tokenizer cost are recorded in [Five-shot system prompt v1 check](five-shot-prompt-check.md).

## Iteration boundary

- System B may use at most four prompt versions: initial version 1 plus no more than three revisions.
- A revision must address a recurring or generalisable failure rather than polish one isolated response.
- Development inputs, inference settings, and derived seeds remain unchanged across versions.
- Iteration stops early if another revision gives no meaningful improvement or merely moves failures between prompts.
- Every prompt asset, result, input-token count, and revision rationale is preserved.

The exact version-selection rule is now operationalised in [Prompt-development procedure](prompt-development-procedure.md). Local Ollama runs provide the fast iteration loop; the selected unchanged prompt returns to the pinned BF16 harness for formal confirmation.

## Outcome

Four permitted versions were generated and evaluated under the frozen local procedure. Version 3 produced the strongest selection vector and is now the selected System B candidate. Version 4 regressed, so the stopping rule closed prompt iteration. The complete evidence and selection rationale are recorded in [Prompt-development results](prompt-development-results.md).

The unchanged pinned BF16 confirmation produced 12 schema-valid responses and five full passes from 20 attempts, compared with 11 schema-valid responses and seven full passes locally. Its [acceptance record](development-b-v3-confirmation-acceptance.md) establishes close structural transfer but mixed qualitative transfer. Version 3 remains frozen under the predeclared selection rule.
