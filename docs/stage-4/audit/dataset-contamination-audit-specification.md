# Dataset Duplication, Contamination, and Exclusions Audit Specification

> **Historical and superseded (2026-07-16).** This design was executed once and
> produced 41,957 review flags despite zero automatic failures. It is retained
> to show what was tried and learned, but it no longer governs Stage 4. D-059
> and `scripts/audit_dataset_v1.py` define the proportionate replacement.

- **Stage:** 4 — Build and freeze dataset v1
- **Step:** 10 — Audit duplication, contamination, and exclusions
- **Status:** Frozen after one adversarial review and one bounded amendment pass; no production audit has been run
- **Date:** 2026-07-16
- **Audit ID:** `chatgnt-dataset-contamination-audit-v1`

## Purpose and boundary

This specification fixes the complete Stage 4 audit method before its results are inspected. It asks whether the 200 terminally accepted supervised examples contain internal duplicates or repeated teaching templates, reproduce material that was prohibited during authoring, violate scenario identity, or enter the three deliberately withheld domains.

This step is a corpus gate, not another open-ended writing or polishing round. Similarity scores retrieve pairs for review; they do not decide semantic duplication. The governing semantic question remains the frozen three-part rule from D-039 and the Stage 3 unseen protocol.

This specification does not author or inspect exact held-out prompts, query or load Qwen, assign splits, render training conversations, run a pilot, train a model, revise System B, inspect model performance, or change the frozen evaluation protocol. Exact held-out records are neither an input nor an allowed path. The audit operates on the current accepted semantic records before split assignment.

The proportionality boundary is fixed:

1. one adversarial review of this specification before implementation, now completed by `docs/dataset-contamination-audit-adversarial-review.md`;
2. one implementation review before the production run;
3. one human-readable disposition for every generated review flag;
4. no threshold, view, source-set, or decision-rule tuning after production results exist; and
5. no candidate change inside this audit; any later corpus change requires a separately authorised contract amendment and a new complete immutable audit generation.

## Governing contracts

The implementation must reuse, not redefine:

- `chatgnt.evaluation_protocol.normalize_text`, `text_identity`, `lexical_score`, `lexical_neighbours`, `metadata_neighbours`, MiniLM embedding/token diagnostics, cosine ranking, and canonical record identities;
- RapidFuzz `3.14.5` `fuzz.token_ratio`;
- `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, attention-masked mean pooling, L2 normalisation, 384 dimensions, cosine similarity, and 256-wordpiece truncation;
- the substantive collision rule in D-039, `docs/unseen-contamination-protocol.md`, and `docs/dataset-v1-design.md`;
- the source record, lifecycle, provenance, reason-code, and canonical JSONL rules in `docs/dataset-contract-specification.md` and `docs/dataset-authoring-guide.md`; and
- the three withheld-domain identifiers in `config/dataset-v1.json`: `photography`, `tabletop_games`, and `pottery_ceramics`.

Normalization is Unicode NFC, line-ending normalization, Unicode case folding, collapse of every whitespace run to one ASCII space, and outer trimming. Punctuation is retained. Any implementation that changes normalization, model revision, pooling, truncation, tie order, or RapidFuzz version is a new audit protocol, not v1.

## Frozen production inputs and identities

Every path is resolved beneath the repository root and must match its SHA-256 before extraction. Missing, additional, stale, or identity-mismatched sources fail closed. The source manifest records byte count, record count, extractor version, extracted record count, and canonical extracted-record SHA-256 in addition to the file identities below.

### Supervised corpus under audit

The active corpus is the concatenation of Batch 01 through Batch 11 in numeric order:

- `data/dataset-v1/authoring/batch-01/candidates.jsonl` through `batch-11/candidates.jsonl`;
- `data/dataset-v1/authoring/batch-01/workflow-events.jsonl` through `batch-11/workflow-events.jsonl`.

The entry identity is:

- batch-ordered candidates SHA-256: `65a29225f94cd062344b34adf368fd6c8b0a5d84a911eb91a7c60a983e10c2ac`;
- batch-ordered workflow-events SHA-256: `585babc1a883cbecd6e39f8b5b6426c894a9c4af4fad108285b1e8d2ecea5c3e`.

The implementation freezes `config/dataset-contamination-audit-sources-v1.json`, a path-aware source manifest whose canonical entries contain relative path, role, byte count, record count, and file SHA-256. Its supervised entries must equal this table; the two concatenated digests above remain secondary collection identities:

| Batch | Candidates records / SHA-256 | Events records / SHA-256 |
| --- | --- | --- |
| `01` | `10` / `5c0fcb7c6a2da43f48371fef00bf630c87881a8673b8581328042c26cb5d5dd3` | `88` / `81388100b8ac5762157bffd02fcf21b519ed953b55b7070526b82696d12d30d0` |
| `02` | `20` / `1be38573233b170b3646180c63d7aba2b8e87a581258defad8f1d9897c9316d2` | `108` / `162ef63c0830d5a6c152dc333954acdf32aed063fc5b4e503b9849d188c5c462` |
| `03` | `20` / `9c7ba19dc0b63cfc2ab1ba74bf77a636b43002dea71d098231f75b9955838697` | `62` / `6243aae8e811bb9769e3d0402a7a7013b59d5bdafa7684d7adb454d92de20b65` |
| `04` | `20` / `3043b4c404c4dccba294ab9a6ddaa3706222f21a99e89aca14ad7ad23475ba16` | `62` / `5885b81b02f765aa99c3eca70de7c4291f516b5eacf0eb5d6a37dd680d2c8d2b` |
| `05` | `20` / `025f5a1ca773020d03231de76c515655d2baee0fa28341692c0338380ac004d2` | `64` / `2faf63df545529175426f7107d6f4af4c23324818fd4b2bfce1715f16b04809d` |
| `06` | `20` / `b829e065135c2c2702d858b8e1008e270efe9d8b697a28daa41f382da18a829f` | `76` / `e7417d303369e7401c1d799f9dd27f58d61f6a7847211e4c4ff8af43f88febf9` |
| `07` | `20` / `bf2473ba4bcd44290ea0b09907ccea9bdc8086677f1a36637d03786079715dbf` | `84` / `00718c9942a4fa78023013115eca159eb1d99ae362772c2604dcc85f86167a7f` |
| `08` | `20` / `bae82c15b4c98f41cba8c31b8d36db26a3cdda31150a507c3d3be281ccf26ff9` | `64` / `9a5bcf7d5f4fdf531f81eb6ce182c961c38623fa5f81819d661afc6f1b3` |
| `09` | `20` / `19a2a220011b29db9d8c187917fecc1fb1ee49b8556ca67af9be53ee842c87e9` | `70` / `20b8bc197161cbf660734466adc74b08d4dd79b90d49e208ba85f1e55547822a` |
| `10` | `20` / `a81bf705ccb1b7e43ee28e023a2a999d7e9e02fc17c24629553aadf70ccae8a1` | `74` / `972b92144bc7feb9ebcd20478bf2814569df9bb1bc976b774c5daad08e948a56` |
| `11` | `10` / `478909da8c390c03c050fdd73dd92a3bfe6a3dc863c42392a595526686bc318b` | `32` / `65fec7ddf25228539caa12c732e0155ed3f31330b7d9dd73fb971100091b648d` |

The source-manifest digest is frozen during implementation review before production content is processed and is then required by every generation. The verifier must reconstruct exactly 200 current terminally accepted records, validate every source record and complete lifecycle chain in authoring mode, and require null splits and `pilot_member: false`. It must not trust the count or terminal status from this document.

### Worked baseline material

The five System B worked examples are extracted as separate user-prompt and assistant-response references from:

- `data/prompt-engineering/worked-examples-v1.json`, SHA-256 `0cb6afd2bf88ed1f9a3edf8e5ffc479e22c69b91ea7220988c5b1dee51f429b6`.

The extractor requires exactly five unique example IDs and binds both views. It also verifies that the selected prompt remains:

- `config/prompts/five-shot-v3.json`, SHA-256 `cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31`, prompt asset ID `five-shot-v3`, with exactly five worked examples.

The assembled prompt is an identity/control input, not one giant similarity reference: shared contract instructions and JSON field names are expected and must not swamp retrieval. Agreement is exact and deterministic, not semantic: `chatgnt.prompting.expected_five_shot_asset_v3()` and `scripts/build_five_shot_v3.py` must reconstruct the complete selected asset byte-for-byte from the validated instructions and `worked-examples-v1.json`. No natural-language parser for the assembled prompt is permitted.

### Prompt-development inputs and outputs

The complete development input population is extracted once from:

- `data/development/prompts-v1.jsonl`, SHA-256 `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1`, exactly 20 prompt records.

All target-model development outputs are prohibited source material and contribute their `raw_output` as response references. Every run is a three-file source binding, not a free-standing response file:

| Run directory | Manifest SHA-256 | Prompts records / SHA-256 | Responses records / SHA-256 |
| --- | --- | --- | --- |
| `experiments/development/local/five-shot-v1-ollama-q4km-20260715` | `c18f49b9eafec27b2ed60e4cb19a2a8d13b01718cc24de68300226583c07f5a4` | `20` / `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` | `20` / `eb7ac9bb80b6bf1e5e5816082609d7ccb5b143f3c906084028e8c0848b55cf1c` |
| `experiments/development/local/five-shot-v2-ollama-q4km-20260715` | `379f5c7fd22aa05503e27dd23a954c73c91eec74cf48d630e7295c0651ef5855` | `20` / `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` | `20` / `1f17a4f35258c4c12f9b42df3fba079321375b54fcd2c4e864ffce59eee466a6` |
| `experiments/development/local/five-shot-v3-ollama-q4km-20260715` | `fba67e13ed8d46f4a095cda1ced5d2c99e731f7a0a991d110fb1d9de604c9141` | `20` / `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` | `20` / `c4cb947893031099ccd8d709fea6eda3d4a56d52db99566267df369211d7d761` |
| `experiments/development/local/five-shot-v4-ollama-q4km-20260715` | `839ec38b146482fa8b8ea4b2585ea356d83a5e3e7f3318767fabfab4d65e4d49` | `20` / `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` | `20` / `a0fd70e5ed2f5c21fabf61108aa3b758994c0714aaba4182b003b4673cb0320e` |
| `experiments/runs/development-ab-v1-20260715` | `415408d949c9f8487c6ce6688f04a12fee98a5cee408d225a35e8bd08f5609ce` | `20` / `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` | `40` / `0bfb4e728a5b8e941445a150536fd74c27e9aeebc0b8331d0a31193c9f59bed4` |
| `experiments/runs/development-b-v3-confirmation-20260715` | `9a600c36cf0749f7114c5d1c88defb2e6d22297d47127a848ee6444663e9b76f` | `20` / `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` | `20` / `2b9a56b8886e625565bf7504b4bcc7b5b962eb8032a0137b1930fce3d94cb86c` |

For local runs, join each response to the sibling prompt by `prompt_id`; require manifest `run_id`, prompt-set identity, prompt-asset ID/digest, response `run_id`, `system_id`, unique `attempt_index`, and stored raw-output hash to agree. For formal runs, additionally require the response's embedded user message to equal the joined prompt, and require unique `(system_id, prompt_id, repeat_index, attempt_index)`, prompt-asset identity, manifest schedule, and raw-output hash. Every joined exchange receives a stable ID derived from source manifest identity plus run/system/prompt/repeat/attempt identity. Repeated input prompts are de-duplicated only in the standalone prompt reference collection by `(prompt_id, normalized_sha256)`; exchanges and distinct outputs retain run/system provenance.

The early local preflight prompts and outputs are also prohibited target-model sources:

- `experiments/preflight/ollama-qwen2.5-1.5b-2026-07-14.jsonl`, SHA-256 `bedc84fea0dafa17ae0e0810e60bba719dd555ab5d8ac4c119468ab027fca54f`, six records.

Each preflight row contributes `prompt`, `raw_output`, and a joined exchange keyed by unique `probe_id`; the raw-output identity is recomputed because the format contains no stored output digest.

The existing pinned-Qwen CUDA diagnostic is included rather than treated as a technical-fixture exception:

| Diagnostic source | Records | SHA-256 |
| --- | ---: | --- |
| `artifacts/diagnostics/inference-harness-cuda/20260714T151316Z-0879c92d/manifest.json` | 1 | `f94ea2832ae26a3f6146fa6370c06f0d67d05fa8f94fd14b8266d63836c26da3` |
| `artifacts/diagnostics/inference-harness-cuda/20260714T151316Z-0879c92d/prompts.jsonl` | 1 | `3e4590ca32441373f2b0d2fcd2e2b1284092cadee3c524ef1bc87cf400730881` |
| `artifacts/diagnostics/inference-harness-cuda/20260714T151316Z-0879c92d/responses.jsonl` | 2 | `3f1334e7be37dfc80045ff307bf1e4bf1a56caeb6b1fa4ab854c5146d19fd7c9` |

Its extractor validates the manifest prompt-set and system-set identities, joins responses by `prompt_id`, verifies the embedded user message, prompt asset, system/adapter state, unique attempt identity, and raw-output hash, and emits prompt, response, and joined-exchange references. No repository-resident target-model semantic prompt or output known at specification review is excluded.

### Evaluation-development and calibration material

All authored text-bearing records in these frozen calibration files are excluded sources:

| Source | SHA-256 |
| --- | --- |
| `data/evaluation/contamination-calibration-v1.jsonl` | `242d4fae46d975ca31d80c8765e2b9dae9521665c1fc5e9855970e148d1a626b` |
| `data/evaluation/judge-calibration-v1.jsonl` | `46ef76c16073998843045ed99221f67a18b6b61b737f939236436f2f393668f9` |
| `data/evaluation/response-similarity-calibration-v1.jsonl` | `d156c5fd5a846fc37ccef73a41b805388569d9facbcc76ace181fc3e96631ccf` |

The extractor includes candidate and existing prompts, calibration user prompts, candidate/query/reference responses, and any supplied text embedded in those fields. Labels, rationales, expected decisions, generic schema keys, and judge instructions are not comparison content.

The authoring-guide calibration fragments are also prohibited, as required by the guide. They are extracted only from list items beginning `- Pass anchor:`, `- Revise anchor:`, or `- Reject anchor:` beneath the three numbered qualitative-review subsections and the `Garnish-only calibration fragments` paragraph in:

- `docs/dataset-authoring-guide.md`, SHA-256 `7d7fe271a3f5057aa605b4d3c698b5b4e244583f5dfd2fb2c31fe89921854f0f`.

Extraction stops at the next heading of equal or higher level, retains the outcome label and subsection in each stable ID, and takes the text after the first colon as a response-fragment reference. It does not infer hypothetical prompts or complete responses from explanatory prose. The implementation review freezes the resulting record IDs and canonical extracted-record digest before the production run.

### Normative identity controls

The audit report additionally binds these files so the meaning of the records and exclusions cannot drift between specification and run:

| Path | SHA-256 |
| --- | --- |
| `config/dataset-v1.json` | `4ed2f61fa14000293debe2556e63297b3b1e439b41d7a4c7ef5285f2704c6a3c` |
| `schemas/supervised-example-v1.schema.json` | `727b2e9373a5c17ff3bdaf84c862a6bbd1a9e86d13bfb2fc12f74dacc5be7f01` |
| `schemas/chatgnt-response-v1.schema.json` | `107f6f93ed77c1a1c057af78e832ab178f817192b90deb8ca333af458591953d` |
| `config/dataset-authoring-rubric-v1.3.json` | `4d8df1ee6db926cc4d4e28a55f8bffbe06aa81eac2d1cc959a554364e4a65201` |
| `config/evaluation-protocol-v1.json` | `8d23e010e4b68a3e25248fc54d3e4ea80371b1e397b3117cf899adeb7d954cd4` |
| `chatgnt/evaluation_protocol.py` | `21f5eae0a6d36a79de38f7848de768b4207aa004d5f15ec7e8d1685339e8bfc4` |
| `scripts/generate_semantic_evidence.py` | `33103427ad36ee5f92d601dbfb6fc2ecee56cdd1993a4b4a949e54e23410dd76` |

The future audit implementation and schemas receive their own identities in the implementation-review record and production manifest.

## Canonical comparison views

Every view retains its source collection, stable record ID, originating field path, original SHA-256, normalized text, normalized SHA-256, and MiniLM token diagnostic. No comparison concatenates unrelated records.

For each supervised example, construct:

1. **Prompt view:** exact `user_prompt`.
2. **Scenario view:** field-labelled `user_goal`, `requested_task_or_artefact`, `scenario_summary`, and each `important_constraints` item in authored order.
3. **Complete response view:** the frozen field-labelled representation used by `response_similarity_text_view`, including title, ingredient amounts/units/names, every method step, and garnish.
4. **Full supervision view:** field-labelled prompt followed by the complete response view.
5. **Component views:** title; each ingredient name; each complete method step; garnish.
6. **Structural signature:** intent family, task subtype, ingredient count, ordered exact `(amount JSON value, normalized unit)` sequence, and method-step count.

The structural signature deliberately contains only intent family, task subtype, ingredient count, ordered exact `(amount JSON value, normalized unit)` sequence, and method-step count. Ambiguous sentence-opening, title-prefix, garnish-opening, and token-count extractors are removed. Structural signatures are internal diversity evidence only.

### Exhaustive source/view eligibility matrix

No generic fallback comparison is permitted. Every extracted reference belongs to exactly one row:

| Source class and extracted field | Reference view | Eligible candidate view(s) | Stable nested/join identity |
| --- | --- | --- | --- |
| Internal supervised `user_prompt` | prompt | prompt, scenario | `example_id:user_prompt` |
| Internal supervised scenario metadata | scenario | prompt, scenario | `example_id:scenario` |
| Internal supervised parsed response | complete response and same-type components | complete response and same-type components | `example_id:response` plus field/index path |
| Internal supervised joined prompt + response | full supervision | full supervision | `example_id:exchange` |
| Worked example `user_prompt` | prompt | prompt, scenario | `worked-example-id:user_prompt` |
| Worked example `assistant_response` | complete response and same-type components | complete response and same-type components | `worked-example-id:response` plus field/index path |
| Worked example joined pair | full supervision | full supervision | `worked-example-id:exchange` |
| Standalone development prompt | prompt | prompt, scenario | `prompt_id:prompt` |
| Development/preflight/CUDA `raw_output` | complete raw response; parsed complete response/components when schema-valid | complete response; same-type components only when parsed | source manifest + run/probe/system/prompt/attempt identity |
| Joined development/preflight/CUDA prompt + output | full supervision | full supervision | source manifest + run/probe/system/prompt/repeat/attempt identity |
| Contamination calibration `candidate_prompt` or `existing_prompt` | prompt | prompt, scenario | `case_id:field-name` |
| Judge calibration `user_prompt` | prompt | prompt, scenario | `calibration_id:user_prompt` |
| Judge calibration `candidate_response`, or each explicitly labelled response branch | complete raw/parsed response and eligible components | complete response and same-type components | `calibration_id:field-name[:branch-label]` |
| Judge calibration deterministic prompt/response pair | full supervision | full supervision | `calibration_id:exchange:field-name[:branch-label]` |
| Response-similarity `query_response` and each `references[]` member | complete raw/parsed response and eligible components | complete response and same-type components | `case_id:query_response` or `case_id:reference:reference-id` |
| Authoring-guide underlying-answer or metaphor anchor | response fragment | complete response only | subsection + outcome + ordinal |
| Authoring-guide recipe-style anchor | response fragment | complete response and method components | subsection + outcome + ordinal |
| Authoring-guide garnish-only anchor | response fragment | complete response and garnish component | subsection + outcome + ordinal |

Response-similarity records have no prompt and are never full-supervision references. A standalone raw output is never compared with full supervision. Mixed calibration branches are enumerated from their closed schema and never collapsed into one string. Internal comparisons are like-with-like, unordered, and self-excluding.

Metadata retrieval is eligible only for internal supervised scenario records and source prompt records that contain every frozen metadata field in the required scalar/array shape. It is ineligible for raw responses, exchanges, worked examples without complete retrieval metadata, preflight/CUDA technical prompts without complete retrieval metadata, calibration records, and guide anchors. Ineligible classes produce no synthetic empty metadata and no metadata ranks.

Generic JSON field labels and the empty system message are never standalone references. Invalid development output is normalized as complete raw text. If a development output parses to the ChatG&T schema, the implementation also builds the complete response view; the raw text identity remains retained.

## Deterministic checks and fixed thresholds

All pair ordering uses descending score followed by ascending canonical pair ID. Internal comparisons are unordered pairs and exclude self-matches. A pair produced by several signals becomes one flag listing every triggering signal, score, rank, view, and source collection.

### Automatic failures

The following require no semantic discretion and set the run status to `fail`:

- a missing, extra, stale, noncanonical, structurally invalid, nonterminal, or nonaccepted supervised input;
- duplicate `example_id` or inconsistent lifecycle/content identity;
- exact normalized equality between two supervised prompt views;
- exact normalized equality between a supervised prompt view and a prohibited prompt reference;
- exact normalized equality between two complete supervised response views;
- exact normalized equality between a complete supervised response view and a prohibited complete response reference;
- exact normalized equality between two full-supervision views;
- provenance naming the pinned Qwen model or its prohibited aliases in any frontier-model authoring/revision/review event;
- a missing, malformed, orphaned, contradictory, or unresolved flag disposition.

An automatic failure still receives a disposition record so the evidence and remedy are human-readable. Exact equality of a short component such as a title, ingredient, or garnish is a review flag rather than an automatic failure because ordinary recipe vocabulary can recur legitimately.

### Lexical flags

RapidFuzz `token_ratio` is computed on normalized text. A pair is flagged when:

- prompt, scenario, or full-supervision score is at least `90.0`;
- complete-response score is at least `92.0`; or
- a same-type component of at least five normalized word tokens scores at least `95.0`.

In addition, sharing a contiguous normalized eight-word sequence in prompt, scenario, response, or component text creates a flag. The implementation reports but does not flag shorter shared sequences. It may not remove stopwords or maintain an after-the-fact boilerplate exception list.

### Semantic flags

MiniLM cosine similarity creates a flag when:

- prompt or scenario cosine is at least `0.82`;
- full-supervision cosine is at least `0.86`; or
- complete-response cosine is at least `0.88`.

The top five lexical and top five semantic neighbours per query, eligible view, and source collection always require dispositions even when below threshold. Each list contains exactly `min(5, eligible_reference_count)` entries. Scores sort descending and ties sort by ascending stable reference ID, so a tie at rank five does not expand the list. Any query or reference over 256 wordpieces is marked truncated; every selected pair involving one is reviewed against complete text, never only the truncated view.

### Metadata flags

Metadata comparison reuses the frozen fields `topic`, `user_goal`, `requested_task_or_artefact`, `scenario_summary`, and `important_constraints`. A pair is flagged when it has exact normalized overlap in at least two fields. `topic` alone never flags a pair. For arrays, any shared normalized item counts as that field's overlap.

Exact overlap in all of `user_goal`, `requested_task_or_artefact`, and `scenario_summary` is a high-priority review flag, not an automatic semantic verdict. A metadata statement can itself be generic or erroneous; the reviewer must inspect the actual prompt and response.

Two records sharing one `scenario_id` are placed in review together but do not fail automatically: the dataset contract deliberately permits related examples to form an indivisible scenario group. The reviewer checks that the ID is justified by the substantive rule. Conversely, different scenario IDs do not protect an otherwise duplicated scenario.

Metadata retrieval returns exactly the first `min(5, eligible_reference_count)` records ordered by descending count of matching frozen metadata fields and ascending stable reference ID; zero-match records are excluded. Every returned metadata pair requires a disposition. The absolute two-field rule remains an additional high-priority flag and can add pairs outside that top five.

### Structural and templating flags

A pair is flagged for structural review when either condition holds:

- identical structural signatures plus the same intent family and task subtype; or
- at least two exact same-type component matches, where each matched component contains at least five normalized word tokens.

Corpus summaries report exact normalized titles, ingredient names, ordered exact amount/unit signatures, ingredient counts, method counts, exact method/garnish components, and contiguous eight-word sequences by frequency. Any single exact structural signature appearing in four or more examples, any exact title in three or more, or any exact component of at least five words in three or more creates pair flags between the members. Counts below these limits remain descriptive. These rules implement D-046's diversity audit without treating common `ml` units or cocktail vocabulary as failures.

## Human-readable semantic disposition

Every flag receives exactly one current disposition, written without access to desired corpus counts or later model performance. One disposition can cite several triggering signals for the same canonical pair; it cannot dispose of a different pair by analogy.

The record contains:

```json
{
  "audit_id": "chatgnt-dataset-contamination-audit-v1",
  "flag_id": "dataset-audit-flag-v1-0001",
  "pair_id": "stable-canonical-pair-id",
  "candidate_example_ids": ["dataset-v1-001", "dataset-v1-002"],
  "reference_collection": "internal_dataset",
  "reference_id": "dataset-v1-002",
  "views": ["prompt"],
  "triggers": [],
  "complete_text_reviewed": true,
  "same_user_goal": "yes|no|uncertain",
  "same_situation_concept_source_or_artefact": "yes|no|uncertain",
  "answer_reusable_with_surface_changes_only": "yes|no|uncertain",
  "response_overlap": "none|generic|distinctive_template|substantive_duplicate|exact",
  "withheld_domain": null,
  "decision": "allow|revise_or_replace|escalate_uncertain",
  "reason_codes": [],
  "rationale": "concise evidence grounded in both complete records",
  "reviewer_type": "human_review|adversarial_llm_review",
  "reviewer_identity": "attributable identity",
  "reviewed_at_utc": "RFC-3339 UTC",
  "candidate_content_sha256": ["..."],
  "source_manifest_sha256": "..."
}
```

For scenario duplication, `revise_or_replace` is required only when all three collision questions are `yes`. Any `no` permits `allow` on that ground. `uncertain` requires `escalate_uncertain`; unresolved uncertainty fails the current generation and can be addressed only after the separate contract-amendment process, not by lowering a threshold.

Distinctive response reproduction, repeated reusable answer progression, or templating can require replacement even when the prompts are not the same scenario. Shared domain, intent, task form, schema, ordinary cocktail language, robustness mechanism, or broad advice is allowed when the substantive answer differs. A numerical score is never the rationale by itself.

Automatic failures use the same record with the applicable facts prepopulated and `decision: revise_or_replace`. The reviewer confirms the complete texts and remedy but cannot convert exact equality into `allow`.

## Withheld-domain audit

The excluded subject matter is substantive photography, tabletop games, and pottery/ceramics in either prompt, metadata, or target response. Incidental uses such as “focus,” “frame,” “game plan,” “turn,” “clay colour,” or “glaze” outside those domains do not decide a violation.

The implementation creates `config/dataset-withheld-lexicon-v1.json` under a new closed JSON Schema and `data/evaluation/dataset-withheld-lexicon-calibration-v1.jsonl` before production. The lexicon contains exactly the three domain IDs, and for each a unique list of terms stored as normalized token arrays plus a stable term ID. Matching first applies the frozen text normalization, then tokenizes into maximal contiguous Unicode letter-or-number sequences; hyphens and punctuation are boundaries. A one-token term matches one complete token and a multi-token term matches one contiguous token sequence. No substring matching or stemming is permitted, so desired inflections and spelling variants must be explicit terms.

The calibration contains versioned positive and negative records for every term, including punctuation/hyphen variants and ambiguous incidental uses. A positive fixture must yield the declared domain/term match; a negative fixture must not yield that match. Lexicon occurrence always creates a review flag and never automatically decides substantive presence, including in free-text metadata. The schema, lexicon, fixture, extractor implementation, record counts, and digests freeze at the one implementation review and enter the source manifest. No term or matching rule may change after a production generation is created.

Each of the 200 complete records is also covered by three collection-level, attributable attestations—one per withheld domain—confirming that the reviewer inspected the complete prompt, metadata, and response collection and found either no material occurrence or linked every occurrence to a flag disposition. The audit cannot pass on keyword absence alone.

A substantive occurrence uses `withheld_domain_violation` and requires replacement. If a prohibited source collection itself contains a withheld domain, that does not contaminate the supervised corpus; it is reported as source context and does not weaken the supervised exclusion.

## Candidate reduction and review workload

The complete Cartesian checks remain machine evidence, but manual review is the deterministic de-duplicated union of:

- all automatic failures;
- every top-five lexical neighbour for every eligible query/view/source collection;
- every top-five semantic neighbour for every eligible query/view/source collection;
- every top-five nonzero metadata neighbour for every eligible query/source collection;
- every above-threshold lexical or semantic pair;
- every metadata, component, phrase, structural, frequency, or withheld-domain flag; and
- every truncated pair already in that union.

Pairs are canonicalized and de-duplicated before review. The immutable machine build reports counts before and after union by signal, view, and collection, and stores every triggering rank and score. Thresholds can add pairs but never remove a member of the frozen top-five lexical, semantic, and metadata workload. Reviewers assess this frozen union, not all Cartesian pairs.

The implementation may batch the presentation of flags but may not batch their decisions: every canonical flag has one separately attributable disposition. A flag remains open until its current candidate and source hashes match the record.

## Source-use and provenance audit

Text similarity cannot prove how a draft was produced. The audit therefore separately verifies:

- every frontier-model event has a nonempty model identity and passes the prohibited-Qwen identity gate;
- candidate provenance summaries agree exactly with their complete event chains;
- no event occurs after terminal acceptance or rejection;
- every current content hash is the hash that passed independent quality review and terminal acceptance; and
- the project author records one corpus-level source-use attestation that the named, existing worked, development, calibration, and target-model materials were not supplied as drafting seeds, templates, paraphrase sources, or selection signals; and
- the project author records a separate no-heldout-access attestation, bound to the Stage 4 boundary and repository state, that exact held-out prompts did not exist or were not accessible and were not opened during dataset authoring or audit.

Both attestations are attributable process claims, not cryptographic proof. The no-heldout-access statement does not imply that absent material was inspected. Exact held-out prompts remain unavailable and are not searched. Attempting to open or add a held-out source is a protocol breach and aborts the run.

## Failure, replacement, and later generations

A failed current example is never silently edited and its historical accepted event is never rewritten. This audit defines no replacement ledger, active-set overlay, supersession event, replacement path, or downstream exception. Any automatic failure or `revise_or_replace`/unresolved disposition makes Step 10 fail closed with the complete entry-generation evidence retained unchanged.

Before any candidate can be replaced, a separate, versioned dataset-contract amendment must choose and implement a representation that the ordinary authoring, split, projection, rendering, and freeze validators understand. It must bind replacement candidate/event paths and preserve the complete prior lifecycle evidence while yielding exactly 200 active accepted records under the amended contract. Alternatively it may define a new dataset version whose complete lifecycle is unambiguous while retaining dataset v1 entry evidence externally. This Step 10 specification does not choose between those designs and grants no authority to write replacements.

Only after that amendment is specified, reviewed, implemented, and verified may a later audit generation be authorised. The later generation must rerun the complete audit against the whole resulting corpus and every frozen prohibited source. Local rechecking is insufficient. Its manifest binds the decisive prior flags/dispositions, contract-amendment identity, predecessor generation ID, and new corpus identities; all earlier evidence remains immutable.

## Required outputs

The atomic machine build writes canonical artefacts under a new immutable `data/dataset-v1/audit/v1/generation-NNN/` directory:

- `generation-manifest.json` — generation ID, predecessor when any, all input, extractor, implementation, package, model, command, and artifact identities;
- `source-manifest.json` — the frozen path-aware source inventory;
- `extracted-references.jsonl` — canonical prohibited-reference inventory with provenance;
- `exact-and-structural-report.json` — complete deterministic counts and automatic failures;
- `lexical-neighbours.jsonl` — top-five evidence and threshold triggers;
- `metadata-neighbours.jsonl` — top-five nonzero metadata evidence and additional metadata triggers;
- `semantic-evidence.json` — closed MiniLM inventory, token diagnostics, ranks, scores, and generator provenance;
- `flags.jsonl` — canonical de-duplicated review workload;
- `machine-summary.json` — machine counts, automatic failures, immutable flag-set SHA-256, and generation result `awaiting_review` or `machine_fail`.

The build does not create or modify human judgments. The reviewer separately authors canonical inputs under `data/dataset-v1/audit/v1/review/generation-NNN/`:

- `dispositions.jsonl` — exactly one disposition per immutable flag;
- `withheld-domain-checks.jsonl` — three collection-level attestations plus linked term flags;
- `source-use-attestation.json`; and
- `no-heldout-access-attestation.json`.

Finalization consumes those files and the immutable generation, then atomically creates a new no-overwrite `data/dataset-v1/audit/v1/finalization-NNN/` containing `finalization-manifest.json`, `audit-summary.json`, and generated `audit-report.md`. The finalization ID is unique and binds exactly one generation ID, flag-set identity, review-input identities, implementation identity, and result. It never writes into the generation directory or reviewer-input directory.

No report embeds exact held-out material. No output contains hidden reasoning. All JSONL is canonical UTF-8 with LF endings; all JSON identities use the repository canonical serializer.

## Implementation and execution sequence

1. Conduct one adversarial review of this specification without candidate or held-out contents. That bounded review is complete; this is the sole amendment pass. Freeze the amended document identity and stop specification review.
2. Implement the source extractors, comparison views, deterministic checks, evidence schemas, CLI, and focused synthetic tests. The tests cover normalization, exact matches, every threshold boundary immediately below/equal/above, tie order, pair de-duplication, truncation, withheld variants, stale identities, orphan dispositions, atomic no-overwrite behavior, generation/finalization binding, and fail-closed replacement decisions.
3. Conduct one implementation review using synthetic fixtures and source identities only. Freeze implementation/schema identities and the extracted-reference inventory identity. Do not inspect production similarity results during this review.
4. Run one atomic production build into a new generation ID. The command creates every machine artifact in a temporary sibling directory, validates the complete bundle, fsyncs files/directories as supported, and atomically renames it to the requested final path only if that path does not exist. It refuses overwrite, resume, partial reuse, symlink targets, and an existing generation ID. A failed build leaves no final generation directory.
5. Complete exactly one disposition for every immutable flag and the three withheld/source-use/no-heldout attestations. Do not rerun retrieval to obtain a more convenient flag set.
6. Run the separate no-overwrite finalizer. If all flags allow and every gate passes, close Step 10. If any flag requires replacement or remains uncertain, finalize the generation as failed and stop; candidate change requires the separate contract amendment described above.
7. Correct a genuine implementation defect only through a documented audit amendment that explains the defect and invalidates all prior outputs. A defect correction is not threshold tuning.

## Reproducible commands

The implementation must expose these repository-root commands. Exact script names and options are part of the implementation-review identity. Initial production uses `generation-001` and `finalization-001`; any later authorised generation/finalization increments its three-digit ID, names its predecessor, and never reuses a prior path or ID:

```bash
uv run --frozen python scripts/verify_dataset_contamination_audit.py --mode specification
uv run --frozen python scripts/verify_dataset_contamination_audit.py --mode sources
uv run --frozen python scripts/build_dataset_contamination_audit.py --generation-id generation-001 --output data/dataset-v1/audit/v1/generation-001
uv run --frozen python scripts/verify_dataset_contamination_audit.py --mode generation --generation-dir data/dataset-v1/audit/v1/generation-001
uv run --frozen python scripts/finalize_dataset_contamination_audit.py --generation-dir data/dataset-v1/audit/v1/generation-001 --review-dir data/dataset-v1/audit/v1/review/generation-001 --finalization-id finalization-001 --output data/dataset-v1/audit/v1/finalization-001
uv run --frozen python scripts/verify_dataset_contamination_audit.py --mode final --finalization-dir data/dataset-v1/audit/v1/finalization-001
uv run --frozen python -m unittest discover -s contract_tests -v
uv run --frozen python -m unittest discover -s tests -q
git diff --check
```

Only the build and finalization commands write generated artifacts, and both are atomic and no-overwrite. Reviewer files are authored between them. Verification modes are read-only. Production commands log package versions, wall-clock timestamps, device, model/revision, command arguments, exit status, and stdout/stderr SHA-256. The frozen historical test suite runs in isolation, never concurrently with another suite that shares fixtures.

## Pass and stopping conditions

The audit passes only when all of the following are true:

- the active set contains exactly 200 terminally accepted, structurally valid, unallocated examples and still satisfies every frozen coverage target;
- every source and normative identity matches;
- all exact, lexical, semantic, metadata, structural, component, phrase, provenance, and withheld checks completed under this frozen method;
- there are no automatic failures in the active set;
- every flag has exactly one current, hash-matched disposition and none is `escalate_uncertain` or `revise_or_replace`;
- all three withheld-domain attestations, the source-use attestation, and the separate no-heldout-access attestation are present and internally consistent;
- the selected finalization binds exactly one immutable generation and reports `pass`;
- no exact held-out prompt was accessed, no Qwen/model generation occurred, and no split or training artefact was created; and
- focused audit tests, the existing contract suite, the isolated 128-test historical suite, compilation checks, and `git diff --check` pass.

The stopping condition is evidence closure, not exhaustion. Once these gates pass, Step 10 stops. It does not perform optional wording improvements, tune thresholds, seek more reviewers, or run additional semantic models. Step 11 may then assign scenario-isolated splits and construct the dataset freeze package. Any uncertainty, automatic failure, or `revise_or_replace` decision closes the current finalization as failed; no candidate is changed until a separately authorised dataset-contract amendment exists.

## Interpretation limits

Passing means no duplication, prohibited-project-source contamination, or withheld-domain violation was found by this declared, reproducible project audit. It does not prove independence from unknown model pretraining, prove that no unrecorded source influenced an author, or establish held-out generalisation. MiniLM truncation, RapidFuzz subset behaviour, broad metadata, and finite human judgment remain disclosed limitations. The retained complete-text dispositions and source-use attestation make those limits visible rather than converting retrieval scores into stronger claims.
