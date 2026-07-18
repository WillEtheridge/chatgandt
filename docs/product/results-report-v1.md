# ChatG&T Results Report v1

- **Purpose:** canonical editorial source for the public Results page
- **Evidence date:** 2026-07-17
- **Report date:** 2026-07-18
- **Status:** Draft v1

## Editorial thesis

> Fine-tuning learned the ChatG&T recipe more reliably than it learned to answer the underlying task. It produced more schema-valid responses with 98.8% less input context, but it was slower, the apparent quality advantage depended on the evaluator, and no candidate met the predeclared viability gate.

This is a mixed result, not a disguised win or a total failure. The public page should keep four facts visible together:

1. fine-tuning materially improved first-attempt schema reliability;
2. it removed almost all recurring prompt context;
3. it did not establish a robust qualitative or preference advantage; and
4. the bounded search ended with no viable adapter selected.

Candidate 3 was later published and served through the portfolio demonstration path as a diagnostic model. That use does not reverse the no-winner decision or make it a product-quality model.

## 01 — Opening

### Evidence label

`FROZEN EVALUATION / 60 UNSEEN PROMPTS / 240 FIRST ATTEMPTS / 17 JULY 2026`

### Headline

> Fine-tuning learned the recipe.  
> The hard part was the answer.

### Plain-language result

The fine-tuned model produced valid ChatG&T recipes more reliably than the same base model following a developed five-shot prompt. It also replaced 2,544 recurring input tokens per request with a minimal prompt.

But the adapter was slower in the matched generation measurement, still produced incomplete and incorrect underlying answers, and did not pass the quality gate required to become a viable ChatG&T model. The strongest conclusion is structural: fine-tuning taught the representation more reliably than it taught substantive correctness.

### Decision callout

> **Decision / No viable adapter selected**
>
> Candidate 3 was the strongest bounded candidate, but it achieved 6/10 full passes where the frozen gate required 7/10. It was retained for the held-out experiment and demonstration as a fixed diagnostic treatment, not promoted into a product-quality winner.

## 02 — At a glance

The opening evidence should use four large editorial measures rather than a generic KPI dashboard.

### Structural reliability

> **52 / 60**  
> Fine-tuned responses were schema-valid, compared with 43/60 prompted responses.

Observed difference: **+15 percentage points**. Paired 95% bootstrap interval: **+1.7 to +28.3 points**.

### Recurring context

> **−98.8%**  
> Mean rendered input fell from 2,575.9 tokens to 31.9.

The fine-tuned treatment used exactly **2,544 fewer input tokens per request** on this population.

### Generation latency

> **+1.78 seconds**  
> Fine-tuning was slower in the matched generation-only measurement.

Mean timed generation was 5.70 seconds for the fine-tuned treatment and 3.92 seconds for the prompted treatment. Paired 95% interval: **+1.36 to +2.21 seconds**.

### Full response pass

> **26 / 60**  
> Fine-tuned responses passed the complete contract, compared with 16/60 prompted responses.

The observed difference was +16.7 points, but its paired 95% interval was **0.0 to +33.3 points**. The apparent quality advantage therefore remains compatible with no difference at the lower boundary and depends on the qualitative judge.

## 03 — Four systems, one frozen run

The experiment tested every combination of model and prompt treatment once on each of the 60 held-out prompts.

| | Minimal prompt | Five-shot prompt |
| --- | --- | --- |
| Untouched base model | A — untreated reference | B — prompting treatment |
| Candidate 3 adapter | C — fine-tuning diagnostic | D — combined diagnostic |

All systems used the same Qwen2.5-1.5B-Instruct base, frozen generation profile, seed policy, BF16 runtime, and matched RTX 4090. Every first attempt was retained. There were no quality-driven retries, repairs, or replacements.

| System | JSON valid | Schema valid | Full response pass |
| --- | ---: | ---: | ---: |
| A — base + minimal | 5/60 (8.3%) | 0/60 (0.0%) | 0/60 (0.0%) |
| B — base + five-shot | 52/60 (86.7%) | 43/60 (71.7%) | 16/60 (26.7%) |
| C — adapter + minimal | 54/60 (90.0%) | 52/60 (86.7%) | 26/60 (43.3%) |
| D — adapter + five-shot | 52/60 (86.7%) | 48/60 (80.0%) | 21/60 (35.0%) |

The practical primary comparison was B versus C: a strong prompt-engineering strategy against a fine-tuning strategy using almost no recurring instruction. Because both the prompt and adapter state differ, it is a strategy comparison rather than the isolated causal effect of one variable. Systems A and D complete the two-by-two context.

## 04 — The format was learned

Structural reliability is the strongest result because it is deterministic and operationally meaningful. A schema failure prevents the ordinary product interface from rendering a recipe at all.

### Prompted treatment B

- JSON valid: 52/60
- Schema valid: 43/60
- Structural failures: 17/60
- Failure labels: seven JSON syntax, six ingredient-count, three wrong-top-level-type, and three Markdown-fence findings

### Fine-tuned treatment C

- JSON valid: 54/60
- Schema valid: 52/60
- Structural failures: 8/60
- Failure labels: six JSON syntax, one ingredient-count, and one method-count finding

Failure labels can overlap on one response.

The fine-tuned treatment improved schema validity by 15 percentage points over the developed prompt. Its paired interval excluded zero. This supports the public claim that fine-tuning materially improved first-attempt contract reliability under the documented conditions.

It does not support a universal claim that fine-tuning is better than prompting, nor does schema validity establish that the answer inside the object is useful.

## 05 — The answer remained the bottleneck

A full response pass required all four of the following:

1. schema-valid JSON;
2. an acceptable underlying answer;
3. a coherent cocktail metaphor; and
4. convincing recipe-style execution.

All end-to-end rates retain the complete 60-prompt denominator.

| End-to-end acceptable | B — prompted | C — fine-tuned |
| --- | ---: | ---: |
| Underlying answer | 19/60 (31.7%) | 29/60 (48.3%) |
| Metaphorical coherence | 33/60 (55.0%) | 42/60 (70.0%) |
| Recipe execution | 39/60 (65.0%) | 45/60 (75.0%) |
| Full response pass | 16/60 (26.7%) | 26/60 (43.3%) |

Both systems were much better at producing the cocktail presentation than at fulfilling the underlying task. Fine-tuning moved the bottleneck; it did not remove it.

The distinction becomes even clearer when only schema-valid responses are considered:

| Conditional acceptability | B, n=43 | C, n=52 |
| --- | ---: | ---: |
| Underlying answer | 19/43 (44.2%) | 29/52 (55.8%) |
| Metaphorical coherence | 33/43 (76.7%) | 42/52 (80.8%) |
| Recipe execution | 39/43 (90.7%) | 45/52 (86.5%) |

C's end-to-end recipe advantage came from getting more responses through the structural gate. Among responses already eligible for judging, B had slightly higher recipe-style acceptability. That is another reason not to collapse the experiment into one winner score.

### Diagnostic variation

These subgroup counts help locate failures but are not confirmatory comparisons. Each intent family contains only 12 prompts, no subgroup interval was calculated, and no multiplicity correction was applied.

| Full passes by intent family | A | B | C | D |
| --- | ---: | ---: | ---: | ---: |
| Advice and decision support | 0/12 | 3/12 | 5/12 | 5/12 |
| Creative generation | 0/12 | 3/12 | 9/12 | 1/12 |
| Technical explanation | 0/12 | 1/12 | 1/12 | 2/12 |
| Low-stakes emotional support | 0/12 | 7/12 | 7/12 | 7/12 |
| Short-form transformation | 0/12 | 2/12 | 4/12 | 6/12 |

| Full passes by reporting slice | A | B | C | D |
| --- | ---: | ---: | ---: | ---: |
| Target use, n=30/system | 0 | 9 | 13 | 15 |
| Cross-domain, n=15/system | 0 | 5 | 7 | 3 |
| Robustness, n=15/system | 0 | 2 | 6 | 3 |

The small cells reveal heterogeneity rather than subgroup winners. Technical explanation remained difficult across all treatments, while the combined D treatment varied sharply by intent.

## 06 — Preference depended on the judge

### Primary LLM pairwise result

B and C were both schema-valid on 38 prompts. The primary LLM judge compared those 38 pairs blindly:

- C preferred: 24/38 (63.2%)
- B preferred: 14/38 (36.8%)
- Tie: 0/38

Across all 60 prompts, including mechanical structure wins:

- C wins: 38
- B wins: 19
- Both fail: 3

The all-60 outcome is not 60 subjective preferences. It combines the 38 judged pairs with 14 C-only-valid prompts, five B-only-valid prompts, and three prompts where neither response was valid.

### The judge was imperfect before production

On six frozen pre-run calibration anchors, the primary judge:

- matched two of six complete anchors exactly;
- matched seven of 12 individual qualitative scores exactly;
- agreed on ten of 12 qualitative pass/fail boundaries; and
- matched one of two pairwise choices.

It scored some strong responses conservatively and converted one intended tie into a narrow winner. The project retained those discrepancies instead of selecting a more agreeable judge after seeing the result.

### Sealed project-author calibration

The project author later scored a predetermined blind sample of 18 individual responses and 15 B/C pairs. This was a single first-pass rater, not a representative human panel.

Agreement with the primary LLM judge was:

| Measure | Agreement |
| --- | ---: |
| Underlying answer, exact 1–3 score | 2/18 (11.1%) |
| Underlying answer, acceptable/not acceptable | 9/18 (50.0%) |
| Metaphor, exact score | 5/18 (27.8%) |
| Metaphor, acceptable/not acceptable | 14/18 (77.8%) |
| Recipe execution, exact score | 9/18 (50.0%) |
| Recipe execution, acceptable/not acceptable | 17/18 (94.4%) |
| Pairwise choice | 7/15 (46.7%) |

On the same 15 B/C pairs:

| Evaluator | B | C | Tie |
| --- | ---: | ---: | ---: |
| Primary LLM judge | 8 | 7 | 0 |
| Project author | 10 | 4 | 1 |

The disagreement does not prove that either evaluator was right. It shows that claims about substantive usefulness and preference depend heavily on who judged them. Agreement was high on recipe execution and much weaker on the underlying answer—the exact dimension already identified as the model's bottleneck.

The automatic structural result is therefore firmer than the qualitative or preference result. Public copy must not say that users or humans generally preferred either treatment.

## 07 — Less context, more latency

| Mean per request | B — prompted | C — fine-tuned | C minus B, paired 95% interval |
| --- | ---: | ---: | ---: |
| Input tokens | 2,575.9 | 31.9 | −2,544.0 [−2,544.0, −2,544.0] |
| Generated tokens | 190.1 | 166.3 | −23.9 [−43.3, −3.4] |
| Timed generation | 3.92s | 5.70s | +1.78s [+1.36, +2.21] |

Fine-tuning removed almost all recurring prompt context and generated fewer output tokens. It was nevertheless slower in the matched measurement.

The contradiction matters. Fewer prompt tokens can reduce context usage and recurring token processing without guaranteeing faster generation. Adapter execution, output dynamics, implementation, and hardware can change the result.

The latency figure covers the synchronized `model.generate()` call on one matched RTX 4090. It excludes loading, tokenisation, decoding, persistence, network time, cold start, application rendering, and tail latency. It is not an end-user latency or universal serving-cost result.

## 08 — The treatments were not additive

System D combined Candidate 3 with the complete five-shot prompt. It was fully generated, structurally evaluated, qualitatively scored, and included in the similarity review.

| Combined-treatment comparison | C — adapter + minimal | D — adapter + five-shot |
| --- | ---: | ---: |
| Schema valid | 52/60 | 48/60 |
| Full response pass | 26/60 | 21/60 |
| Mean input tokens | 31.9 | 2,575.9 |
| Mean generated tokens | 166.3 | 134.5 |
| Mean timed generation | 5.70s | 4.68s |

Adding the five-shot prompt to the adapter did not improve the observed aggregate result. It may have been redundant or may have changed output behaviour in competing ways, but this run did not include a dedicated C/D preference comparison or a precomputed paired C/D interval. The interaction remains a secondary descriptive finding, not evidence that prompting generally harms a fine-tuned model.

## 09 — How the search ended with no winner

The held-out result did not select Candidate 3. The product decision had already been made on a separate ten-prompt spent-development population under a fixed, non-compensatory gate:

- at least 8/10 schema-valid responses;
- at least 7/10 full response passes; and
- at least one full pass in every intent family.

| Candidate | Training hypothesis | Selected validation loss | Schema valid | Full passes | Families represented | Decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Full-corpus anchor | 2.080787 | 7/10 | 3/10 | 2/5 | Failed |
| 2 | More exposure | 1.981721 | 9/10 | 4/10 | 2/5 | Failed |
| 3 | Broader attention adaptation | 1.966936 | 10/10 | 6/10 | 5/5 | Failed by one |
| 4 | Attention and MLP adaptation | 1.900072 | 9/10 | 6/10 | 4/5 | Failed quality and coverage |
| 5 | Content-token weighting | 1.968187 | 9/10 | 4/10 | 3/5 | Regressed |

Candidate 3 was clearly the strongest bounded option, but “best available” was not allowed to become “good enough” after the outputs were visible.

Candidate 4 reached the lowest validation loss of all five candidates without improving Candidate 3's full-pass count; it also lost perfect structure and complete family coverage. Candidate 5 put more training weight on answer-bearing token locations but did not provide a signal for whether the answer itself was correct.

The fixed five-candidate allowance ended with zero viable adapters and no sixth attempt. Candidate 3 was then bound before held-out generation as the simplest and most informative diagnostic treatment. The held-out set could characterise what it changed, but could not rescue it, restart tuning, or relax the gate.

## 10 — What failure looked like

The most informative failures were substantive, not cosmetic.

### Prompted B / held-out prompt 053

The task required rewriting a sentence. The response instead supplied generic access-management advice. It entered the recipe mode without delivering the requested artefact.

### Prompted B / held-out prompt 039

The task required a detective story. The response gestured at a premise but did not actually produce the story.

### Fine-tuned C / held-out prompt 019

The response incorrectly explained high camera ISO as making pixels expose for longer. The output was polished and recipe-shaped, but factually wrong.

### Fine-tuned C / held-out prompt 012

The response misconstrued a required photograph of a meter as an inventory-related task.

### Combined D / held-out prompt 055

The user requested a less-grand photography caption. The response failed to supply the requested transformation.

These cases illustrate the central diagnosis: presentation can conceal failure. A valid, entertaining cocktail recipe is not successful if it solves a nearby problem, misses a constraint, omits the requested artefact, or states a material falsehood.

If the public page presents complete examples, it should also include at least one transparently selected success and state how examples were chosen. The page must not replace the frozen raw outputs with repaired showcase responses.

## 11 — Resemblance, not proof

Every held-out response was compared with the frozen worked examples, training responses, and the other responses produced by the same system.

- Responses reviewed: 240
- Response/reference pairs reviewed: 5,468
- Exact canonical matches: 0
- Non-exact review flags: 10 across seven responses

| System | Exposed-source flags | Within-system flags | Interpretation |
| --- | ---: | ---: | --- |
| A | 0 | 5 | Generic long-form template collapse |
| B | 1 | 1 | Strong worked-example reuse and one local recurrence |
| C | 2 | 0 | Two parallels with training scenarios |
| D | 1 | 0 | Partial worked-example reuse |

B's response to prompt 035 reproduced most of the “Familiar Face” demonstration's ingredient concepts and four method steps. Two C responses echoed known training scenarios. These are meaningful exposure-related similarities, not proof of a causal memorisation mechanism.

The audit covers known project material only. It cannot inspect Qwen's unknown pretraining corpus and does not establish that an output is globally novel.

## 12 — What the result establishes

### Supported

- Fine-tuning materially improved first-attempt schema reliability over the developed five-shot strategy under the documented conditions.
- It replaced approximately 98.8% of recurring input context and generated fewer output tokens.
- It was slower in the matched generation-only measurement.
- It learned format, metaphor, and recipe execution more reliably than substantive task fulfilment.
- None of the five bounded training candidates met the predeclared viability bar.
- The observed qualitative and preference result depends materially on the evaluator.

### Not established

- That fine-tuning generally produces better answers than prompting.
- That users or humans generally preferred the adapter.
- That the 98.8% input-token reduction made serving 98.8% cheaper, faster, or more efficient overall.
- That the adapter is a viable product-quality ChatG&T model.
- That the results generalise beyond this base model, synthetic dataset, single seed policy, and authored 60-prompt population.
- That the response-similarity flags prove memorisation.

### Closing statement

> The fine-tune succeeded at a narrower task than the one we hoped to solve. It learned how a ChatG&T answer should look and made that interface substantially more reliable. It did not consistently learn what the answer should say.
>
> Preserving that distinction—and stopping without a viable winner—is the result.

## Evidence and navigation

The public page should close with three onward paths:

- **Experiments:** research question, systems, dataset, training, frozen evaluation, and limitations;
- **Learning:** transferable lessons about validation loss, structured behaviour, judging, infrastructure, and proportionate research practice; and
- **Evidence:** the source repository and frozen machine-readable result.

Canonical evidence:

- `docs/stage-7/primary-results.md`
- `docs/stage-7/judge-calibration-assessment.md`
- `docs/stage-7/response-similarity-results.md`
- `docs/stage-6/full-training-candidate-selection-results.md`
- `docs/stage-6/second-round-results.md`
- `experiments/evaluations/heldout-evaluation-v1-20260717-run01/analysis/primary-results.json`
- `experiments/evaluations/heldout-evaluation-v1-20260717-run01/derived/generation-manifest.json`
- `experiments/evaluations/heldout-evaluation-v1-20260717-run01/structure/summary.json`
- `experiments/evaluations/heldout-evaluation-v1-20260717-run01/judging/`
- `experiments/evaluations/heldout-evaluation-v1-20260717-run01/similarity/summary.json`

## Implementation direction

The page should read as a long-form editorial report, not a live analytics dashboard.

- Preserve the established concrete background, steel text, signal accent, Neue Montreal Mono face, thin rules, visible grids, and large typographic hierarchy.
- Use numbered chapters, generous whitespace, narrow reading measures, and a small number of full-width evidence comparisons.
- Prefer direct counts, count strips, simple CSS bars, matrices, and accessible tables over chart libraries, donuts, animated counters, or generic KPI cards.
- Use signal red to identify editorial importance, uncertainty, or a selected comparison—not to mark a winner.
- Keep all denominators visible. Clearly label conditional results when they exclude structural failures.
- Keep the no-viable-adapter decision near the top rather than burying it after favourable metrics.
- Use progressive disclosure for subgroup diagnostics, exact interval details, latency scope, and evidence paths if the main reading flow becomes too dense.
- Do not incorporate public Tasting Room choices. They are unrecorded demonstrations and not part of the frozen evidence.
- Do not add a charting library or modify the shared visual system for v1.

