# Stage 6 Pilot Behavioural Inspection Results

- **Inspection ID:** `pilot-behaviour-v1`
- **Run ID:** `pilot-behaviour-v1-20260717`
- **Execution commit:** `f1a3e8483ce31ea1dffdf129866e24889298b632`
- **Adapter digest:** `1386a85dd3c5c4c047c2e991dc1dd125ef871f795f91446d4d28654499d624ba`
- **Date:** 2026-07-17
- **Result:** Complete; no schema-valid response from either system

## Evidence integrity

Local harness inspection passed with 20 scheduled and 20 complete response records. There were no missing, duplicate, malformed, or unexpected attempts. The manifest records a clean execution checkout, the expected prompt and system assets, and the provenance-complete pilot adapter active and unmerged for System C.

| Evidence file | SHA-256 |
| --- | --- |
| `manifest.json` | `d56fc65a272e946f90e42a97242a13bba0c558fd5c00b55374e7eeed44303704` |
| `prompts.jsonl` | `0b3acdeb84a13acfee45905e6d40cd4c5bf2e26f546299bbd5ab2fec44826cba` |
| `responses.jsonl` | `dc7211a1290f90a760e5d0b37803c66bcb3edd470e310334f978d1e1c5fe7bdc` |

The harness's 20 `valid_response_count` records are structurally complete capture records, not ChatG&T schema passes. The frozen response validator was applied separately to their untouched raw output.

## Structural result

| System | Attempts | Schema-valid | JSON-syntax failures | Wrong top-level type |
| --- | ---: | ---: | ---: | ---: |
| A — untouched base, minimal prompt | 10 | 0 | 9 | 1 |
| C — pilot adapter, minimal prompt | 10 | 0 | 9 | 1 |

None of the 20 responses began with a Markdown code fence. The syntax failures were ordinary prose or Markdown rather than fenced JSON. The two wrong-top-level responses were JSON strings containing slogans rather than the required object.

Nine attempts per system stopped normally on an EOS token. One attempt per system, both for `dataset-v1-205`, reached the 512-token ceiling. Truncation therefore occurred but does not explain the population-wide structural failure.

System C differed textually from A on nine of ten paired prompts, confirming that the active adapter affected generation. The two systems produced the same raw output only for `dataset-v1-200`. Behavioural influence did not amount to the required ChatG&T format.

## Qualitative-scoring boundary

The frozen evaluation rule scores qualitative dimensions only for schema-valid responses. Because all 20 attempts failed the hard structural gate, no response was eligible for formal 1–3 scoring. Both systems have a joint full-response pass rate of 0% in this diagnostic population.

The raw prose may contain useful or relevant content, but scoring it under the ChatG&T qualitative rubric would change the predeclared rule after seeing the outcome. It is retained as diagnostic text rather than converted into formal scores.

## Interpretation

The pilot adapter was valid, active, and behaviourally non-neutral, but three epochs and 15 optimiser updates over the 40-example pilot did not teach the complete ChatG&T behaviour strongly enough to control generation under a minimal prompt.

This result does not contradict the earlier validation-loss reduction. Teacher-forced validation measures target-token prediction while supplying the correct preceding target tokens. Free generation must first enter the intended JSON recipe pattern and then sustain it using its own generated history. A real loss improvement can therefore remain below the threshold needed to change visible generation behaviour.

The pilot has done its intended job: it proved the mechanics, demonstrated a learning signal, and showed that the pilot-sized exposure is not itself a viable final recipe. It does not establish that full-corpus training will fail.

## Cost

The complete fresh-Runpod inspection session cost **$0.15**. This is the provider's final session charge and is separate from the pilot-training run's training-only compute estimate.

## Evidence location

`experiments/training/pilot-training-v1-20260717-run01/behaviour/pilot-behaviour-v1-20260717/`
