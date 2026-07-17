# Stage 7 Primary Results

**Run:** `heldout-evaluation-v1-20260717-run01`

**Status:** Complete, including sealed project-author calibration

## What ran

One matched RTX 4090 generated the complete frozen 4 × 60 population under seed `20260715`. All 240 first attempts completed and passed integrity inspection. Systems A and B used the untouched Qwen2.5-1.5B-Instruct model; C and D used the fixed Candidate 3 diagnostic adapter. A and C used the minimal prompt, while B and D used `five-shot-v3`.

The adapter remains below the Stage 6 product gate. These results characterise the treatment; they do not retroactively select it for deployment.

## Headline outcomes

| System | JSON valid | Schema valid | Full response pass |
| --- | ---: | ---: | ---: |
| A — base + minimal | 5/60 (8.3%) | 0/60 (0.0%) | 0/60 (0.0%) |
| B — base + five-shot | 52/60 (86.7%) | 43/60 (71.7%) | 16/60 (26.7%) |
| C — adapted + minimal | 54/60 (90.0%) | 52/60 (86.7%) | 26/60 (43.3%) |
| D — adapted + five-shot | 52/60 (86.7%) | 48/60 (80.0%) | 21/60 (35.0%) |

A full response pass requires schema validity and resolved scores of at least 2/3 for underlying answer quality, metaphorical coherence, and recipe-style execution. Every rate retains the full 60-prompt denominator.

C exceeded B by 15 percentage points in schema validity; the paired 95% bootstrap interval was +1.7 to +28.3 points. Its full-pass difference was +16.7 points, with a wider interval from 0.0 to +33.3 points. The observed direction favours C, but the authored sample does not rule out no full-pass-rate difference at its lower interval boundary.

Underlying answer quality remained the bottleneck. It was acceptable end-to-end on 19/60 B responses and 29/60 C responses, compared with metaphorical coherence on 33/60 and 42/60, and recipe execution on 39/60 and 45/60 respectively. Fine-tuning improved the distinctive representation more reliably than it solved substantive answer selection.

## Blind B-versus-C comparison

Among the 38 prompts where both B and C were schema-valid, the primary judge preferred C on 24 (63.2%) and B on 14 (36.8%), with no ties. Across all 60 prompts—where the only schema-valid response wins mechanically—C won 38, B won 19, and both failed on 3.

The judge calibration matched only two of six complete anchors exactly, although ten of twelve qualitative dimension decisions agreed at the pass/fail boundary. It also converted the intended calibration tie into a narrow winner. Pairwise and qualitative results are therefore model-based judgments, not objective ground truth.

## Sealed project-author calibration

The project author completed the predetermined blind calibration after the primary results were sealed: 18 single-response assessments (six each from B, C, and D; A had no eligible schema-valid response) and all 15 B-versus-C pairs. The primary scores remain the analysis outcome; the human sample measures evaluator agreement and is reported separately.

| Measure | Agreement with primary LLM judge |
| --- | ---: |
| Underlying-answer exact 1–3 score | 2/18 (11.1%) |
| Underlying-answer acceptable/not acceptable | 9/18 (50.0%) |
| Metaphor exact 1–3 score | 5/18 (27.8%) |
| Metaphor acceptable/not acceptable | 14/18 (77.8%) |
| Recipe-style exact 1–3 score | 9/18 (50.0%) |
| Recipe-style acceptable/not acceptable | 17/18 (94.4%) |
| Pairwise A/B/tie choice | 7/15 (46.7%) |

The author was generally more generous than the LLM judge on the qualitative scores, especially for underlying answer quality. In the 15-pair sample, the author chose B ten times, C four times, and tie once; the primary judge chose B eight times and C seven times. This small, single-rater calibration sample does not overturn the all-60 primary results, but it materially lowers confidence in treating the judge-derived quality and preference differences as objective. The strongest conclusion remains the automatic structural result: C produced schema-valid JSON more reliably than B while using far fewer input tokens. Claims that C was broadly preferred or substantively more useful should remain qualified.

## Efficiency trade-off

| Measure, mean per request | B | C | C minus B, paired 95% bootstrap |
| --- | ---: | ---: | ---: |
| Input tokens | 2,575.9 | 31.9 | −2,544.0 [−2,544.0, −2,544.0] |
| Generated tokens | 190.1 | 166.3 | −23.9 [−43.3, −3.4] |
| Timed generation latency | 3.92 s | 5.70 s | +1.78 s [+1.36, +2.21] |

The adapter removed roughly 98.8% of B's rendered input tokens and generated fewer output tokens, but it was slower in this matched local generation measurement. Prompt-token reduction is therefore a real context and serving-cost advantage, not automatic evidence of lower model-generation latency. The latency figure excludes loading, tokenisation, decoding, persistence, network time, and application rendering.

## Interaction and limits

Combining the adapter with the five-shot prompt did not improve on the adapter alone: D full-passed 21/60 versus C's 26/60. Treatments are not automatically additive; redundant or competing behavioural signals can change output length and quality.

The held-out population is a deliberately authored 60-prompt experiment, not a random sample of all possible users. Its intervals describe prompt-level sampling variation inside that population and do not correct authoring bias. Candidate 3 was selected before held-out generation only as the fixed diagnostic adapter, and no held-out result may restart tuning or change the product-gate failure.

The canonical machine-readable result is `experiments/evaluations/heldout-evaluation-v1-20260717-run01/analysis/primary-results.json`.

## Representative failures

The failures were substantive rather than merely cosmetic. B did not rewrite the sentence in heldout prompt 053 and instead supplied generic access-management advice; on prompt 039 it gestured at a detective premise without actually producing the requested story. C inaccurately explained high camera ISO as making pixels expose longer on prompt 019, and misconstrued a required meter photograph as inventory-related on prompt 012. D failed to supply the requested less-grand photography caption on prompt 055.

These examples support the Stage 6 diagnosis: the treatment often entered the right structured, metaphorical mode while still selecting an incomplete, imprecise, or incorrect underlying answer. The frozen raw responses and per-dimension rationales remain available for inspection rather than being replaced by repaired showcase examples.

## Response similarity

The frozen retrieval union produced 5,468 response/reference pairs. Complete blinded review found no exact response match and marked 10 non-exact pairs for review across seven generated responses. Because retrieval and review flags are diagnostics rather than proof, these are reported by exposure:

- B had one strong exposed worked-example reuse flag and one within-system template flag.
- C had two exposed training-response flags: one shared a map-centred Mara story pattern, and one closely paralleled a room-change notice.
- D had one exposed worked-example reuse flag.
- A had five within-system generic-collapse flags centred on reusable long-form advice lists.

The clearest exposure case was B's response to prompt 035, which reproduced most of the “Familiar Face” worked example's ingredients and method nearly verbatim while changing a few surface details. D reused a smaller distinctive subset from the same example. These findings show that demonstrations can be copied as well as generalised, and that fine-tuned outputs can echo training scenarios. They do not establish access to or memorisation of Qwen's unknown pretraining corpus.

Full hashes, ranks, scores, blinded rationales, exposure attribution, and validation evidence are recorded under `experiments/evaluations/heldout-evaluation-v1-20260717-run01/similarity/`.
