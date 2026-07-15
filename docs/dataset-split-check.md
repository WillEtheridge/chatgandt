# Dataset Split and Pilot Selection Check

- **Stage:** 4 — Build and freeze dataset v1
- **Step:** 6 — Scenario-isolated allocation
- **Date:** 2026-07-15
- **Result:** Pass

## Implemented procedure

The allocator:

- requires 200 terminally accepted, family-balanced, unallocated records;
- groups records by scenario and rejects cross-family scenario groups;
- uses coverage-aware dynamic programming to assign whole groups to validation;
- targets 40 validation examples and eight per family;
- records rather than hides any scenario-driven deviation;
- selects exactly 40 representative training-only pilot examples;
- returns deep-copied allocated records and canonical projections without mutating input; and
- supports dry-run reporting or an explicit atomic output directory.

No real dataset was used. All checks used temporary synthetic records and no model operation occurred.

## Live verification

```text
uv run --frozen python scripts/assign_dataset_splits.py --check-config
result: pass

uv run --frozen python -m unittest discover -s contract_tests -v
Ran 14 tests
OK

uv run --frozen python -m unittest discover -s tests
Ran 128 tests
OK

python -m compileall -q chatgnt scripts contract_tests
result: pass

git diff --check
result: pass
```

## Key identities

| Artefact | SHA-256 |
| --- | --- |
| Allocation configuration | `fc7bf20b89a7c22056ad370c2fd0120250c8c4554db69728a3af0209dbb3313f` |
| Allocation report schema | `c35d3c2591e627ec7afc68e901a42b085d79a40f8b889a1228de3174b9b026bc` |
| Allocation implementation | `7bef8cc9b958895597f09f4b35862433fac82f2fd6c94fbfc4fe2aa1bafa6c80` |
| Allocation CLI | `06bebd7c459f47fd4ecbb3be1e8f671a44ffa7d8d0c103370a5b38f8524bbc9b` |
| Allocation tests | `97aa6d612608447205412bf5a80da59af0bb8fae4c784e66d7c377a0a971d474` |
| Procedure specification | `2d7270c7919ca2225dc7d4fba58c73e4cc04a9dde13a19ac69d51922bac367b7` |

## Result

The exact singleton-scenario fixture produces 160 training, 40 validation, and 40 pilot records with eight validation and eight pilot records per family. Multi-record scenarios remain intact. A deliberately indivisible fixture produces a visible non-exact allocation and requires later approval rather than crossing a scenario.
