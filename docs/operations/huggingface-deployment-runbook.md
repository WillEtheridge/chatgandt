# Hugging Face deployment runbook

This runbook reproduces the ChatG&T serving path without exposing a Hugging Face credential to the browser. It publishes the LoRA adapter as a public model repository, runs inference in a private ZeroGPU Space, and connects the local Next.js application through same-origin server routes.

## Architecture and boundaries

```text
browser -> Next.js /api/* -> private Gradio Space -> Qwen base + LoRA adapter
```

- The browser never receives `HF_TOKEN` or the private Space URL.
- The adapter is public and contains no training data.
- The Space is private, stores no prompts or responses, and exposes only named Gradio endpoints.
- Generated invalid JSON or invalid-schema output is returned as an honest model outcome. It is not repaired or retried.
- Visitor choices are held only in browser state and are not persisted.

## Prerequisites

1. Use Python 3.12 and the locked repository environment: `uv sync --frozen`.
2. Install frontend dependencies: `cd frontend && npm ci`.
3. Authenticate the Hugging Face CLI: `hf auth login`.
4. Confirm the account has ZeroGPU access. ChatG&T used HF PRO without enabling paid ZeroGPU overage.

Never commit an access token, put one in a `NEXT_PUBLIC_*` variable, print it in a shell command, or paste it into client-side code.

## Publish the adapter

Build the distribution package from the immutable Candidate 3 adapter:

```bash
uv run --frozen python scripts/package_hf_adapter.py
```

The packaging step preserves `adapter_model.safetensors` byte-for-byte but replaces the machine-local base-model path in `adapter_config.json` with `Qwen/Qwen2.5-1.5B-Instruct`. It records both the source and publication identities in `publication-provenance.json`.

Create the repository once, then upload the package:

```bash
hf repos create wetheridge/chatgnt-qwen2.5-1.5b-lora --repo-type model --exist-ok
hf upload wetheridge/chatgnt-qwen2.5-1.5b-lora artifacts/deployment/hf-model . --repo-type model
```

The expected public repository is <https://huggingface.co/wetheridge/chatgnt-qwen2.5-1.5b-lora>. Verify its files and re-download the published package before treating publication as complete.

## Build and deploy the private Space

Build the allowlisted Space bundle:

```bash
uv run --frozen python scripts/package_hf_space.py
```

Only the serving application, required `chatgnt` modules, frozen prompts, model configuration, and response schema enter `artifacts/deployment/hf-space`. Datasets, held-out responses, frontend source, Git history, and credentials are excluded.

Create the private Space once and select ZeroGPU hardware:

```bash
hf spaces create wetheridge/chatgnt-api --sdk gradio --private --exist-ok
hf spaces hardware wetheridge/chatgnt-api --set zero-a10g
hf upload wetheridge/chatgnt-api artifacts/deployment/hf-space . --repo-type space
```

Check deployment state and logs:

```bash
hf spaces info wetheridge/chatgnt-api
hf spaces logs wetheridge/chatgnt-api
```

Wait for `runtime.stage` to become `RUNNING`. The health endpoint must report the pinned base revision, adapter repository revision, adapter digest, and schema digest.

## Verify the live service

Run the credential-safe smoke test. It prints identities and status classes, not prompts, model text, or the token:

```bash
uv run --with gradio-client==2.5.0 python scripts/verify_hf_space.py --count 3
```

A `valid`, `invalid-json`, or `invalid-schema` Spirit result all prove that the request completed through the intended service contract. The latter two are model-quality failures, not infrastructure failures. Health or response-envelope mismatches fail the smoke test.

## Run the frontend locally

For UI-only development, use the deterministic mock provider:

```bash
cd frontend
npm run dev
```

To run against the private live Space without copying a token into `.env.local`:

```bash
uv run --frozen python scripts/run_frontend_with_hf.py
```

Exercise both Spirit Guide and Tasting Room. The API routes enforce JSON content type, an exact one-field request contract, a 4 KiB body limit, a 500-character prompt limit, no-store responses, an exact production origin, and a four-minute provider timeout.

## Vercel handoff

The frontend is ready for the operator to import `frontend/` as a Vercel project. Configure these server-only production variables:

| Variable | Value |
| --- | --- |
| `CHATGNT_BACKEND` | `huggingface` |
| `HF_SPACE_ID` | `wetheridge/chatgnt-api` |
| `HF_TOKEN` | A new fine-grained read token limited to the private Space |
| `CHATGNT_ALLOWED_ORIGIN` | The exact canonical HTTPS frontend origin |

Do not reuse the broad CLI token. Apply Vercel rate limits before announcing the site: 6 requests per 10 minutes per IP for `/api/spirit-guide`, and 3 per 10 minutes per IP for `/api/tasting-room`. The lower Tasting Room limit reflects its two generations per request. Keep the Space private and do not enable prepaid ZeroGPU credits without a new cost decision.

After deployment, repeat the homepage, Spirit Guide, Tasting Room, mobile layout, cold-start, invalid-model-output, and rate-limit checks against the public origin. Roll back the Vercel deployment if the proxy boundary fails; make the Space private again immediately if it is ever exposed accidentally.

## Current immutable identities

- Base: `Qwen/Qwen2.5-1.5B-Instruct` at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- Public adapter commit: `12af8027a481bef7df618f32bb8787889526c343`
- Publication adapter digest: `034e0c79b1201350784e0409d5f28ffcf92d8dfa9697b291b2dd4bf45129100c`
- Source experiment adapter digest: `0eef1d5da017a18f571a5e37cc152d1351bfbda9f0d343c3f376a1f68a2d4249`
- Private Space commit: `af13cd5bca32f1a3d80982a712046051803bdcfe`
