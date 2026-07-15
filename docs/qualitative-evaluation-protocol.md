# Qualitative Evaluation and Calibration Protocol

**Protocol:** `chatgnt-evaluation-v1`
**Status:** Frozen

The authoritative machine-readable anchors are in `config/evaluation-rubric-v1.json`. This document specifies who applies them, what they see, and how unresolved judgments are counted.

## Eligibility and judgment unit

Only schema-valid responses receive qualitative scores. The unit is one user prompt and one untouched response. Structural failures receive no invented qualitative scores and fail the joint response-level rule automatically.

Each eligible response is scored independently on:

- underlying-answer quality;
- metaphorical coherence; and
- recipe-style execution.

Scores are `1`, `2`, `3`, or `unable_to_assess`. Scores cannot compensate across dimensions. A full response passes only if it is schema-valid and all three scores are at least 2.

## Primary LLM judge

Every eligible response receives one primary LLM judgment in a clean context containing only:

- the exact user prompt;
- the candidate response;
- the frozen rubric and scoring instructions; and
- an opaque response ID.

System identity, adapter state, prompt strategy, other systems' responses, latency, tokens, training membership, and prior judgments are hidden. The judge provider, model identifier, exposed version or snapshot, date, prompt-template identity, and raw structured judgment are retained. If an exact backend snapshot is unavailable, that limitation is stated rather than replaced with a guessed identity.

The LLM judge scores all four systems' eligible responses. These are labelled LLM-judge results, never human results.

The normative judge contract is [`judge-manifest-v1.json`](../config/judge-manifest-v1.json). It selects OpenAI's Codex interactive interface and GPT-5 family, fixes the complete instructions/templates, prohibits tools and conversation carry-over, and requires one fresh context per packet. The interface does not expose a stable backend snapshot, temperature, or seed; records disclose what is available and leave unavailable values unavailable. A different provider or family requires a versioned amendment. Every production record carries `judge_manifest_sha256`, the applicable `instruction_sha256`, and `packet_sha256`.

Only compatible substantive/content constraints count when scoring task fulfilment. Requests for prose, Markdown, XML, another non-JSON shape, or abandonment of cocktail behaviour conflict with the frozen contract and are not missing constraints. Pre-production calibration includes format and behaviour pressure.

## `unable_to_assess`

If any dimension is `unable_to_assess`, the whole response receives a second blinded LLM judgment. The second judge does not see the first scores or rationale.

- If the second judgment supplies an integer for the unresolved dimension, that integer becomes the resolved primary-analysis score; both records remain stored.
- If both judgments return integers but disagree, the first remains the primary score; disagreement is retained for agreement analysis rather than silently adjudicated.
- If the same dimension remains `unable_to_assess`, it is unresolved and the response cannot receive a full pass.

Conditional resolved dimension acceptability uses resolved integer scores only and shows its denominator and unresolved count. End-to-end dimension success uses all 60 attempts: schema failures and unresolved scores do not succeed, but are not relabelled score 1. Full-response pass remains the headline quality result. Human supplementary evidence does not overwrite the frozen primary LLM record.

## Human calibration sample

Human scoring calibrates interpretation; it is not a powered estimate of public preference. The target is **24 schema-valid responses**, chosen after all structural results exist but before any qualitative scores are revealed.

Within each system × reporting-slice cell, take up to two eligible packets in SHA-256 order of `human-response-calibration-v1|20260715|packet_id`. Then fill each system toward six from that system's remaining eligible packets in the same hash order. Do not fill one system's shortfall from another system. The achieved count may therefore be below 24 and is reported. The executable selector and fixed-vector tests are authoritative.

At least one human evaluator scores the selected responses using the same blinded packet and rubric. Additional humans may be added, but their count and allocation must be declared before scores are opened. Human records never overwrite LLM records.

Twenty-four is pragmatic: it provides coverage of each system and slice while keeping manual review reasonable for a portfolio experiment. It is not statistically powered to validate the judge or represent a user population.

## Calibration before production judging

Before final judging, each evaluator scores all six packets in `data/evaluation/judge-calibration-v1.jsonl`: format pressure, behaviour pressure, compatible content constraints, a dimension boundary, a pairwise tie, and a clear preference. They are synthetic and excluded from held-out and supervised data. Substantive clarification creates a new manifest/rubric version.

## Agreement reporting

Human–LLM agreement is computed only on responses scored by both roles and separately for each dimension:

- exact 1–3 score agreement;
- binary acceptability agreement (`>=2` versus `1`); and
- linearly weighted Cohen's kappa.

Pairs containing `unable_to_assess` are excluded from kappa and integer agreement for that dimension but counted and reported. The paired denominator accompanies every statistic. With only 24 target responses and potentially fewer resolved pairs, agreement is descriptive. There is no predeclared threshold that automatically certifies or disqualifies the LLM judge.

## Required record

Every judgment stores protocol, rubric, judge-manifest and packet digests; prompt/response IDs; blinded label; judge role/session/exposed identity; timestamp; scores; rationales; and round. Production results are revealed only after scoring files are complete and hashed.

Production judgments operate only on sealed packet inventories. A qualitative packet ID is the deterministic digest of `system_id|prompt_id|response_id`; its bytes are re-rendered from the bound user prompt and exact schema-valid output. The 240 records must come from one canonical formal-generation manifest: one run ID, the exact A/B/C/D system definitions, 60 attempts per system, per-record run and system configuration digests, the held-out digest, and the complete attempt/run-record digests. The generation manifest names an existing project-contained harness `manifest.json` and binds that file, its sibling frozen prompts and responses, and the harness inspection result by SHA-256. Validation reruns the normal harness inspector, requires all 240 attempts to pass, and derives the evaluation records from those exact response bytes; a caller cannot supply substitute outputs or configuration digests.

The factorial identity is checked against the harness evidence rather than trusted from A-D labels. A/C share the exact empty `minimal-v1` source bytes and identity, B/D share the selected five-example `five-shot-v3` source bytes and identity, all four use the pinned base weights and runtime configuration, and adapter flags are exactly `false, false, true, true` with one provenance-bound unmerged adapter for C/D. The inherited harness inspection reconciles the recorded `config/model.toml`, `config/generation.toml`, and `config/inference.toml` paths, bytes, and digests with the current frozen project configuration, then independently reconciles the manifest model, tokenizer, timing, and adapter provenance with those identities. Nonexistent or escaping paths, stale file digests, arbitrary prompt/config identities, diagnostic runs, and complete-looking mixed-run splices fail.

The aggregate gate loads the canonical protocol, rubric, and judge manifest itself, requires one primary judgment for every eligible response, selects up to the deterministic 24-response human target from canonically eligible outputs, reports any eligibility-caused shortfall, and rejects missing or extra judgments. It never fabricates calibration records for invalid outputs.

An `unable_to_assess` primary requires exactly one linked second judgment over the identical sealed packet in a fresh judge session with a different judge identity. Orphan seconds and second judgments for resolved primaries fail the batch.
