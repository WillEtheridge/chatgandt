# ChatG&T

ChatG&T is a reproducible experiment comparing prompt engineering with LoRA fine-tuning on the same small language model.

The task is deliberately unusual but measurable: turn a low-stakes user request into a useful metaphorical cocktail recipe encoded as strict JSON. The experiment asks whether a fine-tuned model can learn that behaviour more reliably than the untouched base model given a developed five-shot prompt—and what it costs in context and generation time.

> Fine-tuning learned the recipe more reliably than it learned to answer the underlying task.

## Results at a glance

The frozen evaluation used Qwen2.5-1.5B-Instruct, 60 unseen prompts, four treatment combinations, and 240 first-attempt generations on one RTX 4090.

| System | Model | Prompt | Schema-valid | Full response pass |
| --- | --- | --- | ---: | ---: |
| A | Base | Minimal | 0/60 (0.0%) | 0/60 (0.0%) |
| B | Base | Five-shot | 43/60 (71.7%) | 16/60 (26.7%) |
| C | LoRA adapter | Minimal | 52/60 (86.7%) | 26/60 (43.3%) |
| D | LoRA adapter | Five-shot | 48/60 (80.0%) | 21/60 (35.0%) |

The primary engineering comparison was B versus C:

- Fine-tuning improved schema validity by 15 percentage points.
- Mean rendered input fell from 2,575.9 tokens to 31.9—a 98.8% reduction.
- Mean generation time increased from 3.92 seconds to 5.70 seconds in the matched measurement.
- The full-pass advantage was less certain: its paired 95% interval included no difference at the lower boundary.
- No trained candidate passed the predeclared product-viability gate. Candidate 3 is retained as a diagnostic and demonstration model, not presented as a product-quality winner.

The strongest supported conclusion is structural: the adapter learned the output contract more reliably. Claims about answer quality or preference remain qualified because the human and LLM judges agreed on only 7 of 15 blind pairwise choices.

See the [full results report](docs/product/results-report-v1.md), [primary evaluation results](docs/stage-7/primary-results.md), and [limitations](docs/limitations.md) for the evidence and interpretation.

## Experimental design

The project uses a two-by-two design so prompting and adaptation can be examined separately as well as compared as practical strategies.

| | Minimal prompt | Five-shot prompt |
| --- | --- | --- |
| Untouched base model | A | B |
| LoRA-adapted model | C | D |

All four systems share the same pinned base model, generation profile, seed policy, response schema, and evaluation population. Outputs are judged on first attempts: the harness does not retry, repair, or reformat invalid generations.

A full response pass requires:

1. valid JSON matching the frozen schema;
2. an acceptable underlying answer;
3. a coherent cocktail metaphor; and
4. convincing recipe-style execution.

## Repository contents

```text
chatgnt/       Strict configuration, inference, validation, and evaluation code
config/        Frozen model, generation, prompt, run, and judge configuration
data/          Versioned training, validation, development, and held-out records
experiments/   Captured runs, evaluations, training reports, and analysis artefacts
scripts/       Verification, dataset, training, scoring, and packaging entry points
schemas/       JSON Schemas for responses and experimental records
tests/         Python unit tests
contract_tests/ Dataset and split contract tests
frontend/      Next.js public experience and experiment narrative
deployment/    Hugging Face model card, Space app, and deployment tests
docs/          Protocols, decisions, runbooks, results, limitations, and learnings
video/         Remotion source and rendered project promos
```

The repository intentionally retains more than application code. Frozen inputs, provenance records, raw outputs, reviewer decisions, and machine-readable summaries are part of the experimental evidence.

## Quick start

### Python checks

Requirements:

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/) 0.11.28

```bash
git clone https://github.com/WillEtheridge/chatgandt.git
cd chatgandt
uv sync --frozen
uv run --frozen python -m unittest discover -s tests
uv run --frozen python -m unittest discover -s contract_tests
```

Run the frozen protocol verifier:

```bash
uv run --frozen python scripts/verify_evaluation_protocol.py
```

Inspect a captured run without loading a model:

```bash
uv run --frozen python -m chatgnt.harness inspect \
  --run-dir experiments/runs/heldout-evaluation-v1-20260717-run01
```

### Frontend

Requirements: a current Node.js release supported by Next.js 16 and npm.

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

The interactive Spirit Guide and Tasting Room use a private Hugging Face Space. Set `HF_TOKEN` in `frontend/.env.local` to a token that can access the configured `HF_SPACE_ID`. The static experiment, results, and learning pages do not require model access.

Useful frontend checks:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

## Reproducing model runs

The ordinary test suite and run inspection are local and do not require a GPU. Generating new formal results does.

The harness verifies pinned model files, adapter provenance, configuration digests, prompt identities, deterministic scheduling, runtime properties, and completeness before accepting a run. A formal evaluation also requires a CUDA device with BF16 support and the exact base-model snapshot and adapter referenced by the run plan.

The generic runner interface is:

```bash
uv run --frozen python -m chatgnt.harness run \
  --prompts PATH/TO/PROMPTS.jsonl \
  --system-set PATH/TO/SYSTEMS.json \
  --run-seed 20260715 \
  --device cuda:0 \
  --adapter-path PATH/TO/ADAPTER
```

Before attempting a formal rerun, read the [Stage 7 execution plan](docs/stage-7/execution-plan.md) and the relevant run plan under [`config/runs`](config/runs). These define the exact hardware, artefact, and provenance requirements; changing them produces a different experiment.

## Model and deployment

- Base model: [Qwen/Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct), pinned to the revision in [`config/model.toml`](config/model.toml)
- Published diagnostic adapter: [wetheridge/chatgnt-qwen2.5-1.5b-lora](https://huggingface.co/wetheridge/chatgnt-qwen2.5-1.5b-lora)
- Serving boundary: a private Gradio/ZeroGPU Space exposing `spirit_guide`, `tasting_room`, and `health`

The deployed service preserves the experiment’s failure semantics: invalid model output is returned as a failure rather than silently repaired, and prompts or visitor choices are not persisted by the application.

## Documentation

Start with:

- [Experiment plan](docs/experiment-plan.md)
- [Behavioural contract](docs/behavioural-contract.md)
- [Evaluation protocol](docs/stage-3-evaluation-protocol.md)
- [Results report](docs/product/results-report-v1.md)
- [Limitations](docs/limitations.md)
- [Learnings log](docs/learnings.md)
- [Decision log](docs/decisions.md)

## Scope and safety

ChatG&T is a research and portfolio project for English-language, single-turn, low-stakes prompts. The model can produce well-formed responses that are incomplete, imprecise, or factually wrong. It should not be relied on for medical, legal, financial, crisis, or other consequential guidance.
