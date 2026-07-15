# Prompt-Development Results

- **Date:** 2026-07-15
- **Population:** 20 frozen development prompts
- **Selected candidate:** `five-shot-v3`
- **Status:** Local selection and pinned structural and qualitative confirmation complete

## Scope

These results describe prompt engineering on a development workbench. They are not held-out evidence and do not answer the project's research question. The local prompt-version comparison used the same quantised Ollama model, inputs, generation settings, and stable per-prompt seeds throughout. Formal version 1 evidence is shown separately rather than mixed into the local ranking.

Schema-invalid responses were not qualitatively scored. The qualitative figures are LLM-judge scores from OpenAI Codex (GPT-5) in the 2026-07-15 session; an exact backend snapshot was unavailable, and later human calibration remains required.

## Initial formal A/B observation

The accepted pinned BF16 v1 run completed all 40 attempts. System A, the base model with an empty system message, produced `0 / 20` schema-valid responses. System B with `five-shot-v1` produced `9 / 20` schema-valid responses, of which six passed all three qualitative dimensions.

This is useful development evidence that the five-shot prompt changes behaviour substantially. It is not a final performance estimate.

## Local version comparison

The selection vector is ordered as full response passes, schema-valid responses, acceptable underlying answers, acceptable metaphors, and acceptable recipe style.

| Version | Intervention | Selection vector | Mean prompt tokens | Result |
| --- | --- | --- | ---: | --- |
| v1 | Original detailed instructions, five examples, short final reminder | `4 / 9 / 5 / 7 / 6` | 2,357.15 | Initial local reference |
| v2 | Replace the final reminder with a detailed silent checklist | `6 / 11 / 6 / 10 / 10` | 2,513.15 | Improvement |
| v3 | Replace prose checklist with a recent concrete JSON skeleton | `7 / 11 / 7 / 10 / 11` | 2,582.15 | **Selected** |
| v4 | Compress the main instructions while retaining examples and v3 skeleton | `6 / 10 / 6 / 9 / 10` | 2,400.15 | Regression |

The frozen lexicographic rule selects v3 because it has the highest full-response pass count. v4 is cheaper in prompt tokens than v3, but token cost is only a tie-breaker after quality; its quality regression therefore cannot be traded away silently.

The machine-readable aggregate is retained in [`experiments/evaluations/prompt-development-summary-v1.json`](../experiments/evaluations/prompt-development-summary-v1.json). Raw outputs, structural diagnostics, blind packets, concealed scores, revealed scores, and each revision rationale are retained alongside it.

## What changed and what did not

The increasingly explicit final controls improved the local full-pass result from 4 to 7. The concrete recent shape cue in v3 improved task completion and recipe-style acceptability over v2, but did not increase schema-valid count beyond 11. Recurring failures remained: invalid JSON, conflicting-format compliance, wrong top-level types, too few ingredients, and failure to deliver a requested textual artefact.

Instruction compression in v4 reduced the mean prompt by 182 tokens relative to v3 but moved every quality count in the wrong direction. This is evidence against assuming that a shorter prompt helps a small model merely by reducing instruction load.

Local and formal v1 both produced `9 / 20` schema-valid responses, but their qualitative results differed: four full passes locally versus six formally. Matching aggregate structure did not make the quantised local runtime equivalent to the pinned BF16 system.

## Stopping decision

Prompt development stops because:

- v4 regressed relative to v3; and
- all four predeclared prompt versions have been inspected.

No fifth version will be created from these development outputs. `five-shot-v3`, SHA-256 `cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31`, is the selected System B candidate.

## Pinned transfer check

The unchanged v3 prompt subsequently produced 12 schema-valid responses from 20 attempts through the pinned Hugging Face BF16 harness, compared with 11 locally. All 20 generations completed successfully, and the run is accepted in [Development System B v3 confirmation acceptance](development-b-v3-confirmation-acceptance.md).

Blinded scoring found five full passes, eight acceptable underlying answers, nine acceptable metaphors, and seven acceptable recipe-style executions. Local v3 had seven full passes, while pinned v1 had six. The result therefore supports close structural transfer but not an overall quality improvement.

The confirmation remains development evidence rather than a new prompt-development opportunity or held-out result. Version 3 remains frozen because it won the predeclared local rule; the mixed transfer result becomes evidence for dataset and evaluation design rather than justification for a fifth prompt version.
