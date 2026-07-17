# Stage 6 Full-Training Implementation Check

- **Date:** 2026-07-17
- **Status:** Passed locally before GPU execution; formal runs completed 2026-07-17
- **Scope:** The three frozen first-round configurations and their shared training runner

## Outcome

The pilot runner has been generalised without creating a second training implementation. The historical pilot remains its default entry point, while `scripts/run_full_training.py` exposes only Candidates 1–3 from the frozen plan.

Every full run uses all 160 training examples, evaluates all 40 validation examples without gradients, masks prompt and padding tokens from the loss, forbids truncation, checks that only LoRA parameters are trainable, and saves a formally identified adapter after every epoch. Final adapters are cleanly reloaded and compared exactly as in the successful pilot.

## Frozen implementation identities

| Artefact | SHA-256 |
| --- | --- |
| Shared training core, `scripts/run_pilot_training.py` | `44e84ff742ef3c96a03ad067f227d3f7a14fff65e648019737b1a25a9a474a89` |
| Full-training entry point, `scripts/run_full_training.py` | `320294158089b9ffabae75cb0e116718acfa9c48e08af227e9e2356a2f69b96b` |
| Stage-specific verifier, `scripts/verify_full_training.py` | `d2c0156ad925dca2c510b91f7296486a6c41d9baa62cb8d7cf6624b1a3f5d9fa` |
| Candidate 1 configuration | `861bdc138ecffae1d7bbd425d55df6f8cdbbf50ae2898732660c84cd3692c954` |
| Candidate 2 configuration | `97c1951930c6ef821002d08a3fa440b255cfe0dfb460869fffb3d9d5a8c088dc` |
| Candidate 3 configuration | `86496cdbf692166e0c824c0cbc6d85200a5595f0d293ac27695e2dec1f97753e` |

The execution reports will additionally bind the exact clean Git commit used on Runpod.

## Verified candidate shapes

| Candidate | Epochs | Updates per epoch | Total updates | Effective batch | LoRA targets | Trainable parameters |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | 3 | 20 | 60 | 8 | `q_proj`, `v_proj` | 1,089,536 |
| 2 | 6 | 20 | 120 | 8 | `q_proj`, `v_proj` | 1,089,536 |
| 3 | 3 | 20 | 60 | 8 | `q_proj`, `k_proj`, `v_proj`, `o_proj` | 2,179,072 |

The verifier proves mechanically that Candidate 2 differs from Candidate 1 only in duration and Candidate 3 differs only in LoRA target surface.

## Local verification

The following checks passed sequentially in the pinned environment:

```text
uv run --frozen python scripts/verify_full_training.py --model-capacity
uv run --frozen python scripts/run_full_training.py --candidate all --check-inputs
uv run --frozen python scripts/run_pilot_training.py --check-inputs
uv run --frozen python -m unittest discover -s tests
```

The checks established:

- exact identities for the frozen training, validation, workflow-event, and manifest files;
- exactly 160 training and 40 validation records with no scenario overlap;
- no truncation, with all observed examples below the 512-token limit;
- prompt tokens and padding excluded from the loss;
- the actual Candidate 3 LoRA parameter count against the pinned model;
- formal checkpoint provenance and detection of changed checkpoint weights;
- the unchanged 40-example pilot entry point still resolves to 15 updates; and
- the complete historical 128-test regression suite still passes.

## GPU boundary

These CPU-side contract and compatibility checks did not themselves prove successful training. The later formal CUDA batch established finite optimisation, frozen base weights, VRAM headroom, per-epoch validation, material adapter effect, exact final reload, and complete output evidence. Its separate results are recorded in `docs/stage-6/full-training-results.md`.
