# Automatic, Efficiency, and Uncertainty Analysis Protocol

**Protocol:** `chatgnt-evaluation-v1`
**Status:** Frozen

## Denominators

Each system is scheduled once on each of 60 held-out prompts. Missing attempts and generation errors remain in the 60-attempt denominator and fail JSON validity, schema validity, and full-response pass. They are not replaced or retried for the primary evaluation.

For every rate, the report shows its numerator and denominator. Conditional resolved dimension acceptability uses schema-valid responses with resolved integer judgments. End-to-end dimension success uses all 60 attempts and counts only resolved scores `>=2` as success without imputing score 1. Full-response pass is the headline quality rate.

## Automatic measures

The existing strict parser and Draft 2020-12 ChatG&T response schema remain authoritative. Untouched raw output is measured for:

- generation completion and termination reason;
- strict JSON validity;
- schema validity and deterministic failure labels;
- full-response pass after blinded qualitative scoring;
- rendered input tokens;
- generated tokens;
- raw output characters; and
- per-attempt synchronized generation latency.

No extraction, fence stripping, repair, constrained decoding, or retry is allowed in the primary result. Derived canonical rendering is used only for blinded display and response-similarity analysis after the untouched structural result is recorded.

## Efficiency conditions

Systems run through the frozen harness at batch size one, under matched hardware, model revision, tokenizer, dtype/quantisation, generation settings, and software. Each loaded runtime receives one unmeasured warm-up. Inputs are tokenized before timing; CUDA is synchronized immediately before and after `model.generate()`. Model load, tokenization, decode, persistence, network, and application rendering are excluded.

For latency, input tokens, output tokens, and raw characters, report count, mean, median, standard deviation where configured, and interquartile range. Latency summaries state achieved count. Matched C-minus-B latency differences use only prompts successful for both systems.

Adapter size and training time are reported separately from per-request inference. Input-token reduction is not treated as proof of latency reduction.

## Uncertainty

Overall binary rates receive 95% Wilson score intervals calculated from integer success and denominator counts, including completion, JSON validity, schema validity, dimension acceptability where resolved, and full-response pass. Individual B-win, C-win, and tie proportions may receive Wilson intervals, but these are marginal intervals rather than one simultaneous multinomial confidence region.

Matched C-minus-B differences use a non-parametric paired percentile bootstrap:

1. the resampling unit is a held-out **prompt ID**;
2. binary rates sample all 60 prompt IDs; continuous means sample the achieved matched prompt IDs with resample size equal to achieved `n`;
3. carry every B and C outcome attached to each sampled prompt together, preserving pairing;
4. compute the C-minus-B difference for the chosen statistic;
5. repeat 10,000 times using seed `20260715`; and
6. report the 2.5th and 97.5th percentiles.

Primary intervals apply only to paired rate differences and paired mean efficiency differences. Conditional pairwise bootstrap resamples eligible resolved IDs and reports achieved `n`. Medians and median differences are descriptive only.

The bootstrap describes sampling variability within this authored evaluation; it does not correct prompt-selection bias or make 60 prompts representative of all users. No subgroup confidence intervals, multiplicity-adjusted significance tests, or `p < 0.05` winner rule are planned. Intent-family and slice results show counts and point estimates as diagnostics.

## Missingness and unresolved judgments

- Missing/generation-failed outputs count as structural and full-response failures.
- A structurally valid response with a persistently unresolved qualitative score cannot full-pass.
- Persistently unresolved pairwise choices remain a separate end-to-end outcome.
- Continuous metrics never silently discard failures: every summary states the successful or matched count.

## Interpretation

Quality and efficiency remain separate outcomes. The final report records observed trade-offs and uncertainty; it does not invent a universal exchange rate between a quality point, token, and millisecond. Small differences compatible with the interval are described as inconclusive rather than success or failure by default.
