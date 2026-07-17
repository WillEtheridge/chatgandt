# Implementation Review of the Dataset Contamination Audit

> **Historical review.** The implementation it assesses was removed after its
> first production generation proved disproportionate to the research risk.

- **Reviewed specification:** `docs/dataset-contamination-audit-specification.md`
- **Specification SHA-256:** `0e87888a02caba963ce37f5d39c8e71929b2f7e89cbab6ef03b85692f1b4f820`
- **Review date:** 2026-07-16
- **Review type:** Single bounded pre-production implementation review
- **Verdict:** **Amend before production**

## Scope and method

This review checked D-058, the frozen specification and its adversarial review, the audit module, three CLIs, five audit schemas, the source manifest, withheld lexicon and calibration, and the focused contract tests. It used static inspection, source-identity/extractor verification, deterministic five-shot equality, and synthetic tests only.

It did not run the production builder, create a generation, review, or finalization directory, inspect production similarity results, inspect or create held-out prompts, query or load a model, assign splits, render training data, train, or modify candidate records. The only repository write is this review record.

The permitted checks produced:

- specification/source verifier: pass, `63` bound sources;
- extracted prohibited-reference inventory: `1,386` records, canonical collection SHA-256 `b6c9b78a10e22032c6e476c350c5d4d5aa0ab817f6c316c1ce9e4d05f9ec2cf6`;
- withheld calibration: pass, `48` cases and `24` terms;
- focused synthetic tests: `10/10` pass;
- deterministic five-shot object equality: pass, asset `five-shot-v3`, five worked examples; and
- canonical-file check on that same selected asset: fail, as described in C-01.

Passing the existing focused tests does not establish conformance: several tests encode only a reduced contract, and one test demonstrates that malformed attestations are presently accepted.

## Critical findings

### C-01 — The documented production build cannot pass its five-shot control

`build_generation()` loads `config/prompts/five-shot-v3.json` with `load_canonical_object()` before any production extraction (`chatgnt/dataset_contamination_audit.py:504`). The selected prompt is intentionally pretty-printed rather than one-line canonical JSON, so that loader rejects it even though its parsed object is byte-for-byte deterministically reconstructible at the object level.

The permitted control check failed with:

```text
ContractError: config/prompts/five-shot-v3.json: expected one canonical JSON object plus LF
```

Loading the same file as an ordinary strict source object and comparing it with `expected_five_shot_asset_v3()` returns `True`, with `worked_example_count == 5`. Therefore the failure is in the implementation's input-format assumption, not the frozen asset. Initial production cannot begin under the declared command.

**Required amendment:** validate the pinned file identity, parse it with the source-object contract used by the prompt subsystem, and retain exact deterministic object/content equality. Add a synthetic or read-only control test that exercises the exact build-side validation path.

### C-02 — Source extraction and source-specific joins do not implement the frozen inventory contract

Several omissions can remove prohibited material or accept a misbound run:

- Preflight rows emit raw-response and joined-exchange views but never emit the required standalone prompt view (`lines 337–355`).
- Formal/local/CUDA joining checks only scheduled response count, not exact equality with the manifest's scheduled `(system_id, prompt_id, repeat_index, attempt_index)` population (`lines 399–425`). A same-size substituted schedule can pass.
- CUDA extraction does not verify the manifest's declared system adapter state against each response, despite the frozen CUDA-specific contract.
- Parsed raw outputs are treated as schema-valid based on a partial key/type probe rather than validation against `chatgnt-response-v1`; extra keys and invalid nested values can acquire parsed views (`lines 213–229, 346–349`).
- Worked-example IDs are not required to be five unique nonempty IDs; exact duplicates may silently collapse in the final record-ID map (`lines 321–331, 427–432`).
- Authoring-guide anchors are selected globally by line prefix under whichever heading was last seen, not only within the frozen qualitative-review subsections and garnish paragraph (`lines 375–381`).
- The generated source manifest contains neither per-source extracted-record counts nor the canonical extracted-record digest required by the specification (`lines 283–295`).

The source verifier passes the current frozen files because those files happen to satisfy much of the assumed shape; it does not prove that the extractor enforces the frozen source-specific contracts.

**Required amendment:** implement and test every declared source-specific join and extraction invariant, including preflight prompt views, exact schedule equality, CUDA system/adapter identity, response-schema validation, worked-ID uniqueness, scoped guide extraction, and extracted-record identities in the source manifest.

### C-03 — The machine build does not produce the complete frozen evidence or workload

The nine filenames are created, but their substantive contents omit required gates and summaries:

- There is no explicit shared-`scenario_id` review trigger.
- The exact/structural report contains only automatic exact failures and structural-signature frequencies. It omits the required title, ingredient-name, amount/unit, ingredient-count, method-count, exact component, and contiguous eight-word frequency summaries.
- The required counts before and after union by signal, view, and collection are absent from `machine-summary.json`.
- Authoring-guide `response_fragment` references are excluded from semantic inventory because inventory membership requires the reference view itself to be a key in `SEMANTIC_THRESHOLDS` (`line 567`), even though response fragments are eligible references for complete-response queries.
- MiniLM token diagnostics are stored only for the reduced semantic inventory, not retained on every canonical comparison view as specified; selected triggers also do not record the pair's truncation state.
- `union_flags()` canonicalizes view-record IDs, not the substantive candidate/reference owner pair (`lines 268–280`). The same two complete records reached through prompt, scenario, response, or exchange views become separate flags rather than one canonical flag retaining all views and signals.
- `audit-report.md` contains only generation ID, finalization ID, result, and flag count (`lines 670–672`); it is not the required deterministic report of checks, thresholds, findings, and dispositions.

These are not presentation-only gaps. They alter which pairs receive review and prevent an auditor from proving that all frozen gates ran.

**Required amendment:** implement the complete evidence inventories and canonical owner-pair union, restore every eligible top-five semantic workload, annotate truncation, generate the mandated count breakdowns, and produce a report that deterministically summarizes every frozen gate and disposition result.

### C-04 — Disposition and attestation finalization can accept stale or malformed review evidence

None of the five audit schemas is invoked by generation verification or finalization. `validate_dispositions()` checks only flag ID, pair ID, source-manifest digest, uniqueness, and decision (`lines 637–650`). It does not require or bind the disposition fields frozen in the specification, including complete-text review, collision answers, response overlap, candidate IDs/content hashes, reason codes, reviewer identity, or review timestamp.

Attestations are checked only for three domain names and `attested: true` (`lines 655–664`). They are not bound to audit ID, generation ID, flag-set identity, corpus/source identity, reviewer, timestamp, or linked term flags. The focused finalization test supplies `{"attested": true}`—invalid under the attestation schema because reviewer identity and timestamp are absent—and receives a passing finalization. Thus the current test suite positively demonstrates the false-pass path.

`escalate_uncertain` and `revise_or_replace` do produce a failed result, which is correct, but that fail-closed decision cannot compensate for review records whose substance and freshness were never validated.

**Required amendment:** validate every review input against closed, role-specific schemas; bind it to the generation, flag set, source manifest, canonical members, and current candidate content hashes; enforce the three collision-answer decision rules and automatic-failure constraints; and require linked withheld occurrences and attributable review metadata.

### C-05 — Read-only verification cannot establish generation or finalization integrity

`verify_generation()` checks the directory filename set, only the artifact entries that the manifest happens to list, and the flags digest/count in the summary (`lines 622–634`). It does not require the manifest's artifact inventory to be complete and unique, validate any schema, compare audit/generation IDs across artifacts, bind the manifest's source digest to `source-manifest.json`, recompute automatic-failure/result consistency, or compare recorded implementation identities with the frozen implementation.

`verify_final()` checks only the three filenames, artifact entries listed by the manifest, and result/generation equality between manifest and summary (`lines 681–690`). It does not validate finalization ID syntax, generation-manifest binding, flag-set binding, review-input identities, implementation identity, audit ID, or schema. A modified binding field can therefore verify if the two generated report artifacts remain unchanged.

The schemas themselves are also not closed evidence contracts: four use `additionalProperties: true`, the flag trigger accepts an arbitrary object, and the generation/finalization schemas describe only a handful of top-level fields.

**Required amendment:** make the schemas closed and complete, validate every artifact, require exact artifact sets inside manifests, recompute all cross-artifact identities and outcomes, verify current frozen implementation/source identities, and test stale generation, flag, review-input, implementation, and finalization bindings independently.

## Material findings

### M-01 — Atomic/no-overwrite behavior is only partially enforced

The sibling temporary-directory rename and overwrite refusal work in the focused synthetic test. However, the CLIs do not constrain output paths to the declared audit roots, require basename/ID equality, reject a symlinked output parent, or prove that generation/finalization IDs have not been used elsewhere. `finalization_id` is not syntax-validated at all. The generation manifest also omits the required canonical command arguments, package versions, exit status, and stdout/stderr identities.

**Required amendment:** enforce declared root, real-parent, basename, ID, and predecessor rules; validate finalization IDs; and record the complete frozen execution identity. Add symlink-parent, wrong-root, wrong-basename, reused-ID, interrupted-write, and finalizer no-overwrite tests.

### M-02 — Source/view collection boundaries are too coarse in places

All three calibration files share `source_collection: "calibration"`, so top-five retrieval is over their combined population rather than per declared calibration collection. Standalone prompt records from development/run prompt files collapse correctly today because their file digests and content agree, but that behavior is incidental to record-ID construction and is not an explicit `(prompt_id, normalized_sha256)` de-duplication invariant.

**Required amendment:** assign stable declared source-collection IDs and test top-five equality separately for every eligible source/view collection, including collections smaller than five and ties at rank five.

### M-03 — Focused boundary coverage is substantially below the frozen test matrix

The ten focused tests cover one generic `90.0` threshold boundary, lexical tie ordering, a two-signal union, three small withheld examples, one metadata-ineligibility check, basic atomic cleanup/no-overwrite, one stale artifact, orphan/stale/missing dispositions, one passing finalization, and one replacement failure.

They do not cover normalization; the `92/95` lexical and `0.82/0.86/0.88` semantic boundaries; semantic or metadata top-five/ties; fewer-than-five collections; exact prompt/response/exchange failures; scenario IDs; structural/component/frequency/eight-word gates; truncation; all lexicon terms and calibration-schema validity; source-specific extractors/joins; canonical multi-view union; complete artifact generation; schema rejection; implementation/source identity drift; attestation bindings; uncertainty; finalization ID/path rules; or parent-symlink behavior.

**Required amendment:** add focused synthetic tests at every frozen boundary and ensure they exercise the production functions rather than isolated helpers only.

### M-04 — Implementation and protocol identities are recorded incompletely

The generation manifest records hashes for the module, three CLIs, and five audit schemas, but the verifier does not compare them with the reviewed identities. The implementation inventory omits the focused tests and withheld lexicon/calibration schemas, while package/model execution details required by the specification are absent. The source manifest does bind the lexicon controls and frozen normative documents, but does not include D-058 as a separate normative identity or the extracted-reference digest.

**Required amendment:** declare one complete reviewed implementation/protocol identity set and enforce it during build and verification.

## Minor findings

### m-01 — Symmetric internal checks duplicate machine evidence

Internal queries evaluate both directions. Automatic exact failures and neighbour rows can therefore be duplicated even where the review flag later coalesces. This inflates counts and makes the absent pre/post-union accounting harder to interpret. Emit canonical unordered internal evidence once, or explicitly retain both directional ranks while counting the canonical pair once.

### m-02 — CLI success wording is ambiguous for a failed audit

The finalizer CLI prints `{"result":"pass"}` whenever finalization execution succeeds, even when the generated audit result is `fail`. Distinguish command status from audit result to avoid operational misreading.

### m-03 — Dead generic extraction code obscures the closed-extractor claim

`_extract_text_fields()` is unused. Removing it would make it clearer that no generic recursive fallback extractor is part of v1.

## Reviewed identities

These are the exact candidate implementation identities reviewed. Because the verdict is amend, they are evidence of the rejected implementation state, not authorization to run production:

| Path | SHA-256 |
| --- | --- |
| `chatgnt/dataset_contamination_audit.py` | `99f271118a0cf3b3c38adb102eb8950c518250db4f03f9936f0016c04ccdc39e` |
| `scripts/build_dataset_contamination_audit.py` | `eaa9af643e1fcdccf9c1ae66ec9188118a3f368b66a20deb7957cbf4c54f5972` |
| `scripts/verify_dataset_contamination_audit.py` | `baaf0098d8367f0f2f12a530bd010433037ba442e9b0ed16cdb676410a17b80d` |
| `scripts/finalize_dataset_contamination_audit.py` | `e77a9de0e46d3e5dfc87a09b695b2efc7b050cbf57364687410b3a6f956e4b84` |
| `schemas/dataset-contamination-audit-flag-v1.schema.json` | `8d50e920540d183d456345662c3914bd58b19e3418e035f1fc0aeca67a6f3b98` |
| `schemas/dataset-contamination-audit-disposition-v1.schema.json` | `f98fc01ed2a9e791518eeeb1b492e075fdc7f1d8475540a8911525c56b9f9cec` |
| `schemas/dataset-contamination-audit-generation-v1.schema.json` | `19f0bf6cd0f862f75fa95f09d6bc3c2c44cf486779b94c227d8336ca7801a34b` |
| `schemas/dataset-contamination-audit-attestation-v1.schema.json` | `86c3e7c660c8a915aab2b7185aac3a616fb489235f3b465eda7d6011a69396df` |
| `schemas/dataset-contamination-audit-finalization-v1.schema.json` | `35b87afdb9013e8077e7665b3d2195e8af8c266238f44dc90c315a481ba37d8e` |
| `contract_tests/test_dataset_contamination_audit.py` | `9d61696771549a8ea7d333ee1b207445b11d127d4648480c10252451b1d8e513` |
| `config/dataset-contamination-audit-sources-v1.json` | `5779cf8b8cf96c159623ac7980e5c78f8f9eba7f0d9cb7edf978705b2cedb5b3` |
| `config/dataset-withheld-lexicon-v1.json` | `c3f6eb746559b44ea94a57e760b394618287bb25d21239015df543f979fce81d` |
| `schemas/dataset-withheld-lexicon-v1.schema.json` | `255105b0c588a0cc780a98273c14121f37e14f7bac515623a7e841e905ca94fd` |
| `schemas/dataset-withheld-lexicon-calibration-v1.schema.json` | `6cf615aee2f9bd1aa64b07660686775a441793f403a9ac7ad6caa81ebb0e985c` |
| `data/evaluation/dataset-withheld-lexicon-calibration-v1.jsonl` | `04160bdb5eb15941580c270ad22b9916784773757c0f2bd4df6cbe725b2abcef` |

## Stopping decision

Do not run `generation-001`. The implementation does not yet satisfy D-058 or the frozen specification, and its current production entry point is non-runnable. Remediation must be limited to the findings above, followed by synthetic/source-identity verification of the amended implementation and recording of its new identities before any production content is processed. No thresholds, source set, views, or substantive decision rules should change during that remediation.
