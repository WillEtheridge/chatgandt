# Stage 4 Readiness Review

- **Dataset:** `chatgnt-dataset-v1.2`
- **Dataset status:** Frozen
- **Stage verdict:** Pass
- **Date:** 2026-07-16

## Readiness question

Is there a fixed, validated, contamination-checked supervised dataset suitable for pilot and full training, with validation isolated from training and no access yet to exact held-out prompts or model performance?

**Yes.** Stage 5 may author the exact held-out prompts under the frozen evaluation protocol. Model training and held-out generation remain out of scope until their planned stages.

## Requirement audit

| Requirement | Finding |
| --- | --- |
| Active population | Pass: amendments 001–002 yield exactly 200 terminally accepted active examples while retaining all superseded history |
| Quality | Pass: every active record is schema-valid and has a terminal passing qualitative review and acceptance chain |
| Coverage | Pass: exactly 40 examples per intent family and all frozen slice, input-form, complexity, constraint, robustness, topic, subtype, and ingredient-count requirements |
| Contamination | Pass: no exact duplicate, prior-prompt match, worked-response match, withheld-domain occurrence, substantive reviewed collision, or obvious template collapse |
| Split isolation | Pass: 160 training and 40 validation examples, exactly 32/8 per family, with no scenario crossing splits |
| Pilot | Pass: 40 training-only examples, eight per family, covering every required axis |
| Token balance | Pass: mean rendered lengths are 232.91 training tokens and 233.90 validation tokens; medians are 234 and 241, with ranges 147–320 and 149–286 |
| Reproducibility | Pass: seed `20260715`, exact allocation, no deviation record, canonical files, hash-bound manifest, and byte-identical second build |
| System B fairness | Pass: all five worked examples meet the final v1.3 teaching standard; five-shot-v3 remains unchanged |
| Experimental boundary | Pass: no exact held-out prompts were authored or inspected, no Qwen output informed data selection, and no training occurred |

## Frozen identities

- Dataset manifest SHA-256: `bbc749a1a840213fa9b09680df9da7b06e35cb0c7deceab60ecd2744e354aca5`.
- Training JSONL SHA-256: `1690561db24ba4d2ae3c56f0ba4e988643994cb2add51f01beef901ebf5095b2`.
- Validation JSONL SHA-256: `b9e344f6582a9ebe4d9b83801cf71acc2abf2c4f95efd71bcd58eafbfb36bdc5`.
- Pilot JSONL SHA-256: `a8e4ad6ea6923c18e1111d16c00c07b40004d9533c04d32d6550edf2521565dd`.
- Passing contamination findings SHA-256: `9d0b3cccc137ce3a96f004218c8b75dee14f8c671c9fa9735e9fb5bcaa2d86f2`.
- System B prompt SHA-256: `cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31`.

## Limitations

The examples are synthetic and were primarily authored and reviewed by frontier-model agents under project-master supervision. Distinct actor identities and passes provide process separation, not independent human evaluation. Similarity review protects against observable project overlap but cannot prove independence from unknown model pretraining. The two amendment layers are explicit and executable but make v1.2 less direct than an untouched single-pass corpus.

These are proportionate limitations for the portfolio experiment and remain documented rather than converted into stronger claims.

## Verdict

Stage 4 is complete. The next step is Stage 5: author exactly 60 held-out prompts to the frozen population blueprint without generating system responses, compare them against the now-frozen supervised and worked-example sources, and freeze them before training or evaluation.
