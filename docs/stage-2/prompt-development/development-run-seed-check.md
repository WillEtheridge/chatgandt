# Development A/B Run Seed Check

- **Date:** 2026-07-14
- **Result:** Pass
- **Experimental model generation performed:** No

## Frozen run-plan identity

- Path: [`config/runs/development-ab-v1.json`](../../../config/runs/development-ab-v1.json)
- Run plan ID: `development-ab-v1`
- SHA-256: `63db3e2cd65354b037c62eda2c5cabc34ae32f336b42aff8cf7f19cd08672271`
- Master run seed: `20260714`
- Derived execution-order seed: `17625029341685692511`
- Primary samples per prompt and system: 1
- Expected schedule size: 40 attempts

The run plan binds the seed to the frozen 20-prompt development set and base-only System A/B mapping. The master seed is supplied explicitly; there is no random default.

For each prompt, the harness derives a generation seed from the master run seed, prompt ID, and repeat index. System identity is deliberately excluded, so A and B receive the same pseudorandom stream for the same input. A separately namespaced seed determines the randomised execution order.

Run the check with:

```bash
uv run --frozen python scripts/verify_development_run_plan.py
```

Verification results:

- development-run-plan verifier: pass;
- focused run-plan tests: 2/2 pass; and
- complete regression suite: 88/88 pass.

## Evidence boundary

This freezes the master seed and referenced inputs. It does not yet materialise the 40-attempt ordered schedule or generate model outputs.
