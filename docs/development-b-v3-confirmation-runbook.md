# Development System B v3 Confirmation Runbook

- **Purpose:** Confirm that the locally selected prompt transfers unchanged to the pinned BF16 harness
- **Candidate:** `five-shot-v3`
- **Run seed:** `20260714`
- **Status:** Prepared; paid execution not yet authorised

This is a 20-attempt development confirmation run, not held-out evaluation. It deliberately runs only System B because System A already has accepted pinned evidence and was not part of the local version ranking. Latency from separate sessions must not be presented as a matched A/B latency comparison.

## Frozen inputs

| Input | SHA-256 |
| --- | --- |
| Development prompts | `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` |
| Five-shot v3 prompt | `cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31` |
| System B/v3 set | `ee85e9a115971b473e4e732eb81a0e904fe8b9405e9b78d2a1f84205f05a92e6` |
| Confirmation run plan | `feb635d9de48a1cabc46b5185c9e1c42708df90f63a6001f57c91d7b7d0faa98` |

The execution commit must be recorded after the current work is reviewed and committed. Do not edit the prompt, inputs, generation configuration, or seed on the Pod.

## Preflight

Use the reusable Runpod workflow to start or provision a CUDA-compatible Pod, transfer or update the exact committed repository, install the required `uv` version, run `uv sync --frozen`, verify the GPU/BF16 tensor path, and run the pinned model verifier.

Before paid generation, confirm:

```bash
sha256sum \
  data/development/prompts-v1.jsonl \
  config/prompts/five-shot-v3.json \
  config/systems/development-b-v3.json \
  config/runs/development-b-v3-confirmation.json

git status --short
git rev-parse HEAD

uv run --frozen python scripts/verify_prompt_confirmation.py
```

The confirmation verifier must report `"result": "pass"` and 20 scheduled attempts. Stop if any digest differs from the table, the intended execution commit is not checked out, the repository is dirty, CUDA/BF16 verification fails, or the pinned model verification fails.

## Execute

Choose a unique date-bearing run ID and ensure it does not already exist:

```bash
test ! -e experiments/runs/development-b-v3-confirmation-YYYYMMDD

uv run --frozen python -m chatgnt.harness run \
  --prompts data/development/prompts-v1.jsonl \
  --system-set config/systems/development-b-v3.json \
  --run-seed 20260714 \
  --device cuda:0 \
  --run-id development-b-v3-confirmation-YYYYMMDD
```

Do not retry individual responses, repair output, or add Ollama's `format` option. A failed or interrupted run remains evidence under its unique ID.

## Inspect and preserve

```bash
uv run --frozen python -m chatgnt.harness inspect \
  --run-dir experiments/runs/development-b-v3-confirmation-YYYYMMDD

wc -l experiments/runs/development-b-v3-confirmation-YYYYMMDD/responses.jsonl

sha256sum experiments/runs/development-b-v3-confirmation-YYYYMMDD/*
```

The inspector must report a complete 20-attempt run. Copy the entire run directory home, rerun the inspector locally, compare file hashes, record the final provider charge and observed GPU metadata, and only then stop or terminate the Pod.

After preservation, apply the same frozen structural and blinded qualitative evaluation used for the local versions. Report transfer discrepancies; do not create a fifth prompt version from them.
