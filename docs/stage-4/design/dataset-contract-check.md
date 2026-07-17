# Dataset Contract Check

- **Stage:** 4 — Build and freeze dataset v1
- **Step:** 5 — Dataset records, workflow history, validation, and rendering
- **Date:** 2026-07-15
- **Result:** Pass

## Implemented contract

The reviewed dataset-v1 contract now provides:

- controlled metadata and workflow registries;
- strict supervised-example, workflow-event, and split-deviation schemas;
- duplicate-key-safe canonical JSONL loading;
- record, cross-field, lifecycle, authoring, freeze, coverage, projection, and split-deviation validation;
- lifecycle-gated training messages with the explicit `title`, `ingredients`, `method`, `garnish` target order;
- a read-only contract, authoring, and freeze CLI; and
- synthetic exact-allocation and reviewed-deviation tests.

No real supervised or held-out examples were created and no model operation occurred.

## Live verification

```text
uv run --frozen python scripts/verify_dataset_contract.py --mode contract
result: pass
schema/config parity: pass
built-in lifecycle: pass
targets: 200 accepted, 160 train, 40 validation, 40 pilot

uv run --frozen python -m unittest discover -s contract_tests -v
Ran 8 tests
OK

uv run --frozen python -m unittest discover -s tests
Ran 128 tests
OK

python -m compileall -q chatgnt scripts contract_tests
result: pass

git diff --check
result: pass
```

The new suite is intentionally outside `tests/test_*.py` because Stage 3 evidence binds that historical file set. Both the frozen suite and the additive contract suite pass.

## Key identities

| Artefact | SHA-256 |
| --- | --- |
| Dataset configuration | `4ed2f61fa14000293debe2556e63297b3b1e439b41d7a4c7ef5285f2704c6a3c` |
| Supervised-example schema | `727b2e9373a5c17ff3bdaf84c862a6bbd1a9e86d13bfb2fc12f74dacc5be7f01` |
| Workflow-event schema | `dd1ec327e591dfac7c7bd2c5e05ad5e04bb1fbe97d830e8a106e6a54b0fed9fd` |
| Split-deviation schema | `e5e30ee05963723073102e8b73e950d04a53b62f7a1a1f399e7078c528aa03ce` |
| Dataset implementation | `710fb8122053f828ac9e9e04a749189a6ac9794805653c06782f124194a820b8` |
| Verification CLI | `dacc8f77d20a50cdce20f0c557ff62ce3062ba5dcd67fff354afe700b7980b73` |
| Reviewed specification | `915f63547179c792beacae06f7373af6df99c4976ad2cc61cbf2ab450936e62f` |
| Adversarial review record | `02287362e73532216b4439348f75cd991f52f05343540c4190ca9341efa89b93` |
| Focused contract tests | `431ccaa3d50234fcdf359e6286b153900c5e1f4f0196dabe594fac49a485c4aa` |

## Review result

The bounded adversarial review found one blocker and five material issues. All were resolved in one specification repair pass. Independent implementation review then corrected the authoring/freeze lifecycle boundary without expanding scope. No material dataset-contract issue remains known at handoff.
