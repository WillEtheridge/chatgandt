# Dataset v1.2 Freeze

- **Date:** 2026-07-16
- **Status:** Frozen; Stage 4 readiness review passed
- **Bundle:** `data/dataset-v1/frozen-v1.2/`
- **Manifest SHA-256:** `bbc749a1a840213fa9b09680df9da7b06e35cb0c7deceab60ecd2744e354aca5`
- **Command:** `UV_CACHE_DIR=/tmp/chatgnt-uv-cache HF_HUB_OFFLINE=1 uv run --frozen python scripts/freeze_dataset_v1_2.py`

## Result

The first valid deterministic allocation was accepted without manual selection or rerunning for a preferred composition:

| Set | Count | Per intent family |
| --- | ---: | ---: |
| Training | 160 | 32 |
| Validation | 40 | 8 |
| Pilot, drawn only from training | 40 | 8 |

All 200 active scenarios are unique, so no scenario crosses training and validation. The allocation is exact and requires no split-deviation record.

Validation covers all input forms, complexities, coverage slices, constraint status, and robustness roles, across 14 topics and 22 task subtypes. The pilot covers the same required axes across 16 topics and 35 task subtypes.

## Frozen files

| File | Records | SHA-256 |
| --- | ---: | --- |
| `candidates.jsonl` | 200 | `af3e6ae0d1cdc756e57adf5ba2950b256c70ea0423fb894b0d21f44d4ef59b97` |
| `workflow-events.jsonl` | 772 | `9fb18167271982dd808a0b3d5892050952e97366188dd77cdb8f140cca4c86f9` |
| `train.jsonl` | 160 | `1690561db24ba4d2ae3c56f0ba4e988643994cb2add51f01beef901ebf5095b2` |
| `validation.jsonl` | 40 | `b9e344f6582a9ebe4d9b83801cf71acc2abf2c4f95efd71bcd58eafbfb36bdc5` |
| `pilot.jsonl` | 40 | `a8e4ad6ea6923c18e1111d16c00c07b40004d9533c04d32d6550edf2521565dd` |
| `allocation-report.json` | — | `67582f3446f756e2487dc1171e82961ed58a4bf697926735f1b96defca526a48` |

The freeze command was rerun into a temporary directory and every output matched byte for byte.
