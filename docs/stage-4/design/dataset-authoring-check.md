# Dataset Authoring Guide Check

- **Stage:** 4 — Build and freeze dataset v1
- **Step:** 7 — Authoring guide and quality rubric
- **Date:** 2026-07-15
- **Result:** Pass

## Frozen decisions

- Automated structural and scope gates remain separate from qualitative review.
- Underlying-answer quality, metaphorical coherence, and recipe-style execution each use `pass`, `revise`, or `reject`.
- Every dimension must pass; strengths cannot compensate for a non-pass dimension.
- Dimension results map deterministically to the existing workflow outcomes.
- The guide maps all 17 frozen reason codes to concrete review problems.
- Candidate production begins with a 10-record calibration batch and then uses batches of at most 20.
- Separate drafting and review contexts, bounded material revision, and deterministic terminal acceptance preserve attributable judgment without requiring per-example human approval.
- Calibration fragments are authoring aids, not eligible dataset records.

## Verification

```text
Rubric/config parity check
result: pass
rubric_id: chatgnt-dataset-authoring-v1

uv run --frozen python scripts/verify_dataset_contract.py --mode contract
result: pass

uv run --frozen python -m unittest discover -s contract_tests -v
Ran 14 tests
OK

uv run --frozen python -m unittest discover -s tests
Ran 128 tests
OK

git diff --check
result: pass
```

## Original Step 7 identities

| Artefact | SHA-256 |
| --- | --- |
| Authoring guide at the original Step 7 freeze | `98a7380605325a034272373136e0b25c55318ddfd66b86c9c00a7e64cf23a670` |
| Machine-readable rubric v1 | `e8fcd865babf89a340ad5d4fffc5a9fb9329b76a308b08fb792099d737757d88` |

At the time of the original check, no candidate supervised example or exact held-out prompt had been authored. The target Qwen model was not queried, loaded, or trained.

## Calibration amendment 01

The first 10-candidate calibration batch exposed that “relevant final detail” permitted method-like content in `garnish`. Decision D-052 amended only the Stage 4 teaching-target guide and created machine-readable rubric v1.1. The frozen Stage 3 behavioural contract and evaluation identities were not changed.

| Amended artefact | SHA-256 |
| --- | --- |
| Authoring guide at amendment 01 | `f507248c89630be71b30bd72d4eedbe9741d368cb68cb4760c32bc130498f4f8` |
| Machine-readable rubric v1.1 | `4453f3125f5b99f1f335b72f0118946b8a7923b1ecf1f21dbfde198cb5211bbd` |

The amended batch remains unresolved pending direct project-author inspection. No Qwen output, held-out prompt, split assignment, or training activity was introduced.

## Calibration amendment 02

Direct project-author inspection found that schema-valid, garnish-corrected responses could still read as ordinary prose placed inside recipe fields. Decision D-053 therefore amended the Stage 4 teaching-target guide and created machine-readable rubric v1.2 with a holistic bartender test. The frozen Stage 3 behavioural contract and evaluation identities remain unchanged.

| Amended artefact | SHA-256 |
| --- | --- |
| Current authoring guide | `7c690afaa78ed4d210c9479b9bebe174833dfb69a98c5e6348ddf73b15dec43b` |
| Machine-readable rubric v1.2 | `019cbe1532d0da4a41610918194bb35bf986f6b912bfa42561a482e6237f3e5c` |

All ten calibration candidates have current v1.2 rewrites, passed direct project-author review, and were accepted. No candidate has been allocated to a split, and no Qwen output, held-out prompt, or training activity was introduced.

The current v1.2 batch passed the authoring validator with no warnings, rubric/config parity, JSON integrity checks, all 14 additive dataset-contract tests, all 128 frozen project tests, and `git diff --check`. Candidate and event identities are recorded in the calibration report.

## Production amendment 03

Batch 02 review found a systematic score-like measurement and generic method scaffold across otherwise useful, coherent drafts. Project-author adjudication retained `ml` as the expected default and narrowed the defect to implausible or routinely normalised proportions plus repeated reasoning architecture. Decision D-055 created authoring rubric v1.3 and froze a one-pass construction overlay before any candidate revision.

| Amended artefact | SHA-256 |
| --- | --- |
| Current authoring guide | `04a3a75604a2ef77e41a210a20fcb2b054cf07703104954ea198fdab7eb7f2b1` |
| Machine-readable rubric v1.3 | `4d8df1ee6db926cc4d4e28a55f8bffbe06aa81eac2d1cc959a554364e4a65201` |
| Frozen Batch 02 revision overlay | `49e5606c11bd1ac333c8ee92afe2d86de5e2caba13a358768aac20c83b3a293b` |

The amendment changes only the Stage 4 teaching-target standard. The frozen Stage 3 behavioural contract and evaluation identities remain unchanged. No held-out prompt, Qwen output, split assignment, or training activity was introduced.

The authorised pass completed with all frozen overlay gates satisfied. Terminal review passed 15 candidates, requested three concrete local repairs, and raised two templating findings whose claimed exact collision was not reproduced by independent verification. No further whole-batch correction is authorised; the five outcomes remain for project-author disposition.

## Production amendment 04

Batch 02 demonstrated that requiring a human `accepted` event for every passing example does not scale and duplicates already-recorded qualitative judgment. Decision D-056 therefore separates judgment from terminal bookkeeping. A human or frontier-model reviewer still must attest that all three non-compensatory dimensions pass in an independent context. The code-owned `chatgnt-dataset-terminalizer-v1` validator may then append `accepted` events deterministically after validating the complete batch.

The finalizer is fail-closed, dry-run by default, idempotent, preserves candidate bytes and content hashes, refuses unresolved non-passes, checks reviewer independence from the latest content actor, validates the proposed post-state, and atomically replaces only the workflow-event JSONL file. Frontier models remain unable to emit `accepted` events directly, and existing human acceptances remain valid.

Verification after amendment 04:

```text
uv run --frozen python scripts/verify_dataset_contract.py --mode contract
result: pass

uv run --frozen python -m unittest discover -s contract_tests -v
Ran 19 tests
OK

uv run --frozen python -m unittest discover -s tests -q
result: pass

Batch 02 terminalizer dry run
accepted_count: 20
written: false

Batch 02 terminalizer write
accepted_count: 20
written: true

Batch 02 terminalizer idempotence run
accepted_count: 0
written: false
```

Batch 03 exercised the amended workflow end to end without human acceptance: 19 initial passes, one local factual repair, one fresh terminal pass, 20 deterministic acceptances, and a zero-addition idempotence run. The batch authoring validator reports 20 accepted, zero rejected, zero unresolved, and no warnings.
