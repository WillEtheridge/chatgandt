# Development A/B Schedule Check

- **Date:** 2026-07-14
- **Result:** Pass
- **Experimental model generation performed:** No

## Frozen schedule

- Path: [`data/development/schedule-ab-v1.json`](../../../data/development/schedule-ab-v1.json)
- SHA-256: `ae55b4521dfe581c10febbe0c13bcdfd26262de616a493e331c7562e89a36468`
- Master run seed: `20260714`
- Execution-order seed: `17625029341685692511`
- Ordering algorithm: `sha256-sort-v1`
- Scheduled attempts: 40

The schedule was produced by the same `schedule_attempts` implementation used by the inference harness. Every one of the 20 frozen development prompts appears exactly once for System A and once for System B. Both attempts for a prompt share one derived generation seed, while their positions in the run are independently determined by the seeded order-key hash.

Coverage checks:

- System A attempts: 20;
- System B attempts: 20;
- complete A/B prompt pairs: 20;
- prompt pairs sharing one generation seed: 20; and
- attempt indices: contiguous from 0 through 39.

The first five scheduled attempts are:

| Index | Prompt | System |
| ---: | --- | :---: |
| 0 | `dev-v1-explanation-clean` | A |
| 1 | `dev-v1-explanation-robustness` | B |
| 2 | `dev-v1-transformation-naturalistic` | B |
| 3 | `dev-v1-advice-robustness` | B |
| 4 | `dev-v1-explanation-clean` | B |

Run the check with:

```bash
uv run --frozen python scripts/verify_development_schedule.py
```

Verification results:

- production-derived schedule verifier: pass;
- focused run-plan and schedule tests: 4/4 pass;
- complete regression suite: 90/90 pass; and
- bytecode compilation and diff whitespace checks: pass.

At runtime the harness will regenerate this schedule from the frozen inputs and snapshot it in the immutable manifest. The dry artifact is not trusted as an alternative scheduler input; equality with production derivation is the acceptance condition.

## Evidence boundary

This accepts the planned coverage, order, and seeds. It does not show that an attempt executed or that a model returned a response.
