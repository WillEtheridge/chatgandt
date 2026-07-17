# Stage 6 Full-Training Candidate Selection Results

- **Date:** 2026-07-17
- **Generation execution commit:** `481c914ee2dd2ba524daf9fa7531a2aba0119564`
- **Population:** ten frozen spent-development prompts per candidate
- **Result:** no first-round candidate met the complete viability gate
- **Strongest candidate:** Candidate 3, not selected
- **Held-out prompts used:** none

## What was run

The lowest-validation-loss checkpoint from each frozen training trajectory answered the same ten pilot-behaviour prompts with the minimal prompt, frozen generation settings, and run seed `20260715`. Three separate adapted-only system-C harness runs preserved the existing inference implementation while giving each candidate the same per-prompt generation seeds. The manifests bind the distinct adapter digest used by each run.

All 30 scheduled responses completed and all three immutable run bundles passed local integrity inspection after retrieval. Structural validation ran before qualitative scoring. Candidate identity was hidden in a shuffled 26-response packet, and every schema-valid response was scored using the exact frozen rubric bytes. The identity mapping was not opened until all scores and rationales were complete.

Each manifest recorded `git_dirty: true` because the operator created an untracked session-log directory beneath `experiments/runs/` immediately before starting the batch. No source or configuration file changed. A post-retrieval check compared every recorded `chatgnt/*.py` behaviour-file hash directly with commit `481c914ee2dd2ba524daf9fa7531a2aba0119564`; all matched, and all three manifests recorded the same behaviour-tree, `pyproject.toml`, and `uv.lock` digests. The run was not repeated after inspection merely to improve this metadata flag.

## Frozen-gate result

| Candidate | Schema valid | Joint passes | Families represented | Qualitative score total | Mean latency | Mean generated tokens | Viable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 — full-corpus anchor | 7/10 | 3/10 | 2/5 | 36 | 3029.37 ms | 171.8 | No |
| 2 — exposure challenger | 9/10 | 4/10 | 2/5 | 49 | 2951.91 ms | 164.5 | No |
| 3 — capacity challenger | 10/10 | 6/10 | 5/5 | 56 | 3476.53 ms | 155.7 | No |

Viability required all of: at least 8/10 schema-valid responses, at least 7/10 joint passes, and at least one joint pass in every intent family. Candidate 1 failed all three requirements. Candidate 2 passed only the structural requirement. Candidate 3 passed the structural and family-coverage requirements but missed the joint-pass threshold by one response.

The predeclared no-winner rule therefore selects no adapter. Candidate 3 is the strongest diagnostic result, but promoting it as “least bad” would discard the minimum quality bar after observing the evidence.

## Structural results

Candidate 1 had three invalid responses: one JSON syntax failure, one wrong field type, and one response that violated both ingredient- and method-count limits. Candidate 2 had one JSON syntax failure. Candidate 3 produced ten valid schema instances.

This is a material improvement over the pilot adapter, which produced zero valid objects from the same ten prompts. Broader attention targeting also improved structure more than doubling exposure: Candidate 3 reached 10/10 after three epochs, while Candidate 2 reached 9/10 after six.

## Blinded qualitative results

| Candidate | Underlying answer ≥2 | Metaphor ≥2 | Recipe execution ≥2 | Full joint pass |
| --- | ---: | ---: | ---: | ---: |
| 1 | 3/7 eligible | 6/7 | 6/7 | 3/10 population |
| 2 | 4/9 eligible | 8/9 | 9/9 | 4/10 population |
| 3 | 6/10 eligible | 10/10 | 10/10 | 6/10 population |

Candidate 3 consistently learned the cocktail representation: every response passed metaphorical coherence and recipe-style execution. Its four joint failures were all failures of underlying task fulfilment:

- it invented an unsupported noon finish in a simple volunteer reminder;
- it recommended a fixed weekly commitment despite the user's changing schedule;
- it returned an eight-word bicycle slogan and used “fixing” despite the constraint; and
- it blurred the distinction between synchronisation and backup in its conclusion.

The common first-round bottleneck is therefore not entering or sustaining the ChatG&T format. It is retaining precise substantive instruction-following while expressing the answer through that format. Additional repeated exposure alone was not supported: Candidate 2 trained twice as long as Candidate 1 but remained weak on the same decision, creative, and transformation tasks. Broader target surface was supported directionally because Candidate 3 improved structure, family coverage, and joint passes without additional epochs.

This diagnosis is specific enough to justify discussing a bounded second-round capacity hypothesis, such as whether extending adaptation beyond attention projections improves content selection and constraint adherence. No second-round configuration has been frozen or run as part of this result.

## Infrastructure and cost

The preferred Community Cloud RTX 4090 had no deployable capacity. The already-approved fallback used one Secure Cloud NVIDIA L4 with 24 GB VRAM from Runpod's official PyTorch 2.8.0 template at `$0.39/hour`. The host exposed driver `580.126.20` and CUDA 13.0 compatibility. A two-hour automatic termination deadline guarded the session.

All evidence was retrieved and verified before deletion. After the provider's delayed billing entry settled, the account balance had moved from `$8.0117290235` to `$7.9425150717`, a session cost of `$0.0692139518`, rounded to `$0.07`. Runpod then reported no Pods and `$0/hour` active spend.

## Evidence locations

- Generation runs: `experiments/runs/full-candidate-*-behaviour-v1-20260717-run01/`
- Session evidence: `experiments/runs/candidate-selection-session-20260717/`
- Structural evaluations: `experiments/evaluations/full-candidate-*-behaviour-v1-20260717-run01-structure/`
- Blind packets, scores, mapping, reveal, and summary: `experiments/evaluations/full-training-candidates-v1-20260717-blind-scoring/`
- Mechanical selection result: `experiments/evaluations/full-training-candidates-v1-20260717-selection.json`
- Retrieved archive SHA-256: `fadc1d81d19e4a77e4c8ba2966d6b8a33e7e6198f64b40070f8af4990d1bd396`
- Recorded behaviour-tree SHA-256: `a0ab38a39f15d204142df24baa5bb0564c38adf51ffbfb530a3a8b501f766944` (verified byte-for-byte against the execution commit)

## Next decision

Stage 6 cannot freeze an adapter yet. Discuss whether the evidence supports using the predeclared second-round allowance. If so, freeze at most two configurations tied to the content-selection and constraint-adherence diagnosis before either is trained.
