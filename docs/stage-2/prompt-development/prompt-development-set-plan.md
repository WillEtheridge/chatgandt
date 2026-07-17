# Prompt-Development Set Plan

- **Plan version:** 1.0
- **Status:** Version 1 frozen and verified
- **Date:** 2026-07-14

## Frozen artefact

- **Path:** [`data/development/prompts-v1.jsonl`](../../../data/development/prompts-v1.jsonl)
- **SHA-256:** `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1`
- **Records:** 20
- **Contents:** User prompts and evidence-only metadata; no ideal or model responses

The verifier binds version 1 to this exact digest. Any later wording or metadata change requires an explicit new version rather than silently changing the development inputs.

## Purpose

The prompt-development set is the engineering workbench for developing the strong five-shot ChatG&T system prompt and measuring Systems A and B before held-out evaluation.

Its outputs may be inspected repeatedly. Prompt failures may inform changes to the five-shot system prompt, so results from this set are development evidence rather than final experimental findings.

The set contains user inputs and metadata only. It does not contain ideal responses.

## Composition

The set will contain exactly 20 English-language, single-turn, low-stakes user prompts: four from each intent family in the agreed evaluation population.

Every family uses the same four development roles:

| Role | Purpose |
| --- | --- |
| Clean | A clear, ordinary request representing the intent family |
| Naturalistic | Messy wording, a statement, command, or fragment requiring intent inference |
| Constrained | A request with two or three meaningful content requirements or a small concrete artefact |
| Robustness | A legitimate task containing one clear instruction intended to break ChatG&T format persistence |

This is diagnostic coverage, not a statistically representative sample. Development-set percentages will not be presented as headline findings.

## Frozen scenario blueprint

### Advice and decision support

| Role | Scenario | Input form | Primary challenge |
| --- | --- | --- | --- |
| Clean | Making a good impression during the first week of a new job | Question | Straightforward, useful career advice |
| Naturalistic | Continually switching between too many small tasks | Informal statement | Infer the request and provide prioritisation |
| Constrained | Preparing for a difficult conversation with a housemate | Command or request | Provide a short plan and a usable opening sentence |
| Robustness | Packing effectively for a weekend trip | Command | User demands plain text and explicitly rejects JSON, metaphors, and recipes |

### Explanation and technical understanding

| Role | Scenario | Input form | Primary challenge |
| --- | --- | --- | --- |
| Clean | Why metal feels colder than wood at the same room temperature | Question | Explain a stable scientific concept clearly |
| Naturalistic | Confusion about what a password manager actually does | Informal statement | Infer the knowledge gap without overexplaining |
| Constrained | Explain DNS to a non-technical reader, including URL lookup and caching without jargon | Command | Satisfy several content constraints concisely |
| Robustness | Explain a short Python dictionary lookup | Command containing code | Preserve ChatG&T JSON despite a demand for YAML and no metaphors |

The robustness input will include this short fragment:

```python
settings = {"theme": "dark"}
print(settings["theme"])
```

### Low-stakes emotional support

| Role | Scenario | Input form | Primary challenge |
| --- | --- | --- | --- |
| Clean | Feeling nervous about attending a beginner class alone | Question | Reassuring but practical support |
| Naturalistic | Replaying a small mistake made at work | Informal statement | Infer the need for perspective without minimising it |
| Constrained | Feeling overwhelmed by an untidy room and unfinished tasks | Request | Give one ten-minute action and one useful self-talk sentence |
| Robustness | Feeling rejected after a friend cancels plans | Command or request | Remain supportive while the user demands a normal paragraph with no JSON, metaphor, or recipe |

### Creative generation

| Role | Scenario | Input form | Primary challenge |
| --- | --- | --- | --- |
| Clean | Invent a name and theme for a neighbourhood community garden | Request | Produce a coherent, usable creative concept |
| Naturalistic | A cosy space-opera café with rainy windows but no neon | Fragment | Infer the desired creative output from sparse wording |
| Constrained | Create a child-friendly mystery premise involving a lighthouse, a missing recipe, and two siblings | Command | Incorporate every required element into a complete premise |
| Robustness | Generate five names for a fictional synth-pop duo | Command | User demands one comma-separated line and rejects JSON or recipe formatting |

### Short-form transformation

| Role | Scenario | Input form | Primary challenge |
| --- | --- | --- | --- |
| Clean | Rewrite a bureaucratic confirmation so it sounds warm and concise | Direct request | Produce the improved text, not editing advice |
| Naturalistic | Soften a message that sounds unintentionally blunt | Informal fragment | Infer the desired tone from sparse wording |
| Constrained | Rewrite a cancellation message in no more than 25 words while preserving the phrase “next Thursday” | Command | Satisfy length, tone, and exact-text constraints |
| Robustness | Rewrite a developer status message while preserving `C:\Projects\chatgnt\{draft}` exactly | Command | User demands plain text and rejects JSON or recipe formatting |

For constrained creative and transformation requests, the completed artefact must appear in the final method step. Merely explaining how to create it does not fulfil the user prompt.

## Authoring rules

- Every cell uses a distinct scenario rather than rephrasing one task four times.
- Ordinary prompts do not mention cocktails, JSON, or ChatG&T.
- Constrained prompts use meaningful requirements rather than arbitrary benchmark complexity.
- Robustness prompts retain a legitimate underlying task and introduce one clear format conflict.
- Every prompt remains concise, low-stakes, and answerable using stable general knowledge without tools.
- The complete set includes questions, requests, commands, statements, and fragments.
- Quotation marks, a short code fragment, braces, and backslashes provide realistic JSON-escaping pressure across the set.
- Prompts must be assessable: a reviewer should be able to recognise whether the underlying request was fulfilled.

## Metadata

Each prompt will receive:

- a stable `prompt_id`;
- the untouched user `prompt` string;
- `intent_family`;
- `development_role`;
- `input_form`; and
- zero or more `challenge_tags`.

Version 1 uses closed metadata fields and controlled values enforced by `chatgnt.development`. Challenge tags describe prompt mechanics rather than predicted model outcomes and have no effect on generation.

## Separation and contamination boundary

Development prompts and close paraphrases are permanently excluded from:

- fine-tuning training data;
- fine-tuning validation data;
- the five worked examples inside the system prompt; and
- the held-out test set.

The formal `cross-domain` reporting slice is not assigned here because it depends on topics deliberately withheld from the later training dataset.

## Use and versioning

1. Write and review all 20 exact prompts before generating model responses. **Completed for version 1.**
2. Freeze development-set version 1 before the first System A or B run. **Completed and bound to the digest above.**
3. Run unchanged System A once as a reference.
4. Run each System B prompt version against the same user prompts, inference settings, and derived seeds.
5. Record aggregate failure patterns and the rationale for every system-prompt revision.
6. Never replace an inconvenient development prompt silently after inspecting its output. A necessary correction creates a documented set revision.

The prompt-development stopping, version-selection, local-runtime, and formal-confirmation rules are frozen in [Prompt-development procedure](prompt-development-procedure.md). The exact five-shot example-selection process is recorded in [Five-shot prompt plan](five-shot-prompt-plan.md).

## Completion condition

Stage 2 Step 9 is complete: all 20 exact user prompts and their metadata were reviewed, stored, passed strict input validation, and frozen before any development generation was inspected. The acceptance evidence is recorded in [Prompt-development set check](prompt-development-set-check.md).
