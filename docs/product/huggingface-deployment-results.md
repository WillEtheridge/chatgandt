# Hugging Face deployment results

**Recorded:** 2026-07-17

**Status:** live serving path verified; public Vercel deployment remains an operator handoff

## Outcome

The Candidate 3 diagnostic adapter is published at <https://huggingface.co/wetheridge/chatgnt-qwen2.5-1.5b-lora>. A private ZeroGPU Gradio Space at <https://huggingface.co/spaces/wetheridge/chatgnt-api> serves Spirit Guide and Tasting Room requests. The local Next.js application has completed both flows through its own server routes and the private Space.

This deployment does not overturn the Stage 6 no-winner decision. Candidate 3 remains a diagnostic model and the public copy must describe its limitations honestly.

## Verified properties

- The adapter weights re-downloaded from the Hub exactly match the packaged weights.
- Publication provenance relates the machine-portable adapter identity to the immutable source experiment identity.
- The Space is private, RUNNING on `zero-a10g`, and contains only 17 allowlisted serving files.
- Health reports the expected base revision, adapter revision, adapter digest, and schema digest.
- Three live Spirit Guide and three live Tasting Room smoke requests completed through the published contract.
- The local Next.js proxy completed real Spirit Guide and Tasting Room requests without sending the HF token to the browser.
- Invalid JSON and invalid-schema generations remain explicit successful transport responses with failed model outcomes.
- The frontend mock and live providers share the same typed application contract.

## Deployment-specific compatibility work

ZeroGPU accepts PyTorch 2.11.0 rather than the experiment's PyTorch 2.12.1. Model, adapter, prompt, generation, and schema identities remain pinned. ZeroGPU also initialises the application without an allocated physical CUDA device, so the Space package loads PEFT safetensors through CPU before moving the fully frozen model inside the GPU-decorated request. This is an allowlisted serving transform; the source experimental inference implementation is unchanged.

The first Space builds exposed these compatibility constraints directly. Each correction addressed a concrete platform boundary: supported PyTorch version, startup-safe adapter loading, explicit adapter freezing, and Gradio's requirement for string JSON-object keys. Subsequent cold builds reached `RUNNING` and passed live calls.

## Remaining production handoff

The frontend has not yet been deployed to Vercel because the project owner reserved that operation. Before public launch, create a narrowly scoped read token, configure `HF_SPACE_ID` and `HF_TOKEN`, add route-specific Vercel rate limits, and repeat the end-to-end checks against the canonical origin.
