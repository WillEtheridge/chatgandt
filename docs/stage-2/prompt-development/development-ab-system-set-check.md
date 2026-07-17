# Development System A/B Set Check

- **Date:** 2026-07-14
- **Result:** Pass
- **Experimental model generation performed:** No

## Accepted system set

- Path: [`config/systems/development-ab-v1.json`](../../../config/systems/development-ab-v1.json)
- Version: 1
- SHA-256: `c2c59b412f7982d07b026e61a347f03acdbbf2f7c8aa4136bf5094fecbae45cc`
- Systems: A and B only
- Adapter-enabled systems: none

The exact mapping is:

| System | Base model | Prompt asset | Adapter |
| --- | --- | --- | --- |
| A | Pinned untouched Qwen2.5-1.5B-Instruct | `minimal-v1` | Disabled |
| B | Pinned untouched Qwen2.5-1.5B-Instruct | `five-shot-v1` | Disabled |

The prompt assets are separately bound to their frozen digests. Relative asset paths resolve from the system-set file, and the generic inference contract independently enforces the empty/five-shot invariants and adapter flags associated with A and B.

`chatgnt.prompting.validate_development_ab_system_set` additionally requires exactly the intended A/B pair, the reviewed prompt identifiers and digests, the untouched base-only runtime condition, and identity with the system-set digest.

Run the check with:

```bash
uv run --frozen python scripts/verify_development_systems.py
```

Verification results:

- development-system-set verifier: pass;
- prompt and system-asset tests: 7/7 pass; and
- complete regression suite: 86/86 pass.

## Evidence boundary

This accepts which two systems will participate in the first development comparison. It does not yet choose the run seed, construct the randomised schedule, or run the model.
