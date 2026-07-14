# Five-Shot System Prompt v1 Check

- **Date:** 2026-07-14
- **Result:** Pass
- **Experimental model generation performed:** No

## Accepted prompt asset

- Path: [`config/prompts/five-shot-v1.json`](../config/prompts/five-shot-v1.json)
- Prompt asset ID: `five-shot-v1`
- Version: 1
- SHA-256: `7b8c25f04fba15373813862bba9705d4585ba919e855612909830757e4bd93d6`
- Worked examples: 5
- Content characters: 9,765

The instruction source is [`data/prompt-engineering/instructions-v1.txt`](../data/prompt-engineering/instructions-v1.txt), SHA-256 `4690e96ec8bcaca5f7dcd0a512885e1d39d57c80e6858426cebb36336ecc0d97`. The worked-example source remains frozen at SHA-256 `0cb6afd2bf88ed1f9a3edf8e5ffc479e22c69b91ea7220988c5b1dee51f429b6`.

`chatgnt.prompting.render_five_shot_content` deterministically assembles the instruction text, five labelled user/assistant pairs, explicit example boundaries, and the closing raw-JSON reminder. The verifier requires the committed prompt content to equal that rendering and the complete asset to match its frozen digest.

## Pinned-tokenizer measurement

The exact Qwen2.5-1.5B-Instruct tokenizer and official chat template measured the complete rendered input for all 20 frozen development prompts. The comparison preserves the empty system role used by System A.

| Measurement | System A: empty system | System B: five-shot system |
| --- | ---: | ---: |
| Minimum complete input tokens | 25 | 2,344 |
| Maximum complete input tokens | 75 | 2,394 |
| Mean complete input tokens | 38.15 | 2,357.15 |

The paired five-shot overhead is exactly 2,319 tokens for every development prompt. Tokenising the system content alone also produces 2,319 tokens, but that standalone value is diagnostic rather than treated as an independently additive metric.

With the pinned 32,768-token model context and a 512-token generation allowance, the longest development input leaves 29,862 tokens of headroom. Every input fits without truncation.

Run the checks with:

```bash
uv run --frozen python scripts/verify_five_shot_prompt.py --measure-tokens
uv run --frozen python -m unittest tests.test_prompting -v
```

Verification results:

- deterministic prompt and token-budget verifier: pass;
- dedicated prompt-assembly tests: 3/3 pass;
- complete regression suite: 82/82 pass; and
- bytecode compilation and diff whitespace checks: pass.

## Evidence boundary

This accepts the identity, deterministic composition, schema-valid embedded examples, and input-token feasibility of the initial System B prompt. It does not establish that Qwen follows the prompt or that its responses are useful. Those questions begin with the controlled System A/B development run.
