# Development System B v3 Confirmation Acceptance

- **Accepted:** 2026-07-15
- **Run ID:** `development-b-v3-confirmation-20260715`
- **Status:** Accepted as complete development evidence; structural and blinded qualitative scoring complete
- **Final Runpod charge:** `$0.14`

## Acceptance scope

This record establishes the identity, operational completeness, integrity, cost, and structural result of the pinned BF16 confirmation of the locally selected `five-shot-v3` prompt. It is a development transfer check, not held-out evaluation.

The three raw run files remain unchanged. Structural evaluation was written to a separate derived-results directory using the frozen validator.

## Immutable run evidence

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `manifest.json` | 26,105 | `9a600c36cf0749f7114c5d1c88defb2e6d22297d47127a848ee6444663e9b76f` |
| `prompts.jsonl` | 6,666 | `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` |
| `responses.jsonl` | 741,522 | `2b9a56b8886e625565bf7504b4bcc7b5b962eb8032a0137b1930fce3d94cb86c` |

The local inspector reported:

- `complete: true`;
- 20 scheduled and 20 unique valid response records;
- 20 successful generations terminating with EOS;
- no missing, duplicate, unexpected, malformed, or integrity-failing records; and
- no response reaching the maximum-new-token boundary.

## Frozen experimental identity

| Component | Recorded identity |
| --- | --- |
| Execution commit | `8f3d43ea133c7faf385c373fadaf7d13b4f46908` |
| Git state before execution | Clean |
| Behaviour digest | `34e0270aa8f2c3ee3b52a368c361db3d689c5efdfeac7e72ceb18509ae2cf589` |
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Model revision | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |
| Base weights | `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee` |
| Weight dtype | BF16 |
| Prompt set | 20 prompts; `0f9b594b3e8388ee803a31e69882bf8a6822eb147cfecaf4e16a9bf6fbd96bd1` |
| System set | `ee85e9a115971b473e4e732eb81a0e904fe8b9405e9b78d2a1f84205f05a92e6` |
| Prompt asset | `five-shot-v3`; `cdd68af07f6668c8526c357a7f9df6600d95cbfa03da83bcb5280ee053a89d31` |
| Master seed | `20260714` |
| Execution-order seed | `17625029341685692511` |

System B used the untouched base model with the selected five-shot prompt and no adapter.

## Recorded runtime

| Field | Recorded value |
| --- | --- |
| Manifest creation | `2026-07-15T10:41:24.660186+00:00` |
| GPU | NVIDIA GeForce RTX 4090 |
| GPU memory | 25,250,627,584 bytes |
| Driver | `580.173.02` |
| PyTorch | `2.12.1+cu130` |
| CUDA build | `13.0` |
| cuDNN | `92000` |
| Python | `3.12.13` |
| Transformers | `5.12.1` |
| Attention | SDPA |

The 20 synchronized `model.generate()` calls totalled 56.3293 seconds and averaged 2.8165 seconds. Complete inputs averaged 2,582.15 tokens and visible outputs averaged 154.75 tokens. These timings describe this v3 session only and are not a matched latency comparison with System A from another session.

## Preflight deviation

The fresh checkout ran 102 unit tests: 101 passed and one adapter-loading test errored because it depended on a Git-ignored lifecycle-adapter artefact present on the development machine but absent from a clean clone.

The failure occurred before the test's mocked adapter loader and did not exercise the current confirmation path. This run selected only base System B, supplied no adapter path, and loaded no adapted runtime. The deviation is accepted as unrelated to the generated evidence, but the test must create its own disposable fixture before the next formal run.

## Structural result

The frozen structural evaluator produced:

| Metric | Result |
| --- | ---: |
| Completed generations | 20 / 20 |
| JSON-valid responses | 16 / 20 |
| Schema-valid responses | **12 / 20** |

Observed failure labels were:

- `json_syntax`: 4;
- `ingredient_count`: 2;
- `wrong_top_level_type`: 2;
- `markdown_fence`: 1; and
- `method_count`: 1.

Labels can coexist on one response, so they should not be summed as a response count.

Derived evidence:

| File | SHA-256 |
| --- | --- |
| `summary.json` | `ded6d5ffddaed80527452f5b77114d0dd3790f070ce61af120b98f8adaf7c76b` |
| `validations.jsonl` | `a194e8929e825ba9fc2daf01fdeea37adc7a06a1abed1633c8987cca70e85dce` |

Pinned v3 exceeded local v3's structural result by one response (`12 / 20` versus `11 / 20`) and pinned v1 System B's result by three (`12 / 20` versus `9 / 20`). This supports structural transfer on this development set. It does not establish superior qualitative quality or generalisation.

## Blinded qualitative result

All 12 schema-valid responses were placed into identity-blinded packets and scored against the frozen three-dimension rubric before the source mapping was revealed. The evaluator was recorded as `OpenAI Codex (GPT-5), 2026-07-15 session; exact backend snapshot unavailable`.

| Metric | Count | End-to-end rate |
| --- | ---: | ---: |
| Schema-valid responses scored | 12 | 60% of 20 attempts |
| Underlying answer at least acceptable | 8 | 40% |
| Metaphorical coherence at least acceptable | 9 | 45% |
| Recipe-style execution at least acceptable | 7 | 35% |
| **Full response passes** | **5** | **25%** |

The four underlying-answer failures included an inaccurate DNS explanation, failure to provide a softened rewritten sentence, failure to explain why metal feels colder, and failure to supply the requested housemate-conversation opening. Five schema-valid answers also failed recipe-style execution by becoming ordinary advice or design prose inside the JSON shape.

Blinded evidence:

| File | SHA-256 |
| --- | --- |
| `rubric.json` | `0d5aaeed4e6ac69ec0a9c2b8a64a6fddc9d9adcd792412867a46fe51db91f217` |
| `packets.jsonl` | `d85d8093994dcaa41e3b89ad4f0ee01849a052e5ce56848287ed8b8b4a56edb6` |
| `identity-mapping.jsonl` | `e1a8617ae9a3a9920ddd9c6696f21229d82f4af5aabbb1574ad75bcfbc9e462d` |
| `scores.jsonl` | `7f4e602fd087ab9895231575b2134dacb3cb4eaa8bebd9a21fc2b1719ae2a5bb` |
| `revealed-scores.jsonl` | `b38b8e30e8e1fc217131407019fe49faf16326cf5c8a4884cf1e339b9393ed6b` |
| `summary.json` | `fa0e88cc34e3b3e490c5c08688aa3326d07d499f5404c859e1e5c97ed6ff442e` |

## Transfer interpretation

| Runtime and prompt | Full passes | Schema valid | Underlying ≥ 2 | Metaphor ≥ 2 | Recipe style ≥ 2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Local quantised v3 | 7 | 11 | 7 | 10 | 11 |
| Pinned BF16 v3 | 5 | 12 | 8 | 9 | 7 |
| Pinned BF16 v1 | 6 | 9 | 6 | 7 | 8 |

The concrete v3 shape cue transferred structurally: pinned v3 achieved the highest schema-valid count. It did not transfer as an end-to-end quality improvement. Pinned v3 produced one fewer full pass than pinned v1 and two fewer than local v3, with recipe-style execution the largest qualitative weakness.

These are small development samples generated in different sessions. They diagnose behaviour but do not estimate final generalisation performance or establish a statistically reliable ranking.

## Acceptance decision

The run is accepted for its intended purpose. It demonstrates that the unchanged selected prompt executed through the pinned BF16 harness and retained approximately the same structural behaviour observed locally.

Qualitative transfer is accepted as mixed rather than successful overall. Version 3 remains the frozen System B baseline because it won the predeclared local selection procedure and the four-version development budget is closed. The final research comparison remains the later matched held-out System B versus System C evaluation.

Recorded Runpod spend is now `$0.53`: `$0.14` feasibility, `$0.10` CUDA harness acceptance, `$0.15` initial A/B development, and `$0.14` v3 confirmation.
