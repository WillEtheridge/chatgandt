# Stage 5 Readiness Review

- **Held-out set:** `heldout-v1`
- **Status:** Frozen
- **Stage verdict:** Pass
- **Date:** 2026-07-16

## Readiness question

Is there a fixed, balanced, scorable held-out prompt set that remained unavailable while the systems and supervised data were developed, contains no model responses, and is sealed before training?

**Yes.** Stage 6 may train and select an adapter without using held-out v1. The prompt file remains unavailable for configuration, model selection, or debugging.

## Requirement audit

| Requirement | Finding |
| --- | --- |
| Population | Pass: exactly 60 prompts and 12 per intent family |
| Reporting slices | Pass: 30 target-use, 15 cross-domain, and 15 robustness prompts; each family contributes 6/3/3 |
| Input forms | Pass: 15 questions, 30 direct requests or commands, and 15 statements or fragments |
| Complexity | Pass: 40 standard and 20 composed prompts; each family has three composed robustness prompts and one composed target-use prompt |
| Constraints | Pass: exactly ten constraint-bearing prompts, two per family |
| Cross-domain matrix | Pass: photography, tabletop games, and pottery/ceramics each appear once in every intent family and were absent from frozen supervised data |
| Robustness matrix | Pass: format, behaviour, and serialization pressure each appear once in every intent family |
| Quality | Pass: every task is low-stakes, single-turn, answerable without tools, naturally phrased, and scorable under the frozen rubric |
| Separation | Pass: comparison against 231 prohibited project prompts produced zero exact or threshold flags; no replacement was required |
| Experimental boundary | Pass: no model answer was generated or inspected; dataset v1.2 and Systems A–D remain unchanged |
| Reproducibility | Pass: one executable builder reproduces the records, quota report, audit, and manifest deterministically |

## Frozen identities

- Held-out prompt SHA-256: `1a4ce978e056866d0c5fc6f2a9ee5cd4bf7f49caf9bc13cfcee3edd4394382d4`.
- Audit SHA-256: `3824e14fb0f3f5ff9ee85703ed1623bd785b948793bbd56709604ff1bf7d9d2d`.
- Quota report SHA-256: `5f3241d0b11841a3a2d3ddcc149a27e28278c794bc754efefd4a811c9f93a515`.
- Manifest SHA-256: `d3bcfb9c5c8bdafe73e1ae65631b1d2aee4263332f32ab0aa902c8aba804d689`.

## Limitations

The overlap control uses exact and bounded lexical similarity rather than claiming proof of semantic independence. The prompts and the complete-set review were produced by a frontier-model project agent, not an independent human panel. These limitations should accompany later results.

## Verdict

Stage 5 is complete. The next step is Stage 6: repair the known portable adapter test fixture, pass preflight, and run the frozen 40-example pilot without opening held-out prompts for model development.
