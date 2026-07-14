# Minimal System Prompt v1 Check

- **Date:** 2026-07-14
- **Result:** Pass
- **Experimental model generation performed:** No

## Accepted asset

- Path: [`config/prompts/minimal-v1.json`](../config/prompts/minimal-v1.json)
- Prompt asset ID: `minimal-v1`
- Version: 1
- SHA-256: `f09b7712fb9b36c9fc6fc54b1fc72fbf2d95cc8e5e1d8d570d88a54ccde2d821`
- Worked examples: 0
- Content characters: 0

The asset represents an explicit system message whose content is the empty string. The inference engine still passes that message through Qwen's pinned official chat template before the unchanged user message. It does not remove or modify the system role.

This is the agreed System A condition: the untouched instruction model receives no ChatG&T-specific system content. Comparing it with System B therefore isolates the detailed five-shot prompt while preserving the conversation structure.

`chatgnt.prompting.validate_minimal_prompt` checks the closed generic prompt-asset contract, exact empty content, zero worked examples, stable identity, and frozen digest.

Run the check with:

```bash
uv run --frozen python scripts/verify_minimal_prompt.py
```

Verification results:

- minimal-prompt verifier: pass;
- prompt-asset tests: 5/5 pass; and
- complete regression suite: 84/84 pass.

## Evidence boundary

This accepts only the System A prompt asset. The A/B system set and scheduled run are not yet configured, and no model generation has occurred.
