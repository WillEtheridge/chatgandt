# End-of-Stage-4 System B Worked-Examples Checkpoint

- **Date:** 2026-07-16
- **Worked examples:** `data/prompt-engineering/worked-examples-v1.json`
- **Selected prompt:** `config/prompts/five-shot-v3.json`
- **Standard:** `chatgnt-dataset-authoring-v1.3`
- **Verdict:** Pass; preserve System B unchanged

## Why this checkpoint exists

The five prompt-engineering examples were written before the supervised-data rubric reached its final standard. Before held-out authoring, they were reassessed so System B would not receive deliberately weaker teaching examples than the fine-tuned system.

## Review

| Example | Underlying answer | Metaphorical coherence | Recipe-style execution | Verdict |
| --- | --- | --- | --- | --- |
| Remembering names | Pass: attentive listening, repetition, association, later recall, and graceful repair are specific and usable | Pass: attention is the base pour and recall/self-compassion act as smaller modifiers | Pass: title, measures, “shake” and “stir” sustain the recipe; the optional contact-note garnish reads naturally after “Garnish with” | Pass |
| Leap years | Pass: simple explanation includes the accumulated hours, century rule, examples, and consequence of omission | Pass: real calendar units are substantively meaningful measures rather than decorative scores | Pass: pour, save, stir, finer measure, and the glass-based garnish integrate explanation and recipe | Pass |
| Mixed feelings | Pass: validates simultaneous feelings, separates comparison from self-worth, and offers a manageable action | Pass: the balanced pours communicate emotional emphasis and the spritz metaphor supports the reframing | Pass: shaker and straining language carry the reasoning; the reminder garnish is an optional tonal finish | Pass |
| Library mascot | Pass: supplies a complete character, visual identity, behaviour, and practical uses while correctly resisting the format conflict | Pass: every ingredient contributes to one recognisable mascot concept | Pass: title, measured character features, twist and serve language remain cocktail-like; the invitation garnish is an optional slogan accent | Pass |
| Product description | Pass: the finished two-sentence artefact includes the battery, avoids the prohibited word, and communicates value | Pass: features become the base and modifiers of one foldaway-light concept | Pass: shake, strain, and serve naturally transform notes into copy; the garnish reinforces rather than completes the artefact | Pass |

The three garnishes that initially warranted attention—contact note, reminder, and invitation—do not contain information required to fulfil their prompts. Each is concise, reinforces the completed answer, and works grammatically after “Garnish with.” They therefore pass rather than triggering revisions merely because a different garnish could also work.

## Automated evidence

- Five worked examples, five intent families, and the intended role allocation: pass.
- Response-schema validity: 5/5.
- Exact development-prompt overlap: zero.
- Worked-example source SHA-256: `0cb6afd2bf88ed1f9a3edf8e5ffc479e22c69b91ea7220988c5b1dee51f429b6`.
- Deterministic five-shot-v3 assembly: pass.
- Selected prompt SHA-256: `cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31`.
- Dataset v1.2 audit: no exact worked-response match and no reviewed substantive collision requiring replacement.

## Boundary

This was a qualitative project-master review against the frozen authoring rubric, not new prompt development and not a model-performance test. No Qwen generation, held-out prompt, or training result was inspected. Because every example passed, the planned amendment path was not activated and the selected System B treatment remains byte-for-byte unchanged.
