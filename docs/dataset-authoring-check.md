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
- Separate drafting and review contexts, bounded material revision, and project-author acceptance preserve attributable judgment.
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

## Key identities

| Artefact | SHA-256 |
| --- | --- |
| Authoring guide | `98a7380605325a034272373136e0b25c55318ddfd66b86c9c00a7e64cf23a670` |
| Machine-readable rubric | `e8fcd865babf89a340ad5d4fffc5a9fb9329b76a308b08fb792099d737757d88` |

No candidate supervised example or exact held-out prompt was authored. The target Qwen model was not queried, loaded, or trained.
