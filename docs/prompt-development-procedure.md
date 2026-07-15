# Prompt-Development Procedure

- **Version:** 1.0
- **Adopted:** 2026-07-15
- **Status:** Executed; version 3 selected after four inspected versions

## Purpose

Develop a credible five-shot System B prompt quickly on the local machine while reserving the pinned Hugging Face BF16 harness for formal confirmation.

Local Ollama generations are development diagnostics. They may guide prompt changes but cannot replace formal results because the quantised weights, runtime, prompt implementation, and sampling implementation differ from the pinned Transformers environment.

## Fixed development population

Every inspected prompt version uses the same 20 frozen prompts in `data/development/prompts-v1.jsonl`. Their exact text and close paraphrases remain excluded from training, validation, worked examples, and held-out evaluation.

System A is not rerun during local prompt iteration. The accepted formal System A run remains the no-ChatG&T reference. Every System B candidate, including `five-shot-v1`, is run locally so comparisons between prompt versions use one local runtime and configuration.

## Version boundary

A prompt draft becomes an immutable numbered version as soon as model outputs produced with it are inspected. Wording edits made before any output is inspected remain drafting, but inspected alternatives cannot be discarded or renamed as though they never existed.

Prompt development permits at most four numbered versions in total:

- `five-shot-v1`, already frozen and formally run; and
- at most three evidence-backed revisions.

Each version retains its exact prompt asset, digest, local raw outputs, validation results, qualitative scores, and revision rationale. A formal confirmation run of unchanged prompt text does not create another prompt version.

## Local runtime contract

The local loop uses the installed `qwen2.5:1.5b-instruct` Ollama model, currently model ID `65ec06548149`, Q4_K_M quantisation, and CPU execution. The run record must capture the observed Ollama version, model identity, model blob identity, template, default system instruction, generation settings, host execution mode, prompt-asset digest, and development-set digest.

System B supplies its complete prompt as the request system message, replacing the irrelevant vendor identity message for that request. The request uses Ollama `/api/chat` with streaming disabled and no `format` constraint, extraction, repair, continuation, or retry.

All local versions use the same frozen settings:

- temperature `0.7`;
- top-p `0.8`;
- top-k `20`;
- repetition penalty `1.1`;
- maximum generation `512` tokens;
- context window `8192` tokens; and
- one stable derived local seed per prompt, reused across prompt versions.

Local timing and token counts are diagnostic and cannot be compared directly with formal BF16 measurements.

## Evaluation order

For each numbered version:

1. Preserve all 20 untouched raw outputs and runtime metadata.
2. Apply the frozen strict parser and ChatG&T response schema without repair.
3. Create identity-blinded judge packets containing only the user prompt, candidate response, and frozen rubric.
4. Score schema-valid responses on underlying-answer quality, metaphorical coherence, and recipe-style execution using the frozen 1–3 anchors.
5. Label Codex assessments as LLM-judge scores and record the available evaluator identity.
6. Record joint full-response passes and aggregate failure patterns.

Schema-invalid responses receive structural diagnostics but no qualitative score under the frozen evaluation rule. Human calibration remains a later requirement and is not silently replaced by the LLM judge.

## Revision trigger

A new prompt version is justified only by a prompt-addressable failure pattern observed in at least two development responses. The rationale must name the pattern, cite the affected blinded records, explain why prompt wording or examples could plausibly correct it, and state the intended change before new outputs are generated.

Do not revise for:

- one unlucky or merely mediocre sample;
- missing base-model knowledge;
- a failure unlikely to respond to system-prompt changes;
- cosmetic preference;
- an edit tailored to the wording of one known prompt; or
- a change likely to improve one case by weakening general behavior.

## Version selection

Compare prompt versions only on local runs produced by this procedure. Select the lexicographically strongest observed version using:

1. full-response pass count;
2. schema-valid count;
3. count scoring at least 2 for underlying-answer quality;
4. count scoring at least 2 for metaphorical coherence;
5. count scoring at least 2 for recipe-style execution; and
6. lower complete rendered input-token cost when quality is otherwise tied.

Keep dimension-level results and failure patterns visible; the selection vector is a development decision aid, not a headline metric or statistical claim.

## Stopping rule

Stop prompt development when the earliest of these conditions occurs:

- the current best version has no recurring prompt-addressable failure;
- the newest revision does not improve the selection vector or introduces a material regression;
- a further edit would amount to tuning for individual development prompts; or
- four prompt versions have been inspected.

The strongest observed local candidate is then frozen and rerun unchanged through the pinned BF16 harness. If behavior fails to transfer materially, use a remaining revision slot only when the same revision trigger is met; otherwise report the transfer discrepancy.

The four-version ceiling was reached on 2026-07-15. Version 3 was the strongest observed candidate and version 4 regressed, so no revision slot remains. Any transfer discrepancy will therefore be reported rather than prompting a fifth version.

## Formal boundary

Only a pinned-harness run can provide formal model identity, matched latency, or final System B evidence. The eventual held-out System B versus System C comparison runs both systems through that harness on matched hardware and settings. Local Ollama results remain clearly labelled as prompt-development diagnostics throughout the project.
